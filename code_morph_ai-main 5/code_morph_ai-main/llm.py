import openai
import streamlit as st
import os
from dotenv import load_dotenv
import requests

# Load environment variables
load_dotenv()

# Define the prompt
prompt = "Who is the prime minister?"

def llm(prompt):
    
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": os.environ["AZURE_OPENAI_API_KEY"]
        }
        data = {
            "model": os.environ["MODEL_NAME"],
            "messages": [
                {"role": "system", "content": "Answer the user's questions based on the extracted text."},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(f"{os.environ["AZURE_OPENAI_ENDPOINT"]}/openai/deployments/{os.environ['DEPLOYMENT_NAME']}/chat/completions?api-version=2024-09-01-preview",
                                 headers=headers, 
                                 json=data
                                 )
        
        response.raise_for_status()
        
        result = response.json()
        st.success("Analysis Complete!")

        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error calling GPT model: {e}")
        return None
    
st.write(llm(prompt))

