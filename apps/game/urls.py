from django.urls import path

from .views import FinishSessionView, NextQuestionView, SessionCreateView, SubmitAnswerView

urlpatterns = [
    path("sessions/", SessionCreateView.as_view(), name="session-create"),
    path("sessions/<uuid:session_id>/next/", NextQuestionView.as_view(), name="session-next"),
    path("sessions/<uuid:session_id>/answer/", SubmitAnswerView.as_view(), name="session-answer"),
    path("sessions/<uuid:session_id>/finish/", FinishSessionView.as_view(), name="session-finish"),
]
