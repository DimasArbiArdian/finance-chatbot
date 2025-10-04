# Gemini Finance Chatbot

An AI-powered financial consultation workspace built with Streamlit and Google Gemini. The assistant can shift personas across multiple finance-centric scenarios (customer service, literacy education, travel budgeting, and productivity coaching) while letting users tune tone, risk posture, planning horizon, and other creative parameters.

> **Repository URL:** https://github.com/YOUR-ORG/finance-chatbot

## Key Features
- Uses Google Gemini (`google-genai`) for natural language understanding and generation.
- Four pre-built financial playbooks that align with common chatbot use cases: retail banking concierge, financial literacy coach, travel budget strategist, and productivity & savings partner.
- Rich parameter controls for tone, knowledge domains, risk appetite, planning horizon, actionable outputs, compliance reminders, and session memory.
- Upload PDF, text, CSV, or image files so the assistant can cite information directly from user-provided material.
- Switch between system, light, and dark themes from the sidebar to match your workspace.
- Toggle the interface language between English and Indonesian; responses follow the selected language.
- Prompt orchestration that injects the selected configuration into every Gemini call to keep replies on-brief.
- Session memory snapshot so the bot can recall recent user goals when enabled.

## Getting Started

### 1. Prerequisites
- Python 3.9 or newer
- Google AI Studio API key with access to Gemini models (`GOOGLE_API_KEY`)
- `pip` for installing Python packages

### 2. Installation
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows use: .venv\Scriptsctivate
pip install -r requirements.txt
```

### 3. Run the App
```bash
streamlit run finance_chatbot_app.py
```

Open the displayed local URL in your browser. Add your Google API key in the sidebar and choose a playbook to start exploring.

## Use Cases & Parameters

| Playbook | Primary Outcomes | Example Prompts |
| --- | --- | --- |
| Retail Banking Concierge | Fee explanations, dispute guidance, escalation playbooks | "Help me understand why I was charged overdraft fees last week." |
| Financial Literacy Coach | Lesson plans, challenges, confidence-based explanations | "Create a lesson plan to explain compound interest to college students." |
| Travel Budget Strategist | Route planning with FX considerations and savings tactics | "Plan a 5-day Tokyo trip under $2,000 all-in." |
| Productivity & Savings Partner | Goal sprint mapping, automation suggestions, motivational nudges | "Help me build a 90-day sprint to pay down $5k of debt." |

### Creative Parameters
- **Language style:** Formal, conversational, or analytical tone control.
- **Knowledge modules:** Choose domain expertise like budgeting, FX markets, or regulations.
- **Risk appetite:** Scale (1-5) that shifts recommendations along conservative to aggressive lines.
- **Planning horizon:** Immediate to multi-year guidance framing.
- **Actionable checklist:** Toggle to enforce task lists in every reply.
- **Compliance reminder:** Optional closing disclaimer for regulated contexts.
- **Session memory:** Stores up to five recent user prompts to maintain continuity.
- **Creativity bias:** Adjusts how exploratory or deterministic the assistant should be.

### Theme & Language
- Choose **Theme** in the sidebar to toggle between system default, light, and dark palettes.
- Set **Language** to English or Indonesian; the UI labels and assistant replies switch instantly.
- Language-aware prompts ensure Gemini responds with terminology appropriate for the selected locale.

### Working with Uploaded Documents
- Supported formats: PDF, TXT/Markdown, CSV, and common image types (PNG, JPG, WEBP).
- Each file is trimmed to the first ~6,000 characters to protect model context limits; the UI shows whether content was truncated.
- Use the **Clear document context** button under the chat uploader to remove uploaded references without resetting the conversation.

## Deployment Notes
- The project is ready for GitHub. Update the repository URL above after pushing.
- For container-based deployments, adapt the Streamlit launch command inside your orchestration platform (e.g., Cloud Run, App Engine).
- Ensure the `GOOGLE_API_KEY` environment variable is provided securely in production.

## Next Steps
- Extend playbooks with organisation-specific datasets or APIs.
- Add analytics (e.g., Streamlit events or logging) to monitor real user questions.
- Wire optional tools such as currency rate services once external integrations are approved.
