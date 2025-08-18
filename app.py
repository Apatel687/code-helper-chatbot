# Add this line at the top temporarily
print("Redeploy test")

import streamlit as st
import requests

# =========================
# API Key Setup
# =========================
API_KEY = st.secrets.get("OPENROUTER_API_KEY")

if not API_KEY:
    st.error(
        "API key not found! Set OPENROUTER_API_KEY in Streamlit secrets "
        "or as an environment variable."
    )
    st.stop()

# =========================
# OpenRouter API & Model
# =========================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "qwen/qwen3-coder:free"  # Qwen3-Coder free model for coding tasks

# =========================
# Streamlit Page Config
# =========================
st.set_page_config(page_title="Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.markdown("Ask me to write, debug, or explain Python code.")

# =========================
# Chat Message State
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful Python assistant."}
    ]

# Show previous chat messages
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

# =========================
# User Input
# =========================
if prompt := st.chat_input("What code help do you need?"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL_NAME,
            "messages": st.session_state.messages
        }

        try:
            response = requests.post(API_URL, headers=headers, json=data, timeout=15)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
        else:
            reply = response.json()["choices"][0]["message"]["content"]
            st.chat_message("assistant").write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})





