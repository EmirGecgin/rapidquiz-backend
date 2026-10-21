from rest_framework.throttling import AnonRateThrottle


class SessionCreateThrottle(AnonRateThrottle):
    scope = "session_create"


class AnswerThrottle(AnonRateThrottle):
    scope = "answer_submit"
