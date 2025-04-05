import re
import json
import os
import subprocess
import sys

class CommandParser:
    def __init__(self):
        # Define action keywords and patterns
        self.action_patterns = {
            "add": ["add", "create", "implement", "define", "insert", "make"],
            "remove": ["remove", "delete", "eliminate", "get rid of"],
            "modify": ["modify", "change", "update", "alter"],
            "rename": ["rename", "change name", "call", "name"],
            "get": ["get", "retrieve", "find", "show", "display"]
        }
        
        # Define target patterns
        self.target_patterns = {
            "method": ["method", "function", "procedure"],
            "class": ["class", "object", "type"],
            "property": ["property", "attribute", "field", "variable"],
            "parameter": ["parameter", "param", "argument", "arg"],
            "loop": ["loop", "for loop", "while loop", "for", "while", "iterate"],
            "conditional": ["if", "else", "conditional", "switch", "case", "if-else", "if/else"],
            "inheritance": ["inheritance", "inherit", "extends", "subclass", "derive from"],
            "polymorphism": ["polymorphism", "polymorphic", "override", "overload"]
        }
        
        # Try loading spaCy - if not available, use NLTK
        self.nlp = self._initialize_nlp()
        
    def _initialize_nlp(self):
        """Initialize either spaCy or NLTK based on availability"""
        try:
            import spacy
            
            # Check if the model is installed
            try:
                return spacy.load("en_core_web_sm")
            except OSError:
                # If model isn't installed, try to download it
                print("Downloading spaCy language model...")
                subprocess.check_call([sys.executable, "-m", "spacy", "download", "en_core_web_sm"])
                return spacy.load("en_core_web_sm")
                
        except (ImportError, subprocess.CalledProcessError):
            # If spaCy is not available or download fails, fall back to NLTK
            try:
                import nltk
                from nltk.tokenize import word_tokenize
                from nltk.tag import pos_tag
                
                # Make sure necessary NLTK data is downloaded
                try:
                    nltk.data.find('tokenizers/punkt')
                except LookupError:
                    nltk.download('punkt', quiet=True)
                
                try:
                    nltk.data.find('taggers/averaged_perceptron_tagger')
                except LookupError:
                    nltk.download('averaged_perceptron_tagger', quiet=True)
                
                # Create a wrapper class to provide a spaCy-like interface with NLTK
                class NLTKWrapper:
                    def __call__(self, text):
                        tokens = word_tokenize(text)
                        pos_tags = pos_tag(tokens)
                        
                        # Create a document-like object with token objects
                        class TokenObj:
                            def __init__(self, token, pos):
                                self.text = token
                                self.pos_ = pos
                                self.lemma_ = token.lower()
                        
                        class DocObj:
                            def __init__(self, tokens, pos_tags, text):
                                self.tokens = [TokenObj(token, pos) for token, pos in pos_tags]
                                self.text = text
                            
                            def __iter__(self):
                                return iter(self.tokens)
                            
                            def __getitem__(self, i):
                                return self.tokens[i]
                            
                            def __len__(self):
                                return len(self.tokens)
                        
                        return DocObj(tokens, pos_tags, text)
                
                return NLTKWrapper()
                
            except ImportError:
                print("Neither spaCy nor NLTK are available. Falling back to basic regex parsing.")
                # Create a very basic tokenizer class as a last resort
                class BasicTokenizer:
                    def __call__(self, text):
                        tokens = text.split()
                        
                        class TokenObj:
                            def __init__(self, token):
                                self.text = token
                                self.pos_ = "UNKNOWN"
                                self.lemma_ = token.lower()
                        
                        class DocObj:
                            def __init__(self, tokens, text):
                                self.tokens = [TokenObj(token) for token in tokens]
                                self.text = text
                            
                            def __iter__(self):
                                return iter(self.tokens)
                            
                            def __getitem__(self, i):
                                return self.tokens[i]
                            
                            def __len__(self):
                                return len(self.tokens)
                        
                        return DocObj(tokens, text)
                
                return BasicTokenizer()
    
    def parse_command(self, command_text):
        """
        Parse a natural language command into a structured intent
        
        Args:
            command_text (str): The natural language command
            
        Returns:
            dict: A structured intent representing the command
        """
        # Process the text with NLP
        doc = self.nlp(command_text)
        command = command_text.lower()
        
        # Initialize the intent structure
        intent = {}
        
        # First determine the base action type
        base_action = self._determine_base_action(command)
        
        # Next, determine what we're acting on
        target_type = self._determine_target_type(command)
        
        # Set the full action based on base action and target
        if base_action and target_type:
            intent["action"] = f"{base_action}_{target_type}"
        else:
            intent["action"] = base_action if base_action else "unknown"
            
        if intent["action"] == "add_class":
            class_name = self._extract_class_name(command_text)
            if class_name:
                intent["class_name"] = class_name
                
            # Check for attributes in the command
            attrs = self._extract_attributes(command)
            if attrs:
                intent["attributes"] = attrs
                
        if intent["action"] == "add_attribute":
            # Extract attributes
            attrs = self._extract_attributes(command_text)
            if attrs and len(attrs) > 0:
                intent["attribute_name"] = attrs[0]  # Take the first attribute
                
            # Extract class name for the attributes
            class_name = self._extract_class_for_attribute(command_text)
            if class_name:
                intent["target_class"] = class_name
        
        # Special case for function in class context
        if "function" in command and "in" in command and "class" in command:
            if "action" in intent and intent["action"] == "add_function":
                intent["action"] = "add_method"
            
        # Extract other relevant information based on the action type
        if "method" in intent["action"] or "function" in intent["action"]:
            # Extract method name
            method_name = self._extract_method_or_function_name(command)
            if method_name:
                intent["method_name"] = method_name
                
            # Extract parameters if adding a method/function
            if base_action == "add":
                parameters = self._extract_parameters(command)
                if parameters:
                    intent["parameters"] = parameters
                    
            # Extract class if specified
            class_name = self._extract_class_name(command)
            if class_name:
                intent["target_class"] = class_name
                
        elif "class" in intent["action"]:
            # Extract class name
            class_name = self._extract_class_name(command)
            if class_name:
                intent["target_class"] = class_name
                
        elif "attribute" in intent["action"] or "property" in intent["action"]:
            # Extract attributes
            attrs = self._extract_attributes(command)
            if attrs:
                intent["attributes"] = attrs
                
            # Extract class name for the attributes
            class_name = self._extract_class_for_attribute(command)
            if class_name:
                intent["target_class"] = class_name
                
        # Handle rename operations
        if base_action == "rename":
            if target_type == "class":
                old_name = self._extract_old_class_name(command)
                new_name = self._extract_new_class_name(command)
                if old_name:
                    intent["old_name"] = old_name
                if new_name:
                    intent["new_name"] = new_name
                    
            elif target_type == "method":
                old_name = self._extract_old_method_name(command)
                new_name = self._extract_new_method_name(command)
                if old_name:
                    intent["method_name"] = old_name
                if new_name:
                    intent["new_method_name"] = new_name
                
                # Extract class if specified
                class_name = self._extract_class_for_method(command)
                if class_name:
                    intent["target_class"] = class_name
                    
        # Handle loop operations
        if "loop" in command or intent["action"] == "add_loop":
            loop_type = self._extract_loop_type(command)
            if loop_type:
                intent["loop_type"] = loop_type
                
            # Extract the method/function the loop should be added to
            container_name = self._extract_container_name(command)
            if container_name:
                intent["container_name"] = container_name
                
                # Determine if it's a method or function
                if "method" in command:
                    intent["container_type"] = "method"
                else:
                    intent["container_type"] = "function"
                    
            # Ensure the action is set correctly
            intent["action"] = "add_loop"
                    
        # Handle conditional operations
        if "conditional" in command or "if/else" in command or "switch" in command or "statement" in command or intent["action"] == "add_conditional":
            conditional_type = self._extract_conditional_type(command)
            if conditional_type:
                intent["conditional_type"] = conditional_type
                
            # Extract the method/function the conditional should be added to
            container_name = self._extract_container_name(command)
            if container_name:
                intent["container_name"] = container_name
                
                # Determine if it's a method or function
                if "method" in command:
                    intent["container_type"] = "method" 
                else:
                    intent["container_type"] = "function"
                    
            # Ensure the action is set correctly
            intent["action"] = "add_conditional"
                    
        # Handle inheritance
        if "inheritance" in intent["action"]:
            # Extract child class
            child_class = self._extract_child_class(command)
            if child_class:
                intent["child_class"] = child_class
                
            # Extract parent class
            parent_class = self._extract_parent_class(command)
            if parent_class:
                intent["parent_class"] = parent_class
                
        # Handle polymorphism
        if "polymorphism" in intent["action"] or "override" in command or "polymorphism" in command:
            # Extract method to override
            method_name = self._extract_method_to_override(command)
            if method_name:
                intent["method_name"] = method_name
                
            # Extract class if specified
            class_name = self._extract_class_name(command)
            if class_name:
                intent["target_class"] = class_name
                
            # Ensure the action is set correctly
            intent["action"] = "add_polymorphism"
        
        return intent
    
    def _determine_base_action(self, command):
        """Determine the base action (add, remove, rename, etc.)"""
        for action, keywords in self.action_patterns.items():
            for keyword in keywords:
                if keyword in command.split():
                    # Special case for rename which is often expressed as "change X to Y"
                    if action == "modify" and "to" in command:
                        if any(word in command for word in ["rename", "name"]):
                            return "rename"
                    return action
        return None
    
    def _determine_target_type(self, command):
        """Determine what we're acting on (class, method, attribute, etc.)"""
        # Special case for loops
        if any(word in command for word in ["for loop", "while loop", " loop"]) and "to the" in command:
            return "loop"
            
        # Special case for conditionals
        if any(word in command for word in ["if/else", "if-else", "switch/case", "conditional", "statement"]) and "to the" in command:
            return "conditional"
            
        # Special case for polymorphism
        if "polymorphism" in command or "override" in command or "overload" in command:
            return "polymorphism"
            
        # Special case for inheritance
        if "inherit" in command or "extends" in command or "subclass" in command:
            return "inheritance"
            
        # Check for function first with specific context
        if any(word in command for word in ["standalone function", "function outside", "global function"]):
            return "function"
        
        # Check for method or function
        if "method" in command and not any(phrase in command for phrase in ["to the", "loop to", "conditional to", "statement to"]):
            return "method"
        elif "function" in command and not any(phrase in command for phrase in ["to the", "loop to", "conditional to", "statement to", "class"]):
            return "function"
            
        # Check for attribute/property
        if any(word in command for word in ["attribute", "property", "field"]):
            return "attribute"
            
        # Check for class
        if "class" in command:
            return "class"
            
        return None
    
    def _extract_method_or_function_name(self, command):
        """Extract method or function name from command"""
        # Pattern for "X called/named Y"
        called_pattern = re.compile(r"(?:method|function)\s+(?:called|named)\s+(\w+)", re.IGNORECASE)
        matches = called_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "the X method/function"
        the_pattern = re.compile(r"the\s+(\w+)\s+(?:method|function)", re.IGNORECASE)
        matches = the_pattern.search(command)
        if matches:
            return matches.group(1)
        
        # Pattern for "a X method/function"
        a_pattern = re.compile(r"a\s+(\w+)\s+(?:method|function)", re.IGNORECASE)
        matches = a_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "method/function X"
        direct_pattern = re.compile(r"(?:method|function)\s+(?:named|called)?\s*(\w+)", re.IGNORECASE)
        matches = direct_pattern.search(command)
        if matches and matches.group(1).lower() not in ["called", "named"]:
            return matches.group(1)
            
        return None
    
    def _extract_class_name(self, command):
        """Extract class name from command with improved pattern matching"""
        # Pattern for "X class"
        class_pattern = re.compile(r"(\w+)\s+class", re.IGNORECASE)
        matches = class_pattern.search(command)
        if matches and matches.group(1).lower() not in ["a", "the", "new", "any"]:
            return matches.group(1)
            
        # Pattern for "class called/named X"
        called_pattern = re.compile(r"class\s+(?:called|named)\s+(\w+)", re.IGNORECASE)
        matches = called_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "in/to/from class X"
        prep_pattern = re.compile(r"(?:in|to|from)\s+(?:the\s+)?(\w+)\s+class", re.IGNORECASE)
        matches = prep_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "class X" or "a new class X" (captures the last word)
        last_word_pattern = re.compile(r"(?:a\s+(?:new\s+)?)?class\s+(\w+)(?:\s|$)", re.IGNORECASE)
        matches = last_word_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None

    
    def _extract_parameters(self, command):
        """Extract parameters for methods/functions"""
        # Pattern for "with parameter(s) X, Y, Z"
        param_pattern = re.compile(r"with\s+parameters?\s+([\w\s,]+)(?:\s+(?:in|to))?", re.IGNORECASE)
        matches = param_pattern.search(command)
        if matches:
            param_text = matches.group(1)
            # Clean and split parameters, removing trailing class reference
            params = []
            raw_params = re.split(r',|\s+and\s+', param_text)
            for p in raw_params:
                p = p.strip()
                if p and p.lower() not in ["in", "to", "from"]:
                    # Remove any trailing "to/in class X" part
                    p = re.sub(r'\s+(?:to|in)\s+\w+\s+class$', '', p)
                    params.append(p)
            return params
            
        return None
    
    def _extract_attributes(self, command):
        """Extract attributes for add/remove attribute operations with improved patterns"""
        # Pattern for "attribute X" or "an attribute X"
        attr_pattern = re.compile(r"(?:an?\s+)?attribute\s+(\w+)", re.IGNORECASE)
        matches = attr_pattern.search(command)
        if matches and matches.group(1).lower() not in ["to", "from", "in", "named", "called"]:
            return [matches.group(1)]
            
        # Pattern for "attributes X, Y, Z"
        attrs_pattern = re.compile(r"attributes?\s+([\w\s,]+)(?:\s+(?:to|from))?", re.IGNORECASE)
        matches = attrs_pattern.search(command)
        if matches:
            attr_text = matches.group(1)
            # Clean and split attributes
            attrs = []
            raw_attrs = re.split(r',|\s+and\s+', attr_text)
            for a in raw_attrs:
                a = a.strip()
                if a and not any(word in a.lower() for word in ["class", "to", "from"]):
                    attrs.append(a)
            return attrs
            
        # Pattern for "attribute called X"
        called_pattern = re.compile(r"attribute\s+(?:called|named)\s+(\w+)", re.IGNORECASE)
        matches = called_pattern.search(command)
        if matches:
            return [matches.group(1)]

        # Pattern for "X attribute" (like "email attribute")
        single_attr_pattern = re.compile(r"(?:the\s+)?(\w+)\s+attribute", re.IGNORECASE)
        matches = single_attr_pattern.search(command)
        if matches and matches.group(1).lower() not in ["an", "a", "the", "new", "add"]:
            return [matches.group(1)]
            
        # Additional pattern for "add X to Y class" format
        add_to_pattern = re.compile(r"add\s+(\w+)\s+to", re.IGNORECASE)
        matches = add_to_pattern.search(command)
        if matches and matches.group(1).lower() not in ["an", "a", "the", "attribute"]:
            return [matches.group(1)]
            
        return None
    
    def _extract_class_for_attribute(self, command):
        """Extract the class name for attribute operations"""
        # Pattern for "to/from X class"
        class_pattern = re.compile(r"(?:to|from)\s+(?:the\s+)?(\w+)\s+class", re.IGNORECASE)
        matches = class_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None
    
    def _extract_class_for_method(self, command):
        """Extract the class name for method operations"""
        # Pattern for "in the X class"
        class_pattern = re.compile(r"in\s+(?:the\s+)?(\w+)\s+class", re.IGNORECASE)
        matches = class_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None
    
    def _extract_old_class_name(self, command):
        """Extract old class name for rename operations"""
        # Pattern for "rename X class"
        rename_pattern = re.compile(r"rename\s+(?:the\s+)?(\w+)\s+class", re.IGNORECASE)
        matches = rename_pattern.search(command)
        if matches and matches.group(1).lower() not in ["named", "called", "the"]:
            return matches.group(1)
        
        # Pattern for "rename the class named X"
        named_pattern = re.compile(r"rename\s+(?:the\s+)?class\s+(?:named|called)\s+(\w+)", re.IGNORECASE)
        matches = named_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "class X"    
        class_x_pattern = re.compile(r"class\s+(\w+)", re.IGNORECASE)
        matches = class_x_pattern.search(command)
        if matches and matches.group(1).lower() not in ["named", "called", "the"]:
            return matches.group(1)
                
        return None
    
    def _extract_new_class_name(self, command):
        """Extract new class name for rename operations"""
        # Pattern for "to X"
        to_pattern = re.compile(r"to\s+(\w+)(?:\s+class)?", re.IGNORECASE)
        matches = to_pattern.search(command)
        if matches:
            return matches.group(1)
        
        # Check for "as X" pattern
        as_pattern = re.compile(r"as\s+(\w+)(?:\s+class)?", re.IGNORECASE)
        matches = as_pattern.search(command)
        if matches:
            return matches.group(1)
                
        return None
    
    def _extract_old_method_name(self, command):
        """Extract old method name for rename operations"""
        # Pattern for "rename X method"
        rename_pattern = re.compile(r"rename\s+(?:the\s+)?(\w+)\s+method", re.IGNORECASE)
        matches = rename_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "rename method X"
        alt_pattern = re.compile(r"rename\s+(?:the\s+)?method\s+(?:called|named)?\s*(\w+)", re.IGNORECASE)
        matches = alt_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Pattern for "method called X"
        called_pattern = re.compile(r"method\s+(?:called|named)\s+(\w+)", re.IGNORECASE)
        matches = called_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None

    
    def _extract_new_method_name(self, command):
        """Extract new method name for rename operations"""
        # Pattern for "to X"
        to_pattern = re.compile(r"to\s+(\w+)(?:\s+in)?", re.IGNORECASE)
        matches = to_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None
    
    def _extract_loop_type(self, command):
        """Extract loop type (for or while)"""
        if "for" in command.split():
            return "for"
        elif "while" in command.split():
            return "while"
        return "for"  # Default
    
    def _extract_conditional_type(self, command):
        """Extract conditional type (if/else or switch/case)"""
        if "switch" in command or "case" in command:
            return "switch"
        return "if_else"  # Default
    
    def _extract_container_name(self, command):
        """Extract name of method/function to add loop/conditional to"""
        # Pattern for "to the X method/function"
        to_pattern = re.compile(r"to\s+(?:the\s+)?(\w+)\s+(?:method|function)", re.IGNORECASE)
        matches = to_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Additional pattern for "handle_action function"
        func_pattern = re.compile(r"(?:the\s+)?(\w+)\s+(?:method|function)", re.IGNORECASE)
        matches = func_pattern.search(command)
        if matches and matches.group(1).lower() not in ["a", "the", "if/else", "for", "while", "switch/case", "add"]:
            return matches.group(1)
            
        return None
    
    def _extract_child_class(self, command):
        """Extract child class for inheritance operations"""
        # Pattern for "make X class inherit"
        make_pattern = re.compile(r"make\s+(?:the\s+)?(\w+)\s+class\s+inherit", re.IGNORECASE)
        matches = make_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None
    
    def _extract_parent_class(self, command):
        """Extract parent class for inheritance operations"""
        # Pattern for "from X class"
        from_pattern = re.compile(r"from\s+(?:the\s+)?(\w+)\s+class", re.IGNORECASE)
        matches = from_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None
    
    def _extract_method_to_override(self, command):
        """Extract method name for polymorphism operations"""
        # Pattern for "override X method"
        override_pattern = re.compile(r"override\s+(?:the\s+)?(\w+)\s+method", re.IGNORECASE)
        matches = override_pattern.search(command)
        if matches:
            return matches.group(1)
            
        # Generic pattern looking for a method name
        method_pattern = re.compile(r"(?:the\s+)?(\w+)\s+method", re.IGNORECASE)
        matches = method_pattern.search(command)
        if matches:
            return matches.group(1)
            
        return None

# Example usage
if __name__ == "__main__":
    parser = CommandParser()
    
    test_commands = [
        "Add a method called eat with parameter food to Animal class",
        "Create a function named calculate_area with parameters width and height in Rectangle class",
        "Delete the run method from the Dog class",
        "Add a class called Customer",
        "Remove the Person class",
        "Add attributes name, age, and address to User class",
        "Remove the email attribute from Customer class",
        "Rename the speak method to talk in the Person class",
        "Rename the User class to Customer",
        "Add a standalone function called calculate_tax outside any class",
        "Delete the function process_payment",
        "Add a for loop to the process_items method",
        "Add a while loop to the read_file function",
        "Add if/else conditional to the validate method",
        "Add a switch/case statement to handle_action function",
        "Make Customer class inherit from Person class",
        "Add polymorphism by overriding speak method"
    ]
    
    for cmd in test_commands:
        intent = parser.parse_command(cmd)
        print(f"Command: {cmd}")
        print(f"Intent: {json.dumps(intent, indent=2)}")
        print("-" * 50)