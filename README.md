# 🤖 Telegram AI Assistant Bot

![Python](https://shields.io)
![aiogram](https://shields.io)
![OpenRouter](https://shields.io)

An asynchronous Telegram bot that searches real-time information on the web, generates structured responses, refines text for natural human-likeness, evaluates AI probability locally, and builds ready-to-use **Word**, **Excel**, and **PowerPoint** files directly in RAM (`BytesIO`) without saving temporary files to disk.
---

## 👤 Author & License

Created at **16** as my first full-scale Python project exploring Telegram bots and LLM workflows. Feel free to explore, fork, and use this code under the [MIT License](LICENSE)

---

## ✨ Key Features

* **Multi-Step Content Pipeline:**
  1. **Security Firewall (`security.py`):** Validates input length, strips system role tags, runs an AI prompt-injection check, and isolates user topics inside `<user_topic>` XML tags.
  2. **Web Search (`ddgs`):** Fetches up-to-date facts and local sources tailored to the user's region via DuckDuckGo.
  3. **Writer & Editor Agents (OpenRouter):** Generates comprehensive drafts in the user's language and rewrites them to remove robotic phrasing and clichés.
  4. **Local AI Detector (`detec.py`):** Evaluates text human-likeness mathematically on Python (sentence length variance / *burstiness*, lexical diversity, and punctuation density) without spending external API tokens.
* **Zero-Disk Document Generation (`file_maker.py`):** Creates **`.docx`**, **`.xlsx`**, and **`.pptx`** (with auto-fetched slide images) strictly in memory via `io.BytesIO`.
* **Interactive Telegram UI:** Inline format selection, slide count picker (5–15 slides), anti-spam concurrency lock, and one-click **Approve / Regenerate** controls for both text messages and generated files.

---

## 🗂 Project Structure

```text
├── bot.py             # Main Telegram bot handlers, FSM states, and pipeline orchestration
├── file_maker.py      # In-memory generator for .docx, .xlsx, and .pptx documents
├── detec.py           # Local mathematical AI-probability analyzer
├── security.py        # Multi-layered prompt injection protection & XML sandboxing
├── requirements.txt   # Python dependencies
├── .env.example       # Environment variables template
└── .gitignore         # Excludes secrets (.env) and cache files from version control
```

---

## 🚀 Installation & Local Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/gastratatuy322-cmyk/telegram-ai-bot
   cd telegram-ai-bot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux / macOS:
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**
   * Copy `.env.example` to `.env`:
     ```bash
     cp .env.example .env
     ```
   * Open `.env` and add your credentials:
     * `BOT_TOKEN` — Telegram bot token from [@BotFather](https://t.me).
     * `OPENROUTER_API_KEY` — API key from [OpenRouter](https://openrouter.ai).

5. **Run the bot:**
   ```bash
   python bot.py
   ```
