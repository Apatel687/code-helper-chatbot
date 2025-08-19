import os
import time
import requests
import streamlit as st
from PIL import Image
from io import BytesIO

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 AI Chat + Image Generator", page_icon="🤖")
st.title("🧠 AI Chat + Image Generator")
st.caption("Text chat using OpenRouter free GPT model + Text-to-Image via Hugging Face free API")

# -----------------------------
# Load API keys
# -----------------------------
def _read_openrouter_key():
    key = st.secrets.get("OPENROUTER_API_KEY")
    if key:
        return key
    return os.environ.get("OPENROUTER_API_KEY")

def _read_hf_key():
    key = st.secrets.get("HF_API_KEY")
    if key:
        return key
    return os.environ.get("HF_API_KEY")

OPENROUTER_API_KEY = _read_openrouter_key()
HF_API_KEY = _read_hf_key()

if not OPENROUTER_API_KEY:
    st.error("Set OPENROUTER_API_KEY in Streamlit secrets or environment variable.")
    st.stop()
if not HF_API_KEY:
    st.error("Set HF_API_KEY in Streamlit secrets or environment variable.")
    st.stop()

# -----------------------------
# Sidebar
# -----------------------------
with st.sidebar:
    st.subheader("Model Settings")
    model_id_text = "openai/gpt-oss-20b:free"
    model_id_img = "stabilityai/stable-diffusion-2-1"
    st.markdown("**Chat Model:** " + model_id_text)
    st.markdown("**Image Model:** " + model_id_img)
    st.slider("Max tokens for text", 16, 1024, 256, 16, key="max_tokens")
    st.slider("Temperature", 0.0, 1.5, 0.7, 0.1, key="temperature")
    st.markdown("---")

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful AI assistant."}]

# Display chat messages
for msg in st.session_state.messages:
    if msg["role"] in ("user", "assistant"):
        st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Functions
# -----------------------------
def build_prompt(messages):
    prompt = ""
    for m in messages:
        if m["role"] == "system":
            prompt += f"System: {m['content']}\n"
        elif m["role"] == "user":
            prompt += f"User: {m['content']}\n"
        elif m["role"] == "assistant":
            prompt += f"Assistant: {m['content']}\n"
    prompt += "Assistant:"
    return prompt

def chat_generate(prompt, max_tokens=256, temperature=0.7):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": model_id_text,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    # OpenRouter returns 'choices'
    return data["choices"][0]["message"]["content"]

def generate_image(prompt):
    url = f"https://api-inference.huggingface.co/models/{model_id_img}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {"inputs": prompt}
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    # Hugging Face returns bytes in 'content'
    img_bytes = BytesIO(r.content)
    img = Image.open(img_bytes)
    return img

# -----------------------------
# User input
# -----------------------------
tab1, tab2 = st.tabs(["Chat", "Text-to-Image"])

with tab1:
    if prompt := st.chat_input("Ask me something..."):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            try:
                full_prompt = build_prompt(st.session_state.messages)
                reply = chat_generate(
                    full_prompt,
                    max_tokens=st.session_state.max_tokens,
                    temperature=st.session_state.temperature,
                )
            except Exception as e:
                reply = f"API error: {e}"

        st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

with tab2:
    img_prompt = st.text_area("Enter prompt for image generation:")
    if st.button("Generate Image"):
        if img_prompt.strip():
            with st.spinner("Generating image..."):
                try:
                    img = generate_image(img_prompt)
                    st.image(img, caption="Generated image", use_column_width=True)
                except Exception as e:
                    st.error(f"Image API error: {e}")
        else:
            st.warning("Please enter a prompt for image generation.")















