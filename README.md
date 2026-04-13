# Quizly Backend - Generative AI Quiz Platform

Quizly is a powerful Django-based REST API that uses state-of-the-art AI to generate interactive quizzes from YouTube videos. By leveraging **yt-dlp** for audio extraction, **OpenAI Whisper** for transcription, and **Google Gemini 2.0 Flash** for quiz generation, Quizly provides a seamless experience for creating educational content.

---

## Features

- **Automated Quiz Generation**: Enter a YouTube URL and get a 10-question quiz in seconds.
- **Secure Authentication**: JWT-based authentication using **HttpOnly Cookies** (`access_token` and `refresh_token`) for maximum security.
- **AI-Powered**: Uses Google's latest Gemini 2.0 Flash model for high-quality question generation.
- **Clean Architecture**: Strictly separated business logic in `functions.py` and response logic in `views.py`.
- **Full Documentation Alignment**: Built to match the internal Quizly API specification.

---

## Prerequisites

Before setting up the project, ensure you have the following installed:

- **Python 3.12+**
- **FFMPEG**: This is **REQUIRED** for Whisper AI and yt-dlp to process audio data.
  - *Linux*: `sudo apt install ffmpeg`
  - *macOS*: `brew install ffmpeg`
  - *Windows*: Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to your PATH.

---

## Installation & Setup

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd Backend---Quizly
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   # .venv\Scripts\activate   # Windows
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Create a `.env` file in the root directory and add your credentials:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   GEMINI_API_KEY=your_google_gemini_api_key
   ```

5. **Run Migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```

---

## API Usage

The main endpoints for quiz management are available under `/api/quizzes/`.

### Create a Quiz
**POST** `/api/quizzes/`
```json
{
  "url": "https://www.youtube.com/watch?v=example"
}
```

### List Your Quizzes
**GET** `/api/quizzes/`

### Get Quiz Details
**GET** `/api/quizzes/{id}/`

---

## Testing

The project comes with a comprehensive suite of **38 tests** covering both authentication and quiz management.

To run the tests:
```bash
python manage.py test
```

---

## Tech Stack

- **Backend**: Django 6.0, Django REST Framework 3.17
- **Authentication**: SimpleJWT (Cookie-based)
- **Audio Processing**: yt-dlp, FFmpeg
- **Machine Learning**: OpenAI Whisper (Local transcription)
- **AI Model**: Google Gemini 2.0 Flash (SDK: `google-genai`)

---
