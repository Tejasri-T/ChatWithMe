from __future__ import annotations


import tempfile
import os
from uuid import MAX
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import StateGraph,START,END
from typing import Any, Dict, Literal, TypedDict,Annotated,Optional
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from dotenv import load_dotenv
from langgraph.graph.message import add_messages
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite import SqliteSaver
from langchain_core.messages import BaseMessage,SystemMessage, HumanMessage
from openai import BaseModel
import sqlite3
from langchain_community.vectorstores import FAISS
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_community.tools import DuckDuckGoSearchRun
from langchain_core.tools import tool



load_dotenv()

# -------------------
# 2. PDF retriever store (per thread)
# -------------------
_THREAD_RETRIEVERS: Dict[str, Any] = {}
_THREAD_METADATA: Dict[str, dict] = {}

MAX_TOKENS = 4096


llm = ChatGoogleGenerativeAI(model = "gemini-3.5-flash-lite")
embeddings = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2-preview")


#-------------------load pdf------------------------------
def _get_retriever(thread_id: Optional[str]):
    """Fetch the retriever for a thread if available."""
    if thread_id and thread_id in _THREAD_RETRIEVERS:
        return _THREAD_RETRIEVERS[thread_id]
    return None


def ingest_pdf(file_bytes: bytes, thread_id: str, filename: Optional[str] = None) -> dict:
    """
    Build a FAISS retriever for the uploaded PDF and store it for the thread.

    Returns a summary dict that can be surfaced in the UI.
    """
    if not file_bytes:
        raise ValueError("No bytes received for ingestion.")

    print(f"Ingesting PDF for thread {thread_id} with filename: {filename or 'Unnamed'}")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(file_bytes)
        temp_path = temp_file.name

    try:
        loader = PyPDFLoader(temp_path)
        docs = loader.load()

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000, chunk_overlap=200, separators=["\n\n", "\n", " ", ""]
        )
        chunks = splitter.split_documents(docs)

        vector_store = FAISS.from_documents(chunks, embeddings)
        retriever = vector_store.as_retriever(
            search_type="similarity", search_kwargs={"k": 4}
        )

        _THREAD_RETRIEVERS[str(thread_id)] = retriever
        _THREAD_METADATA[str(thread_id)] = {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }

        return {
            "filename": filename or os.path.basename(temp_path),
            "documents": len(docs),
            "chunks": len(chunks),
        }
    finally:
        # The FAISS store keeps copies of the text, so the temp file is safe to remove.
        try:
            os.remove(temp_path)
        except OSError:
            pass



#--------------Tools and Tool Node-------------------------

search_tool = DuckDuckGoSearchRun(region="us-en")

@tool
def rag_tool(query: str, thread_id: Optional[str] = None)-> dict:
    """
    Retrieve relevant information from the pdf document.
Use this tool when the user asks factual / conceptual questions that might be answered from the stored documents.
    """
    
    retriever = _get_retriever(thread_id)
    
    if retriever is None:
        return {
            "error": "No document indexed for this chat. Upload a PDF first.",
            "query": query,
        }
    
    results = retriever.invoke(query)
    
    context = [doc.page_content for doc in results]
    
    metadata = [doc.metadata for doc in results]
    
    return {
        "query": query,
        "context": context,
        "metadata": metadata,
        "source_file": _THREAD_METADATA.get(str(thread_id), {}).get("filename"),
    }
    
    
tools = [search_tool,rag_tool]

llm_with_tools = llm.bind_tools(tools)


#----------Database connection-------------
conn = sqlite3.connect(database='chatbot.db',check_same_thread=False)

# Create naming database
cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS chat_threads (
        thread_id TEXT PRIMARY KEY,
        chat_name TEXT
    )
""")

conn.commit()




class ChatState(TypedDict):
    
    messages: Annotated[list[BaseMessage],add_messages]
    # name:str
 

#--------------Name Bot------------------------

class NameState(TypedDict):
    messages:list
    name:str
   
class NameSchema(BaseModel):
    name: str
    
structured_llm = llm.with_structured_output(NameSchema)
    
def name_node(state:NameState,config):
    
    cursor.execute("""
            SELECT thread_id, chat_name
            FROM chat_threads
        """)
    past_names = [row[1] for row in cursor.fetchall()]
    
    response = structured_llm.invoke(f"Give a small chat name for the chat based on the conversation: {state['messages']}, other than titles of previous chats : {past_names}")
    
    chat_name = response.name
    thread_id = config["configurable"]["thread_id"]
    
    cursor.execute("""
        INSERT OR REPLACE INTO chat_threads
        (thread_id, chat_name)
        VALUES (?, ?)
    """, (str(thread_id), chat_name))

    conn.commit()
    
    return {"name":chat_name}


#------------------------chatbot----------------------------

def chat_node(state : ChatState,config = None):
    
    """LLM node that may answer or request a tool call."""
   
    thread_id = None
    if config and isinstance(config, dict):
        thread_id = config.get("configurable", {}).get("thread_id")

    system_message = SystemMessage(
        content=(
            "You are a helpful assistant. For questions about the uploaded PDF, call "
            "the `rag_tool` and include the thread_id "
            f"`{thread_id}`. You can also use the web search, stock price, and "
            "calculator tools when helpful. If no document is available, ask the user "
            "to upload a PDF."
        )
    )

    messages = [system_message, *state["messages"]]
    response = llm_with_tools.invoke(messages, config=config)
    return {"messages": [response]}

# def name_condition(state: ChatState)->Literal['name_node','chat_node']:
    
#     if len(state['messages'])<3:
#         return 'name_node'
#     else:
#         return 'chat_node'

tool_node = ToolNode(tools)



#------------check pointer--------------------
# checkpointer = MemorySaver()
checkpointer = SqliteSaver(conn = conn)

graph = StateGraph(ChatState)

graph.add_node("chat_node",chat_node)
graph.add_node("tools", tool_node)

graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools',"chat_node")


chatbot = graph.compile(checkpointer = checkpointer)

#-------namebot---------------------
name_checkpointer = MemorySaver()
name_graph = StateGraph(NameState)

name_graph.add_node("name_node",name_node)

name_graph.add_edge(START,"name_node")
name_graph.add_edge("name_node",END)

namebot = name_graph.compile(checkpointer = name_checkpointer)





def retrieve_all_threads():
    
    all_threads = {
        checkpoint.config['configurable']['thread_id']
        for checkpoint in checkpointer.list(None)
    }

    if not all_threads:
        return {}

    placeholders = ",".join("?" for _ in all_threads)

    cursor.execute(
        f"""
        SELECT thread_id, chat_name
        FROM chat_threads
        WHERE thread_id IN ({placeholders})
        """,
        tuple(all_threads)
    )

    return dict(cursor.fetchall())

def get_name(thread_id):
    
    cursor.execute("""
        SELECT chat_name
        FROM chat_threads
        WHERE thread_id = ?
    """, (thread_id,))

    result = cursor.fetchone()
    # print(result)
    return result[0] if result else None

def thread_has_document(thread_id: str) -> bool:
    return str(thread_id) in _THREAD_RETRIEVERS


def thread_document_metadata(thread_id: str) -> dict:
    return _THREAD_METADATA.get(str(thread_id), {})

if __name__ == '__main__':

    CONFIG = {'configurable' : {'thread_id' : 'thread_4'}}
    
    # thread_id = '1'
    # while True:
        
    #     user_message = input('Typed here: ')
        
    #     print("User: ",user_message)
        
    #     if user_message.strip().lower() in ["end","exit","quit","bye"]:
    #         break
        
    #     config = {'configurable' : {'thread_id' : thread_id}}
        
    #     response = chatbot.invoke({'messages': [HumanMessage(content=user_message)]}, config=config)
        
    #     history = response['messages']
    #     print("AI: ",response['messages'][-1].content[0]['text'])
        
    # response =chatbot.invoke(
    #     {"messages": [HumanMessage(content="Hey, did i greet you?")]},
    #     config=CONFIG
    # )
    # response = namebot.invoke(
    #             {"messages":"Hey add some random numbers"},
    #             config=CONFIG
    #             )
    response = retrieve_all_threads()
    print(response)
    