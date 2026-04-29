#ir_builder.py

class IRBuilder:

    def __init__(self):
        self.node_id = 1

    def new_node(self, type_, indent=None, line=None, **kwargs):
        node = {
            "id": self.node_id,
            "type": type_,
            **kwargs
        }
        if indent is not None:
            node["indent"] = indent
        if line is not None:
            node["line"] = line
        self.node_id += 1
        return node

    def build(self, tokens):
        nodes = []
        edges = []

        prev_id = None
        prev_node = None
        stack = []
        loop_exit_marker = None  # Track where loop should exit to

        for token in tokens:
            t = token["type"]
            indent = token.get("indent", 0)
            line = token.get("line", 0)

            # =========================
            # START / END
            # =========================
            if t == "START":
                node = self.new_node("start", indent=indent, line=line)

            elif t == "END":
                node = self.new_node("end", indent=indent, line=line)

            # =========================
            # ASSIGNMENT
            # =========================
            elif t == "ASSIGN":
                var = token['data']['var']
                value = token['data']['value']

                # 🔥 FIX: skip auto increment inside FOR loop
                if stack and stack[-1]["type"] == "FOR":
                    if value.strip() == f"{var} + 1":
                        continue

                code = f"{var} = {value}"
                node = self.new_node("process", code=code, indent=indent, line=line)
            # =========================
            # OUTPUT
            # =========================
            elif t == "OUTPUT":
                code = f"print({token['data']['value']})"
                node = self.new_node("output", code=code, indent=indent, line=line)

            # =========================
            # IF
            # =========================
            elif t == "IF":
                node = self.new_node("decision", condition=token['data']['condition'], indent=indent, line=line)

                stack.append({
                    "type": "IF",
                    "node_id": node["id"],
                    "has_else": False,
                    "true_target": False,
                    "indent": indent
                })

            # =========================
            # ELSE
            # =========================
            elif t == "ELSE":
                node = self.new_node("else", indent=indent, line=line)

                if stack and stack[-1]["type"] == "IF":
                    stack[-1]["has_else"] = True
                    # Save the last node in the true branch
                    if prev_id:
                        stack[-1]["true_branch_end"] = prev_id

            # =========================
            # WHILE
            # =========================
            elif t == "WHILE":
                node = self.new_node("loop", condition=token['data']['condition'], indent=indent, line=line)

                stack.append({
                    "type": "LOOP",
                    "start_id": node["id"],
                    "indent": indent,
                    "loop_body_started": False
                })

            # =========================
            # FOR LOOP
            # =========================
            elif t == "FOR":
                node = self.new_node(
                    "for",
                    var=token["data"]["var"],
                    start=token["data"]["start"],
                    end=token["data"]["end"],
                    indent=indent,
                    line=line
                )

                stack.append({
                    "type": "FOR",
                    "start_id": node["id"],
                    "indent": indent,
                    "loop_body_started": False
                })

            # =========================
            # LOOP END - CREATE LOOP-BACK + EXIT EDGE
            # =========================
            elif t == "LOOP_END":
                node = self.new_node("loop_end", indent=indent, line=line)

                if stack:
                    top = stack[-1]

                    if top["type"] in ["FOR", "LOOP"]:
                        top = stack.pop()

                        # Create loop-back edge (last statement in loop → back to loop start)
                        if prev_id:
                            edges.append({
                                "from": prev_id,
                                "to": top["start_id"],
                                "label": "loop_back"
                            })
                        
                        # Store the loop exit marker so next statement can connect
                        loop_exit_marker = node["id"]
                        
                        # Set prev_id to loop_end so next statement connects from there
                        prev_id = node["id"]
                        
                        # CREATE FALSE EDGE: from loop condition to loop_end (for when condition is false)
                        edges.append({
                            "from": top["start_id"],
                            "to": node["id"],
                            "label": "false"
                        })

            # =========================
            # END IF - CONNECT BRANCHES TO END_IF
            # =========================
            elif t == "END_IF":
                node = self.new_node("end_if", indent=indent, line=line)
                if stack and stack[-1]["type"] == "IF":
                    ctx = stack.pop()
                    
                    # Connect true branch end to END_IF
                    if "true_branch_end" in ctx:
                        edges.append({
                            "from": ctx["true_branch_end"],
                            "to": node["id"]
                        })
                    
                    # Connect false branch end to END_IF
                    if ctx.get("has_else", False) and prev_id:
                        edges.append({
                            "from": prev_id,
                            "to": node["id"]
                        })
                    else:
                        # If NO ELSE: create false branch from decision directly to END_IF
                        edges.append({
                            "from": ctx["node_id"],
                            "to": node["id"],
                            "label": "false"
                        })

            # =========================
            # ADD NODE
            # =========================
            nodes.append(node)

            # =========================
            # CREATE EDGES BASED ON CONTEXT
            # =========================
            
            # 1. NORMAL FLOW: from previous regular node (ELSE nodes CAN have outgoing edges)
            if prev_id and prev_node and prev_node["type"] not in ["decision", "loop", "for"] and t != "ELSE" and t != "LOOP_END" and t != "END_IF":
                edges.append({
                    "from": prev_id,
                    "to": node["id"]
                })
            
            # 2. FROM WHILE/FOR LOOP: create edge to first statement in loop body
            if stack:
                for ctx in stack:
                    if ctx["type"] in ["LOOP", "FOR"] and t not in ["ELSE", "LOOP_END", "END_IF"] and not ctx.get("loop_body_started", False) and node["id"] != ctx["start_id"]:
                        edges.append({
                            "from": ctx["start_id"],
                            "to": node["id"],
                            "label": "true"
                        })
                        ctx["loop_body_started"] = True
            
            # 3. FROM IF DECISION NODE: create true branch edge to first statement in IF block
            if stack:
                for ctx in stack:
                    if ctx["type"] == "IF" and t != "ELSE" and not ctx.get("has_else", False) and node["id"] != ctx["node_id"] and not ctx.get("true_target", False):
                        edges.append({
                            "from": ctx["node_id"],
                            "to": node["id"],
                            "label": "true"
                        })
                        ctx["true_target"] = True

            # 4. ELSE BRANCH: create false edge from IF to ELSE
            if t == "ELSE":
                if stack and stack[-1]["type"] == "IF":
                    edges.append({
                        "from": stack[-1]["node_id"],
                        "to": node["id"],
                        "label": "false"
                    })

            # Update trackers
            if t != "LOOP_END":
                prev_id = node["id"]
            prev_node = node

        return {
            "nodes": nodes,
            "edges": edges
        }