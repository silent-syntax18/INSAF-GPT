import streamlit as st
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import os
import re
import hashlib
from pathlib import Path
from io import BytesIO
from dotenv import load_dotenv

# =========================================================
# INSAF GPT — MULTI-AGENT AI LEGAL AID PLATFORM
# =========================================================

BASE_DIR = Path(__file__).resolve().parent
ENV_FILE = BASE_DIR / ".env"
HISTORY_FILE = BASE_DIR / "insaf_history.json"

load_dotenv(dotenv_path=ENV_FILE, override=True)

st.set_page_config(
    page_title="INSAF GPT",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =========================================================
# CUSTOM CSS
# =========================================================

st.markdown("""
<style>

.stApp {
    background:
        radial-gradient(circle at 10% 10%, rgba(32,183,125,.10), transparent 25%),
        radial-gradient(circle at 90% 20%, rgba(57,230,160,.08), transparent 25%),
        linear-gradient(135deg,#06150f 0%,#0b2b21 50%,#04100b 100%);
    color: white;
}

[data-testid="stSidebar"] {
    background: #071c15;
    border-right: 1px solid #176b50;
}

.hero {
    padding: 35px;
    border-radius: 25px;
    background: linear-gradient(135deg,#0d382a,#08251c);
    border: 1px solid #20b77d;
    box-shadow: 0 0 35px rgba(32,183,125,.16);
    margin-bottom: 25px;
}

.hero h1 {
    font-size: 48px;
    color: #39e6a0;
    margin-bottom: 5px;
}

.hero p {
    color: #c9e9dc;
    font-size: 17px;
}

.card {
    padding: 22px;
    border-radius: 18px;
    background: linear-gradient(135deg,#0d3327,#09251d);
    border: 1px solid #176b50;
    margin: 10px 0;
    box-shadow: 0 0 20px rgba(32,183,125,.08);
}

.card h3 {
    color: #39e6a0;
}

.metric-card {
    padding: 20px;
    border-radius: 18px;
    text-align: center;
    background: #0b2920;
    border: 1px solid #176b50;
}

.metric-number {
    font-size: 30px;
    font-weight: bold;
    color: #39e6a0;
}

.agent {
    padding: 14px;
    border-radius: 13px;
    background: #0a251d;
    border: 1px solid #176b50;
    margin: 5px 0;
}

.status {
    color: #54f0aa;
    font-weight: bold;
}

.tag {
    display: inline-block;
    padding: 7px 12px;
    margin: 4px;
    border-radius: 20px;
    background: #123d30;
    border: 1px solid #1f8f68;
    color: #8ff5ca;
    font-size: 13px;
}

.source-box {
    padding: 15px;
    border-radius: 14px;
    background: #081f17;
    border: 1px solid #176b50;
    margin-top: 12px;
}

.action-box {
    padding: 18px;
    border-radius: 15px;
    background: #102d23;
    border-left: 4px solid #39e6a0;
    margin: 10px 0;
}

.small-note {
    color: #a9cfc1;
    font-size: 13px;
}

.disclaimer {
    padding: 16px;
    border-radius: 13px;
    background: #17271f;
    border-left: 4px solid #e0c35a;
    color: #e9e1bd;
    margin-top: 20px;
}

.feature {
    padding: 18px;
    border-radius: 17px;
    background: linear-gradient(135deg,#0b3024,#09231b);
    border: 1px solid #176b50;
    min-height: 145px;
    margin-bottom: 12px;
}

.feature h2 {
    margin-bottom: 5px;
}

.success-feature {
    color: #54f0aa;
    font-weight: bold;
}

.not-feature {
    color: #ff9b9b;
    font-weight: bold;
}

.pdf-box {
    padding: 20px;
    border-radius: 18px;
    background: linear-gradient(135deg,#103b2d,#09251d);
    border: 1px solid #39e6a0;
    margin: 18px 0;
}

.module-header {
    padding: 18px;
    border-radius: 16px;
    background: #0a281f;
    border: 1px solid #176b50;
    margin-bottom: 20px;
}

</style>
""", unsafe_allow_html=True)


# =========================================================
# KNOWLEDGE BASE
# =========================================================

LEGAL_KNOWLEDGE = [

    {
        "topic": "Unpaid Salary / Wages",
        "keywords": [
            "salary", "wage", "wages", "pay", "payment", "unpaid",
            "employer", "employee", "job", "worker", "monthly",
            "income", "tankhwa", "tankhawa", "mazdoori"
        ],
        "information": (
            "An unpaid-salary dispute may involve employment and "
            "labour-law rights. The applicable rules can depend on "
            "the employment relationship, applicable provincial or "
            "federal law, employment contract and workplace circumstances."
        ),
        "documents": [
            "Employment contract",
            "Salary slips",
            "Bank/payment records",
            "Attendance records",
            "Messages or emails with employer"
        ],
        "route": [
            "Relevant labour/employment authority",
            "Employer HR or grievance channel",
            "Qualified employment/labour lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Employment Contract",
        "keywords": [
            "contract", "employment", "agreement", "job", "employee",
            "employer", "termination", "fired", "dismissed", "work",
            "nokri", "mulazmat"
        ],
        "information": (
            "Employment disputes may depend on the terms of the "
            "employment agreement and applicable labour laws. Important "
            "facts include the nature of employment, contract terms, "
            "salary and the reason for the dispute."
        ),
        "documents": [
            "Employment contract",
            "Appointment letter",
            "Salary records",
            "Employer communications"
        ],
        "route": [
            "Employer HR/grievance channel",
            "Relevant labour/employment authority",
            "Qualified employment lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Property / Land Dispute",
        "keywords": [
            "property", "land", "house", "plot", "ownership", "owner",
            "possession", "registry", "sale", "rent", "qabza",
            "zameen", "ghar", "qabze"
        ],
        "information": (
            "Property disputes can involve ownership, possession, title "
            "documents, sale agreements, tenancy arrangements or property "
            "records. The appropriate process depends on the facts and "
            "applicable law."
        ),
        "documents": [
            "Property documents",
            "Sale agreement",
            "Registry/title documents",
            "Payment records",
            "Relevant correspondence",
            "Property or land records"
        ],
        "route": [
            "Relevant land/revenue authority for record-related matters",
            "Relevant civil/legal forum for applicable disputes",
            "Qualified property lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Inheritance / Succession",
        "keywords": [
            "inheritance", "inherit", "heir", "death", "deceased",
            "father", "mother", "brother", "sister", "share",
            "succession", "will", "estate", "warasat", "jaidad"
        ],
        "information": (
            "Inheritance matters can depend on the deceased person's "
            "personal law, succession documents, ownership records and "
            "circumstances of the estate. The exact legal position should "
            "be verified for the particular case."
        ),
        "documents": [
            "Death certificate",
            "Property documents",
            "Family records",
            "Will, if applicable",
            "Succession-related documents"
        ],
        "route": [
            "Relevant succession/civil legal forum",
            "Relevant land/revenue authority for property records",
            "Qualified succession/property lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Online Harassment / Cyber Complaint",
        "keywords": [
            "online", "harassment", "cyber", "whatsapp", "facebook",
            "instagram", "social", "media", "threat", "message",
            "account", "blackmail", "dhamki", "onlineharassment"
        ],
        "information": (
            "Online harassment, threats or other digital misconduct may "
            "involve applicable cybercrime and other laws depending on "
            "the conduct. Preserving digital evidence can be important."
        ),
        "documents": [
            "Screenshots",
            "Messages",
            "Profile/account information",
            "URLs",
            "Relevant files or recordings",
            "Dates and times of incidents"
        ],
        "route": [
            "Relevant cybercrime reporting authority",
            "Appropriate law-enforcement authority where applicable",
            "Qualified lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Police / Criminal Complaint",
        "keywords": [
            "police", "fir", "crime", "criminal", "theft", "stolen",
            "assault", "threat", "complaint", "robbery", "fraud",
            "chori", "maarpeet"
        ],
        "information": (
            "Criminal matters may involve reporting an incident to the "
            "appropriate law-enforcement authority. The correct procedure "
            "depends on the facts, evidence and applicable law."
        ),
        "documents": [
            "Incident details",
            "Identity documents where appropriate",
            "Evidence",
            "Witness information",
            "Relevant communications",
            "Photos/videos where available"
        ],
        "route": [
            "Appropriate local law-enforcement authority",
            "Relevant legal/court forum where applicable",
            "Qualified criminal lawyer",
            "Legal-aid organization where eligible"
        ]
    },

    {
        "topic": "Consumer Complaint",
        "keywords": [
            "consumer", "shop", "product", "seller", "purchase",
            "refund", "defective", "warranty", "customer", "service",
            "company", "dukaan"
        ],
        "information": (
            "Consumer disputes may concern defective products, services, "
            "refunds, warranties or misleading conduct. The available "
            "remedy depends on the transaction and applicable consumer law."
        ),
        "documents": [
            "Receipt",
            "Invoice",
            "Warranty",
            "Product photographs",
            "Messages with seller/company",
            "Order details"
        ],
        "route": [
            "Seller/company complaint channel",
            "Relevant provincial consumer authority/forum",
            "Qualified consumer lawyer where needed",
            "Legal-aid organization where eligible"
        ]
    }
]


# =========================================================
# LANGUAGES / CITIES
# =========================================================

LANGUAGES = [
    "English",
    "Urdu",
    "Roman Urdu",
    "Punjabi",
    "Sindhi",
    "Pashto",
    "Balochi",
    "Saraiki"
]

CITIES = [
    "Karachi",
    "Lahore",
    "Quetta",
    "Peshawar",
    "Multan",
    "Hyderabad",
    "Gilgit",
    "Muzaffarabad",
    "Other"
]


# =========================================================
# HELPERS
# =========================================================

def normalize(text):
    return re.sub(
        r"[^a-z0-9\s]",
        " ",
        str(text).lower()
    ).strip()


def search_legal_knowledge(query):

    text = normalize(query)
    words = set(text.split())
    matches = []

    for item in LEGAL_KNOWLEDGE:

        score = 0
        matched = set()

        for kw in item["keywords"]:

            nkw = normalize(kw)

            if not nkw:
                continue

            if nkw in text:
                score += 3 if " " in nkw else 2
                matched.add(kw)

            elif len(nkw) >= 4 and any(
                w.startswith(nkw) or nkw.startswith(w)
                for w in words
            ):
                score += 1
                matched.add(kw)

        if score:

            matches.append({
                "score": score,
                "matched_words": matched,
                "data": item
            })

    matches.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return matches


def get_best_topic(query):

    matches = search_legal_knowledge(query)

    if matches:
        return matches[0]["data"]

    return None


# =========================================================
# HISTORY
# =========================================================

def load_history():

    try:

        if HISTORY_FILE.exists():

            with open(
                HISTORY_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                data = json.load(f)

                return data if isinstance(data, list) else []

    except Exception:
        pass

    return []


def save_history(
    module,
    query,
    topic,
    answer,
    language=""
):

    history = load_history()

    history.insert(
        0,
        {
            "time": datetime.now().strftime(
                "%d %b %Y %I:%M %p"
            ),
            "module": module,
            "query": str(query)[:500],
            "topic": topic,
            "answer": str(answer)[:3000],
            "language": language
        }
    )

    history = history[:50]

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump(
                history,
                f,
                ensure_ascii=False,
                indent=2
            )

    except Exception:
        pass


def clear_history():

    try:

        with open(
            HISTORY_FILE,
            "w",
            encoding="utf-8"
        ) as f:

            json.dump([], f)

    except Exception:
        pass


def show_history(limit=8):

    history = load_history()

    if not history:

        st.info(
            "🕘 No saved history yet."
        )

        return

    for item in history[:limit]:

        with st.expander(
            f"{item.get('time', '')} • "
            f"{item.get('module', '')} • "
            f"{item.get('topic', '')}"
        ):

            st.write(
                "**Query:**",
                item.get("query", "")
            )

            st.write(
                "**Answer:**",
                item.get("answer", "")
            )

            if item.get("language"):

                st.caption(
                    f"Language: {item['language']}"
                )


# =========================================================
# GROQ API
# =========================================================

def read_env_key():

    try:

        key = os.getenv(
            "GROQ_API_KEY",
            ""
        ).strip()

        if key:
            return key

        if ENV_FILE.exists():

            with open(
                ENV_FILE,
                "r",
                encoding="utf-8"
            ) as f:

                for line in f:

                    line = line.strip()

                    if (
                        line
                        and not line.startswith("#")
                        and line.startswith("GROQ_API_KEY=")
                    ):

                        return (
                            line.split("=", 1)[1]
                            .strip()
                            .strip('"')
                            .strip("'")
                        )

    except Exception:
        pass

    return ""


api_key = read_env_key()


# =========================================================
# VOICE INPUT — GROQ WHISPER
# =========================================================

def transcribe_voice(
    audio_file,
    language="English"
):

    if not audio_file:

        return ""

    if not api_key:

        return (
            "VOICE_ERROR: "
            "Groq API key is not configured."
        )

    try:

        from groq import Groq

        client = Groq(
            api_key=api_key
        )

        language_map = {
            "English": "en",
            "Urdu": "ur",
            "Roman Urdu": None,
            "Punjabi": "pa",
            "Sindhi": "sd",
            "Pashto": "ps",
            "Balochi": None,
            "Saraiki": None
        }

        audio_bytes = audio_file.getvalue()

        args = {
            "file": (
                "insaf_voice.wav",
                audio_bytes,
                getattr(
                    audio_file,
                    "type",
                    None
                ) or "audio/wav"
            ),
            "model": "whisper-large-v3-turbo",
            "response_format": "text"
        }

        whisper_language = language_map.get(
            language
        )

        if whisper_language:

            args["language"] = whisper_language

        result = client.audio.transcriptions.create(
            **args
        )

        if hasattr(result, "text"):

            return result.text.strip()

        return str(result).strip()

    except Exception as e:

        return f"VOICE_ERROR: {str(e)}"


def voice_to_text(
    label,
    language,
    key
):

    audio = st.audio_input(
        label,
        key=key
    )

    if not audio:

        return "", False

    audio_hash = hashlib.sha256(
        audio.getvalue()
    ).hexdigest()

    hash_key = f"{key}_hash"
    text_key = f"{key}_text"

    if st.session_state.get(hash_key) != audio_hash:

        st.session_state[hash_key] = audio_hash

        with st.spinner(
            "🎧 Converting voice to text..."
        ):

            result = transcribe_voice(
                audio,
                language
            )

        if result.startswith("VOICE_ERROR:"):

            st.session_state[text_key] = ""

            st.error(result)

            return "", True

        st.session_state[text_key] = result

        if result:

            st.success(
                "🎤 Voice converted to text!"
            )

            st.caption(
                f"Transcription: {result}"
            )

        return result, True

    return (
        st.session_state.get(
            text_key,
            ""
        ),
        False
    )


# =========================================================
# PDF GENERATOR — STREAMLIT CLOUD SAFE
# =========================================================

def create_pdf(
    title,
    content,
    topic="",
    language="English"
):

    try:

        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import (
            SimpleDocTemplate,
            Paragraph,
            Spacer,
            Table,
            TableStyle
        )
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.enums import TA_CENTER
        from reportlab.lib.units import mm

        buffer = BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=18 * mm,
            leftMargin=18 * mm,
            topMargin=18 * mm,
            bottomMargin=18 * mm
        )

        styles = getSampleStyleSheet()

        title_style = styles["Title"]
        title_style.alignment = TA_CENTER
        title_style.fontSize = 22

        heading_style = styles["Heading2"]
        heading_style.spaceBefore = 10
        heading_style.spaceAfter = 8

        normal = styles["BodyText"]
        normal.leading = 15
        normal.fontSize = 10

        story = []

        story.append(
            Paragraph(
                "INSAF GPT",
                title_style
            )
        )

        story.append(
            Spacer(1, 8)
        )

        story.append(
            Paragraph(
                str(title),
                heading_style
            )
        )

        story.append(
            Spacer(1, 8)
        )

        meta_data = [
            ["Topic", str(topic or "General")],
            ["Language", str(language)],
            [
                "Generated",
                datetime.now().strftime(
                    "%d %B %Y, %I:%M %p"
                )
            ]
        ]

        table = Table(
            meta_data,
            colWidths=[
                35 * mm,
                125 * mm
            ]
        )

        table.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (0, -1),
                    colors.lightgrey
                ),
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "TOP"
                )
            ])
        )

        story.append(table)

        story.append(
            Spacer(1, 15)
        )

        for raw_line in str(content).split("\n"):

            line = raw_line.strip()

            if not line:

                story.append(
                    Spacer(1, 5)
                )

                continue

            line = (
                line
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
            )

            if line.startswith("### "):

                story.append(
                    Paragraph(
                        line[4:],
                        heading_style
                    )
                )

            elif line.startswith("## "):

                story.append(
                    Paragraph(
                        line[3:],
                        heading_style
                    )
                )

            elif line.startswith("# "):

                story.append(
                    Paragraph(
                        line[2:],
                        heading_style
                    )
                )

            else:

                story.append(
                    Paragraph(
                        line,
                        normal
                    )
                )

            story.append(
                Spacer(1, 5)
            )

        story.append(
            Spacer(1, 15)
        )

        disclaimer = (
            "<b>Important:</b> INSAF GPT provides "
            "AI-assisted legal information and drafts. "
            "This document does not replace a qualified lawyer. "
            "Verify current Pakistani law, jurisdiction, "
            "official procedure and document requirements "
            "before formal legal action."
        )

        story.append(
            Paragraph(
                disclaimer,
                normal
            )
        )

        doc.build(story)

        buffer.seek(0)

        return buffer.getvalue()

    except Exception as e:

        st.error(
            f"❌ PDF generation failed: {str(e)}"
        )

        return None


# =========================================================
# AGENTS
# =========================================================

AGENTS = {

    "Zuban Agent": (
        "You are the multilingual intake agent. "
        "Understand the user's language and legal issue, "
        "normalize it into a clear legal problem and explain "
        "it simply. Do not invent laws."
    ),

    "Qanoon Agent": (
        "You are the legal-research agent for Pakistan. "
        "Use ONLY the supplied INSAF knowledge-base context "
        "and information explicitly provided in the prompt. "
        "Do not invent Pakistani law sections, statutes, cases, "
        "authorities, deadlines, penalties, court procedures, "
        "FIR requirements, legal remedies or government requirements. "
        "If the supplied information is insufficient, clearly say "
        "that the matter requires verification under applicable "
        "provincial or federal law and current official procedure."
    ),

    "Musawwid Agent": (
        "You are the legal-drafting agent. "
        "Create a structured AI-assisted draft based only "
        "on user facts and supplied topic context. "
        "Do not invent factual details or legal section numbers."
    ),

    "Rabta Agent": (
        "You are the legal-aid routing agent. "
        "Suggest what type of lawyer, legal-aid organization, "
        "clinic or official authority may be relevant. "
        "Do not invent phone numbers, names, addresses, websites "
        "or contacts."
    ),

    "Amal Agent": (
        "You are the action-planning agent. "
        "Turn the issue into a safe, practical checklist: "
        "preserve evidence, identify the appropriate authority, "
        "prepare documents and verify current procedure. "
        "Do not claim a complaint was submitted."
    )
}


# =========================================================
# GROQ CHAT
# =========================================================

def groq_chat(
    api_key_value,
    system_prompt,
    user_prompt
):

    if not api_key_value:

        return (
            "AGENT_ERROR: "
            "Groq API key is not configured."
        )

    try:

        from groq import Groq

        client = Groq(
            api_key=api_key_value
        )

        response = client.chat.completions.create(
            model="openai/gpt-oss-120b",
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.2,
            max_completion_tokens=1200
        )

        return (
            response
            .choices[0]
            .message
            .content
            .strip()
        )

    except Exception as e:

        return f"AGENT_ERROR: {str(e)}"


# =========================================================
# MULTI-AGENT ENGINE
# =========================================================

def run_multi_agent(
    issue,
    language,
    api_key_value,
    include_draft=False
):

    matches = search_legal_knowledge(issue)

    kb = (
        matches[0]["data"]
        if matches
        else None
    )

    kb_context = (
        "No close topic found in the local knowledge base."
    )

    if kb:

        kb_context = json.dumps(
            {
                "topic": kb["topic"],
                "information": kb["information"],
                "documents": kb["documents"],
                "routing": kb["route"]
            },
            ensure_ascii=False
        )

    user_context = f"""
USER LANGUAGE:
{language}

USER LEGAL ISSUE:
{issue}

LOCAL INSAF GPT KNOWLEDGE-BASE CONTEXT:
{kb_context}

Important:
This is an AI-assisted legal information system.
Do not present uncertain information as a verified legal fact.
"""

    selected = dict(AGENTS)

    if not include_draft:

        selected.pop(
            "Musawwid Agent",
            None
        )

    results = {}

    with ThreadPoolExecutor(
        max_workers=len(selected)
    ) as executor:

        futures = {
            executor.submit(
                groq_chat,
                api_key_value,
                prompt,
                user_context
            ): name
            for name, prompt in selected.items()
        }

        for future in as_completed(futures):

            name = futures[future]

            try:

                results[name] = future.result()

            except Exception as e:

                results[name] = (
                    f"AGENT_ERROR: {str(e)}"
                )

    combined = "\n\n".join(
        [
            f"[{name}]\n{results.get(name, '')}"
            for name in selected
        ]
    )

    orchestrator_prompt = """
You are the INSAF GPT ORCHESTRATOR AGENT for Pakistan.

Combine the specialist-agent reports into one clear,
practical and legally cautious response.

Rules:

- Use the supplied INSAF knowledge base as the primary factual source.
- Never invent Pakistani law sections, statutes, cases or citations.
- Never invent deadlines, penalties or mandatory procedures.
- Never invent FIR requirements.
- Never invent government contacts, phone numbers, addresses or URLs.
- Do not claim a legal notice is always mandatory.
- Do not promise a legal outcome.
- Do not claim a complaint was submitted.
- Do not claim INSAF GPT contacted any authority or lawyer.
- Distinguish general legal information from verified requirements.
- If information is insufficient, say that current official procedure
  should be verified with the relevant authority or qualified lawyer.
- Keep the language simple and practical.

Response structure:

1. Issue understood
2. Relevant legal area
3. General next steps
4. Evidence/documents to preserve
5. Possible routing / where to seek help
6. What needs official verification
7. Important caution
"""

    final_prompt = f"""
USER ISSUE:
{issue}

USER LANGUAGE:
{language}

SPECIALIST AGENT REPORTS:
{combined}

LOCAL KNOWLEDGE-BASE TOPIC:
{kb['topic'] if kb else 'Unknown'}

LOCAL KNOWLEDGE-BASE INFORMATION:
{kb['information'] if kb else 'No close topic found.'}

LOCAL DOCUMENTS:
{', '.join(kb['documents']) if kb else 'None'}

LOCAL ROUTING:
{', '.join(kb['route']) if kb else 'None'}

Answer using only supported information.
"""

    final = groq_chat(
        api_key_value,
        orchestrator_prompt,
        final_prompt
    )

    return (
        results,
        final,
        kb,
        matches
    )


# =========================================================
# RELATED IMAGES
# =========================================================

RELATED_IMAGES = {

    "Unpaid Salary / Wages":
        "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=600&q=70",

    "Employment Contract":
        "https://images.unsplash.com/photo-1450101499163-c8848c66ca85?auto=format&fit=crop&w=600&q=70",

    "Property / Land Dispute":
        "https://images.unsplash.com/photo-1560518883-ce09059eeffa?auto=format&fit=crop&w=600&q=70",

    "Inheritance / Succession":
        "https://images.unsplash.com/photo-1449844908441-8829872d2607?auto=format&fit=crop&w=600&q=70",

    "Online Harassment / Cyber Complaint":
        "https://images.unsplash.com/photo-1563013544-824ae1b704d3?auto=format&fit=crop&w=600&q=70",

    "Police / Criminal Complaint":
        "https://images.unsplash.com/photo-1589829545856-d10d557cf95f?auto=format&fit=crop&w=600&q=70",

    "Consumer Complaint":
        "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?auto=format&fit=crop&w=600&q=70"
}


def show_related_image(
    topic,
    caption="Related visual"
):

    url = RELATED_IMAGES.get(topic)

    if url:

        st.image(
            url,
            caption=f"🖼️ {caption}: {topic}",
            width=230
        )


# =========================================================
# UI HELPERS
# =========================================================

def go_to_page(title):

    st.session_state["main_navigation"] = title


def show_agent_status(
    results=None,
    active=True
):

    st.markdown(
        "### 🤖 Multi-Agent AI Network"
    )

    names = [
        "Zuban Agent",
        "Qanoon Agent",
        "Musawwid Agent",
        "Rabta Agent",
        "Amal Agent",
        "Orchestrator Agent"
    ]

    cols = st.columns(3)

    for i, name in enumerate(names):

        with cols[i % 3]:

            done = (
                results is not None
                and (
                    name == "Orchestrator Agent"
                    or name in results
                )
            )

            label = (
                "● COMPLETE"
                if done
                else (
                    "● READY"
                    if active
                    else "○ IDLE"
                )
            )

            st.markdown(
                f"""
                <div class='agent'>
                    <b>{name}</b><br>
                    <span class='status'>{label}</span>
                </div>
                """,
                unsafe_allow_html=True
            )


def show_sources(
    kb,
    matches=None
):

    st.markdown(
        "### 📚 Legal Knowledge Retrieval"
    )

    if kb:

        st.markdown(
            f"""
            <div class='source-box'>
                <b>📚 INSAF GPT Local Knowledge Base</b><br>
                Topic: {kb['topic']}<br>
                <span class='small-note'>
                Knowledge-grounded local retrieval.
                Verify current official law before formal action.
                </span>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.write(
            "**Knowledge-base information:**"
        )

        st.write(
            kb["information"]
        )

    else:

        st.info(
            "No close topic was found in the local knowledge base."
        )

    if matches:

        matched_topics = [
            item["data"]["topic"]
            for item in matches[:3]
        ]

        if matched_topics:

            st.caption(
                "Related knowledge topics: "
                + " • ".join(matched_topics)
            )


def show_evidence_checklist(kb):

    if not kb:
        return

    st.markdown(
        "### 📎 Evidence Checklist"
    )

    for index, document in enumerate(
        kb["documents"]
    ):

        st.checkbox(
            document,
            key=f"evidence_{normalize(document)}_{index}"
        )


def show_where_to_file(
    kb,
    city
):

    st.markdown(
        "### 🏛️ General Legal Routing"
    )

    if not kb:

        st.info(
            "Describe a more specific legal issue to generate "
            "general routing guidance."
        )

        return

    st.markdown(
        f"""
        <div class='action-box'>
            <b>📍 Selected location:</b> {city}<br>
            <b>⚖️ Legal area:</b> {kb['topic']}
        </div>
        """,
        unsafe_allow_html=True
    )

    for route in kb["route"]:

        st.write(
            "•",
            route
        )

    st.warning(
        "These are general routing categories, not a claim that "
        "a specific authority must handle your case. Verify current "
        "procedure, jurisdiction and contact details directly."
    )


def show_pdf_download(
    pdf_data,
    label,
    file_name,
    key
):

    st.markdown(
        """
        <div class='pdf-box'>
            <h3>📄 PDF Export</h3>
            <p>
            Your document is ready to download.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    if pdf_data:

        st.success(
            "✅ PDF successfully generated!"
        )

        st.download_button(
            label=label,
            data=pdf_data,
            file_name=file_name,
            mime="application/pdf",
            type="primary",
            key=key
        )

    else:

        st.error(
            "❌ PDF could not be generated. "
            "Check that ReportLab is installed."
        )


def render_result(
    final,
    kb,
    matches=None,
    city=None,
    language="English",
    pdf_title="INSAF GPT Legal Report",
    pdf_key="legal_report"
):

    st.markdown(
        "### 🧠 Orchestrator Agent — Final Response"
    )

    st.markdown(
        f"""
        <div class='card'>
            {str(final).replace(chr(10), '<br>')}
        </div>
        """,
        unsafe_allow_html=True
    )

    if not kb:

        st.info(
            "The system could not match this issue to a local "
            "knowledge-base topic."
        )

        return

    show_related_image(
        kb["topic"],
        "Relevant legal topic"
    )

    show_sources(
        kb,
        matches
    )

    show_evidence_checklist(
        kb
    )

    if city:

        show_where_to_file(
            kb,
            city
        )

    pdf_content = (
        f"INSAF GPT — AI-Assisted Legal Report\n\n"
        f"Topic: {kb['topic']}\n"
        f"Language: {language}\n\n"
        f"AI Response:\n{final}\n\n"
        f"Evidence to preserve:\n"
        + "\n".join(
            f"- {d}"
            for d in kb["documents"]
        )
        + "\n\nPossible routing:\n"
        + "\n".join(
            f"- {r}"
            for r in kb["route"]
        )
    )

    pdf_data = create_pdf(
        pdf_title,
        pdf_content,
        kb["topic"],
        language
    )

    show_pdf_download(
        pdf_data,
        "📥 Download Legal Report as PDF",
        "INSAF_GPT_Legal_Report.pdf",
        pdf_key
    )


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.markdown(
        "## ⚖️ INSAF GPT"
    )

    st.caption(
        "Pakistan Multi-Agent AI Legal Aid"
    )

    st.divider()

    if "main_navigation" not in st.session_state:

        st.session_state.main_navigation = (
            "🏠 Dashboard"
        )

    page = st.radio(
        "Navigation",
        [
            "🏠 Dashboard",
            "🌐 Zuban AI",
            "💬 Legal Help",
            "⚖️ Qanoon AI",
            "📄 Musawwid AI",
            "🤝 Rabta AI",
            "🔄 Tarjuman",
            "🏛️ Amal",
            "📊 Admin Analytics",
            "🕘 History"
        ],
        key="main_navigation"
    )

    st.divider()

    language = st.selectbox(
        "🌐 Language",
        LANGUAGES,
        key="global_language"
    )

    if api_key:

        st.success(
            "🔑 Groq API connected"
        )

        st.caption(
            "🎤 Voice input enabled"
        )

    else:

        st.error(
            "❌ Groq API key not found"
        )

        st.caption(
            "Configure GROQ_API_KEY in Streamlit Secrets."
        )

    st.markdown(
        "<p class='status'>● AI SYSTEM ONLINE</p>",
        unsafe_allow_html=True
    )

    st.caption(
        "AI-assisted information • Verify current law"
    )

    st.divider()

    st.markdown(
        "### 🕘 Saved History"
    )

    st.caption(
        f"{len(load_history())} saved request(s)"
    )

    st.button(
        "Open History",
        on_click=go_to_page,
        args=("🕘 History",)
    )

    if st.button(
        "🗑️ Clear History"
    ):

        clear_history()

        st.success(
            "History cleared."
        )

        st.rerun()


# =========================================================
# DASHBOARD
# =========================================================

if page == "🏠 Dashboard":

    st.markdown(
        """
        <div class="hero">
            <h1>⚖️ INSAF GPT</h1>
            <p>Pakistan Multi-Agent AI Legal Aid Platform</p>
            <p>
                One legal issue → specialist AI agents →
                coordinated legal-information response
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

    history = load_history()

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.markdown(
            f"""
            <div class='metric-card'>
                <div class='metric-number'>{len(history)}</div>
                AI Requests
            </div>
            """,
            unsafe_allow_html=True
        )

    with c2:

        st.markdown(
            """
            <div class='metric-card'>
                <div class='metric-number'>8</div>
                Languages
            </div>
            """,
            unsafe_allow_html=True
        )

    with c3:

        st.markdown(
            """
            <div class='metric-card'>
                <div class='metric-number'>5</div>
                Specialist Agents
            </div>
            """,
            unsafe_allow_html=True
        )

    with c4:

        st.markdown(
            """
            <div class='metric-card'>
                <div class='metric-number'>7</div>
                Legal Areas
            </div>
            """,
            unsafe_allow_html=True
        )

    # -----------------------------------------------------
    # IMPLEMENTED FEATURES
    # -----------------------------------------------------

    st.markdown(
        "## ✅ INSAF GPT — Implemented Features"
    )

    implemented_features = [

        ("🤖", "Multi-Agent AI"),
        ("🎯", "Orchestrator Agent"),
        ("📚", "Legal Knowledge Base"),
        ("🔎", "Knowledge Retrieval"),
        ("📄", "PDF Reports"),
        ("📝", "Legal Document Drafting"),
        ("🎤", "Voice Input"),
        ("🗣️", "Groq Whisper"),
        ("🌐", "8 Languages"),
        ("💬", "Legal Help"),
        ("⚖️", "Qanoon AI"),
        ("📄", "Musawwid AI"),
        ("🤝", "Rabta AI"),
        ("🔄", "Tarjuman"),
        ("🏛️", "Amal Action Plan"),
        ("📎", "Evidence Checklist"),
        ("📍", "General Legal Routing"),
        ("🕘", "Local History"),
        ("📊", "Admin Analytics"),
        ("🖼️", "Related Legal Images")
    ]

    feature_cols = st.columns(4)

    for i, (icon, name) in enumerate(
        implemented_features
    ):

        with feature_cols[i % 4]:

            st.markdown(
                f"""
                <div class='feature'>
                    <h2>{icon}</h2>
                    <h4>{name}</h4>
                    <p class='success-feature'>
                        ● IMPLEMENTED
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # NOT IMPLEMENTED
    # -----------------------------------------------------

    st.markdown(
        "## 🔴 Not Currently Implemented"
    )

    not_implemented = [
        (
            "🚫",
            "Automatic Complaint Submission"
        ),
        (
            "🚫",
            "Lawyer Connection / Booking"
        ),
        (
            "🚫",
            "Official Live Pakistani Law Database"
        )
    ]

    not_cols = st.columns(3)

    for i, (icon, name) in enumerate(
        not_implemented
    ):

        with not_cols[i % 3]:

            st.markdown(
                f"""
                <div class='feature'>
                    <h2>{icon}</h2>
                    <h4>{name}</h4>
                    <p class='not-feature'>
                        ● NOT IMPLEMENTED
                    </p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # LANGUAGES
    # -----------------------------------------------------

    st.markdown(
        "## 🌐 Supported Languages"
    )

    language_cols = st.columns(4)

    for i, lang_name in enumerate(
        LANGUAGES
    ):

        with language_cols[i % 4]:

            st.markdown(
                f"""
                <div class='tag'>
                    🌐 {lang_name}
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # CAPABILITIES
    # -----------------------------------------------------

    st.markdown(
        "### 🚀 Core Capabilities"
    )

    features = [
        (
            "🎤",
            "Voice Input",
            "Speak your legal issue"
        ),
        (
            "📚",
            "Knowledge Retrieval",
            "Search local legal knowledge"
        ),
        (
            "📄",
            "PDF Reports",
            "Download generated reports"
        ),
        (
            "📎",
            "Evidence",
            "Organize useful documents"
        ),
        (
            "🏛️",
            "Routing",
            "General legal-aid guidance"
        ),
        (
            "🌐",
            "Languages",
            "8 language options"
        ),
        (
            "🤖",
            "Multi-Agent",
            "Specialist AI workflow"
        ),
        (
            "🕘",
            "History",
            "Save recent requests"
        )
    ]

    feature_cols = st.columns(4)

    for i, (icon, title, desc) in enumerate(
        features
    ):

        with feature_cols[i % 4]:

            st.markdown(
                f"""
                <div class='feature'>
                    <h2>{icon}</h2>
                    <h4>{title}</h4>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

    # -----------------------------------------------------
    # AGENTS
    # -----------------------------------------------------

    show_agent_status(
        active=True
    )

    # -----------------------------------------------------
    # MODULES
    # -----------------------------------------------------

    st.markdown(
        "### 🚀 Open Modules"
    )

    module_cards = [

        (
            "🌐 Zuban AI",
            "Multilingual legal intake"
        ),

        (
            "💬 Legal Help",
            "Describe your legal problem"
        ),

        (
            "⚖️ Qanoon AI",
            "Knowledge-grounded legal research"
        ),

        (
            "📄 Musawwid AI",
            "AI-assisted document drafting"
        ),

        (
            "🤝 Rabta AI",
            "Legal-aid routing"
        ),

        (
            "🔄 Tarjuman",
            "Legal translation"
        ),

        (
            "🏛️ Amal",
            "Action planning"
        ),

        (
            "📊 Admin Analytics",
            "System analytics"
        )
    ]

    cols = st.columns(4)

    for i, (title, desc) in enumerate(
        module_cards
    ):

        with cols[i % 4]:

            st.markdown(
                f"""
                <div class='card'>
                    <h3>{title}</h3>
                    <p>{desc}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.button(
                f"Open {title.split(' ', 1)[1]}",
                key=f"dash_{i}",
                on_click=go_to_page,
                args=(title,)
            )

    # -----------------------------------------------------
    # RECENT HISTORY
    # -----------------------------------------------------

    st.markdown(
        "### 🕘 Recent History"
    )

    show_history(5)


# =========================================================
# ZUBAN AI
# =========================================================

elif page == "🌐 Zuban AI":

    st.title(
        "🌐 Zuban AI — Multilingual Intake"
    )

    st.write(
        "Describe your legal issue in your preferred language."
    )

    lang = st.selectbox(
        "Select language",
        LANGUAGES,
        key="zuban_lang"
    )

    voice_issue, new_voice = voice_to_text(
        "🎤 Record your legal problem",
        lang,
        "voice_zuban"
    )

    if new_voice and voice_issue:

        st.session_state[
            "zuban_text"
        ] = voice_issue

    issue = st.text_area(
        "🗣️ Your legal problem",
        placeholder=(
            "Example: Meri zameen par qabza ho gaya hai..."
        ),
        height=150,
        key="zuban_text"
    )

    if st.button(
        "🤖 Run Multi-Agent Legal Analysis",
        type="primary"
    ):

        if not issue.strip():

            st.warning(
                "Please describe your legal problem first."
            )

        elif not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            with st.spinner(
                "🤖 Specialist agents are analyzing..."
            ):

                results, final, kb, matches = run_multi_agent(
                    issue,
                    lang,
                    api_key,
                    include_draft=False
                )

            show_agent_status(
                results
            )

            if kb:

                st.success(
                    f"✅ Topic detected: {kb['topic']}"
                )

            render_result(
                final,
                kb,
                matches,
                language=lang,
                pdf_title="INSAF GPT Zuban AI Report",
                pdf_key="zuban_pdf"
            )

            save_history(
                "Zuban AI",
                issue,
                kb["topic"] if kb else "Unknown",
                final,
                lang
            )


# =========================================================
# LEGAL HELP
# =========================================================

elif page == "💬 Legal Help":

    st.title(
        "💬 Legal Help"
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_issue, new_voice = voice_to_text(
        "🎤 Record your legal issue",
        language,
        "voice_legal_help"
    )

    if new_voice and voice_issue:

        st.session_state[
            "legal_help_text"
        ] = voice_issue

    issue = st.text_area(
        "📝 Your Legal Issue",
        placeholder=(
            "Example: My employer has not paid my salary "
            "for two months..."
        ),
        height=160,
        key="legal_help_text"
    )

    city = st.selectbox(
        "📍 Your city",
        CITIES,
        key="legal_help_city"
    )

    if st.button(
        "🤖 Analyze My Issue",
        type="primary"
    ):

        if not issue.strip():

            st.error(
                "Please describe your legal issue first."
            )

        elif not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            with st.spinner(
                "Running specialist agents..."
            ):

                results, final, best, matches = run_multi_agent(
                    issue,
                    language,
                    api_key,
                    include_draft=False
                )

            show_agent_status(
                results
            )

            st.success(
                "✅ Multi-agent analysis completed."
            )

            render_result(
                final,
                best,
                matches,
                city=city,
                language=language,
                pdf_title="INSAF GPT Legal Help Report",
                pdf_key="legal_help_pdf"
            )

            save_history(
                "Legal Help",
                issue,
                best["topic"] if best else "Unknown",
                final,
                language
            )


# =========================================================
# QANOON AI
# =========================================================

elif page == "⚖️ Qanoon AI":

    st.title(
        "⚖️ Qanoon AI Agent"
    )

    st.write(
        "Dedicated legal-research agent grounded in "
        "the local INSAF knowledge base."
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_query, new_voice = voice_to_text(
        "🎤 Ask Qanoon Agent by voice",
        language,
        "voice_qanoon"
    )

    if new_voice and voice_query:

        st.session_state[
            "qanoon_text"
        ] = voice_query

    query = st.text_area(
        "🔎 What do you want to know?",
        placeholder=(
            "Example: My employer has not paid my salary "
            "for two months. What legal options may apply?"
        ),
        height=160,
        key="qanoon_text"
    )

    if st.button(
        "⚖️ Ask Qanoon Agent",
        type="primary"
    ):

        if not query.strip():

            st.error(
                "Please enter your legal question first."
            )

        elif not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            matches = search_legal_knowledge(
                query
            )

            kb = (
                matches[0]["data"]
                if matches
                else None
            )

            context = (
                json.dumps(
                    kb,
                    ensure_ascii=False
                )
                if kb
                else "No matching local knowledge-base topic."
            )

            answer = groq_chat(
                api_key,
                AGENTS["Qanoon Agent"],
                (
                    f"Language: {language}\n"
                    f"Question: {query}\n"
                    f"Knowledge base: {context}"
                )
            )

            show_agent_status(
                {
                    "Qanoon Agent": answer
                }
            )

            render_result(
                answer,
                kb,
                matches,
                language=language,
                pdf_title="INSAF GPT Qanoon Report",
                pdf_key="qanoon_pdf"
            )

            save_history(
                "Qanoon AI",
                query,
                kb["topic"] if kb else "Unknown",
                answer,
                language
            )


# =========================================================
# MUSAWWID AI
# =========================================================

elif page == "📄 Musawwid AI":

    st.title(
        "📄 Musawwid AI Agent"
    )

    st.write(
        "Create an AI-assisted legal document draft "
        "from the facts you provide."
    )

    document_type = st.selectbox(
        "📄 Document Type",
        [
            "Legal Notice",
            "Salary Demand Notice",
            "Complaint Application",
            "General Legal Application",
            "Statement"
        ],
        key="document_type"
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_details, new_voice = voice_to_text(
        "🎤 Describe your case by voice",
        language,
        "voice_musawwid"
    )

    if new_voice and voice_details:

        st.session_state[
            "musawwid_details"
        ] = voice_details

    details = st.text_area(
        "📝 Case Details",
        placeholder=(
            "Enter the important facts of your case..."
        ),
        height=180,
        key="musawwid_details"
    )

    if st.button(
        "📄 Generate with Musawwid Agent",
        type="primary"
    ):

        if not details.strip():

            st.error(
                "Please enter case details."
            )

        elif not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            prompt = f"""
Create a structured AI-assisted {document_type} draft.

Language: {language}

User facts:
{details}

Rules:
- Do not invent facts.
- Do not invent legal section numbers.
- Do not invent deadlines.
- Do not create fake authorities or contacts.
- Clearly mark the output as an AI-assisted draft.
"""

            draft = groq_chat(
                api_key,
                AGENTS["Musawwid Agent"],
                prompt
            )

            show_agent_status(
                {
                    "Musawwid Agent": draft
                }
            )

            st.success(
                "✅ Draft generated."
            )

            st.markdown(
                "### 📄 AI-Assisted Draft"
            )

            st.text_area(
                "Draft",
                value=draft,
                height=450
            )

            st.download_button(
                "⬇️ Download TXT Draft",
                data=draft,
                file_name="INSAF_GPT_Legal_Draft.txt",
                mime="text/plain",
                key="musawwid_txt"
            )

            pdf_data = create_pdf(
                f"INSAF GPT — {document_type}",
                draft,
                document_type,
                language
            )

            show_pdf_download(
                pdf_data,
                "📥 Download PDF Draft",
                "INSAF_GPT_Legal_Draft.pdf",
                "musawwid_pdf"
            )

            st.warning(
                "⚠️ AI-assisted draft. Review it carefully and "
                "verify applicable law before formal use."
            )

            save_history(
                "Musawwid AI",
                details,
                document_type,
                draft,
                language
            )


# =========================================================
# RABTA AI
# =========================================================

elif page == "🤝 Rabta AI":

    st.title(
        "🤝 Rabta AI Agent"
    )

    st.write(
        "General legal-aid routing based on your city "
        "and type of legal need."
    )

    city = st.selectbox(
        "📍 Select your city",
        CITIES,
        key="rabta_city"
    )

    category = st.selectbox(
        "🧭 Type of legal-aid need",
        [
            "Free/low-cost legal aid",
            "Lawyer information",
            "Legal clinic",
            "General legal resources"
        ],
        key="rabta_category"
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_issue, new_voice = voice_to_text(
        "🎤 Describe your issue by voice",
        language,
        "voice_rabta"
    )

    if new_voice and voice_issue:

        st.session_state[
            "rabta_issue"
        ] = voice_issue

    issue = st.text_area(
        "📝 Optional issue details",
        height=120,
        key="rabta_issue"
    )

    if st.button(
        "🔎 Run Rabta Agent",
        type="primary"
    ):

        if not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            prompt = f"""
User city: {city}

Need: {category}

Issue:
{issue or 'Not provided'}

Provide general routing guidance.

Do not invent:
- names
- phone numbers
- addresses
- URLs
- fees
- eligibility requirements

Tell the user what type of authority, lawyer,
clinic or legal-aid channel may be relevant.
"""

            answer = groq_chat(
                api_key,
                AGENTS["Rabta Agent"],
                prompt
            )

            show_agent_status(
                {
                    "Rabta Agent": answer
                }
            )

            st.markdown(
                f"""
                <div class='card'>
                    <h3>📍 {city}</h3>
                    <p>{str(answer).replace(chr(10), '<br>')}</p>
                </div>
                """,
                unsafe_allow_html=True
            )

            best = (
                get_best_topic(issue)
                if issue
                else None
            )

            if best:

                show_sources(
                    best
                )

                show_evidence_checklist(
                    best
                )

                show_where_to_file(
                    best,
                    city
                )

            st.warning(
                "Verify current contact details, jurisdiction, "
                "fees and eligibility directly with the relevant "
                "organization."
            )

            save_history(
                "Rabta AI",
                f"{city} — {category} — {issue}",
                category,
                answer,
                language
            )


# =========================================================
# TARJUMAN
# =========================================================

elif page == "🔄 Tarjuman":

    st.title(
        "🔄 Tarjuman — Translation Agent"
    )

    st.write(
        "Translate legal text while preserving its meaning."
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_source, new_voice = voice_to_text(
        "🎤 Speak the text you want to translate",
        language,
        "voice_tarjuman"
    )

    if new_voice and voice_source:

        st.session_state[
            "tarjuman_source"
        ] = voice_source

    source = st.text_area(
        "📝 Text to translate",
        placeholder="Enter legal text...",
        height=180,
        key="tarjuman_source"
    )

    target = st.selectbox(
        "🌐 Translate to",
        LANGUAGES,
        key="translation_target"
    )

    if st.button(
        "🔄 Translate with AI",
        type="primary"
    ):

        if not source.strip():

            st.error(
                "Please enter text first."
            )

        elif not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            output = groq_chat(
                api_key,
                (
                    "You are Tarjuman, a careful multilingual "
                    "legal translation agent. Preserve meaning. "
                    "Do not add facts or legal claims. "
                    "Flag ambiguous wording when necessary."
                ),
                (
                    f"Translate into {target}.\n\n"
                    f"Text:\n{source}"
                )
            )

            show_agent_status(
                {
                    "Tarjuman Agent": output
                }
            )

            st.success(
                f"Translation completed → {target}"
            )

            st.text_area(
                "Translation Output",
                value=output,
                height=240
            )

            st.download_button(
                "⬇️ Download Translation",
                data=output,
                file_name="INSAF_GPT_Translation.txt",
                mime="text/plain",
                key="tarjuman_download"
            )

            save_history(
                "Tarjuman",
                source,
                target,
                output,
                language
            )


# =========================================================
# AMAL
# =========================================================

elif page == "🏛️ Amal":

    st.title(
        "🏛️ Amal — Action Agent"
    )

    st.write(
        "Turn a legal issue into an organized action checklist."
    )

    issue_type = st.selectbox(
        "⚖️ Issue type",
        [
            "Property / Land",
            "Employment / Salary",
            "Cyber / Online Harassment",
            "Police / Criminal",
            "Consumer",
            "Inheritance"
        ],
        key="amal_issue_type"
    )

    evidence = st.multiselect(
        "📎 Evidence available",
        [
            "CNIC/identity document",
            "Contract",
            "Receipts",
            "Screenshots",
            "Messages",
            "Property documents",
            "Witness details",
            "Photos/videos",
            "Other"
        ],
        key="amal_evidence"
    )

    city = st.selectbox(
        "📍 City",
        CITIES,
        key="amal_city"
    )

    st.caption(
        f"🎤 Voice input language: {language}"
    )

    voice_details, new_voice = voice_to_text(
        "🎤 Describe the case facts by voice",
        language,
        "voice_amal"
    )

    if new_voice and voice_details:

        st.session_state[
            "amal_details"
        ] = voice_details

    details = st.text_area(
        "📝 Brief facts",
        height=120,
        key="amal_details"
    )

    if st.button(
        "🏛️ Build Action Plan",
        type="primary"
    ):

        if not api_key:

            st.error(
                "Groq API key required."
            )

        else:

            prompt = f"""
Issue: {issue_type}

City: {city}

Facts:
{details or 'Not provided'}

Evidence available:
{', '.join(evidence) if evidence else 'None'}

Create a practical action checklist.

Include:
1. Immediate evidence preservation
2. Documents to organize
3. General authority/routing category
4. Questions to ask a lawyer/authority
5. Things that require current official verification

Do not claim that any complaint has been submitted.
Do not invent contacts or legal deadlines.
"""

            answer = groq_chat(
                api_key,
                AGENTS["Amal Agent"],
                prompt
            )

            show_agent_status(
                {
                    "Amal Agent": answer
                }
            )

            issue_topic_map = {

                "Property / Land":
                    "Property / Land Dispute",

                "Employment / Salary":
                    "Unpaid Salary / Wages",

                "Cyber / Online Harassment":
                    "Online Harassment / Cyber Complaint",

                "Police / Criminal":
                    "Police / Criminal Complaint",

                "Consumer":
                    "Consumer Complaint",

                "Inheritance":
                    "Inheritance / Succession"
            }

            target_topic = issue_topic_map[
                issue_type
            ]

            kb = next(
                (
                    item
                    for item in LEGAL_KNOWLEDGE
                    if item["topic"] == target_topic
                ),
                None
            )

            if kb:

                show_related_image(
                    kb["topic"],
                    "Action-plan topic"
                )

            st.markdown(
                f"### ⚖️ {issue_type}"
            )

            st.markdown(
                f"""
                <div class='card'>
                    {str(answer).replace(chr(10), '<br>')}
                </div>
                """,
                unsafe_allow_html=True
            )

            if kb:

                st.markdown(
                    "### 📎 Evidence Checklist"
                )

                for index, item in enumerate(
                    kb["documents"]
                ):

                    st.checkbox(
                        item,
                        key=f"amal_check_{index}_{normalize(item)}"
                    )

                st.markdown(
                    "### 🏛️ General Routing"
                )

                for route in kb["route"]:

                    st.write(
                        "•",
                        route
                    )

                pdf_content = (
                    f"Issue: {issue_type}\n"
                    f"City: {city}\n\n"
                    f"Action Plan:\n{answer}\n\n"
                    f"Evidence:\n"
                    + "\n".join(
                        f"- {d}"
                        for d in kb["documents"]
                    )
                    + "\n\nRouting:\n"
                    + "\n".join(
                        f"- {r}"
                        for r in kb["route"]
                    )
                )

                pdf_data = create_pdf(
                    "INSAF GPT — Amal Action Plan",
                    pdf_content,
                    kb["topic"],
                    language
                )

                show_pdf_download(
                    pdf_data,
                    "📥 Download Action Plan PDF",
                    "INSAF_GPT_Action_Plan.pdf",
                    "amal_pdf"
                )

            st.warning(
                "INSAF GPT does not automatically submit complaints. "
                "Verify official procedure and jurisdiction."
            )

            save_history(
                "Amal",
                details or issue_type,
                issue_type,
                answer,
                language
            )


# =========================================================
# ADMIN ANALYTICS
# =========================================================

elif page == "📊 Admin Analytics":

    st.title(
        "📊 Admin Analytics"
    )

    history = load_history()

    drafts = sum(
        1
        for h in history
        if h.get("module") == "Musawwid AI"
    )

    languages_used = set(
        h.get("language")
        for h in history
        if h.get("language")
    )

    modules_used = set(
        h.get("module")
        for h in history
        if h.get("module")
    )

    c1, c2, c3, c4 = st.columns(4)

    with c1:

        st.metric(
            "Total AI Requests",
            len(history)
        )

    with c2:

        st.metric(
            "Legal Drafts",
            drafts
        )

    with c3:

        st.metric(
            "Languages Used",
            len(languages_used)
        )

    with c4:

        st.metric(
            "Agents",
            6
        )

    st.markdown(
        "### 🤖 Agent Network"
    )

    show_agent_status(
        active=True
    )

    st.markdown(
        "### 📈 Module Usage"
    )

    if modules_used:

        module_counts = {}

        for item in history:

            module = item.get(
                "module",
                "Unknown"
            )

            module_counts[module] = (
                module_counts.get(module, 0) + 1
            )

        for module, count in sorted(
            module_counts.items(),
            key=lambda x: x[1],
            reverse=True
        ):

            st.write(
                f"**{module}:** {count} request(s)"
            )

    else:

        st.info(
            "Analytics will appear after users make requests."
        )

    st.markdown(
        "### 🕘 Recent Requests"
    )

    show_history(10)


# =========================================================
# HISTORY
# =========================================================

elif page == "🕘 History":

    st.title(
        "🕘 Saved History"
    )

    st.write(
        "Your recent AI requests are stored locally in "
        "`insaf_history.json`."
    )

    history = load_history()

    if history:

        st.success(
            f"{len(history)} request(s) saved."
        )

        show_history(50)

        st.divider()

        if st.button(
            "🗑️ Delete All Saved History",
            type="secondary"
        ):

            clear_history()

            st.rerun()

    else:

        st.info(
            "No history saved yet."
        )


# =========================================================
# FINAL DISCLAIMER
# =========================================================

st.markdown(
    """
    <div class='disclaimer'>
    ⚠️ <b>Important:</b> INSAF GPT provides AI-assisted legal
    information, document drafts and general routing guidance.
    It does not replace a qualified lawyer. Information may be
    incomplete or outdated. Verify current Pakistani law,
    jurisdiction, official procedure and any legal document
    with an appropriate qualified professional before formal action.
    </div>
    """,
    unsafe_allow_html=True
)
