from __future__ import annotations

from dataclasses import asdict

import streamlit as st

from unisolved.chat import ChatOrchestrator
from unisolved.config import load_settings


def main() -> None:
    settings = load_settings()
    st.set_page_config(page_title="UniSolved", page_icon="🎓", layout="wide")
    _inject_styles()
    _initialize_state()
    _render_top_navigation()

    if st.session_state.app_view == "landing":
        _render_landing_page(settings.live_mode_enabled, settings.gemini_model)
        return

    orchestrator = ChatOrchestrator(settings)
    campus, course_filter, language_filter = _render_sidebar(settings.live_mode_enabled)
    _render_chat_header(settings.live_mode_enabled, settings.gemini_model)
    prompt = _render_starter_prompts()

    for message in st.session_state.messages:
        _render_message(message)

    user_prompt = st.chat_input("Ask about classes, campus support, mentors, or food near campus.")
    if prompt:
        user_prompt = prompt

    if user_prompt:
        st.session_state.messages.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("Matching mentors and resources..."):
                reply = orchestrator.respond(
                    user_prompt,
                    selected_campus=campus,
                    sidebar_course=course_filter,
                    sidebar_language=language_filter,
                )
                message_payload = {
                    "role": "assistant",
                    "content": reply.answer,
                    "mode_label": reply.mode_label,
                    "mentor_matches": [_mentor_to_dict(match) for match in reply.mentor_matches],
                    "resource_matches": [asdict(match) for match in reply.resource_matches],
                    "citations": [asdict(citation) for citation in reply.citations],
                }
                st.session_state.messages.append(message_payload)
            _render_assistant_message(message_payload)


def _initialize_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "app_view" not in st.session_state:
        st.session_state.app_view = "landing"


def _render_top_navigation() -> None:
    st.markdown(
        """
        <div class="top-nav-shell">
            <div class="top-nav-brand">
                <div class="eyebrow">UniSolved</div>
                <div class="top-nav-title">Student support demo</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    overview_col, chat_col, _ = st.columns([1.1, 1.1, 5.8])
    with overview_col:
        if st.button(
            "Overview",
            key="nav_overview",
            use_container_width=True,
            type="primary" if st.session_state.app_view == "landing" else "secondary",
        ):
            _switch_view("landing")
    with chat_col:
        if st.button(
            "Chat Demo",
            key="nav_chat",
            use_container_width=True,
            type="primary" if st.session_state.app_view == "chat" else "secondary",
        ):
            _switch_view("chat")


def _switch_view(view_name: str) -> None:
    st.session_state.app_view = view_name
    st.rerun()


def _render_landing_page(live_mode_enabled: bool, gemini_model: str) -> None:
    mode_label = "Live Gemini mode" if live_mode_enabled else "Demo mode"
    st.markdown(
        f"""
        <div class="landing-shell">
            <div class="eyebrow">U of T student support assistant</div>
            <h1>UniSolved helps students go from "I'm stuck" to a concrete next step.</h1>
            <p class="hero-copy">
                The demo turns a single student question into a direct answer, curated campus resources,
                and demo mentor matches with fake contact details. It is designed to show how a support
                assistant can guide students without forcing them to navigate multiple campus sites first.
            </p>
            <div class="hero-meta landing-meta">
                <div class="mode-chip {'live' if live_mode_enabled else 'demo'}'>{mode_label}</div>
                <div class="model-chip">Model target: {gemini_model}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    launch_col, secondary_col, _ = st.columns([1.4, 1.4, 4.2])
    with launch_col:
        if st.button("Launch Chat Demo", key="landing_launch_demo", use_container_width=True, type="primary"):
            _switch_view("chat")
    with secondary_col:
        if st.button("Go To Prompts", key="landing_go_to_prompts", use_container_width=True):
            _switch_view("chat")

    st.markdown("### What UniSolved does")
    feature_cards = [
        (
            "Turns vague questions into action",
            "A student can type something messy like “I’m overwhelmed” or “I need help with CSC108” and still get a structured response.",
        ),
        (
            "Blends people and institutional support",
            "The demo combines upper-year mentor matches with official U of T resources, instead of treating those as separate workflows.",
        ),
        (
            "Keeps the demo grounded",
            "Mentors, restaurants, and campus resources come from seeded local data. Live mode is optional and only changes the answer text layer.",
        ),
    ]
    feature_columns = st.columns(3)
    for column, (title, description) in zip(feature_columns, feature_cards):
        with column:
            st.markdown(
                f"""
                <div class="info-card">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### How it works")
    flow_cards = [
        (
            "1. Ask one question",
            "The student describes an academic issue, support need, or food question in plain language.",
        ),
        (
            "2. UniSolved parses and ranks",
            "The app identifies the likely need, matches mentors, and prioritizes campus resources using deterministic local logic.",
        ),
        (
            "3. The student gets a usable next move",
            "Instead of generic advice, the response includes who might help, which resource matters most, and why it was chosen.",
        ),
    ]
    flow_columns = st.columns(3)
    for column, (title, description) in zip(flow_columns, flow_cards):
        with column:
            st.markdown(
                f"""
                <div class="info-card accent">
                    <h3>{title}</h3>
                    <p>{description}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown("### Demo boundaries")
    boundary_columns = st.columns([1.2, 1.8])
    with boundary_columns[0]:
        st.markdown(
            """
            <div class="notice-card">
                <h3>Privacy and safety</h3>
                <p>
                    Mentor phone numbers and emails shown in the demo are fake seeded records.
                    The local app keeps those details inside the UI, and live mode does not send them
                    into the Gemini prompt.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with boundary_columns[1]:
        st.markdown(
            """
            <div class="notice-card">
                <h3>Good questions to try in the demo</h3>
                <p>
                    Ask for a course, a type of help, or a language preference to see the strongest mentor matches.
                    Food-only prompts return restaurants instead of mentors.
                </p>
                <ul class="prompt-list">
                    <li>I'm struggling in CSC108 and want someone who speaks Hindi.</li>
                    <li>I need help with MAT137 and exam prep.</li>
                    <li>Can you find me a Computer Science mentor for debugging and assignments?</li>
                    <li>I'm overwhelmed and need someone on campus to talk to.</li>
                    <li>Where can I eat near campus after class?</li>
                </ul>
            </div>
            """,
            unsafe_allow_html=True,
        )


def _render_sidebar(live_mode_enabled: bool) -> tuple[str, str, str]:
    with st.sidebar:
        st.markdown("## Demo Controls")
        campus = st.selectbox(
            "Campus context",
            ["U of T St. George", "U of T Mississauga", "U of T Scarborough"],
            index=0,
        )
        course_filter = st.text_input("Course focus", placeholder="CSC108, MAT137")
        language_filter = st.selectbox(
            "Preferred mentor language",
            ["", "English", "Hindi", "Mandarin", "Punjabi", "Gujarati", "Arabic", "Spanish", "French", "Bengali", "Urdu", "Malayalam"],
            index=0,
        )
        st.caption(
            "Live Gemini mode uses Google Search grounding when `GEMINI_API_KEY` is configured. "
            "Otherwise the app runs entirely from seeded local demo data."
        )
        st.markdown(
            f"<div class='mode-chip {'live' if live_mode_enabled else 'demo'}'>"
            f"{'Live Gemini mode available' if live_mode_enabled else 'Demo mode only'}</div>",
            unsafe_allow_html=True,
        )
        if st.button("Reset chat", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
    return campus, course_filter, language_filter


def _render_chat_header(live_mode_enabled: bool, gemini_model: str) -> None:
    mode_label = "Live Gemini mode" if live_mode_enabled else "Demo mode"
    st.markdown(
        f"""
        <div class="hero-shell chat-shell">
            <div>
                <div class="eyebrow">U of T student support demo</div>
                <h1>UniSolved Chat Workspace</h1>
                <p class="hero-copy">
                    Ask one question and get a direct answer, official campus help, nearby public options,
                    and mentor matches pulled from demo data.
                </p>
            </div>
            <div class="hero-meta">
                <div class="mode-chip {'live' if live_mode_enabled else 'demo'}'>{mode_label}</div>
                <div class="model-chip">Model target: {gemini_model}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_starter_prompts() -> str:
    st.markdown("### Try a prompt")
    columns = st.columns(3)
    starters = [
        "I'm struggling in CSC108 and want someone who speaks Hindi.",
        "I'm overwhelmed and do not know who to talk to on campus.",
        "Where can I eat near campus after class?",
    ]
    chosen_prompt = ""
    for column, starter in zip(columns, starters):
        with column:
            if st.button(starter, use_container_width=True):
                chosen_prompt = starter
    return chosen_prompt


def _render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message["role"] == "user":
            st.markdown(message["content"])
            return

        _render_assistant_message(message)


def _render_assistant_message(message: dict) -> None:
    st.markdown(
        f"<div class='mode-chip inline {'live' if message.get('mode_label') == 'Live Gemini mode' else 'demo'}'>"
        f"{message.get('mode_label', 'Demo mode')}</div>",
        unsafe_allow_html=True,
    )
    st.markdown(message["content"])

    mentor_matches = message.get("mentor_matches", [])
    if mentor_matches:
        st.markdown("#### Mentor matches")
        for match in mentor_matches:
            st.markdown(
                f"""
                <div class="result-card">
                    <strong>{match['name']}</strong> · {match['program']} · Year {match['year']}<br>
                    {match['why_match']}<br>
                    <span class="contact-line">Phone: {match['phone']} | Email: {match['email']}</span><br>
                    <span class="muted">Availability: {match['availability']}</span>
                </div>
                """,
                unsafe_allow_html=True,
            )

    resource_matches = message.get("resource_matches", [])
    if resource_matches:
        st.markdown("#### Resources and places")
        for match in resource_matches:
            badge = "Official U of T" if match["is_official"] else "Public source"
            st.markdown(
                f"""
                <div class="result-card">
                    <strong>{match['name']}</strong> · {match['category'].replace('_', ' ').title()} · {badge}<br>
                    {match['description']}<br>
                    <span class="muted">{match['why_match']} Area: {match['area']}</span><br>
                    <a href="{match['source_url']}" target="_blank">Open source</a>
                </div>
                """,
                unsafe_allow_html=True,
            )

    citations = message.get("citations", [])
    if citations:
        st.markdown("#### Grounded sources")
        for citation in citations:
            query_text = f"Search query: {citation['query']}" if citation.get("query") else "Grounded public source"
            st.markdown(
                f"- [{citation['title']}]({citation['url']})  \n  {query_text}"
            )


def _mentor_to_dict(match) -> dict:
    return {
        "name": match.mentor.name,
        "program": match.mentor.program,
        "year": match.mentor.year,
        "phone": match.mentor.phone,
        "email": match.mentor.email,
        "availability": match.mentor.availability,
        "why_match": match.why_match,
    }


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --text-primary: #000000;
            --text-secondary: #1f1f1f;
            --text-muted: #333333;
            --surface: rgba(255, 255, 255, 0.94);
            --surface-soft: rgba(250, 250, 250, 0.9);
            --border-soft: rgba(0, 0, 0, 0.12);
        }
        .stApp {
            background:
                radial-gradient(circle at top left, rgba(253, 224, 162, 0.55), transparent 28%),
                radial-gradient(circle at top right, rgba(168, 230, 207, 0.35), transparent 24%),
                linear-gradient(180deg, #fdf7ef 0%, #f3efe6 100%);
            color: var(--text-primary);
            font-family: "Avenir Next", "IBM Plex Sans", "Trebuchet MS", sans-serif;
        }
        .stApp,
        .stApp p,
        .stApp li,
        .stApp label,
        .stApp h1,
        .stApp h2,
        .stApp h3,
        .stApp h4,
        .stApp h5,
        .stApp h6,
        .stApp div,
        .stApp span,
        .stApp input,
        .stApp textarea {
            color: var(--text-primary);
        }
        .stChatInput textarea,
        .stTextInput input,
        .stSelectbox div[data-baseweb="select"] * {
            color: var(--text-primary) !important;
        }
        .top-nav-shell {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 0.7rem;
            padding: 0.85rem 1rem;
            border: 1px solid var(--border-soft);
            border-radius: 18px;
            background: rgba(255, 255, 255, 0.78);
            backdrop-filter: blur(8px);
        }
        .top-nav-title {
            font-size: 1.05rem;
            font-weight: 700;
            color: var(--text-primary);
        }
        .landing-shell,
        .hero-shell {
            display: flex;
            justify-content: space-between;
            gap: 1rem;
            padding: 1.6rem 1.8rem;
            margin-bottom: 1rem;
            border: 1px solid var(--border-soft);
            border-radius: 22px;
            background: linear-gradient(135deg, rgba(255, 252, 245, 0.96), rgba(244, 240, 232, 0.92));
            box-shadow: 0 20px 40px rgba(51, 37, 22, 0.08);
        }
        .landing-shell {
            flex-direction: column;
            gap: 1.1rem;
            margin-bottom: 1rem;
            background:
                radial-gradient(circle at top left, rgba(255, 224, 160, 0.34), transparent 24%),
                radial-gradient(circle at bottom right, rgba(145, 198, 255, 0.2), transparent 20%),
                linear-gradient(135deg, rgba(255, 252, 245, 0.98), rgba(248, 244, 236, 0.94));
        }
        .hero-shell h1 {
            margin: 0;
            font-size: 3rem;
            line-height: 1;
            letter-spacing: -0.04em;
        }
        .landing-shell h1 {
            margin: 0;
            max-width: 54rem;
            font-size: 3.35rem;
            line-height: 1.02;
            letter-spacing: -0.05em;
        }
        .eyebrow {
            margin-bottom: 0.7rem;
            text-transform: uppercase;
            font-size: 0.76rem;
            letter-spacing: 0.14em;
            color: var(--text-secondary);
        }
        .hero-copy {
            max-width: 44rem;
            margin-top: 0.9rem;
            font-size: 1rem;
            color: var(--text-primary);
        }
        .hero-meta {
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: flex-end;
            gap: 0.75rem;
        }
        .landing-meta {
            align-items: flex-start;
            flex-direction: row;
            flex-wrap: wrap;
        }
        .mode-chip, .model-chip {
            display: inline-block;
            width: fit-content;
            padding: 0.45rem 0.8rem;
            border-radius: 999px;
            font-size: 0.85rem;
            font-weight: 700;
        }
        .mode-chip.demo {
            background: rgba(193, 120, 34, 0.12);
            color: var(--text-primary);
        }
        .mode-chip.live {
            background: rgba(44, 122, 84, 0.12);
            color: var(--text-primary);
        }
        .mode-chip.inline {
            margin-bottom: 0.5rem;
        }
        .model-chip {
            background: rgba(0, 0, 0, 0.08);
            color: var(--text-primary);
        }
        .result-card {
            margin-bottom: 0.8rem;
            padding: 0.9rem 1rem;
            border-radius: 16px;
            border: 1px solid var(--border-soft);
            background: var(--surface);
        }
        .info-card,
        .notice-card {
            height: 100%;
            padding: 1.1rem 1.15rem;
            border-radius: 18px;
            border: 1px solid var(--border-soft);
            background: rgba(255, 255, 255, 0.78);
            box-shadow: 0 12px 24px rgba(21, 16, 10, 0.05);
        }
        .info-card.accent {
            background: linear-gradient(180deg, rgba(255, 248, 235, 0.94), rgba(255, 255, 255, 0.8));
        }
        .info-card h3,
        .notice-card h3 {
            margin-top: 0;
            margin-bottom: 0.4rem;
            font-size: 1.08rem;
        }
        .info-card p,
        .notice-card p {
            margin-bottom: 0;
            color: var(--text-secondary);
        }
        .prompt-list {
            margin: 0.85rem 0 0;
            padding-left: 1.25rem;
        }
        .prompt-list li {
            margin-bottom: 0.45rem;
            color: var(--text-primary);
        }
        .contact-line {
            font-weight: 600;
            color: var(--text-primary);
        }
        .muted {
            color: var(--text-muted);
        }
        .stSidebar {
            color: var(--text-primary);
        }
        .stButton button {
            color: var(--text-primary);
            border-color: var(--border-soft);
            background: var(--surface-soft);
        }
        .stButton button:hover {
            border-color: rgba(0, 0, 0, 0.22);
            background: rgba(255, 255, 255, 0.98);
        }
        a {
            color: #000000;
        }
        @media (max-width: 900px) {
            .landing-shell,
            .hero-shell {
                flex-direction: column;
            }
            .landing-shell h1 {
                font-size: 2.55rem;
            }
            .hero-meta {
                align-items: flex-start;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
