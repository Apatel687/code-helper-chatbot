import os
import time
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Free tier: OpenRouter GPT-OSS for chat + Hugging Face Stable Diffusion for images")

# -----------------------------
# Load API keys
# -----------------------------
def _read_key(name):
    try:
        key = st.secrets.get(name)
        if key:
            return key
        gen = st.secrets.get("general")
        if isinstance(gen, dict) and gen.get(name):
            return gen.get(name)
    except Exception:
        pass
    return os.environ.get(name)

OPENROUTER_KEY = _read_key("OPENROUTER_API_KEY")
HF_KEY = _read_key("HF_API_KEY")

if not OPENROUTER_KEY or not HF_KEY:
    st.error("Both OPENROUTER_API_KEY and HF_API_KEY are required.")
    st.stop()

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.subheader("Model settings")
    chat_model_id = st.text_input(
        "Chat model",
        value="openai/gpt-oss-20b:free",
        help="OpenRouter GPT-OSS 20B free tier"
    )
    image_model_id = st.text_input(
        "Image model",
        value="stabilityai/stable-diffusion-2",
        help="Hugging Face free Stable Diffusion model"
    )
    max_tokens = st.slider("Max tokens", 16, 512, 256, 16)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    top_p = st.slider("Top-p", 0.1, 1.0, 0.95, 0.05)

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful Python assistant."}
    ]

# Show previous messages
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        st.chat_message(m["role"]).write(m["content"])

# -----------------------------
# Chat input
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

def chat_generate(prompt: str):
    url = f"https://openrouter.ai/api/v1/chat/completions"
    payload = {
        "model": chat_model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p
    }
    headers = {"Authorization": f"Bearer {OPENROUTER_KEY}"}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

# -----------------------------
# Text-to-Image
# -----------------------------
def generate_image(prompt: str):
    url = f"https://api-inference.huggingface.co/models/{image_model_id}"
    headers = {"Authorization": f"Bearer {HF_KEY}"}
    payload = {"inputs": prompt}
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    return r.content

# -----------------------------
# User input type
# -----------------------------
option = st.radio("Choose input type:", ["Chat", "Generate Image"])

if option == "Chat":
    if prompt := st.chat_input("Ask me anything about code or AI:"):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            try:
                reply = chat_generate(prompt)
            except Exception as e:
                st.error(f"Chat API error: {e}")
                reply = ""
        if reply:
            st.chat_message("assistant").write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

elif option == "Generate Image":
    prompt = st.text_input("Enter image description:")
    if st.button("Generate Image") and prompt:
        with st.spinner("Generating image..."):
            try:
                img_bytes = generate_image(prompt)
                st.image(img_bytes)
            except Exception as e:
                st.error(f"Image API error: {e}")

st.caption("Tip: Use free APIs. Chat uses OpenRouter GPT-OSS 20B; images use HF Stable Diffusion.")
















