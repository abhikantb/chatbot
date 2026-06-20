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
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
import requests
import os
weatherstack_API_KEY = os.getenv("weatherstack_API_KEY")
alpha_vantage_stock_API_KEY = os.getenv("alpha_vantage_stock_API_KEY")

# -------------------
# 1 tools 
# -------------------
@tool
def web_search(query: str) -> str:
    """Search the web for current events, news, or general information."""
    search_tool = DuckDuckGoSearchRun(region="us-en")
    return search_tool.run(query)

@tool
def get_weather_data(city: str) -> str:
    """
    This function fetches the current weather data for a given city
    """
    url = f'https://api.weatherstack.com/current?access_key={weatherstack_API_KEY}&query={city}'
    response = requests.get(url)
    return response.json()

@tool
def get_stock_price(symbol: str) -> dict:
    """
    Fetch latest stock price for a given symbol (e.g. 'AAPL', 'TSLA') 
    using Alpha Vantage with API key in the URL.
    """
    url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={alpha_vantage_stock_API_KEY}"
    r = requests.get(url)
    return r.json()

tools = [web_search, get_weather_data, get_stock_price]
llm_with_tools = llm.bind_tools(tools,tool_choice="auto")

# -------------------
# 2 state
# -------------------
class ChatState(TypedDict):
    messages : Annotated[list[BaseMessage],add_messages]

# -------------------
# 3 all nodes
# -------------------
tool_node = ToolNode(tools)

@traceable
def chat_node(state:ChatState):
    messages = state['messages']
    response= llm_with_tools.invoke(messages)
    return {'messages':[response]}

# -------------------
# 4 checkpointer
# -------------------
conn= sqlite3.connect(database='chatbot.db',check_same_thread=False)
checkpointer = SqliteSaver(conn=conn)

# -------------------
# 5 graph
# -------------------
graph=StateGraph(ChatState)
graph.add_node('chat_node',chat_node)
graph.add_node('tools',tool_node)

graph.add_edge(START,'chat_node')
graph.add_conditional_edges('chat_node',tools_condition)
graph.add_edge('tools', 'chat_node')

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

# if __name__ == "__main__":
#     from langchain_core.messages import HumanMessage
    
#     # This sends a message to your compiled chatbot
#     config = {"configurable": {"thread_id": "test_thread"}}
#     initial_state = {"messages": [HumanMessage(content="Hello! Can you hear me?")]}
    
#     print("Invoking chatbot...")
#     response = chatbot.invoke(initial_state, config=config)
    
#     # Print the last message from the AI
#     print("AI Response:", response["messages"][-1].content)