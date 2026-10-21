from rest_framework.exceptions import (
    AuthenticationFailed,
    NotAuthenticated,
    NotFound,
    ParseError,
    PermissionDenied,
    Throttled,
    UnsupportedMediaType,
    ValidationError,
)
from rest_framework.views import exception_handler as drf_exception_handler

KNOWN_ERROR_CODES = {
    "invalid_token",
    "session_expired",
    "session_finished",
    "question_mismatch",
    "already_answered",
    "invalid_name",
    "rate_limited",
    "not_found",
    "validation_error",
}

_EXCEPTION_CODES = {
    ValidationError: "validation_error",
    ParseError: "validation_error",
    UnsupportedMediaType: "validation_error",
    NotFound: "not_found",
    Throttled: "rate_limited",
    AuthenticationFailed: "invalid_token",
    NotAuthenticated: "invalid_token",
    PermissionDenied: "invalid_token",
}


def custom_exception_handler(exc, context):
    # exc.default_code wins when it's one of KNOWN_ERROR_CODES (custom game exceptions set this).
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    default_code = getattr(exc, "default_code", None)
    if default_code in KNOWN_ERROR_CODES:
        code = default_code
    else:
        code = _EXCEPTION_CODES.get(type(exc), "validation_error")

    detail = response.data
    if isinstance(detail, dict) and "detail" in detail:
        message = str(detail["detail"])
    elif isinstance(detail, list):
        message = str(detail[0]) if detail else ""
    else:
        message = str(detail)

    response.data = {"error": {"code": code, "message": message}}
    return response
