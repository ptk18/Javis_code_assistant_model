import ast
import sys
import json
from typing import Dict, List, Any

class CodeStructureExtractor:
    def __init__(self, code: str):
        """Initialize the extractor with Python code as a string."""
        self.code = code
        try:
            self.tree = ast.parse(code)
            self.parsing_error = None
        except SyntaxError as e:
            self.parsing_error = e
            self.tree = None
        
    def extract_structure(self) -> Dict[str, Any]:
        """Extract the structure of the code (classes, functions, methods, attributes)."""
        if self.parsing_error:
            return {
                "status": "error",
                "message": f"Syntax error: {self.parsing_error}",
                "line": self.parsing_error.lineno,
                "offset": self.parsing_error.offset
            }
        
        # Initialize structure containers
        structure = {
            "status": "success",
            "classes": {},
            "functions": [],
            "imports": []
        }
        
        # Extract top-level elements
        for node in ast.iter_child_nodes(self.tree):
            # Extract functions
            if isinstance(node, ast.FunctionDef):
                structure["functions"].append({
                    "name": node.name,
                    "location": self._get_node_location(node),
                    "arguments": [arg.arg for arg in node.args.args]
                })
            
            # Extract classes
            elif isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "location": self._get_node_location(node),
                    "bases": [self._get_base_name(base) for base in node.bases],
                    "methods": [],
                    "attributes": []
                }
                
                # Extract methods and attributes from class body
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        method_info = {
                            "name": item.name,
                            "location": self._get_node_location(item),
                            "arguments": [arg.arg for arg in item.args.args]
                        }
                        class_info["methods"].append(method_info)
                        
                        # Extract attribute assignments in methods, especially __init__
                        if item.name == "__init__":
                            for stmt in item.body:
                                if isinstance(stmt, ast.Assign):
                                    for target in stmt.targets:
                                        if isinstance(target, ast.Attribute) and \
                                           isinstance(target.value, ast.Name) and \
                                           target.value.id == "self":
                                            class_info["attributes"].append({
                                                "name": target.attr,
                                                "location": self._get_node_location(stmt)
                                            })
                
                structure["classes"][node.name] = class_info
            
            # Extract imports
            elif isinstance(node, ast.Import):
                for name in node.names:
                    structure["imports"].append({
                        "name": name.name,
                        "alias": name.asname,
                        "type": "import"
                    })
            elif isinstance(node, ast.ImportFrom):
                for name in node.names:
                    structure["imports"].append({
                        "name": name.name,
                        "alias": name.asname,
                        "module": node.module,
                        "type": "from_import"
                    })
                    
        return structure
    
    def _get_base_name(self, node):
        """Extract the name of a base class from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Handle cases like module.ClassName
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.insert(0, current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.insert(0, current.id)
            return '.'.join(parts)
        return str(node)  # Fallback for other cases
    
    def _get_node_location(self, node) -> Dict:
        """Get the location information for a node."""
        return {
            "line_start": node.lineno,
            "line_end": node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            "col_start": node.col_offset,
            "col_end": node.end_col_offset if hasattr(node, 'end_col_offset') else node.col_offset
        }

def extract_code_structure(code: str) -> Dict:
    """
    Extract the structure of Python code and return information about classes, functions, methods, and attributes.
    
    Args:
        code: A string containing Python code to analyze
        
    Returns:
        A dictionary with structure information
    """
    extractor = CodeStructureExtractor(code)
    return extractor.extract_structure()

def extract_from_file(filename: str) -> Dict:
    """
    Extract code structure from a file.
    
    Args:
        filename: Path to the Python file to analyze
    
    Returns:
        A dictionary with structure information
    """
    try:
        with open(filename, 'r') as f:
            code = f.read()
        return extract_code_structure(code)
    except FileNotFoundError:
        return {
            "status": "error",
            "message": f"File not found: {filename}"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error reading file: {str(e)}"
        }

# This part runs when the script is executed directly
if __name__ == "__main__":
    # Example usage
    if len(sys.argv) > 1:
        # Extract structure from file
        result = extract_from_file(sys.argv[1])
        print(json.dumps(result, indent=2))
    else:
        # Example code for demonstration
        example_code = """
class Animal:
    species_count = 0
    
    def __init__(self, name, age):
        self.name = name
        self.age = age
        Animal.species_count += 1
    
    def speak(self):
        print("Some sound")

class Dog(Animal):
    def __init__(self, name, age, breed):
        super().__init__(name, age)
        self.breed = breed
    
    def speak(self):
        print("Woof!")

def calculate_animal_stats(animals):
    total_age = 0
    for animal in animals:
        total_age += animal.age
    return total_age / len(animals)
"""
        result = extract_code_structure(example_code)
        print(json.dumps(result, indent=2))