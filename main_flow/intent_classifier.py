import spacy
import re
from typing import Dict, List, Any, Optional
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
import numpy as np
from datasets import Dataset

class CodeIntentClassifier:
    def __init__(self, model_name="distilbert-base-uncased"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=4)
        self.labels = ["add", "modify", "delete", "explain"]
        self.is_trained = False
        
    def prepare_dataset(self, texts: List[str], labels: List[str]) -> Dataset:
        """for converting training data to HuggingFace datasets format"""
        label_indices = [self.labels.index(label) for label in labels]
        
        dataset_dict = {
            "text": texts,
            "label": label_indices
        }
        
        return Dataset.from_dict(dataset_dict)
    
    def tokenize_function(self, examples):
        return self.tokenizer(
            examples["text"],
            padding="max_length",
            truncation = True,
            max_length = 128
        )
    
    def compute_metrics(self, eval_pred):
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=1)
        accuracy = (predictions == labels).mean()
        return {"accuracy": accuracy}
    
    def train(self, texts: List[str], labels: List[str]) -> None:
        dataset = self.prepare_dataset(texts, labels)
        tokenized_dataset = dataset.map(self.tokenize_function, batched=True)
        
        training_args = TrainingArguments(
            output_dir = "./results",
            num_train_epochs = 3,
            per_device_train_batch_size = 8,
            per_device_eval_batch_size = 8,
            warmup_steps = 100,
            weight_decay = 0.01,
            logging_dir = "./logs",
            logging_steps = 10,
            save_strategy = "no",
        )
        
        trainer = Trainer(
            model = self.model,
            args = training_args,
            train_dataset = tokenized_dataset,
            compute_metrics = self.compute_metrics
        )
        
        trainer.train()
        
        self.is_trained = True
        print("Model trained successfully")
        
    def predict(self, text: str) -> str:
        if not self.is_trained:
            return self._rule_based_intent(text)
        
        inputs = self.tokenizer (
            text,
            return_tensors = "pt",
            truncation = True,
            padding = True
        )
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
            predicted_class = torch.argmax(predictions, dim=-1).item()
        
        confidence = predictions[0][predicted_class].item()
        print(f"Intent prediction confidence: {confidence:.4f}")
        
        if confidence < 0.6:
            rule_based_intent = self._rule_based_intent(text)
            if rule_based_intent: 
                return rule_based_intent
            
        return self.labels[predicted_class]
    
    def _rule_based_intent(self, text: str) -> Optional[str]:
        """fallback rule-based intent detection"""
        intents = {
            "add": ["add", "create", "insert", "new", "implement", "develop"],
            "modify": ["change", "modify", "update", "edit", "refactor", "rename"],
            "delete": ["delete", "remove", "eliminate", "get rid of"],
            "explain": ["explain", "describe", "what", "how", "document"]
        }
        
        for intent, keywords in intents.items():
            if any(keyword in text.lower() for keyword in keywords):
                return intent
            
        return "explain"

def extract_entities_with_nlp(text: str, nlp) -> Dict[str, Any]:
    doc = nlp(text)
    
    entities = {}
    
    code_element_types = ["function", "method", "class", "variable", "parameter", "import", "module"]
    for element_type in code_element_types:
        if element_type in text.lower():
            entities["element_type"] = element_type
            break
        
    name_patterns = [
        r"(?:called|named|with name|with the name)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?",
        r"(?:add|create|implement)\s+(?:a|an|the)?\s+(?:new\s+)?(?:method|function|class|variable)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?",
        r"(?:delete|remove|eliminate)\s+(?:the\s+)?(?:method|function|class|variable)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?"
    ]
    
    for pattern in name_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            entities["name"] = match.group(1)
            break
        
    class_patterns = [
        r"(?:to|from|in)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?\s+class",
        r"class\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?",
        r"(?:the|a|an)\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+class"
    ]
    
    for pattern in class_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            entities["class_name"] = match.group(1)
            break
        
    if "rename" in text.lower():
        rename_patterns = [
            r"(?:to|as)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?",
            r"rename\s+.*?\s+to\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?"
        ]
        
        for pattern in rename_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                entities["new_name"] = match.group(1)
                break
            
    if "parameter" in text.lower() or "arg" in text.lower() or "argument" in text.lower():
        param_pattern = r"(?:parameter|arg|argument)\s+[\"']?([a-zA-Z_][a-zA-Z0-9_]*)[\"']?"
        match = re.search(param_pattern, text, re.IGNORECASE)
        if match:
            entities["parameter_name"] = match.group(1)
    return entities

def extract_intent_and_entities(text: str) -> Dict[str, Any]:
    try:
        nlp = spacy.load("en_core_web_lg")
    except OSError:
        print("Downloading SpaCy model...")
        spacy.cli.download("en_core_web_lg")
        nlp = spacy.load("en_core_web_lg")
        
    classifier = CodeIntentClassifier()
    training_texts = [
        "Add a method called eat to Animal class",
        "Create a new function to handle file uploads",
        "Implement a validation method for the input form",
        "Delete the unused function from the utils file",
        "Remove the deprecated class from the codebase",
        "Eliminate redundant validation in the process method",
        "Change the parameter name from count to total",
        "Rename the Customer class to Client",
        "Update the error handling in the payment method",
        "Explain how the authentication flow works",
        "What does this function do?",
        "Document the API endpoints for the client",
        "Can you add support for JSON in this class?",
        "I need to remove this redundant method",
        "Let's refactor this function to use async/await",
        "How does this algorithm work?",
        "Could you update the error handling here?",
        "Insert a new property for storing user preferences"
    ]
        
    training_labels = [
        "add", "add", "add",
        "delete", "delete", "delete",
        "modify", "modify", "modify",
        "explain", "explain", "explain",
        "add", "delete", "modify",
        "explain", "modify", "add"
    ]
        
    print("Training intent classifier...")
    classifier.train(training_texts, training_labels)
        
    intent = classifier.predict(text)
        
    entities = extract_entities_with_nlp(text, nlp)
        
    return {
        "intent": intent,
        "entities": entities,
        "full_text": text
    }