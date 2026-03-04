# ---------------------------------------------------------
# Chainlit Retail Store Assistant

import chainlit as cl
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import ClientSession, StdioServerParameters
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_core.messages import AIMessage, ToolMessage
from langchain.tools import tool
from dotenv import load_dotenv
from langchain_core.runnables import RunnableLambda
from operator import itemgetter
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate

from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.agents import create_agent
from langgraph.prebuilt import create_react_agent
from langgraph_supervisor import create_supervisor
import os
import asyncio

load_dotenv(override=True)

########################################################################################################################
# PREPARE RAG SYSTEM PROMPT
########################################################################################################################

# bring in the system instructions
with open("rag-system-prompt.txt", "r", encoding="utf-8") as f:
    rag_system_text = f.read()


########################################################################################################################
# PREPARE SQL SYSTEM PROMPT
########################################################################################################################

# bring in the system instructions
with open("sql-system-prompt.txt", "r", encoding="utf-8") as f:
    sql_system_text = f.read()


########################################################################################################################
# Load the vector DB with embeddings
########################################################################################################################

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Chroma(persist_directory="retail_vector_db_chroma",
                     collection_name="retail_help_qa",
                     embedding_function=embeddings)

########################################################################################################################
# Create a retriever object with a suitable k value (e.g., 8)
########################################################################################################################

#retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

retriever = vectorstore.as_retriever(search_type="similarity_score_threshold", search_kwargs={"k": 6,  "score_threshold": 0.25})



########################################################################################################################
# Initialize LLM model
########################################################################################################################
llm = ChatOpenAI(model="gpt-4.1", temperature=0)

########################################################################################################################
# Define tool for RAG generation
########################################################################################################################

prompt = ChatPromptTemplate.from_template(rag_system_text)

def format_docs(docs):
    contents = [d.page_content for d in docs]
    return "\n\n".join(contents)

@tool
async def rag_agent(question: str):
    """Use this tool for questions about store policies, returns, or general FAQs."""

    # RAG answer chain: {input} -> retrieve -> format -> prompt -> model -> string
    # In the context of a RAG pipeline, RunnableLambda(format_docs) is a bridge that transforms the raw output of a retriever (list of document objects) into a format the LLM can understand
    # RunnableLambda does Type Conversion + Chain Integration + allows Observability in langsmith - this formatting step will show up as its own named block, allowing you to see exactly what "context" was sent to the prompt after retrieval
    rag_answer_chain = (
        {
            "context": itemgetter("input") | retriever | RunnableLambda(format_docs),
            "question": itemgetter("input"),    
        }
        | prompt
        | llm
    )
    response = await rag_answer_chain.ainvoke({"input": question})
    return response.content

########################################################################################################################
# Code for chainlit UI
########################################################################################################################

@cl.on_chat_start
async def start():
    mcp_tools = []

    # Setup MCP Connection
    # Configure the servers in a dictionary format
    server_config = {
        "postgres": {
            "command": "npx",
            "args": [
                "-y", 
                "@modelcontextprotocol/server-postgres", 
                f"postgresql://postgres:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DBNAME')}?sslmode=no-verify"
            ],
            "transport": "stdio"
        }
    }

    try:
        # Initialize the MultiServer client
        client = MultiServerMCPClient(server_config)
        cl.user_session.set("mcp_client", client)

        mcp_tools = await asyncio.wait_for(client.get_tools(), timeout=15.0)
        print(f"Successfully loaded {len(mcp_tools)} tools from MCP")

    except Exception as e:
        await cl.Message(content=f"⚠️ Connection failed: {str(e)}").send()
        mcp_tools = []

    sql_agent = create_agent(
            llm, 
            tools=mcp_tools, 
            system_prompt=sql_system_text
        )

    @tool
    async def sales_db_tool(query: str):
        """Use this for order status, shipping status or sales data."""

        try:

            response = await sql_agent.ainvoke({"messages": [("user", query)]})
            return response["messages"][-1].content
        except Exception as e:
            return f"Error accessing database: {str(e)}"

    # Initialize the parent Agent
    parent_agent = create_agent(ChatOpenAI(model="gpt-4.1", temperature=0), 
                                tools=[sales_db_tool, rag_agent],
                                system_prompt="You are a retail assistant. Route queries to the order expert or policy expert as needed."
                                )
    cl.user_session.set("parent_agent", parent_agent)

    await cl.Message(content="Hello! I'm your retail assistant. How can I help with your order or our policies today?").send()

# --- Message Handling ---
@cl.on_message
async def handle_message(message: cl.Message):
    """Handle user messages and stream agent responses."""
    print("Inside on message func")
    final_answer = ""
    agent = cl.user_session.get("parent_agent")

    res = await agent.ainvoke({"messages": [("user", message.content)]})

    await cl.Message(content=res["messages"][-1].content).send()

@cl.on_chat_end
async def end():
    # Cleanup MCP connection
    transport = cl.user_session.get("mcp_transport")
    if transport:
        await transport.__aexit__(None, None, None)
