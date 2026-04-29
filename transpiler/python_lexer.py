import re

class PythonToken:
    def __init__(self, type, value, line, col):
        self.type = type
        self.value = value
        self.line = line
        self.col = col
    
    def __repr__(self):
        return f"PythonToken({self.type}, '{self.value}', {self.line}:{self.col})"

class PythonLexer:
    """Python Lexer using Regular Expressions (Finite Automata)"""

    TOKEN_PATTERNS = [
        ('IF', r'\bif\b'),
        ('ELSE', r'\belse\b'),
        ('WHILE', r'\bwhile\b'),
        ('FOR', r'\bfor\b'),
        ('PRINT', r'\bprint\b'),
        ('IN', r'\bin\b'),
        
        # Literals
        ('NUMBER', r'\b\d+(\.\d+)?\b'),
        ('STRING', r'\"[^\"]*\"|\'[^\']*\''),
        
        ('LTE', r'<='),    
        ('GTE', r'>='),    
        ('EQ', r'=='),
        ('NEQ', r'!='),
        ('ASSIGN', r'='),
        ('PLUS', r'\+'),
        ('MINUS', r'-'),
        ('MULT', r'\*'),
        ('DIV', r'/'),
        ('MOD', r'%'),
        ('LT', r'<'),      
        ('GT', r'>'),      
    
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LBRACE', r'\{'), 
        ('RBRACE', r'\}'), 
        ('LSQUARE', r'\['),
        ('RSQUARE', r'\]'),
        ('COLON', r':'),
        ('COMMA', r','),
        
        ('IDENTIFIER', r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'),
        
        ('WHITESPACE', r'[ \t]+'),
        ('COMMENT', r'#.*'),
    ]
    
    def __init__(self):
        patterns = []
        for token_name, pattern in self.TOKEN_PATTERNS:
            patterns.append(f'(?P<{token_name}>{pattern})')
        
        self.token_regex = re.compile('|'.join(patterns))
    
    def tokenize(self, code):
        """Tokenize Python source code"""
        tokens = []
        lines = code.split('\n')
        indent_stack = [0] 
        
        for line_num, line in enumerate(lines, 1):
            indent_level = len(line) - len(line.lstrip())
            current_indent = indent_stack[-1]
            
            if indent_level > current_indent:
                tokens.append(PythonToken('INDENT', '', line_num, 1))
                indent_stack.append(indent_level)
            elif indent_level < current_indent:
                while indent_stack[-1] > indent_level:
                    tokens.append(PythonToken('DEDENT', '', line_num, 1))
                    indent_stack.pop()
        
            line = line.strip()
            if not line or line.startswith('#'):
                if line_num < len(lines):
                    tokens.append(PythonToken('NEWLINE', '\\n', line_num, 1))
                continue
            
            pos = 0
            while pos < len(line):
                match = self.token_regex.match(line, pos)
                if match:
                    token_type = match.lastgroup
                    token_value = match.group()
                    
                    # Skip whitespace and comments
                    if token_type not in ['WHITESPACE', 'COMMENT']:
                        col = pos + 1  # 1-based column
                        tokens.append(PythonToken(token_type, token_value, line_num, col))
                    
                    pos = match.end()
                else:
                    pos += 1
        
            if line_num < len(lines):
                tokens.append(PythonToken('NEWLINE', '\\n', line_num, len(line) + 1))
    
        while len(indent_stack) > 1:
            tokens.append(PythonToken('DEDENT', '', line_num, 1))
            indent_stack.pop()
    
        tokens.append(PythonToken('EOF', '', line_num, 1))    
        return tokens