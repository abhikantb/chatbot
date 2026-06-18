import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
load_dotenv()
from typing import TypedDict,Annotated
from langchain_core.messages import BaseMessage,HumanMessage
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq
llm=ChatGroq(model="llama-3.3-70b-versatile",temperature=0.3)
from langgraph.graph import StateGraph,START,END
from langgraph.checkpoint.sqlite import SqliteSaver
import sqlite3
from langsmith import traceable


class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]

@traceable
def chat_node(state:ChatState):
    messages = state['messages']
    response= llm.invoke(messages)
    return {'messages':[response]}

conn= sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

graph=StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_edge(START,'chat_node')
graph.add_edge('chat_node',END)

chatbot=graph.compile(checkpointer=checkpointer)

## for stream use below code
# stream = chatbot.stream(
#     {'messages': [HumanMessage(content='What is the recipe to make pasta')]},
#     config={"configurable": {"thread_id": "streamlit_test_1"}},
#     stream_mode="messages")

# # This loop pulls the data out of the generator and prints it
# for message_chunk, metadata in stream:
#     if message_chunk.content:
#         print(message_chunk.content, end=" ", flush=True)