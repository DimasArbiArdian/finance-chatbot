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

LANGUAGE_OPTIONS = ["English", "Indonesian"]
DEFAULT_LANGUAGE = LANGUAGE_OPTIONS[0]

LANGUAGE_STRINGS = {
    "English": {
        "assistant_settings": "Assistant Settings",
        "api_key_label": "Google AI API Key",
        "model_label": "Gemini Model",
        "use_case_label": "Use Case",
        "tone_label": "Language Style",
        "creativity_label": "Creativity Bias",
        "creativity_help": "Lower values force deterministic analysis, higher values allow richer storytelling.",
        "knowledge_label": "Knowledge Modules",
        "risk_label": "Risk Appetite",
        "risk_help": "1 = very cautious, 5 = aggressive growth focus.",
        "planning_label": "Planning Horizon",
        "actions_toggle": "Include actionable checklist",
        "disclaimer_toggle": "Include compliance reminder",
        "memory_toggle": "Enable session memory",
        "theme_label": "Theme",
        "language_label": "Language",
        "reset_button": "Reset conversation",
        "need_api_key": "Please add your Google AI API key in the sidebar to start the consultation.",
        "page_title": "Financial Consultation Assistant🧑‍💻",
        "page_caption": "Configurable AI advisor powered by Google Gemini models",
        "focus_heading": "Focus Areas",
        "samples_heading": "Sample Prompts",
        "config_heading": "Current Configuration",
        "config_model": "Model",
        "config_tone": "Tone",
        "config_domains": "Knowledge modules",
        "config_risk": "Risk appetite",
        "config_horizon": "Planning horizon",
        "config_memory": "Session memory",
        "persona_intro": "You are a Gemini-powered financial consultant specialised in the '{title}' playbook.",
        "persona_mission": "Mission: {tagline}",
        "persona_expertise": "Expertise modules to lean on: {knowledge}.",
        "persona_language_style": "Language style directive: {language_style}",
        "persona_risk": "Target risk posture: level {risk} on a 1-5 scale (1=capital preservation, 5=aggressive growth).",
        "persona_horizon": "Planning horizon: {horizon}.",
        "default_knowledge": "general financial guidance",
        "status_enabled": "enabled",
        "status_disabled": "disabled",
        "attachment_header": "Attach reference documents (optional)",
        "upload_help": "Upload PDF, text, CSV, or image files to ground the assistant's answers.",
        "clear_docs": "Clear document context",
        "chat_placeholder": "Share a financial challenge, goal, or question...",
        "doc_expander": "Attached document excerpts",
        "memory_expander": "Session memory snapshot",
        "memory_prefix": "Session memory: key user preferences so far -> ",
        "documents_label": "Reference documents supplied by the user:",
        "user_request_label": "User request:",
        "response_format_title": "Response format:",
        "response_step_1": "1. Executive insight (1-2 sentences).",
        "response_step_2": "2. Detailed guidance with numbered recommendations.",
        "response_step_3": "3. Scenario or calculation examples when useful.",
        "response_step_4": "4. Resource suggestions (articles, tools, or checklists).",
        "response_step_5": "5. Compliance or risk caveats (keep concise).",
        "document_prefix": "Document",
        "truncated_suffix": " (truncated)",
        "characters_label": "characters",
        "persona_grounding": "Ground every recommendation in verifiable finance principles and up-to-date best practices.",
        "persona_assumptions": "Cite assumptions when precise data is unavailable.",
        "persona_actions": "Always convert insights into a prioritised action plan with owners or suggested tools.",
        "persona_disclaimer": "Close with a compliance reminder that personalised advice requires a licensed professional.",
        "persona_language_instruction": "Respond in English.",
    },
    "Indonesian": {
        "assistant_settings": "Pengaturan Asisten",
        "api_key_label": "Google AI API Key",
        "model_label": "Model Gemini",
        "use_case_label": "Skenario",
        "tone_label": "Gaya Bahasa",
        "creativity_label": "Bias Kreativitas",
        "creativity_help": "Nilai rendah membuat analisis lebih deterministik, nilai tinggi memberi ruang cerita yang lebih kaya.",
        "knowledge_label": "Modul Pengetahuan",
        "risk_label": "Selera Risiko",
        "risk_help": "1 = sangat hati-hati, 5 = fokus pertumbuhan agresif.",
        "planning_label": "Horizon Perencanaan",
        "actions_toggle": "Sertakan daftar tindakan",
        "disclaimer_toggle": "Sertakan pengingat kepatuhan",
        "memory_toggle": "Aktifkan memori sesi",
        "theme_label": "Tema",
        "language_label": "Bahasa",
        "reset_button": "Mulai ulang percakapan",
        "need_api_key": "Tambahkan Google AI API key di sidebar untuk mulai berkonsultasi.",
        "page_title": "Asisten Konsultasi Keuangan 🧑‍💻",
        "page_caption": "Konsultan AI yang dapat dikonfigurasi dengan model Google Gemini",
        "focus_heading": "Bidang Fokus",
        "samples_heading": "Contoh Pertanyaan",
        "config_heading": "Konfigurasi Saat Ini",
        "config_model": "Model",
        "config_tone": "Gaya",
        "config_domains": "Modul pengetahuan",
        "config_risk": "Selera risiko",
        "config_horizon": "Horizon perencanaan",
        "config_memory": "Memori sesi",
        "persona_intro": "Anda adalah konsultan keuangan bertenaga Gemini yang fokus pada playbook '{title}'.",
        "persona_mission": "Misi: {tagline}",
        "persona_expertise": "Modul keahlian yang perlu diutamakan: {knowledge}.",
        "persona_language_style": "Instruksi gaya bahasa: {language_style}",
        "persona_risk": "Selera risiko target: level {risk} pada skala 1-5 (1=melindungi modal, 5=pertumbuhan agresif).",
        "persona_horizon": "Horizon perencanaan: {horizon}.",
        "default_knowledge": "panduan keuangan umum",
        "status_enabled": "aktif",
        "status_disabled": "nonaktif",
        "attachment_header": "Lampirkan dokumen referensi (opsional)",
        "upload_help": "Unggah file PDF, teks, CSV, atau gambar untuk membantu jawaban asisten.",
        "clear_docs": "Bersihkan konteks dokumen",
        "chat_placeholder": "Bagikan tantangan, tujuan, atau pertanyaan keuangan...",
        "doc_expander": "Cuplikan dokumen terlampir",
        "memory_expander": "Ringkasan memori sesi",
        "memory_prefix": "Memori sesi: preferensi pengguna sejauh ini -> ",
        "documents_label": "Dokumen referensi dari pengguna:",
        "user_request_label": "Permintaan pengguna:",
        "response_format_title": "Format respons:",
        "response_step_1": "1. Wawasan utama (1-2 kalimat).",
        "response_step_2": "2. Rekomendasi rinci dengan penomoran.",
        "response_step_3": "3. Contoh skenario atau perhitungan bila relevan.",
        "response_step_4": "4. Rekomendasi sumber daya (artikel, alat, atau daftar periksa).",
        "response_step_5": "5. Catatan kepatuhan atau risiko (singkat saja).",
        "document_prefix": "Dokumen",
        "truncated_suffix": " (dipersingkat)",
        "characters_label": "karakter",
        "persona_grounding": "Dasarkan setiap rekomendasi pada prinsip keuangan yang dapat diverifikasi dan praktik terbaru.",
        "persona_assumptions": "Sebutkan asumsi saat data presisi tidak tersedia.",
        "persona_actions": "Selalu ubah wawasan menjadi daftar tindakan terurut lengkap dengan penanggung jawab atau alat yang disarankan.",
        "persona_disclaimer": "Akhiri dengan pengingat bahwa saran personal memerlukan profesional berlisensi.",
        "persona_language_instruction": "Gunakan bahasa Indonesia dalam setiap jawaban.",
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

KNOWLEDGE_OPTION_LABELS = {
    "Asset Allocation": {"English": "Asset Allocation", "Indonesian": "Alokasi Aset"},
    "Behavioral Finance": {"English": "Behavioral Finance", "Indonesian": "Keuangan Perilaku"},
    "Budgeting": {"English": "Budgeting", "Indonesian": "Penganggaran"},
    "Corporate Finance": {"English": "Corporate Finance", "Indonesian": "Keuangan Korporat"},
    "Credit Management": {"English": "Credit Management", "Indonesian": "Manajemen Kredit"},
    "Customer Service": {"English": "Customer Service", "Indonesian": "Layanan Pelanggan"},
    "Education": {"English": "Education", "Indonesian": "Pendidikan"},
    "FX Markets": {"English": "FX Markets", "Indonesian": "Pasar Valuta Asing"},
    "Personal Finance": {"English": "Personal Finance", "Indonesian": "Keuangan Pribadi"},
    "Regulations": {"English": "Regulations", "Indonesian": "Regulasi"},
    "Retail Banking": {"English": "Retail Banking", "Indonesian": "Perbankan Ritel"},
    "Risk Management": {"English": "Risk Management", "Indonesian": "Manajemen Risiko"},
    "Savings": {"English": "Savings", "Indonesian": "Tabungan"},
    "Small Business": {"English": "Small Business", "Indonesian": "Usaha Kecil"},
    "Tax Planning": {"English": "Tax Planning", "Indonesian": "Perencanaan Pajak"},
    "Travel": {"English": "Travel", "Indonesian": "Perjalanan"},
}

LANGUAGE_STYLE_LABELS = {
    "Formal": {"English": "Formal", "Indonesian": "Formal"},
    "Conversational": {"English": "Conversational", "Indonesian": "Percakapan"},
    "Analytical": {"English": "Analytical", "Indonesian": "Analitis"},
}

LANGUAGE_STYLE_DESCRIPTIONS = {
    "Formal": {
        "English": "Deliver polished, compliance-friendly prose with structured paragraphs.",
        "Indonesian": "Gunakan bahasa resmi yang sesuai kepatuhan dengan paragraf terstruktur.",
    },
    "Conversational": {
        "English": "Use approachable, empathetic language with practical analogies.",
        "Indonesian": "Gunakan bahasa akrab dan empatik dengan analogi yang mudah dipahami.",
    },
    "Analytical": {
        "English": "Lead with metrics, benchmarks, and scenario analysis.",
        "Indonesian": "Fokus pada metrik, tolok ukur, dan analisis skenario.",
    },
}

CREATIVITY_MODE_TEXT = {
    "English": {
        "low": "Prioritise precision and policy alignment over creativity.",
        "balanced": "Blend strategic insight with practical examples.",
        "high": "Incorporate creative storytelling while staying financially sound.",
    },
    "Indonesian": {
        "low": "Utamakan ketepatan dan kepatuhan kebijakan dibanding kreativitas.",
        "balanced": "Padukan wawasan strategis dengan contoh praktis.",
        "high": "Gunakan cerita kreatif tanpa mengorbankan ketepatan finansial.",
    },
}

TIME_HORIZONS = ["Immediate", "30 Days", "Quarter", "Annual", "Multi-Year"]
TIME_HORIZON_LABELS = {
    "Immediate": {"English": "Immediate", "Indonesian": "Segera"},
    "30 Days": {"English": "30 Days", "Indonesian": "30 Hari"},
    "Quarter": {"English": "Quarter", "Indonesian": "Triwulan"},
    "Annual": {"English": "Annual", "Indonesian": "Tahunan"},
    "Multi-Year": {"English": "Multi-Year", "Indonesian": "Multi-Tahun"},
}

USE_CASES = {
    "retail_banking": {
        "default_domains": ["Retail Banking", "Customer Service", "Regulations"],
        "locales": {
            "English": {
                "title": "Retail Banking Concierge",
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
            },
            "Indonesian": {
                "title": "Konsier Perbankan Ritel",
                "tagline": "Selesaikan pertanyaan rekening, biaya, dan pengajuan pinjaman dengan empati dan kejelasan.",
                "focus": [
                    "Menjelaskan aktivitas rekening, biaya, dan detail kebijakan",
                    "Memandu nasabah melalui tahapan pengajuan pinjaman atau kartu",
                    "Mengeskalasi situasi berisiko dengan langkah lanjutan yang jelas",
                ],
                "sample_prompts": [
                    "Jelaskan mengapa saya dikenakan biaya overdraft minggu lalu.",
                    "Panduan langkah demi langkah untuk menggugat transaksi kartu kredit.",
                ],
            },
        },
    },
    "financial_literacy": {
        "default_domains": ["Education", "Budgeting", "Behavioral Finance"],
        "locales": {
            "English": {
                "title": "Financial Literacy Coach",
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
            },
            "Indonesian": {
                "title": "Pelatih Literasi Keuangan",
                "tagline": "Ajarkan konsep uang penting dengan sesi yang mudah dipahami dan latihan praktis.",
                "focus": [
                    "Menyederhanakan istilah teknis dan menegaskan dasar-dasarnya",
                    "Memberikan latihan anggaran dan tantangan literasi",
                    "Menyesuaikan penjelasan dengan tingkat kepercayaan diri peserta",
                ],
                "sample_prompts": [
                    "Buat rencana pembelajaran untuk menjelaskan bunga majemuk kepada mahasiswa.",
                    "Berikan tantangan mingguan agar saya bisa membangun dana darurat.",
                ],
            },
        },
    },
    "travel_budget": {
        "default_domains": ["Travel", "FX Markets", "Savings"],
        "locales": {
            "English": {
                "title": "Travel Budget Strategist",
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
            },
            "Indonesian": {
                "title": "Strateg Keuangan Perjalanan",
                "tagline": "Padukan perencanaan perjalanan dengan pengendalian biaya dan tips mata uang.",
                "focus": [
                    "Mendesain itinerary yang sesuai batas pengeluaran",
                    "Menyoroti biaya lintas negara, valuta asing, dan kebutuhan asuransi",
                    "Menyarankan cara menghemat sebelum dan selama perjalanan",
                ],
                "sample_prompts": [
                    "Rencanakan perjalanan 5 hari ke Tokyo dengan total anggaran di bawah $2.000.",
                    "Bagaimana saya harus menyusun anggaran liburan keluarga ke tiga kota di Uni Eropa?",
                ],
            },
        },
    },
    "productivity_partner": {
        "default_domains": ["Personal Finance", "Productivity", "Behavioral Finance"],
        "locales": {
            "English": {
                "title": "Productivity & Savings Partner",
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
            },
            "Indonesian": {
                "title": "Partner Produktivitas & Tabungan",
                "tagline": "Ubah tujuan keuangan menjadi rutinitas dan pengingat yang konsisten.",
                "focus": [
                    "Menerjemahkan tujuan ke dalam tonggak yang dapat dilacak",
                    "Merekomendasikan otomatisasi, pengingat, dan ritme evaluasi",
                    "Menjaga momentum dengan check-in yang memotivasi",
                ],
                "sample_prompts": [
                    "Bantu saya menyusun sprint 90 hari untuk melunasi utang $5k.",
                    "Otomatisasi apa yang perlu saya buat agar anggaran tetap terjaga?",
                ],
            },
        },
    },
}

USE_CASE_ORDER = list(USE_CASES.keys())

UPLOADABLE_TYPES = ["pdf", "txt", "md", "csv", "png", "jpg", "jpeg", "webp"]
IMAGE_TYPES = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
IMAGE_CAPTION_MODEL = "gemini-1.5-flash-latest"
MAX_DOCUMENT_CHARS = 6000
DOCUMENT_PREVIEW_CHARS = 600
CSV_PREVIEW_ROWS = 80

THEME_OPTIONS = ["System default", "Light", "Dark"]
DARK_THEME_CSS = """
<style>
:root {
    color-scheme: dark;
}
html, body, [data-testid='stAppViewContainer'] {
    background-color: #0f172a;
    color: #f8fafc;
}
[data-testid='stSidebar'] {
    background-color: #111827;
}
.stButton>button {
    background-color: #e11d48;
    color: #f8fafc;
    border: none;
}
.stSelectbox, .stTextInput, .stSlider, .stTextArea {
    color: inherit;
}
</style>
"""
LIGHT_THEME_CSS = """
<style>
:root {
    color-scheme: light;
}
html, body, [data-testid='stAppViewContainer'] {
    background-color: #ffffff;
    color: #0f172a;
}
[data-testid='stSidebar'] {
    background-color: #f5f7fb;
}
.stButton>button {
    background-color: #ef4444;
    color: #ffffff;
    border: none;
}
</style>
"""
DEFAULT_THEME_CSS = """<style></style>"""


def get_language() -> str:
    return st.session_state.get("language_choice", DEFAULT_LANGUAGE)


def tr(key: str, language: str | None = None) -> str:
    lang = language or get_language()
    return LANGUAGE_STRINGS[lang][key]


def apply_theme(choice: str):
    if choice == "Dark":
        st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)
    elif choice == "Light":
        st.markdown(LIGHT_THEME_CSS, unsafe_allow_html=True)
    else:
        st.markdown(DEFAULT_THEME_CSS, unsafe_allow_html=True)


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


def truncate_text(text: str, max_chars: int) -> Tuple[str, bool]:
    if len(text) <= max_chars:
        return text, False
    return text[:max_chars], True


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
    use_case: str,
    tone: str,
    knowledge_domains: List[str],
    risk_band: int,
    horizon: str,
    include_actions: bool,
    include_disclaimer: bool,
    creativity_level: float,
    language: str,
):
    case_locale = USE_CASES[use_case]["locales"][language]
    if knowledge_domains:
        knowledge_text = ", ".join(KNOWLEDGE_OPTION_LABELS[item][language] for item in knowledge_domains)
    else:
        knowledge_text = tr("default_knowledge", language)

    if creativity_level <= 0.3:
        creativity_prompt = CREATIVITY_MODE_TEXT[language]["low"]
    elif creativity_level >= 0.7:
        creativity_prompt = CREATIVITY_MODE_TEXT[language]["high"]
    else:
        creativity_prompt = CREATIVITY_MODE_TEXT[language]["balanced"]

    guidelines = [
        tr("persona_intro", language).format(title=case_locale["title"]),
        tr("persona_mission", language).format(tagline=case_locale["tagline"]),
        tr("persona_expertise", language).format(knowledge=knowledge_text),
        tr("persona_language_style", language).format(language_style=LANGUAGE_STYLE_DESCRIPTIONS[tone][language]),
        tr("persona_risk", language).format(risk=risk_band),
        tr("persona_horizon", language).format(horizon=TIME_HORIZON_LABELS[horizon][language]),
        creativity_prompt,
        tr("persona_grounding", language),
        tr("persona_assumptions", language),
    ]
    if include_actions:
        guidelines.append(tr("persona_actions", language))
    if include_disclaimer:
        guidelines.append(tr("persona_disclaimer", language))
    guidelines.append(tr("persona_language_instruction", language))
    return chr(10).join(guidelines)


def build_structured_prompt(
    *,
    persona_prompt: str,
    user_message: str,
    memory_notes: List[str],
    documents: List[str],
    language: str,
):
    sections = [persona_prompt]
    if memory_notes:
        sections.append(tr("memory_prefix", language) + "; ".join(memory_notes))
    if documents:
        sections.append(tr("documents_label", language) + "\n" + "\n\n".join(documents))
    sections.append(tr("user_request_label", language) + "\n" + user_message)
    sections.append(
        "\n".join(
            [
                tr("response_format_title", language),
                tr("response_step_1", language),
                tr("response_step_2", language),
                tr("response_step_3", language),
                tr("response_step_4", language),
                tr("response_step_5", language),
            ]
        )
    )
    return "\n\n".join(sections)


# --- Session State Defaults ---
if "theme_choice" not in st.session_state:
    st.session_state.theme_choice = THEME_OPTIONS[0]
if "language_choice" not in st.session_state:
    st.session_state.language_choice = DEFAULT_LANGUAGE
if "uploaded_documents" not in st.session_state:
    st.session_state.uploaded_documents = []
if "document_errors" not in st.session_state:
    st.session_state.document_errors = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "memory_notes" not in st.session_state:
    st.session_state.memory_notes = []
if "knowledge_modules" not in st.session_state:
    st.session_state.knowledge_modules = USE_CASES[USE_CASE_ORDER[0]]["default_domains"]
if "_last_use_case" not in st.session_state:
    st.session_state._last_use_case = USE_CASE_ORDER[0]
if "tone_choice" not in st.session_state:
    st.session_state.tone_choice = "Conversational"
if "creativity_level" not in st.session_state:
    st.session_state.creativity_level = 0.4
if "risk_appetite" not in st.session_state:
    st.session_state.risk_appetite = 3
if "planning_horizon" not in st.session_state:
    st.session_state.planning_horizon = TIME_HORIZONS[2]
if "include_actions" not in st.session_state:
    st.session_state.include_actions = True
if "include_disclaimer" not in st.session_state:
    st.session_state.include_disclaimer = True
if "enable_memory" not in st.session_state:
    st.session_state.enable_memory = True

current_language = st.session_state.language_choice

with st.sidebar:
    st.header(tr("assistant_settings"))
    google_api_key = st.text_input(tr("api_key_label"), type="password")

    language_choice = st.selectbox(tr("language_label"), LANGUAGE_OPTIONS, index=LANGUAGE_OPTIONS.index(current_language))
    if language_choice != current_language:
        st.session_state.language_choice = language_choice
        current_language = language_choice

    theme_choice = st.selectbox(tr("theme_label"), THEME_OPTIONS, index=THEME_OPTIONS.index(st.session_state.theme_choice))
    st.session_state.theme_choice = theme_choice

    model_name = st.selectbox(tr("model_label"), MODEL_OPTIONS, index=0)

    use_case = st.selectbox(
        tr("use_case_label"),
        USE_CASE_ORDER,
        index=USE_CASE_ORDER.index(st.session_state._last_use_case),
        format_func=lambda case_id: USE_CASES[case_id]["locales"][current_language]["title"],
    )
    if use_case != st.session_state._last_use_case:
        st.session_state._last_use_case = use_case
        st.session_state.knowledge_modules = USE_CASES[use_case]["default_domains"]

    tone = st.selectbox(
        tr("tone_label"),
        list(LANGUAGE_STYLE_LABELS.keys()),
        format_func=lambda value: LANGUAGE_STYLE_LABELS[value][current_language],
        index=list(LANGUAGE_STYLE_LABELS.keys()).index(st.session_state.tone_choice),
    )
    st.session_state.tone_choice = tone

    creativity_slider = st.slider(
        tr("creativity_label"),
        0.0,
        1.0,
        st.session_state.creativity_level,
        0.05,
        help=tr("creativity_help"),
    )
    st.session_state.creativity_level = creativity_slider

    selected_domains = st.multiselect(
        tr("knowledge_label"),
        KNOWLEDGE_OPTIONS,
        default=st.session_state.knowledge_modules,
        format_func=lambda value: KNOWLEDGE_OPTION_LABELS[value][current_language],
    )
    st.session_state.knowledge_modules = selected_domains

    risk_appetite = st.slider(
        tr("risk_label"),
        1,
        5,
        st.session_state.risk_appetite,
        help=tr("risk_help"),
    )
    st.session_state.risk_appetite = risk_appetite

    planning_horizon = st.selectbox(
        tr("planning_label"),
        TIME_HORIZONS,
        index=TIME_HORIZONS.index(st.session_state.planning_horizon),
        format_func=lambda value: TIME_HORIZON_LABELS[value][current_language],
    )
    st.session_state.planning_horizon = planning_horizon

    include_actions = st.toggle(tr("actions_toggle"), value=st.session_state.include_actions)
    st.session_state.include_actions = include_actions

    include_disclaimer = st.toggle(tr("disclaimer_toggle"), value=st.session_state.include_disclaimer)
    st.session_state.include_disclaimer = include_disclaimer

    enable_memory = st.toggle(tr("memory_toggle"), value=st.session_state.enable_memory)
    st.session_state.enable_memory = enable_memory

    reset_button = st.button(tr("reset_button"), type="primary")

apply_theme(st.session_state.theme_choice)

if reset_button:
    st.session_state.pop("chat", None)
    st.session_state.messages = []
    st.session_state.memory_notes = []
    st.session_state.uploaded_documents = []
    st.session_state.document_errors = []
    st.session_state.knowledge_modules = USE_CASES[use_case]["default_domains"]
    st.rerun()

if not google_api_key:
    st.info(tr("need_api_key"))
    st.stop()

if ("genai_client" not in st.session_state) or (st.session_state.get("_last_key") != google_api_key):
    st.session_state.genai_client = genai.Client(api_key=google_api_key)
    st.session_state._last_key = google_api_key
    st.session_state.pop("chat", None)
    st.session_state.messages = []
    st.session_state.memory_notes = []

profile_signature = "|".join(
    [
        model_name,
        use_case,
        st.session_state.tone_choice,
        ",".join(sorted(st.session_state.knowledge_modules)),
        str(st.session_state.risk_appetite),
        st.session_state.planning_horizon,
        str(st.session_state.include_actions),
        str(st.session_state.include_disclaimer),
        f"creativity={st.session_state.creativity_level:.2f}",
        current_language,
    ]
)

if ("chat" not in st.session_state) or (st.session_state.get("_profile_signature") != profile_signature):
    st.session_state.chat = st.session_state.genai_client.chats.create(model=model_name)
    st.session_state._profile_signature = profile_signature
    st.session_state.messages = []
    st.session_state.memory_notes = []

selected_case_locale = USE_CASES[use_case]["locales"][current_language]

uploaded_files = None
clear_docs_clicked = False

with st.chat_message("assistant"):
    st.markdown(f"**{tr('attachment_header')}**")
    uploaded_files = st.file_uploader(
        tr("attachment_header"),
        type=UPLOADABLE_TYPES,
        accept_multiple_files=True,
        label_visibility="collapsed",
        help=tr("upload_help"),
    )
    clear_docs_clicked = st.button(tr("clear_docs"))

if uploaded_files:
    documents, doc_errors = prepare_documents(uploaded_files, st.session_state.genai_client, model_name)
    st.session_state.uploaded_documents = documents
    st.session_state.document_errors = doc_errors

if clear_docs_clicked:
    st.session_state.uploaded_documents = []
    st.session_state.document_errors = []

if st.session_state.document_errors:
    for error in st.session_state.document_errors:
        st.error(error)

st.title(tr("page_title"))
st.caption(tr("page_caption"))
st.subheader(selected_case_locale["title"])
st.write(selected_case_locale["tagline"])

focus_col, config_col = st.columns([1, 1])
with focus_col:
    st.markdown(f"**{tr('focus_heading')}**")
    for item in selected_case_locale["focus"]:
        st.markdown(f"- {item}")

with config_col:
    st.markdown(f"**{tr('config_heading')}**")
    st.markdown(f"- {tr('config_model')}: `{model_name}`")
    st.markdown(f"- {tr('config_tone')}: {LANGUAGE_STYLE_LABELS[st.session_state.tone_choice][current_language]}")
    domain_labels = ", ".join(KNOWLEDGE_OPTION_LABELS[item][current_language] for item in st.session_state.knowledge_modules) or tr('default_knowledge', current_language)
    st.markdown(f"- {tr('config_domains')}: {domain_labels}")
    st.markdown(f"- {tr('config_risk')}: {st.session_state.risk_appetite}")
    st.markdown(f"- {tr('config_horizon')}: {TIME_HORIZON_LABELS[st.session_state.planning_horizon][current_language]}")
    memory_status = tr('status_enabled') if enable_memory else tr('status_disabled')
    st.markdown(f"- {tr('config_memory')}: {memory_status}")

st.markdown(f"**{tr('samples_heading')}**")
for prompt in selected_case_locale["sample_prompts"]:
    st.markdown(f"- _{prompt}_")

if st.session_state.uploaded_documents:
    with st.expander(tr("doc_expander"), expanded=False):
        for doc in st.session_state.uploaded_documents:
            meta = f"**{doc['name']}** · {doc['char_count']} {tr('characters_label')}"
            if doc["truncated"]:
                meta += tr("truncated_suffix")
            st.markdown(meta)
            st.code(doc["preview"], language="markdown")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_prompt = st.chat_input(tr("chat_placeholder"))

document_context = [
    f"{tr('document_prefix')}: {doc['name']}{tr('truncated_suffix') if doc['truncated'] else ''}{chr(10)}{doc['content']}"
    for doc in st.session_state.uploaded_documents
]

if user_prompt:
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user"):
        st.markdown(user_prompt)

    if enable_memory:
        notes = st.session_state.memory_notes
        notes.append(user_prompt)
        st.session_state.memory_notes = notes[-5:]

    persona_prompt = build_persona_prompt(
        use_case=use_case,
        tone=st.session_state.tone_choice,
        knowledge_domains=st.session_state.knowledge_modules,
        risk_band=st.session_state.risk_appetite,
        horizon=st.session_state.planning_horizon,
        include_actions=st.session_state.include_actions,
        include_disclaimer=st.session_state.include_disclaimer,
        creativity_level=st.session_state.creativity_level,
        language=current_language,
    )

    structured_prompt = build_structured_prompt(
        persona_prompt=persona_prompt,
        user_message=user_prompt,
        memory_notes=st.session_state.memory_notes if enable_memory else [],
        documents=document_context,
        language=current_language,
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
    with st.expander(tr("memory_expander"), expanded=False):
        st.write(chr(10).join(st.session_state.memory_notes))
