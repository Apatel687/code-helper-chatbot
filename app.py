import streamlit as st
import requests

# Hugging Face Inference API endpoint
API_URL = "https://api-inference.huggingface.co/models/bigcode/starcoderbase-1b"
headers = {"Authorization": f"Bearer {st.secrets['HF_API_KEY']}"}

# Chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Streamlit UI
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="🤖")
st.title("🧠 Code Helper Chatbot")
st.write("Free tier via Hugging Face Inference API. For reliability use small models.")

# Chat input
user_input = st.chat_input("Ask me about coding...")

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    if response.status_code == 200:
        return response.json()[0]["generated_text"]
    else:
        return f"API error: {response.status_code} {response.reason} - {response.text}"

if user_input:
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.spinner("Thinking..."):
        output = query({"inputs": user_input})
    st.session_state["messages"].append({"role": "assistant", "content": output})

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])






