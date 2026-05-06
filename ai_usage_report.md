# AI Usage Report — News Bias Analyzer

**Course:** CS 485  
**Author:** Mujtaba Atif  
**Date:** May 2026  

---

## 1. Purpose of This Report

This document provides a complete and honest account of every AI tool used during the development of the News Bias Analyzer, consistent with the academic integrity expectations of CS 485.

---

## 2. AI Tools Used

| Tool | Provider | Role |
|---|---|---|
| **Claude Sonnet** (claude-sonnet-4-6) | Anthropic | Code generation, architecture design, debugging, documentation |
| **Groq** (LLM API) | Groq | Runtime feature inside the finished app (tone, framing, loaded language, comparison, summary) |

---

## 3. Development Use — Claude

### 3.1 Architecture Design
Claude was used to design the multi-module architecture: separating `groq_utils.py` (API wrapper), `analyzer.py` (analysis logic), `sample_data.py` (demo content), and `app.py` (UI). The key decisions — strict JSON output, session state for persistent results, dynamic article management via UUID-keyed dicts — came from this architectural discussion.

**Prompt used (paraphrased):**  
*"Refactor a Streamlit news bias analyzer to use a cleaner multi-file structure, fix JSON parse errors from the LLM, add dynamic article adding/removing with session state, and add a Load Sample Data button."*

### 3.2 Code Generation
Claude generated the implementations of:

- `groq_utils.py` — the Groq client wrapper, strict JSON mode, retry/back-off logic, and multi-strategy extraction fallback
- `analyzer.py` — the `ArticleAnalysis` dataclass, all analysis functions, and the structured AI prompts
- `app.py` — the session-state-based dynamic article system, the callback functions (`_add_article`, `_remove_article`, `_load_sample`), the progress bar during analysis, and the results display across three tabs
- `sample_data.py` — the two demo articles (Wall Street Journal style and Guardian style) on the minimum wage topic

### 3.3 Debugging
Claude diagnosed the root cause of earlier API/JSON failures: the model sometimes returned markdown code fences or extra text that broke `json.loads`. The fix was twofold:
1. Force JSON-only output via the API when supported
2. Keep a multi-strategy fallback parser (`strip fences → find first {...} block`) as a safety net

### 3.4 Documentation
The `README.md`, `project_report.md`, and `ai_usage_report.md` were drafted by Claude and reviewed and edited by me for accuracy, completeness, and appropriateness.

---

## 4. What I Did Myself

- **Reviewed all generated code** line by line and verified it matched the requirements
- **Tested the app end-to-end** with real news articles from CNN, Fox News, BBC, and Reuters on multiple topics
- **Validated the sample articles** — rewrote sections to make the framing difference more pronounced and the analysis more educational
- **Adjusted the AI prompts** — trimmed token usage by capping article text, and refined the `table_rows` structure after seeing inconsistent value arrays
- **Tested edge cases**: single article (should reject), very short text (should reject), rate limit (should retry and surface a clear message)
- **Made UX decisions** independently: the progress bar per article, the two-column layout for takeaways vs. differences, showing loaded words as inline code badges

---

## 5. Runtime AI Feature — Groq Inside the App

The app calls Groq at runtime on the user's behalf. This is a **product feature**, not a development tool. The call is documented in `groq_utils.py` and `analyzer.py`. The prompt purpose is:

| Function | Prompt purpose |
|---|---|
| `run_full_analysis()` | Single call that returns per-article analysis, cross-source comparison, and balanced summary |

All prompts are visible in `analyzer.py`. No prompt content is hidden or obfuscated.

---

## 6. API Key Security

The Groq API key is loaded exclusively from a `.env` file using `python-dotenv`. It is:
- Never printed, logged, or displayed in the UI
- Never committed to git (`.env` is in `.gitignore`)
- Never passed as a function argument (the client is configured once at module level in `groq_utils.py`)

---

## 7. Reflection

The most valuable aspect of using Claude for this project was not code generation per se, but the speed of iteration on architectural decisions. Problems that might take hours to diagnose (like JSON parse failures) were identified and fixed in minutes.

The most important lesson: AI-generated code requires genuine understanding before submission. Every function in this project was read, tested, and in many cases rewritten. The code that Claude generates is a strong starting point, not a finished product.

---

## 8. Academic Integrity Statement

All AI usage described in this report was conducted in accordance with course policies. No AI tool was used to complete graded assessments other than this project, answer exam questions, or misrepresent work as entirely my own without disclosure. This report is a complete and honest account of AI involvement in this project.
