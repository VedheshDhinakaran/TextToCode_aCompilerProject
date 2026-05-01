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
            # DO - Start of do-while block
            # =========================
            elif t == "DO":
                # Mark where DO block body will start (next statement index)
                # Don't add a marker node - just track the index
                stack.append({
                    "type": "DO",
                    "start_idx": len(nodes),  # Index where body statements will start
                    "indent": indent,
                    "loop_body_started": False
                })
                continue

            # =========================
            # WHILE - Can be regular while or do-while (if DO is on stack)
            # =========================
            elif t == "WHILE":
                condition = token['data']['condition']
                
                # Check if this is a do-while (DO on stack)
                if stack and stack[-1]["type"] == "DO":
                    # DO-WHILE: body statements are from DO marker to here
                    do_ctx = stack.pop()
                    
                    # Get first and last body statement IDs
                    first_body_stmt_id = do_ctx.get("first_statement_id")
                    last_body_stmt_id = nodes[-1]["id"] if nodes else None
                    
                    # Create condition node with body statement IDs for AST builder
                    condition_node = self.new_node("loop", condition=condition, indent=indent, line=line, 
                                                   is_do_while=True, 
                                                   do_first_stmt_id=first_body_stmt_id,
                                                   do_last_stmt_id=last_body_stmt_id)
                    
                    # Create loop_end node (hidden type to not be drawn)
                    loop_end_node = self.new_node("loop_end", indent=indent, line=line)
                    
                    # Create edges for do-while loop
                    if first_body_stmt_id is not None:
                        # Edge: last body statement → condition (check condition after body)
                        edges.append({
                            "from": last_body_stmt_id,
                            "to": condition_node["id"]
                        })
                        
                        # Edge: condition true → first body statement (loop back to body)
                        edges.append({
                            "from": condition_node["id"],
                            "to": first_body_stmt_id,
                            "label": "true"
                        })
                    
                    # Edge: condition false → loop_end (exit loop)
                    edges.append({
                        "from": condition_node["id"],
                        "to": loop_end_node["id"],
                        "label": "false"
                    })
                    
                    # Append condition and loop_end nodes
                    nodes.append(condition_node)
                    nodes.append(loop_end_node)
                    
                    # Set prev_id to loop_end so next statement connects from there
                    prev_id = loop_end_node["id"]
                    prev_node = loop_end_node
                    node = condition_node  # For continue logic
                else:
                    # REGULAR WHILE: condition check at start of loop
                    node = self.new_node("loop", condition=condition, indent=indent, line=line)
                    
                    # FIX: Connect initialization statement to while condition
                    if prev_id and prev_node:
                        edges.append({
                            "from": prev_id,
                            "to": node["id"]
                        })
                    
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
            # For DO token: don't add (marker only)
            # For WHILE with is_do_while: already added in handler
            # For all other tokens: add the node
            if t != "DO" and not (t == "WHILE" and node.get("is_do_while")):
                nodes.append(node)

            # =========================
            # CREATE EDGES BASED ON CONTEXT
            # =========================
            
            # 1. NORMAL FLOW: from previous regular node (ELSE nodes CAN have outgoing edges)
            # Exclude WHILE since it's handled separately for do-while and regular while
            if prev_id and prev_node and prev_node["type"] not in ["decision", "loop", "for"] and t not in ["ELSE", "LOOP_END", "END_IF", "DO", "WHILE"]:
                edges.append({
                    "from": prev_id,
                    "to": node["id"]
                })
            
            # 2. FROM WHILE/FOR LOOP: create edge to first statement in loop body
            if stack:
                for ctx in stack:
                    if ctx["type"] in ["LOOP", "FOR"] and t not in ["ELSE", "LOOP_END", "END_IF", "WHILE"] and not ctx.get("loop_body_started", False) and node["id"] != ctx["start_id"]:
                        edges.append({
                            "from": ctx["start_id"],
                            "to": node["id"],
                            "label": "true"
                        })
                        ctx["loop_body_started"] = True
                    
                    # Track first statement in do-while body
                    if ctx["type"] == "DO" and t not in ["ELSE", "LOOP_END", "END_IF", "WHILE"] and ctx.get("first_statement_id") is None:
                        ctx["first_statement_id"] = node["id"]
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
            # For regular WHILE: don't update (handled by loop structure)
            # For DO_WHILE: already updated in handler
            # For other tokens: update normally
            if t == "WHILE":
                # WHILE already handles prev_id in its handler for do-while
                if not (node.get("is_do_while")):
                    # Regular while: don't update prev_id
                    pass
            elif t not in ["LOOP_END", "DO"]:
                prev_id = node["id"]
            
            if t != "DO" and not (t == "WHILE" and node.get("is_do_while")):
                prev_node = node

        return {
            "nodes": nodes,
            "edges": edges
        }