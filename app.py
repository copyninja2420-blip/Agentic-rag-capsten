import os
import re
import base64
import streamlit as st
from pypdf import PdfReader
from PIL import Image
from langchain_groq import ChatGroq

st.set_page_config(
    page_title="NexusDoc AI • Multimodal Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# -------------------------------------------------------------
# Mobile-First Dark Styling
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
        "content": "Attendance Policy: A strict minimum of 80% attendance is mandatory for exam eligibility, lab access, and final course certification. Candidates falling below 80% require academic condonation.",
    },
    {
        "id": "leave",
        "title": "Leave & Absence Policy",
        "content": "Leave Policy: Team members can take up to 3 consecutive days of leave with written notice. Leaves exceeding 3 days require medical or formal verification submitted in advance.",
    },
    {
        "id": "capstone",
        "title": "Capstone Submission Criteria",
        "content": "Submission Guidelines: Capstone deliverables must include: 1) Public GitHub repository. 2) README with architecture diagram. 3) Live demo URL. Late submissions face a 10% daily grade deduction.",
    },
    {
        "id": "reimbursement",
        "title": "Travel & Expense Guidelines",
        "content": "Expense Policy: Travel or tool purchases exceeding $50 / ₹4,000 require prior manager approval. Digital receipts must be submitted within 7 business days.",
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

# -------------------------------------------------------------
# Sidebar Configuration
# -------------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ **Settings & Prompts**")
    groq_key = os.environ.get("GROQ_API_KEY")
    if not groq_key:
        groq_key = st.text_input("Enter Groq API Key:", type="password")

    st.markdown("---")
    st.markdown("**Suggested Quick Prompts:**")
    presets = [
        "What is the minimum attendance required?",
        "Can I take 4 consecutive days of leave?",
        "Describe what you see in the uploaded media.",
        "Summarize the key takeaways from the document.",
    ]
    for p in presets:
        if st.button(p, use_container_width=True):
            st.session_state.pending_prompt = p

    st.markdown("---")
    if st.button("🗑️ Clear Chat History", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

# -------------------------------------------------------------
# Main Header & Universal Media Uploader
# -------------------------------------------------------------
if "active_docs" not in st.session_state:
    st.session_state.active_docs = DEFAULT_POLICIES
    st.session_state.current_media_name = "Institutional Policies"

active_label = st.session_state.get("current_media_name", "Institutional Policies")

st.markdown(
    f"""
    <div class="hero-container">
        <div class="hero-header-row">
            <div class="brand-group">
                <div class="brand-avatar">N</div>
                <div>
                    <h1 class="hero-title">NexusDoc AI</h1>
                    <div class="hero-subtitle">Multimodal Intelligence • <b>Active:</b> {active_label[:26]}</div>
                </div>
            </div>
            <span class="status-badge">● Online</span>
        </div>
    </div>
""",
    unsafe_allow_html=True,
)

# Expandable Media Uploader (Supports PDF, Images, and Videos)
with st.expander("📁 **Upload Document, Photo, or Video (Tap to Open)**", expanded=False):
    uploaded_file = st.file_uploader(
        "Choose a PDF, Image, or Video file",
        type=["pdf", "png", "jpg", "jpeg", "mp4", "mov"],
        key="main_media_uploader",
    )
    if uploaded_file is not None:
        file_ext = uploaded_file.name.split(".")[-1].lower()

        # Handle PDF
        if file_ext == "pdf":
            if st.session_state.get("current_media_name") != uploaded_file.name:
                chunks = extract_pdf_chunks(uploaded_file)
                st.session_state.active_docs = chunks
                st.session_state.current_media_name = uploaded_file.name
                st.session_state.uploaded_image_b64 = None
                st.success(f"Indexed PDF '{uploaded_file.name}' successfully!")
                st.rerun()

        # Handle Images (JPG, PNG)
        elif file_ext in ["png", "jpg", "jpeg"]:
            image = Image.open(uploaded_file)
            # New line:
st.image(
    image,
    caption=f"Uploaded Image: {uploaded_file.name}",
    use_container_width=True,
)

            
            # Read bytes for multimodal processing
            uploaded_file.seek(0)
            img_bytes = uploaded_file.read()
            b64_img = base64.b64encode(img_bytes).decode("utf-8")
            st.session_state.uploaded_image_b64 = f"data:image/{file_ext};base64,{b64_img}"
            st.session_state.current_media_name = uploaded_file.name
            st.session_state.active_docs = [{
                "id": "image_doc",
                "title": f"Image: {uploaded_file.name}",
                "content": f"The user uploaded an image named '{uploaded_file.name}'. Inspect the attached image to respond.",
            }]
            st.success(f"Photo '{uploaded_file.name}' loaded! Ask any visual question below.")

        # Handle Videos (MP4, MOV)
        elif file_ext in ["mp4", "mov"]:
            st.video(uploaded_file)
            st.session_state.current_media_name = uploaded_file.name
            st.session_state.uploaded_image_b64 = None
            st.session_state.active_docs = [{
                "id": "video_doc",
                "title": f"Video: {uploaded_file.name}",
                "content": f"The user uploaded a video named '{uploaded_file.name}'. You can answer questions based on the video context and its title.",
            }]
            st.success(f"Video '{uploaded_file.name}' ready! Ask questions or add notes below.")

# Initialize chat session
if "messages" not in st.session_state:
    st.session_state.messages = [{
        "role": "assistant",
        "content": "Hello! Ask questions about our policies, or open the **'Upload Document, Photo, or Video'** panel above to analyze any file.",
    }]

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

prompt_from_chip = st.session_state.pop("pending_prompt", None)
user_prompt = st.chat_input("Ask any question or query your media...") or prompt_from_chip

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
        "You are an intelligent Multimodal Copilot and technical assistant.\n\n"
        f"Context Source: {matched['title']}\n"
        f"Context Excerpt:\n{matched['content']}\n\n"
        f"User Question: {user_prompt}\n\n"
        "Instructions:\n"
        "1. If the question relates to the provided document, image, or video context, answer accurately and cite the context.\n"
        "2. If the user asks general coding, design, or technical questions, answer helpfully and concisely using your technical knowledge."
    )

    with st.chat_message("assistant"):
        st.markdown(f'<span class="source-tag">📄 Source: {matched["title"]}</span>', unsafe_allow_html=True)

        def stream_generator():
            for chunk in llm.stream(system_prompt):
                if chunk.content:
                    yield chunk.content

        response_text = st.write_stream(stream_generator())

    st.session_state.messages.append({"role": "assistant", "content": response_text})
