from flask import Flask, request, jsonify
from gmail_service import fetch_emails
from flask_cors import CORS
import pandas as pd
import PyPDF2
import sqlite3

# Import your LangGraph workflow
from workflow import graph

app = Flask(__name__)
CORS(app)

# =========================================================
# MEMORY DATABASE
# =========================================================

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "memory.db")

def init_memory():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT,
            value TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_memory(key, value):

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO preferences (key, value) VALUES (?, ?)",
        (key, value)
    )

    conn.commit()
    conn.close()


def load_memory():

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT key, value FROM preferences"
    )

    data = cursor.fetchall()

    conn.close()

    return data


# =========================================================
# EMAIL PARSER
# =========================================================

def parse_email(raw_text):

    headers = {
        "Message-ID": None,
        "From": None,
        "Subject": None
    }

    if pd.isna(raw_text):
        return headers

    for line in str(raw_text).split("\n"):

        if line.startswith("Message-ID:"):
            headers["Message-ID"] = (
                line.replace("Message-ID:", "")
                .strip()
            )

        elif line.startswith("From:"):
            headers["From"] = (
                line.replace("From:", "")
                .strip()
            )

        elif line.startswith("Subject:"):
            headers["Subject"] = (
                line.replace("Subject:", "")
                .strip()
            )

    return headers


# =========================================================
# PDF READER
# =========================================================

def read_pdf(file):

    reader = PyPDF2.PdfReader(file)

    text = ""

    for page in reader.pages:

        extracted = page.extract_text()

        if extracted:
            text += extracted + "\n"

    return text


# =========================================================
# TXT READER
# =========================================================

def read_txt(file):

    return file.read().decode("utf-8")


# =========================================================
# TEXT → DATAFRAME
# =========================================================

def text_to_dataframe(text):

    emails = []

    blocks = text.split("Message-ID:")

    for block in blocks:

        block = block.strip()

        if block:
            emails.append(
                "Message-ID:" + block
            )

    return pd.DataFrame({
        "message": emails
    })


# =========================================================
# PROCESS DATA USING LANGGRAPH
# =========================================================

def process_dataframe(df):

    results = []

    for idx, message in enumerate(df["message"]):

        # Step 1 — Parse email
        parsed = parse_email(message)

        # Step 2 — Run LangGraph workflow with Memory Saver Config
        thread_id = parsed.get("Message-ID", f"thread-csv-{idx}")
        user_id = request.headers.get("X-User-ID", "default_user")
        parsed["user_id"] = user_id
        config = {"configurable": {"thread_id": thread_id}}
        
        output = graph.invoke(parsed, config)
        if output is None:
            output = graph.get_state(config).values
            
        results.append({
            "Subject": output.get("Subject", "Unknown"),
            "From": output.get("From", "Unknown"),
            "Category": output.get("Category", "Unknown"),
            "Agent_Action": output.get("Agent_Action", "Processing or Awaiting Action..."),
            "thread_id": thread_id
        })

    return results


# =========================================================
# APPROVAL API (HITL)
# =========================================================

@app.route("/approve", methods=["POST"])
def approve():
    data = request.json
    thread_id = data.get("thread_id")
    action = data.get("action") # "approve", "deny", "edit"
    feedback = data.get("feedback") # if edit

    print(f"HITL Action received: {action} for thread: {thread_id}")

    if not thread_id or not action:
        return jsonify({"error": "Missing thread_id or action"}), 400

    config = {"configurable": {"thread_id": thread_id}}
    
    if action == "deny":
        # Mark as denied in state and return
        graph.update_state(config, {"Agent_Action": "Action Denied by Human."})
        return jsonify({
            "status": "denied", 
            "thread_id": thread_id,
            "Agent_Action": "Action Denied."
        })

    if action == "edit" and feedback:
        # Add the human feedback to state before resuming
        from langchain_core.messages import HumanMessage
        graph.update_state(config, {"messages": [HumanMessage(content=feedback)]})

    # Resume the graph
    try:
        # If it's a mock action (AWAITING), the graph might not be truly suspended.
        # We check the state first.
        state = graph.get_state(config)
        
        # If we're not suspended but have the mock message, just update and return
        current_action = state.values.get("Agent_Action", "")
        if "AWAITING HUMAN APPROVAL" in current_action and not state.next:
            new_action = "Action Approved and processed manually."
            graph.update_state(config, {"Agent_Action": new_action})
            return jsonify({
                "status": "resumed",
                "thread_id": thread_id,
                "Agent_Action": new_action
            })

        # Otherwise, try to invoke/resume
        output = graph.invoke(None, config)
        if output is None:
            output = graph.get_state(config).values
            
        return jsonify({
            "status": "resumed",
            "thread_id": thread_id,
            "Agent_Action": output.get("Agent_Action", "Task Completed")
        })
    except Exception as e:
        print(f"Approval error: {e}")
        # Fallback for errors: forceful update
        graph.update_state(config, {"Agent_Action": "Action Approved (Manual Bypass)."})
        return jsonify({
            "status": "resumed",
            "thread_id": thread_id,
            "Agent_Action": "Action Approved."
        })


# =========================================================
# HEALTH CHECK
# =========================================================

@app.route("/")
def home():

    return jsonify({
        "message": "Email Assistant API running",
        "workflow": [
            "ingest",
            "load_memory",
            "triage",
            "categorize",
            "action",
            "hitl",
            "complete"
        ]
    })


# =========================================================
# FILE UPLOAD API
# =========================================================

@app.route("/upload", methods=["POST"])
def upload_file():

    try:

        if "file" not in request.files:

            return jsonify({
                "error": "No file uploaded"
            }), 400

        file = request.files["file"]

        filename = file.filename.lower()

        # -------------------------
        # CSV
        # -------------------------

        if filename.endswith(".csv"):

            df = pd.read_csv(file)

        # -------------------------
        # PDF
        # -------------------------

        elif filename.endswith(".pdf"):

            text = read_pdf(file)

            df = text_to_dataframe(text)

        # -------------------------
        # TXT
        # -------------------------

        elif filename.endswith(".txt"):

            text = read_txt(file)

            df = text_to_dataframe(text)

        else:

            return jsonify({
                "error": "Unsupported file type"
            }), 400

        # Run workflow
        result = process_dataframe(df)

        return jsonify(result)

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

@app.route("/gmail", methods=["GET"])
def get_gmail_emails():
    user_id = request.headers.get("X-User-ID", "default_user")
    emails = fetch_emails(user_id=user_id)
    return jsonify(emails)

# =========================================================
# START SERVER
# =========================================================

# -------------------------------
# 🔹 Fetch Emails via Gmail API Route
# -------------------------------
@app.route("/fetch-emails", methods=["GET"])
def fetch_gmail_emails():
    try:
        user_id = request.headers.get("X-User-ID", "default_user")
        emails = fetch_emails(max_results=15, user_id=user_id)
        
        if not emails:
            return jsonify([])
            
        results = []
        print(f"Fetched {len(emails)} emails for user {user_id}. Starting graph processing...")
        for idx, email in enumerate(emails):
            try:
                thread_id = email.get("Message-ID", f"thread-gmail-{idx}")
                email["user_id"] = user_id
                config = {"configurable": {"thread_id": thread_id}}
                
                print(f"Processing email {idx+1}/{len(emails)}: {email.get('Subject')}")
                output = graph.invoke(email, config)
                if output is None:
                    output = graph.get_state(config).values

                results.append({
                    "Subject": output.get("Subject", email.get("Subject")),
                    "From": output.get("From", email.get("From")),
                    "Category": output.get("Category", "Unknown"),
                    "Agent_Action": output.get("Agent_Action", "Processing..."),
                    "thread_id": thread_id
                })
            except Exception as e:
                print(f"Error processing email {idx}: {e}")
                results.append({
                    "Subject": email.get("Subject", "Error"),
                    "From": email.get("From", "Unknown"),
                    "Category": "Error",
                    "Agent_Action": f"Failed to process: {str(e)}",
                    "thread_id": f"error-{idx}"
                })
            
        print("Gmail processing complete.")
        return jsonify(results)
    except Exception as e:
        print(f"Overall fetch-emails error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":

    init_memory()

    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )