import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import streamlit as st
from prompt import prompt_sam, debater_prompts
from back_end import DEBATERS

# Set API keys from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["general"]["OPENAI_API_KEY"]
os.environ["GOOGLE_API_KEY"] = st.secrets["general"]["GOOGLE_API_KEY"]
os.environ["PINECONE_API_KEY"] = st.secrets["general"]["PINECONE_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["tracing"]["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Group Debating"

class GroupDebateQA:
    def __init__(self, model_name='models/text-embedding-004', llm_model='gemini-2.0-flash',
                 index_name="groupdebate", namespace=None):
        """
        Initialize the GroupDebateQA class with model parameters.
        
        Args:
            model_name (str): Embedding model name
            llm_model (str): LLM model name
            index_name (str): Pinecone index name
            namespace (str): Pinecone namespace (optional)
        """
       
        # Initialize embedding model
        self.embeddings = GoogleGenerativeAIEmbeddings(model=model_name)
        
        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(model=llm_model, temperature=0.0)
        
        # Store index name for later use
        self.index_name = index_name
        
        # Initialize vector store if namespace is provided
        if namespace:
            self.vectorstore = PineconeVectorStore(
                index_name=index_name,
                embedding=self.embeddings,
                namespace=namespace
            )
        else:
            self.vectorstore = None
            self.namespace = None
       
    def search_similar_documents(self, query, k=5, namespace=None):
        """
        Search for similar documents in the vector store.
        
        Args:
            query (str): Query to search for
            k (int): Number of documents to return
            namespace (str): Optional namespace to search in
            
        Returns:
            list: List of similar documents
        """
        # If a new namespace is provided, create a new vector store
        if namespace and (not self.vectorstore or namespace != self.namespace):
            self.vectorstore = PineconeVectorStore(
                index_name=self.index_name,
                embedding=self.embeddings,
                namespace=namespace
            )
            self.namespace = namespace
            
        if self.vectorstore:
            return self.vectorstore.similarity_search(query, k=k)
        else:
            raise ValueError("No vector store initialized. Please provide a namespace.")
    
    def ask_question_with_custom_context(self, query, search_results, system_prompt=prompt_sam, debater_name="Sam Altman"):
        """
        Ask a question using specific search results as context.
        For more direct control over the context provided to the LLM.
        
        Args:
            query (str): Question to ask
            search_results (list): Search results to use as context
            system_prompt (str): Optional system prompt to use
            debater_name (str): Name of the debater to use for the prompt
            
        Returns:
            dict: Answer and sources
        """
        # Use the appropriate prompt for the debater if available
        if debater_name in debater_prompts:
            system_prompt = debater_prompts[debater_name]
        
        # Extract content from search results
        contexts = [doc.page_content for doc in search_results]
        sources = [doc.metadata.get('source', 'Unknown') for doc in search_results]
        
        # Build a consolidated context string
        context_str = "\n\n".join([f"Context {i+1}:\n{context}" 
                                for i, context in enumerate(contexts)])
        
         # Create a direct message to the LLM
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context information:\n{context_str}\n\nQuestion: {query}"}
        ]
        
        # Directly use the ChatOpenAI model
        response = self.llm.invoke(messages)
        
        # Format the response to match the expected output structure
        return {
            "answer": response.content,
            "sources": ", ".join(set(sources))  # Deduplicated list of sources
        }
