import sys
import os
import json
import traceback
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from transpiler.python_to_c_toc import PythonToCTranspiler

app = Flask(__name__, static_folder='../website')
CORS(app)

@app.route('/')
def serve_index():
    return send_from_directory('../website', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('../website', filename)

def format_tokens_for_display(tokens):
    formatted = []
    for token in tokens:
        token_type = getattr(token, 'type', 'UNKNOWN')
        token_value = getattr(token, 'value', '')
        line = getattr(token, 'line', 1)
        col = getattr(token, 'col', 1)
        formatted.append(f"{token_type}('{token_value}') @ {line}:{col}")
    
    return formatted

def format_ast_for_display(ast):
    if not ast:
        return "No AST generated"
    
    def format_node(node, indent=0):
        indent_str = "  " * indent
        node_type = type(node).__name__
        result = f"{indent_str}{node_type}"
        if hasattr(node, 'var_name'):
            result += f" ({node.var_name})"
        elif hasattr(node, 'name'):
            result += f" ({node.name})"
        elif hasattr(node, 'value'):
            if isinstance(node.value, str):
                result += f" ('{node.value}')"
            else:
                result += f" ({node.value})"
        elif hasattr(node, 'op'):
            result += f" ({node.op})"
        elif hasattr(node, 'func'):
            result += f" ({node.func})"
        elif hasattr(node, 'array_name'):
            result += f" ({node.array_name})"
        
        result += "\n"

        if hasattr(node, 'children'):
            for child in node.children:
                if child:
                    result += format_node(child, indent + 1)
        elif hasattr(node, 'statements'):
            for stmt in node.statements:
                if stmt:
                    result += format_node(stmt, indent + 1)
        elif hasattr(node, 'expression'):
            result += format_node(node.expression, indent + 1)
        elif hasattr(node, 'condition'):
            result += indent_str + "  Condition:\n"
            result += format_node(node.condition, indent + 2)
            if hasattr(node, 'then_branch'):
                result += indent_str + "  Then:\n"
                for stmt in node.then_branch:
                    if stmt:
                        result += format_node(stmt, indent + 2)
            if hasattr(node, 'else_branch'):
                result += indent_str + "  Else:\n"
                for stmt in node.else_branch:
                    if stmt:
                        result += format_node(stmt, indent + 2)
        elif hasattr(node, 'body'):
            result += indent_str + "  Body:\n"
            for stmt in node.body:
                if stmt:
                    result += format_node(stmt, indent + 2)
        elif hasattr(node, 'elements'):
            result += indent_str + "  Elements:\n"
            for elem in node.elements:
                if elem:
                    result += format_node(elem, indent + 2)
        elif hasattr(node, 'items'):
            result += indent_str + "  Items:\n"
            for key, value in node.items:
                result += indent_str + "    Key:\n"
                result += format_node(key, indent + 3)
                result += indent_str + "    Value:\n"
                result += format_node(value, indent + 3)
        elif hasattr(node, 'args'):
            result += indent_str + "  Args:\n"
            for arg in node.args:
                if arg:
                    result += format_node(arg, indent + 2)
        elif hasattr(node, 'left') and hasattr(node, 'right'):
            result += indent_str + "  Left:\n"
            result += format_node(node.left, indent + 2)
            result += indent_str + "  Right:\n"
            result += format_node(node.right, indent + 2)
        
        return result
    
    return format_node(ast)


@app.route('/api/transpile', methods=['POST'])
def transpile_to_c():
    try:
        data = request.json
        code = data.get('code', '')
        print(f"🔄 Transpiling Python to C ({len(code)} chars)")
        transpiler = PythonToCTranspiler()
        c_code = transpiler.transpile(code)
        tokens = []
        if hasattr(transpiler, 'lexer'):
            tokens_obj = transpiler.lexer.tokenize(code)
            tokens = format_tokens_for_display(tokens_obj)
        
        ast_str = ""
        ast = None
        if hasattr(transpiler, 'parser'):
            tokens_for_ast = transpiler.lexer.tokenize(code)
            ast = transpiler.parser.parse(tokens_for_ast)
            ast_str = format_ast_for_display(ast)
        
        #Getting variables
        variables = []
        if hasattr(transpiler, 'variables'):
            for var_name, var_type in transpiler.variables.items():
                if isinstance(var_type, str):
                    variables.append(f"{var_name}: {var_type}")
        
        response = {
            'success': True,
            'output': c_code,
            'tokens': tokens,
            'ast': ast_str,
            'variables': variables,
            'mode': 'c'
        }
        
        return jsonify(response)
        
    except Exception as e:
        error_msg = f"Transpilation Error: {str(e)}"
        print(f"Error: {error_msg}")
        traceback.print_exc()
        
        return jsonify({
            'success': False,
            'error': error_msg,
            'traceback': traceback.format_exc(),
            'mode': 'error'
        })

@app.route('/api/examples/<name>')
def get_example(name):
    examples = {
        'simple': {
            'code': 'x = 5\ny = x + 10\nprint(y)',
            'type': 'python'
        },
        'conditional': {
            'code': 'score = 85\nif score >= 90:\n    print("A")\nelse:\n    if score >= 80:\n        print("B")\n    else:\n        print("C")',
            'type': 'python'
        },
        'loop': {
            'code': 'i = 0\nwhile i < 5:\n    print(i)\n    i = i + 1',
            'type': 'python'
        },
        'demo': {
            'code': 'x = 10\ny = x * 2 + 5\n\nif y > 20:\n    print("Large number: ")\n    print(y)\nelse:\n    print("Small number")\n\ncounter = 0\nwhile counter < 3:\n    print(counter)\n    counter = counter + 1',
            'type': 'python'
        },
        'python_list': {
            'code': '# Python list example\nnumbers = [1, 2, 3, 4, 5]\ntotal = 0\nfor num in numbers:\n    total = total + num\nprint(total)',
            'type': 'python'
        },
        'python_range': {
            'code': '# Python range() example\nfor i in range(5):\n    print(f"Number: {i}")\n\nfor j in range(2, 10, 2):\n    print(f"Even: {j}")',
            'type': 'python'
        },
    }
    return jsonify(examples.get(name, examples['demo']))

if __name__ == '__main__':
    print("Starting PyToC Transpiler Server...")    
    print("Website: http://localhost:5000")
    print("API: http://localhost:5000/api/transpile")

    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)