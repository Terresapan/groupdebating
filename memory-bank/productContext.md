# Product Context

## Purpose

- To provide an interactive way to explore information from group debates.
- To offer two distinct applications: a chatbot for individual debater Q&A and a simulator for multi-debater debates.

## Problems Solved

- Eliminates the need to manually search through debate transcripts or documents.
- Provides a structured and conversational interface for accessing debate-related information.
- Offers different perspectives by allowing users to select specific debaters.
- Simulates debates between multiple tech leaders, providing insights into their potential interactions.

## How it Works

- The chatbot allows users to select a debater and ask questions, with answers retrieved from a vector database and potentially filtered or framed by the selected debater's "knowledge".
- The simulator uses LangGraph to orchestrate debates between multiple debaters, retrieving relevant information from Pinecone for each debater to ground their arguments.
- Both applications use Pinecone namespaces to store knowledge specific to each debater.
- The system uses distinct system prompts for each debater to guide the LLM's response generation.

## User Experience Goals

- Easy navigation and clear instructions.
- Intuitive debater selection.
- Well-structured presentation of debate content and sources.
- Engaging and informative simulated debates.
- Clear attribution of responses to specific debaters.
- Password protection for application access.
- A feedback submission feature.
