import torch
from torch import nn
from transformers import BertModel, BertTokenizer, AutoModelForCausalLM, AutoTokenizer
import ast
import astor
import re
import textwrap

class CodeAssistantModel:
    def __init__(self, bert_model_name='bert-base-uncased', llm_model_name='gpt2'):
        # Initialize BERT for high-level intent classification
        self.intent_tokenizer = BertTokenizer.from_pretrained(bert_model_name)
        self.bert_model = BertModel.from_pretrained(bert_model_name)
        
        # Initialize a much simpler intent classifier with fewer categories
        self.intent_classifier = nn.Linear(768, 3)  # Just 3 high-level intents
        self.intent_labels = ["add", "modify", "delete"]
        
        # Initialize LLM for code generation
        self.llm_tokenizer = AutoTokenizer.from_pretrained(llm_model_name)
        self.llm_model = AutoModelForCausalLM.from_pretrained(llm_model_name)
        
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.bert_model.to(self.device)
        self.intent_classifier.to(self.device)
        self.llm_model.to(self.device)
    
    def classify_high_level_intent(self, command):
        """Classify command into high-level intent categories"""
        tokens = self.intent_tokenizer(command, padding='max_length', max_length=128, 
                                      truncation=True, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            outputs = self.bert_model(**tokens)
            pooled_output = outputs.pooler_output
        
        intent_logits = self.intent_classifier(pooled_output)
        intent_id = torch.argmax(intent_logits, dim=1).item()
        return self.intent_labels[intent_id]
    
    def modify_code(self, code_string, command):
        """Use LLM to generate modified code based on the original code and command"""
        # Optionally get high-level intent for context
        high_level_intent = self.classify_high_level_intent(command)
        
        # Create a prompt for the LLM
        prompt = f"""
Original code:
```python
{code_string}
```

Modification request: {command}

Modified code:
```python
"""
        
        # Generate completion with LLM
        input_ids = self.llm_tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        attention_mask = torch.ones(input_ids.shape, device=self.device)
        
        output = self.llm_model.generate(
            input_ids, 
            attention_mask=attention_mask,
            max_length=1024,
            temperature=0.2,
            top_p=0.95,
            do_sample=True,
            pad_token_id=self.llm_tokenizer.eos_token_id
        )
        
        generated_text = self.llm_tokenizer.decode(output[0], skip_special_tokens=True)
        
        # Extract the modified code from the generated text
        pattern = r"Modified code:\n```python\n(.*?)```"
        match = re.search(pattern, generated_text, re.DOTALL)
        
        if match:
            modified_code = match.group(1).strip()
            
            # Validate that the generated code is valid Python
            try:
                ast.parse(modified_code)
                return modified_code
            except SyntaxError:
                # If there's a syntax error, try to fix it with another LLM call
                return self._fix_syntax_errors(modified_code)
        else:
            # If pattern not found, return the whole generated text
            return generated_text
    
    def _fix_syntax_errors(self, code_with_errors):
        """Fix syntax errors in generated code"""
        prompt = f"""
The following Python code has syntax errors. Please fix them:
```python
{code_with_errors}
```

Fixed code:
```python
"""
        
        input_ids = self.llm_tokenizer.encode(prompt, return_tensors="pt").to(self.device)
        attention_mask = torch.ones(input_ids.shape, device=self.device)
        
        output = self.llm_model.generate(
            input_ids, 
            attention_mask=attention_mask,
            max_length=1024,
            temperature=0.2,
            top_p=0.95,
            do_sample=True,
            pad_token_id=self.llm_tokenizer.eos_token_id
        )
        
        generated_text = self.llm_tokenizer.decode(output[0], skip_special_tokens=True)
        
        pattern = r"Fixed code:\n```python\n(.*?)```"
        match = re.search(pattern, generated_text, re.DOTALL)
        
        if match:
            fixed_code = match.group(1).strip()
            return fixed_code
        else:
            return "Error: Could not fix syntax errors in generated code."
            
    def train_intent_classifier(self, training_data):
        """Train the high-level intent classifier
        
        training_data: list of (command, intent) tuples
        """
        self.bert_model.train()
        self.intent_classifier.train()
        
        optimizer = torch.optim.Adam(list(self.bert_model.parameters()) + 
                                     list(self.intent_classifier.parameters()), 
                                     lr=3e-5)
        loss_fn = nn.CrossEntropyLoss()
        
        for command, intent in training_data:
            tokens = self.intent_tokenizer(command, padding='max_length', max_length=128, 
                                         truncation=True, return_tensors="pt").to(self.device)
            
            outputs = self.bert_model(**tokens)
            pooled_output = outputs.pooler_output
            
            intent_logits = self.intent_classifier(pooled_output)
            intent_id = self.intent_labels.index(intent)
            
            loss = loss_fn(intent_logits, torch.tensor([intent_id], device=self.device))
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
    
    def fine_tune_llm(self, code_modification_examples):
        """Fine-tune the LLM on code modification examples
        
        code_modification_examples: list of (original_code, command, modified_code) tuples
        """
        # This would be implemented with the appropriate training code for the LLM
        # Using techniques like LoRA for parameter-efficient fine-tuning
        pass
    
    def save_models(self, path_prefix):
        """Save all models"""
        torch.save(self.bert_model.state_dict(), f"{path_prefix}_bert.pt")
        torch.save(self.intent_classifier.state_dict(), f"{path_prefix}_intent.pt")
        self.llm_model.save_pretrained(f"{path_prefix}_llm")
        self.llm_tokenizer.save_pretrained(f"{path_prefix}_llm_tokenizer")
        self.intent_tokenizer.save_pretrained(f"{path_prefix}_intent_tokenizer")

# Example usage
def main():
    # Create the code assistant model
    model = CodeAssistantModel()
    
#     # Initial code example
#     initial_code = """class Animal:
#     def __init__(self):
#         pass
#     def sound(self):
#         return "generic sound"
# """
    initial_code = textwrap.dedent("""
    class Animal:
        def __init__(self):
            pass
        def sound(self):
            return "generic sound"
    """)
    
    # Example 1: Add a method
    command1 = "Add a method called eat with parameter food to Animal class"
    modified_code = model.modify_code(initial_code, command1)
    print("Modified code after adding method:")
    print(modified_code)
    
    # Example 2: Add a loop to the newly created method
    command2 = "Put a for loop inside the method eat from Animal class"
    modified_code = model.modify_code(modified_code, command2)
    print("\nModified code after adding loop:")
    print(modified_code)

if __name__ == "__main__":
    main()