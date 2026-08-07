from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
import logging

logger = logging.getLogger(__name__)

from schedule.exceptions import WorkspaceNotFoundException
from schedule.serializers import (
    GenerateScheduleSerializer,
    StudyScheduleSerializer,
)
from dashboard.services import ActivityLogger
from schedule.services import ScheduleGenerationService
from schedule.selectors import ScheduleSelector
from schedule.models import ScheduleGenerationJob
from workspace.models import Workspace
from quiz.models import QuizAttempt
import threading


class GenerateScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = GenerateScheduleSerializer(
            data=request.data,
        )
        serializer.is_valid(
            raise_exception=True,
        )

        logger.info("Schedule generation requested for attempt_id: %s by user: %s", serializer.validated_data["attempt_id"], request.user.id)

        try:
            attempt = QuizAttempt.objects.select_related("quiz__workspace").get(
                id=serializer.validated_data["attempt_id"], user=request.user
            )
        except QuizAttempt.DoesNotExist:
            return Response({"error": "Quiz attempt not found"}, status=status.HTTP_404_NOT_FOUND)

        # Create the generation job
        job = ScheduleGenerationJob.objects.create(
            user=request.user,
            workspace=attempt.quiz.workspace,
            status="RUNNING"
        )

        def generate_in_background(job_id, attempt_id, user_id, study_days, hours_per_day, start_date):
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                schedule = ScheduleGenerationService.generate_schedule(
                    attempt_id=attempt_id,
                    user=user,
                    study_days=study_days,
                    hours_per_day=hours_per_day,
                    start_date=start_date,
                )
                
                # Update job status
                job_instance = ScheduleGenerationJob.objects.get(id=job_id)
                job_instance.status = "COMPLETED"
                job_instance.schedule = schedule
                job_instance.save()
                
                ActivityLogger.log(
                    user=user,
                    action="SCHEDULE_CREATED",
                    description=f"Generated a new study schedule based on quiz attempt.",
                    metadata={"schedule_id": str(schedule.id), "workspace_id": str(schedule.workspace_id), "job_id": str(job_id)}
                )
                logger.info("Schedule successfully generated with ID: %s", schedule.id)

            except Exception as e:
                logger.error("Failed to generate schedule for job %s: %s", job_id, e)
                job_instance = ScheduleGenerationJob.objects.filter(id=job_id).first()
                if job_instance:
                    job_instance.status = "FAILED"
                    job_instance.failure_reason = str(e)
                    job_instance.save()

        # Start thread
        thread = threading.Thread(
            target=generate_in_background,
            args=(
                job.id,
                serializer.validated_data["attempt_id"],
                request.user.id,
                serializer.validated_data["study_days"],
                serializer.validated_data["hours_per_day"],
                serializer.validated_data["start_date"],
            )
        )
        thread.daemon = True
        thread.start()

        return Response(
            {"job_id": job.id, "detail": "Schedule generation started in background."},
            status=status.HTTP_202_ACCEPTED,
        )

class ScheduleJobStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, job_id):
        try:
            job = ScheduleGenerationJob.objects.get(id=job_id, user=request.user)
        except ScheduleGenerationJob.DoesNotExist:
            return Response({"error": "Job not found"}, status=status.HTTP_404_NOT_FOUND)

        data = {
            "status": job.status,
            "failure_reason": job.failure_reason,
            "schedule_id": job.schedule_id,
        }
        return Response(data, status=status.HTTP_200_OK)


class WorkspaceScheduleJobStatusAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, workspace_id):
        # Return the most recent job for this workspace
        job = ScheduleGenerationJob.objects.filter(
            workspace_id=workspace_id, user=request.user
        ).order_by("-created_at").first()

        if not job:
            return Response({"status": "NONE"}, status=status.HTTP_200_OK)

        data = {
            "status": job.status,
            "failure_reason": job.failure_reason,
            "schedule_id": job.schedule_id,
        }
        return Response(data, status=status.HTTP_200_OK)

class StudyScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        schedule_id,
    ):
        logger.info("Retrieving study schedule ID: %s for user: %s", schedule_id, request.user.id)

        schedule = ScheduleSelector.get_schedule_for_user(
            schedule_id=schedule_id,
            user=request.user,
        )

        ActivityLogger.log(
            user=request.user,
            action="SCHEDULE_VIEWED",
            description="Viewed a study schedule.",
            metadata={"schedule_id": str(schedule.id)}
        )

        return Response(
            StudyScheduleSerializer(schedule).data,
            status=status.HTTP_200_OK,
        )


class LatestStudyScheduleAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        workspace_id,
    ):
        logger.info("Retrieving latest study schedule for workspace: %s", workspace_id)

        try:
            workspace = request.user.workspaces.get(
                id=workspace_id,
            )
        except Workspace.DoesNotExist:
            logger.warning("Workspace %s not found for user %s", workspace_id, request.user.id)
            raise WorkspaceNotFoundException()

        schedule = ScheduleSelector.get_latest_schedule(
            workspace=workspace,
        )

        if schedule is None:
            logger.info("No active schedule found for workspace: %s", workspace_id)
            return Response(
                None,
                status=status.HTTP_204_NO_CONTENT,
            )

        logger.info("Found latest schedule ID: %s", schedule.id)
        return Response(
            StudyScheduleSerializer(schedule).data,
            status=status.HTTP_200_OK,
        )


class WorkspaceStudySchedulesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(
        self,
        request,
        workspace_id,
    ):
        logger.info("Retrieving all study schedules for workspace: %s", workspace_id)

        try:
            workspace = request.user.workspaces.get(
                id=workspace_id,
            )
        except Workspace.DoesNotExist:
            logger.warning("Workspace %s not found for user %s", workspace_id, request.user.id)
            raise WorkspaceNotFoundException()

        schedules = ScheduleSelector.get_all_schedules_for_workspace(
            workspace=workspace,
        )

        return Response(
            StudyScheduleSerializer(schedules, many=True).data,
            status=status.HTTP_200_OK,
        )


class ToggleScheduleTopicAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(
        self,
        request,
        schedule_id,
        topic_index,
    ):
        logger.info("Toggling topic index: %s in schedule ID: %s for user: %s", topic_index, schedule_id, request.user.id)

        schedule = ScheduleSelector.get_schedule_for_user(
            schedule_id=schedule_id,
            user=request.user,
        )

        is_completed = request.data.get("is_completed")
        if is_completed is None:
            return Response({"error": "is_completed field is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure generated_plan exists and has a schedule list
        if not schedule.generated_plan or "schedule" not in schedule.generated_plan:
            return Response({"error": "Schedule plan is missing"}, status=status.HTTP_400_BAD_REQUEST)

        topics_list = schedule.generated_plan["schedule"]
        
        if not (0 <= topic_index < len(topics_list)):
            return Response({"error": "Invalid topic index"}, status=status.HTTP_400_BAD_REQUEST)

        # Toggle the status
        topics_list[topic_index]["is_completed"] = bool(is_completed)
        
        # Save the updated JSON plan
        schedule.generated_plan["schedule"] = topics_list
        schedule.save(update_fields=["generated_plan"])

        ActivityLogger.log(
            user=request.user,
            action="SCHEDULE_TOPIC_TOGGLED",
            description=f"Marked topic '{topics_list[topic_index].get('topic', 'Unknown')}' as {'completed' if is_completed else 'incomplete'}.",
            metadata={"schedule_id": str(schedule.id), "topic_index": topic_index}
        )

        return Response(
            StudyScheduleSerializer(schedule).data,
            status=status.HTTP_200_OK,
        )


