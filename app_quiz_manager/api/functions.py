import os
import re
import json
import uuid
import whisper
import yt_dlp
from google import genai
from google.genai.errors import ClientError
from rest_framework.exceptions import ValidationError
from ..models import Quiz, Question

_model_whisper = None

def extract_video_id(url: str) -> str:
    """Extracts video ID from a YouTube URL."""
    regex = r"(?:v=|be\/|embed\/|v\/|shorts\/|[?&]v=)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    if not match:
        raise ValidationError({'url': 'Invalid YouTube URL'})
    return match.group(1)

def download_audio(url: str, tmp_filename: str) -> None:
    """Downloads audio from YouTube using yt-dlp."""
    ydl_opts = {"format": "bestaudio/best", "outtmpl": tmp_filename, "quiet": True, "noplaylist": True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except yt_dlp.utils.DownloadError:
        raise ValidationError({'url': 'Invalid YouTube URL or video unavailable'})

def transcribe_audio(file_path: str) -> str:
    """Lazy-loads Whisper model and transcribes audio."""
    global _model_whisper
    if _model_whisper is None: _model_whisper = whisper.load_model("base")
    return _model_whisper.transcribe(file_path, fp16=False)["text"]

def generate_quiz_json(transcript: str) -> dict:
    """Generates JSON quiz using Gemini API with controlled output."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key: raise ValueError("GEMINI_API_KEY must be set")
    client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
    prompt = (
        "Based on the transcript, generate a 10-question quiz JSON. "
        "Each question must have exactly 4 options. "
        "Schema: title, description, questions (question_title, question_options [list of 4], answer). "
        f"Transcript: {transcript}"
    )
    cfg = {'response_mime_type': 'application/json'}
    resp = client.models.generate_content(model='gemini-2.0-flash', contents=prompt, config=cfg)
    return json.loads(resp.text)

def _create_questions(quiz: Quiz, questions_data: list):
    """Helper to create questions for a quiz."""
    for q in questions_data:
        opts = q.get('question_options', q.get('options', [])) + [""] * 4
        Question.objects.create(
            quiz=quiz, question_title=q.get('question_title', q.get('text', '')),
            option_a=opts[0], option_b=opts[1], option_c=opts[2], option_d=opts[3],
            correct_answer=q.get('answer', q.get('correct_answer', ''))
        )

def save_quiz_to_db(data: dict, user, video_url: str) -> Quiz:
    """Saves quiz data and questions to the database."""
    quiz = Quiz.objects.create(
        user=user, title=data.get('title', 'Untitled')[:150],
        description=data.get('description', '')[:150], video_url=video_url
    )
    _create_questions(quiz, data.get('questions', []))
    return quiz

def run_quiz_generation_pipeline(url: str, user) -> Quiz:
    """Orchestrates quiz generation with modular steps."""
    v_id, t_file = extract_video_id(url), f"/tmp/{uuid.uuid4()}.m4a"
    n_url = f"https://www.youtube.com/watch?v={v_id}"
    try:
        download_audio(n_url, t_file)
        transcript = transcribe_audio(t_file)
        quiz_data = generate_quiz_json(transcript)
        return save_quiz_to_db(quiz_data, user, url)
    except Exception as e:
        raise ValidationError({'url': 'Generation failed. Please try again later.'})
    finally:
        if os.path.exists(t_file): os.remove(t_file)
