from common.choices import FileStatus, FileRole
from django.db.models import Count
from files.models import File
from quiz.models import Quiz
from workspace.models import Workspace


class WorkspaceSelector:
    @staticmethod
    def get_user_workspaces_details(user):
        return Workspace.objects.filter(owner=user).annotate(
            quiz_count=Count('quizzes', distinct=True),
            file_count=Count('files', distinct=True)
        ).order_by('-updated_at')

    @staticmethod
    def get_workspace_files(workspace_id):
        """
        Returns a dictionary containing the active question bank file 
        and a list of active notes files for the given workspace.
        """
        active_files = File.objects.filter(
            workspace_id=workspace_id,
            status=FileStatus.ACTIVE
        )

        question_bank = active_files.filter(role=FileRole.QUESTION_BANK).first()
        notes = list(active_files.filter(role=FileRole.NOTES))

        return {
            "question_bank": question_bank,
            "notes": notes,
        }

    @staticmethod
    def get_workspace_quizzes(workspace_id):
        """
        Returns a list of all quizzes created within the given workspace.
        """
        return list(Quiz.objects.filter(workspace_id=workspace_id).order_by('-created_at'))
