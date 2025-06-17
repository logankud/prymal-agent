import streamlit as st
import sys
import uuid

# Fix PyTorch compatibility with Streamlit
if "torch" in sys.modules:
    import torch
    torch._classes.__path__ = []

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

# ──────────────── New user input ─────────────────────
# Generate a unique run_id for every new prompt
run_id = uuid.uuid4().hex[:8]

# Pass run_id into the key for chat_input
user_prompt = st.chat_input(
    "What would you like to know about your Shopify data?",
    key=f"chat_input_{run_id}"
)

if user_prompt:
    # 1) echo & store user
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    store_message(
        session_id=st.session_state.session_id,
        agent_name="user",
        role="user",
        message=user_prompt,
    )
    # Set a flag to process the message on next run
    st.session_state.process_user_message = True
    st.experimental_rerun()  # to render the newly appended message immediately

# ──────────────── Process agent response if flagged ────────────────
if getattr(st.session_state, 'process_user_message', False) and st.session_state.messages and st.session_state.messages[-1]["role"] == "user":
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
        # build prompt from last 10 messages
        hist = get_recent_history(st.session_state.session_id, limit=10)
        txt = "\n".join(f"{m['role']}: {m['content']}" for m in hist)
        prompt = f"Recent history:\n{txt}\n\nUser: {st.session_state.messages[-1]['content']}"
        resp = manager_agent.run(prompt)

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

    finally:
        manager_agent.step_callbacks = mgr_cb
        analyst_agent.step_callbacks = anl_cb

    # store & append
    store_message(
        session_id=st.session_state.session_id,
        agent_name="Manager",
        role="agent",
        message=resp,
    )
    st.session_state.messages.append({"role": "assistant", "content": resp})
    # Clear the processing flag
    st.session_state.process_user_message = False

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
