import json
from typing import Dict, List, Any, Tuple

class CodeGenerator:
    def __init__(self):
        self.original_code_lines = []
        self.code_analysis = {}
        self.intent = {}
        
    def load_code(self, code: str):
        self.original_code_lines = code.split('\n')
        
    def load_analysis(self, analysis_json: str):
        if isinstance(analysis_json, str):
            self.code_analysis = json.loads(analysis_json)
        else:
            self.code_analysis = analysis_json
            
    def load_intent(self, intent_json: str):
        if isinstance(intent_json, str):
            self.intent = json.loads(intent_json)
        else:
            self.intent = intent_json
            
    def get_indentation(self, line: str) -> str:
        return line[:len(line) - len(line.lstrip())]
    
    def get_class_indentation(self, class_name: str) -> str:
        if class_name not in self.code_analysis.get('classes', {}):
            return "    " 
            
        class_info = self.code_analysis['classes'][class_name]
        
        if class_info.get('methods'):
            first_method = class_info['methods'][0]
            line_index = first_method['location']['line_start'] - 1
            if 0 <= line_index < len(self.original_code_lines):
                return self.get_indentation(self.original_code_lines[line_index])
        
        return "    "  
    
    def add_method(self) -> str:
        """Handle the add_method intent."""
        if self.intent.get('action') != 'add_method':
            return "Error: Intent is not add_method"
            
        method_name = self.intent.get('method_name')
        target_class = self.intent.get('target_class')
        parameters_raw = self.intent.get('parameters', [])
        
        if len(parameters_raw) > 0:
            param_text = parameters_raw[0]
            param_parts = param_text.split(" to ")
            if len(param_parts) > 0:
                parameters = param_parts[0].strip().split(", ")
            else:
                parameters = []
        else:
            parameters = []
        
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        class_end_line = class_info['location']['line_end']
        
        indentation = self.get_class_indentation(target_class)
        
        param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
        new_method = f"{indentation}def {method_name}({param_str}):\n{indentation}    pass"
        
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(class_end_line, new_method)
        
        return '\n'.join(modified_lines)
    
    def remove_method(self) -> str:
        if self.intent.get('action') != 'remove_method':
            return "Error: Intent is not remove_method"
                
        method_name = self.intent.get('method_name')
        target_class = self.intent.get('target_class')
        
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
        
        method_to_remove = None
        for method in class_info.get('methods', []):
            if method['name'].lower() == method_name.lower():
                method_to_remove = method
                break
                    
        if not method_to_remove:
            return f"Error: Method {method_name} not found in class {actual_class_name}"
                
        start_line = method_to_remove['location']['line_start'] - 1
        end_line = method_to_remove['location']['line_end']
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
    
    def add_class(self) -> str:
        if self.intent.get('action') != 'add_class':
            return "Error: Intent is not add_class"
                
        class_name = self.intent.get('class_name')
        if not class_name:
            return "Error: Missing class name"
            
        base_classes = self.intent.get('base_classes', [])
        methods = self.intent.get('methods', [])
        attributes = self.intent.get('attributes', [])
        
        insertion_line = len(self.original_code_lines)
        for class_info in self.code_analysis.get('classes', {}).values():
            insertion_line = max(insertion_line, class_info['location']['line_end'] + 1)
            
        base_classes_str = f"({', '.join(base_classes)})" if base_classes else ""
        class_def = f"class {class_name}{base_classes_str}:"
        
        class_body = []
        if attributes:
            init_body = ["self." + attr + " = " + attr for attr in attributes]
            param_str = "self" + (", " + ", ".join(attributes) if attributes else "")
            init_method = f"    def __init__({param_str}):\n        " + "\n        ".join(init_body)
            class_body.append(init_method)
        
        for method in methods:
            method_name = method.get('name', 'unknown_method')
            params = method.get('params', [])
            body = method.get('body', 'pass')
            
            param_str = "self" + (", " + ", ".join(params) if params else "")
            method_str = f"    def {method_name}({param_str}):\n        {body}"
            class_body.append(method_str)
            
        if not class_body:
            class_body = ["    pass"]
            
        new_class = class_def + "\n" + "\n\n".join(class_body)
        
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, "\n\n" + new_class)
        
        return '\n'.join(modified_lines)
    
    def remove_class(self) -> str:
        if self.intent.get('action') != 'remove_class':
            return "Error: Intent is not remove_class"
            
        class_name = self.intent.get('class_name')

        if class_name not in self.code_analysis.get('classes', {}):
            return f"Error: Class {class_name} not found"
            
        class_info = self.code_analysis['classes'][class_name]
        
        start_line = class_info['location']['line_start'] - 1
        end_line = class_info['location']['line_end']
        
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
        
    def add_attribute(self) -> str:
        if self.intent.get('action') != 'add_attribute':
            return "Error: Intent is not add_attribute"
                
        target_class = self.intent.get('target_class')
        attribute_name = self.intent.get('attribute_name')
        default_value = self.intent.get('default_value', 'None')
        
        if not target_class:
            return "Error: Missing target class"
            
        if not attribute_name:
            return "Error: Missing attribute name"
        
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
        
        init_method = None
        for method in class_info.get('methods', []):
            if method['name'] == '__init__':
                init_method = method
                break
                
        modified_lines = self.original_code_lines.copy()
                
        if not init_method:
            indentation = self.get_class_indentation(actual_class_name)
            init_method_str = f"{indentation}def __init__(self, {attribute_name}):\n{indentation}    self.{attribute_name} = {attribute_name}"
            
            class_start_line = class_info['location']['line_start']
            modified_lines.insert(class_start_line, init_method_str)
        else:
            init_end_line = init_method['location']['line_end'] - 1
            init_line = self.original_code_lines[init_end_line]
            indentation = self.get_indentation(init_line)
            
            attribute_line = f"{indentation}self.{attribute_name} = {attribute_name}"
            modified_lines.insert(init_end_line, attribute_line)
            
            if self.intent.get('add_parameter', True):
                init_start_line = init_method['location']['line_start'] - 1
                init_def_line = self.original_code_lines[init_start_line]
                
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
        if self.intent.get('action') != 'remove_attribute':
            return "Error: Intent is not remove_attribute"
                
        target_class = self.intent.get('target_class')
        
        attribute_name = self.intent.get('attribute_name')
        if not attribute_name and 'attributes' in self.intent and len(self.intent['attributes']) > 0:
            attribute_name = self.intent['attributes'][0]
            
        if not target_class:
            return "Error: Missing target class"
            
        if not attribute_name:
            return "Error: Missing attribute name"
        
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
        
        attribute_to_remove = None
        for attr in class_info.get('attributes', []):
            if attr['name'].lower() == attribute_name.lower():
                attribute_to_remove = attr
                break
                
        if not attribute_to_remove:
            return f"Error: Attribute {attribute_name} not found in class {actual_class_name}"
            
        modified_lines = self.original_code_lines.copy()
        attr_line = attribute_to_remove['location']['line_start'] - 1
        del modified_lines[attr_line]
        
        init_method = None
        for method in class_info.get('methods', []):
            if method['name'] == '__init__':
                init_method = method
                break
                
        if init_method:
            has_param = False
            for arg in init_method.get('arguments', []):
                if arg.lower() == attribute_name.lower():
                    has_param = True
                    break
                    
            if has_param:
                init_line = init_method['location']['line_start'] - 1
                init_def = modified_lines[init_line]
                
                param_start = init_def.find('(')
                param_end = init_def.find(')')
                if param_start >= 0 and param_end >= 0:
                    param_text = init_def[param_start+1:param_end]
                    params = [p.strip() for p in param_text.split(',')]
                    
                    new_params = []
                    for p in params:
                        if p.strip().lower() != attribute_name.lower():
                            new_params.append(p)
                            
                    new_def = init_def[:param_start+1] + ', '.join(new_params) + init_def[param_end:]
                    modified_lines[init_line] = new_def
        
        return '\n'.join(modified_lines)
    
    def rename_class(self) -> str:
        if self.intent.get('action') != 'rename_class':
            return "Error: Intent is not rename_class"
            
        old_name = self.intent.get('old_name', self.intent.get('target_class'))
        new_name = self.intent.get('new_name', self.intent.get('new_class_name'))
        
        if not old_name or not new_name:
            return "Error: Missing old or new class name"
        
        actual_class_name = None
        if old_name:
            old_name_lower = old_name.lower()
            for class_name in self.code_analysis.get('classes', {}):
                if class_name.lower() == old_name_lower:
                    actual_class_name = class_name
                    break
        
        if not actual_class_name:
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
        
        modified_lines = self.original_code_lines.copy()
        class_def = modified_lines[class_line]
        
        class_start = class_def.find('class')
        if class_start >= 0:
            name_start = class_def.find(actual_class_name, class_start)
            name_end = name_start + len(actual_class_name)
            new_def = class_def[:name_start] + new_name + class_def[name_end:]
            modified_lines[class_line] = new_def

        for line_idx, line in enumerate(modified_lines):
            if line_idx == class_line:
                continue
                    
            if actual_class_name in line:
                new_line = ""
                i = 0
                while i < len(line):
                    if line[i:i+len(actual_class_name)] == actual_class_name:
                        if i == 0 or not line[i-1].isalnum():
                            if i+len(actual_class_name) == len(line) or not line[i+len(actual_class_name)].isalnum():
                                new_line += new_name
                                i += len(actual_class_name)
                                continue
                    
                    new_line += line[i]
                    i += 1
                
                modified_lines[line_idx] = new_line
        
        return '\n'.join(modified_lines)
    
    def rename_method(self) -> str:
        if self.intent.get('action') != 'rename_method':
            return "Error: Intent is not rename_method"
            
        target_class = self.intent.get('target_class')
        old_name = self.intent.get('old_name')
        new_name = self.intent.get('new_name')
        
        if target_class and target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        if target_class:
            class_info = self.code_analysis['classes'][target_class]
            
            method_to_rename = None
            for method in class_info.get('methods', []):
                if method['name'] == old_name:
                    method_to_rename = method
                    break
                    
            if not method_to_rename:
                return f"Error: Method {old_name} not found in class {target_class}"
                
            method_line = method_to_rename['location']['line_start'] - 1
            method_def = self.original_code_lines[method_line]
            
            def_start = method_def.find('def')
            if def_start >= 0:
                name_start = method_def.find(old_name, def_start)
                name_end = name_start + len(old_name)
                new_def = method_def[:name_start] + new_name + method_def[name_end:]
                
                modified_lines = self.original_code_lines.copy()
                modified_lines[method_line] = new_def
                
                return '\n'.join(modified_lines)
        else:
            function_to_rename = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == old_name:
                    function_to_rename = function
                    break
                    
            if not function_to_rename:
                return f"Error: Function {old_name} not found"
                
            function_line = function_to_rename['location']['line_start'] - 1
            function_def = self.original_code_lines[function_line]
            
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
        if self.intent.get('action') != 'add_function':
            return "Error: Intent is not add_function"
            
        function_name = self.intent.get('function_name')
        parameters = self.intent.get('parameters', [])
        function_body = self.intent.get('function_body', 'pass')
        
        if function_body == 'pass':
            function_body_formatted = "    pass"
        else:
            function_body_lines = function_body.split('\n')
            function_body_formatted = '\n'.join([f"    {line}" for line in function_body_lines])
        
        param_str = ", ".join(parameters)
        new_function = f"def {function_name}({param_str}):\n{function_body_formatted}"
        
        insertion_line = len(self.original_code_lines)
        for class_info in self.code_analysis.get('classes', {}).values():
            insertion_line = max(insertion_line, class_info['location']['line_end'] + 1)
            
        for function in self.code_analysis.get('functions', []):
            insertion_line = max(insertion_line, function['location']['line_end'] + 1)
        
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, "\n\n" + new_function)
        
        return '\n'.join(modified_lines)
    
    def remove_function(self) -> str:
        if self.intent.get('action') != 'remove_function':
            return "Error: Intent is not remove_function"
            
        function_name = self.intent.get('function_name')
        
        function_to_remove = None
        for function in self.code_analysis.get('functions', []):
            if function['name'] == function_name:
                function_to_remove = function
                break
                
        if not function_to_remove:
            return f"Error: Function {function_name} not found"
            
        start_line = function_to_remove['location']['line_start'] - 1
        end_line = function_to_remove['location']['line_end']
        
        modified_lines = self.original_code_lines.copy()
        del modified_lines[start_line:end_line]
        
        return '\n'.join(modified_lines)
    
    def add_loop(self) -> str:
        """Handle the add_loop intent."""
        if self.intent.get('action') != 'add_loop':
            return "Error: Intent is not add_loop"
            
        loop_type = self.intent.get('loop_type', 'for')  
        target_type = self.intent.get('target_type')  
        target_name = self.intent.get('target_name')
        target_class = self.intent.get('target_class')  
        
        iterator = self.intent.get('iterator', 'i')
        iterable = self.intent.get('iterable', 'range(10)')
        condition = self.intent.get('condition', 'True')  
        loop_body = self.intent.get('loop_body', 'pass')
        
        if target_type == 'method':
            if not target_class or target_class not in self.code_analysis.get('classes', {}):
                return f"Error: Class {target_class} not found"
                
            class_info = self.code_analysis['classes'][target_class]
            target = None
            for method in class_info.get('methods', []):
                if method['name'] == target_name:
                    target = method
                    break
        else:  
            target = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == target_name:
                    target = function
                    break
                    
        if not target:
            return f"Error: {target_type.capitalize()} {target_name} not found"
            
        insertion_line = target['location']['line_end'] - 1
        insertion_line_content = self.original_code_lines[insertion_line]
        indentation = self.get_indentation(insertion_line_content)
        
        if loop_type == 'for':
            loop_code = f"{indentation}for {iterator} in {iterable}:"
        else:  
            loop_code = f"{indentation}while {condition}:"
            
        if loop_body == 'pass':
            loop_body_formatted = f"{indentation}    pass"
        else:
            loop_body_lines = loop_body.split('\n')
            loop_body_formatted = '\n'.join([f"{indentation}    {line}" for line in loop_body_lines])
            
        full_loop = f"{loop_code}\n{loop_body_formatted}"
        
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, full_loop)
        
        return '\n'.join(modified_lines)
    
    def add_conditional(self) -> str:
        """Handle the add_conditional intent."""
        if self.intent.get('action') != 'add_conditional':
            return "Error: Intent is not add_conditional"
            
        conditional_type = self.intent.get('conditional_type', 'if')  
        target_type = self.intent.get('target_type')  
        target_name = self.intent.get('target_name')
        target_class = self.intent.get('target_class')  
        
        conditions = self.intent.get('conditions', ['True'])
        bodies = self.intent.get('bodies', ['pass'])
        match_subject = self.intent.get('match_subject', '')  
        cases = self.intent.get('cases', []) 
        
        if target_type == 'method':
            if not target_class or target_class not in self.code_analysis.get('classes', {}):
                return f"Error: Class {target_class} not found"
                
            class_info = self.code_analysis['classes'][target_class]
            target = None
            for method in class_info.get('methods', []):
                if method['name'] == target_name:
                    target = method
                    break
        else:  
            target = None
            for function in self.code_analysis.get('functions', []):
                if function['name'] == target_name:
                    target = function
                    break
                    
        if not target:
            return f"Error: {target_type.capitalize()} {target_name} not found"
            
        insertion_line = target['location']['line_end'] - 1
        insertion_line_content = self.original_code_lines[insertion_line]
        indentation = self.get_indentation(insertion_line_content)
        
        conditional_code = []
        
        if conditional_type == 'match':
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
        
        modified_lines = self.original_code_lines.copy()
        modified_lines.insert(insertion_line, full_conditional)
        
        return '\n'.join(modified_lines)
    
    def implement_interface(self) -> str:
        if self.intent.get('action') != 'implement_interface':
            return "Error: Intent is not implement_interface"
            
        target_class = self.intent.get('target_class')
        interface_class = self.intent.get('interface_class')
        methods_to_implement = self.intent.get('methods', [])
        
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        
        modified_code = self.original_code_lines.copy()
        insertion_line = class_info['location']['line_end']
        indentation = self.get_class_indentation(target_class)
        
        for method in methods_to_implement:
            method_name = method.get('name')
            parameters = method.get('parameters', [])
            body = method.get('body', 'pass')
            
            param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
            
            if body == 'pass':
                body_formatted = f"{indentation}    pass"
            else:
                body_lines = body.split('\n')
                body_formatted = '\n'.join([f"{indentation}    {line}" for line in body_lines])
                
            method_code = f"{indentation}def {method_name}({param_str}):\n{body_formatted}"
            
            modified_code.insert(insertion_line, method_code)
            insertion_line += 1  
            
        class_line = class_info['location']['line_start'] - 1
        class_def = modified_code[class_line]
        
        if interface_class not in class_info.get('bases', []):
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, {interface_class}"
                else:
                    new_bases = interface_class
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
                modified_code[class_line] = new_def
            else:
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + f"({interface_class})" + class_def[class_name_end:]
                    modified_code[class_line] = new_def
        
        return '\n'.join(modified_code)
    
    def apply_polymorphism(self) -> str:
        if self.intent.get('action') != 'apply_polymorphism':
            return "Error: Intent is not apply_polymorphism"
            
        target_class = self.intent.get('target_class')
        parent_class = self.intent.get('parent_class')
        methods_to_override = self.intent.get('methods', [])
        
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        if parent_class not in self.code_analysis.get('classes', {}):
            return f"Error: Parent class {parent_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        if parent_class not in class_info.get('bases', []):
            class_line = class_info['location']['line_start'] - 1
            class_def = self.original_code_lines[class_line]
            
            modified_lines = self.original_code_lines.copy()
            
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, {parent_class}"
                else:
                    new_bases = parent_class
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
            else:
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + f"({parent_class})" + class_def[class_name_end:]
                else:
                    return f"Error: Invalid class definition format"
                    
            modified_lines[class_line] = new_def
        else:
            modified_lines = self.original_code_lines.copy()
        
        parent_info = self.code_analysis['classes'][parent_class]
        parent_methods = {method['name']: method for method in parent_info.get('methods', [])}
        
        insertion_line = class_info['location']['line_end']
        indentation = self.get_class_indentation(target_class)
        
        for method_name in methods_to_override:
            if method_name not in parent_methods:
                continue  
                
            parent_method = parent_methods[method_name]
            
            method_exists = False
            for method in class_info.get('methods', []):
                if method['name'] == method_name:
                    method_exists = True
                    break
                    
            if method_exists:
                continue  
                
            params = parent_method.get('arguments', ['self'])
            param_str = ", ".join(params)
            
            method_code = f"{indentation}def {method_name}({param_str}):\n"
            method_code += f"{indentation}    # Override of {parent_class}.{method_name}\n"
            method_code += f"{indentation}    # Call parent method if needed\n"
            method_code += f"{indentation}    # super().{method_name}({', '.join([p for p in params if p != 'self'])})\n"
            method_code += f"{indentation}    pass"
            
            modified_lines.insert(insertion_line, method_code)
            insertion_line += 1  
            
        return '\n'.join(modified_lines)
    
    def add_abstract_method(self) -> str:
        if self.intent.get('action') != 'add_abstract_method':
            return "Error: Intent is not add_abstract_method"
            
        target_class = self.intent.get('target_class')
        method_name = self.intent.get('method_name')
        parameters = self.intent.get('parameters', [])
        
        if target_class not in self.code_analysis.get('classes', {}):
            return f"Error: Class {target_class} not found"
            
        class_info = self.code_analysis['classes'][target_class]
        
        modified_lines = self.original_code_lines.copy()
        abc_import_found = False
        
        for line in modified_lines:
            if 'import abc' in line or 'from abc import' in line:
                abc_import_found = True
                break
                
        if not abc_import_found:
            modified_lines.insert(0, "from abc import ABC, abstractmethod")
            
            for class_name, info in self.code_analysis['classes'].items():
                info['location']['line_start'] += 1
                info['location']['line_end'] += 1
                
                for method in info.get('methods', []):
                    method['location']['line_start'] += 1
                    method['location']['line_end'] += 1
                    
                for attr in info.get('attributes', []):
                    attr['location']['line_start'] += 1
                    
            class_info = self.code_analysis['classes'][target_class]
            
        class_line = class_info['location']['line_start'] - 1
        class_def = modified_lines[class_line]
        
        if 'ABC' not in class_def:
            open_paren = class_def.find('(')
            close_paren = class_def.find(')')
            
            if open_paren >= 0 and close_paren >= 0:
                bases = class_def[open_paren+1:close_paren].strip()
                if bases:
                    new_bases = f"{bases}, ABC"
                else:
                    new_bases = "ABC"
                
                new_def = class_def[:open_paren+1] + new_bases + class_def[close_paren:]
            else:
                class_name_end = class_def.find(':')
                if class_name_end >= 0:
                    new_def = class_def[:class_name_end] + "(ABC)" + class_def[class_name_end:]
                else:
                    return f"Error: Invalid class definition format"
                    
            modified_lines[class_line] = new_def
            
        indentation = self.get_class_indentation(target_class)
        param_str = "self" + (", " + ", ".join(parameters) if parameters else "")
        
        method_code = f"{indentation}@abstractmethod\n"
        method_code += f"{indentation}def {method_name}({param_str}):\n"
        method_code += f"{indentation}    pass"
        
        insertion_line = class_info['location']['line_end']
        modified_lines.insert(insertion_line, method_code)
        
        return '\n'.join(modified_lines)
    
    def generate_modified_code(self) -> str:
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
    normalized_intent = command_parser_output.copy()
    
    if 'target_class' in normalized_intent:
        target_class_lower = normalized_intent['target_class'].lower()
        for class_name in code_analyzer_output.get('classes', {}):
            if class_name.lower() == target_class_lower:
                normalized_intent['target_class'] = class_name
                break
    
    for field in ['old_name', 'new_name', 'parent_class', 'interface_class', 'child_class']:
        if field in normalized_intent:
            field_lower = normalized_intent[field].lower()
            for class_name in code_analyzer_output.get('classes', {}):
                if class_name.lower() == field_lower:
                    normalized_intent[field] = class_name
                    break
    
    generator = CodeGenerator()
    generator.load_code(original_code)
    generator.load_intent(normalized_intent)
    generator.load_analysis(code_analyzer_output)
    
    return generator.generate_modified_code()

