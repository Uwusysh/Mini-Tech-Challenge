import os
import json
import re
from pathlib import Path
from groq import Groq
from flask import Flask, request, render_template_string
import pandas as pd
from groq import Groq

# Hard-coded key version
client = Groq(api_key="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")

# --- Configuration ---
CSV_FILE = os.getenv("OUTPUT_CSV", "call_analysis.csv")
MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
client = Groq(api_key="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")


app = Flask(__name__)

# Minimal HTML UI (very small single-file form)
HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8" />
    <title>Call Analysis (Groq)</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 30px; }
      textarea { width: 100%; height: 150px; }
      .result { margin-top: 20px; padding: 12px; border-radius: 6px; background:#f6f6f8 }
      label { font-weight: bold }
    </style>
  </head>
  <body>
    <h2>Call Analysis (Groq)</h2>
    <form action="/analyze" method="post">
      <label for="transcript">Paste a call transcript:</label><br />
      <textarea name="transcript" id="transcript">{{ default_transcript }}</textarea><br />
      <button type="submit">Analyze</button>
    </form>

    {% if result %}
      <div class="result">
        <h3>Result</h3>
        <p><strong>Transcript:</strong><br>{{ result.Transcript }}</p>
        <p><strong>Summary:</strong> {{ result.Summary }}</p>
        <p><strong>Sentiment:</strong> {{ result.Sentiment }}</p>
        <p>Saved to <code>{{ csv_file }}</code></p>
      </div>
    {% endif %}

  </body>
</html>
"""

SAMPLE_TRANSCRIPT = """Hi, I tried to book a slot yesterday but the payment failed. I got charged twice and the slot is still not booked. Please help — I'm very frustrated because it's urgent."""


def call_groq_summary_and_sentiment(transcript: str) -> dict:
    """Call Groq Chat Completions to obtain a JSON response with `summary` and `sentiment`.

    Returns dict with keys: summary (str), sentiment (str).
    If parsing fails, returns best-effort fallback values.
    """
    user_prompt = (
        "Analyze the following customer call transcript and return a STRICT JSON object with exactly two keys:\n"
        '  "summary": a concise 2-3 sentence summary of the customer\'s problem (do NOT repeat the transcript),\n'
        '  "sentiment": one of "Positive", "Neutral", or "Negative".\n'
        'Return only valid JSON with those keys and no extra explanation.\n\n'
        f"Transcript:\n\"\"\"{transcript}\"\"\"\n"
    )

    try:
        completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": "You are a concise assistant that outputs strict JSON."},
                {"role": "user", "content": user_prompt},
            ],
            model=MODEL,
            temperature=0.0,
            max_tokens=300,
        )

        # The library returns typed response objects. The assistant text usually lives at:
        raw = completion.choices[0].message.content

        # Normalize raw content into a single string
        if isinstance(raw, str):
            text = raw
        elif isinstance(raw, list):
            parts = []
            for p in raw:
                if isinstance(p, dict):
                    parts.append(p.get("text") or p.get("content") or str(p))
                else:
                    parts.append(str(p))
            text = "".join(parts)
        else:
            text = str(raw)

        # Try to extract a JSON object from the response
        json_obj = None
        # 1) try direct parse
        try:
            json_obj = json.loads(text)
        except Exception:
            # 2) try to find a {...} substring
            m = re.search(r"\{.*\}", text, re.S)
            if m:
                try:
                    json_obj = json.loads(m.group(0))
                except Exception:
                    json_obj = None

        if isinstance(json_obj, dict):
            summary = str(json_obj.get("summary", "")).strip()
            sentiment = str(json_obj.get("sentiment", "")).strip()
        else:
            # Fallback: simple heuristics
            summary = text.strip().split("\n")[0][:500]
            sentiment = "Negative" if re.search(r"frustrat|angry|not happy|charged twice|failed|fail", transcript, re.I) else "Neutral"

    except Exception as e:
        # On error, return fallback values and bubble up message in the summary
        summary = f"Error calling Groq API: {e}"
        sentiment = "Neutral"

    # Normalize sentiment to one of the three values
    sentiment = sentiment.capitalize()
    if sentiment.lower().startswith("pos"):
        sentiment = "Positive"
    elif sentiment.lower().startswith("neg"):
        sentiment = "Negative"
    else:
        sentiment = "Neutral"

    return {"summary": summary, "sentiment": sentiment}


@app.route("/", methods=["GET"])
def index():
    return render_template_string(HTML_TEMPLATE, default_transcript=SAMPLE_TRANSCRIPT, result=None, csv_file=CSV_FILE)


@app.route("/analyze", methods=["POST"])
def analyze():
    transcript = request.form.get("transcript")
    if not transcript:
        return "No transcript provided", 400

    res = call_groq_summary_and_sentiment(transcript)
    summary = res.get("summary", "")
    sentiment = res.get("sentiment", "Neutral")

    row = {"Transcript": transcript, "Summary": summary, "Sentiment": sentiment}

    # Save/append to CSV
    csv_path = Path(CSV_FILE)
    if csv_path.exists():
        existing = pd.read_csv(csv_path)
        combined = pd.concat([existing, pd.DataFrame([row])], ignore_index=True)
        combined.to_csv(csv_path, index=False)
    else:
        pd.DataFrame([row]).to_csv(csv_path, index=False)

    # Print to console
    print("--- Call Analysis ---")
    print("Transcript:\n", transcript)
    print("Summary:\n", summary)
    print("Sentiment:\n", sentiment)

    return render_template_string(HTML_TEMPLATE, default_transcript=transcript, result=row, csv_file=CSV_FILE)


if __name__ == "__main__":
    # Run on localhost:5000 (debug mode helpful for development)
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", 5000)), debug=True)
