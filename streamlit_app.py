
import streamlit as st
import os
from agents import manager_agent
from memory_utils import store_message, get_recent_history

# Set page configuration
st.set_page_config(
    page_title="AI Agent Chat",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "session_id" not in st.session_state:
    import uuid
    st.session_state.session_id = f"streamlit_{str(uuid.uuid4())[:8]}"

# Page header
st.title("🤖 AI Agent Chat Interface")
st.markdown("Chat with your AI agent for Shopify analysis and insights")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message["role"] == "assistant":
            # Display assistant messages in thought bubble style
            st.markdown(f"""
            <div style="
                background-color: #f0f2f6;
                border: 2px solid #e1e5e9;
                border-radius: 20px;
                padding: 20px;
                margin: 10px 0;
                position: relative;
                font-style: italic;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
                <div style="
                    position: absolute;
                    left: -10px;
                    top: 20px;
                    width: 0;
                    height: 0;
                    border-top: 10px solid transparent;
                    border-bottom: 10px solid transparent;
                    border-right: 15px solid #f0f2f6;
                "></div>
                {message["content"]}
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
                    
                    # Display the step in real-time
                    with logs_container:
                        with st.expander(f"🔍 Step {step.step_number} - {agent.name}", expanded=False):
                            if step_info["input_text"]:
                                st.text_area("📥 Input", step_info["input_text"], height=100, disabled=True)
                            
                            if step_info["output_text"]:
                                st.text_area("📤 Output", step_info["output_text"], height=100, disabled=True)
                            
                            if step_info["tool_calls"]:
                                st.json({"🔨 Tool Calls": [str(tc) for tc in step_info["tool_calls"]]})
                            
                            if step_info["observations"]:
                                st.text_area("🧾 Observations", step_info["observations"], height=80, disabled=True)
                            
                            if step_info["error"]:
                                st.error(f"❌ Error: {step_info['error']}")
                
                # Temporarily add our callback to the manager agent
                original_callbacks = manager_agent.step_callbacks.copy()
                manager_agent.step_callbacks.append(streamlit_log_callback)
                
                try:
                    # Get response from manager agent
                    response = manager_agent.run(full_prompt)
                    
                    # Display final answer in thought bubble style
                    with final_answer_container:
                        st.markdown("### 💭 Final Answer")
                        st.markdown(f"""
                        <div style="
                            background-color: #f0f2f6;
                            border: 2px solid #e1e5e9;
                            border-radius: 20px;
                            padding: 20px;
                            margin: 10px 0;
                            position: relative;
                            font-style: italic;
                            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        ">
                            <div style="
                                position: absolute;
                                left: -10px;
                                top: 20px;
                                width: 0;
                                height: 0;
                                border-top: 10px solid transparent;
                                border-bottom: 10px solid transparent;
                                border-right: 15px solid #f0f2f6;
                            "></div>
                            {response}
                        </div>
                        """, unsafe_allow_html=True)
                    
                finally:
                    # Restore original callbacks
                    manager_agent.step_callbacks = original_callbacks
                
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
    
    # Clear chat button
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.rerun()
