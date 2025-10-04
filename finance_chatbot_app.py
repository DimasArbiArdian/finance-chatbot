import base64
import io
from pathlib import Path
from typing import List, Tuple

import streamlit as st
from google import genai
from PyPDF2 import PdfReader

st.set_page_config(
    page_title="Financial Consultant",
    page_icon="💼",
    layout="wide",
)

MODEL_OPTIONS = [
    "gemini-2.5-flash",
    "gemini-2.0-flash-exp",
    "gemini-1.5-pro",
]

USE_CASES = {
    "Retail Banking Concierge": {
        "tagline": "Resolve account questions, fees, and loan inquiries with empathetic clarity.",
        "focus": [
            "Explain account activity, fees, and policy details",
            "Guide users through loan or card application steps",
            "Escalate red-flag scenarios with clear next actions",
        ],
        "sample_prompts": [
            "Help me understand why I was charged overdraft fees last week.",
            "Walk me through the steps to dispute a credit card transaction.",
        ],
        "default_domains": ["Retail Banking", "Customer Service", "Regulations"],
    },
    "Financial Literacy Coach": {
        "tagline": "Teach core money concepts with digestible lessons and practical activities.",
        "focus": [
            "Simplify jargon and reinforce the fundamentals",
            "Offer budgeting drills and literacy challenges",
            "Adapt explanations to the learner's confidence level",
        ],
        "sample_prompts": [
            "Create a lesson plan to explain compound interest to college students.",
            "Give me a weekly challenge to build emergency savings.",
        ],
        "default_domains": ["Education", "Budgeting", "Behavioral Finance"],
    },
    "Travel Budget Strategist": {
        "tagline": "Blend itinerary planning with real-world cost controls and currency tips.",
        "focus": [
            "Design itineraries aligned to spending caps",
            "Highlight cross-border fees, FX, and insurance needs",
            "Suggest savings tactics before and during the trip",
        ],
        "sample_prompts": [
            "Plan a 5-day Tokyo trip under $2,000 all-in.",
            "How should I budget for a family vacation across three EU cities?",
        ],
        "default_domains": ["Travel", "FX Markets", "Savings"],
    },
    "Productivity & Savings Partner": {
        "tagline": "Turn financial goals into repeatable rituals and smart nudges.",
        "focus": [
            "Translate goals into trackable milestones",
            "Recommend automations, alerts, and review cadences",
            "Keep momentum with motivational check-ins",
        ],
        "sample_prompts": [
            "Help me build a 90-day sprint to pay down $5k of debt.",
            "What automation rules should I create to stay on budget?",
        ],
        "default_domains": ["Personal Finance", "Productivity", "Behavioral Finance"],
    },
}

KNOWLEDGE_OPTIONS = [
    "Asset Allocation",
    "Behavioral Finance",
    "Budgeting",
    "Corporate Finance",
    "Credit Management",
    "Customer Service",
    "Education",
    "FX Markets",
    "Personal Finance",
    "Regulations",
    "Retail Banking",
    "Risk Management",
    "Savings",
    "Small Business",
    "Tax Planning",
    "Travel",
]

LANGUAGE_STYLES = {
    "Formal": "Deliver polished, compliance-friendly prose with structured paragraphs.",
    "Conversational": "Use approachable, empathetic language with practical analogies.",
    "Analytical": "Lead with metrics, benchmarks, and scenario analysis.",
}

TIME_HORIZONS = ["Immediate", "30 Days", "Quarter", "Annual", "Multi-Year"]

UPLOADABLE_TYPES = ["pdf", "txt", "md", "csv", "png", "jpg", "jpeg", "webp"]
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
IMAGE_CAPTION_MODEL = "gemini-1.5-flash-latest"
MAX_DOCUMENT_CHARS = 6000
DOCUMENT_PREVIEW_CHARS = 600
CSV_PREVIEW_ROWS = 80


def truncate_text(text: str, max_chars: int) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True




def describe_image_bytes(client, data: bytes, mime_type: str, model_hint: str | None = None) -> tuple[str, str | None]:
    if client is None:
        return "", "No Google client available to interpret the image."
    payload = base64.b64encode(data).decode("utf-8")

    model_sequence: list[str] = []
    if IMAGE_CAPTION_MODEL:
        model_sequence.append(IMAGE_CAPTION_MODEL)
    if model_hint and model_hint not in model_sequence:
        model_sequence.append(model_hint)
    fallback_model = "gemini-1.5-pro-latest"
    if fallback_model not in model_sequence:
        model_sequence.append(fallback_model)

    last_error: str | None = None
    for model_name in model_sequence:
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {
                                "text": (
                                    "Summarise this image focusing on financial data, text, or cues that could help a "
                                    "financial advisor understand the user's situation. Respond with concise bullet "
                                    "points and include any legible figures."
                                )
                            },
                            {"inline_data": {"mime_type": mime_type, "data": payload}},
                        ],
                    }
                ],
            )
            if hasattr(response, "text") and response.text:
                return response.text.strip(), None
            candidates = getattr(response, "candidates", None)
            if candidates:
                for candidate in candidates:
                    content = getattr(candidate, "content", None)
                    parts = getattr(content, "parts", None) if content else None
                    if parts:
                        text_parts = [getattr(part, "text", "") for part in parts]
                        summary = "\n".join(p for p in text_parts if p)

                        if summary.strip():
                            return summary.strip(), None
        except Exception as exc:
            last_error = str(exc)
            if "NOT_FOUND" not in last_error and "unsupported" not in last_error.lower():
                return "", f"Could not interpret image: {exc}"
    if last_error:
        return "", f"Could not interpret image: {last_error}"
    return "", "Image analysis returned no text."

def extract_text_from_file(uploaded_file, client=None, model_hint: str | None = None) -> Tuple[str, bool, str | None]:
    suffix = Path(uploaded_file.name).suffix.lower()
    try:
        data = uploaded_file.read()
        uploaded_file.seek(0)
    except Exception as exc:
        return "", False, f"Could not read file bytes: {exc}"

    if not data:
        return "", False, "File is empty."

    try:
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(data))
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        elif suffix in {".txt", ".md"}:
            text = data.decode("utf-8", errors="ignore")
        elif suffix == ".csv":
            decoded = data.decode("utf-8", errors="ignore")
            lines = decoded.splitlines()
            preview = "\n".join(lines[:CSV_PREVIEW_ROWS])
            if len(lines) > CSV_PREVIEW_ROWS:
                preview += "\n..."
            text = preview
        elif suffix in IMAGE_TYPES:
            summary, image_error = describe_image_bytes(client, data, IMAGE_TYPES[suffix], model_hint)
            if image_error:
                return "", False, image_error
            text = summary
        else:
            return "", False, f"Unsupported file type: {suffix or 'unknown'}"
    except Exception as exc:
        return "", False, f"Could not parse file: {exc}"

    cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not cleaned:
        return "", False, "No readable text found in the file."

    truncated_text, truncated = truncate_text(cleaned, MAX_DOCUMENT_CHARS)
    return truncated_text, truncated, None


def prepare_documents(files, client, model_hint: str | None = None) -> Tuple[List[dict], List[str]]:
    documents = []
    errors = []
    for uploaded_file in files:
        content, truncated, error = extract_text_from_file(uploaded_file, client, model_hint)
        if error:
            errors.append(f"{uploaded_file.name}: {error}")
            continue
        preview, _ = truncate_text(content, DOCUMENT_PREVIEW_CHARS)
        documents.append(
            {
                "name": uploaded_file.name,
                "content": content,
                "preview": preview,
                "truncated": truncated,
                "char_count": len(content),
            }
        )
    return documents, errors


def build_persona_prompt(
    *,
    use_case,
    tone,
    knowledge_domains,
    risk_band,
    horizon,
    include_actions,
    include_disclaimer,
    creativity_level,
):
    case = USE_CASES[use_case]
    knowledge_text = ", ".join(knowledge_domains) if knowledge_domains else "general financial guidance"
    creativity_modes = {
        "Low": "Prioritise precision and policy alignment over creativity.",
        "Balanced": "Blend strategic insight with practical examples.",
        "High": "Incorporate creative storytelling while staying financially sound.",
    }
    if creativity_level <= 0.3:
        creativity_prompt = creativity_modes["Low"]
    elif creativity_level >= 0.7:
        creativity_prompt = creativity_modes["High"]
    else:
        creativity_prompt = creativity_modes["Balanced"]

    guidelines = [
        f"You are a Gemini-powered financial consultant specialised in the '{use_case}' playbook.",
        f"Mission: {case['tagline']}",
        f"Expertise modules to lean on: {knowledge_text}.",
        f"Language style directive: {LANGUAGE_STYLES[tone]}",
        f"Target risk posture: level {risk_band} on a 1-5 scale (1=capital preservation, 5=aggressive growth).",
        f"Planning horizon: {horizon}.",
        creativity_prompt,
        "Ground every recommendation in verifiable finance principles and up-to-date best practices.",
        "Cite assumptions when precise data is unavailable.",
    ]

    if include_actions:
        guidelines.append("Always convert insights into a prioritised action plan with owners or suggested tools.")
    if include_disclaimer:
        guidelines.append("Close with a compliance reminder that personalised advice requires a licensed professional.")

    return "\n".join(guidelines)


def build_structured_prompt(
    *,
    persona_prompt,
    user_message,
    memory_notes,
    documents,
):
    sections = [persona_prompt]
    if memory_notes:
        sections.append("Session memory: key user preferences so far -> " + "; ".join(memory_notes))
    if documents:
        sections.append("Reference documents supplied by the user:\n" + "\n\n".join(documents))
    sections.append("User request:\n" + user_message)
    sections.append(
        "Response format:\n"
        "1. Executive insight (1-2 sentences).\n"
        "2. Detailed guidance with numbered recommendations.\n"
        "3. Scenario or calculation examples when useful.\n"
        "4. Resource suggestions (articles, tools, or checklists).\n"
        "5. Compliance or risk caveats (keep concise)."
    )
    return "\n\n".join(sections)


with st.sidebar:
    st.header("Assistant Settings")
    google_api_key = st.text_input("Google AI API Key", type="password")
    model_name = st.selectbox("Gemini Model", MODEL_OPTIONS, index=0)
    use_case = st.selectbox("Financial Playbook", list(USE_CASES.keys()))
    tone = st.selectbox("Language Style", list(LANGUAGE_STYLES.keys()), index=1)
    creativity_slider = st.slider(
        "Creativity Bias",
        0.0,
        1.0,
        0.4,
        0.05,
        help="Lower values force deterministic analysis, higher values allow richer storytelling.",
    )
    selected_domains = st.multiselect(
        "Knowledge Modules",
        KNOWLEDGE_OPTIONS,
        default=USE_CASES[use_case]["default_domains"],
    )
    risk_appetite = st.slider("Risk Appetite", 1, 5, 3, help="1 = very cautious, 5 = aggressive growth focus.")
    planning_horizon = st.selectbox("Planning Horizon", TIME_HORIZONS, index=2)
    include_actions = st.toggle("Include actionable checklist", value=True)
    include_disclaimer = st.toggle("Include compliance reminder", value=True)
    enable_memory = st.toggle("Enable session memory", value=True)
    reset_button = st.button("Reset conversation", type="primary")


if not google_api_key:
    st.info("Add your Google AI API key in the sidebar to start the consultation.", icon="ℹ️")
    st.stop()

if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
if "document_errors" not in st.session_state:
    st.session_state.document_errors = []

if ("genai_client" not in st.session_state) or (st.session_state.get("_last_key") != google_api_key):
    st.session_state.genai_client = genai.Client(api_key=google_api_key)
    st.session_state._last_key = google_api_key
    st.session_state.pop("chat", None)
    st.session_state.pop("messages", None)
    st.session_state.pop("memory_notes", None)

profile_signature = "|".join(
    [
        model_name,
        use_case,
        tone,
        ",".join(sorted(selected_domains)),
        str(risk_appetite),
        planning_horizon,
        str(include_actions),
        str(include_disclaimer),
        f"creativity={creativity_slider:.2f}",
    ]
)

if ("chat" not in st.session_state) or (st.session_state.get("_profile_signature") != profile_signature):
    st.session_state.chat = st.session_state.genai_client.chats.create(model=model_name)
    st.session_state._profile_signature = profile_signature
    st.session_state.messages = []
    st.session_state.memory_notes = []

if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_notes" not in st.session_state:
    st.session_state.memory_notes = []

if reset_button:
    st.session_state.pop("chat", None)
    st.session_state.pop("messages", None)
    st.session_state.pop("memory_notes", None)
    st.rerun()

selected_case = USE_CASES[use_case]

document_errors = st.session_state.document_errors
if document_errors:
    for error in document_errors:
        st.error(error)

hero_col, focus_col = st.columns([2, 1])
with hero_col:
    st.title("Financial Consultation Assistant 💼")
    st.caption("Solve money challenges with expert AI guidance.")
    st.subheader(use_case)
    st.write(selected_case["tagline"])

with focus_col:
    st.markdown("**Focus Areas**")
    for item in selected_case["focus"]:
        st.markdown(f"- {item}")

st.divider()

samples_col, config_col = st.columns(2)
with samples_col:
    st.markdown("**Sample Prompts**")
    for prompt in selected_case["sample_prompts"]:
        st.markdown(f"- _{prompt}_")

with config_col:
    st.markdown("**Current Configuration**")
    st.markdown(f"- Model: `{model_name}`")
    st.markdown(f"- Tone: {tone}")
    st.markdown(f"- Knowledge modules: {', '.join(selected_domains) if selected_domains else 'generalist'}")
    st.markdown(f"- Risk appetite: {risk_appetite}")
    st.markdown(f"- Planning horizon: {planning_horizon}")
    st.markdown(f"- Session memory: {'enabled' if enable_memory else 'disabled'}")

with st.chat_message("assistant"):
    st.markdown("**Attach reference documents (optional)**")
    uploaded_files = st.file_uploader(
        "Attach reference documents",
        type=UPLOADABLE_TYPES,
        accept_multiple_files=True,
        key="chat_uploader",
        label_visibility="collapsed",
        help="Upload PDF, text, CSV, or image files to ground the assistant's answers.",
    )
    clear_docs = st.button("Clear document context", key="chat_clear_docs")

if uploaded_files:
    documents, doc_errors = prepare_documents(uploaded_files, st.session_state.genai_client, model_name)
    st.session_state.uploaded_documents = documents
    st.session_state.document_errors = doc_errors

if clear_docs:
    st.session_state.uploaded_documents = []
    st.session_state.document_errors = []
    st.session_state.pop("chat_uploader", None)

if st.session_state.uploaded_documents:
    with st.expander("Attached document excerpts", expanded=False):
        for doc in st.session_state.uploaded_documents:
            meta = f"**{doc['name']}** · {doc['char_count']} characters"
            if doc["truncated"]:
                meta += " (truncated)"
            st.markdown(meta)
            st.code(doc["preview"], language="markdown")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Share a financial challenge, goal, or question...")

document_context = [
    f"Document: {doc['name']}{' (truncated)' if doc['truncated'] else ''}\n{doc['content']}"
    for doc in st.session_state.uploaded_documents
]

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    if enable_memory:
        notes = st.session_state.get("memory_notes", [])
        notes.append(user_prompt)
        st.session_state.memory_notes = notes[-5:]

    persona_prompt = build_persona_prompt(
        use_case=use_case,
        tone=tone,
        knowledge_domains=selected_domains,
        risk_band=risk_appetite,
        horizon=planning_horizon,
        include_actions=include_actions,
        include_disclaimer=include_disclaimer,
        creativity_level=creativity_slider,
    )
    structured_prompt = build_structured_prompt(
        persona_prompt=persona_prompt,
        user_message=user_prompt,
        memory_notes=st.session_state.memory_notes if enable_memory else [],
        documents=document_context,
    )

    try:
        response = st.session_state.chat.send_message(structured_prompt)
        assistant_answer = response.text if hasattr(response, "text") else str(response)
    except Exception as error:
        assistant_answer = f"⚠️ Unable to complete the request: {error}"

    with st.chat_message("assistant"):
        st.markdown(assistant_answer)

    st.session_state.messages.append({"role": "assistant", "content": assistant_answer})

if enable_memory and st.session_state.memory_notes:
    with st.expander("Session memory snapshot", expanded=False):
        st.write("\n".join(st.session_state.memory_notes))
