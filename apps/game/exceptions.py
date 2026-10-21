from rest_framework import status
from rest_framework.exceptions import APIException


class InvalidToken(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = "Geçersiz oturum anahtarı."
    default_code = "invalid_token"


class SessionExpired(APIException):
    status_code = status.HTTP_410_GONE
    default_detail = "Oturumun süresi doldu."
    default_code = "session_expired"


class SessionFinished(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Oturum zaten bitti."
    default_code = "session_finished"


class QuestionMismatch(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Bu soru şu anda aktif değil."
    default_code = "question_mismatch"


class AlreadyAnswered(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_detail = "Bu soru zaten cevaplandı."
    default_code = "already_answered"


class InvalidName(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = "Geçersiz isim."
    default_code = "invalid_name"
