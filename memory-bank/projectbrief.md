# Project Brief

## Core Requirements

- Provide a conversational interface for users to ask questions about group debates.
- Allow users to select different "debaters" (personas) to answer questions.
- Ground debater responses in a knowledge base using a vector database.
- Include a separate application for simulating debates between multiple debaters.
- Implement password protection for application access.
- Provide a mechanism for users to submit feedback.

## Goals

- Enable users to explore information related to group debates from different perspectives.
- Showcase the use of vector databases and LLMs for building Q&A and simulation applications.
- Provide a platform for simulated debates between prominent tech figures.
- Gather user feedback for application improvement.

## Scope

- The project includes two main Streamlit applications: a Group Debate Chatbot and an AI Debate Simulator.
- The chatbot focuses on single-debater Q&A.
- The simulator focuses on multi-debater simulated debates using LangGraph.
- Knowledge is stored and retrieved from a Pinecone vector database, with separate namespaces for each debater.
- User authentication is handled via a simple password check.
- Feedback is saved to a Google Sheet.
