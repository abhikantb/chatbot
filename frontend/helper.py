from langchain_core.messages import HumanMessage,ToolMessage
from backend.graph import chatbot,checkpointer
import streamlit as st

def get_stream_generator(user_query, thread_id):
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id},
        "run_name": "chat_turn"
    }
    status_holder = {"box": None} # for displaying tool name in UI
    def ai_only_stream():
        stream = chatbot.stream(   # streaming(display) messages as soon as llm generates them
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            stream_mode="messages",
        )
        for message_chunk, metadata in stream:
            if isinstance(message_chunk, ToolMessage):
                tool_name = getattr(message_chunk, "name", "tool")
                if status_holder["box"] is None:
                    status_holder["box"] = st.status(f"🔧 Using '{tool_name}'...", expanded=True)
                else:
                    status_holder["box"].update(label=f"🔧 Using '{tool_name}'...", state="running", expanded=True)
                continue    # Skip yielding ToolMessages as stream message, go for next message chunk
                            # otherwise tool msg will be displayed unnecesary in chat window
            
            # filter only AI messages to be displayed to the user (HumanMessage and ToolMessage are not displayed)
            if message_chunk.content and not isinstance(message_chunk, (HumanMessage, ToolMessage)): 
                # If a tool box is still open, close it when AI text starts
                if status_holder["box"]:
                    status_holder["box"].update(label="✅ Tool finished", state="complete", expanded=False)
                    status_holder["box"] = None
                yield message_chunk.content
                
    return ai_only_stream()

def get_thread_state(thread_id):
    config = {'configurable': {'thread_id': thread_id}}
    state = chatbot.get_state(config=config)
    return state.values.get('messages', [])

def get_all_threads():
    checkpoints = checkpointer.list(None)
    threads = set()
    for checkpoint in checkpoints:
        threads.add(checkpoint.config['configurable']['thread_id'])
    return sorted(list(threads), reverse=True)
