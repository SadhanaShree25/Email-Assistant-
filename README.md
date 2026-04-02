# 📧 NexusInbox: Intelligent AI Email Assistant

> **Internship Project**: Developed during my internship at **Infosys Springboard**.

NexusInbox is a state-of-the-art AI agent built to revolutionize how you manage your communications. It doesn't just read your email; it **reasons**, **categorizes**, and **acts** as your personal office assistant.

---

### 🌟 Key Features

*   **Multi-User Support**: Seamlessly switch between Personal, Work, and Guest accounts with isolated credentials.
*   **Gmail Integration**: Directly fetch your real-time messages and send professional replies automatically.
*   **Calendar Intelligence**: Read your availability or schedule meetings directly through Google Calendar v3.
*   **State-of-the-Art AI**: Powered by **LangGraph** and **Google Gemini**, the assistant follows a cyclical "ReAct" loop (Reasoning + Acting) to solve complex tasks.
*   **Human-in-the-Loop (HITL)**: You remain in control. The agent pauses for your "Approve", "Deny", or "Edit" commands before performing high-stakes actions like sending emails.
*   **In-Depth Evaluation**: A built-in LLM-as-a-judge framework to monitor accuracy and professionalism.

---

### 🛠️ Technology Stack

| Pillar | Technology |
| :--- | :--- |
| **Agent Framework** | LangGraph (Stateful cyclical graphs) |
| **Intelligence** | Google Gemini API (LLM) |
| **Frontend** | React + Vite + TailwindCSS + Lucide Icons |
| **Backend** | Python Flask + SQLite (for memory) |
| **Auth** | Google OAuth2 (Unified Gmail & Calendar) |

---

### 🚀 Getting Started

#### 1. Setup Backend
```bash
cd backend
pip install -r requirements.txt
```
*   Create a `.env` file from the placeholder.
*   Add your `GOOGLE_API_KEY` and `credentials.json` from Google Cloud Console.

#### 2. Setup Frontend
```bash
cd frontend
npm install
npm run dev
```

#### 3. Run Evaluation
```bash
python evaluate.py
```

---

### ⚠️ IMPORTANT: Security & Privacy (What NOT to Commit)

When pushing this project to GitHub, **NEVER** include sensitive private data. Ensure the following files are ignored in your `.gitignore`:

| File/Folder | Reason |
| :--- | :--- |
| **`.env`** | Contains your private AI & API keys. |
| **`credentials.json`** | Contains your Google Cloud App secrets. |
| **`token.json` / `tokens/`** | Contains authorized access tokens to YOUR real email/calendar. |
| **`*.db`** | Local database files containing saved email content and memory. |
| **`node_modules/`** | Large folders containing external dependencies. |
| **`__pycache__/`** | Compiled Python cache files. |

---

### 📂 Application Workflow
Ingest ➔ Load Memory ➔ Triage AI ➔ ReAct Reasoning Loop ➔ HITL Checkpoint ➔ Execute ➔ Complete.
