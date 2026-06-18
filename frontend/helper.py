from langchain_core.messages import HumanMessage
from backend.graph import chatbot,checkpointer

def get_stream_generator(user_query, thread_id):
    config = {
        "configurable": {"thread_id": thread_id},
        "metadata": {
            "thread_id": thread_id
        },
        "run_name": "chat_turn"
    }
    stream = chatbot.stream(
        {"messages": [HumanMessage(content=user_query)]},
        config=config,
        stream_mode="messages"
    )
    for message_chunk, metadata in stream:
        if message_chunk.content:
            yield message_chunk.content

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
