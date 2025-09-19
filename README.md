# Call Transcript Analyzer

This project provides a Python-based pipeline to analyze customer call transcripts. It uses an LLM API to generate a **summary** of the customer’s problem and classify the **sentiment** as *Positive*, *Neutral*, or *Negative*.

## Features

* Extracts concise 2–3 sentence summaries of customer issues.
* Performs sentiment analysis: Positive, Neutral, or Negative.
* Handles messy LLM outputs by normalizing responses and attempting JSON parsing.
* Provides fallback heuristics if the model output is invalid.

## Project Structure

* **Transcript Input**: A customer call transcript string.
* **Prompt Engineering**: Constructs a strict JSON request for the model.
* **Response Handling**: Normalizes and parses the model output to ensure valid JSON.
* **Fallback Handling**: If JSON parsing fails, applies heuristics for summary and sentiment.

## Example Flow

1. A transcript is passed into the script.
2. A prompt is generated requesting strict JSON with two keys:

   * `summary`: Concise 2–3 sentence explanation of the customer’s issue.
   * `sentiment`: One of `"Positive"`, `"Neutral"`, or `"Negative"`.
3. The model’s response is normalized and parsed into JSON.
4. If parsing fails, fallback heuristics generate a summary and sentiment.
5. Final output is a structured dictionary containing `summary` and `sentiment`.

## Requirements

* Python 3.9+
* Dependencies:

  ```bash
  pip install groq regex
  ```
* Valid Groq API credentials.

## Usage

```python
transcript = "The customer was charged twice for their subscription and is upset."
result = analyze_transcript(transcript)
print(result)
```

**Output Example:**

```json
{
  "summary": "The customer reported being billed twice for their subscription and expressed dissatisfaction.",
  "sentiment": "Negative"
}
```

## Error Handling

* If the Groq API call fails or returns invalid JSON, the script falls back to:

  * First line of the response as a summary.
  * Regex-based sentiment classification.
