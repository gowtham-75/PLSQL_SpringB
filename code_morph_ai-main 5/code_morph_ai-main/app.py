from dotenv import load_dotenv
import streamlit as st
import os
import requests
from util import extract_code, get_code_prompt
from prompt_templates import code_explain_prompt, java_code_gen_prompt, oo_design_prompt
from langchain.prompts import PromptTemplate
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
import warnings

warnings.filterwarnings('ignore')
_ = load_dotenv()

code_dir_name = "./code"

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

def is_response_incomplete(response):
    """Check if the response appears incomplete"""
    indicators = [
        len(response.split()) >= 900,  # Near token limit
        response.rstrip().endswith((':', '{', '(', ',', ';')),  # Code continuation markers
        response.count('{') != response.count('}'),  # Unmatched braces
        'class' in response.lower() and '}' not in response,  # Incomplete class definition
        'public' in response.lower() and '}' not in response,  # Incomplete method/class
        'private' in response.lower() and '}' not in response,
    ]
    return any(indicators)

def has_unmatched_code_blocks(response, stack):
    """Check for unmatched code blocks using the stack"""
    return bool(stack) or response.count('{') != response.count('}')

def create_continuation_prompt(previous_response, code_block_stack, attempt_number):
    """Create a context-aware continuation prompt"""
    last_context = previous_response[-500:]  # Increased context window
    
    prompt = (
        "Continue the Java code conversion from where you left off. "
        f"Current context: '{last_context}'\n"
        f"Open code blocks: {len(code_block_stack)}\n"
        "Maintain consistent code style and complete any unfinished statements or blocks.\n"
        "If generating a new method or class, ensure proper closure and documentation."
    )
    
    if attempt_number > 3:
        prompt += "\nPrioritize completing open code blocks and ensuring syntactic correctness."
        
    return prompt

def is_valid_continuation(continuation, full_response, last_chunk_size):
    """Validate the continuation response"""
    if len(continuation.strip()) < 10:
        return False
    
    # Check for duplicated content
    if continuation.strip() in full_response[-max(last_chunk_size * 2, 200):]:
        return False
        
    return True

def clean_continuation_response(continuation, previous_response):
    """Clean and format the continuation response"""
    # Remove common prefixes that might be duplicated
    common_prefixes = ['public class', 'private', 'public', 'protected', '    }']
    cleaned = continuation
    
    for prefix in common_prefixes:
        if (previous_response.strip().endswith(prefix) and 
            continuation.strip().startswith(prefix)):
            cleaned = continuation.replace(prefix, '', 1).strip()
    
    # Remove duplicate line endings
    if previous_response.strip().endswith(cleaned.strip()[:50]):
        return ""
        
    return cleaned

def update_code_block_stack(code_chunk, stack):
    """Update the stack of open code blocks"""
    for char in code_chunk:
        if char == '{':
            stack.append('{')
        elif char == '}' and stack:
            stack.pop()

def post_process_response(response, code_block_stack):
    """Post-process the complete response"""
    # Ensure all code blocks are properly closed
    missing_closures = len(code_block_stack)
    if missing_closures > 0:
        response += '\n' + '    }' * missing_closures
    
    # Clean up any formatting issues
    response = response.replace('\n\n\n', '\n\n')
    response = response.replace('};', '}')
    
    return response.strip()

def llm(prompt, model_name):
    """
    Enhanced LLM calling function with improved long response handling and strict loop control
    
    Args:
        prompt (str): The input prompt to send to the model
        model_name (str): Name of the model to use
        
    Returns:
        str: The complete response from the model
    """
    try:
        conversation = initialize_conversation(model_name)
        
        # Generate initial response
        response = conversation.predict(input=prompt)
        full_response = response
        max_tokens = 500
        
        # Track number of continuation attempts
        continuation_attempts = 0
        max_attempts = 3
        last_processed_length = 0
        code_block_stack = []
        
        while is_response_incomplete(full_response) and continuation_attempts < max_attempts:
            # Check if response needs continuation
            current_length = len(full_response)
            needs_continuation = is_response_incomplete(full_response)
            
            # Break if response seems complete or hasn't grown
            if not needs_continuation or current_length == last_processed_length:
                break
                
            last_processed_length = current_length
                
            # Create a context-aware continuation prompt
            continuation_prompt = create_continuation_prompt(full_response, code_block_stack, continuation_attempts)
                
            try:
                continuation_response = conversation.predict(input=continuation_prompt)
                
                # Validate continuation
                if not is_valid_continuation(continuation_response, full_response, current_length):
                    # If the continuation is not valid, retry with the original prompt
                    continuation_prompt = prompt
                    continuation_response = conversation.predict(input=continuation_prompt)
                    
                    if not is_valid_continuation(continuation_response, full_response, current_length):
                        break  # Break if response is still not valid
                
                # Clean and format the continuation response
                cleaned_continuation = clean_continuation_response(continuation_response, full_response)
                if cleaned_continuation:
                    full_response += "\n" + cleaned_continuation
                
                # Update the code block stack
                update_code_block_stack(cleaned_continuation, code_block_stack)
                    
                continuation_attempts += 1
                
                # Progress indicator
                if st.session_state.get('show_progress', True):
                    st.write(f"Generating continuation {continuation_attempts}/{max_attempts}...")
                
            except Exception as e:
                st.warning(f"Continuation attempt {continuation_attempts + 1} failed: {str(e)}")
                
                # If the continuation fails, retry with the original prompt
                continuation_prompt = prompt
                try:
                    continuation_response = conversation.predict(input=continuation_prompt)
                    full_response += "\n" + continuation_response
                except Exception as e:
                    st.error(f"Error calling model: {str(e)}")
                    return None
                    
                continuation_attempts += 1
                
                if continuation_attempts >= max_attempts:
                    st.warning("Reached maximum number of continuation attempts. Response may be truncated.")
                    break
        
        # Post-process the final response
        full_response = post_process_response(full_response, code_block_stack)
        return full_response.strip()
 
    except Exception as e:
        st.error(f"Error calling model: {str(e)}")
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

elif add_radio == "/generate_java_code":
    st.title("/generate_java_code")
    for file in file_content:
        response = execute(selected_model, java_code_gen_prompt, file)
        st.write(response)
        st.write("\nApproximate word count:", len(response.split()))
# # -----------------------------------------------------------------------------------------
# from dotenv import load_dotenv
# import streamlit as st
# import os
# import requests
# from util import extract_code, get_code_prompt
# from prompt_templates import code_explain_prompt, java_code_gen_prompt, oo_design_prompt
# from langchain_core.prompts import PromptTemplate
# from langchain.chains.conversation.base import ConversationChain
# from langchain.memory import ConversationBufferMemory
# from langchain_openai import AzureChatOpenAI
# import warnings

# warnings.filterwarnings('ignore')
# _ = load_dotenv()

# code_dir_name = "./code"

# def initialize_conversation(model_name):
#     """
#     Initialize the conversation chain with the specified model
#     """
#     chat = AzureChatOpenAI(
#         azure_deployment=os.environ["DEPLOYMENT_NAME"],
#         openai_api_version="2024-09-01-preview",
#         azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
#         api_key=os.environ["AZURE_OPENAI_API_KEY"],
#         temperature=0.5,
#         max_tokens=4000,
#         model_name=model_name
#     )
#     memory = ConversationBufferMemory(return_messages=True)
#     return ConversationChain(llm=chat, memory=memory)




















# def is_response_incomplete(response):
#     """Check if the response appears incomplete"""
#     indicators = [
#         len(response.split()) >= 900,  # Near token limit
#         response.rstrip().endswith((':', '{', '(', ',', ';')),  # Code continuation markers
#         response.count('{') != response.count('}'),  # Unmatched braces
#         'class' in response.lower() and '}' not in response,  # Incomplete class definition
#         'public' in response.lower() and '}' not in response,  # Incomplete method/class
#         'private' in response.lower() and '}' not in response,
#     ]
#     return any(indicators)

# def has_unmatched_code_blocks(response, stack):
#     """Check for unmatched code blocks using the stack"""
#     return bool(stack) or response.count('{') != response.count('}')

# def create_continuation_prompt(previous_response, code_block_stack, attempt_number):
#     """Create a context-aware continuation prompt"""
#     last_context = previous_response[-500:]  # Increased context window
    
#     prompt = (
#         "Continue the Java code conversion from where you left off. "
#         f"Current context: '{last_context}'\n"
#         f"Open code blocks: {len(code_block_stack)}\n"
#         "Maintain consistent code style and complete any unfinished statements or blocks.\n"
#         "If generating a new method or class, ensure proper closure and documentation."
#     )
    
#     if attempt_number > 3:
#         prompt += "\nPrioritize completing open code blocks and ensuring syntactic correctness."
        
#     return prompt

# def is_valid_continuation(continuation, full_response, last_chunk_size):
#     """Validate the continuation response"""
#     if len(continuation.strip()) < 10:
#         return False
    
#     # Check for duplicated content
#     if continuation.strip() in full_response[-max(last_chunk_size * 2, 200):]:
#         return False
        
#     return True

# def clean_continuation_response(continuation, previous_response):
#     """Clean and format the continuation response"""
#     # Remove common prefixes that might be duplicated
#     common_prefixes = ['public class', 'private', 'public', 'protected', '    }']
#     cleaned = continuation
    
#     for prefix in common_prefixes:
#         if (previous_response.strip().endswith(prefix) and 
#             continuation.strip().startswith(prefix)):
#             cleaned = continuation.replace(prefix, '', 1).strip()
    
#     # Remove duplicate line endings
#     if previous_response.strip().endswith(cleaned.strip()[:50]):
#         return ""
        
#     return cleaned

# def update_code_block_stack(code_chunk, stack):
#     """Update the stack of open code blocks"""
#     for char in code_chunk:
#         if char == '{':
#             stack.append('{')
#         elif char == '}' and stack:
#             stack.pop()

# def post_process_response(response, code_block_stack):
#     """Post-process the complete response"""
#     # Ensure all code blocks are properly closed
#     missing_closures = len(code_block_stack)
#     if missing_closures > 0:
#         response += '\n' + '    }' * missing_closures
    
#     # Clean up any formatting issues
#     response = response.replace('\n\n\n', '\n\n')
#     response = response.replace('};', '}')
    
#     return response.strip()

















# def llm(prompt, model_name):
#     """
#     Enhanced LLM calling function with improved long response handling and strict loop control
    
#     Args:
#         prompt (str): The input prompt to send to the model
#         model_name (str): Name of the model to use
        
#     Returns:
#         str: The complete response from the model
#     """
#     try:
#         conversation = initialize_conversation(model_name)
        
#         # Generate initial response
#         response = conversation.predict(input=prompt)
#         full_response = response
#         max_tokens = 500
#         # Track number of continuation attempts
#         continuation_attempts = 0
#         max_attempts = 3
#         last_processed_length = 0
        
#         needs_continuation = len(response.split()) >= max_tokens - 50
        
#         while needs_continuation and continuation_attempts < max_attempts:
#             # Check if response needs continuation
#             current_length = len(full_response)
#             needs_continuation = (
#                 len(full_response.split()) >= max_tokens - 50  # Close to token limit
#                 or full_response.rstrip().endswith(('.', ':', ','))  # Ends mid-sentence
#                 or not full_response.strip().endswith(('.', '!', '?', '"', "'"))  # No proper ending
#             )
            
#             # Break if response seems complete or hasn't grown
#             if not needs_continuation or current_length == last_processed_length:
#                 break
                
#             last_processed_length = current_length
                
#             # Add context from previous response to maintain coherence
#             continuation_prompt = (
#                 "The previous response may be incomplete. Please continue from where "
#                 "you left off, maintaining the same context and format. "
#                 "Here's the last part of the previous response: "
#                 f"'{full_response[-200:]}'..."
#             )
                
#             try:
#                 continuation_response = conversation.predict(input=continuation_prompt)
                
#                 # Validate continuation
#                 if len(continuation_response.strip()) < 10:
#                     # If the continuation is too short, retry with the original prompt
#                     continuation_prompt = prompt
#                     continuation_response = conversation.predict(input=continuation_prompt)
                    
#                     if len(continuation_response.strip()) < 10:
#                         break  # Break if response is still too short
                
#                 # Check for duplicate content
#                 if continuation_response.strip() not in full_response[-200:]:
#                     full_response += "\n" + continuation_response
#                 else:
#                     break  # Break if getting duplicate content
                    
#                 continuation_attempts += 1
                
#                 # Progress indicator
#                 if st.session_state.get('show_progress', True):
#                     st.write(f"Generating continuation {continuation_attempts}/{max_attempts}...")
                
#             except Exception as e:
#                 st.warning(f"Continuation attempt {continuation_attempts + 1} failed: {str(e)}")
                
#                 # If the continuation fails, retry with the original prompt
#                 continuation_prompt = prompt
#                 try:
#                     continuation_response = conversation.predict(input=continuation_prompt)
#                     full_response += "\n" + continuation_response
#                 except Exception as e:
#                     st.error(f"Error calling model: {str(e)}")
#                     return None
                    
#                 continuation_attempts += 1
                
#                 if continuation_attempts >= max_attempts:
#                     st.warning("Reached maximum number of continuation attempts. Response may be truncated.")
#                     break
        
#         return full_response.strip()
 
#     except Exception as e:
#         st.error(f"Error calling model: {str(e)}")
#         return None




# # Extract code content
# code_index, code_text, file_content = extract_code(code_dir_name)

# # Initialize selected model
# selected_model = None

# st.title("/CodeMorph_AI")

# # Sidebar styling
# st.markdown(
#     """
#     <style>
#         section[data-testid="stSidebar"] {
#             width: 300px !important;
#         }
#     </style>
#     """,
#     unsafe_allow_html=True,
# )

# # Sidebar content
# with st.sidebar:
#     st.title("/CodeMorph_AI")
#     st.image("image/legacy_mod.jpeg", width=250)

#     select_model = st.radio(
#         "Select the Language Model",
#         ("/openai_gpt_4o_mini",
#          "/openai_gpt_4o",
#          "/openai_o1_preview",
#          "/openai_o1_mini",
#          "/claude_3.5_sonnet")
#     )

#     # Map selection to model names
#     model_mapping = {
#         "/openai_gpt_4o_mini": "gpt-4o-mini",
#         "/openai_gpt_4o": "gpt-4o",
#         "/openai_o1_preview": "o1-preview",
#         "/openai_o1_mini": "o1-mini",
#         "/claude_3.5_sonnet": "claude-3-5-sonnet"
#     }
    
#     selected_model = model_mapping[select_model]
#     st.write("Selected Language Model:", selected_model)

#     add_radio = st.radio(
#         "What can I do for you today?",
#         ("/show_code",
#          "/command_interface",
#          "/explain",
#          "/generate_oo_design",
#          "/generate_java_code")
#     )

# def execute(model_name, exec_prompt, code):
#     """
#     Execute LLM with provided prompt template
#     """
#     final_prompt = PromptTemplate.from_template(exec_prompt)
#     formatted_prompt = final_prompt.format(PLSQL_CODE=code)
#     return llm(formatted_prompt, model_name)

# # Main content based on selection
# if add_radio == "/show_code":
#     st.title("/show_code")
#     st.write("Here is the index of the files in the codebase:")
#     st.write(code_index)
#     st.write("Here is the entire codebase:")
#     st.code(code_text)

# elif add_radio == "/command_interface":
#     st.title("/command_interface")
#     question = st.text_input("Enter your question here:")
#     if st.button("/get_answer"):
#         prompt = get_code_prompt(question, code_index, code_text)
#         response = llm(prompt, selected_model)
#         st.write(response)
#         st.write("\nApproximate word count:", len(response.split()))

# elif add_radio == "/explain":
#     st.title("/explain")
#     for file in file_content:
#         response = execute(selected_model, code_explain_prompt, file)
#         st.write(response)
#         st.write("\nApproximate word count:", len(response.split()))

# elif add_radio == "/generate_oo_design":
#     st.title("/generate_oo_design")
#     response = execute(selected_model, oo_design_prompt, code_text)
#     st.write(response)
#     st.write("\nApproximate word count:", len(response.split()))

# elif add_radio == "/generate_java_code":
#     st.title("/generate_java_code")
#     for file in file_content:
#         response = execute(selected_model, java_code_gen_prompt, file)
#         st.write(response)
#         st.write("\nApproximate word count:", len(response.split()))
        
        
        
        
        # --------------------------------------------------------------------------------------------
        
# def llm(prompt, model_name):
#     """
#     Enhanced LLM calling function with robust long response handling for code generation
    
#     Args:
#         prompt (str): The input prompt to send to the model
#         model_name (str): Name of the model to use
        
#     Returns:
#         str: The complete response from the model
#     """
#     try:
#         conversation = initialize_conversation(model_name)
        
#         # Split long prompts into manageable chunks if needed
#         max_prompt_length = 4000
#         # if len(prompt) > max_prompt_length:
#         #     st.warning("Long Response - processing in chunks...")
            
#         # Generate initial response
#         full_response = conversation.predict(input=prompt)
        
#         # Initialize variables for response tracking
#         continuation_attempts = 0
#         max_attempts = 3  # Increased for complex code generation
#         last_chunk_size = 0
#         code_block_stack = []  # Track open code blocks
        
#         # Check if response appears incomplete
#         while (continuation_attempts < max_attempts and 
#                (is_response_incomplete(full_response) or 
#                 has_unmatched_code_blocks(full_response, code_block_stack))):
            
#             # Create a context-aware continuation prompt
#             continuation_prompt = create_continuation_prompt(
#                 full_response, 
#                 code_block_stack,
#                 continuation_attempts
#             )
            
#             try:
#                 continuation_response = conversation.predict(input=continuation_prompt)
                
#                 # Validate continuation response
#                 if is_valid_continuation(continuation_response, full_response, last_chunk_size):
#                     # Clean and append the continuation
#                     cleaned_continuation = clean_continuation_response(
#                         continuation_response,
#                         full_response
#                     )
                    
#                     if cleaned_continuation:
#                         full_response += "\n" + cleaned_continuation
#                         last_chunk_size = len(cleaned_continuation)
#                         update_code_block_stack(cleaned_continuation, code_block_stack)
                        
#                         # Show progress in Streamlit
#                         if st.session_state.get('show_progress', True):
#                             progress_message = (
#                                 f"Generating continuation {continuation_attempts + 1}/{max_attempts}\n"
#                                 f"Code blocks status: {len(code_block_stack)} open"
#                             )
#                             st.write(progress_message)
#                     else:
#                         break  # No valid continuation found
#                 else:
#                     break  # Invalid continuation
                
#                 continuation_attempts += 1
#                 if(continuation_attempts==3):
#                     break
                
#             except Exception as e:
#                 st.warning(f"Continuation attempt {continuation_attempts + 1} failed: {str(e)}")
#                 break
        
#         # Post-processing
#         final_response = post_process_response(full_response, code_block_stack)
        
#         if continuation_attempts >= max_attempts:
#             st.warning("Reached maximum continuation attempts. Please verify the complete code conversion.")
        
#         return final_response
    
#     except Exception as e:
#         st.error(f"Error in code conversion: {str(e)}")
#         return None

# def llm(prompt, model_name):
    # """
    # Enhanced LLM calling function with improved long response handling and strict loop control
    
    # Args:
    #     prompt (str): The input prompt to send to the model
    #     model_name (str): Name of the model to use
        
    # Returns:
    #     str: The complete response from the model
    # """
    # try:
    #     conversation = initialize_conversation(model_name)
        
    #     # Generate initial response
    #     response = conversation.predict(input=prompt)
    #     full_response =response
    #     max_tokens = 500
    #     # Track number of continuation attempts
    #     continuation_attempts = 0
    #     max_attempts = 3
    #     last_processed_length = 0
        
        
    #     needs_continuation = len(response.split()) >= max_tokens - 50
                                                                                                                           
    #     while needs_continuation and continuation_attempts < max_attempts:
    #         print(continuation_attempts)
    #         if(continuation_attempts==3):
    #             print("breakloop")
    #             break
    #         # Check if response needs continuation
    #         current_length = len(full_response)
    #         needs_continuation = (
    #             len(full_response.split()) >= 450  or  # Close to token limit
    #             full_response.rstrip().endswith(('.', ':', ',')) or  # Ends mid-sentence
    #             not full_response.strip().endswith(('.', '!', '?', '"', "'"))  # No proper ending
    #         )
            
    #         # Break if response seems complete or hasn't grown
    #         if not needs_continuation or current_length == last_processed_length:
    #             break
                
    #         last_processed_length = current_length
                                                                                                                                  
    #         # Add context from previous response to maintain coherence
    #         continuation_prompt = (
    #             "The previous response may be incomplete. Please continue from where "
    #             "you left off, maintaining the same context and format. "
    #             "Here's the last part of the previous response: "
    #             f"'{full_response[-200:]}'..."
    #         )
                                                                                                                                  
    #         try:
    #             continuation_response = conversation.predict(input=continuation_prompt)
                
    #             # Validate continuation
    #             if len(continuation_response.strip()) < 10:
    #                 break  # Break if response is too short
                    
    #             # Check for duplicate content
    #             if continuation_response.strip() not in full_response[-200:]:
    #                 full_response += "\n" + continuation_response
    #             else:
    #                 break  # Break if getting duplicate content
                    
    #             continuation_attempts += 1
                
    #             # Progress indicator
    #             if st.session_state.get('show_progress', True):
    #                 st.write(f"Generating continuation {continuation_attempts}/{max_attempts}...")
                
    #         except Exception as e:
    #             st.warning(f"Continuation attempt {continuation_attempts + 1} failed: {str(e)}")
    #             break
            
            
    #         needs_continuation = len(continuation_response.split()) >= max_tokens - 50
    
    #     if continuation_attempts >= max_attempts:
    #         st.warning("Reached maximum number of continuation attempts. Response may be truncated.")
            
    #     return full_response.strip()
 
    # except Exception as e:
    #     st.error(f"Error calling model: {str(e)}")
    #     return None 
    