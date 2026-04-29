from transpiler.python_lexer import PythonLexer
from transpiler.python_parser import PythonParser

class RangeCall:
    def __init__(self, args):
        self.func = 'range'
        self.args = args

class PythonToCTranspiler:
    def __init__(self):
        self.lexer = PythonLexer()
        self.parser = PythonParser()
        self.output_lines = []
        self.variables = {} 
        self.indent_level = 0
        self.functions = [] 
        self.current_function = None
        self.global_declarations = []

    def transpile(self, python_code):
        """Transpile Python code to C"""
        # Reset state
        self.output_lines = []
        self.variables = {}
        self.indent_level = 0
        self.functions = []
        self.current_function = None
        self.global_declarations = [] 

        tokens = self.lexer.tokenize(python_code)
        ast = self.parser.parse(tokens)
        self.visit(ast)
    
        includes = ["#include <stdio.h>"]
        if any('malloc(' in line for line in self.global_declarations):
            includes.append("#include <stdlib.h>")
        
        if any('float' in line for line in self.global_declarations):
            includes.append("#include <math.h>")
        
        c_code = '\n'.join(includes) + '\n\n'
        c_code += "int main() {\n"
        for decl in self.global_declarations:
            if 'malloc(' in decl:
                c_code += "    " + decl + "\n"
            elif '=' in decl:
                c_code += "    " + decl + "\n"
            else:
                c_code += "    " + decl + ";\n"
        
        for line in self.output_lines:
            if line.strip(): 
                c_code += "    " + line + "\n"
        
        c_code += "    return 0;\n}\n"
        
        return c_code
    
    def add_line(self, line):
        """Add a line with proper indentation for statements inside main"""
        self.output_lines.append(line)
    
    def visit(self, node):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.generic_visit)
        return method(node)
    
    def generic_visit(self, node):
        if hasattr(node, 'children'):
            for child in node.children:
                self.visit(child)
    
    def visit_ProgramNode(self, node):
        for statement in node.statements:
            self.visit(statement)
    
    def visit_AssignNode(self, node):
        var_name = node.var_name
        expr_result = self.visit(node.expression)
        
        if var_name not in self.variables:
            var_type = 'int'
            if hasattr(node.expression, 'elements'):
                elements = node.expression.elements
                if elements:
                    first_elem = elements[0]
                    if hasattr(first_elem, 'value'):
                        if isinstance(first_elem.value, int):
                            elem_type = 'int'
                            var_type = f'{elem_type}*'
                            decl = f"{var_type} {var_name} = malloc({len(elements)} * sizeof({elem_type}));"
                            self.global_declarations.append(decl)
                            self.global_declarations.append(f"int {var_name}_size = {len(elements)};")
                            for i, elem in enumerate(elements):
                                elem_val = self.visit(elem)
                                self.global_declarations.append(f"{var_name}[{i}] = {elem_val};")
                                
                        elif isinstance(first_elem.value, str):
                            elem_type = 'char*'
                            var_type = f'{elem_type}*'
                            decl = f"{var_type} {var_name} = malloc({len(elements)} * sizeof({elem_type}));"
                            self.global_declarations.append(decl)
                            self.global_declarations.append(f"int {var_name}_size = {len(elements)};")
                            for i, elem in enumerate(elements):
                                elem_val = self.visit(elem)
                                self.global_declarations.append(f'{var_name}[{i}] = "{elem_val}";')
                        else:
                            var_type = 'int*'
                            decl = f"{var_type} {var_name} = malloc({len(elements)} * sizeof(int));"
                            self.global_declarations.append(decl)
                    else:
                        var_type = 'int*'
                        decl = f"{var_type} {var_name} = malloc({len(elements)} * sizeof(int));"
                        self.global_declarations.append(decl)
                else:
                    var_type = 'int*'
                    self.global_declarations.append(f"{var_type} {var_name} = NULL;")
            
            elif hasattr(node.expression, 'items'):
                item_count = len(node.expression.items)
                self.global_declarations.append(f"// Dictionary: {var_name} with {item_count} items")
                self.global_declarations.append(f"// Requires hashmap implementation")
                self.global_declarations.append(f"void* {var_name}; // Placeholder")
                var_type = 'void*'
            
            elif hasattr(node.expression, 'value'):
                value = node.expression.value
                if isinstance(value, int):
                    var_type = 'int'
                elif isinstance(value, float):
                    var_type = 'float'
                elif isinstance(value, str):
                    var_type = 'char*'
                    expr_result = f'"{value}"'
                else:
                    var_type = 'int'
                self.global_declarations.append(f"{var_type} {var_name} = {expr_result};")
            
            elif hasattr(node.expression, 'name'):
                rhs_var = node.expression.name
                if rhs_var in self.variables:
                    var_type = self.variables[rhs_var]
                else:
                    var_type = 'int'
                self.global_declarations.append(f"{var_type} {var_name} = {expr_result};")
            
            elif hasattr(node.expression, '__class__') and node.expression.__class__.__name__ == 'IndexNode':
                obj_name = node.expression.obj.name if hasattr(node.expression.obj, 'name') else ''
                if obj_name in self.variables:
                    list_type = self.variables[obj_name]
                    if '*' in list_type:
                        var_type = list_type.replace('*', '')
                    else:
                        var_type = 'int'
                else:
                    var_type = 'int'
                self.global_declarations.append(f"{var_type} {var_name} = {expr_result};")
            
            else:
                self.global_declarations.append(f"int {var_name} = {expr_result};")
                var_type = 'int'
            
            self.variables[var_name] = var_type
        else:
            if var_name in self.variables and self.variables[var_name] == 'char*':
                self.output_lines.append(f'{var_name} = "{expr_result}";')
            else:
                self.output_lines.append(f"{var_name} = {expr_result};")
        
        return expr_result
    
    def visit_IndexAssignNode(self, node):
        array_name = node.array_name
        index = self.visit(node.index)
        value = self.visit(node.value)
        
        self.output_lines.append(f"{array_name}[{index}] = {value};")
        return value
    
    
    def visit_PrintNode(self, node):
        expr_result = self.visit(node.expression)
        if hasattr(node.expression, 'name'):
            var_name = node.expression.name
            if var_name in self.variables:
                var_type = self.variables[var_name]
                if var_type == 'char*':
                    self.add_line(f'printf("%s\\n", {var_name});')
                elif var_type == 'float':
                    self.add_line(f'printf("%f\\n", {var_name});')
                else:
                    self.add_line(f'printf("%d\\n", {var_name});')
            else:
                self.add_line(f'printf("%d\\n", {var_name});')
        
        elif hasattr(node.expression, 'value') and isinstance(node.expression.value, str):
            self.add_line(f'printf("%s\\n", "{expr_result}");')
        elif hasattr(node.expression, '__class__') and node.expression.__class__.__name__ == 'IndexNode':
            array_name = node.expression.obj.name if hasattr(node.expression.obj, 'name') else ''
            if array_name in self.variables:
                var_type = self.variables[array_name]
                if 'char' in var_type or var_type == 'char**':
                    self.add_line(f'printf("%s\\n", {expr_result});')
                else:
                    self.add_line(f'printf("%d\\n", {expr_result});')
            else:
                self.add_line(f'printf("%d\\n", {expr_result});')
        else:
            self.add_line(f'printf("%d\\n", {expr_result});')
    
    def visit_IfNode(self, node):
        condition = self.visit(node.condition)
        self.add_line(f"if ({condition}) {{")
        self.indent_level += 1
        
        for stmt in node.then_branch:
            self.visit(stmt)
        
        self.indent_level -= 1
        
        if node.else_branch:
            self.add_line("} else {")
            self.indent_level += 1
            
            for stmt in node.else_branch:
                self.visit(stmt)
            
            self.indent_level -= 1
        
        self.add_line("}")
    
    def visit_WhileNode(self, node):
        condition = self.visit(node.condition)
        self.add_line(f"while ({condition}) {{")
        self.indent_level += 1
        
        for stmt in node.body:
            self.visit(stmt)
        
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_ForNode(self, node):
        var_name = node.var_name
        iterable = self.visit(node.iterable)
        if isinstance(iterable, RangeCall):
            args = iterable.args
            if len(args) == 1:
                end = args[0]
                self.add_line(f"for (int {var_name} = 0; {var_name} < {end}; {var_name}++) {{")
            elif len(args) == 2:
                start = args[0]
                end = args[1]
                self.add_line(f"for (int {var_name} = {start}; {var_name} < {end}; {var_name}++) {{")
            elif len(args) == 3:
                start = args[0]
                end = args[1]
                step = args[2]
                self.add_line(f"for (int {var_name} = {start}; {var_name} < {end}; {var_name} += {step}) {{")
            else:
                self.add_line(f"for (int {var_name} = 0; {var_name} < 10; {var_name}++) {{")
        else:
            list_name = node.iterable.name if hasattr(node.iterable, 'name') else str(iterable)
            is_string_list = False
            if list_name in self.variables:
                var_type = self.variables[list_name]
                if var_type == 'char**' or (isinstance(var_type, str) and 'char' in var_type):
                    is_string_list = True
            if is_string_list:
                self.add_line(f"// Python for loop: for {var_name} in {list_name}")
                self.add_line(f"for (int {var_name}_idx = 0; {var_name}_idx < {list_name}_size; {var_name}_idx++) {{")
                self.add_line(f"    char* {var_name} = {list_name}[{var_name}_idx];")
                self.variables[var_name] = 'char*'
            else:
                self.add_line(f"// Python for loop: for {var_name} in {list_name}")
                self.add_line(f"for (int {var_name}_idx = 0; {var_name}_idx < {list_name}_size; {var_name}_idx++) {{")
                self.add_line(f"    int {var_name} = {list_name}[{var_name}_idx];")
                self.variables[var_name] = 'int'
        self.indent_level += 1
        for stmt in node.body:
            self.visit(stmt)
        
        self.indent_level -= 1
        self.add_line("}")
    
    def visit_IndexNode(self, node):
        obj = self.visit(node.obj)
        index = self.visit(node.index)
        return f"{obj}[{index}]"
    
    def visit_ListNode(self, node):
        elements = [self.visit(elem) for elem in node.elements]
        if not elements:
            return "NULL"

        if elements:
            return elements[0]
        return "0"
    
    def visit_DictNode(self, node):
        return "/* dictionary placeholder */"
    
    def visit_BinOpNode(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op
        if op == '==':
            op = '=='
        elif op == '!=':
            op = '!='
        elif op == 'and':
            op = '&&'
        elif op == 'or':
            op = '||'
        elif op == '>=':
            op = '>='
        elif op == '<=':
            op = '<='
        
        return f"{left} {op} {right}"
    
    def visit_NumberNode(self, node):
        return str(node.value)
    
    def visit_StringNode(self, node):
        return node.value
    
    def visit_VarNode(self, node):
        return node.name
    
    def visit_CallNode(self, node):
        args_str = ', '.join([self.visit(arg) for arg in node.args])
        
        if node.func == 'range':
            args = [self.visit(arg) for arg in node.args]
            return RangeCall(args)
        elif node.func == 'print':
            if node.args:
                first_arg = node.args[0]
                if hasattr(first_arg, 'value') and isinstance(first_arg.value, str):
                    return first_arg.value
                else:
                    arg_str = self.visit(first_arg)
                    return arg_str
            return ''
        elif node.is_standalone:
            self.add_line(f"{node.func}({args_str});")
            return f"{node.func}({args_str})"
        else:
            return f"{node.func}({args_str})"