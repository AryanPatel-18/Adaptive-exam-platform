from rest_framework.exceptions import APIException


class QuizException(APIException):
    status_code = 400
    default_detail = "A quiz operation failed."
    default_code = "quiz_error"


class QuizNotFoundException(QuizException):
    status_code = 404
    default_detail = "The requested quiz does not exist."
    default_code = "quiz_not_found"


class QuizAttemptNotFoundException(QuizException):
    status_code = 404
    default_detail = "The requested quiz attempt does not exist."
    default_code = "quiz_attempt_not_found"


class QuizAlreadyCompletedException(QuizException):
    status_code = 409
    default_detail = "This quiz attempt has already been completed."
    default_code = "quiz_already_completed"


class InvalidQuestionException(QuizException):
    status_code = 404
    default_detail = "The requested question does not belong to this quiz."
    default_code = "invalid_question"


class InvalidQuestionOrderException(QuizException):
    status_code = 400
    default_detail = "The requested question order is invalid."
    default_code = "invalid_question_order"


class InvalidQuestionCountException(QuizException):
    status_code = 400
    default_detail = "Invalid number of questions requested."
    default_code = "invalid_question_count"


class InvalidQuizSubmissionException(QuizException):
    status_code = 400
    default_detail = "Unable to submit the quiz."
    default_code = "invalid_quiz_submission"


class QuizPermissionException(QuizException):
    status_code = 403
    default_detail = "You do not have permission to access this quiz."
    default_code = "quiz_permission_denied"


class QuestionAlreadyAnsweredException(QuizException):
    status_code = 409
    default_detail = "This question has already been answered."
    default_code = "question_already_answered"


class NoQuestionsAvailableException(QuizException):
    status_code = 400
    default_detail = "No questions are available in this workspace to create a quiz."
    default_code = "no_questions_available"
