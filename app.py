import base64
import io
import os
import re
from groq import Groq
from gtts import gTTS
from langchain_groq import ChatGroq
from PIL import Image
from pypdf import PdfReader
import streamlit as st

st.set_page_config(
    page_title="NexusDoc AI • Integrated Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# Modern Mobile-First Styling
# -------------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
    .stApp { background-color: #0b0f19; color: #f3f4f6; }
    
    .hero-container {
        padding: 1.1rem 1.3rem;
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 14px;
        margin-bottom: 0.9rem;
    }
    
    .hero-header-row {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        flex-wrap: wrap;
    }

    .brand-group {
        display: flex;
        align-items: center;
        gap: 10px;
    }

    .brand-avatar {
        width: 38px;
        height: 38px;
        border-radius: 10px;
        background: linear-gradient(135deg, #38bdf8, #0284c7);
        display: flex;
        align-items: center;
        justify-content: center;
        color: #0b0f19;
        font-weight: 800;
        font-size: 1.1rem;
    }

    .hero-title {
        font-size: clamp(1.2rem, 4.5vw, 1.75rem) !important;
        font-weight: 800 !important;
        color: #38bdf8 !important;
        line-height: 1.2 !important;
        margin: 0 !important;
        white-space: nowrap;
    }
    
    .hero-subtitle {
        color: #9ca3af;
        font-size: 0.82rem;
        margin-top: 0.25rem;
    }
    
    .status-badge {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.3);
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.72rem;
        font-weight: 600;
        white-space: nowrap;
    }

    .chat-dock {
        background: #111827;
        border: 1px solid #1f2937;
        border-radius: 12px;
        padding: 10px 14px;
        margin-top: 10px;
        margin-bottom: 8px;
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
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        padding: 2px 8px;
        border-radius: 4px;
        margin-bottom: 6px;
        border: 1px solid rgba(56, 189, 248, 0.3);
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
    .stButton > button:hover { border-color: #38bdf8; color: #ffffff; }
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


def text_to_audio_bytes(text: str):
  clean_text = re.sub(r"[*#_`\[\]()]", "", text)
  tts = gTTS(text=clean_text[:400], lang="en", slow=False)
  audio_fp = io.BytesIO()
  tts.write_to_fp(audio_fp)
  audio_fp.seek(0)
  return audio_fp


# -------------------------------------------------------------
# Sidebar Configuration
# -------------------------------------------------------------
with st.sidebar:
  st.markdown("### ⚙️ **Control Panel**")
  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq API Key:", type="password")

  enable_tts = st.toggle("🔊 Auto Voice Response (TTS)", value=True)

  st.markdown("---")
  st.markdown("**Suggested Quick Prompts:**")
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
  if st.button("🗑️ Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.session_state.active_docs = DEFAULT_POLICIES
    st.session_state.current_media_name = "Institutional Policies"
    st.rerun()

# -------------------------------------------------------------
# Session Initialization
# -------------------------------------------------------------
if "active_docs" not in st.session_state:
  st.session_state.active_docs = DEFAULT_POLICIES
  st.session_state.current_media_name = "Institutional Policies"

active_label = st.session_state.get("current_media_name", "Institutional Policies")

# Hero Header
st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-header-row">
            <div class="brand-group">
                <div class="brand-avatar">⚡</div>
                <div>
                    <h1 class="hero-title">NexusDoc AI</h1>
                    <div class="hero-subtitle">Unified Copilot • <b>Active:</b> {active_label[:26]}</div>
                </div>
            </div>
            <span class="status-badge">● Online</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Chat History
if "messages" not in st.session_state:
  st.session_state.messages = [{
      "role": "assistant",
      "content": (
          "Hello! Attach files (PDF, image, video) or record audio right in the"
          " chat panel below to begin."
      ),
  }]

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])
    if "audio_bytes" in msg:
      st.audio(msg["audio_bytes"], format="audio/mp3")

# -------------------------------------------------------------
# Unified In-Chat Dock (File Attachments + Voice + Chat Input)
# -------------------------------------------------------------
st.markdown('<div class="chat-dock">', unsafe_allow_html=True)
dock_col1, dock_col2 = st.columns([1, 1])

# Column 1: Universal Attachment Picker
with dock_col1:
  uploaded_file = st.file_uploader(
      "📎 Attach PDF, Image, or Video",
      type=["pdf", "png", "jpg", "jpeg", "mp4", "mov"],
      key="in_chat_file_uploader",
      label_visibility="collapsed",
  )

# Column 2: Voice Audio Input
with dock_col2:
  voice_audio = st.audio_input(
      "🎤 Record Voice Question",
      key="in_chat_voice_recorder",
      label_visibility="collapsed",
  )

st.markdown("</div>", unsafe_allow_html=True)

# Process Attached Media
if uploaded_file is not None:
  file_ext = uploaded_file.name.split(".")[-1].lower()

  if file_ext == "pdf":
    if st.session_state.get("current_media_name") != uploaded_file.name:
      chunks = extract_pdf_chunks(uploaded_file)
      st.session_state.active_docs = chunks
      st.session_state.current_media_name = uploaded_file.name
      st.success(f"📄 PDF Attached: {uploaded_file.name}")

  elif file_ext in ["png", "jpg", "jpeg"]:
    image = Image.open(uploaded_file)
    st.image(image, caption=f"Attached: {uploaded_file.name}", width=240)
    width, height = image.size
    st.session_state.current_media_name = uploaded_file.name
    st.session_state.active_docs = [{
        "id": "image_doc",
        "title": f"Image: {uploaded_file.name}",
        "content": (
            f"Image asset: {uploaded_file.name} ({width}x{height}). Analyze"
            " styling, elements, and specifications based on this image."
        ),
    }]

  elif file_ext in ["mp4", "mov"]:
    st.video(uploaded_file)
    st.session_state.current_media_name = uploaded_file.name
    st.session_state.active_docs = [{
        "id": "video_doc",
        "title": f"Video: {uploaded_file.name}",
        "content": f"Video asset: {uploaded_file.name}.",
    }]

# Process Audio via Whisper
transcribed_voice_prompt = None
if voice_audio is not None and groq_key:
  if st.session_state.get("last_processed_audio") != voice_audio:
    with st.spinner("Transcribing speech..."):
      groq_client = Groq(api_key=groq_key)
      transcription = groq_client.audio.transcriptions.create(
          file=("audio.wav", voice_audio.read()),
          model="whisper-large-v3",
          response_format="text",
      )
      transcribed_voice_prompt = str(transcription).strip()
      st.session_state.last_processed_audio = voice_audio
      st.info(f'🎙️ Heard: "{transcribed_voice_prompt}"')

# Chat Input Bar
prompt_from_chip = st.session_state.pop("pending_prompt", None)
chat_typed_prompt = st.chat_input("Ask a question or speak above...")
user_prompt = transcribed_voice_prompt or prompt_from_chip or chat_typed_prompt

# -------------------------------------------------------------
# Inference Execution & TTS
# -------------------------------------------------------------
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
      temperature=0.2,
      streaming=True,
  )

  history_context = "\n".join([
      f"{m['role'].capitalize()}: {m['content']}"
      for m in st.session_state.messages[-4:-1]
  ])

  system_prompt = (
      "You are an intelligent Multimodal Copilot and technical assistant.\n\n"
      f"Context Source: {matched['title']}\n"
      f"Context Excerpt:\n{matched['content']}\n\n"
      f"Conversation History:\n{history_context}\n\n"
      f"User Question: {user_prompt}\n\n"
      "Instructions:\n"
      "1. If the question relates to the provided document, image, or policy"
      " context, base your answer strictly on that context.\n"
      "2. Keep responses concise and direct for fast spoken playback."
  )

  with st.chat_message("assistant"):
    st.markdown(
        f'<span class="source-tag">📄 Source: {matched["title"]}</span>',
        unsafe_allow_html=True,
    )

    def stream_generator():
      try:
        for chunk in llm.stream(system_prompt):
          if chunk.content:
            yield chunk.content
      except Exception as e:
        yield f"Notice: Streaming error ({str(e)})."

    response_text = st.write_stream(stream_generator())

    # Text-To-Speech Audio Playback
    audio_data = None
    if enable_tts and response_text:
      with st.spinner("Synthesizing audio..."):
        audio_data = text_to_audio_bytes(response_text)
        st.audio(audio_data, format="audio/mp3", autoplay=True)

  msg_payload = {"role": "assistant", "content": response_text}
  if audio_data:
    msg_payload["audio_bytes"] = audio_data
  st.session_state.messages.append(msg_payload)
               
