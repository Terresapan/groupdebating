import streamlit as st
from main import GroupDebateQA
from prompt import prompt_sam

# Set page configuration
st.set_page_config(
    page_title="Group Debate Chatbot",
    page_icon="💬",
    layout="wide"
)

# Initialize session state for chat history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Add a title to the app
st.title("Group Debate Chatbot")
st.subheader("Ask questions about the group debates")

# Initialize the QA engine
@st.cache_resource
def initialize_qa_engine():
    return GroupDebateQA()

try:
    qa_engine = initialize_qa_engine()
    st.success("✅ Successfully connected to Pinecone and OpenAI!")
except Exception as e:
    st.error(f"❌ Error initializing the QA engine: {str(e)}")
    st.stop()

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input for user query
user_query = st.chat_input("Ask a question about the group debates...")

# Handle user input
if user_query:
    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Display user message
    with st.chat_message("user"):
        st.markdown(user_query)

    # Get response from QA engine
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                # First get search results
                k_value = st.session_state.get("k_value", 5)  # Get k value from session state
                similar_docs = qa_engine.search_similar_documents(user_query, k=k_value)
                
                # Use the custom context method for more reliable answers
                response = qa_engine.ask_question_with_custom_context(
                    user_query, 
                    search_results=similar_docs, 
                    system_prompt=prompt_sam
                )
                
                # Format answer with sources
                answer = response["answer"]
                sources = response["sources"].strip()
                
                if sources:
                    formatted_response = f"{answer}\n\n**Sources:**\n{sources}"
                else:
                    formatted_response = answer
                
                st.markdown(formatted_response)
                
                # Add assistant message to chat history
                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                
                # Show similar documents in an expander
                with st.expander("View similar documents"):
                    for i, doc in enumerate(similar_docs):
                        st.markdown(f"**Document {i+1}**")
                        st.markdown(f"**Content:** {doc.page_content}")
                        st.markdown(f"**Source:** {doc.metadata.get('source', 'Unknown')}")
                        st.markdown("---")
            
            except Exception as e:
                error_message = f"❌ Error generating response: {str(e)}"
                st.error(error_message)
                st.session_state.messages.append({"role": "assistant", "content": error_message})

# Add sidebar with information
with st.sidebar:
    st.title("About")
    st.markdown("""
    This chatbot uses Pinecone vector database to retrieve relevant information about group debates.
    
    Ask questions like:
    - What was discussed in the fireside chat at Harvard University?
    - What are Sam Altman's views on AI safety?
    - What were the key topics in recent debates?
    """)
    
    # Add controls for search parameters
    st.subheader("Search Settings")
    # Store the k_value in session state so it persists between reruns
    if "k_value" not in st.session_state:
        st.session_state.k_value = 5
    
    k_value = st.slider(
        "Number of documents to retrieve", 
        min_value=1, 
        max_value=10, 
        value=st.session_state.k_value,
        key="k_slider"
    )
    
    # Update session state when slider changes
    if k_value != st.session_state.k_value:
        st.session_state.k_value = k_value
    
    # Add reset button
    if st.button("Reset Conversation"):
        st.session_state.messages = []
        st.rerun()