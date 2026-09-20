import os
import re
from langchain_groq import ChatGroq
import streamlit as st

st.set_page_config(
    page_title="NexusPolicy • AI Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# Modern Cyber-Glassmorphic Styling
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;700;800&display=swap');
    
    * {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    /* Background Gradient */
    .stApp {
        background: radial-gradient(circle at 10% 20%, rgb(18, 20, 32) 0%, rgb(10, 11, 18) 90.2%);
        color: #f1f5f9;
    }
    
    /* Sleek Hero Banner */
    .hero-container {
        padding: 2.2rem 2rem;
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 20px;
        backdrop-filter: blur(16px);
        margin-bottom: 2rem;
        box-shadow: 0 20px 40px -15px rgba(0,0,0,0.6);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }
    
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        background: linear-gradient(135deg, #38bdf8 0%, #818cf8 50%, #c084fc 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .hero-badge {
        background: rgba(56, 189, 248, 0.12);
        color: #38bdf8;
        border: 1px solid rgba(56, 189, 248, 0.3);
        padding: 6px 14px;
        border-radius: 9999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    
    /* Chat Bubbles */
    .stChatMessage {
        border-radius: 16px !important;
        margin-bottom: 12px !important;
        padding: 14px 18px !important;
        background: rgba(255, 255, 255, 0.04) !important;
        border: 1px solid rgba(255, 255, 255, 0.07) !important;
        transition: all 0.2s ease-in-out;
    }
    
    .stChatMessage:hover {
        border-color: rgba(99, 102, 241, 0.3) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25);
    }
    
    /* Clean Sidebar */
    [data-testid="stSidebar"] {
        background: rgba(14, 16, 26, 0.95) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    /* Prompt Chip Buttons */
    .stButton > button {
        background: rgba(255, 255, 255, 0.04);
        border: 1px solid rgba(255, 255, 255, 0.1);
        color: #cbd5e1;
        border-radius: 12px;
        padding: 0.6rem 1rem;
        font-size: 0.85rem;
        font-weight: 500;
        transition: all 0.2s ease;
        text-align: left;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15), rgba(129, 140, 248, 0.15));
        border-color: #818cf8;
        color: #ffffff;
        transform: translateY(-1px);
    }
    
    /* Source Pill Tag */
    .source-tag {
        display: inline-block;
        font-size: 0.75rem;
        background: rgba(99, 102, 241, 0.15);
        color: #a5b4fc;
        padding: 2px 8px;
        border-radius: 6px;
        margin-bottom: 8px;
        border: 1px solid rgba(99, 102, 241, 0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# Knowledge Base
# -------------------------------------------------------------
POLICY_DB = [
    {
        "id": "attendance",
        "title": "Attendance & Eligibility Rules",
        "content": (
            "Attendance Policy: A strict minimum of 80% attendance is"
            " mandatory for exam eligibility, lab access, and final course"
            " certification. Candidates below 80% require special academic dean"
            " condonation."
        ),
        "keywords": ["attendance", "present", "absent", "percentage", "exam", "qualification", "certification"]
    },
    {
        "id": "leave",
        "title": "Leave & Absence Policy",
        "content": (
            "Leave Policy: Team members are entitled to up to 3 consecutive"
            " days of absence with written mentor or manager notification."
            " Leaves exceeding 3 days require formal medical or personal proof"
            " submitted 48 hours in advance."
        ),
        "keywords": ["leave", "sick", "days", "vacation", "absence", "off", "consecutive"]
    },
    {
        "id": "capstone",
        "title": "Capstone Submission Criteria",
        "content": (
            "Submission Guidelines: Capstone deliverables must include: 1) A"
            " verified public GitHub repository. 2) A comprehensive README with"
            " system architecture diagram. 3) A deployed live demo URL or cloud"
            " link. Late submissions face a 10% daily grade deduction."
        ),
        "keywords": ["capstone", "submission", "github", "deadline", "project", "guidelines", "diagram"]
    },
    {
        "id": "reimbursement",
        "title": "Travel & Expense Claim Guidelines",
        "content": (
            "Expense Policy: Any travel or tool expense exceeding $50 / ₹4,000"
            " requires prior approval from the department lead. Original digital"
            " tax receipts must be uploaded within 7 business days."
        ),
        "keywords": ["expense", "travel", "claim", "reimbursement", "money", "budget", "receipt"]
    }
]

# High-speed keyword + semantic overlap retriever (instant execution)
def ultra_fast_retriever(query: str):
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
# Sidebar Configuration
# -------------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚡ **NexusPolicy Control**")
  st.caption("Agentic RAG Engine • Ultra-Low Latency")

  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq Key:", type="password")

  st.markdown("---")
  st.markdown("##### 🚀 **Recommended Prompts**")
  presets = [
      "What is the minimum attendance required?",
      "Can I take 4 days of leave consecutively?",
      "What are the capstone submission deliverables?",
      "What is the policy on travel expense claims?",
  ]
  for p in presets:
    if st.button(p, use_container_width=True):
      st.session_state.pending_prompt = p

  st.markdown("---")
  if st.button("🧹 Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# -------------------------------------------------------------
# Hero Interface
# -------------------------------------------------------------
st.markdown(
    """
    <div class="hero-container">
        <div>
            <h1 class="hero-title">NexusPolicy AI</h1>
            <p style="color: #94a3b8; margin: 4px 0 0 0; font-size: 0.95rem;">
                Autonomous Grounded Policy & Institutional Guidelines Copilot
            </p>
        </div>
        <div class="hero-badge">● Engine Online</div>
    </div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = [
      {
          "role": "assistant",
          "content": (
              "Hello! I am your autonomous policy intelligence copilot. Ask me"
              " any question regarding attendance criteria, leave allowances, or"
              " capstone guidelines."
          ),
      }
  ]

# Render chat messages
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

# Collect user prompt
prompt_from_chip = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask any guideline or rule...") or prompt_from_chip

if user_prompt:
  if not groq_key:
    st.error("Please provide a valid Groq API key in Secrets or the sidebar.")
    st.stop()

  # Show user query
  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.markdown(user_prompt)

  # 1. Zero-latency context retrieval
  matched = ultra_fast_retriever(user_prompt)

  # 2. Real-time streaming via Groq LPU
  llm = ChatGroq(
      model="llama-3.3-70b-versatile",
      api_key=groq_key,
      temperature=0.1,
      streaming=True,
  )

  system_prompt = (
      f"Context:\nTitle: {matched['title']}\nContent: {matched['content']}\n\n"
      f"User Question: {user_prompt}\n\n"
      "Instructions: Answer directly, authoritatively, and concisely. Use"
      " clean bullet points when helpful. Never guess."
  )

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
    
