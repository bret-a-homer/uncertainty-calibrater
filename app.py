"""
Uncertainty Calibration Trainer — Flask backend
------------------------------------------------
Serves the single-page frontend and provides two JSON API endpoints:

  GET  /api/questions?topic=<slug>   → 40 random questions for a topic
  POST /api/score                    → compute calibration curve + Pearson score
"""

import json
import math
import random

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ── Load question bank once at startup ────────────────────────────────────────

with open("questions.json", "r", encoding="utf-8") as f:
    ALL_QUESTIONS: list[dict] = json.load(f)

QUESTIONS_PER_SESSION = 40

# ── Bucket definitions ─────────────────────────────────────────────────────────
# Five equal-width buckets covering the confidence range 50–100 %

BUCKETS = [
    {"label": "50–60%", "lo": 50, "hi": 60,  "midpoint": 55},
    {"label": "60–70%", "lo": 60, "hi": 70,  "midpoint": 65},
    {"label": "70–80%", "lo": 70, "hi": 80,  "midpoint": 75},
    {"label": "80–90%", "lo": 80, "hi": 90,  "midpoint": 85},
    {"label": "90–100%","lo": 90, "hi": 101, "midpoint": 95},  # hi=101 so 100 is included
]


def bucket_index(confidence: int) -> int:
    """Return the index (0–4) of the bucket that contains *confidence*."""
    for i, b in enumerate(BUCKETS):
        if b["lo"] <= confidence < b["hi"]:
            return i
    return len(BUCKETS) - 1  # clamp 100 into the last bucket


# ── Statistics helpers ─────────────────────────────────────────────────────────

def pearson_correlation(xs: list[float], ys: list[float]) -> float | None:
    """
    Return the Pearson correlation coefficient r for two equal-length lists.
    Returns None when the correlation is undefined (e.g. zero variance).
    """
    n = len(xs)
    if n < 2:
        return None

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n

    numerator   = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    variance_x  = sum((x - mean_x) ** 2 for x in xs)
    variance_y  = sum((y - mean_y) ** 2 for y in ys)

    if variance_x == 0 or variance_y == 0:
        return None

    return numerator / math.sqrt(variance_x * variance_y)


# ── Routes ─────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the single-page application."""
    return render_template("index.html")


@app.route("/api/questions")
def get_questions():
    """
    Return a JSON array of up to QUESTIONS_PER_SESSION randomly sampled
    questions for the requested topic.

    Query params:
      topic (str): one of general | global_health | animal_welfare | ai_development
    """
    topic = request.args.get("topic", "general")

    pool = [q for q in ALL_QUESTIONS if q["topic"] == topic]

    if not pool:
        return jsonify({"error": f"Unknown topic '{topic}'"}), 400

    # Sample without replacement; fall back to the full pool if it's small
    count = min(QUESTIONS_PER_SESSION, len(pool))
    selected = random.sample(pool, count)

    return jsonify(selected)


@app.route("/api/score", methods=["POST"])
def compute_score():
    """
    Accept the user's answers and return calibration data.

    Expected JSON body:
    {
      "answers": [
        {
          "question_id":    "gen_001",
          "user_answer":    true,
          "correct_answer": true,
          "confidence":     75
        },
        ...
      ]
    }

    Returns:
    {
      "score":            0.87 | null,
      "score_label":      "Good" | null,
      "score_message":    "...",
      "bucket_data":      [ { label, midpoint, avg_confidence, accuracy, count }, ... ],
      "overall_accuracy": 62.5,
      "total_questions":  40
    }
    """
    body = request.get_json(silent=True)
    if not body or "answers" not in body:
        return jsonify({"error": "Request must include an 'answers' array"}), 400

    answers: list[dict] = body["answers"]
    if not answers:
        return jsonify({"error": "Answers array is empty"}), 400

    # ── Accumulate per-bucket statistics ──────────────────────────────────────

    # Each bucket stores running totals for efficient single-pass aggregation
    counts    = [0] * len(BUCKETS)
    corrects  = [0] * len(BUCKETS)
    conf_sums = [0] * len(BUCKETS)

    total_correct = 0

    for ans in answers:
        confidence = int(ans.get("confidence", 75))
        user_answer    = ans.get("user_answer")
        correct_answer = ans.get("correct_answer")

        # Clamp confidence to valid range
        confidence = max(50, min(100, confidence))

        is_correct = user_answer == correct_answer
        if is_correct:
            total_correct += 1

        idx = bucket_index(confidence)
        counts[idx]    += 1
        corrects[idx]  += 1 if is_correct else 0
        conf_sums[idx] += confidence

    # ── Build per-bucket summary (only non-empty buckets) ─────────────────────

    bucket_data = []
    for i, b in enumerate(BUCKETS):
        if counts[i] == 0:
            continue  # skip empty buckets — no data to plot

        accuracy       = (corrects[i] / counts[i]) * 100
        avg_confidence = conf_sums[i] / counts[i]

        bucket_data.append({
            "label":          b["label"],
            "midpoint":       b["midpoint"],
            "avg_confidence": round(avg_confidence, 1),
            "accuracy":       round(accuracy, 1),
            "count":          counts[i],
        })

    # ── Calibration score (Pearson r) ─────────────────────────────────────────

    score = None
    score_label = None

    if len(bucket_data) < 3:
        score_message = (
            "Not enough variation in confidence levels to compute a score. "
            "Try using a wider range of confidence levels."
        )
    else:
        xs = [b["midpoint"]  for b in bucket_data]
        ys = [b["accuracy"]  for b in bucket_data]

        r = pearson_correlation(xs, ys)

        if r is None:
            score_message = (
                "Could not compute a calibration score — "
                "your accuracy was identical across all confidence buckets."
            )
        else:
            score = round(r, 2)

            if score >= 0.90:
                score_label   = "Excellent"
                score_message = "Excellent — your confidence closely tracks your accuracy."
            elif score >= 0.70:
                score_label   = "Good"
                score_message = "Good — you have a reasonable sense of what you know."
            elif score >= 0.50:
                score_label   = "Moderate"
                score_message = "Moderate — your confidence and accuracy are loosely related."
            else:
                score_label   = "Needs work"
                score_message = "Needs work — your confidence levels aren't tracking accuracy well."

    # ── Overall accuracy ───────────────────────────────────────────────────────

    overall_accuracy = round((total_correct / len(answers)) * 100, 1)

    return jsonify({
        "score":            score,
        "score_label":      score_label,
        "score_message":    score_message,
        "bucket_data":      bucket_data,
        "overall_accuracy": overall_accuracy,
        "total_questions":  len(answers),
    })


# ── Entry point ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    # debug=True enables auto-reload on code changes; disable for production
    app.run(debug=True, port=5000)
