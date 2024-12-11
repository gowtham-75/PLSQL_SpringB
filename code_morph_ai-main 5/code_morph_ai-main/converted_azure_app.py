from dotenv import load_dotenv
import streamlit as st
import os
import requests
from util import extract_code, get_code_prompt
from prompt_templates import code_explain_prompt, java_code_gen_prompt, oo_design_prompt
from langchain_core.prompts import PromptTemplate

_ = load_dotenv()

code_dir_name = "./code1"

def llm(prompt, model_name):
    """
    Generic LLM calling function that works with Azure OpenAI
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "api-key": os.environ["AZURE_OPENAI_API_KEY"]
        }
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "Answer the user's questions based on the extracted text."},
                {"role": "user", "content": prompt}
            ]
        }
        
        response = requests.post(
            f"{os.environ['AZURE_OPENAI_ENDPOINT']}/openai/deployments/{os.environ['DEPLOYMENT_NAME']}/chat/completions?api-version=2024-09-01-preview",
            headers=headers, 
            json=data
        )
        
        response.raise_for_status()
        result = response.json()
        return result['choices'][0]['message']['content']
    except Exception as e:
        st.error(f"Error calling GPT model: {e}")
        return None

# Extract code content
code_index, code_text, file_content = extract_code(code_dir_name)

# Initialize selected model
selected_model = None

st.title("/CodeMorph_AI")

# Sidebar styling
st.markdown(
    """
    <style>
        section[data-testid="stSidebar"] {
            width: 300px !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Sidebar content
with st.sidebar:
    st.title("/CodeMorph_AI")
    st.image("image/legacy_mod.jpeg", width=250)

    select_model = st.radio(
        "Select the Language Model",
        ("/openai_gpt_4o_mini",
         "/openai_gpt_4o",
         "/openai_o1_preview",
         "/openai_o1_mini",
         "/claude_3.5_sonnet")
    )

    # Map selection to model names
    model_mapping = {
        "/openai_gpt_4o_mini": "gpt-4o-mini",
        "/openai_gpt_4o": "gpt-4o",
        "/openai_o1_preview": "o1-preview",
        "/openai_o1_mini": "o1-mini",
        "/claude_3.5_sonnet": "claude-3-5-sonnet"
    }
    
    selected_model = model_mapping[select_model]
    st.write("Selected Language Model:", selected_model)

    add_radio = st.radio(
        "What can I do for you today?",
        ("/show_code",
         "/command_interface",
         "/explain",
         "/generate_oo_design",
         "/generate_java_code")
    )

def execute(model_name, exec_prompt, code):
    """
    Execute LLM with provided prompt template
    """
    final_prompt = PromptTemplate.from_template(exec_prompt)
    formatted_prompt = final_prompt.format(PLSQL_CODE=code)
    return llm(formatted_prompt, model_name)

# Main content based on selection
if add_radio == "/show_code":
    st.title("/show_code")
    st.write("Here is the index of the files in the codebase:")
    st.write(code_index)
    st.write("Here is the entire codebase:")
    st.code(code_text)

elif add_radio == "/command_interface":
    st.title("/command_interface")
    question = st.text_input("Enter your question here:")
    if st.button("/get_answer"):
        prompt = get_code_prompt(question, code_index, code_text)
        response = llm(prompt, selected_model)
        st.write(response)

elif add_radio == "/explain":
    st.title("/explain")
    for file in file_content:
        response = execute(selected_model, code_explain_prompt, file)
        st.write(response)

elif add_radio == "/generate_oo_design":
    st.title("/generate_oo_design")
    response = execute(selected_model, oo_design_prompt, code_text)
    st.write(response)

elif add_radio == "/generate_java_code":
    st.title("/generate_java_code")
    for file in file_content:
        response = execute(selected_model, java_code_gen_prompt, file)
        st.write(response)