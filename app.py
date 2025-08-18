import streamlit as st
import requests

# =========================
# API Key Setup
# =========================
# Fallback to a local variable for testing
API_KEY = st.secrets.get("OPENROUTER_API_KEY", "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")

if not API_KEY:
    st.error("API key not found! Set OPENROUTER_API_KEY in Streamlit secrets or here for local testing.")
    st.stop()

# =========================
# OpenRouter API
# =========================
API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_NAME = "openai/gpt-oss-20b:free"

# =========================
# Streamlit page setup
# =========================
st.set_page_config(page_title="Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.markdown("Ask me to write, debug, or explain Python code.")

# =========================
# Chat messages
# =========================
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful Python assistant."}]

for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

# =========================
# User input
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




