import requests
import streamlit as st

# ==========================================================
# PAGE CONFIGURATION
# ==========================================================

st.set_page_config(
    page_title="AI Research Assistant", page_icon="🔍", layout="wide"
)

# ==========================================================
# SESSION STATE INITIALIZATION
# ==========================================================

if "selected_lang" not in st.session_state:
    st.session_state.selected_lang = "Azərbaycan"

if "user_query" not in st.session_state:
    st.session_state.user_query = ""

if "last_lang" not in st.session_state:
    st.session_state.last_lang = st.session_state.selected_lang

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

    /* RADIO & CHECKBOX */
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] label span,
    div[data-testid="stCheckbox"] label,
    div[data-testid="stCheckbox"] label span,
    div[data-testid="stRadio"] p,
    div[data-testid="stRadio"] div,
    div[data-testid="stCheckbox"] p {
        color: #ffffff !important;
    }

    div[data-testid="stRadio"] div[role="radiogroup"] {
        gap: 20px;
        margin-bottom: 10px;
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
    selected_llm = st.selectbox(
        "LLM Provider / LLM Provider",
        ["openai", "gemini", "anthropic"],
        index=0,
    )

    st.markdown("---")
    st.subheader("📚 Sources / Sources")
    use_web = st.checkbox("Web (Tavily)", value=False)
    use_wiki = st.checkbox("Wikipedia", value=False)
    use_arxiv = st.checkbox("Arxiv (Scientific papers)", value=False)

# Sources list (Optional: if none selected, sends empty string or None)
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
    # LANGUAGE SELECTION
    selected_lang = st.radio(
        "Select language / Dil seçin",
        ["Azərbaycan", "English"],
        horizontal=True,
        key="selected_lang",
    )

    if st.session_state.last_lang != selected_lang:
        st.session_state.last_lang = selected_lang
        st.session_state.user_query = ""
        st.rerun()

    if selected_lang == "Azərbaycan":
        placeholder_text = "Sualınızı yazın və Enter düyməsini basın..."
        button_text = "Axtar"
        spinner_text = "Məlumatlar toplanır..."
        results_title = "Nəticələr"
        sources_title = "İstifadə olunan mənbələr və linklər:"
        llm_label = "İstifadə olunan LLM:"
        connection_error = "Backend serverinə qoşulmaq olmadı (Server işləmir)."
        validation_error = "Validasiya xətası."
        timeout_error = "Backend serverindən cavab almaq üçün gözləmə müddəti bitdi."
    else:
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
        backend_url = "http://127.0.0.1:8000/research"

        payload = {
            "question": query,
            "sources": sources_str,
            "language": selected_lang,
            "llm_provider": selected_llm,
        }

        try:
            with st.spinner(spinner_text):
                response = requests.post(backend_url, json=payload, timeout=60)

            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(f"### {results_title}")

            if response.status_code == 200:
                data = response.json()
                default_no_ans = (
                    "Cavab tapılmadı."
                    if selected_lang == "Azərbaycan"
                    else "No answer found."
                )
                answer = data.get("answer", default_no_ans)
                st.write(answer)

                # Display the selected LLM provider
                data_llm_used = selected_llm
                st.markdown(f"**{llm_label}** {data_llm_used}")

                # Display citations with clickable links if available
                citations = data.get("citations", [])
                if citations:
                    st.markdown(f"**{sources_title}**")
                    for cit in citations:
                        title = cit.get("title", "Source")
                        url = cit.get("url", "#")
                        origin = cit.get("origin", "web")
                        st.markdown(f"- [{title}]({url}) *({origin})*")

            elif response.status_code == 422:
                try:
                    error_detail = response.json().get("detail", validation_error)
                except Exception:
                    error_detail = validation_error

                err_prefix = "Xəta: " if selected_lang == "Azərbaycan" else "Error: "
                st.error(f"{err_prefix}{error_detail}")

            else:
                err_prefix = "Xəta: " if selected_lang == "Azərbaycan" else "Error: "
                st.error(f"{err_prefix}Unexpected status code from server: {response.status_code}")

            st.markdown("</div>", unsafe_allow_html=True)

        except requests.exceptions.ConnectionError:
            st.markdown('<div class="result-container">', unsafe_allow_html=True)
            st.markdown(f"### {results_title}")
            st.write(connection_error)
            st.markdown("</div>", unsafe_allow_html=True)

        except requests.exceptions.Timeout:
            st.error(timeout_error)

        except Exception as e:
            err_prefix = "Xəta: " if selected_lang == "Azərbaycan" else "Error: "
            st.error(f"{err_prefix}{e}")