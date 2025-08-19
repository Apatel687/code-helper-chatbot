import os
import time
import requests
import streamlit as st

# -----------------------------
# Page UI
# -----------------------------
st.set_page_config(page_title="🧠 Code Helper Chatbot", page_icon="💻")
st.title("🧠 Code Helper Chatbot")
st.caption("Using OpenRouter free API model: openai/gpt-oss-20b. Smaller models recommended.")

# -----------------------------
# Load API key from secrets or environment
# -----------------------------
def _read_api_key():
    try:
        key = st.secrets.get("HF_API_KEY")  # root-level
        if key:
            return key
        gen = st.secrets.get("general")     # [general] section
        if isinstance(gen, dict) and gen.get("HF_API_KEY"):
            return gen.get("HF_API_KEY")
    except Exception:
        pass
    return os.environ.get("HF_API_KEY")

HF_API_KEY = _read_api_key()
if not HF_API_KEY:
    st.error(
        "HF API key not found.\n\n"
        "Add a secret named **HF_API_KEY** in Streamlit Cloud → App → Settings → Secrets.\n"
        'TOML format: HF_API_KEY = "hf_xxx..."'
    )
    st.stop()

# -----------------------------
# Sidebar settings
# -----------------------------
with st.sidebar:
    st.subheader("Model settings")
    model_id = st.text_input(
        "Model ID",
        value="openai/gpt-oss-20b:free",
        help="Use smaller models for free tier."
    )
    max_new_tokens = st.slider("Max new tokens", 64, 512, 256, 16)
    temperature = st.slider("Temperature", 0.0, 1.5, 0.7, 0.1)
    top_p = st.slider("Top P", 0.1, 1.0, 0.95, 0.05)
    st.markdown("---")
    if st.button("Test API connection"):
        try:
            r = requests.post(
                f"https://api-inference.huggingface.co/models/{model_id}",
                headers={"Authorization": f"Bearer {HF_API_KEY}"},
                json={"inputs": "ping"},
                timeout=30
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
        {"role": "system", "content": (
            "You are a friendly AI assistant that explains Python code clearly, "
            "debugs errors, suggests fixes, and gives examples when possible. "
            "Always provide concise, human-readable responses, like ChatGPT would."
        )}
    ]

# Show conversation history
for m in st.session_state.messages:
    if m["role"] in ("user", "assistant"):
        st.chat_message(m["role"]).write(m["content"])

# -----------------------------
# Build prompt for model
# -----------------------------
def build_prompt(messages):
    conversation = ""
    for m in messages:
        role, content = m["role"], m["content"]
        if role == "system":
            conversation += f"System: {content}\n"
        elif role == "user":
            conversation += f"User: {content}\n"
        elif role == "assistant":
            conversation += f"Assistant: {content}\n"
    conversation += "Assistant:"  # model continues as assistant
    return conversation

# -----------------------------
# Generate response from model
# -----------------------------
def generate_response(model_id, prompt, max_new_tokens, temperature, top_p):
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

    for attempt in range(6):  # retry logic
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
        elif r.status_code in (503, 429):
            wait = 5 + attempt * 3
            time.sleep(wait)
            continue
        else:
            r.raise_for_status()
    raise TimeoutError("Model did not load in time. Try a smaller model.")

# -----------------------------
# Chat input
# -----------------------------
if prompt := st.chat_input("Ask me to write, debug, or explain Python code"):
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.spinner("Thinking..."):
        try:
            full_prompt = build_prompt(st.session_state.messages)
            reply = generate_response(
                model_id=model_id,
                prompt=full_prompt,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p
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
st.caption("Tip: Smaller models are faster and more reliable on the free API.")











