import os
import time
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Free tier via OpenRouter & Hugging Face APIs. Smaller models recommended for speed.")

# -----------------------------
# Load API keys from Streamlit secrets or environment
# -----------------------------
OPENROUTER_API_KEY = st.secrets.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
HF_API_KEY = st.secrets.get("HF_API_KEY") or os.environ.get("HF_API_KEY")

if not OPENROUTER_API_KEY:
    st.error(
        "OpenRouter API key not found.\n\n"
        "Add a secret named **OPENROUTER_API_KEY** in Streamlit Cloud → *App → Settings → Secrets*.\n"
        'Format: OPENROUTER_API_KEY = "sk-or-xxxx..."'
    )
    st.stop()

# -----------------------------
# Sidebar for model selection
# -----------------------------
with st.sidebar:
    st.subheader("Model settings")
    use_openrouter = st.checkbox("Use OpenRouter GPT-OSS 20B (free)", value=True)
    hf_model_id = st.text_input(
        "Hugging Face model ID",
        value="meta-llama/Llama-2-7b",
        help="Enter any Hugging Face model ID you want to use."
    )
    max_new_tokens = st.slider("Max new tokens", 16, 1024, 256, 16)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.05)
    top_p = st.slider("Top-p", 0.1, 1.0, 0.95, 0.05)
    st.markdown("---")
    if st.button("Test API connection"):
        if use_openrouter:
            url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
            payload = {"model": "openai/gpt-oss-20b:free", "messages": [{"role": "user", "content": "ping"}]}
        else:
            url = f"https://api-inference.huggingface.co/models/{hf_model_id}"
            headers = {"Authorization": f"Bearer {HF_API_KEY}"}
            payload = {"inputs": "ping"}
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=30)
            st.write("Status:", r.status_code)
            st.json(r.json())
        except Exception as e:
            st.error(f"Connection error: {e}")

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful Python assistant."}]

for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        st.chat_message(m["role"]).write(m["content"])

# -----------------------------
# Prompt builder
# -----------------------------
def build_prompt(messages):
    parts = []
    system = None
    for m in messages:
        if m["role"] == "system":
            system = m["content"]
    if system:
        parts.append(f"System: {system}\n")
    for m in messages:
        if m["role"] == "user":
            parts.append(f"User: {m['content']}\n")
        elif m["role"] == "assistant":
            parts.append(f"Assistant: {m['content']}\n")
    parts.append("Assistant:")
    return "\n".join(parts)

# -----------------------------
# OpenRouter API call
# -----------------------------
def openrouter_generate(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": "openai/gpt-oss-20b:free",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_new_tokens
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    try:
        return data["choices"][0]["message"]["content"]
    except Exception:
        return str(data)

# -----------------------------
# Hugging Face API call
# -----------------------------
def hf_generate(model_id, prompt):
    url = f"https://api-inference.huggingface.co/models/{model_id}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "do_sample": True,
            "return_full_text": False
        }
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, list) and data and "generated_text" in data[0]:
        return data[0]["generated_text"]
    if isinstance(data, dict) and "generated_text" in data:
        return data["generated_text"]
    if isinstance(data, dict) and "error" in data:
        raise RuntimeError(data["error"])
    return str(data)

# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("Ask me to write, debug, or explain Python code:"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            full_prompt = build_prompt(st.session_state.messages)
            if use_openrouter:
                reply = openrouter_generate(full_prompt)
            else:
                reply = hf_generate(hf_model_id, full_prompt)
        except Exception as e:
            st.error(f"API error: {e}")
            reply = ""

    if reply:
        st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

st.caption("Tip: Smaller models are faster and more reliable on free API.")














