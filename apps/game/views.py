from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import (
    AnswerRequestSerializer,
    AnswerResponseSerializer,
    FinishRequestSerializer,
    FinishResponseSerializer,
    NextQuestionResponseSerializer,
    SessionCreateResponseSerializer,
    StartSessionRequestSerializer,
)
from .throttling import AnswerThrottle, SessionCreateThrottle


class SessionCreateView(APIView):
    throttle_classes = [SessionCreateThrottle]

    @extend_schema(request=StartSessionRequestSerializer, responses=SessionCreateResponseSerializer)
    def post(self, request):
        serializer = StartSessionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session = services.start_session(
            category_slug=serializer.validated_data["category"],
            platform=serializer.validated_data["platform"],
        )

        return Response(
            {
                "session_id": session.id,
                "token": session.token,
                "total_questions": len(session.question_ids),
                "time_limit_ms": services.TIME_LIMIT_MS,
            },
            status=201,
        )


class NextQuestionView(APIView):
    @extend_schema(request=None, responses=NextQuestionResponseSerializer)
    def post(self, request, session_id):
        session = services.get_authenticated_session(session_id, request.headers.get("X-Session-Token"))
        return Response(services.next_question(session))


class SubmitAnswerView(APIView):
    throttle_classes = [AnswerThrottle]

    @extend_schema(request=AnswerRequestSerializer, responses=AnswerResponseSerializer)
    def post(self, request, session_id):
        session = services.get_authenticated_session(session_id, request.headers.get("X-Session-Token"))
        serializer = AnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = services.submit_answer(session, **serializer.validated_data)
        return Response(data)


class FinishSessionView(APIView):
    @extend_schema(request=FinishRequestSerializer, responses=FinishResponseSerializer)
    def post(self, request, session_id):
        session = services.get_authenticated_session(session_id, request.headers.get("X-Session-Token"))
        serializer = FinishRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        data = services.finish_session(session, **serializer.validated_data)
        return Response(data)
