from flask import Flask, render_template, request, jsonify
from nlp_pipeline import NLPProcessor

# 🔥 Import P2 pipeline
from P2_Module.main import run_pipeline
# 🔥 Import P3 pipeline
from P3_Module.main import run_ast_pipeline, ast_to_dict
# 🔥 Import P4 pipeline
from P4_Module.main import generate_code

app = Flask(__name__)

nlp = NLPProcessor()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/compile', methods=['POST'])
def compile_code():
    try:
        data = request.json

        text = data.get("text", "")
        language = data.get("language", "python")

        # P1
        p1_result = nlp.process(text)
        tokens = p1_result.get("tokens", [])

        # P2
        from P2_Module.main import run_pipeline
        p2_result = run_pipeline(tokens)

        # P3
        from P3_Module.main import run_ast_pipeline, ast_to_dict
        p3_result = run_ast_pipeline(p2_result.get("ir", {}))
        ast_json = ast_to_dict(p3_result)

        # P4
        from P4_Module.main import generate_code
        code = generate_code(p3_result, language)

        return jsonify({
            "tokens": tokens,
            "ir": p2_result.get("ir", {}),
            "cfg": p2_result.get("cfg_edges", []),
            "dead_code": p2_result.get("dead_code", []),
            "cycles": p2_result.get("cycles", []),
            "branch_errors": p2_result.get("branch_errors", []),
            "flowchart": p2_result.get("flowchart", ""),
            "ast": ast_json,
            "code": code,
            "errors": p1_result.get("errors", []),
            "suggestions": p1_result.get("suggestions", [])
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)})
    
if __name__ == '__main__':
    app.run(debug=True)