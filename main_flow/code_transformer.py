import ast
import libcst as cst
from typing import Dict, List, Any, Tuple

def parse_code(code_string: str) -> Dict[str, Any]:
    try:
        tree = ast.parse(code_string)
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        classes = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        variables = [node.id for node in ast.walk(tree) if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store)]
            
        return {
            "functions": list(set(functions)),
            "classes": list(set(classes)),
            "variables": list(set(variables)),
            "ast_tree": tree
        }
    except SyntaxError as e:
        return {"error": str(e)}
    
class AddMethodToClassTransformer(cst.CSTTransformer):
    def __init__(self, method_name: str, class_name: str):
        self.method_name = method_name
        self.class_name = class_name
        
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            for node in original_node.body.body:
                if isinstance(node, cst.FunctionDef) and node.name.value == self.method_name:
                    return updated_node
            
            new_method = cst.FunctionDef(
                name=cst.Name(self.method_name),
                params=cst.Parameters([cst.Param(cst.Name("self"))]),
                body=cst.IndentedBlock([
                    # cst.SimpleStatementLine([
                    #     cst.Expr(cst.SimpleString('"""Method documentation goes here."""'))
                    # ]),
                    cst.SimpleStatementLine([cst.Pass()])
                ]),
                decorators=[]
            )
            
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=list(updated_node.body.body) + [new_method]
                )
            )
        return updated_node

class DeleteMethodFromClassTransformer(cst.CSTTransformer):
    def __init__(self, method_name: str, class_name: str):
        self.method_name = method_name
        self.class_name = class_name
        
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            new_body = [
                node for node in updated_node.body.body
                if not (isinstance(node, cst.FunctionDef) and node.name.value == self.method_name)
            ]
            
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=new_body
                )
            )
        return updated_node
    
class ModifyMethodInClassTransformer(cst.CSTTransformer):
    def __init__(self, method_name: str, class_name: str, modification_type: str, new_content: str = None):
        self.method_name = method_name
        self.class_name = class_name
        self.modification_type = modification_type 
        self.new_content = new_content
        
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.class_name:
            new_body = []
            
            for node in updated_node.body.body:
                if isinstance(node, cst.FunctionDef) and node.name.value == self.method_name:
                    if self.modification_type == "rename" and self.new_content:
                        new_body.append(node.with_changes(
                            name=cst.Name(self.new_content)
                        ))
                    else:
                        new_body.append(node)
                else:
                    new_body.append(node)
            
            return updated_node.with_changes(
                body=updated_node.body.with_changes(
                    body=new_body
                )
            )
        return updated_node

class RenameClassTransformer(cst.CSTTransformer):
    def __init__(self, old_class_name: str, new_class_name: str):
        self.old_class_name = old_class_name
        self.new_class_name = new_class_name
    
    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        if original_node.name.value == self.old_class_name:
            return updated_node.with_changes(
                name=cst.Name(self.new_class_name)
            )
        return updated_node

class DeleteClassTransformer(cst.CSTTransformer):
    def __init__(self, class_name: str):
        self.class_name = class_name
        self.should_remove = False
    
    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        new_body = [
            node for node in updated_node.body
            if not (isinstance(node, cst.ClassDef) and node.name.value == self.class_name)
        ]
        
        return updated_node.with_changes(body=new_body)

def modify_code_with_libcst(code: str, intent: str, entities: Dict[str, Any], full_text: str) -> str:
    """Modify code based on intent and entities using LibCST"""
    try:
        module = cst.parse_module(code)
        transformer = None
        
        if intent == "add":
            element_type = entities.get("element_type")
            name = entities.get("name")
            class_name = entities.get("class_name")
            
            if element_type == "method" and name and class_name:
                transformer = AddMethodToClassTransformer(name, class_name)
        
        elif intent == "delete":
            element_type = entities.get("element_type")
            name = entities.get("name")
            class_name = entities.get("class_name")
            
            if element_type == "method" and name and class_name:
                transformer = DeleteMethodFromClassTransformer(name, class_name)
            elif element_type == "class" and name:
                transformer = DeleteClassTransformer(name)
        
        elif intent == "modify":
            element_type = entities.get("element_type")
            name = entities.get("name")
            class_name = entities.get("class_name")
            new_name = entities.get("new_name")
            
            if "rename" in full_text.lower():
                if element_type == "method" and name and class_name and new_name:
                    transformer = ModifyMethodInClassTransformer(name, class_name, "rename", new_name)
                elif element_type == "class" and name and new_name:
                    transformer = RenameClassTransformer(name, new_name)
        
        if transformer:
            modified_module = module.visit(transformer)
            return modified_module.code
        
        return code
        
    except Exception as e:
        print(f"Error in code modification: {e}")
        return code