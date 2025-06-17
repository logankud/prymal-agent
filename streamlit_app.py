import streamlit as st
import sys
import uuid

# Comprehensive fix for PyTorch-Streamlit compatibility
def fix_torch_streamlit_compatibility():
    """Fix PyTorch compatibility issues with Streamlit"""
    if "torch" in sys.modules:
        import torch
        
        # Fix the __path__ attribute issue
        if hasattr(torch._classes, '__path__'):
            torch._classes.__path__ = []
        
        # Disable Streamlit's file watcher for torch modules
        if hasattr(torch._classes, '_path'):
            torch._classes._path = []
            
        # Safer monkey patch approach - only if __getattr__ exists
        if hasattr(torch._classes, '__getattr__'):
            original_getattr = torch._classes.__getattr__
            def safe_getattr(name):
                if name in ('__path__', '_path'):
                    return []
                return original_getattr(name)
            torch._classes.__getattr__ = safe_getattr
        else:
            # If no __getattr__, create a custom one
            def safe_getattr(name):
                if name in ('__path__', '_path'):
                    return []
                # Try to get the attribute normally, or raise AttributeError
                if hasattr(torch._classes, name):
                    return getattr(torch._classes, name)
                raise AttributeError(f"module 'torch._classes' has no attribute '{name}'")
            torch._classes.__getattr__ = safe_getattr

# Apply the fix before importing any other modules
fix_torch_streamlit_compatibility()

from agents import manager_agent, analyst_agent, set_agents_session_id
from memory_utils import store_message, get_recent_history

st.set_page_config(
    page_title="AI Agent Chat",
    page_icon="🤖",
    layout="wide",
)

def get_or_create_session():
    query_params = st.query_params
    if "session" in query_params:
        sid = query_params["session"]
        try:
            if get_recent_history(session_id=sid, limit=1):
                return sid
        except:
            pass
    new_sid = f"streamlit_{uuid.uuid4().hex[:8]}"
    st.query_params["session"] = new_sid
    return new_sid

def load_history(session_id):
    raw = get_recent_history(session_id=session_id, limit=100)
    msgs = []
    for m in raw:
        role = "assistant" if m["role"] == "agent" else "user"
        msgs.append({"role": role, "content": m["content"]})
    return msgs

# ──────────────── Session & History ──────────────────
if "session_id" not in st.session_state:
    st.session_state.session_id = get_or_create_session()
    st.session_state.messages = load_history(st.session_state.session_id)

# ──────────────── Render existing chat ────────────────
st.title("🤖 AI Agent Chat Interface")
for msg in st.session_state.messages:
    if msg["role"] == "assistant":
        st.markdown(f"""<div style="display:flex;align-items:flex-start;margin:20px 0">
            <div style="width:32px;height:32px;background:linear-gradient(135deg,#6366f1,#8b5cf6);
                        border-radius:50%;display:flex;align-items:center;justify-content:center;
                        margin-right:12px;">
              <span style="color:white;font-weight:bold">AI</span>
            </div>
            <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:12px;
                        padding:16px;flex:1;color:#334155;">
              {msg["content"]}
            </div>
        </div>""", unsafe_allow_html=True)
    else:
        st.markdown(f"""<div style="display:flex;align-items:flex-start;margin:20px 0;justify-content:flex-end">
            <div style="background:#3b82f6;color:white;border-radius:12px;padding:16px;
                        max-width:70%;margin-right:12px;">
              {msg["content"]}
            </div>
            <div style="width:32px;height:32px;background:#3b82f6;border-radius:50%;
                        display:flex;align-items:center;justify-content:center;">
              <span style="color:white;font-weight:bold">U</span>
            </div>
        </div>""", unsafe_allow_html=True)

# ──────────────── Initialize processing state ─────────────────────
if "pending_user_message" not in st.session_state:
    st.session_state.pending_user_message = None
if "processing_message" not in st.session_state:
    st.session_state.processing_message = False

# ──────────────── New user input ─────────────────────
user_prompt = st.chat_input("What would you like to know about your Shopify data?")

if user_prompt and not st.session_state.processing_message:
    # Debug logging
    st.write(f"🔍 Debug: User submitted: '{user_prompt}'")
    st.write(f"🔍 Debug: Session ID: {st.session_state.session_id}")
    
    # 1) echo & store user
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    try:
        store_message(
            session_id=st.session_state.session_id,
            agent_name="user",
            role="user",
            message=user_prompt,
        )
        st.write("✅ Debug: Message stored successfully")
    except Exception as e:
        st.write(f"❌ Debug: Error storing message: {e}")
    
    # Set the user message to process
    st.session_state.pending_user_message = user_prompt
    st.session_state.processing_message = True
    st.write(f"🔍 Debug: Set pending message: '{st.session_state.pending_user_message}'")
    st.write(f"🔍 Debug: Processing flag: {st.session_state.processing_message}")
    st.experimental_rerun()  # to render the newly appended message immediately

# ──────────────── Process agent response if there's a pending message ────────────────
st.write(f"🔍 Debug: Checking for pending message...")
st.write(f"🔍 Debug: pending_user_message value: '{st.session_state.pending_user_message}'")
st.write(f"🔍 Debug: processing_message value: {st.session_state.processing_message}")

if st.session_state.pending_user_message and st.session_state.processing_message:
    
    st.write("🚀 Debug: Starting agent processing...")
    # Containers for logs and answer
    logs_ct = st.container()
    answer_ct = st.container()
    st.session_state.current_run_logs = []

    # Callback to render each step
    def log_cb(step, agent):
        num = step.step_number
        info = {
            "input": None,
            "output": getattr(step, "action_output", ""),
            "tools": getattr(step, "tool_calls", []),
            "obs": getattr(step, "observations", ""),
            "err": getattr(step, "error", ""),
        }
        try:
            mem = agent.write_memory_to_messages()
            info["input"] = "\n".join(f"{m['role']}: {m['content']}" for m in mem)
        except:
            info["input"] = "[unavailable]"

        st.session_state.current_run_logs.append(info)

        # render a one-liner
        dot = "#22c55e" if info["tools"] else "#3b82f6"
        lbl = getattr(info["tools"][0], "name", "Tool") if info["tools"] else "Thinking…"
        with logs_ct:
            st.markdown(f"""<div style="display:flex;align-items:center;margin:4px 0">
                <div style="width:12px;height:12px;background:{dot};border-radius:50%;margin-right:8px;"></div>
                <span style="font-weight:500;color:#374151">{lbl}</span>
            </div>""", unsafe_allow_html=True)

            # details under expander
            exp_key = f"exp_{run_id}_{num}"
            with st.expander(f"🔍 Step {num} details"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**💬 Output**")
                    st.text_area("", info["output"], height=100, disabled=True,
                                 key=f"out_{run_id}_{num}_{len(st.session_state.current_run_logs)}")
                    if info["tools"]:
                        st.markdown("**🔨 Tools**")
                        for t in info["tools"]:
                            st.code(str(t), language="python")
                with c2:
                    st.markdown("**🧾 Observations**")
                    st.text_area("", info["obs"], height=100, disabled=True,
                                 key=f"obs_{run_id}_{num}_{len(st.session_state.current_run_logs)}")
                    if info["err"]:
                        st.markdown("**❌ Error**")
                        st.error(info["err"])
                if info["input"] and len(info["input"]) < 800:
                    st.markdown("**📥 Input**")
                    st.text_area("", info["input"], height=80, disabled=True,
                                 key=f"inp_{run_id}_{num}_{len(st.session_state.current_run_logs)}")

    # attach & run
    set_agents_session_id(st.session_state.session_id)
    mgr_cb = manager_agent.step_callbacks.copy()
    anl_cb = analyst_agent.step_callbacks.copy()
    manager_agent.step_callbacks.append(log_cb)
    analyst_agent.step_callbacks.append(log_cb)

    try:
        st.write("🔍 Debug: Building prompt...")
        # build prompt from last 10 messages
        hist = get_recent_history(st.session_state.session_id, limit=10)
        txt = "\n".join(f"{m['role']}: {m['content']}" for m in hist)
        prompt = f"Recent history:\n{txt}\n\nUser: {st.session_state.pending_user_message}"
        st.write(f"🔍 Debug: Prompt built, length: {len(prompt)} chars")
        
        st.write("🤖 Debug: Calling manager_agent.run()...")
        resp = manager_agent.run(prompt)
        st.write(f"✅ Debug: Agent response received, length: {len(resp)} chars")

        with answer_ct:
            st.markdown("---")
            st.markdown("## 🤖 AI Assistant Response")
            st.markdown(f"""
                <div style="display:flex;align-items:flex-start;margin:30px 0;
                            border-top:1px solid #e2e8f0;padding-top:20px">
                  <div style="width:32px;height:32px;
                              background:linear-gradient(135deg,#6366f1,#8b5cf6);
                              border-radius:50%;display:flex;
                              align-items:center;justify-content:center;
                              margin-right:12px;">
                    <span style="color:white;font-weight:bold">AI</span>
                  </div>
                  <div style="background:#f8fafc;border:1px solid #e2e8f0;
                              border-radius:12px;padding:20px;flex:1;
                              line-height:1.6;color:#334155">
                    {resp}
                  </div>
                </div>
            """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"❌ Error during agent execution: {e}")
        st.write(f"🔍 Debug: Full error: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        resp = f"Sorry, I encountered an error: {str(e)}"
    
    finally:
        manager_agent.step_callbacks = mgr_cb
        analyst_agent.step_callbacks = anl_cb

    # store & append
    try:
        store_message(
            session_id=st.session_state.session_id,
            agent_name="Manager",
            role="agent",
            message=resp,
        )
        st.write("✅ Debug: Agent response stored successfully")
    except Exception as e:
        st.write(f"❌ Debug: Error storing agent response: {e}")
    
    st.session_state.messages.append({"role": "assistant", "content": resp})
    # Clear the pending message and processing flag
    st.session_state.pending_user_message = None
    st.session_state.processing_message = False
    st.write(f"✅ Debug: Cleared pending message and processing flag")

# ─────────────── Sidebar ─────────────────────
with st.sidebar:
    st.header("About")
    st.info("This AI agent can help you analyze your Shopify data…")
    st.header("Session Info")
    st.text(f"Session ID: {st.session_state.session_id}")
    st.text(f"Messages: {len(st.session_state.messages)}")
    link = f"/?session={st.session_state.session_id}"
    st.text_area("Session Link (copy to share/bookmark):", link, height=80)
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()
