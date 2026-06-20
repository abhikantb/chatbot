from langchain_core.messages import HumanMessage,ToolMessage
from backend.graph import chatbot,checkpointer

def get_stream_generator(user_query, thread_id):
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {"thread_id": thread_id},
        "run_name": "chat_turn"
    }
    def agent_stream_generator():
        stream = chatbot.stream(   # streaming(display) messages as soon as llm generates them
            {"messages": [HumanMessage(content=user_query)]},
            config=config,
            stream_mode="messages",
        )
        for message_chunk, metadata in stream:
            if isinstance(message_chunk, ToolMessage):
                tool_name = getattr(message_chunk, "name", "tool")
                yield {"type": "tool", "name": tool_name}
                continue    # Skip yielding ToolMessages as stream message, go for next message chunk
                            # otherwise tool msg will be displayed unnecesary in chat window
            
            # filter only AI messages to be displayed to the user (HumanMessage and ToolMessage are not displayed)
            if message_chunk.content and not isinstance(message_chunk, (HumanMessage, ToolMessage)): 
                yield {"type": "text", "content": message_chunk.content}
                
    return agent_stream_generator()

def get_thread_state(thread_id):
    config = {'configurable': {'thread_id': thread_id}}
    state = chatbot.get_state(config=config)
    return state.values.get('messages', [])

def get_all_threads():
    # By passing None, the database won't filter anything. will show every thread in database
    checkpoints = list(checkpointer.list(None))
    # function to get the timestamp from a checkpoint
    def check_time(checkpoint):
        metadata_pocket = checkpoint.metadata
        return metadata_pocket.get('updated_at', '')
    sorted_checkpoints = sorted(checkpoints, key=check_time, reverse=True) # Sort checkpoints chronologically (Newest first)
    
    # Extract unique thread ID as per updated_at column in database
    unique_thread_ids = []
    for checkpoint in sorted_checkpoints:
        thread_id = checkpoint.config['configurable']['thread_id'] 
        if thread_id not in unique_thread_ids:
            unique_thread_ids.append(thread_id)
            
    return unique_thread_ids
