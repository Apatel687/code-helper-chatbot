import streamlit as st
import requests

# ✅ Replace this with your real OpenRouter API key
API_KEY = st.secrets["OPENROUTER_API_KEY"]

# 📍 OpenRouter API endpoint
API_URL = "https://openrouter.ai/api/v1/chat/completions"

# 🤖 Model to use (openai/gpt-oss-20b:free)
MODEL_NAME = "openai/gpt-oss-20b:free"

st.set_page_config(page_title="Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.markdown("Ask me to write, debug, or explain Python code.")

# Save messages across runs
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful Python assistant."}]

# Show previous chat messages
for msg in st.session_state.messages[1:]:
    st.chat_message(msg["role"]).write(msg["content"])

# User input
if prompt := st.chat_input("What code help do you need?"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "HTTP-Referer": "http://localhost:8501",  # Required by OpenRouter
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL_NAME,
            "messages": st.session_state.messages
        }

        response = requests.post(API_URL, headers=headers, json=data)

        if response.status_code == 200:
            reply = response.json()["choices"][0]["message"]["content"]
            st.chat_message("assistant").write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error("Something went wrong: " + response.text)


