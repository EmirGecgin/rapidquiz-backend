from django.db.models import Count, Q
from rest_framework.generics import ListAPIView

from .models import Category
from .serializers import CategorySerializer


class CategoryListView(ListAPIView):
    serializer_class = CategorySerializer
    pagination_class = None

    def get_queryset(self):
        return (
            Category.objects.filter(is_active=True)
            .annotate(question_count=Count("questions", filter=Q(questions__is_active=True)))
            .order_by("order", "name")
        )
