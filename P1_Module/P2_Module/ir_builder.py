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
                    "indent": indent
                })

            # =========================
            # FOR LOOP ✅ FIXED
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
                    "indent": indent
                })

            # =========================
            # LOOP END ✅ FIXED
            # =========================
            elif t == "LOOP_END":
                node = self.new_node("loop_end", indent=indent, line=line)

                if stack:
                    top = stack[-1]

                    if top["type"] in ["FOR", "LOOP"]:
                        top = stack.pop()

                        # create loop back edge
                        if prev_id:
                            edges.append({
                                "from": prev_id,
                                "to": top["start_id"],
                                "label": "loop_back"
                            })

            # =========================
            # END IF
            # =========================
            elif t == "END_IF":
                node = self.new_node("end_if", indent=indent, line=line)
                if stack and stack[-1]["type"] == "IF":
                    ctx = stack.pop()
                    ctx["end_if_id"] = node["id"]
                    
                    # Create edges from both true and false branch endpoints to END_IF
                    if "true_branch_end" in ctx:
                        edges.append({
                            "from": ctx["true_branch_end"],
                            "to": node["id"]
                        })
                    
                    # If ELSE exists, the last node in false branch is prev_id (before END_IF)
                    if ctx.get("has_else", False) and prev_id:
                        edges.append({
                            "from": prev_id,
                            "to": node["id"]
                        })

            # =========================
            # ADD NODE
            # =========================
            nodes.append(node)

            # =========================
            # NORMAL FLOW EDGE
            # =========================
            if prev_id and prev_node and prev_node["type"] not in ["decision", "loop_end"] and t != "ELSE":
                edges.append({
                    "from": prev_id,
                    "to": node["id"]
                })
                
            if t != "ELSE":
                for ctx in stack:
                    if ctx["type"] == "IF" and "end_if_id" in ctx:
                        edges.append({
                            "from": ctx["end_if_id"],
                            "to": node["id"]
                        })

            # =========================
            # IF / ELSE EDGES
            # =========================
            if stack:
                for ctx in stack:
                    if ctx["type"] == "IF" and t != "ELSE" and not ctx.get("has_else", False) and node["id"] != ctx["node_id"] and not ctx.get("true_target", False):
                        edges.append({
                            "from": ctx["node_id"],
                            "to": node["id"],
                            "label": "true"
                        })
                        ctx["true_target"] = True

                if t == "ELSE":
                    if stack and stack[-1]["type"] == "IF":
                        edges.append({
                            "from": stack[-1]["node_id"],
                            "to": node["id"],
                            "label": "false"
                        })

            prev_id = node["id"]
            prev_node = node

        return {
            "nodes": nodes,
            "edges": edges
        }