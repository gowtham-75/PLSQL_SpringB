from dotenv import load_dotenv
import streamlit as st
import os
import requests
from util import extract_code, get_code_prompt
from prompt_templates import code_explain_prompt, java_code_gen_prompt, oo_design_prompt, ms_prompt
from langchain_core.prompts import PromptTemplate
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
import warnings
import tiktoken


warnings.filterwarnings('ignore')
_ = load_dotenv()

code_dir_name = "./extract_code"

def initialize_conversation(model_name):
    """
    Initialize the conversation chain with the specified model
    """
    chat = AzureChatOpenAI(
        azure_deployment=os.environ["DEPLOYMENT_NAME"],
        openai_api_version="2024-09-01-preview",
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ["AZURE_OPENAI_API_KEY"],
        temperature=0.5,
        max_tokens=4000,
        model_name=model_name
    )
    memory = ConversationBufferMemory(return_messages=True)
    return ConversationChain(llm=chat, memory=memory)


def llm(prompt, model_name):
    """
    Handle LLM interactions with automatic continuation for long responses
    """
    # Initialize conversation with the selected model
    conversation = initialize_conversation(model_name)
    
    # Generate the initial response
    response = conversation.predict(input=prompt)
    
    # Initialize the full response
    full_response = response
    
    
    
    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
    # Encode the text to get tokens
    tokens = encoding.encode(full_response)
    st.write("Number of tokens:", len(tokens))
    
    # Check if continuation is needed (leaving buffer of 50 tokens)
    max_tokens = 4000  # Using the max_tokens set in initialize_conversation
    needs_continuation = len(tokens) >= max_tokens - 400
    # st.write(needs_continuation)
    # Handle continuation if needed
    # check_end="END" in full_response
    # if(check_end):
    #     st.write(check_end)
    # st.write(full_response)
    while needs_continuation:# and "END" not in full_response
        # st.write("Inside_loop",needs_continuation)
        # Prompt the model to continue
        continuation_prompt = "Please continue where you left off."
        
        # Generate the continuation response
        continuation_response = conversation.predict(input=continuation_prompt)
        
        # Append the continuation to the full response
        full_response += " " + continuation_response
        tokens_continuation = encoding.encode(continuation_response)
        # Check again if the continuation is also truncated
        needs_continuation = len(tokens_continuation) >= max_tokens - 400
        
        # st.write(continuation_response)

        # Add a safeguard to prevent infinite loops
        if len(full_response) > max_tokens * 5:  # Limit to 5 continuations
            break
        
    
    return full_response

def execute(model_name, exec_prompt, code):
    final_prompt = PromptTemplate.from_template(exec_prompt)
    formatted_prompt = final_prompt.format(PLSQL_CODE=code)
    return llm(formatted_prompt, model_name)

def execute1(model_name, exec_prompt, code,response):
    final_prompt = PromptTemplate.from_template(exec_prompt)
    formatted_prompt = final_prompt.format(PLSQL_CODE=code, response=response)
    return llm(formatted_prompt, model_name)

def execute(model_name, exec_prompt, code):
    """
    Execute LLM with provided prompt template
    """
    final_prompt = PromptTemplate.from_template(exec_prompt)
    formatted_prompt = final_prompt.format(PLSQL_CODE=code)
    print(formatted_prompt)
    return llm(formatted_prompt, model_name)
   

# # Extract code content
# code_index, code_text, file_content = extract_code(code_dir_name)

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



import zipfile
import io

# File uploader for zip file
uploaded_file = st.file_uploader("Upload a zip file containing code", type=["zip"])

if uploaded_file is not None:
    # Clear the existing files in the code directory
    if os.path.exists(code_dir_name):
        for filename in os.listdir(code_dir_name):
            file_path = os.path.join(code_dir_name, filename)
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)  # Remove file
                elif os.path.isdir(file_path):
                    os.rmdir(file_path)  # Remove directory (if empty)
            except Exception as e:
                st.write(f"Error removing file {file_path}: {e}")

    else:
        os.makedirs(code_dir_name)  # Create the directory if it doesn't exist

    # Extract the contents of the zip file
    with zipfile.ZipFile(uploaded_file, 'r') as zip_ref:
        zip_ref.extractall(code_dir_name)  # Extract to a directory

    # Now you can call extract_code on the extracted files
    code_index, code_text, file_content = extract_code(code_dir_name)
        
    if "show_code" not in st.session_state:
        st.session_state["show_code"] = False
    if "response" not in st.session_state:
        st.session_state["response"] = None
    if "MS_response" not in st.session_state:
        st.session_state["MS_response"] = None
    if "response_doc" not in st.session_state:
        st.session_state["response_doc"] = None
        
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
            st.write("\nApproximate word count:", len(response.split()))

    elif add_radio == "/explain":
        st.title("/explain")
        for file in file_content:
            response = execute(selected_model, code_explain_prompt, file)
            st.write(response)
            st.write("\nApproximate word count:", len(response.split()))

    elif add_radio == "/generate_oo_design":
        st.title("/generate_oo_design")
        response = execute(selected_model, oo_design_prompt, code_text)
        st.write(response)
        st.write("\nApproximate word count:", len(response.split()))

# elif add_radio == "/generate_java_code":
#     st.title("/generate_java_code")
    # for file in file_content:
    #     response=None
    #     col=st.tabs(["Spring Boot Code", "Microservice Code","Doc to Microservice Code"])
    #     with col[0]:
    #         toggle=st.toggle("Show Code")
    #         if toggle:
    #             response = execute(selected_model, java_code_gen_prompt, file)
    #             st.write(response)
    #         with col[1]:
    #             MS_response = execute(selected_model, ms_prompt, response)
    #             st.write(MS_response)
    #         with col[2]:
            
    #             response_doc = execute(selected_model, oo_design_prompt, code_text)
    #             MS_response = execute(selected_model, ms_prompt, response, response_doc)
    #             st.write(MS_response)
    # Initialize session state variables


    elif add_radio == "/generate_java_code":
        st.title("/generate_java_code")
        # st.write(file_content)
        col = st.tabs(["Spring Boot Code", "Microservice Code", "Doc to Microservice Code"])

        for file in file_content:
            # st.write("file_data_is")
            # st.write(file)

            # Tab 0: Spring Boot Code
            with col[0]:
                st.session_state["show_code"] = st.toggle("Show Code", st.session_state["show_code"], key="check1")
                if st.session_state["show_code"]:
                    if st.session_state["response"] is None:
                        st.session_state["response"] = execute(selected_model, java_code_gen_prompt, file)
                    st.write(st.session_state["response"])
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                    tokens = encoding.encode(st.session_state["response"])
                    st.write("\nApproximate word count:", len(tokens))    

            # Tab 1: Microservice Code
            with col[1]:
                if st.session_state["response"] is not None:
                    if st.session_state["MS_response"] is None:
                        st.session_state["MS_response"] = execute(selected_model, ms_prompt, st.session_state["response"])
                    st.write(st.session_state["MS_response"])
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                    tokens = encoding.encode(st.session_state["MS_response"])
                    st.write("\nApproximate word count:", len(tokens))    

            # Tab 2: Doc to Microservice Code
            with col[2]:
                if st.session_state["response"] is not None:
                    if st.session_state["response_doc"] is None:
                        st.session_state["response_doc"] = execute(selected_model, oo_design_prompt, code_text)
                    if st.session_state["MS_response"] is None:  # Reuse MS_response or create it
                        st.session_state["MS_response"] = execute1(
                            selected_model, ms_prompt, st.session_state["response"], st.session_state["response_doc"]
                        )
                    st.write(st.session_state["MS_response"])
                    encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
                    tokens = encoding.encode(st.session_state["MS_response"])
                    st.write("\nApproximate word count:", len(tokens))            
                    
        # sping boot
        # st.write(response)
        # medhod(response, document)
       




