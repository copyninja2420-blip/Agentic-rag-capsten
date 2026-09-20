import os
import chromadb
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
import streamlit as st

st.set_page_config(
    page_title="AI Policy Copilot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern styling
st.markdown(
    """
    <style>
    .stChatMessage { border-radius: 12px; margin-bottom: 8px; }
    .stChatInput { border-radius: 10px; }
    header {visibility: hidden;}
    footer {visibility: hidden;}
    </style>
""",
    unsafe_allow_html=True,
)

# Sidebar controls
with st.sidebar:
  st.title("⚡ Policy Assistant")
  st.caption("Grounded Agentic RAG • Free Tier")

  groq_key = os.environ.get("GROQ_API_KEY")
  if not groq_key:
    groq_key = st.text_input("Enter Groq API Key:", type="password")

  st.markdown("---")
  st.markdown("### 💡 Quick Queries")
  sample_queries = [
      "What is the policy on attendance?",
      "Can I take 4 consecutive days of leave?",
      "What are the capstone submission guidelines?",
  ]
  for q in sample_queries:
    if st.button(q, use_container_width=True):
      st.session_state.preset_query = q

  st.markdown("---")
  if st.button("🗑️ Clear Chat History", use_container_width=True):
    st.session_state.messages = []
    st.rerun()


# Initialize models and Chroma collection
@st.cache_resource(show_spinner=False)
def load_rag_engine():
  embedder = SentenceTransformer("all-MiniLM-L6-v2")
  client = chromadb.Client()
  collection = client.get_or_create_collection(name="policies")

  policies = [
      (
          "attendance",
          (
              "Attendance Policy: Minimum 80% attendance is mandatory for exam"
              " eligibility and course certification. Falling below 80%"
              " disqualifies the candidate."
          ),
      ),
      (
          "leave",
          (
              "Leave Policy: Students and employees can take up to 3"
              " consecutive days of leave with written mentor/manager"
              " notification. Leaves exceeding 3 days require special approval."
          ),
      ),
      (
          "submission",
          (
              "Submission Policy: Capstone submissions must include a public"
              " GitHub repository link, system architecture diagram in README,"
              " and a working live video/demo link."
          ),
      ),
  ]
  for pid, text in policies:
    emb = embedder.encode(text).tolist()
    collection.add(ids=[pid], documents=[text], embeddings=[emb])

  return embedder, collection


with st.spinner("Initializing neural search engine..."):
  embedder, collection = load_rag_engine()

# Initialize session messages
if "messages" not in st.session_state:
  st.session_state.messages = []

# Display conversation history
for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

# Handle chat input or sidebar preset clicks
preset = st.session_state.pop("preset_query", None)
user_query = st.chat_input("Ask any policy question...") or preset

if user_query:
  if not groq_key:
    st.error("Please supply a valid Groq API key to proceed.")
    st.stop()

  # Append and render user message
  st.session_state.messages.append({"role": "user", "content": user_query})
  with st.chat_message("user"):
    st.markdown(user_query)

  # 1. High-speed vector lookup
  query_vec = embedder.encode(user_query).tolist()
  results = collection.query(query_embeddings=[query_vec], n_results=1)
  doc_context = (
      results["documents"][0][0]
      if results["documents"]
      else "No relevant policy documents found."
  )

  # 2. Fast Streaming Generation with Groq
  llm = ChatGroq(
      model="llama-3.1-8b-instant",
      api_key=groq_key,
      temperature=0.0,
      streaming=True,
  )

  prompt = (
      f"Context:\n{doc_context}\n\n"
      f"User Question: {user_query}\n\n"
      "Instructions: Answer concisely, authoritatively, and directly based"
      " only on the context provided. Use clean bullet points where"
      " appropriate."
  )

  with st.chat_message("assistant"):

    def stream_generator():
      for chunk in llm.stream(prompt):
        if chunk.content:
          yield chunk.content

    # Native typewriter effect directly renders tokens as they are produced
    full_response = st.write_stream(stream_generator())

  st.session_state.messages.append(
      {"role": "assistant", "content": full_response}
      )
    
