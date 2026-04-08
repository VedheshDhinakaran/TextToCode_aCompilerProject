# TextToCode_aCompilerProject
This project converts natural language into executable code by interpreting intent from unstructured English. The system maps text to a JSON flowchart, builds a Control Flow Graph (CFG), and transforms it into an Abstract Syntax Tree (AST) to generate source code. This architecture merges compiler design with automated program synthesis.

Here is your **final updated README content** with all corrections:

* ✅ `app.py` inside **P1_Module**
* ✅ `flowchart.py` inside **P2_Module**
* ✅ `optimizer.py` inside **P3_Module**
* ✅ Fully explained and structured

You can **directly copy-paste this into your README.md** 👇

---

# 🚀 Natural Language to Code Compiler

## 📌 Overview

This project implements a **modular compiler pipeline** that converts **natural language instructions into executable code** (Python and Java). It follows core principles of compiler design, including **lexical processing, intermediate representation (IR), control flow graph (CFG), abstract syntax tree (AST), optimization, and multi-target code generation**.

The system allows users to input simple English-like instructions and generates structured, syntactically correct code while also providing intermediate debugging outputs.

---

## 🧠 Pipeline Architecture

```plaintext
Natural Language Input
        ↓
P1: NLP Processing
        ↓
P2: IR + CFG Construction
        ↓
P3: AST Generation + Optimization
        ↓
P4: Code Generation (Python / Java)
        ↓
Final Output
```

---

## 📁 Project Structure

```plaintext
CompilerProject/
│
├── requirements.txt
│
├── templates/
│   └── index.html
│
├── static/
│   ├── style.css
│   └── flowchart.png
│
├── P1_Module/
│   ├── __init__.py
│   ├── app.py
│   ├── nlp_pipeline.py
│
│   ├── P2_Module/
│   │   ├── __init__.py
│   │   ├── ir_builder.py
│   │   ├── cfg_builder.py
│   │   ├── analyzer.py
│   │   ├── visualizer.py
│   │   └── flowchart.py
│
│   ├── P3_Module/
│   │   ├── __init__.py
│   │   ├── ast_nodes.py
│   │   ├── ast_builder.py
│   │   └── optimizer.py
│
│   ├── P4_Module/
│       ├── __init__.py
│       ├── python_generator.py
│       └── java_generator.py
```

---

## 🔍 Module-wise Explanation

---

## 🔷 P1: NLP Frontend + Application Controller

*(Located inside P1_Module)*

---

### 📄 `app.py` (Main Backend Controller)

* Acts as the **central controller of the application**.
* Runs the Flask server.
* Connects all modules (P1 → P4).
* Handles API endpoints:

  * `/` → Loads UI
  * `/compile` → Processes input and returns results

#### Responsibilities:

* Accepts natural language input from UI
* Passes it through:

  * NLP processing (P1)
  * IR & CFG (P2)
  * AST & Optimization (P3)
  * Code generation (P4)
* Returns:

  * Tokens
  * IR
  * CFG
  * AST
  * Optimized AST
  * Generated code
  * Flowchart

---

### 📄 `nlp_pipeline.py`

Converts natural language into structured tokens.

#### Features:

* **Preprocessing**

  * Lowercasing
  * Sentence splitting
  * Synonym normalization
    (e.g., "display" → "print", "initialize" → "set")

* **Intent Classification**
  Recognizes:

  ```
  START, END, ASSIGN, IF, ELSE, WHILE, FOR, OUTPUT, LOOP_END
  ```

* **Condition Translation**

  ```
  "greater than" → >
  "equal to" → ==
  ```

#### Output:

```json
[
  {"type": "ASSIGN", "data": {"var": "x", "value": "5"}},
  {"type": "IF", "data": {"condition": "x > 5"}}
]
```

---

## 🔶 P2: Intermediate Representation & CFG

*(Located inside P1_Module/P2_Module)*

---

### 📄 `ir_builder.py`

* Converts tokens into a structured **Intermediate Representation (IR)**.
* Uses a **stack-based approach** for nested constructs.
* Generates nodes and edges representing execution flow.

---

### 📄 `cfg_builder.py`

* Builds a **Control Flow Graph (CFG)** using graph structures.
* Represents execution paths:

  * Sequential execution
  * Conditional branching
  * Looping

---

### 📄 `analyzer.py`

Performs static analysis on CFG:

* **Dead Code Detection**
* **Cycle Detection (loop validation)**
* **Branch Validation**

  * Ensures IF statements have both true and false paths

---

### 📄 `visualizer.py`

* Converts CFG into a visual graph using Graphviz.

---

### 📄 `flowchart.py` ⭐ (NEW)

* Generates a **flowchart representation of the program** from IR/CFG.
* Uses Graphviz to create structured diagrams.

#### Features:

* Visual representation of program logic
* Node color coding:

  * 🟢 Start
  * 🔵 Process
  * 🟡 Decision
  * 🔴 End
* Saves output as `flowchart.png` in the static folder

#### Importance:

Provides a **visual debugging tool**, making the compiler easier to understand and demonstrate.

---

## 🔶 P3: AST Construction & Optimization

*(Located inside P1_Module/P3_Module)*

---

### 📄 `ast_nodes.py`

Defines the structure of Abstract Syntax Tree.

#### Node Types:

* Program
* Block
* Assignment
* IfElse
* WhileLoop
* ForLoop
* Print

---

### 📄 `ast_builder.py`

* Converts IR into a hierarchical AST.
* Detects patterns:

  * Decision → IfElse
  * Loop → WhileLoop
  * For → ForLoop

#### Role:

Transforms flat IR into structured program logic.

---

### 📄 `optimizer.py` ⭐ (NEW)

Applies optimization techniques on AST.

#### Optimizations:

* **Constant Folding**

  ```
  x = 5
  y = 3
  z = x + y → z = 8
  ```

* **Dead Code Elimination**

  * Removes unreachable code branches

#### Importance:

* Improves performance
* Mimics real compiler optimization stages
* Elevates project from basic to advanced level

---

## 🔶 P4: Code Generation

*(Located inside P1_Module/P4_Module)*

---

### 📄 `python_generator.py`

* Generates Python code from AST.
* Maintains indentation and syntax correctness.

#### Supports:

* If-Else
* While loops
* For loops
* Assignments

---

### 📄 `java_generator.py`

* Generates equivalent Java code from AST.

#### Features:

* Class structure
* `main` method
* Type declarations
* Curly braces formatting

---

## 🌐 Frontend

### 📄 `templates/index.html`

* Provides a modern split-screen UI:

  * Left: Input + Debug panels
  * Right: Generated code

#### Features:

* Language selection
* Toggle-based debug outputs
* Interactive UI design

---

## 📦 Static Files

### 📁 `static/`

* `flowchart.png` → Generated visualization
* `style.css` → UI styling (optional)

---

## ⚙️ Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

---

## ▶️ How to Run

```bash
python P1_Module/app.py
```

Then open:

```
http://127.0.0.1:5000
```

---

## ✨ Features

* Natural language → executable code
* Multi-language support (Python & Java)
* Supports:

  * If-Else
  * While loops
  * For loops
* CFG visualization
* Flowchart generation
* AST optimization
* Static code analysis
* Modular compiler architecture
* Interactive UI

---

## 🧠 Key Concept

> This project demonstrates a modular compiler architecture where a single intermediate representation enables optimization and multi-target code generation, similar to real-world compilers like LLVM.

---

## 🚀 Future Improvements

* Add more programming languages
* Integrate ML-based NLP
* Syntax highlighting editor
* Real-time compilation
* Advanced optimizations

---

## 👨‍💻 Authors

* Vedhesh
* Lakshmipriya
* Keerthi
* Janhavi

---

## 🏁 Conclusion

This project demonstrates how **natural language can be transformed into structured programming logic** using compiler design principles, making it both educational and practically valuable.

---
