from django.urls import path

from quiz.views import (
    CreateQuizAPIView,
    FinishQuizAPIView,
    QuizQuestionAPIView,
    QuizResultAPIView,
    StartQuizAPIView,
    SubmitAnswerAPIView,
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
        "attempt/<uuid:attempt_id>/result/",
        QuizResultAPIView.as_view(),
        name="quiz-result",
    ),
]