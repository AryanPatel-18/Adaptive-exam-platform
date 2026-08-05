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
from workspace.models import Workspace


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


        schedule = ScheduleGenerationService.generate_schedule(
            attempt_id=serializer.validated_data["attempt_id"],
            user=request.user,
            study_days=serializer.validated_data["study_days"],
            hours_per_day=serializer.validated_data["hours_per_day"],
            start_date=serializer.validated_data["start_date"],
        )

        logger.info("Schedule successfully generated with ID: %s", schedule.id)

        ActivityLogger.log(
            user=request.user,
            action="SCHEDULE_CREATED",
            description=f"Generated a new study schedule based on quiz attempt.",
            metadata={"schedule_id": str(schedule.id), "workspace_id": str(schedule.workspace_id)}
        )

        return Response(
            StudyScheduleSerializer(schedule).data,
            status=status.HTTP_201_CREATED,
        )


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

