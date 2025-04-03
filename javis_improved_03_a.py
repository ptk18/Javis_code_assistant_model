import re
import ast
import textwrap
from typing import Dict, List, Tuple, Optional

class FastCodeAssistant:
    """A lightweight, rule-based code modification assistant that doesn't rely on ML models"""
    
    def __init__(self):
        # Define common patterns for code modifications
        self.patterns = {
            "add_method": re.compile(r"add\s+(?:a\s+)?method\s+called\s+(\w+)(?:\s+with\s+parameter\s+(\w+))?", re.IGNORECASE),
            "add_loop": re.compile(r"(?:add|put)\s+(?:a\s+)?(?:for|while)\s+loop\s+(?:in(?:side)?|to)\s+(?:the\s+)?method\s+(\w+)", re.IGNORECASE),
            "add_if": re.compile(r"add\s+(?:a\s+)?(?:if|conditional)\s+(?:statement\s+)?(?:in(?:side)?|to)\s+(?:the\s+)?method\s+(\w+)", re.IGNORECASE),
        }
    
    def parse_code(self, code_string: str) -> Optional[ast.Module]:
        """Parse code string into AST"""
        try:
            return ast.parse(code_string)
        except SyntaxError:
            print("Error parsing code")
            return None
    
    def find_class(self, tree: ast.Module, class_name: Optional[str] = None) -> Optional[ast.ClassDef]:
        """Find a class in the AST by name, or return the first one if no name is provided"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                if class_name is None or node.name == class_name:
                    return node
        return None
    
    def find_method(self, class_node: ast.ClassDef, method_name: str) -> Optional[ast.FunctionDef]:
        """Find a method in a class by name"""
        for node in class_node.body:
            if isinstance(node, ast.FunctionDef) and node.name == method_name:
                return node
        return None
    
    def get_code_segment(self, code_string: str, node: ast.AST) -> str:
        """Extract the code segment corresponding to an AST node"""
        lines = code_string.split('\n')
        return '\n'.join(lines[node.lineno-1:node.end_lineno])
    
    def add_method_to_class(self, code_string: str, class_name: str, method_name: str, 
                          param_name: Optional[str] = None) -> str:
        """Add a new method to a class"""
        tree = self.parse_code(code_string)
        if not tree:
            return code_string
        
        class_node = self.find_class(tree, class_name)
        if not class_node:
            print(f"Class {class_name} not found")
            return code_string
        
        # Create the new method code
        param_str = f", {param_name}" if param_name else ""
        new_method = f"    def {method_name}(self{param_str}):\n        pass"
        
        # Find where to insert the new method
        lines = code_string.split('\n')
        class_end_line = class_node.end_lineno
        
        # Insert the new method before the end of the class
        result_lines = lines[:class_end_line]
        result_lines.append(new_method)
        if class_end_line < len(lines):
            result_lines.extend(lines[class_end_line:])
        
        return '\n'.join(result_lines)
    
    def add_loop_to_method(self, code_string: str, method_name: str, 
                         loop_type: str = "for", class_name: Optional[str] = None) -> str:
        """Add a loop to a method"""
        tree = self.parse_code(code_string)
        if not tree:
            return code_string
        
        # Find the class
        class_node = self.find_class(tree, class_name)
        if not class_node:
            print("Target class not found")
            return code_string
        
        # Find the method
        method_node = self.find_method(class_node, method_name)
        if not method_node:
            print(f"Method {method_name} not found in class {class_node.name}")
            return code_string
        
        # Get method parameters
        params = [arg.arg for arg in method_node.args.args[1:]]  # Skip 'self'
        param_var = params[0] if params else "item"
        
        # Create appropriate loop based on the existing method body
        method_body = [node for node in method_node.body]
        if not method_body or (len(method_body) == 1 and isinstance(method_body[0], ast.Pass)):
            # Empty method body or just 'pass'
            if loop_type == "for":
                loop_code = f"        for i in range(3):\n            print(f\"Processing {{i}} of {{{param_var}}}\")"
            else:  # while loop
                loop_code = f"        count = 0\n        while count < 3:\n            print(f\"Processing {{count}} of {{{param_var}}}\")\n            count += 1"
        else:
            # Extract existing method body and indent it inside the loop
            method_lines = self.get_code_segment(code_string, method_node).split('\n')[1:]  # Skip method definition
            indented_body = '\n'.join(['            ' + line.lstrip() for line in method_lines if line.strip()])
            
            if loop_type == "for":
                loop_code = f"        for i in range(3):\n{indented_body}"
            else:  # while loop
                loop_code = f"        count = 0\n        while count < 3:\n{indented_body}\n            count += 1"
        
        # Replace the method body
        lines = code_string.split('\n')
        method_def_line = lines[method_node.lineno-1]
        method_body_start = method_node.body[0].lineno if method_node.body else method_node.lineno + 1
        method_body_end = method_node.end_lineno
        
        # This is the fix - don't duplicate the method declaration line
        result_lines = lines[:method_node.lineno-1]  # Get everything before the method
        result_lines.append(method_def_line)  # Add the method declaration once
        result_lines.append(loop_code)  # Add the loop code
        result_lines.extend(lines[method_body_end:])  # Add everything after the method
        
        return '\n'.join(result_lines)
    
    def analyze_command(self, command: str) -> Tuple[str, Dict]:
        """Analyze a command and determine what code modification to apply"""
        # Check for add method pattern
        match = self.patterns["add_method"].search(command)
        if match:
            method_name = match.group(1)
            param_name = match.group(2) if match.group(2) else None
            return "add_method", {"method_name": method_name, "param_name": param_name}
        
        # Check for add loop pattern
        match = self.patterns["add_loop"].search(command)
        if match:
            method_name = match.group(1)
            # Determine if for or while loop (default to for)
            loop_type = "for" if "for" in command.lower() else "while"
            return "add_loop", {"method_name": method_name, "loop_type": loop_type}
        
        # Check for add if pattern
        match = self.patterns["add_if"].search(command)
        if match:
            method_name = match.group(1)
            return "add_if", {"method_name": method_name}
        
        # Default response for unrecognized commands
        return "unknown", {}
    
    def modify_code(self, code_string: str, command: str) -> str:
        """Main method to modify code based on natural language command"""
        # Clean up and standardize input code
        code_string = textwrap.dedent(code_string).strip()
        
        # Analyze the command
        operation, params = self.analyze_command(command)
        
        # Extract class name if mentioned in command
        class_match = re.search(r"(?:in|to|from)\s+(?:the\s+)?(\w+)\s+class", command, re.IGNORECASE)
        class_name = class_match.group(1) if class_match else None
        
        # If no class specified, try to find the first class in the code
        if not class_name:
            tree = self.parse_code(code_string)
            if tree:
                class_node = self.find_class(tree)
                if class_node:
                    class_name = class_node.name
        
        # Apply the appropriate modification
        if operation == "add_method":
            return self.add_method_to_class(
                code_string, 
                class_name, 
                params["method_name"], 
                params["param_name"]
            )
        elif operation == "add_loop":
            return self.add_loop_to_method(
                code_string, 
                params["method_name"], 
                params["loop_type"], 
                class_name
            )
        else:
            print(f"Operation {operation} not supported or recognized")
            return code_string

# Example usage
def main():
    # Create the fast code assistant
    assistant = FastCodeAssistant()
    
    # Initial code example
    initial_code = textwrap.dedent("""
    class Animal:
        def __init__(self):
            pass
        def sound(self):
            return "generic sound"
    """)
    
    # Example 1: Add a method
    command1 = "Add a method called eat with parameter food to Animal class"
    start_time = __import__('time').time()
    modified_code = assistant.modify_code(initial_code, command1)
    duration1 = __import__('time').time() - start_time
    print(f"Modified code after adding method (took {duration1:.3f} seconds):")
    print(modified_code)
    
    # Example 2: Add a loop to the newly created method
    command2 = "Put a for loop inside the method eat from Animal class"
    start_time = __import__('time').time()
    modified_code2 = assistant.modify_code(modified_code, command2)
    duration2 = __import__('time').time() - start_time
    print(f"\nModified code after adding loop (took {duration2:.3f} seconds):")
    print(modified_code2)

if __name__ == "__main__":
    main()