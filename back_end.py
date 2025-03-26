from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Literal, Union
import streamlit as st
import os

# Set API keys from Streamlit secrets
os.environ["GOOGLE_API_KEY"] = st.secrets["general"]["GOOGLE_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["tracing"]["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "debate-simulator"

# Constants
GEMINI_2_0_FLASH = "gemini-2.0-flash"

# Define the debaters with descriptions
DEBATERS = {
    "Sam Altman": "CEO of OpenAI, known for his leadership in AI development and ethics",
    "Elon Musk": "CEO of Tesla and SpaceX, known for his views on AI risks and technological innovation",
    "Mark Zuckerberg": "CEO of Meta, known for his focus on social media and the metaverse",
    "Demis Hassabis": "CEO of Google DeepMind, known for his expertise in AI research and development"
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

# Initialize Google Gemini API
def get_llm(api_key, model=GEMINI_2_0_FLASH, temperature=0):
    """Initialize and return the LLM based on the specified model."""    
    return ChatGoogleGenerativeAI(
        model=model,
        temperature=temperature,
        api_key=api_key
    )

# Create a debater node factory function to generate specific debater nodes
def create_debater_node(debater_name):
    """Create a node function for a specific debater."""
    
    def node_function(state: DebateState) -> DebateState:
        model = get_llm(os.environ["GOOGLE_API_KEY"])
        
        # Construct the prompt with character guidance
        prompt = f"""
        You are {debater_name}, participating in a debate on the topic: "{state['topic']}".
        
        This is round {state['current_round']} of {state['max_rounds']}.
        
        Character guidance for {debater_name}:
        - {DEBATERS[debater_name]}
        - Use the speaking style, mannerisms, and viewpoints that {debater_name} is known for
        - Reference relevant companies, projects, or initiatives that {debater_name} is associated with
        - Make arguments that align with {debater_name}'s known positions
        - limit your response to 1-2 paragraphs maximum and within 100 words.
        
        Previous exchanges in this round:
        """
        
        # Add previous exchanges for the current round
        if state['current_round'] <= len(state['history']):
            for i, debater in enumerate(state['debaters']):
                if debater in state['history'][state['current_round'] - 1]:
                    prompt += f"\n{debater}: {state['history'][state['current_round'] - 1][debater]}"
        
        # Add previous rounds if applicable
        if state['current_round'] > 1:
            prompt += "\n\nPrevious rounds:"
            for round_idx in range(state['current_round'] - 1):
                if round_idx < len(state['history']):
                    prompt += f"\n\nRound {round_idx + 1}:"
                    for debater in state['debaters']:
                        if debater in state['history'][round_idx]:
                            prompt += f"\n{debater}: {state['history'][round_idx][debater]}"
        
        # Add instructions for the current speaker
        prompt += f"\n\nNow, as {debater_name}, provide your argument for this round. Be persuasive, use facts, and stay in character. Keep your response concise (1-2 paragraphs maximum)."
        
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
        "topic": topic,
        "debaters": debaters,
        "current_round": 1,
        "max_rounds": num_rounds,
        "history": [{}],
        "current_speaker_idx": 0,
        "user_questions": []
    }
    
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
        # Construct the prompt with context from the debate
        prompt = f"""
        You are {responder_name}, who just participated in a debate on the topic: "{state['topic']}".
        
        The debate history was:
        """
        
        # Add all debate rounds to the prompt
        for round_idx, round_data in enumerate(state['history']):
            if round_data:  # Skip empty rounds
                prompt += f"\n\nRound {round_idx + 1}:"
                for debater, response in round_data.items():
                    prompt += f"\n{debater}: {response}"
        
        # Add previous user questions if any
        if state['user_questions']:
            prompt += "\n\nPrevious follow-up questions and responses:"
            for q_data in state['user_questions']:
                prompt += f"\nUser: {q_data['question']}"
                for resp in q_data['responses']:
                    prompt += f"\n{resp['responder']}: {resp['response']}"
        
        # Add the current question
        prompt += f"\n\nA user has asked you a follow-up question: {question}"
        prompt += f"\n\nAs {responder_name}, respond to this question based on your character, knowledge, and the debate that just occurred. Keep your response concise (1-2 paragraphs maximum)."
        
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
            'response': response_text
        })
    
    # Add the complete question and responses to the state
    state['user_questions'].append(question_entry)
    
    return state


