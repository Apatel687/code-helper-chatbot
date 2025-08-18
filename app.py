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
# Load HF API key from secrets or environment
# -----------------------------
def _read_hf_key():
    try:
        key = st.secrets.get("HF_API_KEY")  # root-level
        if key:
            return key
        gen = st.secrets.get("general")  # optional [general] section
        if isinstance(gen, dict) and gen.get("HF_API_KEY"):
            return gen.get("HF_API_KEY")
    except Exception:
        pass
    return os.environ.get("HF_API_KEY")  # fallback

HF_API_KEY = _read_hf_key()

if not HF_API_KEY:
    st.error(
        "HF API key not found.\n\n"
        "Add a secret named **HF_API_KEY** in Streamlit Cloud → App → Settings → Secrets.\n"
        "TOML format (top-level):\nHF_API_KEY = 'hf_xxx...'"
    )
    st.stop()

# -----------------------------
# Sidebar controls
# -----------------------------
with st.sidebar:
    st.subheader("Model settings")
    model_id = st.text_input(
        "Hugging Face model ID",
        value="bigcode/starcoder",  # valid free code model
        help="Pick a free Hugging Face model. Smaller models work best on free API."
    )
    max_new_tokens = st.slider("Max new tokens", 16, 512, 256, 16)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    top_p = st.slider("top_p", 0.10, 1.00, 0.95, 0.05)
    st.markdown("---")
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
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful Python assistant."}
    ]

# Show history
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
    parts.append("Assistant:")  # model continues as assistant
    return "\n".join(parts)

# -----------------------------
# Hugging Face API call
# -----------------------------
def hf_generate(model_id: str, prompt: str, max_new_tokens: int, temperature: float, top_p: float) -> str:
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
            if isinstance(data, list) and data and "generated_text" in data[0]:
                return data[0]["generated_text"]
            if isinstance(data, dict) and "generated_text" in data:
                return data["generated_text"]
            if isinstance(data, dict) and "error" in data:
                msg = data.get("error", "")
                if "loading" in msg.lower() or "queued" in msg.lower():
                    time.sleep(5 + attempt * 4)
                    continue
                raise RuntimeError(msg)
            return str(data)
        if r.status_code == 503:
            try:
                info = r.json()
                wait = info.get("estimated_time", 5)
            except Exception:
                wait = 5
            time.sleep(wait)
            continue
        if r.status_code == 429:
            raise RuntimeError("Rate limited by HF free API (429). Try again in a minute or switch to a smaller model.")
        r.raise_for_status()

    raise TimeoutError("Model did not load in time. Try a smaller model.")

# -----------------------------
# Chat input and response
# -----------------------------
if prompt := st.chat_input("What code help do you need?"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            full_prompt = build_prompt(st.session_state.messages)
            reply = hf_generate(
                model_id=model_id,
                prompt=full_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
            )
        except Exception as e:
            st.error(f"API error: {e}")
            reply = ""

    if reply:
        st.chat_message("assistant").write(reply)
        st.session_state.messages.append({"role": "assistant", "content": reply})

# -----------------------------
# Footer
# -----------------------------
st.caption("Tip: Smaller models are faster and more reliable on free API.")








