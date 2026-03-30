import streamlit as st

from src.config import DEFAULT_CHAT_MODEL, build_runtime_config, validate_api_keys
from src.evolution.registry import load_active_config
from src.runtime import run_research


def inject_styles():
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&family=Source+Sans+3:wght@400;600&display=swap');

        :root {
            --bg: #f6f1e8;
            --surface: rgba(255, 252, 247, 0.86);
            --surface-strong: #fffaf2;
            --border: rgba(108, 77, 40, 0.16);
            --text: #1f1a17;
            --muted: #6f6258;
            --accent: #d76831;
            --accent-2: #ffb36a;
            --accent-3: #1d7f7a;
            --shadow: 0 24px 60px rgba(82, 53, 24, 0.12);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(255, 190, 130, 0.34), transparent 28%),
                radial-gradient(circle at top right, rgba(43, 155, 147, 0.18), transparent 24%),
                linear-gradient(180deg, #fcf7ef 0%, #f4ede1 48%, #efe6d8 100%);
            color: var(--text);
            font-family: "Source Sans 3", sans-serif;
        }

        h1, h2, h3, h4, .hero-title {
            font-family: "Space Grotesk", sans-serif !important;
            color: var(--text);
            letter-spacing: -0.02em;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, rgba(255,250,242,0.95), rgba(250,242,230,0.92));
            border-right: 1px solid var(--border);
        }

        [data-testid="stSidebar"] * {
            color: var(--text);
        }

        .block-container {
            padding-top: 2rem;
            padding-bottom: 3rem;
        }

        .hero-shell {
            position: relative;
            overflow: hidden;
            background: linear-gradient(135deg, rgba(255,250,244,0.95), rgba(255,239,213,0.92));
            border: 1px solid rgba(140, 100, 50, 0.16);
            box-shadow: var(--shadow);
            border-radius: 28px;
            padding: 2rem 2rem 1.6rem 2rem;
            margin-bottom: 1.25rem;
            animation: fadeUp 0.8s ease-out;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -40px -60px auto;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(215,104,49,0.18), transparent 62%);
            filter: blur(8px);
        }

        .eyebrow {
            display: inline-block;
            padding: 0.35rem 0.7rem;
            border-radius: 999px;
            background: rgba(29, 127, 122, 0.1);
            color: var(--accent-3);
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
            font-size: 0.73rem;
            margin-bottom: 0.9rem;
        }

        .hero-title {
            font-size: clamp(2.1rem, 4vw, 3.6rem);
            line-height: 0.95;
            margin: 0 0 0.8rem 0;
        }

        .hero-copy {
            max-width: 760px;
            font-size: 1.06rem;
            color: var(--muted);
            line-height: 1.6;
            margin-bottom: 1.25rem;
        }

        .hero-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
        }

        .metric-card, .glass-card, .source-card, .empty-card {
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 22px;
            box-shadow: 0 12px 30px rgba(60, 39, 17, 0.08);
            backdrop-filter: blur(8px);
        }

        .metric-card {
            padding: 1rem 1rem 0.95rem 1rem;
        }

        .metric-label {
            color: var(--muted);
            font-size: 0.82rem;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            margin-bottom: 0.35rem;
            font-weight: 700;
        }

        .metric-value {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.35rem;
            font-weight: 700;
            color: var(--text);
        }

        .section-title {
            font-family: "Space Grotesk", sans-serif;
            font-size: 1.1rem;
            font-weight: 700;
            margin: 0 0 0.75rem 0;
            color: var(--text);
        }

        .glass-card {
            padding: 1rem 1.05rem;
            margin-bottom: 1rem;
            animation: fadeUp 0.7s ease-out;
        }

        .source-card {
            padding: 1rem 1rem 0.9rem 1rem;
            margin-bottom: 0.85rem;
            transition: transform 0.25s ease, box-shadow 0.25s ease;
        }

        .source-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 18px 36px rgba(60, 39, 17, 0.12);
        }

        .source-index {
            font-family: "Space Grotesk", sans-serif;
            color: var(--accent);
            font-size: 0.85rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            text-transform: uppercase;
            margin-bottom: 0.3rem;
        }

        .source-title {
            font-weight: 700;
            font-size: 1.05rem;
            margin-bottom: 0.35rem;
        }

        .source-snippet {
            color: var(--muted);
            line-height: 1.55;
            margin-bottom: 0.5rem;
        }

        .source-url a {
            color: var(--accent-3) !important;
            text-decoration: none;
            word-break: break-word;
        }

        .empty-card {
            padding: 1.35rem;
            color: var(--muted);
            margin-top: 0.5rem;
        }

        .log-line {
            padding: 0.72rem 0.9rem;
            border-left: 3px solid rgba(215, 104, 49, 0.52);
            margin-bottom: 0.55rem;
            background: rgba(255, 251, 246, 0.75);
            border-radius: 0 14px 14px 0;
        }

        .hint-list {
            margin: 0;
            padding-left: 1.1rem;
            color: var(--muted);
        }

        .stButton > button, .stDownloadButton > button {
            border-radius: 999px;
            border: 0 !important;
            background: linear-gradient(135deg, var(--accent), #ef8a49) !important;
            color: white !important;
            font-family: "Space Grotesk", sans-serif !important;
            font-weight: 700 !important;
            padding: 0.8rem 1.2rem !important;
            box-shadow: 0 14px 28px rgba(215, 104, 49, 0.24);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }

        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 18px 32px rgba(215, 104, 49, 0.28);
        }

        .stTextArea textarea, .stTextInput input {
            border-radius: 18px !important;
            border: 1px solid var(--border) !important;
            background: rgba(255, 251, 245, 0.95) !important;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 0.5rem;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            background: rgba(255, 248, 238, 0.78);
            border: 1px solid var(--border);
            padding: 0.5rem 1rem;
            font-family: "Space Grotesk", sans-serif;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, rgba(215,104,49,0.18), rgba(255,179,106,0.3));
        }

        @keyframes fadeUp {
            from {
                opacity: 0;
                transform: translateY(12px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        @media (max-width: 900px) {
            .hero-grid {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_hero(active_config):
    st.markdown(
        f"""
        <section class="hero-shell">
            <div class="eyebrow">Autonomous Research Studio</div>
            <div class="hero-title">Turn rough questions into polished research reports.</div>
            <div class="hero-copy">
                Plan the investigation, search the web, critique coverage gaps, and generate a
                citation-backed report through a self-improving multi-step agent workflow.
            </div>
            <div class="hero-grid">
                <div class="metric-card">
                    <div class="metric-label">Active Config</div>
                    <div class="metric-value">{active_config["version"]}</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Search Depth</div>
                    <div class="metric-value">{active_config["search_results_per_query"]} results/query</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">Max Rounds</div>
                    <div class="metric-value">{active_config["max_rounds"]} research passes</div>
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_sources(sources):
    if not sources:
        st.markdown(
            '<div class="empty-card">No sources were collected for this run yet.</div>',
            unsafe_allow_html=True,
        )
        return

    for idx, source in enumerate(sources, start=1):
        st.markdown(
            f"""
            <div class="source-card">
                <div class="source-index">Source {idx}</div>
                <div class="source-title">{source["title"]}</div>
                <div class="source-snippet">{source["snippet"]}</div>
                <div class="source-url"><a href="{source["url"]}" target="_blank">{source["url"]}</a></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_logs(logs):
    if not logs:
        st.markdown(
            '<div class="empty-card">Execution logs will appear here after a run.</div>',
            unsafe_allow_html=True,
        )
        return

    for line in logs:
        st.markdown(f'<div class="log-line">{line}</div>', unsafe_allow_html=True)


def render_summary(result):
    sources = result.get("sources", [])
    findings = result.get("findings", [])
    critique = result.get("critique", {})

    col1, col2, col3, col4 = st.columns(4)
    metrics = [
        ("Sources", len(sources)),
        ("Findings", len(findings)),
        ("Missing Points", len(critique.get("missing_points", []))),
        ("Extra Queries", len(critique.get("extra_queries", []))),
    ]

    for col, (label, value) in zip((col1, col2, col3, col4), metrics):
        with col:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">{label}</div>
                    <div class="metric-value">{value}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_empty_state():
    st.markdown(
        """
        <div class="glass-card">
            <div class="section-title">How To Use This Workspace</div>
            <ul class="hint-list">
                <li>Enter a research topic or decision question in the prompt area.</li>
                <li>Pick the NVIDIA model you want to use from the sidebar.</li>
                <li>Run the pipeline to generate a plan, critique, source list, and final report.</li>
            </ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    st.set_page_config(page_title="Advanced Research Agent", layout="wide")
    inject_styles()

    active_config = load_active_config()
    render_hero(active_config)

    if "last_result" not in st.session_state:
        st.session_state["last_result"] = None

    with st.sidebar:
        st.markdown("### Control Panel")
        st.caption("Tune the model, then launch the research workflow.")
        model_name = st.text_input("NVIDIA chat model", value=DEFAULT_CHAT_MODEL)
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Pipeline</div>
                <div style="color:#6f6258; line-height:1.6;">
                    Memory -> Plan -> Research -> Critique -> Write
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
            <div class="glass-card">
                <div class="section-title">Live Config</div>
                <div style="color:#6f6258; line-height:1.7;">
                    <strong>Version:</strong> {active_config["version"]}<br/>
                    <strong>Search results/query:</strong> {active_config["search_results_per_query"]}<br/>
                    <strong>Max rounds:</strong> {active_config["max_rounds"]}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    left, right = st.columns([1.5, 1])
    with left:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">Research Prompt</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        topic = st.text_area(
            "Enter a research topic",
            label_visibility="collapsed",
            height=180,
            placeholder="Example: Compare the latest open-source and closed-source LLM observability platforms for small engineering teams.",
        )
        run_clicked = st.button("Run Full Pipeline", type="primary")

    with right:
        st.markdown(
            """
            <div class="glass-card">
                <div class="section-title">What You Get</div>
                <ul class="hint-list">
                    <li>A structured research plan</li>
                    <li>Deduplicated search sources</li>
                    <li>Gap analysis and follow-up queries</li>
                    <li>A final markdown report with references</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if run_clicked:
        if not topic.strip():
            st.warning("Please enter a topic.")
            return

        runtime_config = build_runtime_config(
            chat_model=model_name,
            search_results_per_query=active_config["search_results_per_query"],
            max_rounds=active_config["max_rounds"],
        )

        if not validate_api_keys(runtime_config):
            st.error("Missing NVIDIA_API_KEY or SERPAPI_API_KEY in your .env file.")
            return

        with st.spinner("Running research workflow..."):
            try:
                result = run_research(
                    topic=topic,
                    runtime_config=runtime_config,
                    agent_config=active_config,
                    evaluation_mode=False,
                )
            except Exception as exc:
                st.session_state["last_result"] = None
                st.error(f"Research run failed: {exc}")
                st.info(
                    "Check your NVIDIA and SerpAPI credentials, selected model name, and network/API availability."
                )
                return

            st.session_state["last_result"] = result

    result = st.session_state.get("last_result")

    if result:
        render_summary(result)
        tabs = st.tabs(["Final Report", "Plan", "Critique", "Sources", "Logs"])

        with tabs[0]:
            st.markdown(
                """
                <div class="glass-card">
                    <div class="section-title">Generated Report</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown(result.get("report", "No report generated."))
            st.download_button(
                "Download report",
                data=result.get("report", ""),
                file_name="research_report.md",
                mime="text/markdown",
            )

        with tabs[1]:
            st.json(result.get("plan", {}))

        with tabs[2]:
            st.json(result.get("critique", {}))

        with tabs[3]:
            render_sources(result.get("sources", []))

        with tabs[4]:
            render_logs(result.get("logs", []))
    else:
        render_empty_state()


if __name__ == "__main__":
    main()
