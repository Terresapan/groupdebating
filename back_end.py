from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Literal, Union
import streamlit as st
import os
from prompt import debater_prompts

# Set API keys from Streamlit secrets
os.environ["GOOGLE_API_KEY"] = st.secrets["general"]["GOOGLE_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["tracing"]["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "debate-simulator"

# Constants
GEMINI_2_0_FLASH = "gemini-2.0-flash"
EMBEDDING_MODEL = "models/text-embedding-004"
INDEX_NAME = "groupdebate"

# Define the debaters with descriptions and their corresponding namespaces
DEBATERS = {
    "Sam Altman": {
        'description': "CEO of OpenAI, known for his leadership in AI development and ethics",
        'namespace': "samaltman"
    },
    "Elon Musk": {
        'description': "CEO of Tesla and SpaceX, known for his views on AI risks and technological innovation",
        'namespace': "elonmusk"
    },
    "Mark Zuckerberg": {
        'description': "CEO of Meta, known for his focus on social media and the metaverse",
        'namespace': "markzuckerberg"
    },
    "Demis Hassabis": {
        'description': "CEO of Google DeepMind, known for his expertise in AI research and development",
        'namespace': "demishassabis"
    }
}

# Define the state schema for the debate
class DebateState(TypedDict):
    topic: str
    debaters: List[str]
    current_round: int
    max_rounds: int
    history: List[Dict[str, str]]
    current_speaker_idx: int
    user_questions: List[Dict[str, str]]  # To store user follow-up questions and responses
    knowledge_context: Dict[str, List[Dict]]  # To store retrieved knowledge for each debater
    sources: Dict[str, Dict[int, List[Dict[str, str]]]]  # To store sources for each debater by round

# Initialize Google Gemini API
def get_llm(api_key, model=GEMINI_2_0_FLASH, temperature=0):
    """Initialize and return the LLM based on the specified model."""    
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )

# Initialize embeddings model
def get_embeddings(api_key):
    """Initialize and return the embeddings model."""
    return GoogleGenerativeAIEmbeddings(
        model=EMBEDDING_MODEL,
        api_key=api_key
    )

# Retrieve knowledge from Pinecone for a specific debater
def retrieve_knowledge(topic, debater_name, k=5):
    """Retrieve relevant knowledge for a debater on the given topic."""
    try:
        # Get the namespace for the debater
        namespace = DEBATERS[debater_name]['namespace']

        # Initialize embeddings
        embeddings = get_embeddings(os.environ["GOOGLE_API_KEY"])

        # Initialize vector store with the appropriate namespace
        vectorstore = PineconeVectorStore(
            index_name=INDEX_NAME,
            embedding=embeddings,
            namespace=namespace
        )

        # Search for relevant documents
        docs = vectorstore.similarity_search(topic, k=k)

        # Extract content and metadata
        results = []
        for doc in docs:
            results.append({
                'content': doc.page_content,
                'source': doc.metadata.get('source', "Unknown")
            })

        return results
    except Exception as e:
        st.error(f"Error retrieving knowledge for {debater_name}: {str(e)}")
        return []

# Create a debater node factory function to generate specific debater nodes
def create_debater_node(debater_name):
    """Create a node function for a specific debater."""

    def node_function(state: DebateState) -> DebateState:
        model = get_llm(os.environ["GOOGLE_API_KEY"])

        # Retrieve knowledge for this debater if not already in state
        if 'knowledge_context' not in state or debater_name not in state['knowledge_context']:
            if 'knowledge_context' not in state:
                state['knowledge_context'] = {}

            # Retrieve knowledge from Pinecone
            state['knowledge_context'][debater_name] = retrieve_knowledge(state['topic'], debater_name)

        # Get the knowledge context for this debater
        knowledge = state['knowledge_context'].get(debater_name, [])
        
        # Track sources for this round
        if 'sources' not in state:
            state['sources'] = {}
        if debater_name not in state['sources']:
            state['sources'][debater_name] = {}
        
        # Store sources for the current round
        current_round_sources = []
        for item in knowledge:
            if 'source' in item:
                current_round_sources.append({
                    'content': item['content'],
                    'source': item['source']
                })
        
        # Add sources to the state
        state['sources'][debater_name][state['current_round']] = current_round_sources

        # Format knowledge context
        knowledge_context = ""
        if knowledge:
            knowledge_context = ""
            for i, item in enumerate(knowledge):
                knowledge_context += f"{i+1}. {item['content']}"

        # Get the character prompt from the debater_prompts dictionary
        character_prompt = debater_prompts.get(debater_name, "")

        # Construct the prompt with character guidance and knowledge context
        prompt = f"""
        You are {debater_name}, participating in a debate on the topic: "{state['topic']}".

        This is round {state['current_round']} of {state['max_rounds']}.

        Character guidance for {debater_name}:
        {character_prompt}
        - {DEBATERS[debater_name]['description']}
        - Use the speaking style, mannerisms, and viewpoints that {debater_name} is known for
        - Reference relevant companies, projects, or initiatives that {debater_name} is associated with
        - Make arguments that align with {debater_name}'s known positions
        - limit your response to 1-2 paragraphs maximum and within 100 words.
        {knowledge_context}

        Previous exchanges in this round:
        """

        # Add previous exchanges for the current round
        if state['current_round'] <= len(state['history']):
            for i, debater in enumerate(state['debaters']):
                if debater in state['history'][state['current_round'] - 1]:
                    prompt += f"{debater}: {state['history'][state['current_round'] - 1][debater]}"

        # Add previous rounds if applicable
        if state['current_round'] > 1:
            prompt += "Previous rounds:"
            for round_idx in range(state['current_round'] - 1):
                if round_idx < len(state['history']):
                    prompt += f"Round {round_idx + 1}:"
                    for debater in state['debaters']:
                        if debater in state['history'][round_idx]:
                            prompt += f"{debater}: {state['history'][round_idx][debater]}"

        # Add instructions for the current speaker
        prompt += f"Now, as {debater_name}, provide your argument for this round. Be persuasive, use facts, and stay in character. Keep your response concise (1-2 paragraphs maximum)."

        # Generate response with error handling
        try:
            response = model.invoke(prompt)
            response_text = response.content

            # Update state
            if state['current_round'] > len(state['history']):
                state['history'].append({debater_name: response_text})
            else:
                state['history'][state['current_round'] - 1][debater_name] = response_text

        except Exception:
            # Provide a fallback response
            fallback_text = f"As {debater_name}, I believe that {state['topic']} is a critical issue that requires careful consideration."

            if state['current_round'] > len(state['history']):
                state['history'].append({debater_name: fallback_text})
            else:
                state['history'][state['current_round'] - 1][debater_name] = fallback_text

        # Update the current speaker index
        state['current_speaker_idx'] = (state['current_speaker_idx'] + 1) % len(state['debaters'])

        # If we've gone through all speakers for this round, increment the round
        if state['current_speaker_idx'] == 0:
            state['current_round'] += 1

        return state

    return node_function

# Router function to determine which debater should speak next
def router(state: DebateState) -> Union[Literal["end"], str]:
    # Check if debate is complete
    if state['current_round'] > state['max_rounds']:
        return "end"

    # Get the next speaker
    next_speaker = state['debaters'][state['current_speaker_idx']]
    return next_speaker

# Create the debate graph with individual nodes for each debater
def create_debate_graph(debaters):
    workflow = StateGraph(DebateState)

    # Add a node for each debater
    for debater in debaters:
        workflow.add_node(debater, create_debater_node(debater))

    # Add a router node
    workflow.add_node("router", lambda state: state)

    # Connect each debater to the router
    for debater in debaters:
        workflow.add_edge(debater, "router")

    # Add conditional edges from router to appropriate debater or END
    workflow.add_conditional_edges(
        "router",
        router,
        {
            "end": END,
            **{debater: debater for debater in debaters}
        }
    )

    # Set the entry point to the router
    workflow.set_entry_point("router")

    return workflow.compile()

# Function to generate a debate
def generate_debate(topic, debaters, num_rounds):
    # Initialize the state
    initial_state = {
        'topic': topic,
        'debaters': debaters,
        'current_round': 1,
        'max_rounds': num_rounds,
        'history': [{}],
        'current_speaker_idx': 0,
        'user_questions': [],
        'knowledge_context': {},
        'sources': {}
    }
    
    # Initialize sources dictionary for each debater
    for debater in debaters:
        initial_state['sources'][debater] = {}

    # Pre-fetch knowledge for all debaters
    for debater in debaters:
        initial_state['knowledge_context'][debater] = retrieve_knowledge(topic, debater)

    # Create and run the graph with individual debater nodes
    graph = create_debate_graph(debaters)
    final_state = graph.invoke(initial_state)

    return final_state

# Function to handle user follow-up questions
def handle_follow_up_question(state, question, responder_names):
    """Process a follow-up question from the user and get responses from the specified debaters."""
    model = get_llm(os.environ["GOOGLE_API_KEY"])

    # Add the question to the state first
    question_entry = {
        'question': question,
        'responses': []
    }

    # Get response from each selected debater
    for responder_name in responder_names:
        # Get the knowledge context for this debater
        knowledge = state['knowledge_context'].get(responder_name, [])

        # Retrieve additional knowledge specific to the question if needed
        question_knowledge = retrieve_knowledge(question, responder_name, k=3)

        # Combine existing knowledge with question-specific knowledge
        all_knowledge = knowledge + question_knowledge
        
        # Track sources for this follow-up question
        question_sources = []
        for item in all_knowledge:
            if 'source' in item:
                question_sources.append({
                    'content': item['content'],
                    'source': item['source']
                })

        # Format knowledge context
        knowledge_context = ""
        if all_knowledge:
            knowledge_context = "Relevant knowledge for your reference:"
            for i, item in enumerate(all_knowledge):
                knowledge_context += f"{i+1}. {item['content']}"
        # Get the character prompt from the debater_prompts dictionary
        character_prompt = debater_prompts.get(responder_name, "")

        # Construct the prompt with context from the debate and knowledge
        prompt = f"""
        You are {responder_name}, who just participated in a debate on the topic: "{state['topic']}".
        {character_prompt}

        The debate history was:
        """

        # Add all debate rounds to the prompt
        for round_idx, round_data in enumerate(state['history']):
            if round_data:  # Skip empty rounds
                prompt += f"Round {round_idx + 1}:"
                for debater, response in round_data.items():
                    prompt += f"{debater}: {response}"

        # Add previous user questions if any
        if state['user_questions']:
            prompt += "Previous follow-up questions and responses:"
            for q_data in state['user_questions']:
                prompt += f"User: {q_data['question']}"
                for resp in q_data['responses']:
                    prompt += f"{resp['responder']}: {resp['response']}"

        # Add the current question and knowledge context
        prompt += f"A user has asked you a follow-up question: {question}"
        prompt += knowledge_context
        prompt += f"As {responder_name}, respond to this question based on your character, knowledge, and the debate that just occurred. Keep your response concise (1-2 paragraphs maximum)."

        # Generate response with error handling
        try:
            response = model.invoke(prompt)
            response_text = response.content
        except Exception:
            # Provide a fallback response
            response_text = f"As {responder_name}, I appreciate your question but am unable to provide a detailed response at this time."

        # Add this response to the question entry
        question_entry['responses'].append({
            'responder': responder_name,
            'response': response_text,
            'sources': question_sources
        })

    # Add the complete question and responses to the state
    state['user_questions'].append(question_entry)

    return state
