import os
from langchain_openai import ChatOpenAI
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
import streamlit as st
from prompt import prompt_sam

# Set API keys from Streamlit secrets
os.environ["OPENAI_API_KEY"] = st.secrets["general"]["OPENAI_API_KEY"]
os.environ["PINECONE_API_KEY"] = st.secrets["general"]["PINECONE_API_KEY"]
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_API_KEY"] = st.secrets["tracing"]["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_PROJECT"] = "Group Debating"

class GroupDebateQA:
    def __init__(self, model_name='text-embedding-3-small', llm_model='gpt-4o-mini',
                 index_name="groupdebate-samaltman", namespace="groupdebate-samaltman"):
        """
        Initialize the GroupDebateQA class with model parameters.
        
        Args:
            model_name (str): Embedding model name
            llm_model (str): LLM model name
            index_name (str): Pinecone index name
            namespace (str): Pinecone namespace
        """
       
        # Initialize embedding model
        self.embeddings = OpenAIEmbeddings(
            model=model_name
        )
        
        # Initialize vector store
        self.vectorstore = PineconeVectorStore(
            index_name=index_name,
            embedding=self.embeddings,
            namespace=namespace
        )
        
        # Initialize LLM
        self.llm = ChatOpenAI(
            model_name=llm_model,
            temperature=0.0
        )
       
    def search_similar_documents(self, query, k=5):
        """
        Search for similar documents in the vector store.
        
        Args:
            query (str): Query to search for
            k (int): Number of documents to return
            
        Returns:
            list: List of similar documents
        """
        return self.vectorstore.similarity_search(query, k=k)
    
    def ask_question_with_custom_context(self, query, search_results, system_prompt=prompt_sam):
        """
        Ask a question using specific search results as context.
        For more direct control over the context provided to the LLM.
        
        Args:
            query (str): Question to ask
            search_results (list): Search results to use as context
            system_prompt (str): Optional system prompt to use
            
        Returns:
            dict: Answer and sources
        """
        
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