# Python → C Transpiler

A web-based tool that transpiles Python code to C using Theory of Computation principles (Finite Automata, Pushdown Automata, and Context-Free Grammars).

## 🌐 Live Demo

[Deployed on Render](https://py-to-c-transpiler.onrender.com)

## Overview

This project demonstrates compiler design concepts by converting Python code to executable C code. It implements the complete compilation pipeline: lexical analysis → parsing → AST generation → C code generation.

## Tech Stack

| Technology | Purpose | Why Chosen |
|------------|---------|-------------|
| **Python** | Core transpiler logic | Native language for compiler implementation |
| **Flask** | Backend web server | Lightweight, easy routing, perfect for API endpoints |
| **Flask-CORS** | Cross-origin requests | Allows frontend to communicate with backend |
| **HTML/CSS/JS** | Frontend interface | Simple, no framework overhead, works everywhere |
| **Render** | Deployment | Free tier, Python support, automatic HTTPS |

## Theory of Computation Components

The transpiler implements three core TOC concepts:

### 1. **Lexer (`lexer.py`)** - Finite Automata
- Uses Regular Expressions to tokenize Python source code
- Implements a Deterministic Finite Automaton (DFA) for pattern matching
- Converts raw code into a stream of tokens (KEYWORDS, IDENTIFIERS, OPERATORS, etc.)

### 2. **Parser (`parser.py`)** - Pushdown Automata
- Implements recursive descent parsing based on Context-Free Grammar (CFG)
- Builds an Abstract Syntax Tree (AST) from the token stream
- Uses a stack-based approach (Pushdown Automaton) to handle nested structures

### 3. **Code Generator (`python_to_c_toc.py`)** - Translation
- Visits AST nodes using the Visitor pattern
- Generates equivalent C code with proper syntax
- Manages symbol table for variable type tracking

## Working Features

### Fully Supported:
- ✅ **Variables** (int, float, string)
- ✅ **Arithmetic operations** (+, -, *, /, %)
- ✅ **Comparison operators** (<, >, <=, >=, ==, !=)
- ✅ **If-else statements** (nested)
- ✅ **While loops**
- ✅ **For loops with range()** (1, 2, and 3 arguments)
- ✅ **Integer lists** (creation, indexing, iteration)
- ✅ **String lists** (creation, indexing)
- ✅ **Print function** (integers, strings, variables)
- ✅ **Comments** (# style)

### Partially Supported:
- ⚠️ **List iteration** (works for integers, strings work with direct print)
- ⚠️ **Nested if-else** (works, but avoid string variable assignments inside)


### Known Limitations & Gotchas
1. No elif support: Use nested if-else instead.
2. String variables in if-else: Avoid assigning string variables inside conditionals.
3. String list iteration: Iterating over string lists works, but printing requires direct print
4. No function definitions
Only top-level code in main() is supported (no def statements)
5. No for i in list with string modification: Works for reading, but avoid modifying string list elements

### Local Development
Prerequisites
bash
pip install flask flask-cors

### Running the Server
bash
cd backend
python server.py
Access the Application
Open http://localhost:5000 in your browser