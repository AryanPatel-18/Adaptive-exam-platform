from django.urls import path

from quiz.views import (
    CreateQuizAPIView,
    FinishQuizAPIView,
    QuizQuestionAPIView,
    QuizResultAPIView,
    StartQuizAPIView,
    SubmitAnswerAPIView,
    UserQuizAttemptsAPIView,
    WorkspaceQuizStatsAPIView,
    ResumeQuizAPIView,
    PauseQuizAPIView,
    InProgressQuizzesAPIView,
    AttemptableQuizzesAPIView,
    QuizAttemptsAPIView,
)

app_name = "quiz"

urlpatterns = [
    path(
        "create/",
        CreateQuizAPIView.as_view(),
        name="create-quiz",
    ),
    path(
        "<uuid:quiz_id>/start/",
        StartQuizAPIView.as_view(),
        name="start-quiz",
    ),
    path(
        "<uuid:quiz_id>/resume/",
        ResumeQuizAPIView.as_view(),
        name="resume-quiz",
    ),
    path(
        "<uuid:quiz_id>/attempts/",
        QuizAttemptsAPIView.as_view(),
        name="quiz-attempts",
    ),
    path(
        "attempt/<uuid:attempt_id>/question/<int:question_order>/",
        QuizQuestionAPIView.as_view(),
        name="quiz-question",
    ),
    path(
        "attempt/<uuid:attempt_id>/answer/",
        SubmitAnswerAPIView.as_view(),
        name="submit-answer",
    ),
    path(
        "attempt/<uuid:attempt_id>/submit/",
        FinishQuizAPIView.as_view(),
        name="finish-quiz",
    ),
    path(
        "attempt/<uuid:attempt_id>/pause/",
        PauseQuizAPIView.as_view(),
        name="pause-quiz",
    ),
    path(
        "attempt/<uuid:attempt_id>/result/",
        QuizResultAPIView.as_view(),
        name="quiz-result",
    ),
    path(
        "attempts/",
        UserQuizAttemptsAPIView.as_view(),
        name="user-attempts",
    ),
    path(
        "workspace/<uuid:workspace_id>/attemptable/",
        AttemptableQuizzesAPIView.as_view(),
        name="attemptable-quizzes",
    ),
    path(
        "workspace/<uuid:workspace_id>/in-progress/",
        InProgressQuizzesAPIView.as_view(),
        name="in-progress-quizzes",
    ),
    path(
        "workspace/<uuid:workspace_id>/stats/",
        WorkspaceQuizStatsAPIView.as_view(),
        name="workspace-quiz-stats",
    ),
]
# Triggering dev server reload