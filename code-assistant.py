import os
import requests
import json
from typing import Dict, List, Optional, Tuple, Union

class CodeModificationAssistant:
    def __init__(self, initial_code="", api_key=None):
        """Initialize the assistant with optional initial code and API key for LLM services."""
        self.code = initial_code
        self.history = [("initial", initial_code)]
        self.running = True
        self.api_key = api_key or os.environ.get("LLM_API_KEY")
        self.api_url = os.environ.get("LLM_API_URL", "https://api.openai.com/v1/chat/completions")
        
    def start(self):
        """Start the interactive code modification session."""
        print("Code Modification Assistant with LLM Capabilities")
        print("===============================================")
        
        if not self.api_key:
            print("\nWarning: No API key set for LLM services.")
            print("Set the LLM_API_KEY environment variable or provide it during initialization.")
            print("Limited LLM functionality will be available.")
        
        if self.code:
            print("\nInitial code:")
            print(self.display_code())
        
        print("\nEnter commands to modify the code.")
        print("Type 'help' for available commands, 'quit' to exit.")
        
        while self.running:
            command = input("\n> ").strip()
            self.process_command(command)
    
    def process_command(self, command):
        """Process user commands."""
        if command.lower() == "quit" or command.lower() == "exit":
            self.running = False
            print("Exiting. Final code:")
            print(self.display_code())
            return
            
        elif command.lower() == "help":
            self.show_help()
            
        elif command.lower() == "show":
            print(self.display_code())
            
        elif command.lower() == "history":
            self.show_history()
            
        elif command.lower().startswith("undo"):
            self.undo()
            
        elif command.lower().startswith("add "):
            # Extract line number and content
            parts = command[4:].strip().split(" ", 1)
            if len(parts) < 2:
                print("Error: 'add' command requires line number and content")
                return
                
            try:
                line_num = int(parts[0])
                content = parts[1]
                self.add_line(line_num, content)
            except ValueError:
                print(f"Error: Invalid line number '{parts[0]}'")
                
        elif command.lower().startswith("replace "):
            # Extract line number and content
            parts = command[8:].strip().split(" ", 1)
            if len(parts) < 2:
                print("Error: 'replace' command requires line number and content")
                return
                
            try:
                line_num = int(parts[0])
                content = parts[1]
                self.replace_line(line_num, content)
            except ValueError:
                print(f"Error: Invalid line number '{parts[0]}'")
                
        elif command.lower().startswith("delete "):
            # Extract line number
            try:
                line_num = int(command[7:].strip())
                self.delete_line(line_num)
            except ValueError:
                print(f"Error: Invalid line number '{command[7:].strip()}'")
                
        elif command.lower().startswith("import "):
            # Add an import statement at the top
            self.add_import(command[7:].strip())
            
        elif command.lower().startswith("function "):
            # Add a new function
            self.add_function(command[9:].strip())
            
        elif command.lower() == "indent":
            self.indent_code()
            
        elif command.lower() == "dedent":
            self.dedent_code()
            
        elif command.lower().startswith("improve"):
            # Improve the code using LLM
            parts = command.split(" ", 1)
            instructions = parts[1] if len(parts) > 1 else "Make this code more professional and efficient"
            self.improve_code(instructions)
            
        elif command.lower().startswith("generate "):
            # Generate code using LLM based on description
            self.generate_code(command[9:].strip())
            
        elif command.lower().startswith("explain"):
            # Explain the current code
            self.explain_code()
            
        elif command.lower().startswith("refactor"):
            # Refactor the code
            parts = command.split(" ", 1)
            instructions = parts[1] if len(parts) > 1 else "Refactor this code to be more efficient and follow best practices"
            self.refactor_code(instructions)
            
        elif command.lower().startswith("optimize"):
            # Optimize the code
            parts = command.split(" ", 1)
            focus = parts[1] if len(parts) > 1 else "performance"
            self.optimize_code(focus)
            
        elif command.lower().startswith("comment"):
            # Add comments to the code
            self.add_comments()
            
        elif command.lower().startswith("docstring"):
            # Generate or improve docstrings
            self.improve_docstrings()
            
        elif command.lower().startswith("test"):
            # Generate test cases
            self.generate_tests()
            
        else:
            print("Unknown command. Type 'help' for available commands.")
    
    def call_llm(self, prompt: str, system_message: str = "You are a helpful assistant") -> str:
        """Call the language model API with a prompt and return the response."""
        if not self.api_key:
            return "Error: No API key set for LLM services. Set the LLM_API_KEY environment variable or provide it during initialization."
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": "gpt-4",  # Or your preferred model
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # Low temperature for more predictable outputs
                "max_tokens": 2048
            }
            
            response = requests.post(self.api_url, headers=headers, data=json.dumps(data))
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"]
            else:
                return f"Error: API request failed with status code {response.status_code}. Response: {response.text}"
                
        except Exception as e:
            return f"Error calling LLM API: {str(e)}"
    
    def improve_code(self, instructions: str):
        """Improve the code using the LLM."""
        if not self.code.strip():
            print("Error: No code to improve.")
            return
            
        prompt = f"""
I have the following code that I want to improve. Please provide an improved version based on these instructions: {instructions}

Here is the code:
```
{self.code}
```

Please respond with ONLY the improved code, no explanations or additional text. The improved code should be complete and functional.
"""
        
        system_message = "You are an expert programmer who writes clean, efficient, professional code following best practices."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            improved_code = rest.strip()
                        else:
                            improved_code = part.strip()
                    else:
                        improved_code = part.strip()
                    break
        else:
            improved_code = response.strip()
        
        self.history.append(("improve", self.code))
        self.code = improved_code
        print(f"Code improved according to: {instructions}")
    
    def generate_code(self, description: str):
        """Generate code based on a description using the LLM."""
        prompt = f"""
Please write professional Python code based on this description: {description}

The code should be:
1. Complete and functional
2. Well-structured and follow Python best practices
3. Include proper error handling
4. Include clear docstrings and comments

Please respond with ONLY the generated code, no explanations or additional text.
"""
        
        system_message = "You are an expert Python programmer who writes clean, efficient, professional code following best practices."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            generated_code = rest.strip()
                        else:
                            generated_code = part.strip()
                    else:
                        generated_code = part.strip()
                    break
        else:
            generated_code = response.strip()
        
        if self.code and not self.code.endswith("\n\n"):
            if self.code.endswith("\n"):
                self.code += "\n"
            else:
                self.code += "\n\n"
                
        self.history.append(("generate", self.code))
        
        # If there's already code, append the new code; otherwise, set it
        if self.code.strip():
            self.code += generated_code
        else:
            self.code = generated_code
            
        print(f"Generated code based on: {description}")
    
    def explain_code(self):
        """Explain the current code using the LLM."""
        if not self.code.strip():
            print("Error: No code to explain.")
            return
            
        prompt = f"""
Please explain the following code. Focus on what it does, its structure, and any potential issues or improvements:

```python
{self.code}
```

Provide a clear, concise explanation suitable for intermediate programmers.
"""
        
        system_message = "You are an expert programmer who explains code clearly and concisely."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        print("\nExplanation of the current code:")
        print(response)
    
    def refactor_code(self, instructions: str):
        """Refactor the code using the LLM."""
        if not self.code.strip():
            print("Error: No code to refactor.")
            return
            
        prompt = f"""
I have the following code that I want to refactor. Please provide a refactored version based on these instructions: {instructions}

Here is the code:
```python
{self.code}
```

Please respond with ONLY the refactored code, no explanations or additional text. The refactored code should be complete and functional.
"""
        
        system_message = "You are an expert programmer who specializes in code refactoring and improving code quality."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            refactored_code = rest.strip()
                        else:
                            refactored_code = part.strip()
                    else:
                        refactored_code = part.strip()
                    break
        else:
            refactored_code = response.strip()
        
        self.history.append(("refactor", self.code))
        self.code = refactored_code
        print(f"Code refactored according to: {instructions}")
    
    def optimize_code(self, focus: str):
        """Optimize the code with a specific focus using the LLM."""
        if not self.code.strip():
            print("Error: No code to optimize.")
            return
            
        prompt = f"""
I have the following code that I want to optimize for {focus}. Please provide an optimized version:

```python
{self.code}
```

Please respond with ONLY the optimized code, no explanations or additional text. The optimized code should be complete and functional.
"""
        
        system_message = f"You are an expert programmer who specializes in optimizing code for {focus}."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            optimized_code = rest.strip()
                        else:
                            optimized_code = part.strip()
                    else:
                        optimized_code = part.strip()
                    break
        else:
            optimized_code = response.strip()
        
        self.history.append(("optimize", self.code))
        self.code = optimized_code
        print(f"Code optimized for {focus}")
    
    def add_comments(self):
        """Add comments to the code using the LLM."""
        if not self.code.strip():
            print("Error: No code to comment.")
            return
            
        prompt = f"""
Please add clear, helpful comments to the following code. The comments should explain what the code does and why, focusing on complex or non-obvious parts:

```python
{self.code}
```

Please respond with ONLY the code with added comments, no explanations or additional text.
"""
        
        system_message = "You are an expert programmer who writes clear, helpful code comments."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            commented_code = rest.strip()
                        else:
                            commented_code = part.strip()
                    else:
                        commented_code = part.strip()
                    break
        else:
            commented_code = response.strip()
        
        self.history.append(("comment", self.code))
        self.code = commented_code
        print("Added comments to the code")
    
    def improve_docstrings(self):
        """Improve or add docstrings to the code using the LLM."""
        if not self.code.strip():
            print("Error: No code to improve docstrings.")
            return
            
        prompt = f"""
Please improve or add proper docstrings to the following Python code. Follow Google-style docstring format with:
- A clear description of what the function/class does
- Parameter descriptions with types
- Return value descriptions with types
- Exception descriptions if applicable

Here's the code:

```python
{self.code}
```

Please respond with ONLY the code with improved docstrings, no explanations or additional text.
"""
        
        system_message = "You are an expert Python programmer who writes excellent, detailed docstrings."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            improved_code = rest.strip()
                        else:
                            improved_code = part.strip()
                    else:
                        improved_code = part.strip()
                    break
        else:
            improved_code = response.strip()
        
        self.history.append(("docstring", self.code))
        self.code = improved_code
        print("Improved docstrings in the code")
    
    def generate_tests(self):
        """Generate test cases for the code using the LLM."""
        if not self.code.strip():
            print("Error: No code to generate tests for.")
            return
            
        prompt = f"""
Please generate comprehensive unit tests for the following Python code using pytest. The tests should:
- Cover all functions and methods
- Test normal usage and edge cases
- Include descriptive docstrings explaining each test

Here's the code:

```python
{self.code}
```

Please respond with ONLY the test code, no explanations or additional text.
"""
        
        system_message = "You are an expert in Python testing who writes comprehensive, clear test suites."
        response = self.call_llm(prompt, system_message)
        
        if response.startswith("Error:"):
            print(response)
            return
            
        # Extract code from response if there are markdown code blocks
        if "```" in response:
            # Extract code from between code blocks if present
            code_parts = response.split("```")
            for i, part in enumerate(code_parts):
                if i % 2 == 1:  # This is inside a code block
                    # Remove language specification if present
                    if part.strip() and "\n" in part:
                        first_line, rest = part.split("\n", 1)
                        if not first_line.strip() or first_line.strip() in ["python", "py"]:
                            test_code = rest.strip()
                        else:
                            test_code = part.strip()
                    else:
                        test_code = part.strip()
                    break
        else:
            test_code = response.strip()
        
        # Create a new file for tests
        if self.code.strip():
            # Add tests as a new section at the end
            if not self.code.endswith("\n\n"):
                if self.code.endswith("\n"):
                    self.code += "\n"
                else:
                    self.code += "\n\n"
                    
            self.code += "# Test cases\n" + test_code
            print("Generated test cases and added them to the code")
        else:
            self.code = test_code
            print("Generated test cases")
            
        self.history.append(("tests", self.code))
    
    def add_line(self, line_num, content):
        """Add a new line at the specified position."""
        lines = self.code.split("\n")
        
        if line_num < 1 or line_num > len(lines) + 1:
            print(f"Error: Line number out of range (1-{len(lines) + 1})")
            return
            
        lines.insert(line_num - 1, content)
        new_code = "\n".join(lines)
        self.history.append(("add", self.code))
        self.code = new_code
        print(f"Added line {line_num}: {content}")
    
    def replace_line(self, line_num, content):
        """Replace a line at the specified position."""
        lines = self.code.split("\n")
        
        if line_num < 1 or line_num > len(lines):
            print(f"Error: Line number out of range (1-{len(lines)})")
            return
            
        self.history.append(("replace", self.code))
        lines[line_num - 1] = content
        self.code = "\n".join(lines)
        print(f"Replaced line {line_num} with: {content}")
    
    def delete_line(self, line_num):
        """Delete the line at the specified position."""
        lines = self.code.split("\n")
        
        if line_num < 1 or line_num > len(lines):
            print(f"Error: Line number out of range (1-{len(lines)})")
            return
            
        deleted_line = lines.pop(line_num - 1)
        self.history.append(("delete", self.code))
        self.code = "\n".join(lines)
        print(f"Deleted line {line_num}: {deleted_line}")
    
    def add_import(self, import_statement):
        """Add an import statement at the top of the code."""
        lines = self.code.split("\n")
        
        # Find where the imports end
        import_end = 0
        for i, line in enumerate(lines):
            if line.strip() and not (line.strip().startswith("import ") or line.strip().startswith("from ")):
                import_end = i
                break
        
        self.history.append(("add_import", self.code))
        lines.insert(import_end, f"import {import_statement}")
        self.code = "\n".join(lines)
        print(f"Added import: import {import_statement}")
    
    def add_function(self, function_signature):
        """Add a new function at the end of the code."""
        self.history.append(("add_function", self.code))
        
        function_template = f"""
def {function_signature}:
    \"\"\"Add docstring here.\"\"\"
    pass
"""
        if self.code and not self.code.endswith("\n\n"):
            if self.code.endswith("\n"):
                self.code += "\n"
            else:
                self.code += "\n\n"
                
        self.code += function_template
        print(f"Added function: {function_signature}")
    
    def indent_code(self):
        """Indent all lines by 4 spaces."""
        self.history.append(("indent", self.code))
        lines = [f"    {line}" for line in self.code.split("\n")]
        self.code = "\n".join(lines)
        print("Indented all code by 4 spaces.")
    
    def dedent_code(self):
        """Remove 4 spaces of indentation from all lines where possible."""
        self.history.append(("dedent", self.code))
        lines = []
        for line in self.code.split("\n"):
            if line.startswith("    "):
                lines.append(line[4:])
            else:
                lines.append(line)
        self.code = "\n".join(lines)
        print("Removed 4 spaces of indentation where possible.")
    
    def undo(self):
        """Undo the last modification."""
        if len(self.history) <= 1:
            print("Nothing to undo.")
            return
            
        op, prev_code = self.history.pop()
        self.code = prev_code
        print(f"Undid last operation ({op}).")
    
    def show_history(self):
        """Show the history of operations."""
        print("\nOperation history:")
        for i, (op, _) in enumerate(self.history):
            print(f"{i+1}. {op}")
    
    def show_help(self):
        """Display help information."""
        help_text = """
Available commands:
- show                     : Display the current code
- add <line> <content>     : Add a new line at specified position
- replace <line> <content> : Replace a line at specified position
- delete <line>            : Delete a line at specified position
- import <module>          : Add an import statement
- function <signature>     : Add a new function (e.g., function calculate(x, y))
- indent                   : Indent all code by 4 spaces
- dedent                   : Remove 4 spaces of indentation where possible
- undo                     : Undo the last modification
- history                  : Show history of operations

LLM-powered commands:
- improve [instructions]   : Improve the code (optional: provide specific instructions)
- generate <description>   : Generate new code based on a description
- explain                  : Explain what the current code does
- refactor [instructions]  : Refactor the code (optional: provide specific instructions)
- optimize [focus]         : Optimize the code (optional: specify focus like "performance" or "memory")
- comment                  : Add helpful comments to the code
- docstring                : Improve or add proper docstrings
- test                     : Generate test cases for the code

- help                     : Show this help message
- quit                     : Exit and display final code
"""
        print(help_text)
    
    def display_code(self):
        """Format the code for display with line numbers."""
        if not self.code.strip():
            return "[No code yet]"
            
        lines = self.code.split("\n")
        max_line_num_width = len(str(len(lines)))
        
        numbered_lines = []
        for i, line in enumerate(lines):
            line_num = str(i + 1).rjust(max_line_num_width)
            numbered_lines.append(f"{line_num} | {line}")
            
        return "\n".join(numbered_lines)


# Example usage
if __name__ == "__main__":
    initial_code = """def hello_world():
    print("Hello, World!")
    
hello_world()"""
    
    # To use with LLM capabilities, provide your API key:
    # api_key = "your_api_key_here"  # Or set LLM_API_KEY environment variable
    # assistant = CodeModificationAssistant(initial_code, api_key)
    
    # Or use without LLM capabilities (limited functionality):
    assistant = CodeModificationAssistant(initial_code)
    assistant.start()