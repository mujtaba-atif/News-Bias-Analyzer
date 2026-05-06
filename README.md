# 📰 News Bias Analyzer

A polished, beginner-friendly Python + Streamlit web application that lets you paste articles from multiple news sources on the same topic and automatically reveals differences in sentiment, tone, loaded language, and framing — powered by **Groq**.

---

## Features

| Feature | Detail |
|---|---|
| **Dynamic article inputs** | Add or remove article slots with one click; no fixed limit |
| **Load Sample Data** | Instant demo with two pre-loaded articles on minimum wage |
| **Sentiment Analysis** | TextBlob polarity score (−1 to +1) and subjectivity score |
| **Tone Analysis** | Groq describes writing style, objectivity level, and emotional intensity |
| **Loaded Language** | Groq identifies emotionally charged or politically biased words/phrases |
| **Framing Detection** | Groq identifies the primary lens (Economic, Political, Human Interest, etc.) |
| **Neutral Article Summary** | Groq writes a 2–3 sentence factual summary of each article |
| **Side-by-Side Comparison** | Charts, a comparison table, and Groq observations on wording/emphasis |
| **Balanced Final Summary** | Groq synthesises all viewpoints into a neutral narrative |
| **Key Takeaways** | Groq extracts what a critical reader should notice |

---

## Project Structure

```
News Bias Analyzer/
├── app.py              ← Streamlit UI (dynamic inputs, session state, tabs)
├── analyzer.py         ← Analysis logic (TextBlob + Groq via groq_utils)
├── groq_utils.py       ← Groq API wrapper (JSON mode, retry, GroqError)
├── sample_data.py      ← Pre-loaded demo articles
├── requirements.txt    ← Python dependencies
├── .gitignore          ← Keeps .env and caches out of git
├── README.md           ← This file
├── project_report.md   ← Detailed project write-up
└── ai_usage_report.md  ← AI tool usage documentation
```

---

## Setup & Installation

### Prerequisites
- Python **3.9** or newer
- A **Groq API key**

### 1. Get a Groq API key
Create an API key in your Groq account dashboard.

### 2. Clone or download the project
```bash
git clone <your-repo-url>
cd "News Bias Analyzer"
```

### 3. Create and activate a virtual environment
```bash
python3 -m venv venv

# macOS / Linux:
source venv/bin/activate
# Windows:
venv\Scripts\activate
```

### 4. Add your API key
Create a `.env` file in the project folder and add your key:
```
GROQ_API_KEY=...your_actual_key...
```
> `.env` is in `.gitignore` — it will never be committed to git.

### 5. Install dependencies
```bash
pip install -r requirements.txt
```

### 6. Download NLTK data (one-time, automatic)
NLTK corpora are downloaded automatically on first run. To do it manually:
```bash
python3 -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
```

---

## Running the App

```bash
streamlit run app.py
```

Your browser opens at `http://localhost:8501`.  
If the API key is missing the app shows a clear error with setup instructions.

---

## How to Use

1. **Enter the topic** — the subject all articles cover (e.g., "Minimum Wage Increase")
2. **Paste articles** — click **＋ Add Article** to add slots; paste body text in each
3. Click **🔎 Analyze Articles**
4. Explore the three result tabs:
   - **📊 Individual Analysis** — per-article sentiment, summary, tone, framing, loaded language, key sentences
   - **⚖️ Side-by-Side Comparison** — charts, comparison table, wording/emphasis observations, loaded words grid
   - **📝 Summary & Takeaways** — balanced narrative, key takeaways, agreements, and differences

> **Quick demo:** Click **📋 Load Sample Data** to pre-fill two articles on the federal minimum wage debate, then click **Analyze Articles**.

---

## How It Works

### TextBlob (offline, instant)
- **Polarity score** (−1 to +1): how positive or negative the overall text is
- **Subjectivity score** (0 to 1): how fact-based vs. opinion-based
- **Key sentences**: the sentences with the highest absolute polarity

### Groq (AI, ~5–15 seconds)
The app makes **one** Groq call per analysis. The model returns strict JSON that includes:
- Per-article tone, loaded language, framing, and a neutral short summary
- Cross-source comparison (wording/emphasis/agreements + a side-by-side table)
- A balanced 3–4 paragraph narrative summary + takeaways

Results are cached with `st.cache_data`, so Streamlit reruns/tab switches do not repeat API calls unless topic or article text changes.

---

## Dependencies

| Package | Purpose |
|---|---|
| `streamlit` | Web UI framework |
| `textblob` | Offline sentiment analysis |
| `nltk` | Tokenisation, stop-word filtering |
| `groq` | Groq API client |
| `python-dotenv` | Load `GROQ_API_KEY` from `.env` |
| `pandas` | Comparison table DataFrame |

---

## Troubleshooting

| Problem | Fix |
|---|---|
| *GROQ_API_KEY not found* | Create `.env` and add your key |
| *Groq API error* | Wait ~1 minute and retry if rate-limited |
| *NLTK data not found* | Run `python3 -c "import nltk; nltk.download('all')"` |
| *Module not found* | Activate the venv and run `pip install -r requirements.txt` |
| *Results disappear on click* | Results are stored in session state — they persist; try re-analyzing |

---

## License

MIT — free to use and modify for educational purposes.
