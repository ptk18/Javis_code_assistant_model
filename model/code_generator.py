import json
from typing import Dict, List, Any, Tuple

class CodeGenerator:
    def __init__(self):
        self.original_code_lines = []
        self.code_analysis = {}
        self.intent = {}
        
    def load_code(self, code: str):
        """Load the original code to be modified."""
        self.original_code_lines = code.split('\n')
        
    def load_analysis(self, analysis_json: str):
        """Load the code analysis output."""
        if isinstance(analysis_json, str):
            self.code_analysis = json.loads(analysis_json)
        else:
            self.code_analysis = analysis_json
            
    def load_intent(self, intent_json: str):
        """Load the command intent output."""
        if isinstance(intent_json, str):
            self.intent = json.loads(intent_json)
        else:
            self.intent = intent_json
            
    def get_indentation(self, line: str) -> str:
        """Extract the indentation from a line."""
        return line[:len(line) - len(line.lstrip())]
    
    def get_class_indentation(self, class_name: str) -> str:
        """Get standard indentation for a class."""
        if class_name not in self.code_analysis.get('classes', {}):
            return "    "  # Default indentation
            
        class_info = self.code_analysis['classes'][class_name]
        
        # Try to get indentation from a method
        if class_info.get('methods'):
            first_method = class_info['methods'][0]
            line_index = first_method['location']['line_start'] - 1
            if 0 <= line_index < len(self.original_code_lines):
                return self.get_indentation(self.original_code_lines[line_index])
        
        return "    "  # Default indentation
    
    def add_method(self) -> str:
        """Handle the add_method intent."""
        if self.intent.get('action') != 'add_method':
            return "Error: Intent is not add_method"
            
        method_name = self.intent.get('method_name')
        target_class = self.intent.get('target_class')
        parameters_raw = self.intent.get('parameters', [])
        
        # Process parameters - assuming the first parameter contains the parameters list
        if len(parameters_raw) > 0:
            param_text = parameters_raw[0]
            # Extract parameter name from text like "food to Animal class"
            param_parts = param_text.split(" to ")
            if len(param_parts) > 0:
                parameters = param_parts[0].strip().split(", ")
            else:
                parameters = []
        else:
            parameters = []
        
        # Find the target class
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        class_end_line = class_info['location']['line_end']
        
        # Get indentation from an existing method or use standard indentation
        indentation = self.get_class_indentation(target_class)
        
        # Create the new method definition
        param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
        new_method = f"{indentation}def {method_name}({param_str}):\n{indentation}    pass"
        
        # Insert the new method at the end of the class
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(class_end_line, new_method)
        
        return '\n'.join(modified_lines)
    
    def remove_method(self) -> str:
        """Handle the remove_method intent with case-insensitive class matching."""
        if self.intent.get('action') != 'remove_method':
            return "Error: Intent is not remove_method"
                
        method_name = self.intent.get('method_name')
        target_class = self.intent.get('target_class')
        
        # Case-insensitive lookup of the class
        actual_class_name = None
        if target_class:
            target_class_lower = target_class.lower()
            for class_name in self.code_analysis.get('classes', {}):
                if class_name.lower() == target_class_lower:
                    actual_class_name = class_name
                    break
        
        if not actual_class_name:
            return f"Error: Class {target_class} not found"
                
        class_info = self.code_analysis['classes'][actual_class_name]
        
        # Find the method to remove (case-insensitive)
        method_to_remove = None
        for method in class_info.get('methods', []):
            if method['name'].lower() == method_name.lower():
                method_to_remove = method
                break
                    
        if not method_to_remove:
            return f"Error: Method {method_name} not found in class {actual_class_name}"
                
        # Get the line range to remove
        start_line = method_to_remove['location']['line_start'] - 1
        end_line = method_to_remove['location']['line_end']
        
        # Remove the method lines
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
    
    def add_class(self) -> str:
        """Handle the add_class intent."""
        if self.intent.get('action') != 'add_class':
            return "Error: Intent is not add_class"
                
        class_name = self.intent.get('class_name')
        if not class_name:
            return "Error: Missing class name"
            
        base_classes = self.intent.get('base_classes', [])
        methods = self.intent.get('methods', [])
        attributes = self.intent.get('attributes', [])
        
        # Find insertion point - usually after the last class or at the end of the file
        insertion_line = len(self.original_code_lines)
        for class_info in self.code_analysis.get('classes', {}).values():
            insertion_line = max(insertion_line, class_info['location']['line_end'] + 1)
            
        # Create the class definition
        base_classes_str = f"({', '.join(base_classes)})" if base_classes else ""
        class_def = f"class {class_name}{base_classes_str}:"
        
        # Add init method if attributes are specified
        class_body = []
        if attributes:
            init_body = ["self." + attr + " = " + attr for attr in attributes]
            param_str = "self" + (", " + ", ".join(attributes) if attributes else "")
            init_method = f"    def __init__({param_str}):\n        " + "\n        ".join(init_body)
            class_body.append(init_method)
        
        # Add specified methods
        for method in methods:
            method_name = method.get('name', 'unknown_method')
            params = method.get('params', [])
            body = method.get('body', 'pass')
            
            param_str = "self" + (", " + ", ".join(params) if params else "")
            method_str = f"    def {method_name}({param_str}):\n        {body}"
            class_body.append(method_str)
            
        # If no methods or attributes were specified, add a pass statement
        if not class_body:
            class_body = ["    pass"]
            
        # Combine class definition and body
        new_class = class_def + "\n" + "\n\n".join(class_body)
        
        # Insert the new class
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, "\n\n" + new_class)
        
        return '\n'.join(modified_lines)
    
    def remove_class(self) -> str:
        """Handle the remove_class intent."""
        if self.intent.get('action') != 'remove_class':
            return "Error: Intent is not remove_class"
            
        class_name = self.intent.get('class_name')
        
        # Find the class to remove
        if class_name not in self.code_analysis.get('classes', {}):
            return f"Error: Class {class_name} not found"
            
        class_info = self.code_analysis['classes'][class_name]
        
        # Get the line range to remove
        start_line = class_info['location']['line_start'] - 1
        end_line = class_info['location']['line_end']
        
        # Remove the class lines
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
        
    def add_attribute(self) -> str:
        """Handle the add_attribute intent with improved attribute handling."""
        if self.intent.get('action') != 'add_attribute':
            return "Error: Intent is not add_attribute"
                
        target_class = self.intent.get('target_class')
        attribute_name = self.intent.get('attribute_name')
        default_value = self.intent.get('default_value', 'None')
        
        # Validate required fields
        if not target_class:
            return "Error: Missing target class"
            
        if not attribute_name:
            return "Error: Missing attribute name"
        
        # Case-insensitive lookup of the class
        actual_class_name = None
        if target_class:
            target_class_lower = target_class.lower()
            for class_name in self.code_analysis.get('classes', {}):
                if class_name.lower() == target_class_lower:
                    actual_class_name = class_name
                    break
        
        if not actual_class_name:
            return f"Error: Class {target_class} not found"
                
        class_info = self.code_analysis['classes'][actual_class_name]
        
        # Find the __init__ method
        init_method = None
        for method in class_info.get('methods', []):
            if method['name'] == '__init__':
                init_method = method
                break
                
        # Create modified lines from original code
        modified_lines = self.original_code_lines.copy()
                
        if not init_method:
            # No __init__ method exists, need to create one
            indentation = self.get_class_indentation(actual_class_name)
            init_method_str = f"{indentation}def __init__(self, {attribute_name}):\n{indentation}    self.{attribute_name} = {attribute_name}"
            
            # Insert at the beginning of the class
            class_start_line = class_info['location']['line_start']
            modified_lines.insert(class_start_line, init_method_str)
        else:
            # Find where to insert the new attribute
            init_end_line = init_method['location']['line_end'] - 1
            init_line = self.original_code_lines[init_end_line]
            indentation = self.get_indentation(init_line)
            
            # Insert the new attribute assignment
            attribute_line = f"{indentation}self.{attribute_name} = {attribute_name}"
            modified_lines.insert(init_end_line, attribute_line)
            
            # Update the __init__ arguments if not self-initializing
            if self.intent.get('add_parameter', True):
                init_start_line = init_method['location']['line_start'] - 1
                init_def_line = self.original_code_lines[init_start_line]
                
                # Parse the parameter list
                param_start = init_def_line.find('(')
                param_end = init_def_line.find(')')
                if param_start >= 0 and param_end >= 0:
                    params = init_def_line[param_start+1:param_end].strip()
                    if params.endswith(','):
                        new_params = f"{params} {attribute_name}"
                    elif params:
                        new_params = f"{params}, {attribute_name}"
                    else:
                        new_params = "self"
                        
                    new_def_line = init_def_line[:param_start+1] + new_params + init_def_line[param_end:]
                    modified_lines[init_start_line] = new_def_line
        
        return '\n'.join(modified_lines)
        
    def remove_attribute(self) -> str:
        """Handle the remove_attribute intent with improved attribute handling."""
        if self.intent.get('action') != 'remove_attribute':
            return "Error: Intent is not remove_attribute"
                
        target_class = self.intent.get('target_class')
        
        # Get attribute name from either attribute_name or attributes array
        attribute_name = self.intent.get('attribute_name')
        if not attribute_name and 'attributes' in self.intent and len(self.intent['attributes']) > 0:
            attribute_name = self.intent['attributes'][0]
            
        # Validate required fields
        if not target_class:
            return "Error: Missing target class"
            
        if not attribute_name:
            return "Error: Missing attribute name"
        
        # Case-insensitive lookup of the class
        actual_class_name = None
        if target_class:
            target_class_lower = target_class.lower()
            for class_name in self.code_analysis.get('classes', {}):
                if class_name.lower() == target_class_lower:
                    actual_class_name = class_name
                    break
        
        if not actual_class_name:
            return f"Error: Class {target_class} not found"
                
        class_info = self.code_analysis['classes'][actual_class_name]
        
        # Find the attribute to remove (case-insensitive)
        attribute_to_remove = None
        for attr in class_info.get('attributes', []):
            if attr['name'].lower() == attribute_name.lower():
                attribute_to_remove = attr
                break
                
        if not attribute_to_remove:
            return f"Error: Attribute {attribute_name} not found in class {actual_class_name}"
            
        # Remove the attribute assignment line
        modified_lines = self.original_code_lines.copy()
        attr_line = attribute_to_remove['location']['line_start'] - 1
        del modified_lines[attr_line]
        
        # Also remove from __init__ parameters if they exist
        init_method = None
        for method in class_info.get('methods', []):
            if method['name'] == '__init__':
                init_method = method
                break
                
        if init_method:
            # Find if the attribute is in the __init__ parameters
            has_param = False
            for arg in init_method.get('arguments', []):
                if arg.lower() == attribute_name.lower():
                    has_param = True
                    break
                    
            if has_param:
                init_line = init_method['location']['line_start'] - 1
                init_def = modified_lines[init_line]
                
                # Replace parameter in the signature
                param_start = init_def.find('(')
                param_end = init_def.find(')')
                if param_start >= 0 and param_end >= 0:
                    # Split and process parameters
                    param_text = init_def[param_start+1:param_end]
                    params = [p.strip() for p in param_text.split(',')]
                    
                    # Remove the attribute from parameters
                    new_params = []
                    for p in params:
                        if p.strip().lower() != attribute_name.lower():
                            new_params.append(p)
                            
                    new_def = init_def[:param_start+1] + ', '.join(new_params) + init_def[param_end:]
                    modified_lines[init_line] = new_def
        
        return '\n'.join(modified_lines)
    
    def rename_class(self) -> str:
        """Handle the rename_class intent with preserved indentation."""
        if self.intent.get('action') != 'rename_class':
            return "Error: Intent is not rename_class"
            
        # Get class names from intent
        old_name = self.intent.get('old_name', self.intent.get('target_class'))
        new_name = self.intent.get('new_name', self.intent.get('new_class_name'))
        
        if not old_name or not new_name:
            return "Error: Missing old or new class name"
        
        # Case-insensitive lookup of the class
        actual_class_name = None
        if old_name:
            old_name_lower = old_name.lower()
            for class_name in self.code_analysis.get('classes', {}):
                if class_name.lower() == old_name_lower:
                    actual_class_name = class_name
                    break
        
        if not actual_class_name:
            # Try alternative field if available
            if 'target_class' in self.intent and self.intent['target_class'] != old_name:
                alt_name = self.intent['target_class']
                alt_name_lower = alt_name.lower()
                for class_name in self.code_analysis.get('classes', {}):
                    if class_name.lower() == alt_name_lower:
                        actual_class_name = class_name
                        break
        
        if not actual_class_name:
            return f"Error: Class {old_name} not found"
                
        class_info = self.code_analysis['classes'][actual_class_name]
        class_line = class_info['location']['line_start'] - 1
        
        # Update the class definition
        modified_lines = self.original_code_lines.copy()
        class_def = modified_lines[class_line]
        
        # Replace class name in the definition
        class_start = class_def.find('class')
        if class_start >= 0:
            name_start = class_def.find(actual_class_name, class_start)
            name_end = name_start + len(actual_class_name)
            new_def = class_def[:name_start] + new_name + class_def[name_end:]
            modified_lines[class_line] = new_def
                
        # Also update any references to this class (inheritance, etc.) 
        # PRESERVING INDENTATION
        for line_idx, line in enumerate(modified_lines):
            # Skip the line we already modified
            if line_idx == class_line:
                continue
                    
            # Find word boundaries to replace exact class name
            if actual_class_name in line:
                # Create a new line with replacements at word boundaries
                new_line = ""
                i = 0
                while i < len(line):
                    # Check if this position is the start of the class name
                    if line[i:i+len(actual_class_name)] == actual_class_name:
                        # Check if this is a word boundary (start of line, preceded by non-alphanumeric, etc.)
                        if i == 0 or not line[i-1].isalnum():
                            # Check if this is the end of a word (end of line, followed by non-alphanumeric)
                            if i+len(actual_class_name) == len(line) or not line[i+len(actual_class_name)].isalnum():
                                # This is a complete word match - replace it
                                new_line += new_name
                                i += len(actual_class_name)
                                continue
                    
                    # Not a match or not a word boundary - keep the character
                    new_line += line[i]
                    i += 1
                
                modified_lines[line_idx] = new_line
        
        return '\n'.join(modified_lines)
    
    def rename_method(self) -> str:
        """Handle the rename_method intent."""
        if self.intent.get('action') != 'rename_method':
            return "Error: Intent is not rename_method"
            
        target_class = self.intent.get('target_class')
        old_name = self.intent.get('old_name')
        new_name = self.intent.get('new_name')
        
        # Find the target class
        if target_class and target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        if target_class:
            # Method is in a class
            class_info = self.code_analysis['classes'][target_class]
            
            # Find the method to rename
            method_to_rename = None
            for method in class_info.get('methods', []):
                if method['name'] == old_name:
                    method_to_rename = method
                    break
                    
            if not method_to_rename:
                return f"Error: Method {old_name} not found in class {target_class}"
                
            # Rename the method
            method_line = method_to_rename['location']['line_start'] - 1
            method_def = self.original_code_lines[method_line]
            
            # Replace method name in the definition
            def_start = method_def.find('def')
            if def_start >= 0:
                name_start = method_def.find(old_name, def_start)
                name_end = name_start + len(old_name)
                new_def = method_def[:name_start] + new_name + method_def[name_end:]
                
                modified_lines = self.original_code_lines.copy()
                modified_lines[method_line] = new_def
                
                return '\n'.join(modified_lines)
        else:
            # Method is a standalone function
            function_to_rename = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == old_name:
                    function_to_rename = function
                    break
                    
            if not function_to_rename:
                return f"Error: Function {old_name} not found"
                
            # Rename the function
            function_line = function_to_rename['location']['line_start'] - 1
            function_def = self.original_code_lines[function_line]
            
            # Replace function name in the definition
            def_start = function_def.find('def')
            if def_start >= 0:
                name_start = function_def.find(old_name, def_start)
                name_end = name_start + len(old_name)
                new_def = function_def[:name_start] + new_name + function_def[name_end:]
                
                modified_lines = self.original_code_lines.copy()
                modified_lines[function_line] = new_def
                
                return '\n'.join(modified_lines)
        
        return "Error: Could not rename method or function"
    
    def add_function(self) -> str:
        """Handle the add_function intent."""
        if self.intent.get('action') != 'add_function':
            return "Error: Intent is not add_function"
            
        function_name = self.intent.get('function_name')
        parameters = self.intent.get('parameters', [])
        function_body = self.intent.get('function_body', 'pass')
        
        # Format the function body
        if function_body == 'pass':
            function_body_formatted = "    pass"
        else:
            function_body_lines = function_body.split('\n')
            function_body_formatted = '\n'.join([f"    {line}" for line in function_body_lines])
        
        # Create function definition
        param_str = ", ".join(parameters)
        new_function = f"def {function_name}({param_str}):\n{function_body_formatted}"
        
        # Find insertion point - usually after the last function or class
        insertion_line = len(self.original_code_lines)
        for class_info in self.code_analysis.get('classes', {}).values():
            insertion_line = max(insertion_line, class_info['location']['line_end'] + 1)
            
        for function in self.code_analysis.get('functions', []):
            insertion_line = max(insertion_line, function['location']['line_end'] + 1)
        
        # Insert the new function
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, "\n\n" + new_function)
        
        return '\n'.join(modified_lines)
    
    def remove_function(self) -> str:
        """Handle the remove_function intent."""
        if self.intent.get('action') != 'remove_function':
            return "Error: Intent is not remove_function"
            
        function_name = self.intent.get('function_name')
        
        # Find the function to remove
        function_to_remove = None
        for function in self.code_analysis.get('functions', []):
            if function['name'] == function_name:
                function_to_remove = function
                break
                
        if not function_to_remove:
            return f"Error: Function {function_name} not found"
            
        # Get the line range to remove
        start_line = function_to_remove['location']['line_start'] - 1
        end_line = function_to_remove['location']['line_end']
        
        # Remove the function lines
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
    
    def add_loop(self) -> str:
        """Handle the add_loop intent."""
        if self.intent.get('action') != 'add_loop':
            return "Error: Intent is not add_loop"
            
        loop_type = self.intent.get('loop_type', 'for')  # 'for' or 'while'
        target_type = self.intent.get('target_type')  # 'method' or 'function'
        target_name = self.intent.get('target_name')
        target_class = self.intent.get('target_class')  # Only if target_type is 'method'
        
        # Loop parameters
        iterator = self.intent.get('iterator', 'i')
        iterable = self.intent.get('iterable', 'range(10)')
        condition = self.intent.get('condition', 'True')  # Only for while loops
        loop_body = self.intent.get('loop_body', 'pass')
        
        # Find the target method or function
        if target_type == 'method':
            if not target_class or target_class not in self.code_analysis.get('classes', {}):
                return f"Error: Class {target_class} not found"
                
            class_info = self.code_analysis['classes'][target_class]
            target = None
            for method in class_info.get('methods', []):
                if method['name'] == target_name:
                    target = method
                    break
        else:  # function
            target = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == target_name:
                    target = function
                    break
                    
        if not target:
            return f"Error: {target_type.capitalize()} {target_name} not found"
            
        # Get insertion point and indentation
        insertion_line = target['location']['line_end'] - 1
        insertion_line_content = self.original_code_lines[insertion_line]
        indentation = self.get_indentation(insertion_line_content)
        
        # Create loop code
        if loop_type == 'for':
            loop_code = f"{indentation}for {iterator} in {iterable}:"
        else:  # while
            loop_code = f"{indentation}while {condition}:"
            
        # Format loop body
        if loop_body == 'pass':
            loop_body_formatted = f"{indentation}    pass"
        else:
            loop_body_lines = loop_body.split('\n')
            loop_body_formatted = '\n'.join([f"{indentation}    {line}" for line in loop_body_lines])
            
        full_loop = f"{loop_code}\n{loop_body_formatted}"
        
        # Insert the loop
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, full_loop)
        
        return '\n'.join(modified_lines)
    
    def add_conditional(self) -> str:
        """Handle the add_conditional intent."""
        if self.intent.get('action') != 'add_conditional':
            return "Error: Intent is not add_conditional"
            
        conditional_type = self.intent.get('conditional_type', 'if')  # 'if', 'if-else', 'if-elif-else', 'match' (Python 3.10+)
        target_type = self.intent.get('target_type')  # 'method' or 'function'
        target_name = self.intent.get('target_name')
        target_class = self.intent.get('target_class')  # Only if target_type is 'method'
        
        # Conditional parameters
        conditions = self.intent.get('conditions', ['True'])
        bodies = self.intent.get('bodies', ['pass'])
        match_subject = self.intent.get('match_subject', '')  # Only for match statements
        cases = self.intent.get('cases', [])  # Only for match statements
        
        # Find the target method or function
        if target_type == 'method':
            if not target_class or target_class not in self.code_analysis.get('classes', {}):
                return f"Error: Class {target_class} not found"
                
            class_info = self.code_analysis['classes'][target_class]
            target = None
            for method in class_info.get('methods', []):
                if method['name'] == target_name:
                    target = method
                    break
        else:  # function
            target = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == target_name:
                    target = function
                    break
                    
        if not target:
            return f"Error: {target_type.capitalize()} {target_name} not found"
            
        # Get insertion point and indentation
        insertion_line = target['location']['line_end'] - 1
        insertion_line_content = self.original_code_lines[insertion_line]
        indentation = self.get_indentation(insertion_line_content)
        
        # Build the conditional code
        conditional_code = []
        
        if conditional_type == 'match':
            # Python 3.10+ match statement
            conditional_code.append(f"{indentation}match {match_subject}:")
            for case in cases:
                pattern = case.get('pattern', '_')
                body = case.get('body', 'pass')
                
                conditional_code.append(f"{indentation}    case {pattern}:")
                
                if body == 'pass':
                    conditional_code.append(f"{indentation}        pass")
                else:
                    body_lines = body.split('\n')
                    for line in body_lines:
                        conditional_code.append(f"{indentation}        {line}")
        else:
            # if, if-else, if-elif-else
            for i, (condition, body) in enumerate(zip(conditions, bodies)):
                if i == 0:
                    conditional_code.append(f"{indentation}if {condition}:")
                elif i == len(conditions) - 1 and conditional_type in ['if-else', 'if-elif-else']:
                    conditional_code.append(f"{indentation}else:")
                else:
                    conditional_code.append(f"{indentation}elif {condition}:")
                    
                if body == 'pass':
                    conditional_code.append(f"{indentation}    pass")
                else:
                    body_lines = body.split('\n')
                    for line in body_lines:
                        conditional_code.append(f"{indentation}    {line}")
                        
        full_conditional = '\n'.join(conditional_code)
        
        # Insert the conditional
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, full_conditional)
        
        return '\n'.join(modified_lines)
    
    def implement_interface(self) -> str:
        """Handle implementing an interface/abstract class intent."""
        if self.intent.get('action') != 'implement_interface':
            return "Error: Intent is not implement_interface"
            
        target_class = self.intent.get('target_class')
        interface_class = self.intent.get('interface_class')
        methods_to_implement = self.intent.get('methods', [])
        
        # Find the target class
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        
        # Add methods needed for the interface
        modified_code = self.original_code_lines.copy()
        insertion_line = class_info['location']['line_end']
        indentation = self.get_class_indentation(target_class)
        
        for method in methods_to_implement:
            method_name = method.get('name')
            parameters = method.get('parameters', [])
            body = method.get('body', 'pass')
            
            # Format parameters
            param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
            
            # Format body
            if body == 'pass':
                body_formatted = f"{indentation}    pass"
            else:
                body_lines = body.split('\n')
                body_formatted = '\n'.join([f"{indentation}    {line}" for line in body_lines])
                
            method_code = f"{indentation}def {method_name}({param_str}):\n{body_formatted}"
            
            # Insert the method
            modified_code.insert(insertion_line, method_code)
            insertion_line += 1  # Update insertion point for next method
            
        # Check if we need to update the inheritance
        class_line = class_info['location']['line_start'] - 1
        class_def = modified_code[class_line]
        
        # Add the interface to the inheritance list if not already there
        if interface_class not in class_info.get('bases', []):
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                # Already has inheritance
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, {interface_class}"
                else:
                    new_bases = interface_class
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
                modified_code[class_line] = new_def
            else:
                # No inheritance yet
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + f"({interface_class})" + class_def[class_name_end:]
                    modified_code[class_line] = new_def
        
        return '\n'.join(modified_code)
    
    def apply_polymorphism(self) -> str:
        """Handle applying polymorphism by overriding methods from parent class."""
        if self.intent.get('action') != 'apply_polymorphism':
            return "Error: Intent is not apply_polymorphism"
            
        target_class = self.intent.get('target_class')
        parent_class = self.intent.get('parent_class')
        methods_to_override = self.intent.get('methods', [])
        
        # Find both classes
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        if parent_class not in self.code_analysis.get('classes', {}):
            return f"Error: Parent class {parent_class} not found"
            
        # Check if target class inherits from parent class
        class_info = self.code_analysis['classes'][target_class]
        if parent_class not in class_info.get('bases', []):
            # Add inheritance if it doesn't exist
            class_line = class_info['location']['line_start'] - 1
            class_def = self.original_code_lines[class_line]
            
            modified_lines = self.original_code_lines.copy()
            
            # Add parent class to inheritance
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                # Already has inheritance
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, {parent_class}"
                else:
                    new_bases = parent_class
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
            else:
                # No inheritance yet
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + f"({parent_class})" + class_def[class_name_end:]
                else:
                    return f"Error: Invalid class definition format"
                    
            modified_lines[class_line] = new_def
        else:
            modified_lines = self.original_code_lines.copy()
        
        # Get parent class methods
        parent_info = self.code_analysis['classes'][parent_class]
        parent_methods = {method['name']: method for method in parent_info.get('methods', [])}
        
        # Override methods
        insertion_line = class_info['location']['line_end']
        indentation = self.get_class_indentation(target_class)
        
        for method_name in methods_to_override:
            if method_name not in parent_methods:
                continue  # Skip if method doesn't exist in parent
                
            parent_method = parent_methods[method_name]
            
            # Check if method already exists in child class
            method_exists = False
            for method in class_info.get('methods', []):
                if method['name'] == method_name:
                    method_exists = True
                    break
                    
            if method_exists:
                continue  # Skip if already overridden
                
            # Create the overridden method
            params = parent_method.get('arguments', ['self'])
            param_str = ", ".join(params)
            
            # Use parent method signature but with custom implementation
            method_code = f"{indentation}def {method_name}({param_str}):\n"
            method_code += f"{indentation}    # Override of {parent_class}.{method_name}\n"
            method_code += f"{indentation}    # Call parent method if needed\n"
            method_code += f"{indentation}    # super().{method_name}({', '.join([p for p in params if p != 'self'])})\n"
            method_code += f"{indentation}    pass"
            
            # Insert the method
            modified_lines.insert(insertion_line, method_code)
            insertion_line += 1  # Update insertion point for next method
            
        return '\n'.join(modified_lines)
    
    def add_abstract_method(self) -> str:
        """Handle adding an abstract method to a class."""
        if self.intent.get('action') != 'add_abstract_method':
            return "Error: Intent is not add_abstract_method"
            
        target_class = self.intent.get('target_class')
        method_name = self.intent.get('method_name')
        parameters = self.intent.get('parameters', [])
        
        # Find the target class
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        
        # Add ABC import if not present
        modified_lines = self.original_code_lines.copy()
        abc_import_found = False
        
        for line in modified_lines:
            if 'import abc' in line or 'from abc import' in line:
                abc_import_found = True
                break
                
        if not abc_import_found:
            # Add import at the beginning of the file
            modified_lines.insert(0, "from abc import ABC, abstractmethod")
            
            # Update line numbers
            for class_name, info in self.code_analysis['classes'].items():
                info['location']['line_start'] += 1
                info['location']['line_end'] += 1
                
                for method in info.get('methods', []):
                    method['location']['line_start'] += 1
                    method['location']['line_end'] += 1
                    
                for attr in info.get('attributes', []):
                    attr['location']['line_start'] += 1
                    
            # Update the target class info
            class_info = self.code_analysis['classes'][target_class]
            
        # Check if the class inherits from ABC
        class_line = class_info['location']['line_start'] - 1
        class_def = modified_lines[class_line]
        
        if 'ABC' not in class_def:
            # Add ABC to inheritance
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                # Already has inheritance
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, ABC"
                else:
                    new_bases = "ABC"
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
            else:
                # No inheritance yet
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + "(ABC)" + class_def[class_name_end:]
                else:
                    return f"Error: Invalid class definition format"
                    
            modified_lines[class_line] = new_def
            
        # Create the abstract method
        indentation = self.get_class_indentation(target_class)
        param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
        
        method_code = f"{indentation}@abstractmethod\n"
        method_code += f"{indentation}def {method_name}({param_str}):\n"
        method_code += f"{indentation}    pass"
        
        # Insert at the end of the class
        insertion_line = class_info['location']['line_end']
        modified_lines.insert(insertion_line, method_code)
        
        return '\n'.join(modified_lines)
    
    def generate_modified_code(self) -> str:
        """Generate modified code based on the intent."""
        action = self.intent.get('action')
        
        if action == 'add_method':
            return self.add_method()
        elif action == 'remove_method':
            return self.remove_method()
        elif action == 'add_class':
            return self.add_class()
        elif action == 'remove_class':
            return self.remove_class()
        elif action == 'add_attribute':
            return self.add_attribute()
        elif action == 'remove_attribute':
            return self.remove_attribute()
        elif action == 'rename_class':
            return self.rename_class()
        elif action == 'rename_method':
            return self.rename_method()
        elif action == 'add_function':
            return self.add_function()
        elif action == 'remove_function':
            return self.remove_function()
        elif action == 'add_loop':
            return self.add_loop()
        elif action == 'add_conditional':
            return self.add_conditional()
        elif action == 'implement_interface':
            return self.implement_interface()
        elif action == 'apply_polymorphism':
            return self.apply_polymorphism()
        elif action == 'add_abstract_method':
            return self.add_abstract_method()
        else:
            return f"Error: Unsupported action {action}"

def process_command(original_code: str, command_parser_output: Dict, code_analyzer_output: Dict) -> str:
    """
    Process a command to modify code with case-insensitive class matching.
    
    Args:
        original_code: The original code to modify
        command_parser_output: JSON output from command parser
        code_analyzer_output: JSON output from code analyzer
        
    Returns:
        Modified code as string
    """
    # Make a copy of the command intent to avoid modifying the original
    normalized_intent = command_parser_output.copy()
    
    # Normalize class names in the intent to match the case in the code
    if 'target_class' in normalized_intent:
        target_class_lower = normalized_intent['target_class'].lower()
        for class_name in code_analyzer_output.get('classes', {}):
            if class_name.lower() == target_class_lower:
                normalized_intent['target_class'] = class_name
                break
    
    # Handle other class name fields if needed
    for field in ['old_name', 'new_name', 'parent_class', 'interface_class', 'child_class']:
        if field in normalized_intent:
            field_lower = normalized_intent[field].lower()
            for class_name in code_analyzer_output.get('classes', {}):
                if class_name.lower() == field_lower:
                    normalized_intent[field] = class_name
                    break
    
    # Now proceed with the normalized intent
    generator = CodeGenerator()
    generator.load_code(original_code)
    generator.load_intent(normalized_intent)
    generator.load_analysis(code_analyzer_output)
    
    return generator.generate_modified_code()

