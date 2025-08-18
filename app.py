import os
import time
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Free tier via Hugging Face Inference API. Smaller models recommended.")

# -----------------------------
# Load HF API key from Streamlit Secrets or env
# -----------------------------
HF_API_KEY = st.secrets.get("HF_API_KEY") or os.environ.get("HF_API_KEY")
if not HF_API_KEY:
    st.error(
        "HF API key not found.\n\n"
        "Add a secret named **HF_API_KEY** in Streamlit Cloud → App → Settings → Secrets:\n\n"
        'HF_API_KEY = "hf_xxx..."'
    )
    st.stop()

# -----------------------------
# Sidebar for model settings
# -----------------------------
with st.sidebar:
    st.subheader("Model Settings")
    model_id = st.text_input(
        "Hugging Face model ID",
        value="bigcode/starcoderbase-1b",
        help="Pick any free Hugging Face model (smaller models are faster on free API)."
    )
    max_new_tokens = st.slider("Max new tokens", 16, 512, 256, 16)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    top_p = st.slider("Top-p", 0.1, 1.0, 0.95, 0.05)

    if st.button("Test HF connection"):
        url = f"https://api-inference.huggingface.co/models/{model_id}"
        try:
            r = requests.post(
                url,
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                json={"inputs": "ping"},
                timeout=30,
            )
            st.write("Status:", r.status_code)
            st.json(r.json())
        except Exception as e:
            st.error(f"Connection error: {e}")

# -----------------------------
# Chat state
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": "You are a helpful Python assistant."}]

# Show history
for msg in st.session_state.messages:
    if msg["role"] in ("user", "assistant"):
        st.chat_message(msg["role"]).write(msg["content"])

# -----------------------------
# Prompt builder
# -----------------------------
def build_prompt(messages):
    prompt = ""
    for m in messages:
        role = "User" if m["role"] == "user" else "Assistant" if m["role"] == "assistant" else None
        if role:
            prompt += f"{role}: {m['content']}\n"
    prompt += "Assistant:"
    return prompt

# -----------------------------
# HF Inference API call
# -----------------------------
def hf_generate(model_id, prompt, max_new_tokens, temperature, top_p):
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

    for attempt in range(6):
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        if r.status_code == 200:
            data = r.json()
            if isinstance(data, list) and "generated_text" in data[0]:
                return data[0]["generated_text"]
            if isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            if isinstance(data, dict) and "error" in data:
                msg = data["error"]
                if "loading" in msg.lower() or "queued" in msg.lower():
                    time.sleep(5 + attempt*3)
                    continue
                raise RuntimeError(msg)
            return str(data)
        if r.status_code == 503:
            time.sleep(5)
            continue
        if r.status_code == 429:
            raise RuntimeError("Rate limited by HF free API. Try again or choose a smaller model.")
        r.raise_for_status()

    raise TimeoutError("Model did not load in time.")

# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("What code help do you need?"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            reply = hf_generate(model_id, build_prompt(st.session_state.messages), max_new_tokens, temperature, top_p)
        except Exception as e:
            st.error(f"API error: {e}")
            reply = ""

    if reply:
        st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

st.caption("Tip: Smaller models are faster and more reliable on the free API.")







