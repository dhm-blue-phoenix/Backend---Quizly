from rest_framework import serializers
from ..models import Quiz, Question
from .functions import run_quiz_generation_pipeline

class QuestionSerializer(serializers.ModelSerializer):
    question_title = serializers.CharField(source='text')
    question_options = serializers.SerializerMethodField()
    answer = serializers.CharField(source='correct_answer')

    class Meta:
        model = Question
        fields = ['id', 'question_title', 'question_options', 'answer', 'created_at', 'updated_at']

    def get_question_options(self, obj):
        return [obj.option_a, obj.option_b, obj.option_c, obj.option_d]

class QuizSerializer(serializers.ModelSerializer):
    video_url = serializers.URLField(source='url')
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'created_at', 'updated_at', 'video_url', 'questions']
        read_only_fields = ['created_at', 'updated_at']

class QuizCreateSerializer(serializers.Serializer):
    url = serializers.URLField(write_only=True)

    def create(self, validated_data):
        return run_quiz_generation_pipeline(validated_data['url'], validated_data['user'])

    def to_representation(self, instance):
        return QuizSerializer(instance).data
