import textwrap
from typing import Dict, Any, Tuple
from intent_classifier import extract_intent_and_entities
from code_transformer import parse_code, modify_code_with_libcst

def process_natural_language_command(text: str, code: str) -> Tuple[str, Dict[str, Any]]:
    """Process a natural language command and apply it to code"""

    print("Analyzing command...")
    nlu_result = extract_intent_and_entities(text)
    
    print("Parsing code structure...")
    code_structure = parse_code(code)
    
    result_info = {
        "intent": nlu_result["intent"],
        "entities": nlu_result["entities"],
        "code_structure": code_structure
    }
    
    if nlu_result['intent'] in ["add", "modify", "delete"]:
        print(f"Applying {nlu_result['intent']} operation...")
        modified_code = modify_code_with_libcst(
            code, 
            nlu_result['intent'], 
            nlu_result['entities'], 
            nlu_result['full_text']
        )
        return modified_code, result_info
    elif nlu_result['intent'] == "explain":
        print("Generating explanation...")

        return code, result_info
    
    return code, result_info

def main():
    print("JAVIS: Code Modification Assistant")
    print("==================================")
    
    code_string = textwrap.dedent("""
    class Animal:
        def __init__(self):
            pass
        def sound(self):
            return "generic sound"
    """)
    
    examples = [
        "Add a method called eat to Animal class",
        "Delete a method called sound from Animal class",
        "Rename the class called Animal to Mammal",
        "Delete the class called Animal",
        "Explain what this code does"
    ]
    
    print("Initial Code:")
    print(code_string)
    print("\nAvailable commands:")
    for i, example in enumerate(examples):
        print(f"{i+1}. {example}")
    
    while True:
        print("\nEnter your command (or 'q' to quit):")
        user_input = input("> ")
        
        if user_input.lower() == 'q':
            break
            
        modified_code, result_info = process_natural_language_command(user_input, code_string)
        
        if modified_code != code_string:
            code_string = modified_code
            
        print("\nIntent:", result_info["intent"])
        print("Entities:", result_info["entities"])
        print("\nUpdated Code:")
        print(code_string)

if __name__ == "__main__":
    main()