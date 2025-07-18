# Tech Context

## Technologies Used

- Streamlit: For building the user interface of both the chatbot and the debate simulator.
- Langchain: For building the question-answering chains and interacting with LLMs and vector databases.
- LangGraph: For orchestrating the debate flow in the debate simulator.
- Google Generative AI: For LLM capabilities (text generation) and embeddings.
- Pinecone: For vector storage and similarity search.
- gspread and oauth2client: For interacting with Google Sheets to store feedback.
- hmac: For secure password comparison.

## Development Setup

- The project uses Streamlit secrets to store API keys and other sensitive information.
- The `requirements.txt` file lists the project's dependencies.

## Technical Constraints

- The project relies on external services like OpenAI/Google Generative AI and Pinecone, which may have usage limits or cost implications.
- The accuracy and relevance of the responses depend on the quality of the data in the Pinecone vector database.
- The performance of the debate simulator may be limited by the complexity of the LangGraph workflow and the speed of the LLM.

## Dependencies

- streamlit
- gsheets-connection
- gspread
- oauth2client
- langchain
- langgraph
- langsmith
- langchain_openai
- langchain-google-genai
- langchain-community
- langchain_pinecone

## Tool Usage Patterns

- `streamlit`: Used for creating the user interface and handling user input.
- `langchain`: Used for building the question-answering chains and interacting with LLMs and vector databases.
- `langgraph`: Used for orchestrating the debate flow in the debate simulator.
- `Google Generative AI`: Used for generating embeddings and text responses.
- `Pinecone`: Used for storing and retrieving knowledge vectors.
- `gspread`: Used for saving user feedback to a Google Sheet.
