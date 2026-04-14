import os
import re
import json
import uuid
import whisper
import yt_dlp
import traceback
from google import genai
from google.genai.errors import ClientError
from rest_framework.exceptions import ValidationError
from ..models import Quiz, Question

_model_whisper = None

def extract_video_id(url: str) -> str:
    """Extracts video ID from a YouTube URL."""
    #print(f"[DEBUG] Extracting Video ID from URL: {url}")
    regex = r"(?:v=|be\/|embed\/|v\/|shorts\/|[?&]v=)([0-9A-Za-z_-]{11})"
    match = re.search(regex, url)
    if not match:
        #print("[ERROR] Invalid YouTube URL")
        raise ValidationError({'url': 'Invalid YouTube URL'})
    v_id = match.group(1)
    #print(f"[DEBUG] Found Video ID: {v_id}")
    return v_id

def download_audio(url: str, tmp_filename: str) -> None:
    """Downloads audio from YouTube using yt-dlp with remote components."""
    #print(f"[DEBUG] Starting audio download for URL: {url}")
    ydl_opts = {
        "format": "bestaudio/best", "outtmpl": tmp_filename, "quiet": True, 
        "noplaylist": True, "js_runtimes": {"node": {}},
        "remote_components": ["ejs:github"]
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        #print(f"[DEBUG] Audio downloaded successfully to: {tmp_filename}")
    except Exception as e:
        #print(f"[ERROR] yt-dlp Download failed: {str(e)}")
        raise ValidationError({'url': f'Download failed: {str(e)}'})

def transcribe_audio(file_path: str) -> str:
    """Lazy-loads Whisper model and transcribes audio."""
    global _model_whisper
    #print("[DEBUG] Starting Audio Transcription...")
    if _model_whisper is None: 
        #print("[DEBUG] Loading Whisper 'base' model (first time)...")
        _model_whisper = whisper.load_model("base")
    result = _model_whisper.transcribe(file_path, fp16=False)["text"]
    #print(f"[DEBUG] Transcription finished. Length: {len(result)} characters.")
    return result

def _fetch_gemini_json(transcript: str) -> dict:
    """Helper to fetch and clean JSON from Gemini."""
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    prompt = (
        "Respond ONLY with valid raw JSON for a 10-question quiz. "
        "Schema: title, description, questions (question_title, question_options [4], answer). "
        f"Transcript: {transcript}"
    )
    conf = {'response_mime_type': 'application/json', 'max_output_tokens': 8192}
    resp = client.models.generate_content(model='gemini-flash-latest', contents=prompt, config=conf)
    raw = resp.text.strip()
    if raw.startswith("```json"): raw = raw[7:].strip()
    if raw.endswith("```"): raw = raw[:-3].strip()
    return json.loads(raw)

def generate_quiz_json(transcript: str) -> dict:
    """Generates JSON quiz with a 3-attempt retry loop for robustness."""
    #print("[DEBUG] Sending transcript to Gemini API with retry logic...")
    for attempt in range(3):
        try:
            data = _fetch_gemini_json(transcript)
            #print("[DEBUG] Gemini API response received successfully.")
            return data
        except json.JSONDecodeError as de:
            if attempt == 2:
                #print(f"[CRITICAL ERROR] Failed to decode AI JSON after 3 tries.")
                raise de
            #print(f"[DEBUG] JSON parsing failed, retrying (attempt {attempt+2}/3)...")

def _create_questions(quiz: Quiz, questions_data: list):
    """Helper to create questions for a quiz."""
    #print(f"[DEBUG] Saving {len(questions_data)} questions to the database...")
    for q in questions_data:
        opts = q.get('question_options', q.get('options', [])) + [""] * 4
        Question.objects.create(
            quiz=quiz, question_title=q.get('question_title', q.get('text', '')),
            option_a=opts[0], option_b=opts[1], option_c=opts[2], option_d=opts[3],
            correct_answer=q.get('answer', q.get('correct_answer', ''))
        )

def save_quiz_to_db(data, user, video_url: str) -> Quiz:
    """Saves quiz data and questions with normalization."""
    if isinstance(data, list) and len(data) > 0:
        if isinstance(data[0], dict) and 'questions' in data[0]: data = data[0]
        else: data = {'title': 'AI Generated Quiz', 'questions': data}
    elif not isinstance(data, dict): data = {'title': 'AI Generated Quiz', 'questions': []}
    #print(f"[DEBUG] Saving Quiz '{data.get('title')}' for user {user.username}...")
    quiz = Quiz.objects.create(
        user=user, title=str(data.get('title', 'Untitled'))[:150],
        description=str(data.get('description', ''))[:150], video_url=video_url
    )
    _create_questions(quiz, data.get('questions', []))
    #print("[DEBUG] Quiz and questions saved successfully.")
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
        full_error = traceback.format_exc()
        #print(f"[CRITICAL ERROR] Pipeline failed:\n{full_error}")
        raise ValidationError({'url': f'Generation failed: {str(e)}'})
    finally:
        if os.path.exists(t_file): 
            os.remove(t_file)
            #print(f"[DEBUG] Temporary file {t_file} removed.")
