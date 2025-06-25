
# 📞 CallMate AI – Real-time GenAI Call Assistant

<p align="center">
  <img src="https://img.shields.io/badge/Streamlit-1.46-orange?logo=streamlit" />
  <img src="https://img.shields.io/badge/FastAPI-0.110-green?logo=fastapi" />
  <img src="https://img.shields.io/badge/GenAI-powered-blueviolet?logo=openai" />
</p>

> A voice-enabled, explainable, and compliant customer support assistant powered by multi-agent LLM architecture — built for speed, trust, and clarity.

---

## 🚀 Overview

CallMate AI supports customer agents during high-pressure conversations by providing real-time GenAI suggestions that are:

- ✅ Sentiment-aware  
- ✅ Policy-compliant  
- ✅ Confidence-transparent  
- ✅ Voice and text driven  

---

## 🎯 Key Features

| ✅ Feature                | 💡 Description                                                           |
|--------------------------|---------------------------------------------------------------------------|
| 🎙️ Voice & Text Input    | Upload `.wav` audio or type input manually in Streamlit UI               |
| 🤖 Multi-Agent Inference | Sentiment, Compliance, and Knowledge agents working in parallel           |
| 📊 Confidence Display    | Transparent scoring for all responses                                     |
| ⚠️ PII Redaction         | Detects and masks sensitive info (email, card numbers, etc.)              |
| 📑 Post-call Summary     | Automatically generated call recap with key insights                     |
| 🗳️ Feedback Logging      | User feedback stored in local SQLite database                             |
| ☁️ Cloud-Ready           | Deployable on AWS EC2, Bedrock-compatible architecture                    |

---

## 🧠 Architecture

``` 
graph TD
    U[👤 User (Voice/Text)] --> R(🔒 Redactor)
    R --> SA(Sentiment Agent)
    R --> KA(Knowledge Agent)
    R --> CA(Compliance Agent)
    SA --> ESC(🔺 Escalation)
    CA --> ESC
    KA --> UI[💬 Streamlit UI]
    ESC --> UI
```

---

## 🖥️ Live Demos & Docs

| Type            | Link                                                                                           |
|-----------------|------------------------------------------------------------------------------------------------|
| 🖥️ Live EC2 Demo | [http://ec2-XX-XX-XX.compute.amazonaws.com:8501](http://ec2-XX-XX-XX.compute.amazonaws.com:8501) |
| 🧪 Swagger Docs   | [http://localhost:8000/docs](http://localhost:8000/docs)                                       |
| 🎥 Demo Video    | [https://youtu.be/YOUR_VIDEO_ID](https://youtu.be/YOUR_VIDEO_ID)                               |

---

## 🧰 Tech Stack

| Layer    | Tools Used                       |
|----------|----------------------------------|
| UI       | Streamlit, HTML, `streamlit-webrtc` (optional) |
| Backend  | FastAPI, asyncio, Pydantic       |
| Audio    | SpeechRecognition, Pydub, FFmpeg |
| Storage  | SQLite for feedback              |
| Infra    | AWS EC2, localhost, Bedrock-ready |

---

## 📊 Performance Metrics

| Metric                       | Value        |
|-----------------------------|--------------|
| Avg. LLM Suggestion Latency | ~320 ms      |
| PII Redaction Accuracy      | 100%         |
| Sentiment Detection Accuracy| ~92% (sample)|
| Feedback Received           | 👍 5  👎 1     |

---

## ⚙️ Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/RajatShinde/callmate-ai.git
cd callmate-ai
```

### 2. Set up virtual environment
```bash
python -m venv .venv
source .venv/bin/activate       # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Set FFmpeg path (required for audio)
Download FFmpeg from: [https://www.gyan.dev/ffmpeg/builds/](https://www.gyan.dev/ffmpeg/builds/)

Set this in your code before using `AudioSegment`:
```python
from pydub import AudioSegment
AudioSegment.converter = "C:/ffmpeg/bin/ffmpeg.exe"  # Update path accordingly
```

---

## 🌐 Deployment (AWS EC2)

1. Launch EC2 instance (Amazon Linux / Ubuntu)
2. Open inbound ports: **8000** (FastAPI), **8501** (Streamlit)
3. SSH into server & clone this repo
4. Run backend:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
5. Run frontend:
```bash
streamlit run frontend/app.py --server.port 8501
```
6. Access via public DNS in browser

---

## 📁 Project Structure

```
callmate-ai/
│
├── frontend/              # Streamlit app (app.py)
├── backend/               # FastAPI backend
│   ├── agents.py          # AI agents: Sentiment, Knowledge, Compliance
│   ├── feedback_db.py     # Feedback database (SQLite)
│   └── pii_redactor.py    # PII redaction logic
├── requirements.txt       # Python dependencies
└── README.md              # You're here!
```

---

## 🔮 Future Roadmap

- 🔄 Integrate Amazon Bedrock (Titan or Claude)
- 📊 Add real-time charts for confidence drift
- 🎙️ Use Amazon Transcribe for improved voice accuracy
- 💾 Scale logs to DynamoDB
- 🔐 Add role-based authentication for agents

---

## 🏆 Why CallMate AI?

| 💥 Factor            | ✅ Strength                                    |
|----------------------|------------------------------------------------|
| Real-time UX         | Fast LLM response, voice or text input         |
| Trust & Transparency | Clear confidence %, latency, PII masking       |
| Contact Center Ready | Built for CSAT, AHT, escalation tracking       |
| Modular Design       | Easy to plug in new models or services         |
| Developer Friendly   | Pythonic, FastAPI/Streamlit, clean code        |

---

## 📜 License

**MIT License** — Free for personal, academic, and commercial use.

---

## 📬 Contact

- 📧 Email: [rajatshinde100@gmail.com](mailto:rajatshinde100@gmail.com)  
- 🔗 [LinkedIn](https://www.linkedin.com/in/YOUR_LINKEDIN)  
- 🔗 [GitHub](https://github.com/RajatShinde)

---

> ⚠️ DO NOT commit `.env` or sensitive data.
> This repo includes a `.env.example` to help set up locally.

---

## 🔐 Environment Setup

1. Duplicate `.env.example` → rename to `.env`
2. Fill in your API keys before running the app.

> ⚠️ Keep your `.env` private. Never upload to GitHub.

---
