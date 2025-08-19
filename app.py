import os
import time
import requests
import streamlit as st
from io import BytesIO
from PIL import Image

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Free tier: OpenRouter for chat/code, Hugging Face for image generation")

# -----------------------------
# Load API keys from Streamlit secrets or env
# -----------------------------
def _read_key(secret_name, env_name):
    try:
        key = st.secrets.get(secret_name)
        if key:
            return key
    except Exception:
        pass
    return os.environ.get(env_name)

OPENROUTER_API_KEY = _read_key("OPENROUTER_API_KEY", "OPENROUTER_API_KEY")
HF_API_KEY = _read_key("HF_API_KEY", "HF_API_KEY")

if not OPENROUTER_API_KEY:
    st.error("Set OPENROUTER_API_KEY in Streamlit secrets or environment variable.")
    st.stop()
if not HF_API_KEY:
    st.error("Set HF_API_KEY in Streamlit secrets or environment variable.")
    st.stop()

# -----------------------------
# Sidebar controls
# -----------------------------
st.sidebar.title("Settings")
task = st.sidebar.radio("Select task", ["Chat/Code", "Generate Image"])
st.sidebar.markdown("---")

if task == "Chat/Code":
    model_id = st.sidebar.text_input(
        "OpenRouter model",
        value="openai/gpt-oss-20b:free",
        help="OpenRouter free model for chat/code"
    )
    max_tokens = st.sidebar.slider("Max tokens", 16, 1024, 256, 16)
    temperature = st.sidebar.slider("Temperature", 0.0, 1.5, 0.7, 0.1)

elif task == "Generate Image":
    image_model = st.sidebar.text_input(
        "Hugging Face image model",
        value="runwayml/stable-diffusion-v1-5",
        help="Free Hugging Face text-to-image model"
    )
    image_size = st.sidebar.selectbox("Image size", ["256x256", "512x512", "768x768"])
    num_images = st.sidebar.slider("Number of images", 1, 3, 1)

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful AI assistant."}]

# Show chat history
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        st.chat_message(m["role"]).write(m["content"])

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

def openrouter_generate(prompt, model_id, max_tokens, temperature):
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    payload = {
        "model": model_id,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_tokens,
        "temperature": temperature
    }
    r = requests.post(url, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"]

def hf_image_generate(prompt, model, size, n_images):
    url = f"https://api-inference.huggingface.co/models/{model}"
    headers = {"Authorization": f"Bearer {HF_API_KEY}"}
    width, height = map(int, size.split("x"))
    payload = {
        "inputs": prompt,
        "options": {"wait_for_model": True},
        "parameters": {"width": width, "height": height, "num_images": n_images}
    }
    r = requests.post(url, headers=headers, json=payload, timeout=120)
    r.raise_for_status()
    return r.content

# -----------------------------
# Main interaction
# -----------------------------
if task == "Chat/Code":
    if prompt := st.chat_input("Ask me anything about code or general AI:"):
        st.chat_message("user").write(prompt)
        st.session_state.messages.append({"role": "user", "content": prompt})

        with st.spinner("Thinking..."):
            try:
                full_prompt = build_prompt(st.session_state.messages)
                reply = openrouter_generate(full_prompt, model_id, max_tokens, temperature)
            except Exception as e:
                st.error(f"API error: {e}")
                reply = ""

        if reply:
            st.chat_message("assistant").write(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})

elif task == "Generate Image":
    if img_prompt := st.text_input("Enter prompt for image generation:"):
        if st.button("Generate Image"):
            with st.spinner("Generating image..."):
                try:
                    result = hf_image_generate(img_prompt, image_model, image_size, num_images)
                    img = Image.open(BytesIO(result))
                    st.image(img, caption="Generated Image", use_column_width=True)
                except Exception as e:
                    st.error(f"Image API error: {e}")

st.caption("Tip: Free models may be slower or rate-limited. Smaller models are more reliable.")


















