from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import os
import sys
import uuid
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.helper import get_stream_generator, get_thread_state, get_all_threads
from langchain_core.messages import HumanMessage

st.title("Hello Abhi!")

# 1 sidebar layout
with st.sidebar:
    st.title("Chat History")
    if st.button("+ New Chat"):
        st.session_state.messages = [] # Clear history
        st.session_state.thread_id = str(uuid.uuid4()) # new thread_id is created for every new chat button
        st.rerun() # reruns , UI restarts new thread_id will be generated and  chat window updated with empty messages

    st.markdown("---")
    all_threads = get_all_threads()
    for t_id in all_threads:
        display_name = f"Chat: {t_id[:8]}..."  # Display ID as chat history sidebar button label

        if st.sidebar.button(display_name):
            st.session_state.thread_id = t_id
            st.session_state.messages = [] # Clear current view
            
            old_msgs = get_thread_state(t_id) # Fetch and convert old messages
            for msg in old_msgs:
                if not msg.content or msg.content.strip() == "":
                    continue
                role = "user" if isinstance(msg, HumanMessage) else "assistant"
                st.session_state.messages.append({"role": role, "text": msg.content})
            st.rerun()


# 2 Initialize and Display Session State
if "messages" not in st.session_state:
    st.session_state.messages = []
if "thread_id" not in st.session_state:  # if page is refreshed new thread_id is created
    st.session_state.thread_id = str(uuid.uuid4())
# Display all previous messages stored in session state every time the page reloads
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["text"])


user_query = st.chat_input("Type your message here...")
if user_query:
    ### user side
    with st.chat_message("user"):
        st.write(user_query)
    st.session_state.messages.append({"role": "user", "text": user_query})

    ### AI side
    with st.chat_message("assistant"):
        def agent_stream_ui_handler():
            status_box = None
            # Clean call! No silly chatbot argument dragged here anymore
            response_stream = get_stream_generator(user_query, st.session_state.thread_id)
            
            for item in response_stream:
                if item["type"] == "tool":
                    tool_name = item["name"]
                    if status_box is None:
                        status_box = st.status(f"🔧 Using '{tool_name}'...", expanded=True)
                    else:
                        status_box.update(label=f"🔧 Using '{tool_name}'...", state="running", expanded=True)
                
                elif item["type"] == "text":
                    if status_box:
                        status_box.update(label="✅ Tool finished", state="complete", expanded=False)
                        status_box = None
                    yield item["content"]

        ai_response = st.write_stream(agent_stream_ui_handler())
    st.session_state.messages.append({"role": "assistant", "text": ai_response})