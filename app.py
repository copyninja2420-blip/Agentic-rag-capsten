
        
                  import os
import re
from langchain_groq import ChatGroq
from pypdf import PdfReader
import streamlit as st

st.set_page_config(
    page_title="NexusDoc AI • Smart Document Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -------------------------------------------------------------
# Responsive Mobile-First Styling
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

    .stChatMessage {
        border-radius: 12px !important;
        background: #111827 !important;
        border: 1px solid #1f2937 !important;
        margin-bottom: 8px !important;
        padding: 10px 14px !important;
    }

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
# Default Knowledge Base
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


def extract_pdf_chunks(uploaded_file):
  reader = PdfReader(uploaded_file)
  full_text = ""
  for page in reader.pages:
    text = page.extract_text()
    if text:
      full_text += text + "\n"

  # Split text into bite-sized chunks (~400 words each)
  words = full_text.split()
  chunk_size = 350
  chunks = []
  for i in range(0, len(words), chunk_size):
    chunk_str = " ".join(words[i : i + chunk_size])
    chunks.append({
        "id": f"chunk_{i}",
        "title": f"{uploaded_file.name} (Part {i//chunk_size + 1})",
        "content": chunk_str,
    })
  return chunks


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


# -------------------------------------------------------------
# Sidebar & File Upload
# -------------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚙️ **Control Panel**")
  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq API Key:", type="password")

  st.markdown("---")
  st.markdown("### 📁 **Upload Custom Document**")
  uploaded_pdf = st.file_uploader("Upload PDF File", type=["pdf"])

  if uploaded_pdf is not None:
    if (
        "current_pdf_name" not in st.session_state
        or st.session_state.current_pdf_name != uploaded_pdf.name
    ):
      with st.spinner("Extracting and indexing PDF..."):
        custom_chunks = extract_pdf_chunks(uploaded_pdf)
        st.session_state.active_docs = custom_chunks
        st.session_state.current_pdf_name = uploaded_pdf.name
      st.success(
          f"Indexed {len(st.session_state.active_docs)} sections from"
          f" '{uploaded_pdf.name}'!"
      )
  else:
    st.session_state.active_docs = DEFAULT_POLICIES
    st.session_state.current_pdf_name = "Default Policies"

  st.markdown("---")
  st.markdown("**Suggested Prompts:**")
  presets = [
      "What is the minimum attendance required?",
      "Can I take 4 consecutive days of leave?",
      "What are the capstone submission deliverables?",
      "Summarize the uploaded document.",
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
active_source_label = st.session_state.get(
    "current_pdf_name", "Default Policies"
)
st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-header-row">
            <h1 class="hero-title">NexusDoc AI</h1>
            <span class="status-badge">● Active: {active_source_label[:20]}</span>
        </div>
        <div class="hero-subtitle">Upload any PDF in the sidebar or ask questions about existing policies.</div>
    </div>
""",
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "Hello! You can ask questions about our institutional policies or"
          " upload any custom PDF document in the sidebar to query it"
          " instantly."
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

  # Retrieve relevant context from current active document set
  matched = score_and_retrieve(user_prompt, st.session_state.active_docs)

  llm = ChatGroq(
      model="openai/gpt-oss-20b",
      api_key=groq_key,
      temperature=0.1,
      streaming=True,
  )

  system_prompt = (
      "You are an intelligent Document Copilot and technical assistant.\n\n"
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
    
