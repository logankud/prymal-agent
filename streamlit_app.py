import streamlit as st
import os
from agents import manager_agent, analyst_agent
from memory_utils import store_message, get_recent_history

# Set page configuration
st.set_page_config(
    page_title="AI Agent Chat",
    page_icon="🤖",
    layout="wide"
)

# Session management functions
def get_or_create_session():
    """Get existing session ID from URL params or create new one"""
    # Check URL params for existing session
    query_params = st.query_params
    if "session" in query_params:
        session_id = query_params["session"]
        # Validate session exists in database
        try:
            existing_messages = get_recent_history(session_id=session_id, limit=100)
            if existing_messages:
                return session_id, existing_messages
        except Exception:
            pass  # Session doesn't exist or error occurred

    # Create new session
    import uuid
    new_session_id = f"streamlit_{str(uuid.uuid4())[:8]}"
    # Update URL with new session
    st.query_params["session"] = new_session_id
    return new_session_id, []

def load_session_history(session_id):
    """Load chat history for a session"""
    try:
        history = get_recent_history(session_id=session_id, limit=100)
        # Convert to streamlit message format
        messages = []
        for msg in history:
            if msg['role'] in ['user', 'agent']:
                role = 'user' if msg['role'] == 'user' else 'assistant'
                messages.append({"role": role, "content": msg['content']})
        return messages
    except Exception as e:
        st.error(f"Error loading session history: {e}")
        return []

# Initialize session state with persistence
if "session_id" not in st.session_state or "messages" not in st.session_state:
    session_id, existing_messages = get_or_create_session()
    st.session_state.session_id = session_id

    # Load messages from database if they exist, otherwise start empty
    if existing_messages:
        st.session_state.messages = load_session_history(session_id)
    else:
        st.session_state.messages = []

# Page header
st.title("🤖 AI Agent Chat Interface")
st.markdown("Chat with your AI agent for Shopify analysis and insights")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Display assistant messages as clear bot responses
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                border-radius: 15px;
                padding: 20px;
                margin: 10px 0;
                position: relative;
                box-shadow: 0 4px 8px rgba(76,175,80,0.3);
                border-left: 4px solid #2E7D32;
            ">
                <div style="
                    position: absolute;
                    left: -10px;
                    top: 20px;
                    width: 0;
                    height: 0;
                    border-top: 10px solid transparent;
                    border-bottom: 10px solid transparent;
                    border-right: 15px solid #4CAF50;
                "></div>
                <div style="
                    font-size: 16px;
                    line-height: 1.5;
                    font-weight: 500;
                ">
                    🤖 {message["content"]}
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("What would you like to know about your Shopify data?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Store user message in database
    store_message(
        session_id=st.session_state.session_id,
        agent_name='user',
        role='user',
        message=prompt
    )

    # Generate AI response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # Get recent chat history for context
                recent_chat_history = get_recent_history(
                    session_id=st.session_state.session_id,
                    limit=10
                )

                # Construct the prompt with memory
                recent_chat_text = "\n".join([
                    f"{msg['role']}: {msg['content']}" 
                    for msg in recent_chat_history
                ])

                full_prompt = f"""Recent chat history: 
{recent_chat_text}

User Input: 
{prompt}
"""

                # Create containers for logs and final answer
                logs_container = st.container()
                final_answer_container = st.container()

                # Initialize session state for current run logs if not exists
                if "current_run_logs" not in st.session_state:
                    st.session_state.current_run_logs = []

                # Clear current run logs for new query
                st.session_state.current_run_logs = []

                # Custom callback to capture logs for Streamlit display
                def streamlit_log_callback(step, agent):
                    # Build step information
                    step_info = {
                        "step_number": step.step_number,
                        "agent_name": agent.name,
                        "input_text": None,
                        "output_text": getattr(step, "action_output", None),
                        "tool_calls": getattr(step, "tool_calls", None),
                        "observations": getattr(step, "observations", None),
                        "error": getattr(step, "error", None)
                    }

                    # Try to get input from agent memory
                    try:
                        prompt_msgs = agent.write_memory_to_messages()
                        step_info["input_text"] = "\n".join([f"{m['role']}: {m['content']}" for m in prompt_msgs])
                    except Exception:
                        step_info["input_text"] = "[Input unavailable]"

                    # Add to session state logs
                    st.session_state.current_run_logs.append(step_info)

                    # Display the step as an interactive thought bubble in real-time
                    with logs_container:
                        # Create thought bubble style container
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #e8f4fd 0%, #f1f8ff 100%);
                            border: 2px dashed #0066cc;
                            border-radius: 25px;
                            padding: 20px;
                            margin: 15px 0;
                            position: relative;
                            opacity: 0.9;
                            box-shadow: 0 4px 8px rgba(0,102,204,0.2);
                        ">
                            <div style="
                                position: absolute;
                                left: -15px;
                                top: 30px;
                                width: 0;
                                height: 0;
                                border-top: 15px solid transparent;
                                border-bottom: 15px solid transparent;
                                border-right: 20px solid #e8f4fd;
                            "></div>
                            <div style="
                                font-size: 16px;
                                font-weight: bold;
                                color: #0066cc;
                                margin-bottom: 10px;
                                font-style: italic;
                            ">
                                🤔 {agent.name} is thinking... (Step {step.step_number})
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Expandable details for the thought process
                        with st.expander(f"💭 View {agent.name}'s thought process (Step {step.step_number})", expanded=False):
                            st.markdown("**🧠 Agent Internal Processing:**")

                            col1, col2 = st.columns(2)

                            with col1:
                                if step_info["output_text"]:
                                    st.markdown("**💬 Agent Output:**")
                                    st.text_area("", step_info["output_text"], height=120, disabled=True, key=f"output_{step.step_number}")

                                if step_info["tool_calls"]:
                                    st.markdown("**🔨 Tool Calls:**")
                                    for i, tc in enumerate(step_info["tool_calls"]):
                                        st.code(str(tc), language="python")

                            with col2:
                                if step_info["observations"]:
                                    st.markdown("**🧾 Tool Results:**")
                                    st.text_area("", step_info["observations"], height=120, disabled=True, key=f"obs_{step.step_number}")

                                if step_info["error"]:
                                    st.markdown("**❌ Error:**")
                                    st.error(step_info["error"])

                            if step_info["input_text"] and len(step_info["input_text"]) < 1000:
                                st.markdown("**📥 Context/Input:**")
                                st.text_area("", step_info["input_text"], height=80, disabled=True, key=f"input_{step.step_number}")

                # Temporarily add our callback to both manager and analyst agents
                original_manager_callbacks = manager_agent.step_callbacks.copy()
                manager_agent.step_callbacks.append(streamlit_log_callback)

                # Also add to analyst agent
                original_analyst_callbacks = analyst_agent.step_callbacks.copy()
                analyst_agent.step_callbacks.append(streamlit_log_callback)

                try:
                    # Get response from manager agent
                    response = manager_agent.run(full_prompt)

                    # Display final answer as clear bot response
                    with final_answer_container:
                        st.markdown("---")
                        st.markdown("## 🤖 AI Assistant Response")

                        # Bot response container with clear styling
                        st.markdown(f"""
                        <div style="
                            background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                            color: white;
                            border-radius: 15px;
                            padding: 25px;
                            margin: 20px 0;
                            position: relative;
                            box-shadow: 0 6px 12px rgba(76,175,80,0.3);
                            border-left: 5px solid #2E7D32;
                        ">
                            <div style="
                                position: absolute;
                                left: -12px;
                                top: 25px;
                                width: 0;
                                height: 0;
                                border-top: 12px solid transparent;
                                border-bottom: 12px solid transparent;
                                border-right: 15px solid #4CAF50;
                            "></div>
                            <div style="
                                font-size: 18px;
                                line-height: 1.6;
                                font-weight: 500;
                            ">
                                {response}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                finally:
                    # Restore original callbacks for both agents
                    manager_agent.step_callbacks = original_manager_callbacks
                    analyst_agent.step_callbacks = original_analyst_callbacks

                # Store agent response
                store_message(
                    session_id=st.session_state.session_id,
                    agent_name='Manager',
                    role='agent',
                    message=response
                )

                # Add to session state (only the final answer for chat history)
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })

            except Exception as e:
                # Handle specific torch-related errors
                if "torch" in str(e).lower() or "event loop" in str(e).lower():
                    error_message = "I'm experiencing a technical issue. Please try refreshing the page or restarting the chat."
                else:
                    error_message = f"Sorry, I encountered an error: {str(e)}"

                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

                # Log the full error for debugging
                st.write("Debug info:", str(e))

# Sidebar with info
with st.sidebar:
    st.header("About")
    st.info(
        "This AI agent can help you analyze your Shopify data, "
        "answer questions about orders, customers, products, and more."
    )

    st.header("Session Info")
    st.text(f"Session ID: {st.session_state.session_id}")
    st.text(f"Messages: {len(st.session_state.messages)}")

    # Copy session link
    try:
        base_url = st.get_option('browser.serverAddress')
        port = st.get_option('browser.serverPort')
        current_url = f"http://{base_url}:{port}/?session={st.session_state.session_id}"
    except:
        current_url = f"/?session={st.session_state.session_id}"
    st.text_area("Session Link (copy to share/bookmark):", current_url, height=80)

    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()