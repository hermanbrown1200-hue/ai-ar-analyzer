from flask import Flask, request, render_template
from io import BytesIO
from pydub import AudioSegment
import openai
import os

# Get OpenAI key from Render environment variables
openai.api_key = os.environ.get("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload_file():
    # Check if file is uploaded
    if "song" not in request.files:
        return "No file uploaded", 400

    file = request.files["song"]
    genre = request.form.get("genre", "Pop")  # Get genre input

    # Load audio in memory
    audio_bytes = BytesIO(file.read())
    audio = AudioSegment.from_file(audio_bytes)

    # Split into segments (10 seconds each)
    segment_length_ms = 10000
    segments = [audio[i:i+segment_length_ms] for i in range(0, len(audio), segment_length_ms)]

    full_analysis = ""
    for idx, seg in enumerate(segments):
        energy = seg.dBFS  # segment energy in dB

        # Optional: transcribe vocals
        try:
            audio_bytes.seek(0)
            transcription = openai.audio.transcriptions.create(
                model="whisper-1",
                file=BytesIO(file.read())
            )
            lyrics_text = transcription["text"]
        except Exception:
            lyrics_text = "No transcription available."

        # Pro A&R prompt
        prompt = f"""
You are a professional music A&R expert.
Analyze this 10-second segment of a {genre} song.
- Segment duration: {len(seg)/1000:.2f} seconds
- Loudness: {energy:.2f} dB
- Lyrics (if any): {lyrics_text}

Tasks:
1. Compare energy and vibe to popular {genre} songs with millions of streams.
2. Detect musical key.
3. Suggest 2-3 commercially successful songs that are most similar in vibe and key (sound-alike analysis).
4. Give short improvement notes and commercial potential.
"""

        # Call OpenAI GPT
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}]
            )
            segment_analysis = response.choices[0].message.content
        except Exception as e:
            segment_analysis = f"Error: {e}"

        full_analysis += f"\nSegment {idx+1} Analysis:\n{segment_analysis}\n"

    return render_template("feedback.html", feedback=full_analysis)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
