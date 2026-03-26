# Uncertainty Calibration Trainer

A local web app for practising epistemic calibration — learning to match
your stated confidence to your actual accuracy.

---

## What is calibration, and why does it matter?

A well-calibrated person's confidence tracks reality. When they say "I'm
70% sure", they turn out to be correct roughly 70% of the time. Not 90%,
not 50% — 70%.

This matters for decision-making. Overconfident people take on bad bets;
underconfident people avoid good ones. Forecasters, scientists, and
effective altruists have studied calibration extensively because it is both
measurable and improvable with practice.

Julia Galef's book *Scout Mindset* (2021) frames calibration as the
foundation of honest, accurate thinking. The *scout* tries to map reality
correctly, whereas the *soldier* defends a pre-existing belief. This app
is a practical tool for developing the scout's habit of asking "how sure
am I, really?"

---

## Installation

```bash
pip install flask
```

Python 3.10 or later is recommended (the code uses `float | None` type
annotations).

---

## Running the app

```bash
python app.py
```

Then open **http://localhost:5000** in your browser.

Press `Ctrl+C` in the terminal to stop the server.

---

## How to use the app

1. **Choose a topic** on the welcome screen and press **Begin**.
2. For each of the 40 questions:
   - Read the statement and click **True** or **False**.
   - Drag the slider to your confidence level (50% = just guessing,
     100% = completely certain).
   - Click **Next**.
3. After 40 questions you'll see your **calibration curve** and **score**.

No feedback is given during the quiz — this avoids anchoring effects and
more closely mimics real-world forecasting.

---

## Interpreting your results

### Calibration curve

The chart plots your stated confidence (x-axis) against your actual
accuracy (y-axis) for each confidence bucket.

| Bucket | Stated confidence |
|--------|------------------|
| 50–60% | Low confidence   |
| 60–70% |                  |
| 70–80% |                  |
| 80–90% |                  |
| 90–100%| High confidence  |

**The diagonal dashed line** represents perfect calibration — if your dots
fall on this line, your confidence exactly predicts your accuracy.

- **Dots above the line** — you were *underconfident* in that range
  (you knew more than you thought).
- **Dots below the line** — you were *overconfident* (you were surer
  than your accuracy warranted).

Dot size reflects the number of responses in each bucket; larger dots
carry more evidential weight.

Dot colour encodes deviation from perfect calibration on a continuous
scale: near-perfect answers are shown in cool slate, and large deviations
shade progressively to red.

### Calibration score

The score is the **Pearson correlation** between your bucket midpoints
(55, 65, 75, 85, 95) and your actual accuracy in each bucket.

| Score   | Label       | Meaning                                              |
|---------|-------------|------------------------------------------------------|
| 0.90–1.00 | Excellent | Confidence closely tracks accuracy                  |
| 0.70–0.89 | Good      | Reasonable self-knowledge                           |
| 0.50–0.69 | Moderate  | Loose relationship between confidence and accuracy  |
| < 0.50    | Needs work| Confidence is not a reliable signal                 |

A score requires at least 3 non-empty confidence buckets. If you always
choose a confidence near 75%, for example, all your answers fall in one
bucket and the correlation is undefined — try spreading your confidence
levels more.

---

## Adding custom questions

Questions are stored in `questions.json` as a JSON array. Each entry
follows this schema:

```json
{
  "id":          "gen_001",
  "topic":       "general",
  "question":    "The Nile is the longest river in the world.",
  "answer":      true,
  "source":      "optional citation",
  "placeholder": true
}
```

| Field         | Type    | Description                                              |
|---------------|---------|----------------------------------------------------------|
| `id`          | string  | Unique identifier (e.g. `gen_001`, `gh_042`)             |
| `topic`       | string  | `general`, `global_health`, `animal_welfare`, `ai_development` |
| `question`    | string  | The statement to evaluate — must be clearly true or false |
| `answer`      | boolean | `true` if the statement is correct, `false` otherwise    |
| `source`      | string  | Optional citation for fact-checking                      |
| `placeholder` | boolean | `true` on questions that haven't been verified yet       |

**Guidelines for good calibration questions:**

- State facts, not opinions or predictions.
- Avoid trick questions or statements that hinge on unusual definitions.
- Aim for a mix of true and false answers within each topic.
- The question should have a single, unambiguous correct answer.
- Remove or set `"placeholder": false` on questions once you've verified them.

The current question bank contains **placeholder questions only** — they
are marked `"placeholder": true` and labelled with `"source":
"placeholder — verify before use"`. Replace them with verified questions
before using the app for serious calibration training.

---

## Project structure

```
uncertainty-calibrater/
├── app.py           ← Flask backend (routes, scoring logic)
├── questions.json   ← Question bank (edit to add/replace questions)
├── templates/
│   └── index.html   ← Single-page frontend (HTML + CSS + JS)
└── README.md
```

---

## License

MIT — do whatever you like with it.
