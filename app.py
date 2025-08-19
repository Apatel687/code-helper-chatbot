import os
import time
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Chat & Image generation using free APIs. Smaller models recommended.")

# -----------------------------
# Load API keys from secrets
# -----------------------------
def _read_keys():
    hf_key = st.secrets.get("HF_API_KEY") or os.environ.get("HF_API_KEY")
    or_key = st.secrets.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
    return hf_key, or_key

HF_API_KEY, OR_API_KEY = _read_keys()

if not OR_API_KEY:
    st.error("Set OPENROUTER_API_KEY in Streamlit Secrets or environment variable.")
    st.stop()

if not HF_API_KEY:
    st.warning("HF_API_KEY not found. Image generation will not work.")

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.subheader("Model settings")
    chat_model_id = st.text_input(
        "Chat model ID",
        value="openai/gpt-oss-20b:free",
        help="Free GPT-OSS 20B via OpenRouter"
    )
    image_model_id = st.text_input(
        "Image model ID",
        value="runwayml/stable-diffusion-v1-5",
        help="Free HF text-to-image model"
    )
    max_tokens = st.slider("Max tokens (chat)", 16, 512, 256, 16)
    temperature = st.slider("Temperature (chat)", 0.0, 1.5, 0.7, 0.1)
    st.markdown("---")
    st.caption("Tip: Smaller models = faster & reliable on free APIs.")

# -----------------------------
# Chat session state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful assistant."}]

# Show history
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        st.chat_message(m["role"]).write(m["content"])

# -----------------------------
# Build prompt for chat
# -----------------------------
def build_prompt(messages):
    parts = []
    system = next((m["content"] for m in messages if m["role"]=="system"), None)
    if system:
        parts.append(f"System: {system}\n")
    for m in messages:
        if m["role"]=="user":
            parts.append(f"User: {m['content']}\n")
        elif m["role"]=="assistant":
            parts.append(f"Assistant: {m['content']}\n")
    parts.append("Assistant:")
    return "\n".join(parts)

# -----------------------------
# OpenRouter GPT API call
# -----------------------------
def generate_chat(prompt):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OR_API_KEY}"}
    payload = {
        "model": chat_model_id,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        return data.get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"API error: {e}"

# -----------------------------
# Hugging Face Image API call
# -----------------------------
def generate_image(prompt):
    if not HF_API_KEY:
        return None
    url = f"https://api-inference.huggingface.co/models/{image_model_id}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    payload = {
        "inputs": prompt,
        "parameters": {"num_inference_steps": 30, "guidance_scale": 7.5}
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        # Some HF image endpoints return base64 encoded image
        if isinstance(data, dict) and "images" in data:
            return data["images"][0]
        return data
    except Exception as e:
        st.error(f"Image API error: {e}")
        return None

# -----------------------------
# User input
# -----------------------------
mode = st.radio("Mode:", ["Chat", "Generate Image"])

if mode == "Chat":
    if prompt := st.chat_input("Ask me anything..."):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            reply = generate_chat(prompt)
        st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

elif mode == "Generate Image":
    img_prompt = st.text_input("Enter image prompt:")
    if st.button("Generate"):
        with st.spinner("Generating image..."):
            image = generate_image(img_prompt)
        if image:
            st.image(image, caption=img_prompt)

















