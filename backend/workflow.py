import os
import sqlite3
import operator
from typing import TypedDict, Annotated, Any
from dotenv import load_dotenv

from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.sqlite import SqliteSaver

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool
from langchain_google_genai import ChatGoogleGenerativeAI

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(BASE_DIR, ".env"))

# Check for API key and provide a fallback model instance
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash", 
    google_api_key=GOOGLE_API_KEY, 
    temperature=0
)

# ================= TOOLS ===================
from calendar_service import (
    read_calendar as real_read_calendar, 
    create_calendar_invite as real_create_calendar_invite
)

@tool
def read_calendar(date: str, state: Annotated[dict, operator.add]) -> str:
    """Read the calendar for a specific date (YYYY-MM-DD) to check availability. Safe tool."""
    user_id = state.get("user_id", "default_user")
    return real_read_calendar(date, user_id=user_id)

from gmail_service import send_email as real_send_email

@tool
def send_email(to: str, subject: str, body: str, state: Annotated[dict, operator.add]) -> str:
    """Send an email using the Gmail API. THIS IS A DANGEROUS TOOL."""
    user_id = state.get("user_id", "default_user")
    return real_send_email(to, subject, body, user_id=user_id)

@tool
def create_calendar_invite(title: str, date: str, state: Annotated[dict, operator.add]) -> str:
    """Create a calendar invite. THIS IS A DANGEROUS TOOL."""
    user_id = state.get("user_id", "default_user")
    return real_create_calendar_invite(title, date, user_id=user_id)

safe_tools = [read_calendar]
dangerous_tools = [send_email, create_calendar_invite]
all_tools = safe_tools + dangerous_tools

# ================= STATE ===================
class AgentState(TypedDict, total=False):
    From: Any
    Subject: Any
    message: Any
    Message_ID: Any
    Category: Any
    Triage: Any
    user_id: str
    Agent_Action: Any
    preferences: str
    messages: Annotated[list, operator.add]

# ================= NODES ===================
def load_memory_node(state: AgentState):
    """Load Memory: Retrieve all past user preferences from backend memory."""
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, "memory.db")
    prefs = "No major preferences yet."
    try:
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("SELECT key, value FROM preferences")
            rows = c.fetchall()
            if rows:
                prefs = "; ".join([f"{k}: {v}" for k, v in rows])
            conn.close()
    except Exception as e:
        print(f"Memory load error: {e}")
    return {"preferences": prefs}

def triage_node(state: AgentState):
    """Triage (Decide): Classifies email into categories and decides action."""
    sender = state.get("From", "Unknown")
    subject = (state.get("Subject") or "No Subject").lower()
    content = str(state.get("message") or "").lower()
    prompt = (
        f"Email from: {sender}\nSubject: {subject}\n"
        f"Content: {content[:1500]}\n"
        "Classify this email into a category (e.g., Finance, Work, Personal, Social, Travel) "
        "and also decide on a triage action: 'ignore', 'notify_human', or 'respond/act'.\n"
        "Output format: Category | Action"
    )
    
    category = "Personal"
    triage_action = "respond/act"

    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        output = response.content.strip()
        if "|" in output:
            category, triage_action = [x.strip() for x in output.split("|", 1)]
        else:
            category = output
            # Simple heuristic if parsing fails
            if any(x in output.lower() for x in ["ignore", "junk", "newsletter"]):
                 triage_action = "ignore"
            elif "notify" in output.lower():
                 triage_action = "notify_human"
            else:
                 triage_action = "respond/act"
    except Exception:
        # 🔹 BACKUP KEYWORD LOGIC (Fires if AI API key is invalid/missing)
        if any(word in subject or word in content for word in ["invoice", "payment", "receipt", "bank", "bill"]):
            category = "Finance"
        elif any(word in subject or word in content for word in ["meeting", "zoom", "sync", "standup", "sprint"]):
            category = "Work"
        elif any(word in subject or word in content for word in ["party", "invite", "birthday", "hello", "hi"]):
            category = "Personal"
        else:
            category = "General"
        triage_action = "respond/act"
        
    return {"Category": category.capitalize(), "Triage": triage_action.lower()}

def triage_router(state: AgentState):
    triage = state.get("Triage", "respond/act")
    if "ignore" in triage:
        return "ignore_node"
    elif "notify" in triage:
        return "notify_node"
    else:
        return "react_agent"

def ignore_node(state: AgentState):
    return {"Agent_Action": "Archived email as per triage (ignored)."}

def notify_node(state: AgentState):
    return {"Agent_Action": "Flagged email for human review."}

# Setup the ReAct loop
react_llm = llm.bind_tools(all_tools)

def react_agent_node(state: AgentState):
    """ReAct Loop: Reason and generate tool calls/final answers"""
    prefs = state.get("preferences", "")
    system_msg = SystemMessage(content=f"You are a helpful email assistant. Use your tools to solve the user's request based on this email. User preferences and feedback: {prefs}")
    
    messages = state.get("messages", [])
    if not messages:
        email_content = f"Please process this email from {state.get('From', '')} with subject {state.get('Subject', '')}"
        messages = [HumanMessage(content=email_content)]
        
    try:
        response = react_llm.invoke([system_msg] + messages)
        # Check if the LLM finished responding without tools
        if not response.tool_calls:
            return {"messages": [response], "Agent_Action": response.content}
            
        return {"messages": [response]}
    except Exception as e:
        # 🔹 SMART FALLBACK (When AI API Key is invalid or rate limited)
        category = state.get("Category", "General").lower()
        if "finance" in category:
            rec = "Recommended Action: Review financial alert or invoice details immediately."
        elif "work" in category:
            rec = "Recommended Action: Check associated tasks or prepare response for next sync."
        elif "personal" in category:
            rec = "Recommended Action: Review sender content and respond if urgent."
        elif "travel" in category:
            rec = "Recommended Action: Check booking confirmation or schedule changes."
        elif "social" in category:
            rec = "Recommended Action: Mark for weekend review or dismiss."
        else:
            rec = "Recommended Action: Review content and decide on next steps."
            
        fallback_msg = f"AWAITING HUMAN APPROVAL: {rec} [!] Verify GOOGLE_API_KEY in .env for full AI reasoning."
        return {"Agent_Action": fallback_msg}

def tool_router(state: AgentState):
    """Route to safe or dangerous tools to pause operations for human review."""
    messages = state.get("messages", [])
    if not messages:
        return END

    last_message = messages[-1]
    # Check if the last log was just an action
    if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
        return END

    # Look for dangerous tools
    dangerous_names = [t.name for t in dangerous_tools]
    has_dangerous = any(tc["name"] in dangerous_names for tc in last_message.tool_calls)
    
    if has_dangerous:
        return "hitl_checkpoint"
        
    return "safe_tools_node"

safe_node = ToolNode(safe_tools)
all_node = ToolNode(all_tools) # Used to complete the request after user approval

def execute_safe_tools(state: AgentState):
    """Execute Safe tools (like calendar reads) without prompting user."""
    return safe_node.invoke(state)

def hitl_checkpoint(state: AgentState):
    """HITL Checkpoint: A dummy node to pause before dangerous action."""
    return {"Agent_Action": "AWAITING HUMAN APPROVAL for dangerous action."}

def execute_dangerous_tools(state: AgentState):
    """Execute tools post-human approval."""
    return all_node.invoke(state)

# ================= GRAPH BUILDER ===================
builder = StateGraph(AgentState)

builder.add_node("load_memory", load_memory_node)
builder.add_node("triage", triage_node)
builder.add_node("ignore_node", ignore_node)
builder.add_node("notify_node", notify_node)
builder.add_node("react_agent", react_agent_node)
builder.add_node("safe_tools_node", execute_safe_tools)
builder.add_node("hitl_checkpoint", hitl_checkpoint)
builder.add_node("dangerous_tools_node", execute_dangerous_tools)

# Edges
builder.set_entry_point("load_memory")
builder.add_edge("load_memory", "triage")
builder.add_conditional_edges("triage", triage_router)

builder.add_edge("ignore_node", END)
builder.add_edge("notify_node", END)

builder.add_conditional_edges("react_agent", tool_router, {
    "hitl_checkpoint": "hitl_checkpoint",
    "safe_tools_node": "safe_tools_node",
    END: END
})

builder.add_edge("safe_tools_node", "react_agent")
# the hitl_checkpoint interrupts. After resume, dangerous tools node executes.
builder.add_edge("hitl_checkpoint", "dangerous_tools_node")
builder.add_edge("dangerous_tools_node", "react_agent")

# Persistent Settings & Deployment
db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "langgraph_state.db")
memory = SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))

# Compile with interrupt BEFORE the dynamic checkpoint executing dangerous tools.
graph = builder.compile(
    checkpointer=memory,
    interrupt_before=["hitl_checkpoint"]
)