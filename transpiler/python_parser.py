from transpiler.python_lexer import PythonToken

class ASTNode:
    def __init__(self):
        self.children = []
    
    def add_child(self, node):
        if node:
            self.children.append(node)

class ProgramNode(ASTNode):
    def __init__(self, statements):
        super().__init__()
        self.statements = statements
        self.children = statements
    
    def __repr__(self):
        return f"Program({len(self.statements)} statements)"

class AssignNode(ASTNode):
    def __init__(self, var_name, expression):
        super().__init__()
        self.var_name = var_name
        self.expression = expression
        self.children = [expression]
    
    def __repr__(self):
        return f"Assign({self.var_name} = {self.expression})"

class IndexAssignNode(ASTNode):
    def __init__(self, array_name, index, value):
        super().__init__()
        self.array_name = array_name 
        self.index = index 
        self.value = value 
        self.children = [index, value]
    
    def __repr__(self):
        return f"IndexAssign({self.array_name}[{self.index}] = {self.value})"

class PrintNode(ASTNode):
    def __init__(self, expression):
        super().__init__()
        self.expression = expression
        self.children = [expression]
    
    def __repr__(self):
        return f"Print({self.expression})"

class IfNode(ASTNode):
    def __init__(self, condition, then_branch, else_branch=None):
        super().__init__()
        self.condition = condition
        self.then_branch = then_branch
        self.else_branch = else_branch or []
        self.children = [condition] + then_branch + else_branch
    
    def __repr__(self):
        return f"If({self.condition})"

class WhileNode(ASTNode):
    def __init__(self, condition, body):
        super().__init__()
        self.condition = condition
        self.body = body
        self.children = [condition] + body
    
    def __repr__(self):
        return f"While({self.condition})"

class ForNode(ASTNode):
    def __init__(self, var_name, iterable, body):
        super().__init__()
        self.var_name = var_name
        self.iterable = iterable
        self.body = body
        self.children = [iterable] + body
    
    def __repr__(self):
        return f"For({self.var_name} in {self.iterable})"

class ListNode(ASTNode):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements
        self.children = elements
    
    def __repr__(self):
        return f"List({self.elements})"

class DictNode(ASTNode):
    def __init__(self, items):
        super().__init__()
        self.items = items 
        self.children = [item for pair in items for item in pair]
    
    def __repr__(self):
        return f"Dict({len(self.items)} items)"

class IndexNode(ASTNode):
    def __init__(self, obj, index):
        super().__init__()
        self.obj = obj 
        self.index = index  
        self.children = [obj, index]
    
    def __repr__(self):
        return f"Index({self.obj}[{self.index}])"

class BinOpNode(ASTNode):
    def __init__(self, left, op, right):
        super().__init__()
        self.left = left
        self.op = op
        self.right = right
        self.children = [left, right]
    
    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"

class NumberNode(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def __repr__(self):
        return f"Number({self.value})"

class StringNode(ASTNode):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def __repr__(self):
        return f"String('{self.value}')"

class VarNode(ASTNode):
    def __init__(self, name):
        super().__init__()
        self.name = name
    
    def __repr__(self):
        return f"Var({self.name})"

class CallNode(ASTNode):
    def __init__(self, func, args, is_standalone=False):
        super().__init__()
        self.func = func
        self.args = args
        self.is_standalone = is_standalone
        self.children = [func] + args
    
    def __repr__(self):
        return f"Call({self.func}, {self.args})"

class PythonParser:
    def __init__(self):
        self.tokens = []
        self.pos = 0
        self.current_token = None
    
    def parse(self, tokens):
        """Parse tokens into AST"""
        self.tokens = tokens
        self.pos = 0
        if self.tokens:
            self.current_token = self.tokens[0]
        else:
            self.current_token = PythonToken('EOF', '', 0, 0)
        
        return self.program()
    
    def program(self):
        """program : statement*"""
        statements = []
        
        while self.current_token.type != 'EOF':
            # Skip NEWLINE, INDENT, DEDENT at program level
            if self.current_token.type in ['NEWLINE', 'INDENT', 'DEDENT']:
                self.advance()
                continue
            
            stmt = self.statement()
            if stmt:
                statements.append(stmt)
        
        return ProgramNode(statements)
    
    def statement(self):
        """statement : assign_stmt | print_stmt | if_stmt | while_stmt | for_stmt | call_stmt | expr_stmt"""
        token = self.current_token
        
        if token.type == 'IDENTIFIER':
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == 'ASSIGN':
                return self.assign_stmt()
            elif (self.pos + 3 < len(self.tokens) and 
                  self.tokens[self.pos + 1].type == 'LSQUARE'):
                temp_pos = self.pos + 2
                while temp_pos < len(self.tokens) and self.tokens[temp_pos].type not in ['RSQUARE', 'EOF']:
                    temp_pos += 1
                if (temp_pos + 1 < len(self.tokens) and 
                    self.tokens[temp_pos].type == 'RSQUARE' and
                    self.tokens[temp_pos + 1].type == 'ASSIGN'):
                    return self.assign_stmt()
                else:
                    return self.expr_stmt()
            elif self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == 'LPAREN':
                return self.call_stmt()
            else:
                return self.expr_stmt()
        elif token.type == 'PRINT':
            return self.print_stmt()
        elif token.type == 'IF':
            return self.if_stmt()
        elif token.type == 'WHILE':
            return self.while_stmt()
        elif token.type == 'FOR':
            return self.for_stmt()
        elif token.type == 'NEWLINE':
            self.advance()
            return None
        else:
            return self.expr_stmt()
    
    def assign_stmt(self):
        """assign_stmt : IDENTIFIER '=' expression | IDENTIFIER '[' expression ']' '=' expression"""
        if self.current_token.type == 'IDENTIFIER':
            var_name = self.current_token.value
            if self.pos + 1 < len(self.tokens) and self.tokens[self.pos + 1].type == 'LSQUARE':
                self.consume('IDENTIFIER')
                self.consume('LSQUARE')
                index_expr = self.expression()
                self.consume('RSQUARE')
                self.consume('ASSIGN')
                value_expr = self.expression()
                if self.current_token.type == 'NEWLINE':
                    self.advance()
                
                return IndexAssignNode(var_name, index_expr, value_expr)
  
        var_name = self.current_token.value
        self.consume('IDENTIFIER')
        self.consume('ASSIGN')
        expr = self.expression()
        
        if self.current_token.type == 'NEWLINE':
            self.advance()
        
        return AssignNode(var_name, expr)
    
    def print_stmt(self):
        """print_stmt : PRINT '(' expression ')'"""
        self.consume('PRINT')
        if self.current_token.type == 'LPAREN':
            self.consume('LPAREN')
            expr = self.expression()
            self.consume('RPAREN')
        else:
            expr = self.expression()
        if self.current_token.type == 'NEWLINE':
            self.advance()
        
        return PrintNode(expr)
    
    def call_stmt(self):
        """call_stmt : IDENTIFIER '(' [args] ')'"""
        func_name = self.current_token.value
        self.consume('IDENTIFIER')
        self.consume('LPAREN')
        
        args = []
        if self.current_token.type != 'RPAREN':
            args.append(self.expression())
            while self.current_token.type == 'COMMA':
                self.consume('COMMA')
                args.append(self.expression())
        
        self.consume('RPAREN')
        if self.current_token.type == 'NEWLINE':
            self.advance()
        
        return CallNode(func_name, args, is_standalone=True)
    
    def if_stmt(self):
        """if_stmt : IF expression ':' NEWLINE INDENT statement+ DEDENT [ELSE ':' NEWLINE INDENT statement+ DEDENT]"""
        self.consume('IF')
        condition = self.expression()
        self.consume('COLON')
        
        if self.current_token.type == 'NEWLINE':
            self.consume('NEWLINE')
        if self.current_token.type == 'INDENT':
            self.consume('INDENT')
        
        then_branch = []
        while self.current_token.type not in ['DEDENT', 'ELSE', 'EOF']:
            stmt = self.statement()
            if stmt:
                then_branch.append(stmt)
        
        if self.current_token.type == 'DEDENT':
            self.consume('DEDENT')
        
        else_branch = []
        if self.current_token.type == 'ELSE':
            self.consume('ELSE')
            self.consume('COLON')
            
            if self.current_token.type == 'NEWLINE':
                self.consume('NEWLINE')
            if self.current_token.type == 'INDENT':
                self.consume('INDENT')
            
            while self.current_token.type not in ['DEDENT', 'EOF']:
                stmt = self.statement()
                if stmt:
                    else_branch.append(stmt)
            
            if self.current_token.type == 'DEDENT':
                self.consume('DEDENT')
        
        return IfNode(condition, then_branch, else_branch)
    
    def while_stmt(self):
        """while_stmt : WHILE expression ':' NEWLINE INDENT statement+ DEDENT"""
        self.consume('WHILE')
        condition = self.expression()
        self.consume('COLON')
        
        if self.current_token.type == 'NEWLINE':
            self.consume('NEWLINE')
        if self.current_token.type == 'INDENT':
            self.consume('INDENT')
        
        body = []
        while self.current_token.type not in ['DEDENT', 'EOF']:
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        
        if self.current_token.type == 'DEDENT':
            self.consume('DEDENT')
        
        return WhileNode(condition, body)
    
    def for_stmt(self):
        """for_stmt : FOR IDENTIFIER IN expression ':' NEWLINE INDENT statement+ DEDENT"""
        self.consume('FOR')
        var_name = self.current_token.value
        self.consume('IDENTIFIER')
        self.consume('IN')
        iterable = self.expression()
        self.consume('COLON')
        
        if self.current_token.type == 'NEWLINE':
            self.consume('NEWLINE')
        if self.current_token.type == 'INDENT':
            self.consume('INDENT')
        
        body = []
        while self.current_token.type not in ['DEDENT', 'EOF']:
            stmt = self.statement()
            if stmt:
                body.append(stmt)
        
        if self.current_token.type == 'DEDENT':
            self.consume('DEDENT')
        
        return ForNode(var_name, iterable, body)
    
    def expr_stmt(self):
        """expr_stmt : expression"""
        expr = self.expression()
        if self.current_token.type == 'NEWLINE':
            self.advance()
        
        return expr
    
    def expression(self):
        """expression : comparison"""
        return self.comparison()
    
    def comparison(self):
        """comparison : arith_expr (('<' | '>' | '==' | '!=' | '<=' | '>=') arith_expr)*"""
        node = self.arith_expr()
        
        while self.current_token.type in ['LT', 'GT', 'EQ', 'NEQ', 'LTE', 'GTE']:
            op = self.current_token.value
            self.advance()
            right = self.arith_expr()
            node = BinOpNode(node, op, right)
        
        return node
    
    def arith_expr(self):
        """arith_expr : term (('+' | '-') term)*"""
        node = self.term()
        
        while self.current_token.type in ['PLUS', 'MINUS']:
            op = self.current_token.value
            self.advance()
            right = self.term()
            node = BinOpNode(node, op, right)
        
        return node
    
    def term(self):
        """term : factor (('*' | '/' | '%') factor)*"""
        node = self.factor()
        
        while self.current_token.type in ['MULT', 'DIV', 'MOD']:
            op = self.current_token.value
            self.advance()
            right = self.factor()
            node = BinOpNode(node, op, right)
        
        return node
    
    def factor(self):
        """factor : NUMBER | STRING | IDENTIFIER | '(' expression ')' | '[' [expression (',' expression)*] ']' | '{' [pair (',' pair)*] '}' | IDENTIFIER '(' [expression (',' expression)*] ')' | IDENTIFIER '[' expression ']'"""
        token = self.current_token
        
        if token.type == 'NUMBER':
            self.advance()
            if '.' in token.value:
                return NumberNode(float(token.value))
            else:
                return NumberNode(int(token.value))
        
        elif token.type == 'STRING':
            self.advance()
            value = token.value[1:-1]
            return StringNode(value)
        
        elif token.type == 'IDENTIFIER':
            var_name = token.value
            self.consume('IDENTIFIER')
            
            if self.current_token.type == 'LPAREN':
                self.consume('LPAREN')
                
                args = []
                if self.current_token.type != 'RPAREN':
                    args.append(self.expression())
                    while self.current_token.type == 'COMMA':
                        self.consume('COMMA')
                        args.append(self.expression())
                
                self.consume('RPAREN')
                return CallNode(var_name, args)
            elif self.current_token.type == 'LSQUARE':
                self.consume('LSQUARE')
                index_expr = self.expression()
                self.consume('RSQUARE')
                return IndexNode(VarNode(var_name), index_expr)
            else:
                return VarNode(var_name)
        
        elif token.type == 'LPAREN':
            self.consume('LPAREN')
            node = self.expression()
            self.consume('RPAREN')
            return node
        
        elif token.type == 'LSQUARE':  
            self.consume('LSQUARE')
            elements = []
            
            if self.current_token.type != 'RSQUARE':
                elements.append(self.expression())
                while self.current_token.type == 'COMMA':
                    self.consume('COMMA')
                    elements.append(self.expression())
            
            self.consume('RSQUARE')
            return ListNode(elements)
        
        elif token.type == 'LBRACE':
            self.consume('LBRACE')
            items = []
            
            if self.current_token.type != 'RBRACE':
                # Parse key-value pair
                key = self.expression()
                self.consume('COLON')
                value = self.expression()
                items.append((key, value))
                
                while self.current_token.type == 'COMMA':
                    self.consume('COMMA')
                    key = self.expression()
                    self.consume('COLON')
                    value = self.expression()
                    items.append((key, value))
            
            self.consume('RBRACE')
            return DictNode(items)
        
        else:
            raise SyntaxError(f"Unexpected token in factor: {token}")
    
    def advance(self):
        """Move to next token"""
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = PythonToken('EOF', '', 0, 0)
    
    def consume(self, expected_type):
        """Consume token of expected type"""
        if self.current_token.type == expected_type:
            self.advance()
        else:
            raise SyntaxError(f"Expected {expected_type}, got {self.current_token.type}")