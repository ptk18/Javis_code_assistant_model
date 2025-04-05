import json
import os
import time
import traceback
from code_analyzer import extract_code_structure
from command_parser import CommandParser
from code_generator import CodeGenerator, process_command

def print_json(data):
    """Pretty print JSON data"""
    print(json.dumps(data, indent=2))

# def process_command_with_generator(original_code, command_intent, code_analysis):
#     """
#     Process a command with enhanced error handling and support for all code_generator actions
#     """
#     try:
#         return process_command(original_code, command_intent, code_analysis)
#     except Exception as e:
#         # Fall back to creating a CodeGenerator instance directly if process_command fails
#         try:
#             generator = CodeGenerator()
#             generator.load_code(original_code)
#             generator.load_intent(command_intent)
#             generator.load_analysis(code_analysis)
#             return generator.generate_modified_code()
#         except Exception as inner_e:
#             # If both approaches fail, provide detailed error information
#             print(f"Error in code generation: {str(inner_e)}")
#             print("Command intent was:", json.dumps(command_intent, indent=2))
#             print("Traceback:")
#             traceback.print_exc()
#             return f"Error: {str(inner_e)}"

# In javis.py, update the process_command_with_generator function to
# handle and fix common parsing issues with rename commands

def process_command_with_generator(original_code, command_intent, code_analysis):
    """
    Process a command with enhanced error handling and support for all code_generator actions
    """
    # Fix common parsing issues
    fixed_intent = fix_common_intent_issues(command_intent, code_analysis)
    
    try:
        return process_command(original_code, fixed_intent, code_analysis)
    except Exception as e:
        # Fall back to creating a CodeGenerator instance directly if process_command fails
        try:
            generator = CodeGenerator()
            generator.load_code(original_code)
            generator.load_intent(fixed_intent)
            generator.load_analysis(code_analysis)
            return generator.generate_modified_code()
        except Exception as inner_e:
            # If both approaches fail, provide detailed error information
            print(f"Error in code generation: {str(inner_e)}")
            print("Command intent was:", json.dumps(fixed_intent, indent=2))
            print("Traceback:")
            traceback.print_exc()
            return f"Error: {str(inner_e)}"

def fix_common_intent_issues(intent, code_analysis):
    """Fix common issues with parsed intents"""
    fixed_intent = intent.copy()
    
    # Handle rename_class specific issues
    if fixed_intent.get('action') == 'rename_class':
        # Check if target_class is "the" - this is a common parsing error
        if fixed_intent.get('target_class') == 'the':
            # Try to extract the class name from other fields
            if 'old_name' in fixed_intent:
                fixed_intent['target_class'] = fixed_intent['old_name']
            elif 'new_class_name' in fixed_intent:
                # Look for any class that exists in the code analysis
                for class_name in code_analysis.get('classes', {}):
                    if class_name.lower() not in ['the', fixed_intent.get('new_class_name', '').lower()]:
                        fixed_intent['target_class'] = class_name
                        break
        
        # Make sure we have both old and new names
        if 'target_class' in fixed_intent and 'old_name' not in fixed_intent:
            fixed_intent['old_name'] = fixed_intent['target_class']
        
        if 'new_class_name' in fixed_intent and 'new_name' not in fixed_intent:
            fixed_intent['new_name'] = fixed_intent['new_class_name']
    
    # Handle rename_method specific issues
    if fixed_intent.get('action') == 'rename_method':
        if 'new_method_name' in fixed_intent and 'new_name' not in fixed_intent:
            fixed_intent['new_name'] = fixed_intent['new_method_name']
        
        if 'method_name' in fixed_intent and 'old_name' not in fixed_intent:
            fixed_intent['old_name'] = fixed_intent['method_name']
    
    # Apply case-insensitive matching for class names
    if 'target_class' in fixed_intent:
        target_class_lower = fixed_intent['target_class'].lower()
        for class_name in code_analysis.get('classes', {}):
            if class_name.lower() == target_class_lower:
                fixed_intent['target_class'] = class_name
                break
    
    return fixed_intent

def interactive_mode():
    """Run an interactive session that allows code analysis, command parsing, and code generation"""
    parser = CommandParser()
    original_code = None
    code_analysis = None
    
    print("=== Python Code Assistant ===")
    print("Type 'help' for available commands")
    
    while True:
        if original_code is None:
            cmd = input("\nPlease enter code to analyze or load a file (or 'help'): ").strip()
        else:
            cmd = input("\nEnter a command (or 'quit' to exit): ").strip()
        
        if cmd.lower() in ('exit', 'quit'):
            break
            
        elif cmd.lower() == 'help':
            print("\nAvailable commands:")
            print("  load <file.py>              - Load Python file")
            print("  show                        - Show current code")
            print("  analyze                     - Analyze current code")
            print("  clear                       - Clear current code")
            print("  intent <command>            - Show parsed intent without modifying code")
            print("  help                        - Show this help")
            print("  examples                    - Show example commands")
            print("  quit/exit                   - Exit the program")
            print("\nOr type a natural language command like:")
            print("  Add a method called eat with parameter food to Animal class")
            
        elif cmd.lower() == 'examples':
            print("\nExample commands:")
            print("  • Add a method called eat with parameter food to Animal class")
            print("  • Remove the speak method from Dog class")
            print("  • Add a class called Customer with attributes name and email")
            print("  • Remove the Person class")
            print("  • Add attribute address to User class")
            print("  • Remove the email attribute from Customer class")
            print("  • Rename the speak method to talk in Animal class")
            print("  • Rename User class to Customer")
            print("  • Add a function called calculate_tax")
            print("  • Add a for loop to the process_items method")
            print("  • Add an if-else statement to the validate method")
            print("  • Make Customer class inherit from Person class")
            print("  • Add abstract method process to BaseHandler class")
            
        elif cmd.lower().startswith('load'):
            parts = cmd.split(' ', 1)
            if len(parts) > 1:
                file_path = parts[1].strip()
                if os.path.exists(file_path):
                    try:
                        with open(file_path, 'r') as f:
                            original_code = f.read()
                        print(f"Loaded file: {file_path}")
                        print("=== ORIGINAL CODE ===")
                        print(original_code)
                        print("===================")
                        
                        # Automatically analyze the code
                        code_analysis = extract_code_structure(original_code)
                    except Exception as e:
                        print(f"Error loading file: {str(e)}")
                else:
                    print(f"File not found: {file_path}")
                
        elif cmd.lower() == 'show':
            if original_code:
                print("=== CURRENT CODE ===")
                print(original_code)
                print("===================")
            else:
                print("No code loaded. Use 'load <file.py>' or paste code directly.")
                
        elif cmd.lower() == 'analyze':
            if original_code:
                start_time = time.time()
                code_analysis = extract_code_structure(original_code)
                duration = time.time() - start_time
                print(f"Analysis completed in {duration:.3f} seconds:")
                print_json(code_analysis)
            else:
                print("No code loaded. Use 'load <file.py>' or paste code directly.")
                
        elif cmd.lower().startswith('intent '):
            # Show the parsed intent without modifying code
            command_text = cmd[7:].strip()  # Remove 'intent ' prefix
            intent = parser.parse_command(command_text)
            print("Parsed intent:")
            print_json(intent)
                
        elif cmd.lower() == 'clear':
            original_code = None
            code_analysis = None
            print("Code cleared.")
            
        elif original_code is None and not cmd.lower().startswith(('help', 'load', 'quit', 'exit', 'examples')):
            # Treat input as code if no code is loaded yet
            original_code = cmd
            print("=== ORIGINAL CODE ===")
            print(original_code)
            print("===================")
            
            # Automatically analyze the code
            code_analysis = extract_code_structure(original_code)
            
        elif original_code and code_analysis:
            # Process as a command for modifying code
            start_time = time.time()
            command_intent = parser.parse_command(cmd)
            print("Command intent:", json.dumps(command_intent, indent=2))
            
            try:
                modified_code = process_command_with_generator(original_code, command_intent, code_analysis)
                duration = time.time() - start_time
                
                if modified_code.startswith("Error:"):
                    print(modified_code)
                else:
                    print(f"=== MODIFIED CODE (took {duration:.3f} seconds) ===")
                    print(modified_code)
                    print("=====================")
                    
                    # Update the code and analysis
                    original_code = modified_code
                    code_analysis = extract_code_structure(original_code)
            except Exception as e:
                print(f"Error generating code: {str(e)}")
                print("Traceback:")
                traceback.print_exc()
                
        else:
            print(f"Unknown command or no code loaded: {cmd}")
            print("Type 'help' for available commands")

def main():
    interactive_mode()

if __name__ == "__main__":
    main()