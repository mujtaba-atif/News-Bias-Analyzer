"""
analyzer.py — Core analysis logic for News Bias Analyzer.

Responsibilities:
  TextBlob  → fast offline sentiment scoring (polarity + subjectivity)
              + extraction of highest-sentiment sentences
  Groq     → all AI-powered analysis via groq_utils in ONE call:
             per-article tone, loaded language, framing, short summary
             cross-article comparison, balanced final summary
"""

import string
from dataclasses import dataclass
from typing import Dict, List, Tuple

import nltk
from textblob import TextBlob

import groq_utils

# ── NLTK data (downloaded once, silent after first run) ─────────────────────
for _c in ["punkt", "punkt_tab", "stopwords", "averaged_perceptron_tagger"]:
    nltk.download(_c, quiet=True)

from nltk.corpus import stopwords as _sw
from nltk.tokenize import sent_tokenize, word_tokenize

_STOP_WORDS = set(_sw.words("english"))


# ── Data class ───────────────────────────────────────────────────────────────

@dataclass
class ArticleAnalysis:
    """All analysis results for a single article."""
    source_name: str
    text: str
    # ── TextBlob (offline) ──────────────────────────────────────────────────
    sentiment_label: str        # "Positive" | "Negative" | "Neutral"
    sentiment_score: float      # Polarity: -1.0 (very neg) → +1.0 (very pos)
    subjectivity_score: float   # 0.0 (objective) → 1.0 (subjective)
    word_count: int             # Content words, stop-words excluded
    key_sentences: List[str]    # Sentences with highest absolute polarity
    # ── AI (Groq) ──────────────────────────────────────────────────────────
    tone: str                   # Writing-style description
    loaded_words: List[str]     # Emotionally charged / biased words & phrases
    dominant_frame: str         # Primary perspective lens
    short_summary: str          # 2–3 sentence neutral factual summary


# ── TextBlob helpers (fast, no network) ─────────────────────────────────────

def _analyze_sentiment(text: str) -> Tuple[str, float, float]:
    """Return (label, polarity, subjectivity) using TextBlob."""
    blob = TextBlob(text)
    polarity = round(blob.sentiment.polarity, 3)
    subjectivity = round(blob.sentiment.subjectivity, 3)
    label = (
        "Positive" if polarity > 0.1
        else "Negative" if polarity < -0.1
        else "Neutral"
    )
    return label, polarity, subjectivity


def _key_sentences(text: str, n: int = 3) -> List[str]:
    """Return the n sentences with the highest absolute sentiment polarity."""
    sentences = sent_tokenize(text)
    if not sentences:
        return []
    return sorted(
        sentences,
        key=lambda s: abs(TextBlob(s).sentiment.polarity),
        reverse=True,
    )[:n]


# ── AI helpers (strict JSON validation) ──────────────────────────────────────

def _require_dict(d: object, *, name: str) -> dict:
    if not isinstance(d, dict):
        raise groq_utils.GroqError(f"Groq returned invalid JSON ({name} must be an object).")
    return d


def _require_list(v: object, *, name: str) -> list:
    if not isinstance(v, list):
        raise groq_utils.GroqError(f"Groq returned invalid JSON ({name} must be an array).")
    return v


def _require_str(v: object, *, name: str) -> str:
    if not isinstance(v, str) or not v.strip():
        raise groq_utils.GroqError(f"Groq returned invalid JSON ({name} must be a non-empty string).")
    return v.strip()


def _require_str_list(v: object, *, name: str) -> List[str]:
    arr = _require_list(v, name=name)
    out: List[str] = []
    for i, item in enumerate(arr):
        if isinstance(item, str) and item.strip():
            out.append(item.strip())
        else:
            raise groq_utils.GroqError(
                f"Groq returned invalid JSON ({name}[{i}] must be a non-empty string)."
            )
    return out


def _groq_full_analysis(topic: str, articles: List[Tuple[str, str]]) -> dict:
    """
    One Groq call for ALL AI content:
      - per-article tone / loaded language / framing / short summary
      - cross-source comparison
      - balanced summary & takeaways
    """
    blocks = []
    for i, (source, text) in enumerate(articles):
        blocks.append(
            f"ARTICLE {i + 1}\n"
            f"Source: {source}\n"
            f"Text (first 3000 chars):\n{text[:3000]}"
        )

    source_order = ", ".join(f"{i + 1}={src}" for i, (src, _) in enumerate(articles))

    prompt = f"""You are a neutral media-bias analyst and journalism educator.

Topic: "{topic}"
Analyze ALL of the following articles and return ONE JSON object.

Article order: {source_order}

{chr(10).join(blocks)}

Return a JSON object with exactly these top-level fields:

1) "articles": an array of exactly {len(articles)} objects in the SAME order as provided above.
   Each object must have exactly these fields:
   - "source_name": string (must match the given source name exactly)
   - "tone": string (1-2 sentences; objectivity/subjectivity, emotional intensity, slant)
   - "loaded_words": array of strings (0-15 items; words/phrases found verbatim in the text)
   - "framing": string (one sentence identifying the primary lens/perspective)
   - "short_summary": string (2-3 sentence neutral factual summary)

2) "comparison": an object with exactly these fields:
   - "wording_differences": array of 3-4 strings (specific observations; cite source names)
   - "emphasis_notes": array of 3-4 strings (what each source emphasizes; cite source names)
   - "agreements": array of 2-3 strings (facts all sources report similarly)
   - "table_rows": array of exactly 5 objects. Each object has:
       - "aspect": string (use these exactly: "Primary Framing", "Emotional Tone", "Key Emphasis", "Language Style", "Who Is Centered")
       - "values": array of exactly {len(articles)} strings, one per source in the order above (8-12 words each)

3) "summary": an object with exactly these fields:
   - "summary": string (3-4 paragraphs; plain prose; balanced and neutral)
   - "key_takeaways": array of 4-5 strings
   - "agreements": array of 2-3 strings
   - "differences": array of 3-4 strings
"""

    return groq_utils.call_json(prompt)


# ── Public API ───────────────────────────────────────────────────────────────

def _offline_article_rows(source_text_pairs: List[Tuple[str, str]]) -> List[dict]:
    """
    Offline analysis only (TextBlob + NLTK).
    """
    cleaned: List[Tuple[str, str]] = [(s.strip(), t.strip()) for s, t in source_text_pairs]
    offline_rows: List[dict] = []
    for source_name, text in cleaned:
        tokens = word_tokenize(text.lower())
        content_words = [
            t for t in tokens
            if t not in _STOP_WORDS and t not in string.punctuation
        ]
        label, polarity, subjectivity = _analyze_sentiment(text)
        offline_rows.append(
            {
                "source_name": source_name,
                "text": text,
                "sentiment_label": label,
                "sentiment_score": polarity,
                "subjectivity_score": subjectivity,
                "word_count": len(content_words),
                "key_sentences": _key_sentences(text),
            }
        )
    return offline_rows


def run_full_analysis(topic: str, source_text_pairs: List[Tuple[str, str]]) -> Dict[str, object]:
    """
    End-to-end analysis that uses exactly 1 Groq call total.
    """
    cleaned: List[Tuple[str, str]] = [(s.strip(), t.strip()) for s, t in source_text_pairs]
    offline_rows = _offline_article_rows(cleaned)

    g = _groq_full_analysis(topic.strip(), cleaned)
    g = _require_dict(g, name="response")
    g_articles = _require_list(g.get("articles"), name="articles")
    if len(g_articles) != len(cleaned):
        raise groq_utils.GroqError(
            f"Groq returned invalid JSON (articles length {len(g_articles)} != {len(cleaned)})."
        )

    analyses: List[ArticleAnalysis] = []
    for i, row in enumerate(offline_rows):
        ga = _require_dict(g_articles[i], name=f"articles[{i}]")
        src_expected = row["source_name"]
        src_returned = _require_str(ga.get("source_name"), name=f"articles[{i}].source_name")
        if src_returned != src_expected:
            raise groq_utils.GroqError(
                "Groq returned invalid JSON (source_name mismatch). "
                f"Expected '{src_expected}', got '{src_returned}'."
            )

        analyses.append(
            ArticleAnalysis(
                source_name=row["source_name"],
                text=row["text"],
                sentiment_label=row["sentiment_label"],
                sentiment_score=row["sentiment_score"],
                subjectivity_score=row["subjectivity_score"],
                word_count=row["word_count"],
                key_sentences=row["key_sentences"],
                tone=_require_str(ga.get("tone"), name=f"articles[{i}].tone"),
                loaded_words=_require_str_list(ga.get("loaded_words", []), name=f"articles[{i}].loaded_words"),
                dominant_frame=_require_str(ga.get("framing"), name=f"articles[{i}].framing"),
                short_summary=_require_str(ga.get("short_summary"), name=f"articles[{i}].short_summary"),
            )
        )

    # Build comparison object: numeric spreads computed locally; narrative from AI output
    comp = _require_dict(g.get("comparison"), name="comparison")
    comparison: Dict = {
        "sentiment_spread": {},
        "subjectivity_spread": {},
        "framing_spread": {},
        "wording_differences": _require_str_list(comp.get("wording_differences"), name="comparison.wording_differences"),
        "emphasis_notes": _require_str_list(comp.get("emphasis_notes"), name="comparison.emphasis_notes"),
        "agreements": _require_str_list(comp.get("agreements"), name="comparison.agreements"),
        "table_rows": _require_list(comp.get("table_rows"), name="comparison.table_rows"),
    }
    for a in analyses:
        comparison["sentiment_spread"][a.source_name] = {"label": a.sentiment_label, "score": a.sentiment_score}
        comparison["subjectivity_spread"][a.source_name] = a.subjectivity_score
        comparison["framing_spread"][a.source_name] = a.dominant_frame

    summ = _require_dict(g.get("summary"), name="summary")
    summary_data: Dict = {
        "summary": _require_str(summ.get("summary"), name="summary.summary"),
        "key_takeaways": _require_str_list(summ.get("key_takeaways"), name="summary.key_takeaways"),
        "agreements": _require_str_list(summ.get("agreements"), name="summary.agreements"),
        "differences": _require_str_list(summ.get("differences"), name="summary.differences"),
    }

    return {"analyses": analyses, "comparison": comparison, "summary_data": summary_data}
