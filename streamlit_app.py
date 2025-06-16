import streamlit as st
import os

# Fix PyTorch compatibility with Streamlit
import sys
if 'torch' in sys.modules:
    import torch
    # Prevent Streamlit from inspecting torch modules that cause issues
    torch._classes.__path__ = []

from agents import manager_agent, analyst_agent, set_agents_session_id
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
    if message["role"] == "assistant":
        # Display assistant messages in clean style like the image
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: flex-start;
            margin: 20px 0;
        ">
            <div style="
                width: 32px;
                height: 32px;
                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                margin-right: 12px;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 14px; font-weight: bold;">AI</span>
            </div>
            <div style="
                background: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 16px;
                flex: 1;
                line-height: 1.6;
                color: #334155;
            ">
                {message["content"]}
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Display user messages in clean style
        st.markdown(f"""
        <div style="
            display: flex;
            align-items: flex-start;
            margin: 20px 0;
            justify-content: flex-end;
        ">
            <div style="
                background: #3b82f6;
                color: white;
                border-radius: 12px;
                padding: 16px;
                max-width: 70%;
                line-height: 1.6;
                margin-right: 12px;
            ">
                {message["content"]}
            </div>
            <div style="
                width: 32px;
                height: 32px;
                background: #3b82f6;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            ">
                <span style="color: white; font-size: 14px; font-weight: bold;">U</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

# Chat input
if prompt := st.chat_input("What would you like to know about your Shopify data?"):
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in clean style
    st.markdown(f"""
    <div style="
        display: flex;
        align-items: flex-start;
        margin: 20px 0;
        justify-content: flex-end;
    ">
        <div style="
            background: #3b82f6;
            color: white;
            border-radius: 12px;
            padding: 16px;
            max-width: 70%;
            line-height: 1.6;
            margin-right: 12px;
        ">
            {prompt}
        </div>
        <div style="
            width: 32px;
            height: 32px;
            background: #3b82f6;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            flex-shrink: 0;
        ">
            <span style="color: white; font-size: 14px; font-weight: bold;">U</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

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
                        # Generate step description based on tool calls or output
                        step_description = ""
                        if step_info["tool_calls"]:
                            # Extract tool name from first tool call
                            tool_call = step_info["tool_calls"][0]
                            if hasattr(tool_call, 'name'):
                                step_description = f"🔧 {tool_call.name}"
                            elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                step_description = f"🔧 {tool_call.function.name}"
                            else:
                                tool_str = str(tool_call)
                                if "run_shopify_query" in tool_str:
                                    step_description = "🔧 Shopify Query"
                                elif "search_shopify_docs" in tool_str:
                                    step_description = "📚 Docs Search"
                                elif "introspect_shopify_schema" in tool_str:
                                    step_description = "🔍 Schema Introspection"
                                elif "python_interpreter" in tool_str:
                                    step_description = "🐍 Python Code"
                                else:
                                    step_description = "🔧 Tool Call"
                        elif step_info["output_text"] and len(step_info["output_text"]) > 0:
                            # Try to infer step type from output content
                            output_lower = step_info["output_text"].lower()
                            if "thought:" in output_lower:
                                step_description = "💭 Planning"
                            elif "code:" in output_lower or "```" in step_info["output_text"]:
                                step_description = "💻 Coding"
                            elif "final_answer" in output_lower:
                                step_description = "✅ Final Answer"
                            else:
                                step_description = "🧠 Processing"
                        else:
                            step_description = "🤔 Analyzing"

                        # Create clean step indicator like in the image
                        if step_info["tool_calls"]:
                            # Tool call step - show green dot with tool name
                            tool_call = step_info["tool_calls"][0]
                            tool_name = "Unknown Tool"
                            if hasattr(tool_call, 'name'):
                                tool_name = tool_call.name
                            elif hasattr(tool_call, 'function') and hasattr(tool_call.function, 'name'):
                                tool_name = tool_call.function.name
                            else:
                                tool_str = str(tool_call)
                                if "run_shopify_query" in tool_str:
                                    tool_name = "Shopify Query"
                                elif "search_shopify_docs" in tool_str:
                                    tool_name = "Documentation Search"
                                elif "introspect_shopify_schema" in tool_str:
                                    tool_name = "Schema Analysis"
                                elif "python_interpreter" in tool_str:
                                    tool_name = "Python Analysis"
                            
                            st.markdown(f"""
                            <div style="
                                display: flex;
                                align-items: center;
                                padding: 8px 0;
                                margin: 5px 0;
                            ">
                                <div style="
                                    width: 12px;
                                    height: 12px;
                                    background-color: #22c55e;
                                    border-radius: 50%;
                                    margin-right: 12px;
                                "></div>
                                <span style="
                                    font-size: 14px;
                                    color: #374151;
                                    font-weight: 500;
                                ">
                                    {tool_name}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            # Thinking step - show thinking indicator
                            st.markdown(f"""
                            <div style="
                                display: flex;
                                align-items: center;
                                padding: 8px 0;
                                margin: 5px 0;
                            ">
                                <div style="
                                    width: 12px;
                                    height: 12px;
                                    background-color: #3b82f6;
                                    border-radius: 50%;
                                    margin-right: 12px;
                                "></div>
                                <span style="
                                    font-size: 14px;
                                    color: #374151;
                                    font-weight: 500;
                                ">
                                    {step_description}
                                </span>
                            </div>
                            """, unsafe_allow_html=True)

                        # Expandable details for the thought process (less prominent)
                        with st.expander(f"🔍 Step {step.step_number} details", expanded=False):
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

                # Set the session ID on both agents before running
                set_agents_session_id(st.session_state.session_id)

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

                        # Final answer in clean conversational style
                        st.markdown(f"""
                        <div style="
                            display: flex;
                            align-items: flex-start;
                            margin: 30px 0;
                            border-top: 1px solid #e2e8f0;
                            padding-top: 20px;
                        ">
                            <div style="
                                width: 32px;
                                height: 32px;
                                background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                                border-radius: 50%;
                                display: flex;
                                align-items: center;
                                justify-content: center;
                                margin-right: 12px;
                                flex-shrink: 0;
                            ">
                                <span style="color: white; font-size: 14px; font-weight: bold;">AI</span>
                            </div>
                            <div style="
                                background: #f8fafc;
                                border: 1px solid #e2e8f0;
                                border-radius: 12px;
                                padding: 20px;
                                flex: 1;
                                line-height: 1.6;
                                color: #334155;
                                font-size: 16px;
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