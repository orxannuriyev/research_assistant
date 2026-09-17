# Research Assistant CLI

A modular Python CLI application that aggregates information from academic and web sources (Wikipedia, arXiv, DuckDuckGo, Tavily, Serper) and generates structured research summaries using LLM providers (Groq, OpenAI, Anthropic, Gemini).

---

##  Features

* **Multi-Source Fetching:** Asynchronously retrieves context from Wikipedia, arXiv, and Web search providers.
* **Flexible LLM Integration:** Supports Groq API (with automatic fallback to available models), OpenAI, Anthropic, and Google GenAI.
* **Robust Error Handling:** Built-in retries, explicit timeouts, and custom HTTP header handling to prevent API blocks.

---

## Setup & Installation

### 1. Clone & Setup Virtual Environment

```bash
git clone https://github.com/orxannuriyev/research_assistant.git
cd research_assistant

python -m venv .venv
# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate