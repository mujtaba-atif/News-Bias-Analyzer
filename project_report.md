# Project Report — News Bias Analyzer

**Course:** CS 485  
**Author:** Mujtaba Atif  
**Date:** May 2026  

---

## 1. Project Overview

The **News Bias Analyzer** is a Python + Streamlit web application that lets users paste articles from multiple news sources on the same topic and receive an automated, AI-powered analysis of how those sources differ in sentiment, tone, loaded language, framing, and emphasis.

The project demonstrates that meaningful media-bias analysis is achievable with lightweight, well-documented tools — no GPU, no fine-tuned model, no academic dataset required.

---

## 2. Problem Statement

Readers frequently encounter the same event reported in starkly different ways. A protest becomes a "demonstration" in one outlet and a "riot" in another. An economic policy is either a "relief package" or a "spending spree." These choices are not accidental — they reflect editorial bias, audience targeting, and ideological framing.

> *How can we automatically quantify and explain media bias in a way that is accessible to a general audience?*

---

## 3. Architecture

```
app.py  (Streamlit UI)
    │
    ├── session state   (dynamic article list, analysis results)
    │
    └── analyzer.py     (orchestration layer)
            │
            ├── TextBlob            (offline: sentiment + key sentences)
            ├── NLTK                (offline: tokenisation, stop-words)
            └── groq_utils.py       (Groq AI: all other analysis)
                    │
                    └── Groq API
```

### Module responsibilities

| File | Responsibility |
|---|---|
| `app.py` | UI layout, session state, callbacks, result display |
| `analyzer.py` | Orchestrates TextBlob + Groq; owns `ArticleAnalysis` dataclass |
| `groq_utils.py` | Groq client, strict JSON mode, retry logic, debug info |
| `sample_data.py` | Pre-written demo articles |

---

## 4. Key Technical Decisions

### 4.1 Groq with strict JSON output

The most significant technical decision in this project was forcing the AI model to return **strict JSON** and validating it before showing any results. This prevents partial/broken UI states and makes failures easy to handle (single clear error, no "unavailable" sections).

### 4.2 Separation of TextBlob and Groq

TextBlob handles the numeric sentiment values (polarity score, subjectivity) for two reasons:
1. **Speed** — no network call needed
2. **Reproducibility** — the same text always produces the same score, which makes the bar charts stable and trustworthy

Groq handles everything that benefits from natural-language reasoning: tone description, identifying loaded phrases in context, framing analysis, and generating human-readable comparisons and summaries.

### 4.3 Session State for Persistent Results

Streamlit re-executes the entire script on every user interaction. Without `st.session_state`, analysis results would disappear every time the user clicked a tab or typed in a field. Results are stored in `st.session_state.results` immediately after analysis completes, so they persist across all subsequent interactions.

In addition, the app uses `st.cache_data` so reruns/tab switches do not repeat the API call unless the topic or article text changes.

### 4.4 Dynamic Article Management

Rather than a fixed slider (the original approach), articles are managed as a list of ID-keyed dicts in session state. Each article's text lives in `st.session_state[f"src_{id}"]` and `st.session_state[f"txt_{id}"]`, which Streamlit populates automatically from the widget values. This allows add/remove operations without re-running the analysis, and makes the "Load Sample Data" feature straightforward — it sets those keys directly.

---

## 5. Analysis Pipeline

### 5.1 Offline analysis (TextBlob + NLTK)
For each article, the app computes locally:
- **sentiment_label** — Positive / Negative / Neutral (from polarity)
- **sentiment_score** — polarity float, −1 to +1
- **subjectivity_score** — 0 to 1
- **key_sentences** — 3 sentences with highest absolute polarity

### 5.2 Single AI call (Groq)
For each analysis run, the app makes **one** Groq API call that returns strict JSON with:
- Per-article: **tone**, **loaded_words**, **framing**, **short_summary**
- Cross-article: **wording_differences**, **emphasis_notes**, **agreements**, and a 5-row **table_rows** comparison table
- Final synthesis: a balanced **summary**, **key_takeaways**, **agreements**, and **differences**

---

## 6. User Experience Decisions

- **Progressive disclosure** — results only appear after clicking **Analyze Articles**, not on every keystroke
- **Progress feedback** — a progress bar and status message update for each article being analysed
- **Load Sample Data** — makes the demo immediate; no manual copy-pasting required for evaluation
- **Container borders** — `st.container(border=True)` visually separates article inputs
- **No partial results** — if the API or JSON parsing fails, the analysis stops and the UI shows one clear error; no broken sections are displayed

---

## 7. Limitations & Future Work

| Limitation | Potential improvement |
|---|---|
| TextBlob negation handling is basic ("not great" reads as positive) | Replace with a fine-tuned transformer (e.g., cardiffnlp/roberta-base-sentiment) |
| AI output can be inconsistent | Add stronger JSON schema validation and stricter constraints in prompts |
| No article fetching — user must paste text | Integrate a news API (NewsAPI, GDELT) with BeautifulSoup scraping |
| API rate limits | Add request queuing with longer back-off for bulk analysis |
| English-only | Add language detection + multilingual model support |

---

## 8. Conclusion

The News Bias Analyzer demonstrates that combining lightweight NLP libraries (TextBlob, NLTK) with a modern LLM API (Groq) produces a tool that is more capable than either approach alone. TextBlob provides fast, stable numeric scores for charts; the LLM provides nuanced contextual analysis (tone, framing, loaded language, and synthesis) that rule-based systems cannot match. Enforcing strict JSON output and validating it before rendering results are the key reliability improvements.
