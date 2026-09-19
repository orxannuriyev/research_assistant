import os

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="AI Research Assistant", page_icon="🔍", layout="wide"
)

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

# ==========================================================
# CSS STYLING
# ==========================================================

st.markdown(
    """
    <style>
    /* BACKGROUND */
    .stApp {
        background:
            linear-gradient(
                rgba(0, 0, 0, 0.5),
                rgba(0, 0, 0, 0.5)
            ),
            url("https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?q=80&w=1920")
            no-repeat center center fixed;
        background-size: cover;
        color: white;
    }

    /* MAIN TITLE */
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 700;
        margin-top: 4vh;
        margin-bottom: 20px;
        color: #ffffff;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.8);
    }

    /* SIDEBAR STYLING */
    section[data-testid="stSidebar"] {
        background: transparent !important;
        background-color: rgba(0, 0, 0, 0.2) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.2) !important;
    }
    
    div[data-testid="stSidebarContent"] {
        background: transparent !important;
    }

    section[data-testid="stSidebar"] * {
        color: white !important;
    }

    /* SELECTBOX */
    div[data-testid="stSelectbox"] div[data-baseweb="select"] {
        background-color: #ffffff !important;
        border-radius: 8px !important;
    }

    div[data-testid="stSelectbox"] div[data-baseweb="select"] * {
        color: #0f172a !important;
        background-color: transparent !important;
    }

    /* FORM CONTAINER */
    div[data-testid="stForm"] {
        background: transparent !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        border-radius: 10px !important;
        padding: 20px !important;
        box-shadow: none !important;
    }

    /* CHECKBOX */
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label span,
    div[data-testid="stCheckbox"] p {
        color: #ffffff !important;
    }

    /* QUESTION INPUT */
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
    }

    div[data-testid="stTextInput"] input {
        color: #0f172a !important;
        font-size: 1.1rem !important;
    }

    div[data-testid="stTextInput"] input::placeholder {
        color: #64748b !important;
        opacity: 0.8 !important;
    }

    /* SEARCH BUTTON */
    div[data-testid="stFormSubmitButton"] button {
        background: #ffffff !important;
        color: #0f172a !important;
        border: 1px solid #cbd5e1 !important;
        border-radius: 10px !important;
        padding: 8px 24px !important;
        font-weight: 600 !important;
        margin: 10px auto 0 auto !important;
        display: block;
    }

    div[data-testid="stFormSubmitButton"] button:hover {
        background: #f1f5f9 !important;
        border-color: white !important;
    }

    .result-container {
        color: white !important;
        margin-top: 25px;
    }

    .result-container * {
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================================
# SIDEBAR SETTINGS (LLM & Sources Selection)
# ==========================================================

with st.sidebar:
    configured_llm = os.getenv("LLM_PROVIDER", "openai")
    provider_options = ["openai", "gemini", "anthropic"]
    selected_llm = st.selectbox(
        "LLM Provider",
        provider_options,
        index=(
            provider_options.index(configured_llm)
            if configured_llm in provider_options
            else 0
        ),
    )

    st.markdown("---")
    st.subheader("📚 Sources")
    use_web = st.checkbox("Web (Tavily)", value=False)
    use_wiki = st.checkbox("Wikipedia", value=False)
    use_arxiv = st.checkbox("Arxiv (Scientific papers)", value=False)

# Sources list
sources_list = []
if use_web:
    sources_list.append("web")
if use_wiki:
    sources_list.append("wikipedia")
if use_arxiv:
    sources_list.append("arxiv")

sources_str = ", ".join(sources_list) if sources_list else None

# ==========================================================
# TITLE
# ==========================================================

st.markdown(
    '<div class="main-title">Research Assistant</div>', unsafe_allow_html=True
)

# ==========================================================
# CENTER COLUMN
# ==========================================================

col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    placeholder_text = "Type your question and press Enter..."
    button_text = "Search"
    spinner_text = "Gathering data..."
    results_title = "Results"
    sources_title = "Sources and Links Used:"
    llm_label = "LLM Used:"
    connection_error = "Could not connect to the backend server."
    validation_error = "Validation error."
    timeout_error = "The backend request timed out."

    # FORM
    with st.form(key="search_form"):
        query = st.text_input(
            "",
            key="user_query",
            placeholder=placeholder_text,
            label_visibility="collapsed",
        )
        submit_triggered = st.form_submit_button(button_text)

# ==========================================================
# SEND REQUEST TO BACKEND
# ==========================================================

if submit_triggered and query.strip():
    with col2:
        backend_url = os.getenv(
            "RESEARCH_API_URL",
            "http://127.0.0.1:8000/research",
        )

        payload = {
            "question": query,
            "sources": sources_str,
            "llm_provider": selected_llm,
            "no_cache": False,
        }

        try:
            with st.spinner(spinner_text):
                response = requests.post(backend_url, json=payload, timeout=60)

            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(f"### {results_title}")

            if response.status_code == 200:
                data = response.json()
                default_no_ans = "No answer found."
                answer = data.get("answer", default_no_ans)
                st.write(answer)

                # Display the provider confirmed by the backend
                data_llm_used = data.get("llm_provider", selected_llm)
                st.markdown(f"**{llm_label}** {data_llm_used}")

                # Display citations with clickable links if available
                citations = data.get("citations", [])
                if citations:
                    st.markdown(f"**{sources_title}**")
                    for cit in citations:
                        index = cit.get("index", "?")
                        title = cit.get("title", "Source")
                        url = cit.get("url", "#")
                        origin = cit.get("origin", "web")
                        st.markdown(f"- [{index}] [{title}]({url}) *({origin})*")

            elif response.status_code == 422:
                try:
                    error_detail = response.json().get("detail", validation_error)
                except Exception:
                    error_detail = validation_error

                st.error(f"Error: {error_detail}")

            else:
                st.error(f"Error: Unexpected status code from server: {response.status_code}")

            st.markdown("</div>", unsafe_allow_html=True)

        except requests.exceptions.ConnectionError:
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(f"### {results_title}")
            st.write(connection_error)
            st.markdown("</div>", unsafe_allow_html=True)

        except requests.exceptions.Timeout:
            st.error(timeout_error)

        except Exception as e:
            st.error(f"Error: {e}")