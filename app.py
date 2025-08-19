import os
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Using OpenRouter free API model: openai/gpt-oss-20b")

# -----------------------------
# Load OpenRouter API key from secrets or environment variable
# -----------------------------
def get_api_key():
    try:
        key = st.secrets.get("OPENROUTER_API_KEY")
        if key:
            return key
    except Exception:
        pass
    return os.environ.get("OPENROUTER_API_KEY")

API_KEY = get_api_key()

if not API_KEY:
    st.error(
        "OpenRouter API key not found.\n\n"
        "Add a secret named **OPENROUTER_API_KEY** in Streamlit Cloud → App → Settings → Secrets:\n\n"
        'OPENROUTER_API_KEY = "sk-yourkeyhere"'
    )
    st.stop()
else:
    st.success("API key loaded: ✅")

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful coding assistant."}
    ]

# Display chat history
for msg in st.session_state.messages:
    if msg["role"] in ("user", "assistant"):
        st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# OpenRouter API call
# -----------------------------
def openrouter_generate(prompt: str):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    payload = {
        "model": "openai/gpt-oss-20b:free",  # updated model
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 400,  # can adjust as needed
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if "choices" in data and data["choices"]:
            return data["choices"][0]["message"]["content"]
        return "No response from API."
    except requests.exceptions.HTTPError as e:
        return f"API error: {e}"
    except Exception as e:
        return f"Error: {e}"

# -----------------------------
# Chat input
# -----------------------------
if user_input := st.chat_input("Ask me anything about Python or code!"):
    st.chat_message("user").write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})

    with st.spinner("Thinking..."):
        reply = openrouter_generate(user_input)

    st.chat_message("assistant").write(reply)
    st.session_state.messages.append({"role": "assistant", "content": reply})

# -----------------------------
# Footer
# -----------------------------
st.caption("Tip: Using OpenRouter free API model (gpt-oss-20b:free). Responses may be limited in length.")










