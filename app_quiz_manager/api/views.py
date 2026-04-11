from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import QuizSerializer, QuizCreateSerializer
from ..models import Quiz

class QuizViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user).order_by('-created_at')

    def get_serializer_class(self):
        return QuizCreateSerializer if self.action == 'create' else QuizSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
