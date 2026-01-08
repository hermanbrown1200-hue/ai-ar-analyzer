from flask import Flask, request, render_template
from io import BytesIO
from pydub import AudioSegment
import openai
import os

# Set OpenAI key from environment (we’ll add it later)
openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    if "song" not in request.files:
        return "No file uploaded", 400

    file = request.files["song"]

    # Process audio in memory
    audio_bytes = BytesIO(file.read())
    audio = AudioSegment.from_file(audio_bytes)
    duration = len(audio) / 1000  # seconds
    loudness = audio.dBFS

    # Optional: transcribe vocals with Whisper
    try:
        audio_bytes.seek(0)
        transcription = openai.audio.transcriptions.create(
            model="whisper-1",
            file=audio_bytes
        )
        lyrics_text = transcription["text"]
    except Exception:
        lyrics_text = "No transcription available."

    # Build AI A&R prompt
    prompt = f"""
You are an AI A&R agent. I uploaded a song:
- File Name: {file.filename}
- Duration: {duration:.2f} seconds
- Loudness: {loudness:.2f} dB
- Transcription of vocals: {lyrics_text}

Analyze professionally:
1. Overall vibe and genre
2. Strengths
3. Weaknesses / improvements
4. Commercial potential
5. Marketing suggestions
"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        feedback = response.choices[0].message.content
    except Exception as e:
        feedback = f"Error generating feedback: {e}"

    return render_template("feedback.html", feedback=feedback)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
