import os
import re
from langchain_groq import ChatGroq
import streamlit as st

st.set_page_config(
    page_title="NexusPolicy • AI Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# Modern Responsive Mobile-First Styling
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    .stApp {
        background-color: #0b0f19;
        color: #f3f4f6;
    }
    
    /* Responsive Hero Header */
    .hero-container {
        padding: 1.25rem;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        margin-bottom: 1.2rem;
    }
    
    .hero-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 8px;
        flex-wrap: wrap;
    }

    .hero-title {
        font-size: clamp(1.25rem, 5vw, 1.85rem) !important;
        font-weight: 800 !important;
        color: #60a5fa !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        word-break: keep-all;
        white-space: nowrap;
    }
    
    .hero-subtitle {
        color: #9ca3af;
        font-size: 0.85rem;
        margin-top: 0.35rem;
        line-height: 1.4;
    }
    
    .status-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
        white-space: nowrap;
    }

    /* Message Bubbles */
    .stChatMessage {
        border-radius: 12px !important;
        background: #111827 !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 8px !important;
        padding: 10px 14px !important;
    }

    /* Source Tag */
    .source-tag {
        display: inline-block;
        font-size: 0.72rem;
        background: rgba(96, 165, 250, 0.15);
        color: #93c5fd;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        border: 1px solid rgba(96, 165, 250, 0.3);
        font-weight: 500;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 10px;
        border: 1px solid #374151;
        background: #1f2937;
        color: #e5e7eb;
        font-size: 0.82rem;
        padding: 0.45rem 0.8rem;
    }
    .stButton > button:hover {
        border-color: #60a5fa;
        color: #ffffff;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# Knowledge Base & Retrieval
# -------------------------------------------------------------
POLICY_DB = [
    {
        "id": "attendance",
        "title": "Attendance & Eligibility Rules",
        "content": (
            "Attendance Policy: A strict minimum of 80% attendance is"
            " mandatory for exam eligibility, lab access, and final course"
            " certification. Candidates falling below 80% require academic"
            " condonation."
        ),
        "keywords": [
            "attendance",
            "present",
            "absent",
            "percentage",
            "exam",
            "qualification",
            "certification",
        ],
    },
    {
        "id": "leave",
        "title": "Leave & Absence Policy",
        "content": (
            "Leave Policy: Team members can take up to 3 consecutive days of"
            " leave with written notice. Leaves exceeding 3 days require"
            " medical or formal verification submitted in advance."
        ),
        "keywords": [
            "leave",
            "sick",
            "days",
            "vacation",
            "absence",
            "off",
            "consecutive",
        ],
    },
    {
        "id": "capstone",
        "title": "Capstone Submission Criteria",
        "content": (
            "Submission Guidelines: Capstone deliverables must include: 1)"
            " Public GitHub repository. 2) README with architecture diagram. 3)"
            " Live demo URL. Late submissions face a 10% daily grade deduction."
        ),
        "keywords": [
            "capstone",
            "submission",
            "github",
            "deadline",
            "project",
            "guidelines",
            "diagram",
        ],
    },
    {
        "id": "reimbursement",
        "title": "Travel & Expense Guidelines",
        "content": (
            "Expense Policy: Travel or tool purchases exceeding $50 / ₹4,000"
            " require prior manager approval. Digital receipts must be submitted"
            " within 7 business days."
        ),
        "keywords": [
            "expense",
            "travel",
            "claim",
            "reimbursement",
            "money",
            "budget",
            "receipt",
        ],
    },
]


def fast_retrieve(query: str):
  q_tokens = set(re.findall(r"\w+", query.lower()))
  best_doc = POLICY_DB[0]
  best_score = -1

  for item in POLICY_DB:
    score = sum(2 for k in item["keywords"] if k in q_tokens)
    doc_words = set(re.findall(r"\w+", item["content"].lower()))
    score += len(q_tokens.intersection(doc_words))
    if score > best_score:
      best_score = score
      best_doc = item

  return best_doc


# -------------------------------------------------------------
# Sidebar
# -------------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚙️ **Settings & Prompts**")
  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq API Key:", type="password")

  st.markdown("---")
  st.markdown("**Suggested Questions:**")
  presets = [
      "What is the minimum attendance required?",
      "Can I take 4 consecutive days of leave?",
      "What are the capstone submission deliverables?",
      "What is the policy on travel expenses?",
  ]
  for p in presets:
    if st.button(p, use_container_width=True):
      st.session_state.pending_prompt = p

  st.markdown("---")
  if st.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# -------------------------------------------------------------
# Responsive Hero UI
# -------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div class="hero-header-row">
            <h1 class="hero-title">NexusPolicy AI</h1>
            <span class="status-badge">● Online</span>
        </div>
        <div class="hero-subtitle">Instant Grounded Policy & Institutional Guidelines Copilot</div>
    </div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "Hello! Ask any question regarding institutional guidelines,"
          " attendance criteria, or capstone deliverables."
      ),
  }]

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

prompt_from_chip = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask any guideline or rule...") or prompt_from_chip

if user_prompt:
  if not groq_key:
    st.error("Please provide your Groq API key in Secrets or the sidebar.")
    st.stop()

  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.markdown(user_prompt)

  # Retrieve context
  matched = fast_retrieve(user_prompt)

  # Ultra-fast Groq model
  llm = ChatGroq(
      model="openai/gpt-oss-20b",
      api_key=groq_key,
      temperature=0.1,
      streaming=True,
  )

      system_prompt = f"""You are an intelligent Policy Copilot and technical assistant.

Context:
Title: {matched['title']}
Content: {matched['content']}

User Question: {user_prompt}

Instructions:
1. If the question relates to policies, attendance, leaves, capstone rules, or claims, base your answer strictly on the context above.
2. If the user is asking a general technical, coding, or website design question, answer helpfully and concisely using your general technical knowledge.
"""


  with st.chat_message("assistant"):
    st.markdown(
        f'<span class="source-tag">📄 Source: {matched["title"]}</span>',
        unsafe_allow_html=True,
    )

    def stream_generator():
      for chunk in llm.stream(system_prompt):
        if chunk.content:
          yield chunk.content

    response_text = st.write_stream(stream_generator())

  st.session_state.messages.append(
      {"role": "assistant", "content": response_text}
  )
