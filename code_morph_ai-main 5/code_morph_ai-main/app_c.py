from dotenv import load_dotenv
import streamlit as st
import os
import requests
from util import extract_code, get_code_prompt
from prompt_templates import code_explain_prompt, java_code_gen_prompt, oo_design_prompt
from langchain_core.prompts import PromptTemplate
from langchain.chains.conversation.base import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain_openai import AzureChatOpenAI
import warnings

warnings.filterwarnings('ignore')
_ = load_dotenv()

code_dir_name = "./code"

def generate_complete_response(prompt, model_name, initial_temperature=0):
    """
    Generate complete response with dynamic temperature adjustment and chunked completion
    
    Args:
        prompt (str): Input prompt for the model
        model_name (str): Name of the model to use
        initial_temperature (float): Starting temperature value
        
    Returns:
        str: Complete generated response
    """
    def init_llm(temp):
        return AzureChatOpenAI(
            azure_deployment=os.environ["DEPLOYMENT_NAME"],
            openai_api_version="2024-09-01-preview",
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            temperature=temp,
            max_tokens=4000,
            model_name=model_name
        )
    
    # Initialize tracking variables
    full_response = ""
    current_temp = initial_temperature
    max_attempts = 3
    attempt = 0
    
    # Create progress indicators
    if st.session_state.get('show_progress', True):
        progress_bar = st.progress(0)
        status_text = st.empty()
    
    try:
        while attempt < max_attempts:
            # Update progress
            if st.session_state.get('show_progress', True):
                progress = (attempt + 1) / max_attempts
                progress_bar.progress(progress)
                status_text.text(f"Generating response... Attempt {attempt + 1}/{max_attempts}")
            
            # Initialize conversation with current temperature
            conversation = ConversationChain(
                llm=init_llm(current_temp),
                memory=ConversationBufferMemory(return_messages=True)
            )
            
            # Generate response
            if not full_response:
                # Initial generation
                response = conversation.predict(input=prompt)
            else:
                # Continuation prompt
                continuation_prompt = create_continuation_prompt(full_response, prompt)
                response = conversation.predict(input=continuation_prompt)
            
            # Validate and process response
            if is_response_complete(response):
                full_response = response if not full_response else merge_responses(full_response, response)
                break
            else:
                # Incomplete response - adjust temperature and try again
                full_response = response if not full_response else merge_responses(full_response, response)
                current_temp = min(2.0, current_temp + 0.2)  # Increase temperature, max 2.0
                attempt += 1
        
        # Final validation and warning if still incomplete
        if not is_response_complete(full_response):
            st.warning("Generated response may be incomplete. Please verify the output.")
        
        return full_response
        
    except Exception as e:
        st.error(f"Error in response generation: {str(e)}")
        return None

def create_continuation_prompt(previous_response, original_prompt):
    """
    Create a prompt for continuing the response
    """
    return f"""
    Previous response context:
    {previous_response[-500:]}  # Last 500 characters for context
    
    Original request:
    {original_prompt}
    
    Please continue the response, maintaining consistency with the previous content.
    Focus on completing any unfinished sections or thoughts.
    """

def is_response_complete(response):
    """
    Check if the response is complete based on various indicators
    """
    if not response:
        return False
        
    # General completeness indicators
    indicators = [
        not response.rstrip().endswith((':', ';', '{', '(', ',')),  # No hanging punctuation
        response.count('{') == response.count('}'),  # Balanced braces
        response.count('(') == response.count(')'),  # Balanced parentheses
        not any(keyword in response.split()[-1] for keyword in [
            'and', 'or', 'but', 'the', 'a', 'an',
            'in', 'on', 'at', 'to', 'for'
        ]),  # No hanging words
    ]
    
    # For code-specific completeness
    if 'class ' in response or 'def ' in response:
        code_indicators = [
            not any(line.strip().endswith((':', '{')) 
                   for line in response.split('\n')),  # No incomplete blocks
            '}' in response.split('\n')[-1],  # Ends with closing brace
            all('class' not in line or '{' in line 
                for line in response.split('\n')),  # Complete class definitions
        ]
        indicators.extend(code_indicators)
    
    return all(indicators)

def merge_responses(base_response, continuation):
    """
    Intelligently merge the base response with the continuation
    """
    # Clean up responses
    base_response = base_response.rstrip()
    continuation = continuation.lstrip()
    
    # Find a suitable merge point
    merge_point = find_merge_point(base_response, continuation)
    
    if merge_point:
        # Merge at the identified point
        return base_response[:merge_point] + continuation
    else:
        # Simple concatenation with proper spacing
        return f"{base_response}\n{continuation}"

def find_merge_point(base, continuation):
    """
    Find the optimal point to merge the responses
    """
    # Look for overlap in the last 100 characters
    overlap_size = min(100, len(base), len(continuation))
    base_end = base[-overlap_size:]
    cont_start = continuation[:overlap_size]
    
    # Find the longest common substring
    for i in range(overlap_size, 0, -1):
        if base_end[-i:] == cont_start[:i]:
            return len(base) - i
    
    return None




























# def initialize_conversation(model_name):
#     """
#     Initialize the conversation chain with the specified model
#     """
#     chat = AzureChatOpenAI(
#         azure_deployment=os.environ["DEPLOYMENT_NAME"],
#         openai_api_version="2024-09-01-preview",
#         azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
#         api_key=os.environ["AZURE_OPENAI_API_KEY"],
#         temperature=0,
#         max_tokens=4000,
#         model_name=model_name
#     )
#     memory = ConversationBufferMemory(return_messages=True)
#     return ConversationChain(llm=chat, memory=memory)










# # ----------------------------------------------tries

# def llm_with_java_completion(prompt, model_name):
#     """
#     Enhanced LLM function with specific handling for Java code completion
    
#     Args:
#         prompt (str): The input prompt to send to the model
#         model_name (str): Name of the model to use
        
#     Returns:
#         str: The complete Java code response
#     """
#     try:
#         conversation = initialize_conversation(model_name)
        
#         # Generate initial response
#         full_response = conversation.predict(input=prompt)
        
#         # Initialize completion tracking
#         completion_metadata = {
#             'attempts': 0,
#             'max_attempts': 3,
#             'last_completion_length': 0,
#             'java_elements': {
#                 'classes': set(),
#                 'methods': set(),
#                 'interfaces': set()
#             }
#         }
        
#         # Create progress indicators
#         if st.session_state.get('show_progress', True):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
        
#         # Continue generation until code is complete or max attempts reached
#         while needs_completion(full_response, completion_metadata):
#             try:
#                 # Generate continuation prompt based on incomplete elements
#                 continuation_prompt = generate_java_continuation_prompt(
#                     full_response, 
#                     completion_metadata
#                 )
                
#                 # Get continuation response
#                 continuation = conversation.predict(input=continuation_prompt)
                
#                 # Validate and append continuation
#                 if is_valid_java_continuation(continuation, full_response, completion_metadata):
#                     full_response = append_java_continuation(
#                         full_response, 
#                         continuation, 
#                         completion_metadata
#                     )
                    
#                     # Update progress
#                     if st.session_state.get('show_progress', True):
#                         progress = min(1.0, completion_metadata['attempts'] / completion_metadata['max_attempts'])
#                         progress_bar.progress(progress)
#                         status_text.text(f"Completing Java code... {int(progress * 100)}%")
#                 else:
#                     break
                    
#             except Exception as e:
#                 st.warning(f"Java code completion error: {str(e)}")
#                 break
        
#         # Final processing and validation
#         processed_response = post_process_java_code(full_response)
#         if not is_java_code_complete(processed_response):
#             st.warning("Generated Java code may be incomplete. Please verify the output.")
        
#         return processed_response
        
#     except Exception as e:
#         st.error(f"Error in Java code generation: {str(e)}")
#         return None







# def needs_completion(response, metadata):
#     """
#     Check if Java code needs completion
#     """
#     if metadata['attempts'] >= metadata['max_attempts']:
#         return False
        
#     # Parse and analyze Java code structure
#     java_structure = analyze_java_structure(response)
#     metadata['java_elements'] = java_structure
    
#     incomplete_indicators = [
#         has_unmatched_java_braces(response),
#         has_incomplete_class_definitions(java_structure),
#         has_incomplete_method_definitions(java_structure),
#         has_incomplete_interface_definitions(java_structure),
#         ends_with_incomplete_java_statement(response)
#     ]
    
#     metadata['attempts'] += 1
#     return any(incomplete_indicators)

# def analyze_java_structure(code):
#     """
#     Analyze Java code structure and track elements
#     """
#     structure = {
#         'classes': set(),
#         'methods': set(),
#         'interfaces': set(),
#         'unmatched_elements': []
#     }
    
#     lines = code.split('\n')
#     current_class = None
#     current_method = None
    
#     for line in lines:
#         stripped = line.strip()
        
#         # Track class definitions
#         if 'class ' in stripped and not stripped.startswith('/'):
#             class_name = stripped.split('class ')[1].split()[0]
#             current_class = class_name
#             structure['classes'].add(class_name)
            
#         # Track interface definitions
#         elif 'interface ' in stripped and not stripped.startswith('/'):
#             interface_name = stripped.split('interface ')[1].split()[0]
#             structure['interfaces'].add(interface_name)
            
#         # Track method definitions
#         elif any(modifier in stripped for modifier in ['public', 'private', 'protected']) and '(' in stripped:
#             if not stripped.endswith(';'):  # Exclude method declarations
#                 method_name = stripped.split('(')[0].split()[-1]
#                 current_method = method_name
#                 structure['methods'].add(method_name)
    
#     return structure

# def generate_java_continuation_prompt(previous_response, metadata):
#     """
#     Generate context-aware prompt for Java code continuation
#     """
#     java_structure = metadata['java_elements']
#     incomplete_elements = []
    
#     # Identify incomplete elements
#     if has_incomplete_class_definitions(java_structure):
#         incomplete_elements.append("complete class definitions")
#     if has_incomplete_method_definitions(java_structure):
#         incomplete_elements.append("complete method implementations")
#     if has_incomplete_interface_definitions(java_structure):
#         incomplete_elements.append("complete interface definitions")
    
#     # Build continuation prompt
#     prompt_parts = [
#         "Continue the Java code implementation, maintaining consistency with the existing code.",
#         f"Previous code context:\n```java\n{previous_response[-300:]}\n```",
#         f"Please focus on: {', '.join(incomplete_elements)}",
#         "Ensure proper closure of all code blocks and maintain consistent indentation."
#     ]
    
#     return "\n".join(prompt_parts)

# def is_valid_java_continuation(continuation, previous_response, metadata):
#     """
#     Validate Java code continuation
#     """
#     if not continuation.strip():
#         return False
    
#     # Check for meaningful additions
#     if len(continuation.strip()) < metadata['last_completion_length'] * 0.1:
#         return False
    
#     # Avoid duplicate code blocks
#     last_block = previous_response.split('\n')[-5:]
#     continuation_block = continuation.split('\n')[:5]
#     if any(line.strip() in last_block for line in continuation_block):
#         return False
    
#     metadata['last_completion_length'] = len(continuation.strip())
#     return True

# import itertools
# def post_process_java_code(code):
#     """
#     Process and format Java code
#     """
#     lines = code.split('\n')
#     formatted_lines = []
#     indent_level = 0
#     in_comment = False
    
#     for line in lines:
#         stripped = line.strip()
        
#         # Handle comments
#         if stripped.startswith('/*'):
#             in_comment = True
#         if stripped.endswith('*/'):
#             in_comment = False
            
#         # Adjust indentation
#         if stripped.endswith('{'):
#             formatted_lines.append('    ' * indent_level + stripped)
#             indent_level += 1
#         elif stripped.startswith('}'):
#             indent_level = max(0, indent_level - 1)
#             formatted_lines.append('    ' * indent_level + stripped)
#         else:
#             formatted_lines.append('    ' * indent_level + stripped)
    
#     # Clean up empty lines
#     result = '\n'.join(line for line, _ in itertools.groupby(formatted_lines))
#     return result

# def is_java_code_complete(code):
#     """
#     Final validation of Java code completeness
#     """
#     validations = {
#         'balanced_braces': code.count('{') == code.count('}'),
#         'class_completion': all('class' not in line or '{' in line for line in code.split('\n')),
#         'method_completion': all(
#             not any(modifier in line for modifier in ['public', 'private', 'protected']) 
#             or '{' in line or ';' in line 
#             for line in code.split('\n')
#         ),
#         'proper_ending': code.strip().endswith('}'),
#         'no_incomplete_statements': not any(
#             line.strip().endswith((':', ';', '{', '(', ','))
#             for line in code.split('\n')
#         )
#     }
    
#     return all(validations.values())


# def has_unmatched_java_braces(code):
#     """
#     Check for unmatched braces in Java code
    
#     Args:
#         code (str): Java code to analyze
        
#     Returns:
#         bool: True if there are unmatched braces
#     """
#     stack = []
#     in_string = False
#     in_char = False
#     in_comment = False
#     multi_comment = False
    
#     for i, char in enumerate(code):
#         # Handle string literals
#         if char == '"' and not in_char and not in_comment and not multi_comment:
#             if not in_string:
#                 in_string = True
#             elif code[i-1] != '\\':  # Check for escaped quotes
#                 in_string = False
#             continue
            
#         # Handle character literals
#         if char == "'" and not in_string and not in_comment and not multi_comment:
#             if not in_char:
#                 in_char = True
#             elif code[i-1] != '\\':  # Check for escaped quotes
#                 in_char = False
#             continue
            
#         # Skip contents of strings and chars
#         if in_string or in_char:
#             continue
            
#         # Handle comments
#         if char == '/' and i + 1 < len(code):
#             if code[i + 1] == '/' and not in_comment and not multi_comment:
#                 in_comment = True
#                 continue
#             elif code[i + 1] == '*' and not in_comment and not multi_comment:
#                 multi_comment = True
#                 continue
                
#         if char == '\n' and in_comment:
#             in_comment = False
#             continue
            
#         if char == '/' and i > 0 and code[i - 1] == '*' and multi_comment:
#             multi_comment = False
#             continue
            
#         # Skip comments
#         if in_comment or multi_comment:
#             continue
            
#         # Track braces
#         if char == '{':
#             stack.append(char)
#         elif char == '}':
#             if not stack:
#                 return True  # Closing brace without matching opening brace
#             stack.pop()
    
#     return len(stack) > 0  # True if there are unclosed braces

# def has_incomplete_class_definitions(java_structure):
#     """
#     Check for incomplete class definitions
    
#     Args:
#         java_structure (dict): Dictionary containing Java code structure
        
#     Returns:
#         bool: True if there are incomplete class definitions
#     """
#     classes = java_structure['classes']
#     unmatched = java_structure.get('unmatched_elements', [])
    
#     for class_name in classes:
#         # Check class declaration pattern
#         class_pattern = f"class {class_name}"
#         if class_pattern in unmatched:
#             return True
            
#         # Check for missing class body
#         class_body_pattern = f"class {class_name} {{" 
#         if class_body_pattern in unmatched:
#             return True
    
#     return False

# def has_incomplete_method_definitions(java_structure):
#     """
#     Check for incomplete method definitions
    
#     Args:
#         java_structure (dict): Dictionary containing Java code structure
        
#     Returns:
#         bool: True if there are incomplete method definitions
#     """
#     methods = java_structure['methods']
#     lines = java_structure.get('code_lines', [])
    
#     for method in methods:
#         method_found = False
#         method_body_started = False
#         method_body_completed = False
#         brace_count = 0
        
#         for line in lines:
#             if method in line and ('public' in line or 'private' in line or 'protected' in line):
#                 method_found = True
            
#             if method_found:
#                 if '{' in line:
#                     method_body_started = True
#                     brace_count += line.count('{')
                    
#                 if '}' in line:
#                     brace_count -= line.count('}')
                    
#                 if brace_count == 0 and method_body_started:
#                     method_body_completed = True
#                     break
        
#         if method_found and not method_body_completed:
#             return True
            
#     return False

# def has_incomplete_interface_definitions(java_structure):
#     """
#     Check for incomplete interface definitions
    
#     Args:
#         java_structure (dict): Dictionary containing Java code structure
        
#     Returns:
#         bool: True if there are incomplete interface definitions
#     """
#     interfaces = java_structure['interfaces']
#     unmatched = java_structure.get('unmatched_elements', [])
    
#     for interface in interfaces:
#         # Check interface declaration pattern
#         interface_pattern = f"interface {interface}"
#         if interface_pattern in unmatched:
#             return True
            
#         # Check for missing interface body
#         interface_body_pattern = f"interface {interface} {{"
#         if interface_body_pattern in unmatched:
#             return True
            
#         # Check for method declarations without semicolons
#         for line in java_structure.get('code_lines', []):
#             if interface in line and '(' in line and not line.strip().endswith(';'):
#                 return True
    
#     return False

# def ends_with_incomplete_java_statement(code):
#     """
#     Check if the Java code ends with an incomplete statement
    
#     Args:
#         code (str): Java code to analyze
        
#     Returns:
#         bool: True if the code ends with an incomplete statement
#     """
#     # Get the last non-empty line
#     lines = [line.strip() for line in code.split('\n') if line.strip()]
#     if not lines:
#         return False
        
#     last_line = lines[-1]
    
#     # Check for incomplete statements
#     incomplete_indicators = [
#         # Statement terminators missing
#         not last_line.endswith((';', '}', '{')),
        
#         # Common keywords that suggest incomplete statements
#         any(last_line.endswith(keyword) for keyword in [
#             'new',
#             'return',
#             'throw',
#             'throws',
#             'extends',
#             'implements',
#             'instanceof'
#         ]),
        
#         # Access modifiers without completion
#         any(last_line.endswith(modifier) for modifier in [
#             'public',
#             'private',
#             'protected',
#             'static',
#             'final',
#             'abstract'
#         ]),
        
#         # Type declarations without completion
#         any(last_line.endswith(type_decl) for type_decl in [
#             'class',
#             'interface',
#             'enum'
#         ]),
        
#         # Common operators suggesting incomplete expressions
#         any(last_line.endswith(operator) for operator in [
#             '+', '-', '*', '/', '%',
#             '=', '==', '!=', '<', '>', '<=', '>=',
#             '&&', '||', '&', '|', '^',
#             '<<', '>>'
#         ]),
        
#         # Incomplete parentheses or brackets
#         last_line.count('(') > last_line.count(')'),
#         last_line.count('[') > last_line.count(']'),
        
#         # Incomplete string literals
#         last_line.count('"') % 2 == 1,
#         last_line.count("'") % 2 == 1
#     ]
    
#     return any(incomplete_indicators)

# def append_java_continuation(base_code, continuation, metadata):
#     """
#     Intelligently append Java code continuation to base code
    
#     Args:
#         base_code (str): Original Java code
#         continuation (str): New code to append
#         metadata (dict): Metadata about the code generation process
        
#     Returns:
#         str: Combined and properly formatted Java code
#     """
#     # Clean up continuation
#     continuation = continuation.strip()
#     base_code = base_code.strip()
    
#     # Remove duplicate class/method declarations
#     continuation_lines = continuation.split('\n')
#     filtered_lines = []
    
#     base_declarations = extract_declarations(base_code)
    
#     for line in continuation_lines:
#         line_stripped = line.strip()
        
#         # Skip if line is a duplicate declaration
#         if is_declaration(line_stripped) and any(
#             are_similar_declarations(line_stripped, decl) 
#             for decl in base_declarations
#         ):
#             continue
            
#         # Skip if line is just a closing brace that might duplicate
#         if line_stripped == '}' and base_code.rstrip().endswith('}'):
#             continue
            
#         filtered_lines.append(line)
    
#     # Determine proper insertion point
#     insertion_point = find_insertion_point(base_code)
    
#     # Combine code
#     if insertion_point is None:
#         # Simple append with proper spacing
#         if base_code and continuation:
#             return f"{base_code}\n{'\n'.join(filtered_lines)}"
#         return base_code or continuation
#     else:
#         # Insert at specific point
#         base_lines = base_code.split('\n')
#         result = base_lines[:insertion_point]
#         result.extend(filtered_lines)
#         result.extend(base_lines[insertion_point:])
#         return '\n'.join(result)

# def extract_declarations(code):
#     """Helper function to extract class/method declarations"""
#     declarations = []
#     for line in code.split('\n'):
#         line = line.strip()
#         if is_declaration(line):
#             declarations.append(line)
#     return declarations

# def is_declaration(line):
#     """Helper function to identify Java declarations"""
#     declaration_indicators = [
#         'class ',
#         'interface ',
#         'enum ',
#         'public ',
#         'private ',
#         'protected '
#     ]
#     return any(indicator in line for indicator in declaration_indicators)

# def are_similar_declarations(decl1, decl2):
#     """Helper function to compare declarations for similarity"""
#     # Remove access modifiers and whitespace for comparison
#     clean1 = ' '.join(word for word in decl1.split() 
#                      if word not in ['public', 'private', 'protected', 'static', 'final'])
#     clean2 = ' '.join(word for word in decl2.split() 
#                      if word not in ['public', 'private', 'protected', 'static', 'final'])
    
#     # Compare cleaned declarations
#     return clean1 == clean2 or (
#         # Handle method declarations with different parameter names
#         '(' in clean1 and
#         '(' in clean2 and
#         clean1[:clean1.index('(')] == clean2[:clean2.index('(')]
#     )

# def find_insertion_point(code):
#     """Helper function to find appropriate insertion point for continuation"""
#     lines = code.split('\n')
    
#     # Look for incomplete class/method blocks from bottom
#     brace_count = 0
#     for i in range(len(lines) - 1, -1, -1):
#         line = lines[i].strip()
        
#         brace_count += line.count('}')
#         brace_count -= line.count('{')
        
#         if brace_count < 0:
#             # Found an unclosed block
#             return i + 1
            
#     return None















#--------------------------------------------tries2------------------------------------------------------
 
# def llm(prompt, model_name):
#     """
#     Enhanced LLM function with robust output response handling
    
#     Args:
#         prompt (str): The input prompt to send to the model
#         model_name (str): Name of the model to use
        
#     Returns:
#         str: The complete response with proper code generation
#     """
#     try:
#         conversation = initialize_conversation(model_name)
        
#         # Generate initial response
#         full_response = conversation.predict(input=prompt)
        
#         # Track response completeness
#         response_metadata = {
#             'attempts': 0,
#             'max_attempts': 5,
#             'token_count': len(full_response.split()),
#             'code_blocks': {
#                 'class': 0,
#                 'method': 0,
#                 'braces': 0
#             },
#             'last_meaningful_length': 0
#         }
        
#         # Create progress bar
#         if st.session_state.get('show_progress', True):
#             progress_bar = st.progress(0)
#             status_text = st.empty()
        
#         while should_continue_generation(full_response, response_metadata):
#             try:
#                 continuation_prompt = generate_smart_continuation_prompt(full_response, response_metadata)
#                 continuation = conversation.predict(input=continuation_prompt)
                
#                 if is_valid_continuation(continuation, full_response, response_metadata):
#                     full_response = append_continuation(full_response, continuation, response_metadata)
                    
#                     # Update progress
#                     if st.session_state.get('show_progress', True):
#                         progress = min(1.0, response_metadata['attempts'] / response_metadata['max_attempts'])
#                         progress_bar.progress(progress)
#                         status_text.text(f"Generating response... {int(progress * 100)}%")
                        
#                         if is_code_complete(full_response):
#                             status_text.text("Code generation completed successfully!")
#                 else:
#                     break
                    
#             except Exception as e:
#                 st.warning(f"Continuation error: {str(e)}")
#                 break
        
#         # Final validation and cleanup
#         final_response = post_process_code_response(full_response)
#         validate_final_response(final_response)
        
#         return final_response
        
#     except Exception as e:
#         st.error(f"Error in response generation: {str(e)}")
#         return None



# def has_unmatched_braces(response):
#     """
#     Check for unmatched braces in the code
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         bool: True if there are unmatched braces, False otherwise
#     """
#     stack = []
    
#     for char in response:
#         if char == '{':
#             stack.append(char)
#         elif char == '}':
#             if not stack:
#                 return True  # Closing brace without matching opening brace
#             stack.pop()
    
#     return len(stack) > 0  # True if there are unclosed braces

# def ends_with_incomplete_statement(response):
#     """
#     Check if the code ends with an incomplete statement
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         bool: True if the code ends with an incomplete statement
#     """
#     # Remove trailing whitespace and get last line
#     last_line = response.strip().split('\n')[-1].strip()
    
#     # Indicators of incomplete statements
#     incomplete_indicators = [
#         # Ends with common statement continuations
#         last_line.endswith(('{', '(', ',', ';', ':')),
        
#         # Common keywords that suggest incomplete statements
#         any(last_line.endswith(keyword) for keyword in [
#             'return', 'new', 'throw', 'throws', 'extends', 'implements',
#             'public', 'private', 'protected', 'static', 'final',
#             'void', 'class', 'interface'
#         ]),
        
#         # Operators that suggest incomplete expressions
#         any(last_line.endswith(op) for op in [
#             '+', '-', '*', '/', '%', '=', '==', '!=', '<', '>', '<=', '>=',
#             '&&', '||', '&', '|', '^', '<<', '>>'
#         ]),
        
#         # Check for incomplete string or character literals
#         last_line.count('"') % 2 == 1,
#         last_line.count("'") % 2 == 1
#     ]
    
#     return any(incomplete_indicators)

# def is_class_incomplete(response):
#     """
#     Check if any class definition is incomplete
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         bool: True if there are incomplete class definitions
#     """
#     lines = response.split('\n')
#     class_count = 0
#     class_closure_count = 0
#     in_class = False
    
#     for line in lines:
#         stripped_line = line.strip()
        
#         # Count class definitions
#         if 'class ' in stripped_line and not stripped_line.startswith('//'): 
#             class_count += 1
#             in_class = True
            
#         # Count potential class closures
#         if stripped_line.startswith('}') and in_class:
#             class_closure_count += 1
#             in_class = False
            
#         # Check for inner classes
#         if in_class and 'class ' in stripped_line and not stripped_line.startswith('class '):
#             class_count += 1
    
#     return class_count > class_closure_count

# def is_method_incomplete(response):
#     """
#     Check if any method definition is incomplete
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         bool: True if there are incomplete method definitions
#     """
#     lines = response.split('\n')
#     method_stack = []
#     in_comment = False
    
#     for line in lines:
#         stripped_line = line.strip()
        
#         # Skip comments
#         if stripped_line.startswith('/*'):
#             in_comment = True
#             continue
#         if stripped_line.endswith('*/'):
#             in_comment = False
#             continue
#         if in_comment or stripped_line.startswith('//'):
#             continue
            
#         # Method declaration indicators
#         method_indicators = [
#             'public ', 'private ', 'protected ', 'void ', 
#             'static ', 'final ', '@Override'
#         ]
        
#         # Check for method declarations
#         if any(indicator in line for indicator in method_indicators) and '(' in line:
#             if '{' in line:
#                 method_stack.append('method')
#             elif not line.endswith(';'):  # Not a method reference/abstract method
#                 return True  # Incomplete method declaration
        
#         # Count braces for method body tracking
#         if '{' in line:
#             method_stack.append('{')
#         if '}' in line and method_stack:
#             method_stack.pop()
    
#     return len(method_stack) > 0

# def is_code_complete(response):
#     """
#     Comprehensive check for code completeness
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         bool: True if the code appears complete, False otherwise
#     """
#     if not response.strip():
#         return False
        
#     completeness_checks = {
#         'balanced_braces': not has_unmatched_braces(response),
#         'complete_statements': not ends_with_incomplete_statement(response),
#         'complete_classes': not is_class_incomplete(response),
#         'complete_methods': not is_method_incomplete(response),
#         'proper_ending': response.strip().endswith('}'),
#         'basic_structure': all([
#             'class ' in response,  # Has at least one class
#             'public' in response,  # Has access modifiers
#             '{' in response and '}' in response  # Has code blocks
#         ])
#     }
    
#     # Additional syntax checks
#     syntax_checks = {
#         'no_dangling_else': response.count('if') >= response.count('else'),
#         'no_unclosed_strings': response.count('"') % 2 == 0,
#         'no_unclosed_chars': response.count("'") % 2 == 0,
#         'balanced_parentheses': response.count('(') == response.count(')')
#     }
    
#     # Log issues for debugging
#     failed_checks = [check for check, passed in {**completeness_checks, **syntax_checks}.items() 
#                     if not passed]
#     if failed_checks:
#         st.debug(f"Code incompleteness indicators: {', '.join(failed_checks)}")
    
#     return all(completeness_checks.values()) and all(syntax_checks.values())

# def get_completion_status(response):
#     """
#     Get detailed status about code completion
    
#     Args:
#         response (str): The code response to check
        
#     Returns:
#         dict: Detailed status of various completion checks
#     """
#     status = {
#         'has_unmatched_braces': has_unmatched_braces(response),
#         'ends_with_incomplete_statement': ends_with_incomplete_statement(response),
#         'has_incomplete_classes': is_class_incomplete(response),
#         'has_incomplete_methods': is_method_incomplete(response),
#         'is_complete': is_code_complete(response)
#     }
    
#     # Add detailed counts
#     status.update({
#         'class_count': response.count('class '),
#         'method_count': sum(1 for line in response.split('\n') 
#                           if any(mod in line for mod in ['public ', 'private ', 'protected ']) 
#                           and '(' in line),
#         'brace_count': {
#             'opening': response.count('{'),
#             'closing': response.count('}')
#         }
#     })
    
#     return status

# def should_continue_generation(response, metadata):
#     """
#     Determine if response generation should continue
#     """
#     if metadata['attempts'] >= metadata['max_attempts']:
#         return False
        
#     # Check for incomplete code indicators
#     incomplete_indicators = [
#         not is_code_complete(response),
#         has_unmatched_braces(response),
#         ends_with_incomplete_statement(response),
#         is_class_incomplete(response),
#         is_method_incomplete(response)
#     ]
    
#     metadata['attempts'] += 1
#     return any(incomplete_indicators)

# def is_code_complete(response):
#     """
#     Check if the generated code is complete
#     """
#     # Count code structure indicators
#     class_count = response.count('class ')
#     class_end_count = len([line for line in response.split('\n') 
#                           if line.strip().startswith('}') and 
#                           'class' in response[:response.find(line)]])
    
#     # Check basic completion indicators
#     basic_checks = [
#         response.strip().endswith('}'),
#         class_count == class_end_count,
#         response.count('{') == response.count('}'),
#         not response.strip().endswith((':', ';', '{', '(', ',')),
#         not any(keyword in response.splitlines()[-1].lower() 
#                 for keyword in ['public', 'private', 'protected', 'class', 'void', 'return'])
#     ]
    
#     return all(basic_checks)

# def generate_smart_continuation_prompt(previous_response, metadata):
#     """
#     Generate context-aware continuation prompt
#     """
#     # Analyze the last part of the response
#     last_context = previous_response[-300:]
#     incomplete_elements = analyze_incomplete_elements(previous_response)
    
#     prompt_elements = [
#         "Continue the Java code generation, maintaining consistency with the previous output.",
#         f"Context from last output: ```java\n{last_context}\n```"
#     ]
    
#     if incomplete_elements:
#         prompt_elements.append(f"Complete the following elements: {', '.join(incomplete_elements)}")
    
#     if metadata['attempts'] > 2:
#         prompt_elements.append("Focus on completing open code blocks and ensuring proper method/class closure.")
    
#     return "\n".join(prompt_elements)

# def analyze_incomplete_elements(response):
#     """
#     Analyze what elements need completion
#     """
#     incomplete = []
    
#     # Check for incomplete class definitions
#     if response.count('class ') > response.count('\n}'):
#         incomplete.append('class definition')
    
#     # Check for incomplete methods
#     if (response.count('public ') + response.count('private ') + 
#         response.count('protected ')) > response.count('\n    }'):
#         incomplete.append('method definition')
    
#     # Check for open try-catch blocks
#     if response.count('try {') > response.count('} catch'):
#         incomplete.append('try-catch block')
    
#     return incomplete

# def is_valid_continuation(continuation, previous_response, metadata):
#     """
#     Validate if the continuation is meaningful
#     """
#     if len(continuation.strip()) < 10:
#         return False
        
#     # Check for duplicated content
#     last_lines = previous_response.split('\n')[-5:]
#     continuation_lines = continuation.split('\n')[:5]
    
#     if any(line.strip() in last_lines for line in continuation_lines):
#         return False
    
#     # Check for meaningful progress
#     current_length = len(continuation.strip())
#     if current_length <= metadata['last_meaningful_length'] * 0.1:  # Less than 10% of last chunk
#         return False
        
#     metadata['last_meaningful_length'] = current_length
#     return True

# def append_continuation(base_response, continuation, metadata):
#     """
#     Intelligently append continuation to base response
#     """
#     # Clean up continuation
#     continuation = continuation.strip()
    
#     # Remove duplicate line endings
#     while continuation and base_response.strip().endswith(continuation[:50].strip()):
#         continuation = continuation[50:].strip()
    
#     # Add proper spacing
#     if continuation:
#         if not base_response.endswith('\n'):
#             base_response += '\n'
#         base_response += continuation
    
#     return base_response




# import itertools

# def post_process_code_response(response):
#     """
#     Clean and format the final code response
#     """
#     lines = response.split('\n')
#     formatted_lines = []
#     indent_level = 0
    
#     for line in lines:
#         # Adjust indentation based on braces
#         stripped = line.strip()
#         if stripped.endswith('{'):
#             formatted_lines.append('    ' * indent_level + stripped)
#             indent_level += 1
#         elif stripped.startswith('}'):
#             indent_level = max(0, indent_level - 1)
#             formatted_lines.append('    ' * indent_level + stripped)
#         else:
#             formatted_lines.append('    ' * indent_level + stripped)
    
#     # Clean up multiple blank lines using itertools.groupby
#     result = '\n'.join(formatted_lines)
#     result = '\n'.join(line for line, _ in itertools.groupby(result.splitlines()))
    
#     return result

# def validate_final_response(response):
#     """
#     Perform final validation checks on the response
#     """
#     if not response:
#         st.warning("Generated response is empty")
#         return
    
#     # Check for critical code elements
#     validations = {
#         'Has class definition': 'class ' in response,
#         'Proper class closure': response.count('class ') == response.count('\n}'),
#         'Balanced braces': response.count('{') == response.count('}'),
#         'No incomplete methods': not any(line.strip().endswith((':', '{')) 
#                                        for line in response.splitlines()),
#     }
    
#     # Report validation results
#     failed_validations = [k for k, v in validations.items() if not v]
#     if failed_validations:
#         st.warning(f"Response may be incomplete. Issues found: {', '.join(failed_validations)}")


#---------------------------------tries3----------------------------------------------------------




























#----------------------------------------tries4--------------------------------------------------


# def llm(prompt, model_name):
#     """
#     Enhanced LLM calling function with improved long response handling
    
#     Args:
#         prompt (str): The input prompt to send to the model
#         model_name (str): Name of the model to use
        
#     Returns:
#         str: The complete response from the model
#     """
#     try:
#         conversation = initialize_conversation(model_name)
        
#         # Generate initial response
#         full_response = conversation.predict(input=prompt)

#         # Track number of continuation attempts to prevent infinite loops
#         continuation_attempts = 0
#         max_attempts = 3  # Limit the number of continuation attempts
                                                                                                                                  
#         # Check if the response seems incomplete
#         while (continuation_attempts < max_attempts and 
#                (len(full_response.split()) >= 900 or  # Close to token limit
#                 full_response.rstrip().endswith(('.', ':', ',')) or  # Ends mid-sentence
#                 not full_response.strip().endswith(('.', '!', '?', '"', "'")))):  # No proper ending
                                                                                                                      
#             # Add context from previous response to maintain coherence
#             continuation_prompt = (
#                 "The previous response may be incomplete. Please continue from where "
#                 "you left off, maintaining the same context and format. "
#                 "Here's the last part of the previous response: "
#                 f"'{full_response[-200:]}'..."
#             )
                                                                                                                                  
#             try:
#                 continuation_response = conversation.predict(input=continuation_prompt)
                                                                                                                            
#                 # Check if we got a meaningful continuation
#                 if len(continuation_response.strip()) < 10:
#                     break  # Break if response is too short (likely complete)
                    
#                 # Append new content while avoiding duplicates
#                 if continuation_response.strip() not in full_response[-200:]:
#                     full_response += "\n" + continuation_response
#                 else:
#                     break  # Break if we're getting duplicate content
                    
#                 continuation_attempts += 1
                                                                                                                                 
#                 # Optional: Add progress indicator
#                 if st.session_state.get('show_progress', True):
#                     st.write(f"Generating continuation {continuation_attempts}/{max_attempts}...")
                
#             except Exception as e:
#                 st.warning(f"Continuation attempt {continuation_attempts + 1} failed: {str(e)}")
#                 break
                
#         if continuation_attempts >= max_attempts:
#             st.warning("Reached maximum number of continuation attempts. Response may be truncated.")
            
#         return full_response.strip()
 
#     except Exception as e:
#         st.error(f"Error calling model: {str(e)}")
#         return None
    
    
    
    
    

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
        
# In your main code
# if add_radio == "/generate_java_code":
#     st.title("/generate_java_code")
#     for file in file_content:
#         response = execute(selected_model, java_code_gen_prompt, file)
#         if response:
#             st.write(response, language='java')  # Display formatted code
#             st.write("\nApproximate word count:", len(response.split()))        


# def execute_with_java_completion(model_name, exec_prompt, code):
#     """
#     Execute LLM with Java code completion handling
#     """
#     final_prompt = PromptTemplate.from_template(exec_prompt)
#     formatted_prompt = final_prompt.format(PLSQL_CODE=code)
#     return llm_with_java_completion(formatted_prompt, model_name)

# if add_radio == "/generate_java_code":
#     st.title("/generate_java_code")
#     for file in file_content:
#         response = execute_with_java_completion(selected_model, java_code_gen_prompt, file)
#         if response:
#             st.write(response, language='java')
#             st.write("\nApproximate word count:", len(response.split()))



if add_radio == "/generate_java_code":
    st.title("/generate_java_code")
    for file in file_content:
        final_prompt = PromptTemplate.from_template(java_code_gen_prompt)
        formatted_prompt = final_prompt.format(PLSQL_CODE=file)
        response = generate_complete_response(formatted_prompt, selected_model)
        if response:
            st.write(response, language='java')
            st.write("\nApproximate word count:", len(response.split()))