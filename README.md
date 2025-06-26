# 📞 CallMate AI – Your Real-Time GenAI Voice Assistant for Customer Support

![CallMate Banner](https://callmate.life/assets/banner.png) <!-- Replace with your actual banner or remove -->

**CallMate AI** is a cutting-edge real-time voice assistant powered by Generative AI and multi-agent architecture. Designed to support customer service teams, it provides live speech-to-AI interaction, agent suggestions, feedback tracking, and compliance checks — all from within an intuitive, Streamlit-powered interface.

🌐 Live Demo: [callmate.streamlit.app](https://callmate.streamlit.app)  
🔗 Website: [callmate.life](https://callmate.life)  
📊 Dashboard: Built-in analytics, sentiment tracking, escalation flags, and agent feedback  
🧠 Built with: `FastAPI`, `Streamlit`, `Streamlit-webrtc`, `AWS`, `SQLite`

---

## 🚀 Features

- 🎙️ **Live Call Interface** – Real-time voice transcription using WebRTC
- 🧠 **AI Suggestions** – Powered by multi-agent models (sentiment, knowledge, compliance)
- ✅ **Consent Capture** – Checkbox-based user consent logging
- 📊 **Live Dashboard** – Track feedback, sentiment trends, escalation risk
- 🔐 **PII Redaction** – Mask sensitive data before analysis
- 💬 **Post-call Summaries** – Agent-level feedback reports with call context
- 📥 **Feedback Logging** – Stores and visualizes helpful/unhelpful responses

---

## 🧱 Tech Stack

| Layer        | Tech                                    |
|--------------|-----------------------------------------|
| 🖥️ Frontend  | `Streamlit`, `streamlit-webrtc`, `Plotly` |
| 🧠 Backend   | `FastAPI`, `Pydantic`, `OpenAI`, `SQLite` |
| 📊 Analytics | `Pandas`, `Plotly`, `Altair`             |
| ☁️ Hosting   | `Render.com`, `GitHub Pages`, `GoDaddy` |
| 🔒 PII Redact| Custom logic via regex and token filters |
| 🧩 Voice     | `SpeechRecognition`, `PyDub`, `FFmpeg`  |

---

## 🛠️ Project Structure

```
CallMate-AI/
│
├── backend/
│   ├── main.py               # FastAPI app with all endpoints
│   ├── agents.py             # AI multi-agent logic (sentiment, compliance, etc.)
│   ├── context_store.py      # In-memory storage of utterances
│   ├── feedback_db.py        # SQLite storage for feedback
│   ├── feedback_store.py     # JSON-based feedback history
│   ├── pii_redactor.py       # Redacts sensitive data
│
├── frontend/
│   └── app.py                # Streamlit UI with Assistant & Dashboard tabs
│
├── requirements.txt
└── README.md
```

---

## 🔧 Setup Instructions

### ✅ Requirements

- Python 3.10+
- `ffmpeg` installed and added to PATH (for voice support)
- OpenAI API key in `.env`

### 🔌 Install Dependencies

```bash
pip install -r requirements.txt
```
### 📫 Contact
**Founder:** Rajat Shinde  
**Email:** rajatshinde100@gmail.com  
  
