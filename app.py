import streamlit as st
import os
import time
from back_end import DEBATERS, generate_debate, handle_follow_up_question

# Set page configuration (must be the first Streamlit command)
st.set_page_config(
    page_title="Debate Simulator",
    page_icon="🎭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    .debate-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px;
    }
    .debater {
        border-left: 5px solid;
        padding: 15px;
        border-radius: 5px;
        margin-bottom: 15px;
    }
    .Sam-Altman {
        border-left-color: #0066cc;
    }
    .Elon-Musk {
        border-left-color: #ff8c00;
    }
    .Mark-Zuckerberg {
        border-left-color: #4CAF50;
    }
    .Demis-Hassabis {
        border-left-color: #9C27B0;
    }
    .round-header {
        background-color: #343a40;
        color: white;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 15px;
        text-align: center;
    }
    .main-title {
        text-align: center;
        margin-bottom: 30px;
    }
    .source-expander {
        background-color: #f0f0f0;
        border-radius: 5px;
        padding: 10px;
        margin-top: 5px;
        margin-bottom: 10px;
        border-left: 3px solid #9C27B0;
    }
    .source-content {
        font-size: 0.9em;
        color: #555;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state variables
if "debate_state" not in st.session_state:
    st.session_state.debate_state = None
if "debate_completed" not in st.session_state:
    st.session_state.debate_completed = False
if "follow_up_question" not in st.session_state:
    st.session_state.follow_up_question = ""
if "selected_responders" not in st.session_state:
    st.session_state.selected_responders = []
if "process_follow_up" not in st.session_state:
    st.session_state.process_follow_up = False

# App title and description
st.markdown("<h1 class='main-title'>🎭 AI Debate Simulator</h1>", unsafe_allow_html=True)
st.markdown("""
This app simulates a debate between selected tech leaders on a topic of your choice.
Select 2-4 debaters, set the number of rounds, and enter a debate topic to get started.
""")

# UI for selecting debaters
st.subheader("Select Debaters (2-4)")
selected_debaters = st.multiselect(
    "Choose 2-4 debaters to participate",
    options=list(DEBATERS.keys()),
    default=list(DEBATERS.keys())[:2],
    help="Select between 2 and 4 debaters to participate in the debate"
)

# Show descriptions of selected debaters
if selected_debaters:
    st.write("Selected Debaters:")
    cols = st.columns(len(selected_debaters))
    for i, debater in enumerate(selected_debaters):
        with cols[i]:
            st.markdown(f"**{debater}**")
            st.caption(DEBATERS[debater]["description"])

# Validate number of debaters
if len(selected_debaters) < 2:
    st.warning("Please select at least 2 debaters.")
elif len(selected_debaters) > 4:
    st.warning("Please select no more than 4 debaters.")

# Number of rounds
num_rounds = st.slider("Number of debate rounds", min_value=1, max_value=5, value=3)

# Debate topic
debate_topic = st.text_input("Enter debate topic", "The future of artificial intelligence")

# Create a placeholder for the debate content
debate_placeholder = st.empty()

# Determine button text based on state
button_text = "Start New Debate" if st.session_state.debate_state is not None else "Start Debate"

# Process follow-up if flag is set
if st.session_state.process_follow_up:
    with st.spinner("Processing follow-up question..."):
        # Get the question and responders from session state
        question = st.session_state.follow_up_question
        responders = st.session_state.selected_responders

        if question and responders:
            # Update the debate state with the user's question and the responses
            st.session_state.debate_state = handle_follow_up_question(
                st.session_state.debate_state,
                question,
                responders
            )

            # Clear the inputs after processing
            st.session_state.follow_up_question = ""
            st.session_state.selected_responders = []

        # Reset the processing flag
        st.session_state.process_follow_up = False

# Run the debate when the user clicks the button
if st.button(button_text, type="primary", disabled=len(selected_debaters) < 2 or len(selected_debaters) > 4, key="main_debate_button"):
    if st.session_state.debate_state is not None:
        # Reset the debate if we already have one
        st.session_state.debate_state = None
        st.session_state.debate_completed = False
        st.session_state.follow_up_question = ""
        st.session_state.selected_responders = []
        st.session_state.process_follow_up = False
        st.rerun()
    else:
        # Show a progress bar for better UX
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            status_text.text("Initializing debate...")
            progress_bar.progress(10)
            time.sleep(0.5)

            # Initialize QA engine for knowledge retrieval
            status_text.text("Retrieving knowledge from database...")
            progress_bar.progress(30)

            # Create and run the real debate
            status_text.text("Generating debate content...")
            final_state = generate_debate(
                topic=debate_topic,
                debaters=selected_debaters,
                num_rounds=num_rounds
            )

            # Store the debate state in session state
            st.session_state.debate_state = final_state
            st.session_state.debate_completed = True

            progress_bar.progress(90)
            time.sleep(0.5)

            # Complete
            status_text.text("Debate generation complete!")
            progress_bar.progress(100)
            time.sleep(1)

            # Clear the progress indicators
            progress_bar.empty()
            status_text.empty()

        except Exception as e:
            st.error(f"An error occurred: {str(e)}")
            st.error("Please make sure you've set up your Google API key correctly and that you have access to the Gemini API.")

# Display the debate if it exists
if st.session_state.debate_state is not None:
    # Debate content (persistent)
    st.markdown(f"<h2 style='text-align: center;'>Debate on: {st.session_state.debate_state['topic']}</h2>", unsafe_allow_html=True)

    # Display each round of the debate
    for round_num, exchange in enumerate(st.session_state.debate_state['history'], 1):
        if round_num > st.session_state.debate_state['max_rounds']:
            continue

        st.markdown(f"<div class='round-header'><h3>Round {round_num}</h3></div>", unsafe_allow_html=True)

        # Display each debater's argument in this round
        for debater in st.session_state.debate_state['debaters']:
            debater_class = debater.replace(" ", "-")
            if debater in exchange and exchange[debater]:
                st.markdown(f"<div class='debater {debater_class}'><strong>{debater}:</strong> {exchange[debater]}</div>", unsafe_allow_html=True)

                # Display sources if available
                if 'sources' in st.session_state.debate_state and debater in st.session_state.debate_state['sources'] and round_num in st.session_state.debate_state['sources'][debater]:
                    sources = st.session_state.debate_state['sources'][debater][round_num]
                    if sources:
                        with st.expander(f"View sources for {debater}'s argument"):
                            for i, source in enumerate(sources):
                                st.markdown(f"**Source {i+1}:** {source['source']}")
                                st.markdown(f"**Content:** {source['content']}")
                                st.markdown("---")
            else:
                fallback = f"As {debater}, I believe this topic requires careful consideration."
                st.markdown(f"<div class='debater {debater_class}'><strong>{debater}:</strong> {fallback}</div>", unsafe_allow_html=True)

    # Display user follow-up questions and responses
    if st.session_state.debate_state['user_questions']:
        st.markdown(f"<div class='round-header'><h3>Follow-up Discussion</h3></div>", unsafe_allow_html=True)

        for q_data in st.session_state.debate_state['user_questions']:
            # Display user question
            st.markdown(f"<div class='debater User'><strong>User:</strong> {q_data['question']}</div>", unsafe_allow_html=True)

            # Display all debater responses
            for response_data in q_data['responses']:
                responder = response_data['responder']
                responder_class = responder.replace(" ", "-")
                st.markdown(f"<div class='debater {responder_class}'><strong>{responder}:</strong> {response_data['response']}</div>", unsafe_allow_html=True)

                # Display sources if available
                if 'sources' in response_data and response_data['sources']:
                    with st.expander(f"View sources for {responder}'s response"):
                        for i, source in enumerate(response_data['sources']):
                            st.markdown(f"**Source {i+1}:** {source['source']}")
                            st.markdown(f"**Content:** {source['content']}")
                            st.markdown("---")

# Add follow-up question section if debate is completed (separate from debate content)
if st.session_state.debate_completed and st.session_state.debate_state is not None:
    st.markdown("### Join the Conversation")

    # Create a form for the follow-up question
    with st.form(key="follow_up_form"):
        # User question input
        question = st.text_area("Ask a follow-up question:")

        # Select which debaters to respond
        responders = st.multiselect(
            "Select who should respond:",
            options=st.session_state.debate_state['debaters'],
            default=[st.session_state.debate_state['debaters'][0]]
        )

        # Submit button
        submitted = st.form_submit_button("Submit Question")

        if submitted:
            if question and responders:
                # Store the values in session state
                st.session_state.follow_up_question = question
                st.session_state.selected_responders = responders
                st.session_state.process_follow_up = True
                st.rerun()
            elif not question:
                st.warning("Please enter a question before submitting.")
            else:
                st.warning("Please select at least one debater to respond.")

# Instructions for setting up API key
with st.sidebar:

    st.markdown("### How It Works")
    st.markdown("""
    1. Select 2-4 debaters to participate
    2. Set the number of debate rounds (1-5)
    3. Enter a debate topic
    4. Click "Start Debate" to generate the debate
    5. After the debate, ask follow-up questions to any debater

    The app uses LangGraph to orchestrate the debate with separate nodes for each debater. Each debater has their own specialized node in the graph, allowing for independent reasoning and knowledge retrieval from their personalized knowledge bases.

    The system retrieves relevant information from the Pinecone database for each debater, ensuring that their arguments are grounded in their actual statements, positions, and knowledge.

    The human-in-the-loop feature lets you join the conversation after the initial debate concludes.
    """)
