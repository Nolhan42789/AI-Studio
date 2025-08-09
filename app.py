import os
import json
from datetime import datetime
import streamlit as st
from dotenv import load_dotenv
import openai

# load .env (optional)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
DEFAULT_MODEL = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

st.set_page_config(page_title="AI Studio", page_icon="🤖", layout="wide")

# Helpers
def init_openai(key):
    openai.api_key = key

def call_chat(messages, model=DEFAULT_MODEL, max_tokens=600):
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            max_tokens=max_tokens,
            temperature=0.7,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return f"Error calling OpenAI API: {e}"

def save_history(item, filename="history.json"):
    data = []
    if os.path.exists(filename):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            data = []
    data.append(item)
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# UI
st.title("🤖 AI Studio — چند ابزار AI در یک اپ پایتونی")
st.write("یک ابزار ساده و کاربردی: خلاصه‌ساز، تولید README، توضیح کد، تولید کامیت و ... — کلید OpenAI را وارد کن و امتحان کن.")

# sidebar: API key + options
with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("OpenAI API Key (یا ست کن در متغیر OPENAI_API_KEY)", type="password")
    model_input = st.text_input("Model (اختیاری)", value=DEFAULT_MODEL)
    max_tokens = st.slider("Max tokens (response)", 150, 2000, 600)
    if api_key_input:
        init_openai(api_key_input)
    elif OPENAI_API_KEY:
        init_openai(OPENAI_API_KEY)
    else:
        st.warning("برای کار کردن اپ، OpenAI API Key نیاز است — در بالا وارد کن یا متغیر محیطی تنظیم کن.")
    st.markdown("---")
    st.markdown("History & Export")
    if st.button("Show saved history"):
        if os.path.exists("history.json"):
            with open("history.json", "r", encoding="utf-8") as f:
                st.code(f.read()[:10000], language="json")
        else:
            st.info("هنوز هیستوری ذخیره نشده.")
    if os.path.exists("history.json"):
        with open("history.json", "rb") as f:
            st.download_button("Download history.json", f, file_name="ai_studio_history.json")

# Main tools
tool = st.radio("انتخاب ابزار", (
    "Summarize text",
    "Generate README",
    "Explain code",
    "Generate commit message",
    "Blog post / Tweet writer",
    "Image prompt generator"
))

if tool == "Summarize text":
    st.subheader("خلاصه‌ساز متن")
    text = st.text_area("متن خود را اینجا بچسبانید", height=300)
    length = st.selectbox("طول خلاصه", ["Short (1-3 lines)", "Medium (1 paragraph)", "Detailed (several paragraphs)"])
    if st.button("Generate summary"):
        if not (api_key_input or OPENAI_API_KEY):
            st.error("API key لازم است.")
        else:
            instr = f"Summarize the following text. Tone: neutral. Length: {length}.\n\nText:\n{text}"
            messages = [{"role":"system","content":"You are a helpful summarizer."},
                        {"role":"user","content":instr}]
            with st.spinner("Generating..."):
                out = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=max_tokens)
            st.success("Done")
            st.write(out)
            save_history({"tool":"summarize","input":text[:1000],"output":out,"ts":str(datetime.utcnow())})

elif tool == "Generate README":
    st.subheader("تولید README برای پروژه GitHub")
    proj_name = st.text_input("Project name", "My Awesome Project")
    proj_desc = st.text_area("Short project description", "A short one-line description of the project.")
    techs = st.text_input("Tech stack (comma separated)", "python, streamlit, openai")
    features = st.text_area("Key features (one per line)", " - Feature A\n - Feature B")
    usage = st.text_area("Quick start / usage", "1. git clone ...\n2. pip install -r requirements.txt\n3. streamlit run app.py")
    if st.button("Generate README"):
        prompt = f"""Generate a polished, friendly, and concise README.md for a GitHub repo.
Project name: {proj_name}
Description: {proj_desc}
Tech: {techs}
Features: {features}
Usage: {usage}
Include badges: license, python, pip install, streamlit.
Make README suitable for getting stars (include demo, screenshots, deploy instructions, license)."""
        messages = [{"role":"system","content":"You are a professional GitHub README writer."},
                    {"role":"user","content":prompt}]
        with st.spinner("Writing README..."):
            readme = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=max_tokens)
        st.subheader("Generated README.md")
        st.code(readme, language="markdown")
        st.download_button("Download README.md", readme, file_name="README.md")
        save_history({"tool":"readme","input":prompt,"output":readme,"ts":str(datetime.utcnow())})

elif tool == "Explain code":
    st.subheader("توضیح‌دهنده کد — Paste code and get an explanation / comments")
    code = st.text_area("Paste code here", height=300)
    language = st.text_input("Language (optional)", "python")
    if st.button("Explain code"):
        prompt = f"Explain the following {language} code clearly and concisely. Provide a short summary, main responsibilities, potential bugs, and suggested improvements. Also produce an inline-commented version.\n\nCode:\n{code}"
        messages = [{"role":"system","content":"You are an expert developer and code reviewer."},
                    {"role":"user","content":prompt}]
        with st.spinner("Analyzing code..."):
            out = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=max_tokens)
        st.code(out, language="text")
        save_history({"tool":"explain_code","input":code[:2000],"output":out,"ts":str(datetime.utcnow())})

elif tool == "Generate commit message":
    st.subheader("تولید پیام کامیت هوشمند")
    diff = st.text_area("توضیح تغییرات یا paste یک خلاصه از diff", height=200)
    style = st.selectbox("Style", ["Concise", "Detailed", "Conventional Commits"])
    if st.button("Generate commit message"):
        prompt = f"Write a {style} git commit message for these changes:\n\n{diff}"
        messages = [{"role":"system","content":"You are a git commit message assistant."},
                    {"role":"user","content":prompt}]
        with st.spinner("Generating..."):
            out = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=200)
        st.code(out)
        save_history({"tool":"commit","input":diff[:1000],"output":out,"ts":str(datetime.utcnow())})

elif tool == "Blog post / Tweet writer":
    st.subheader("تولید پست بلاگ یا توییت")
    tone = st.selectbox("Tone", ["casual","professional","funny","tutorial"])
    purpose = st.selectbox("Purpose", ["Short tweet", "Medium thread (3-6 tweets)", "Blog post (500-800 words)"])
    topic = st.text_input("Topic / headline", "How to build a deployable AI tool")
    if st.button("Write"):
        prompt = f"Write a {purpose} about '{topic}' in a {tone} tone. Make it engaging and practical. Include code snippets if helpful."
        messages = [{"role":"system","content":"You are a creative writer and developer."},
                    {"role":"user","content":prompt}]
        with st.spinner("Writing..."):
            out = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=max_tokens)
        st.code(out)
        save_history({"tool":"writer","input":topic,"output":out,"ts":str(datetime.utcnow())})

elif tool == "Image prompt generator":
    st.subheader("تولید prompt برای تولید تصویر (برای استفاده در DALL·E, StableDiffusion, Midjourney)")
    desc = st.text_area("Describe the scene / subject", "A cyberpunk city at night, neon lights")
    style = st.text_input("Style (optional)", "cinematic, high detail, 4k")
    if st.button("Generate prompt"):
        prompt = f"Generate 3 high-quality image prompts for generative image models. Scene: {desc}. Style: {style}. Provide short guidance for aspect ratio and negative prompts."
        messages = [{"role":"system","content":"You are an expert prompt engineer for image generation."},
                    {"role":"user","content":prompt}]
        with st.spinner("Generating prompts..."):
            out = call_chat(messages, model=model_input or DEFAULT_MODEL, max_tokens=400)
        st.code(out)
        save_history({"tool":"image_prompt","input":desc,"output":out,"ts":str(datetime.utcnow())})

st.markdown("---")
st.caption("Built with ❤️ — AI Studio minimal. Want the full repo with README, demo GIF and one-click deploy files? Ask me and I will generate the repo files now.")
