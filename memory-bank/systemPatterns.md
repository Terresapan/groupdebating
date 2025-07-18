# System Patterns

## System Architecture

- The project includes two main Streamlit applications: a Group Debate Chatbot and an AI Debate Simulator.
- The chatbot uses a Streamlit frontend (`app.py`) interacting with a backend QA engine (`main.py`).
- The QA engine uses Langchain to connect to Google Generative AI for embeddings and LLM capabilities, and Pinecone for vector storage and similarity search.
- The simulator uses LangGraph to orchestrate debates between multiple debaters.

## Key Technical Decisions

- Using Pinecone namespaces to store knowledge specific to each debater.
- Using distinct system prompts for each debater to guide the LLM's response generation.
- Loading API keys from Streamlit secrets.

## Design Patterns in Use

- The chatbot uses a question-answering pattern with a vector database for context retrieval.
- The simulator uses a stateful graph pattern (LangGraph) to manage the debate flow.

## Component Relationships

- `app.py` (Chatbot Frontend) <-> `main.py` (QA Engine) <-> Pinecone
- `streamlit_app.py` (Debate Simulator Frontend) <-> LangGraph <-> Pinecone
- `back_end.py` defines the `DEBATERS` dictionary used by both applications.
- `prompt.py` defines the system prompts used by both applications.
- `utils.py` provides utility functions for password checking and feedback submission.

## Critical Implementation Paths

- User query -> `app.py` -> `main.py` -> Pinecone -> LLM -> `app.py` -> User
- Debate start -> `streamlit_app.py` -> LangGraph -> Pinecone -> LLM -> `streamlit_app.py` -> User
