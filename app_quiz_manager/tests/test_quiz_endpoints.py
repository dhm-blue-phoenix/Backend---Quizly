from unittest.mock import patch
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.exceptions import ValidationError
from app_quiz_manager.models import Quiz, Question

User = get_user_model()

class QuizEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', email='test@example.com', password='password123')
        self.other_user = User.objects.create_user(username='otheruser', email='other@example.com', password='password123')
        
    def test_unauthenticated_access(self):
        # Unhappy Path: Access without login (401)
        url = reverse('quiz-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        
        response = self.client.post(url, {'url': ''})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    @patch('app_quiz_manager.api.functions.download_audio')
    @patch('app_quiz_manager.api.functions.transcribe_audio')
    @patch('app_quiz_manager.api.functions.generate_quiz_json')
    def test_create_quiz_happy_path(self, mock_generate_json, mock_transcribe, mock_download):
        self.client.force_authenticate(user=self.user)
        
        # Mock implementations
        mock_transcribe.return_value = "Mocked transcription text"
        mock_generate_json.return_value = {
            "title": "Mocked Quiz Title",
            "description": "Mocked description",
            "questions": [
                {
                    "question_title": "What is 2+2?",
                    "question_options": ["1", "2", "3", "4"],
                    "answer": "4"
                }
            ]
        }
        
        url = reverse('quiz-list')
        data = {'url': 'https://www.youtube.com/watch?v=EhKaRi0Og1s'}
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], "Mocked Quiz Title")
        self.assertEqual(response.data['video_url'], data['url'])
        self.assertIn('questions', response.data)
        q0 = response.data['questions'][0]
        self.assertEqual(q0['question_title'], "What is 2+2?")
        self.assertEqual(q0['question_options'], ["1", "2", "3", "4"])
        self.assertEqual(q0['answer'], "4")
        self.assertTrue(Quiz.objects.filter(user=self.user, title="Mocked Quiz Title").exists())
        self.assertTrue(Question.objects.filter(quiz__title="Mocked Quiz Title").exists())
        
        mock_download.assert_called_once()
        mock_transcribe.assert_called_once()
        mock_generate_json.assert_called_once()

    def test_invalid_url(self):
        import yt_dlp
        self.client.force_authenticate(user=self.user)
        url = reverse('quiz-list')
        data = {'url': 'https://www.youtube.com/watch?v=invalid_id1'}
        
        with patch('app_quiz_manager.api.functions.download_audio') as mock_download:
            mock_download.side_effect = ValidationError({'url': 'Invalid YouTube URL or video unavailable'})
            response = self.client.post(url, data, format='json')
            
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)

    def test_invalid_url_format(self):
        self.client.force_authenticate(user=self.user)
        url = reverse('quiz-list')
        
        data = {'url': 'https://completely-invalid-format.com'}
        
        response = self.client.post(url, data, format='json')
        # Expecting a failure handled cleanly with a ValidationError from regex
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('url', response.data)

    def test_get_quizzes(self):
        self.client.force_authenticate(user=self.user)
        Quiz.objects.create(user=self.user, title="My Quiz", description="Desc")
        Quiz.objects.create(user=self.other_user, title="Other Quiz", description="Desc")
        
        url = reverse('quiz-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "My Quiz")

    def test_update_quiz(self):
        self.client.force_authenticate(user=self.user)
        quiz = Quiz.objects.create(user=self.user, title="Old Title", description="Old Desc")
        
        url = reverse('quiz-detail', args=[quiz.id])
        data = {'title': 'New Title'}
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        quiz.refresh_from_db()
        self.assertEqual(quiz.title, "New Title")

    def test_delete_quiz(self):
        self.client.force_authenticate(user=self.user)
        quiz = Quiz.objects.create(user=self.user, title="To Delete", description="Desc")
        
        url = reverse('quiz-detail', args=[quiz.id])
        response = self.client.delete(url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Quiz.objects.filter(id=quiz.id).exists())

    def test_access_other_user_quiz(self):
        # Unhappy Path: Accessing/Modifying quizzes of other users
        self.client.force_authenticate(user=self.user)
        other_quiz = Quiz.objects.create(user=self.other_user, title="Other User Quiz", description="Desc")
        
        url = reverse('quiz-detail', args=[other_quiz.id])
        
        # GET should be 404 since get_queryset filters by user
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        
        # PATCH and DELETE should also be 404
        response = self.client.patch(url, {'title': 'Hacked Title'})
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
