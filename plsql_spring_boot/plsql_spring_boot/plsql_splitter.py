import re
from typing import List, Dict
from dataclasses import dataclass
from pathlib import Path

@dataclass
class PLSQLChunk:
    content: str
    chunk_type: str  # PACKAGE_SPEC, PACKAGE_BODY, PROCEDURE, FUNCTION, TABLE, TRIGGER
    name: str
    package_name: str = None
    signature: str = None
    dependencies: List[str] = None
    parent_object: str = None
    file_path: str = None
    context: str = None

def split_plsql_for_vectordb(file_path: str) -> List[PLSQLChunk]:
    """
    Split PL/SQL file into chunks while preserving complete context for vector embedding.
    Handles packages, standalone procedures/functions, triggers, and table definitions.
    """
    with open(file_path, 'r') as f:
        content = f.read()
    
    chunks = []
    file_name = Path(file_path).name
    
    # First chunk: Complete file as-is for full context
    chunks.append(PLSQLChunk(
        content=content,
        chunk_type="COMPLETE_FILE",
        name=file_name,
        file_path=file_path,
        context="Complete SQL file content"
    ))
    
    # Handle different SQL object types
    if "CREATE TABLE" in content.upper():
        chunks.extend(_split_table_definitions(content, file_path))
    
    if "CREATE TRIGGER" in content.upper():
        chunks.extend(_split_triggers(content, file_path))
    
    if "CREATE PACKAGE" in content.upper():
        chunks.extend(_split_package(content, file_path))
    
    return chunks

def _split_package(content: str, file_path: str) -> List[PLSQLChunk]:
    """Split package into logical components while maintaining context."""
    chunks = []
    package_name = _extract_package_name(content)
    
    # Package Specification
    spec_match = re.search(
        r'(CREATE\s+OR\s+REPLACE\s+PACKAGE\s+.*?END\s+\w+;)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    if spec_match:
        spec_content = spec_match.group(1)
        chunks.append(PLSQLChunk(
            content=spec_content,
            chunk_type="PACKAGE_SPEC",
            name=package_name,
            file_path=file_path,
            context="Package Specification"
        ))
        
        # Extract interface definitions
        for proc_match in re.finditer(r'(PROCEDURE|FUNCTION)\s+(\w+)([^;]+;)', spec_content, re.IGNORECASE):
            chunks.append(PLSQLChunk(
                content=proc_match.group(0),
                chunk_type=f"SPEC_{proc_match.group(1).upper()}",
                name=proc_match.group(2),
                package_name=package_name,
                signature=proc_match.group(0),
                parent_object=package_name,
                file_path=file_path,
                context="Interface Definition"
            ))
    
    # Package Body
    body_match = re.search(
        r'(CREATE\s+OR\s+REPLACE\s+PACKAGE\s+BODY\s+.*?END\s+\w+;)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    if body_match:
        body_content = body_match.group(1)
        chunks.append(PLSQLChunk(
            content=body_content,
            chunk_type="PACKAGE_BODY",
            name=package_name,
            file_path=file_path,
            context="Package Body"
        ))
        
        # Extract implementations with complete context
        for impl_match in re.finditer(
            r'((/\*.*?\*/\s*)?)(PROCEDURE|FUNCTION)\s+(\w+)([^;]+?END\s+\4;)',
            body_content,
            re.IGNORECASE | re.DOTALL
        ):
            proc_name = impl_match.group(4)
            proc_content = impl_match.group(0)
            
            # Get dependencies
            dependencies = _extract_dependencies(proc_content)
            
            # Split into logical parts while maintaining complete context
            declaration_part, body_part = _split_proc_implementation(proc_content)
            
            # Add complete procedure
            chunks.append(PLSQLChunk(
                content=proc_content,
                chunk_type=impl_match.group(3).upper(),
                name=proc_name,
                package_name=package_name,
                signature=_extract_signature(proc_content),
                dependencies=dependencies,
                parent_object=package_name,
                file_path=file_path,
                context="Complete Implementation"
            ))
            
            # Add declaration part if significant
            if declaration_part:
                chunks.append(PLSQLChunk(
                    content=declaration_part,
                    chunk_type="DECLARATION",
                    name=proc_name,
                    package_name=package_name,
                    parent_object=package_name,
                    file_path=file_path,
                    context="Variable Declarations"
                ))
            
            # Split body into logical chunks
            body_chunks = _split_proc_body(body_part, proc_name)
            chunks.extend(body_chunks)
            
    return chunks

def _split_table_definitions(content: str, file_path: str) -> List[PLSQLChunk]:
    """Extract and split table definitions."""
    chunks = []
    for table_match in re.finditer(
        r'CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);',
        content,
        re.IGNORECASE | re.DOTALL
    ):
        table_name = table_match.group(1)
        chunks.append(PLSQLChunk(
            content=table_match.group(0),
            chunk_type="TABLE",
            name=table_name,
            file_path=file_path,
            context="Table Definition"
        ))
    return chunks

def _split_triggers(content: str, file_path: str) -> List[PLSQLChunk]:
    """Extract and split triggers."""
    chunks = []
    for trigger_match in re.finditer(
        r'CREATE\s+(?:OR\s+REPLACE\s+)?TRIGGER\s+(\w+).*?(?:END\s+\1;|/)',
        content,
        re.IGNORECASE | re.DOTALL
    ):
        trigger_name = trigger_match.group(1)
        chunks.append(PLSQLChunk(
            content=trigger_match.group(0),
            chunk_type="TRIGGER",
            name=trigger_name,
            file_path=file_path,
            context="Trigger Definition"
        ))
    return chunks

def _extract_dependencies(content: str) -> List[str]:
    """Extract all dependencies from a code block."""
    dependencies = set()
    
    # Table references
    table_patterns = [
        r'\bFROM\s+(\w+)\b',
        r'\bJOIN\s+(\w+)\b',
        r'\bINTO\s+(\w+)\b',
        r'\bUPDATE\s+(\w+)\b',
        r'\bINSERT\s+INTO\s+(\w+)\b',
        r'\bDELETE\s+FROM\s+(\w+)\b'
    ]
    
    for pattern in table_patterns:
        for match in re.finditer(pattern, content, re.IGNORECASE):
            dependencies.add(f"TABLE:{match.group(1)}")
    
    # Package/Procedure calls
    for match in re.finditer(r'\b(\w+\.\w+)\b', content):
        dependencies.add(f"CALL:{match.group(1)}")
    
    return list(dependencies)

def _split_proc_implementation(content: str) -> tuple:
    """Split procedure implementation into declaration and body parts."""
    parts = re.split(r'\bBEGIN\b', content, flags=re.IGNORECASE, maxsplit=1)
    if len(parts) == 2:
        return parts[0].strip(), f"BEGIN{parts[1]}"
    return "", content

def _split_proc_body(body: str, proc_name: str) -> List[PLSQLChunk]:
    """Split procedure body into logical chunks while maintaining context."""
    chunks = []
    
    # Split on major control structures but keep them together with their content
    control_blocks = re.split(r'(\b(?:IF|LOOP|FOR|WHILE|CASE)\b.*?\bEND\s+\w+;)', body, flags=re.IGNORECASE | re.DOTALL)
    
    current_chunk = []
    for block in control_blocks:
        current_chunk.append(block)
        if len(''.join(current_chunk)) > 1000:  # Approximate chunk size
            chunks.append(PLSQLChunk(
                content=''.join(current_chunk),
                chunk_type="CODE_BLOCK",
                name=proc_name,
                context="Logic Block"
            ))
            current_chunk = []
    
    if current_chunk:
        chunks.append(PLSQLChunk(
            content=''.join(current_chunk),
            chunk_type="CODE_BLOCK",
            name=proc_name,
            context="Logic Block"
        ))
    
    return chunks

def _extract_package_name(content: str) -> str:
    """Extract package name from content."""
    match = re.search(r'CREATE\s+OR\s+REPLACE\s+PACKAGE\s+(\w+)', content, re.IGNORECASE)
    return match.group(1) if match else "UNKNOWN"

def _extract_signature(content: str) -> str:
    """Extract procedure/function signature."""
    match = re.match(
        r'(?:PROCEDURE|FUNCTION)\s+\w+[^;]+?(?=\s+IS|\s+AS|\s+BEGIN)',
        content,
        re.IGNORECASE | re.DOTALL
    )
    return match.group(0) if match else ""
