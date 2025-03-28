import streamlit as st
from main import GroupDebateQA
from prompt import prompt_sam, debater_prompts
from back_end import DEBATERS
from utils import check_password, save_feedback

# Setup sidebar with instructions and feedback form
def setup_sidebar():
    """Setup the sidebar with instructions and feedback form."""
    st.sidebar.header("💬 Group Debate Chatbot")
    st.sidebar.markdown(
        "This chatbot uses Pinecone vector database to retrieve relevant information about group debates. "
        "Select a debater and ask questions to get responses based on their knowledge and perspective."
    )

    st.sidebar.write("### Instructions")
    st.sidebar.markdown(
        "1. Enter password to access the app  \n"
        "2. Select a debater to answer your questions  \n"
        "3. Ask questions about the group debates  \n"
        "4. View sources to verify the information"
    )

    # Add debater selection
    st.sidebar.subheader("Select Debater")
    debater_options = list(DEBATERS.keys())
    selected_debater = st.sidebar.selectbox(
        "Choose a debater to answer your questions",
        options=debater_options,
        index=debater_options.index(st.session_state["selected_debater"]) if st.session_state["selected_debater"] in debater_options else 0
    )

    # Update session state when debater changes
    if selected_debater != st.session_state["selected_debater"]:
        st.session_state["selected_debater"] = selected_debater
        st.rerun()

    # Show description of selected debater
    st.sidebar.markdown(f"**{selected_debater}**")
    st.sidebar.caption(DEBATERS[selected_debater]["description"])

    # Add controls for search parameters
    st.sidebar.subheader("Search Settings")
    # Store the k_value in session state so it persists between reruns
    if "k_value" not in st.session_state:
        st.session_state["k_value"] = 5

    k_value = st.sidebar.slider(
        "Number of documents to retrieve", 
        min_value=1, 
        max_value=10, 
        value=st.session_state["k_value"],
        key="k_slider"
    )

    # Update session state when slider changes
    if k_value != st.session_state["k_value"]:
        st.session_state["k_value"] = k_value

    # Add reset button
    if st.sidebar.button("Reset Conversation"):
        st.session_state["messages"] = []
        st.rerun()

    st.sidebar.write("### 🌎 Visit my AI Agent Projects Website")
    st.sidebar.markdown(
        "[Terresa Pan's Agent Garden Link](https://ai-agents-garden.lovable.app/)"
    )

    # Feedback section
    if 'feedback' not in st.session_state:
        st.session_state["feedback"] = ""

    st.sidebar.markdown("---")
    st.sidebar.subheader("💭 Feedback")
    feedback = st.sidebar.text_area(
        "Share your thoughts",
        value=st.session_state["feedback"],
        placeholder="Your feedback helps us improve..."
    )

    if st.sidebar.button("📤 Submit Feedback"):
        if feedback:
            try:
                save_feedback(feedback)
                st.session_state["feedback"] = ""
                st.sidebar.success("✨ Thank you for your feedback!")
            except Exception as e:
                st.sidebar.error(f"❌ Error saving feedback: {str(e)}")
        else:
            st.sidebar.warning("⚠️ Please enter feedback before submitting")

    try:
        st.sidebar.image("assets/bot01.jpg", use_container_width=True)
    except:
        pass

def main():
    """Main application function."""
    # Set page configuration
    st.set_page_config(
        page_title="Group Debate Chatbot",
        page_icon="💬",
        layout="wide"
    )

    # Initialize session state for chat history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Initialize session state for selected debater
    if "selected_debater" not in st.session_state:
        st.session_state["selected_debater"] = "Sam Altman"

    # Initialize session state for feedback
    if "feedback" not in st.session_state:
        st.session_state["feedback"] = ""

    # Initialize session state for k_value
    if "k_value" not in st.session_state:
        st.session_state["k_value"] = 5

    setup_sidebar()

    if not check_password():
        st.stop()

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
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input for user query
    user_query = st.chat_input("Ask a question about the group debates...")

    # Handle user input
    if user_query:
        # Add user message to chat history
        st.session_state["messages"].append({"role": "user", "content": user_query})

        # Display user message
        with st.chat_message("user"):
            st.markdown(user_query)

        # Get response from QA engine
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                try:
                    # Get the selected debater
                    debater_name = st.session_state["selected_debater"]

                    # Get the namespace for the selected debater
                    namespace = DEBATERS[debater_name]["namespace"]

                    # First get search results from the appropriate namespace
                    k_value = st.session_state.get("k_value", 5)  # Get k value from session state
                    similar_docs = qa_engine.search_similar_documents(user_query, k=k_value, namespace=namespace)

                    # Get the appropriate prompt for the selected debater
                    system_prompt = debater_prompts.get(debater_name, prompt_sam)

                    # Use the custom context method for more reliable answers
                    response = qa_engine.ask_question_with_custom_context(
                        user_query, 
                        search_results=similar_docs, 
                        system_prompt=system_prompt,
                        debater_name=debater_name
                    )

                    # Format answer with sources
                    answer = response["answer"]
                    sources = response["sources"].strip()

                    # Display the answer
                    st.markdown(answer)

                    # Display sources in a more structured way
                    if sources:
                        with st.expander("View Sources"):
                            source_list = sources.split(", ")
                            for i, source in enumerate(source_list):
                                st.markdown(f"**Source {i+1}:** {source}")

                                # Find the corresponding document
                                for doc in similar_docs:
                                    if doc.metadata.get('source', 'Unknown') == source:
                                        st.markdown(f"**Content:** {doc.page_content}")
                                        st.markdown("---")
                                        break

                    # Add assistant message to chat history
                    formatted_response = answer
                    if sources:
                        formatted_response += f"\n\n**Sources:**\n{sources}"

                    st.session_state["messages"].append({"role": "assistant", "content": formatted_response})

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
                    st.session_state["messages"].append({"role": "assistant", "content": error_message})

if __name__ == "__main__":
    main()
