import os
import re
from langchain_groq import ChatGroq
from pypdf import PdfReader
import streamlit as st

st.set_page_config(
    page_title="NexusDoc AI • Enterprise Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# Dynamic Sidebar Theme & Branding Controls
# -------------------------------------------------------------
with st.sidebar:
  st.markdown("### 🎨 **Brand & Theme Settings**")

  brand_name = st.text_input("Brand / Client Name:", value="NexusDoc AI")

  theme_choice = st.selectbox(
      "Accent Theme Color:",
      ["Electric Blue", "Emerald Mint", "Cyber Violet", "Sunset Gold"],
  )

  theme_colors = {
      "Electric Blue": {"primary": "#38bdf8", "border": "#0284c7"},
      "Emerald Mint": {"primary": "#34d399", "border": "#059669"},
      "Cyber Violet": {"primary": "#c084fc", "border": "#9333ea"},
      "Sunset Gold": {"primary": "#fbbf24", "border": "#d97706"},
  }
  selected_color = theme_colors[theme_choice]["primary"]
  selected_border = theme_colors[theme_choice]["border"]

  st.markdown("---")
  st.markdown("### ⚙️ **Engine Config**")
  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq API Key:", type="password")

  st.markdown("---")
  st.markdown("### 📁 **Upload Custom Document**")
  uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])

  st.markdown("---")
  st.markdown("**Suggested Prompts:**")
  presets = [
      "What is the minimum attendance required?",
      "Can I take 4 consecutive days of leave?",
      "What are the capstone submission deliverables?",
      "Summarize the active document.",
  ]
  for p in presets:
    if st.button(p, use_container_width=True):
      st.session_state.pending_prompt = p

  st.markdown("---")
  if st.button("🗑️ Clear Chat", use_container_width=True):
    st.session_state.messages = []
    st.rerun()

# -------------------------------------------------------------
# Responsive Modern Styling with Dynamic Accents
# -------------------------------------------------------------
st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * {{ font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }}
    .stApp {{ background-color: #0b0f19; color: #f3f4f6; }}
    
    .hero-container {{
        padding: 1.15rem 1.4rem;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        margin-bottom: 1.2rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.35);
    }}
    
    .hero-header-row {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }}

    .brand-group {{
        display: flex;
        align-items: center;
        gap: 12px;
    }}

    .brand-avatar {{
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, {selected_color}, {selected_border});
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0b0f19;
        font-weight: 800;
        font-size: 1.1rem;
        box-shadow: 0 0 15px {selected_color}44;
    }}

    .hero-title {{
        font-size: clamp(1.2rem, 4.5vw, 1.75rem) !important;
        font-weight: 800 !important;
        color: {selected_color} !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        white-space: nowrap;
    }}
    
    .hero-subtitle {{
        color: #9ca3af;
        font-size: 0.84rem;
        margin-top: 0.35rem;
        line-height: 1.4;
    }}
    
    .status-badge {{
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        white-space: nowrap;
    }}

    .stChatMessage {{
        border-radius: 12px !important;
        background: #111827 !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 8px !important;
        padding: 10px 14px !important;
    }}

    .source-tag {{
        display: inline-block;
        font-size: 0.72rem;
        background: {selected_color}18;
        color: {selected_color};
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        border: 1px solid {selected_color}44;
        font-weight: 500;
    }}

    .stButton > button {{
        border-radius: 10px;
        border: 1px solid #374151;
        background: #1f2937;
        color: #e5e7eb;
        font-size: 0.82rem;
        padding: 0.45rem 0.8rem;
    }}
    .stButton > button:hover {{ border-color: {selected_color}; color: #ffffff; }}
    </style>
""",
    unsafe_allow_html=True,
)

# -------------------------------------------------------------
# Knowledge Base & Retrieval Logic
# -------------------------------------------------------------
DEFAULT_POLICIES = [
    {
        "id": "attendance",
        "title": "Attendance & Eligibility Rules",
        "content": (
            "Attendance Policy: A strict minimum of 80% attendance is"
            " mandatory for exam eligibility, lab access, and final course"
            " certification. Candidates falling below 80% require academic"
            " condonation."
        ),
    },
    {
        "id": "leave",
        "title": "Leave & Absence Policy",
        "content": (
            "Leave Policy: Team members can take up to 3 consecutive days of"
            " leave with written notice. Leaves exceeding 3 days require"
            " medical or formal verification submitted in advance."
        ),
    },
    {
        "id": "capstone",
        "title": "Capstone Submission Criteria",
        "content": (
            "Submission Guidelines: Capstone deliverables must include: 1)"
            " Public GitHub repository. 2) README with architecture diagram. 3)"
            " Live demo URL. Late submissions face a 10% daily grade deduction."
        ),
    },
    {
        "id": "reimbursement",
        "title": "Travel & Expense Guidelines",
        "content": (
            "Expense Policy: Travel or tool purchases exceeding $50 / ₹4,000"
            " require prior manager approval. Digital receipts must be submitted"
            " within 7 business days."
        ),
    },
]


def extract_pdf_chunks(pdf_file):
  reader = PdfReader(pdf_file)
  full_text = ""
  for page in reader.pages:
    text = page.extract_text()
    if text:
      full_text += text + "\n"

  words = full_text.split()
  chunk_size = 350
  chunks = []
  for i in range(0, len(words), chunk_size):
    chunk_str = " ".join(words[i : i + chunk_size])
    chunks.append({
        "id": f"chunk_{i}",
        "title": f"{pdf_file.name} (Part {i//chunk_size + 1})",
        "content": chunk_str,
    })
  return chunks if chunks else DEFAULT_POLICIES


def score_and_retrieve(query: str, doc_list: list):
  q_tokens = set(re.findall(r"\w+", query.lower()))
  best_doc = doc_list[0]
  best_score = -1

  for item in doc_list:
    doc_words = set(re.findall(r"\w+", item["content"].lower()))
    score = len(q_tokens.intersection(doc_words))
    if score > best_score:
      best_score = score
      best_doc = item

  return best_doc


# Handle document source
if uploaded_pdf is not None:
  if (
      "current_pdf_name" not in st.session_state
      or st.session_state.current_pdf_name != uploaded_pdf.name
  ):
    with st.spinner("Indexing PDF..."):
      st.session_state.active_docs = extract_pdf_chunks(uploaded_pdf)
      st.session_state.current_pdf_name = uploaded_pdf.name
else:
  st.session_state.active_docs = DEFAULT_POLICIES
  st.session_state.current_pdf_name = "Institutional Policies"

# -------------------------------------------------------------
# Hero UI
# -------------------------------------------------------------
active_source_label = st.session_state.get(
    "current_pdf_name", "Institutional Policies"
)
first_initial = brand_name.strip()[0].upper() if brand_name.strip() else "N"

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-header-row">
            <div class="brand-group">
                <div class="brand-avatar">{first_initial}</div>
                <div>
                    <h1 class="hero-title">{brand_name}</h1>
                    <div class="hero-subtitle">Intelligent RAG Assistant • Active Source: {active_source_label[:22]}</div>
                </div>
            </div>
            <span class="status-badge">● Online</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          f"Welcome to **{brand_name}**! Ask questions regarding the active"
          " documentation or upload your custom PDF in the sidebar."
      ),
  }]

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

prompt_from_chip = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask any question or guideline...") or prompt_from_chip

if user_prompt:
  if not groq_key:
    st.error("Please provide your Groq API key in Secrets or the sidebar.")
    st.stop()

  st.session_state.messages.append({"role": "user", "content": user_prompt})
  with st.chat_message("user"):
    st.markdown(user_prompt)

  matched = score_and_retrieve(user_prompt, st.session_state.active_docs)

  llm = ChatGroq(
      model="openai/gpt-oss-20b",
      api_key=groq_key,
      temperature=0.1,
      streaming=True,
  )

  system_prompt = (
      f"You are the official intelligence copilot for {brand_name}.\n\n"
      f"Context Source: {matched['title']}\n"
      f"Context Excerpt:\n{matched['content']}\n\n"
      f"User Question: {user_prompt}\n\n"
      "Instructions:\n"
      "1. If the question relates to the provided document context, answer"
      " accurately and cite the context directly.\n"
      "2. If the user asks a general coding, engineering, or technical"
      " question outside the document, answer clearly and helpfully using your"
      " general technical knowledge."
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
