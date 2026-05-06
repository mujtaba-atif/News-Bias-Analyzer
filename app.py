"""
app.py — Streamlit UI for the News Bias Analyzer.

Run with:
    streamlit run app.py

Requires a .env file in the project folder:
    GROQ_API_KEY=your_key_here
"""

import os
import uuid

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# ── 1. Load .env and validate API key ───────────────────────────────────────
load_dotenv()

if not os.getenv("GROQ_API_KEY"):
    st.set_page_config(page_title="News Bias Analyzer", page_icon="📰", layout="wide")
    st.error(
        "**GROQ_API_KEY not found.**\n\n"
        "Create a `.env` file in the project folder with:\n\n"
        "```\nGROQ_API_KEY=your_key_here\n```\n\n"
        "Then restart with `streamlit run app.py`."
    )
    st.stop()

import analyzer
from groq_utils import GroqError, get_debug_info, test_connection

# ── 2. Page config ───────────────────────────────────────────────────────────
st.set_page_config(
    page_title="News Bias Analyzer",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": None,
    },
)

# ── 3. Custom CSS ────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Hide Streamlit chrome (best-effort; Streamlit may change testids) */
header { visibility: hidden; height: 0px; }
footer { visibility: hidden; height: 0px; }
#MainMenu { visibility: hidden; }
[data-testid="stToolbar"] { visibility: hidden; height: 0px; }
[data-testid="stDeployButton"] { display: none !important; }

/* Palette */
:root {
  --bg: #f6f7fb;
  --bg-gradient: radial-gradient(1200px circle at 15% 0%, rgba(47, 111, 237, 0.12) 0%, rgba(47, 111, 237, 0.00) 55%),
                 linear-gradient(180deg, #f6f7fb 0%, #eef2ff 100%);
  --surface: #ffffff;
  --surface-2: #fbfcfe;
  --border: #e6e8f0;
  --border-2: #d8dbe7;
  --text: #0f172a;
  --muted: #475569;
  --accent: #2f6fed;     /* consistent blue accent */
  --accent-2: #1e5ae6;
  --shadow: 0 1px 2px rgba(15, 23, 42, 0.06);
}

/* Page background */
html, body {
  background: var(--bg-gradient) !important;
}
.stApp {
  background: var(--bg-gradient) !important;
}
[data-testid="stAppViewContainer"] {
  background: var(--bg-gradient);
}

.main .block-container { padding-top: 1.4rem; padding-bottom: 3rem; max-width: 1200px; }

/* Sidebar styling */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #ffffff 0%, #f2f4fb 100%);
  border-right: 1px solid var(--border);
}
[data-testid="stSidebar"] .block-container {
  padding-top: 1.25rem;
}

/* Make dividers subtle */
hr {
  border-color: var(--border);
}

/* Soft "card" look for bordered containers */
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--border);
  border-radius: 12px;
  box-shadow: var(--shadow);
  backdrop-filter: blur(6px);
  padding: 0.25rem 0.25rem 0.75rem 0.25rem;
}

/* Metrics cards */
div[data-testid="metric-container"] {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 0.65rem 0.9rem;
    box-shadow: var(--shadow);
}

/* Buttons: give primary a consistent accent */
button[kind="primary"] {
  background: var(--accent) !important;
  border: 1px solid var(--accent-2) !important;
}
button[kind="primary"]:hover {
  background: var(--accent-2) !important;
}

/* Expanders */
details > summary { font-weight: 600; }

/* Typography tweaks */
.stCaption, .stMarkdown p { color: var(--muted); }
</style>
""", unsafe_allow_html=True)

# ── 4. Display helpers ────────────────────────────────────────────────────────

_SENTIMENT_EMOJI = {"Positive": "🟢", "Negative": "🔴", "Neutral": "🟡"}


def _polarity_bar(score: float) -> str:
    filled = int((score + 1) / 2 * 10)
    return f"`{'█' * filled}{'░' * (10 - filled)}`  {score:+.3f}"


def _subjectivity_label(score: float) -> str:
    if score > 0.6:
        return "Mostly Opinion"
    if score > 0.35:
        return "Mixed (Fact + Opinion)"
    return "Mostly Factual"


def _show_debug_expander(err: GroqError) -> None:
    """Render an expandable debug section after a GroqError."""
    with st.expander("🔧 API Debug Info"):
        info = get_debug_info()
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Key present:** {info['key_present']}")
            st.markdown(f"**Key length:** {info['key_length']}")
            st.markdown(f"**Key preview:** `{info['key_preview']}`")
            st.markdown(f"**Model:** `{info['model_name']}`")
        with col2:
            st.markdown(f"**SDK:** {info['sdk_package']}")
            st.markdown(f"**Client ready:** {info['client_ready']}")
            if info.get("client_init_error"):
                st.markdown(f"**Init error:** {info['client_init_error']}")
        if info["last_call_error"]:
            st.markdown("**Last error:**")
            st.code(info["last_call_error"])
        if err.raw_response:
            st.markdown("**Raw model response (first 500 chars):**")
            st.code(err.raw_response)


# ── 5. Session-state initialisation ──────────────────────────────────────────
if "articles" not in st.session_state:
    st.session_state.articles = [{"id": "init_0"}, {"id": "init_1"}]

if "results" not in st.session_state:
    st.session_state.results = None


# ── 6. Callbacks ──────────────────────────────────────────────────────────────

def _add_article() -> None:
    st.session_state.articles.append({"id": str(uuid.uuid4())[:8]})


def _remove_article(article_id: str) -> None:
    st.session_state.articles = [
        a for a in st.session_state.articles if a["id"] != article_id
    ]
    st.session_state.pop(f"src_{article_id}", None)
    st.session_state.pop(f"txt_{article_id}", None)
    st.session_state.results = None


def _load_sample() -> None:
    from sample_data import SAMPLE_ARTICLES, SAMPLE_TOPIC
    new_articles = []
    for i, art in enumerate(SAMPLE_ARTICLES):
        aid = f"sample_{i}"
        new_articles.append({"id": aid})
        st.session_state[f"src_{aid}"] = art["source"]
        st.session_state[f"txt_{aid}"] = art["text"]
    st.session_state.articles = new_articles
    st.session_state["topic_input"] = SAMPLE_TOPIC
    st.session_state.results = None


# ── 7. Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📰 News Bias Analyzer")
    st.caption("Paste 2+ articles on the same topic to compare framing and language.")
    st.divider()

    st.markdown(
        "**How to use**\n\n"
        "1. Enter the news topic.\n"
        "2. Paste article text for at least 2 sources.\n"
        "3. Click **Analyze Articles**.\n"
        "4. Explore the three result tabs.\n\n"
        "---\n"
        "**Tips**\n\n"
        "- Remove headlines, ads, and by-lines.\n"
        "- Longer articles → richer analysis.\n"
        "- Use **Load Sample Data** for a quick demo."
    )
    st.divider()


# ── 8. Main header ────────────────────────────────────────────────────────────
st.title("📰 News Bias Analyzer")
st.markdown(
    "Paste articles from different news sources on the **same topic** "
    "to reveal differences in sentiment, tone, loaded language, and framing — "
    "powered by **Groq**."
)
st.divider()


# ── 9. Step 1 — Topic ────────────────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Step 1 — Enter the News Topic")
    topic = st.text_input(
        "What topic do all your articles cover?",
        key="topic_input",
        placeholder="e.g., Minimum Wage Increase, Climate Policy, Tech Layoffs",
        label_visibility="collapsed",
    )
    st.divider()


# ── 10. Step 2 — Article inputs ───────────────────────────────────────────────
with st.container(border=True):
    st.subheader("Step 2 — Paste Article Texts")
    st.caption(
        "Add at least 2 articles. Copy only the body text — remove headlines, "
        "by-lines, and advertisements for best results."
    )

    st.write("")

    for art in st.session_state.articles:
        aid = art["id"]
        with st.container(border=True):
            src_col, rm_col = st.columns([6, 1])
            with src_col:
                st.text_input(
                    "Source name",
                    key=f"src_{aid}",
                    placeholder="e.g., CNN, Fox News, BBC, Reuters",
                    label_visibility="visible",
                )
            with rm_col:
                st.write("")
                st.button(
                    "✕ Remove",
                    key=f"rm_{aid}",
                    on_click=_remove_article,
                    args=(aid,),
                    use_container_width=True,
                )
            st.text_area(
                "Article body text",
                key=f"txt_{aid}",
                height=180,
                placeholder="Paste the full article body text here…",
                label_visibility="collapsed",
            )

    st.write("")

    add_col, sample_col, spacer_col = st.columns([1.4, 1.6, 3])
    with add_col:
        st.button("＋  Add Article", on_click=_add_article, use_container_width=True, type="secondary")
    with sample_col:
        st.button("📋  Load Sample Data", on_click=_load_sample, use_container_width=True, type="secondary")

    st.divider()


# ── 11. Analyze button ────────────────────────────────────────────────────────
analyze_clicked = st.button("🔎  Analyze Articles", type="primary", use_container_width=True)

@st.cache_data(show_spinner=False)
def _cached_full_analysis(topic: str, articles: tuple[tuple[str, str], ...]) -> dict:
    # Cached so reruns/tab switches don't re-call the API unless inputs change.
    return analyzer.run_full_analysis(topic, list(articles))

if analyze_clicked:
    if not topic.strip():
        st.error("Please enter a news topic before analyzing.")
        st.stop()

    valid = [
        (
            st.session_state.get(f"src_{a['id']}", "").strip(),
            st.session_state.get(f"txt_{a['id']}", "").strip(),
        )
        for a in st.session_state.articles
        if st.session_state.get(f"src_{a['id']}", "").strip()
        and len(st.session_state.get(f"txt_{a['id']}", "").strip()) > 50
    ]

    if len(valid) < 2:
        st.error(
            "Please provide at least **2 articles** — each needs a source name "
            "and body text longer than 50 characters."
        )
        st.stop()

    try:
        with st.spinner("Running AI analysis (1 Groq call total)…"):
            out = _cached_full_analysis(topic.strip(), tuple(valid))
            analyses = out["analyses"]
            comparison = out["comparison"]
            summary_data = out["summary_data"]

        st.session_state.results = {
            "topic": topic,
            "analyses": analyses,
            "comparison": comparison,
            "summary_data": summary_data,
        }

        st.success(
            f"✅  Full AI analysis complete — **{len(analyses)} articles** on **{topic}**"
        )

    except GroqError as e:
        st.session_state.results = None  # never show stale or partial results
        msg = str(e).strip()
        if msg == "Groq rate limit reached. Wait about 1 minute and try again.":
            st.error(msg)
        else:
            st.error(f"**Groq API error — analysis stopped.**\n\n{e}")
            _show_debug_expander(e)


# ── 12. Results ───────────────────────────────────────────────────────────────
if st.session_state.results:
    res          = st.session_state.results
    analyses     = res["analyses"]
    comparison   = res["comparison"]
    summary_data = res["summary_data"]
    rtopic       = res["topic"]

    st.divider()

    tab1, tab2, tab3 = st.tabs([
        "📊  Individual Analysis",
        "⚖️  Side-by-Side Comparison",
        "📝  Summary & Takeaways",
    ])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Individual Analysis
    # ════════════════════════════════════════════════════════════════════════
    with tab1:
        st.write("")

        for a in analyses:
            emoji = _SENTIMENT_EMOJI.get(a.sentiment_label, "⚪")
            header = f"{emoji}  {a.source_name}  ·  {a.sentiment_label}  ·  {a.word_count} content words"

            with st.expander(header, expanded=True):

                # Metric row
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Sentiment",    a.sentiment_label)
                c2.metric("Polarity",     f"{a.sentiment_score:+.3f}")
                c3.metric("Subjectivity", f"{a.subjectivity_score:.2f}")
                c4.metric("Word Count",   a.word_count)

                st.markdown(
                    f"Polarity bar &nbsp;(neg ← neutral → pos): "
                    f"&nbsp; {_polarity_bar(a.sentiment_score)}  "
                    f"· {_subjectivity_label(a.subjectivity_score)}"
                )

                st.divider()

                # 2-column compact layout for AI fields
                left, right = st.columns(2)

                with left:
                    st.markdown("**Neutral Summary**")
                    st.info(a.short_summary)
                    st.write("")
                    st.markdown("**Tone Analysis**")
                    st.write(a.tone)

                with right:
                    st.markdown("**Main Framing / Perspective**")
                    st.success(a.dominant_frame)
                    st.write("")
                    st.markdown("**Loaded / Emotional Language**")
                    if a.loaded_words:
                        st.markdown("  ".join(f"`{w}`" for w in a.loaded_words))
                    else:
                        st.caption("None detected.")

                st.divider()

                # Key sentences full-width
                st.markdown("**Strongest Emotional Sentences** *(TextBlob — highest absolute polarity)*")
                for sent in a.key_sentences:
                    st.markdown(f"> {sent}")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — Side-by-Side Comparison
    # ════════════════════════════════════════════════════════════════════════
    with tab2:
        st.write("")

        # Sentiment polarity chart — horizontal so source names are readable
        st.markdown("#### Sentiment Polarity by Source")
        st.caption("Range: −1 (very negative) to +1 (very positive).")
        sent_data = {src: d["score"] for src, d in comparison["sentiment_spread"].items()}
        st.bar_chart(sent_data, horizontal=True, height=max(180, len(analyses) * 60))
        for src, d in comparison["sentiment_spread"].items():
            e = _SENTIMENT_EMOJI.get(d["label"], "⚪")
            st.markdown(f"- **{src}**: {e} {d['label']} ({d['score']:+.3f})")

        st.divider()

        # Subjectivity chart — horizontal
        st.markdown("#### Subjectivity by Source")
        st.caption("0 = fully objective/factual  ·  1 = fully subjective/opinion.")
        st.bar_chart(comparison["subjectivity_spread"], horizontal=True, height=max(180, len(analyses) * 60))
        for src, val in comparison["subjectivity_spread"].items():
            st.markdown(f"- **{src}**: {val:.2f}  ({_subjectivity_label(val)})")

        st.divider()

        # Comparison table (AI)
        st.markdown("#### Side-by-Side Comparison Table")
        table_rows = comparison.get("table_rows", [])
        if table_rows:
            sources = [a.source_name for a in analyses]
            rows = []
            for row in table_rows:
                entry = {"Aspect": row.get("aspect", "?")}
                vals  = row.get("values", [])
                for i, src in enumerate(sources):
                    entry[src] = vals[i] if i < len(vals) else "—"
                rows.append(entry)
            df = pd.DataFrame(rows).set_index("Aspect")
            st.dataframe(df, use_container_width=True)

        st.divider()

        # Wording & tone differences (AI)
        st.markdown("#### Wording & Tone Differences")
        for obs in comparison.get("wording_differences", []):
            st.warning(obs)

        st.divider()

        # Emphasis & framing differences
        st.markdown("#### Emphasis & Framing Differences")
        for obs in comparison.get("emphasis_notes", []):
            st.info(obs)
        st.markdown("**Primary frame per source:**")
        for src, frame in comparison["framing_spread"].items():
            st.markdown(f"- **{src}**: {frame}")

        st.divider()

        # Loaded language per source
        st.markdown("#### Loaded Language per Source")
        st.caption("Words and phrases flagged by the AI in each article.")
        word_cols = st.columns(len(analyses))
        for col, a in zip(word_cols, analyses):
            with col:
                st.markdown(f"**{a.source_name}**")
                if a.loaded_words:
                    for w in a.loaded_words:
                        st.markdown(f"- `{w}`")
                else:
                    st.caption("None detected.")

        st.divider()

        # Where sources agree
        st.markdown("#### Where Sources Agree")
        for ag in comparison.get("agreements", []):
            st.success(ag)

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Summary & Takeaways
    # ════════════════════════════════════════════════════════════════════════
    with tab3:
        st.write("")

        # Balanced narrative summary
        st.markdown(f"#### Balanced Summary: *{rtopic}*")
        summary_text = summary_data.get("summary", "")
        if summary_text:
            for para in summary_text.strip().split("\n\n"):
                st.write(para.strip())
                st.write("")

        st.divider()

        left_col, right_col = st.columns(2)

        with left_col:
            st.markdown("#### Key Takeaways")
            for t in summary_data.get("key_takeaways", []):
                st.markdown(f"- {t}")
            st.write("")
            st.markdown("#### Where Sources Agree")
            for ag in summary_data.get("agreements", []):
                st.success(ag)

        with right_col:
            st.markdown("#### Where Sources Differ")
            for d in summary_data.get("differences", []):
                st.warning(d)
