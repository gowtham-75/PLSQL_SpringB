from dotenv import load_dotenv
import os
from plsql_splitter import split_plsql_for_vectordb, PLSQLChunk
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables import RunnablePassthrough
from pathlib import Path
import chromadb

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-large")

llm = ChatOpenAI(model="gpt-4o-mini", 
                 temperature=0)

def load_plsql_file(file_path):
    """Load a PLSQL file and return its content."""
    with open(file_path, 'r') as f:
        return f.read()

def clean_metadata(metadata: dict) -> dict:
    """Clean metadata by removing None values and converting lists to strings."""
    cleaned = {}
    for key, value in metadata.items():
        if value is None or value == []:
            continue  # Skip None values and empty lists
        elif isinstance(value, list):
            cleaned[key] = ", ".join(str(v) for v in value)
        elif isinstance(value, (str, int, float, bool)):
            cleaned[key] = value
        else:
            cleaned[key] = str(value)
    return cleaned

def create_vectorstore(sql_directory: str):
    """Create vector store from SQL files."""
    # Create persistent client
    client = chromadb.PersistentClient(path="./chroma_db")
    
    # Create or get collection
    vectorstore = Chroma(
        client=client,
        collection_name="plsql_code",
        embedding_function=embeddings
    )
    
    # Process all SQL files
    for sql_file in Path(sql_directory).glob("**/*.sql"):
        chunks = split_plsql_for_vectordb(str(sql_file))
        
        for chunk in chunks:
            # Create searchable text that combines code and metadata
            searchable_text = f"""
            Type: {chunk.chunk_type}
            Name: {chunk.name}
            Package: {chunk.package_name or 'N/A'}
            Context: {chunk.context or 'N/A'}
            Dependencies: {', '.join(chunk.dependencies) if chunk.dependencies else 'N/A'}
            
            Code:
            {chunk.content}
            """
            
            # Clean metadata before storing
            metadata = clean_metadata({
                'type': chunk.chunk_type,
                'name': chunk.name,
                'package': chunk.package_name,
                'file_path': str(sql_file),
                'context': chunk.context,
                'signature': chunk.signature
            })
            
            # Only add if we have valid metadata
            if metadata:
                try:
                    vectorstore.add_texts(
                        texts=[searchable_text],
                        metadatas=[metadata]
                    )
                except ValueError as e:
                    print(f"Warning: Could not add chunk {chunk.name} due to: {str(e)}")
                    continue
    
    return vectorstore

def create_qa_chain(vectorstore):
    """Create QA chain for answering questions about the code."""
    # Create retriever
    retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
    
    # Create prompt template
    template = """Answer the following question about the PL/SQL code:
    Question: {question}
    
    Context from the codebase:
    {context}
    
    Please provide a detailed explanation.
    """
    
    prompt = ChatPromptTemplate.from_template(template)
    
    # Create the chain
    chain = (
        {"context": retriever, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )
    
    return chain

def explain_plsql_logic(chain, question: str):
    """Get explanation of PL/SQL logic."""
    try:
        response = chain.invoke(question)
        return response, []  # Empty list for source_documents as we're using the new chain structure
    except Exception as e:
        print(f"Error during explanation: {str(e)}")
        return "Sorry, I couldn't process that question.", []

def generate_spring_boot_code(chain, plsql_object: str):
    """Generate Spring Boot equivalent of PL/SQL code."""
    prompt = f"""
    Based on the PL/SQL implementation of {plsql_object}, generate equivalent Spring Boot code.
    Include:
    1. Entity classes
    2. Repository interfaces
    3. Service layer implementation
    4. Controller endpoints if applicable
    5. Any necessary DTOs
    Maintain the same business logic and validation rules.
    """
    
    try:
        return chain.invoke(prompt)
    except Exception as e:
        print(f"Error during code generation: {str(e)}")
        return "Sorry, I couldn't generate the Spring Boot code."

# Usage example
if __name__ == "__main__":
    try:
        # Create vector store from SQL files
        vectorstore = create_vectorstore("./code/")
        
        # Create chain
        chain = create_qa_chain(vectorstore)
        
        # Example: Explain logic
        explanation, sources = explain_plsql_logic(
            chain,
            "Explain how order processing works in the system"
        )
        print("Explanation:", explanation)
        
        # Example: Generate Spring Boot code
        spring_code = generate_spring_boot_code(
            chain,
            "PKG_ORDER_PROCESSING.PROCESS_ORDER"
        )
        print("\nSpring Boot Implementation:", spring_code)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    


