import os
import chromadb
from langchain_groq import ChatGroq
from sentence_transformers import SentenceTransformer
import streamlit as st

st.set_page_config(
    page_title="Agentic Policy Assistant", page_icon="🤖", layout="centered"
)
st.title("🤖 Agentic Policy Assistant")

# Fetch key from environment or Streamlit secrets
groq_key = os.environ.get("GROQ_API_KEY")
if not groq_key:
  groq_key = st.sidebar.text_input("Enter Groq API Key:", type="password")


# Cache models so they initialize only once
@st.cache_resource
def load_rag_engine():
  embedder = SentenceTransformer("all-MiniLM-L6-v2")
  client = chromadb.Client()
  collection = client.get_or_create_collection(name="policies")

  # Add knowledge documents
  policies = [
      (
          "attendance",
          (
              "Attendance Policy: Minimum 80% attendance is required for exam"
              " eligibility and course certification."
          ),
      ),
      (
          "leave",
          (
              "Leave Policy: Students or employees can take up to 3 consecutive"
              " days with written mentor notification."
          ),
      ),
      (
          "submission",
          (
              "Submission Policy: Capstone submissions must include a public"
              " GitHub link, architecture diagram, and working video link."
          ),
      ),
  ]
  for pid, text in policies:
    emb = embedder.encode(text).tolist()
    collection.add(ids=[pid], documents=[text], embeddings=[emb])

  return embedder, collection


embedder, collection = load_rag_engine()

# Chat history
if "messages" not in st.session_state:
  st.session_state.messages = []

for msg in st.session_state.messages:
  with st.chat_message(msg["role"]):
    st.markdown(msg["content"])

user_query = st.chat_input("Ask a policy question...")
if user_query:
  if not groq_key:
    st.error("Please supply a Groq API key in secrets or the sidebar.")
    st.stop()

  st.session_state.messages.append({"role": "user", "content": user_query})
  with st.chat_message("user"):
    st.markdown(user_query)

  # 1. Local Retrieval
  query_vec = embedder.encode(user_query).tolist()
  retrieved = collection.query(query_embeddings=[query_vec], n_results=1)
  doc_context = (
      retrieved["documents"][0][0]
      if retrieved["documents"]
      else "No relevant policy found."
  )

  # 2. LLM Generation via Groq
  llm = ChatGroq(
      model="openai/gpt-oss-20b", api_key=groq_key, temperature=0.0
  )
  prompt = f"Context:\n{doc_context}\n\nUser Question: {user_query}\n\nAnswer clearly and concisely based strictly on the context:"

  with st.chat_message("assistant"):
    response = llm.invoke(prompt).content
    st.markdown(response)

  st.session_state.messages.append({"role": "assistant", "content": response})
