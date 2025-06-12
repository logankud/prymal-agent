
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
    st.session_state.session_id = f"streamlit_{hash(str(st.experimental_user))}"

# Page header
st.title("🤖 AI Agent Chat Interface")
st.markdown("Chat with your AI agent for Shopify analysis and insights")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
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
                
                # Get response from manager agent
                response = manager_agent.run(full_prompt)
                
                # Display response
                st.markdown(response)
                
                # Store agent response
                store_message(
                    session_id=st.session_state.session_id,
                    agent_name='Manager',
                    role='agent',
                    message=response
                )
                
                # Add to session state
                st.session_state.messages.append({
                    "role": "assistant", 
                    "content": response
                })
                
            except Exception as e:
                error_message = f"Sorry, I encountered an error: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": error_message
                })

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
