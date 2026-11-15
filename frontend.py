import streamlit as st 
from backend import chatbot, ingest_pdf,retrieve_all_threads,namebot,thread_document_metadata
from langchain_core.messages import HumanMessage,AIMessage, ToolMessage
import uuid




#---------------------utility functions-------------------------

def generate_thread_id():
    thread_id = uuid.uuid4()
    # st.session_state['chats'][thread_id] = st.session_state['count']
    # st.session_state['count']+=1
    return thread_id

def reset_chat():
    thread_id = generate_thread_id()
    st.session_state['thread_id'] = thread_id 
    add_thread(st.session_state['thread_id'])
    st.session_state['message_hist'] = []

def add_thread(thread_id):
    if thread_id not in  st.session_state['chat_threads']:
        st.session_state['chat_threads'][thread_id] = f'new chat {len(st.session_state['chat_threads'])+1}'
        
def load_conversation(thread_id):
    state = chatbot.get_state(config={'configurable' : {'thread_id' : thread_id}}).values
    if state:
        messages = state['messages']
    else:
        messages = []
    return messages

#-------------Session state --------------------
if 'message_hist' not in st.session_state:
    st.session_state['message_hist'] = []


# if 'count' not in  st.session_state:
#     st.session_state['count'] = 1
if 'thread_id' not in  st.session_state:
    st.session_state['thread_id'] = generate_thread_id()

if 'chat_threads' not in  st.session_state:
    st.session_state['chat_threads'] = retrieve_all_threads()

if "ingested_docs" not in st.session_state:
    st.session_state["ingested_docs"] = {}


add_thread(st.session_state['thread_id'])
  
thread_key = str(st.session_state["thread_id"])
thread_docs = st.session_state["ingested_docs"].setdefault(thread_key, {})
threads = list(st.session_state["chat_threads"].keys())[::-1]
selected_thread = None



#-------------------Side bar-------------------------

st.sidebar.title('Chatbot')

if st.sidebar.button('New Chat'):
    reset_chat()

if thread_docs:
    latest_doc = list(thread_docs.values())[-1]
    st.sidebar.success(
        f"Using `{latest_doc.get('filename')}` "
        f"({latest_doc.get('chunks')} chunks from {latest_doc.get('documents')} pages)"
    )
else:
    st.sidebar.info("No PDF indexed yet.")
    
uploaded_pdf = st.sidebar.file_uploader("Upload a PDF for this chat", type=["pdf"])
if uploaded_pdf:
    if uploaded_pdf.name in thread_docs:
        st.sidebar.info(f"`{uploaded_pdf.name}` already processed for this chat.")
    else:
        with st.sidebar.status("Indexing PDF…", expanded=True) as status_box:
            summary = ingest_pdf(
                uploaded_pdf.getvalue(),
                thread_id=thread_key,
                filename=uploaded_pdf.name,
            )
            thread_docs[uploaded_pdf.name] = summary
            status_box.update(label="✅ PDF indexed", state="complete", expanded=False)


st.sidebar.header('My Conversation')

if not threads:
    st.sidebar.write("No past conversations yet.")

for thread_id in reversed(st.session_state['chat_threads'].keys()):
    if st.sidebar.button(st.session_state['chat_threads'][thread_id]):
        st.session_state['thread_id'] = thread_id
        loaded_messages = load_conversation(thread_id)

        temp_messages = []
        
        for msg in loaded_messages:
            if isinstance(msg,HumanMessage):
                role = "Human"
                temp_messages.append({'role':role, 'content':msg.content})
            else:
                role = "assistant"
                temp_messages.append({'role':role, 'content':msg.content[0]['text'] if msg.content else ""})
        
        st.session_state['message_hist'] = (temp_messages)
                



#---------------- Messages --------------------------

messages = st.session_state['message_hist']

for message in st.session_state['message_hist']:
    with st.chat_message(message['role']):
        st.write(message['content'])

#---------------- Chat Interface --------------------------


user_message = st.chat_input("Type your message here...")

if user_message:
    
    messages.append({'role':'user','content':user_message})
    with st.chat_message("user"):
        st.write(user_message)
    
    
    
    # response = chatbot.stream(
    #     {'messages': [HumanMessage(content=user_message)]}, 
    #     stream_mode="messages",
    #     config=CONFIG)
    
    
    
    # messages.append({'role':'assistant','content':ai_message})
    CONFIG = {
        'configurable' : {'thread_id' : st.session_state['thread_id']},
        'run_name' : 'chat'
    }

    f = False
    with st.chat_message("assistant"):

        

        if st.session_state['chat_threads'][st.session_state['thread_id']].startswith('new chat') and len(st.session_state['message_hist'])<3:
                    
            response = namebot.invoke(
                {"messages": messages},
                config=CONFIG
                )
            # name = get_name(st.session_state['thread_id'])
            # print(response["name"])
            st.session_state['chat_threads'][st.session_state['thread_id']] = response['name'] if response else ""
            f = True

        status_holder = {"box": None}

        def ai_only_stream():
            for message_chunk, metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_message)]}, 
            stream_mode="messages",
            config=CONFIG
            ): 
                if isinstance(message_chunk, ToolMessage):
                    tool_name = getattr(message_chunk, "name", "tool")
                    if status_holder["box"] is None:
                        status_holder["box"] = st.status(
                            f"🔧 Using `{tool_name}` …", expanded=True
                        )
                    else:
                        status_holder["box"].update(
                            label=f"🔧 Using `{tool_name}` …",
                            state="running",
                            expanded=True,
                        )

                if isinstance(message_chunk,AIMessage) and message_chunk.content:

                    yield message_chunk.content[0]['text']




        ai_message = st.write_stream(
            ai_only_stream()
        )

        if status_holder["box"] is not None:
            status_holder["box"].update(
                label="✅ Tool finished", state="complete", expanded=False
            )
        
        
    messages.append({'role':'assistant','content':ai_message})
    
    doc_meta = thread_document_metadata(thread_key)
    if doc_meta:
        st.caption(
            f"Document indexed: {doc_meta.get('filename')} "
            f"(chunks: {doc_meta.get('chunks')}, pages: {doc_meta.get('documents')})"
        )
      
    if f:
        st.rerun()
        f = False
        
# st.divider()

if selected_thread:
    st.session_state["thread_id"] = selected_thread
    messages = load_conversation(selected_thread)

    temp_messages = []
    for msg in messages:
        role = "user" if isinstance(msg, HumanMessage) else "assistant"
        temp_messages.append({"role": role, "content": msg.content})
    st.session_state["message_history"] = temp_messages
    st.session_state["ingested_docs"].setdefault(str(selected_thread), {})
    st.rerun()
# st.sidebar.write('new chat' in st.session_state['chat_threads'][st.session_state['thread_id']] , len(st.session_state['message_hist'])<3)   
    
        
        
