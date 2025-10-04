import streamlit as st
from google import genai

st.set_page_config(
    page_title="Gemini Financial Consultant",
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


def build_persona_prompt(*, use_case, tone, knowledge_domains, risk_band, horizon, include_actions, include_disclaimer, creativity_level):
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




def build_structured_prompt(*, persona_prompt, user_message, memory_notes):
    sections = [persona_prompt]
    if memory_notes:
        sections.append("Session memory: key user preferences so far -> " + "; ".join(memory_notes))
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
    creativity_slider = st.slider("Creativity Bias", 0.0, 1.0, 0.4, 0.05, help="Lower values force deterministic analysis, higher values allow richer storytelling.")
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

hero_col, focus_col = st.columns([2, 1])
with hero_col:
    st.title("Gemini Financial Consultation Studio")
    st.caption("Configurable AI advisor powered by Google Gemini models")
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

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input("Share a financial challenge, goal, or question...")

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

