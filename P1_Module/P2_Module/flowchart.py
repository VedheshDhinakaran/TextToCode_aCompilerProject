from graphviz import Digraph
import os

class FlowchartGenerator:

    def generate(self, ir):
        try:
            dot = Digraph(format='png')

            nodes_list = ir["nodes"]
            edges_list = ir["edges"]
            print("===== EDGES =====")
            for e in edges_list:
                print(e)

            hidden_types = {"else", "end_if", "loop_end"}
            hidden_nodes = {n["id"] for n in nodes_list if n["type"] in hidden_types}

            # =========================
            # BUILD GRAPH
            # =========================
            adj = {}
            for edge in edges_list:
                adj.setdefault(edge["from"], []).append((edge["to"], edge.get("label", "")))

            # =========================
            # RESOLVE HIDDEN
            # =========================
            def resolve(node_id):
                visited = set()

                while node_id in hidden_nodes:
                    if node_id in visited:
                        return None
                    visited.add(node_id)

                    next_nodes = adj.get(node_id, [])
                    if not next_nodes:
                        return None

                    node_id = next_nodes[0][0]

                return node_id

            # =========================
            # CHECK IF NODE HAS OUTGOING VISIBLE EDGE
            # =========================
            def has_visible_outgoing(node_id):
                for nxt, label in adj.get(node_id, []):
                    
                    # ✅ FIX 1: loop_back is a valid outgoing edge
                    if label == "loop_back":
                        return True

                    resolved = resolve(nxt)

                    # ✅ FIX 2: normal visible edge
                    if resolved and resolved != node_id:
                        return True

                return False

            # =========================
            # FIND END NODE
            # =========================
            end_node = None
            for n in nodes_list:
                if n["type"] == "end":
                    end_node = n["id"]
                    break

            # =========================
            # DRAW NODES
            # =========================
            for node in nodes_list:
                if node["id"] in hidden_nodes:
                    continue

                node_id = str(node["id"])
                t = node["type"]

                if t == "start":
                    dot.node(node_id, "Start", shape="oval")

                elif t == "end":
                    dot.node(node_id, "End", shape="oval")

                elif t == "decision":
                    dot.node(node_id, node.get("condition", ""), shape="diamond")
                
                elif t == "loop":
                    # While loop condition should also be a diamond (decision)
                    dot.node(node_id, node.get("condition", ""), shape="diamond")

                elif t == "for":
                    var = node.get("var", "i")
                    start = node.get("start", "0")
                    end = node.get("end", "10")
                    label = f"for {var} in range({start}, {end})"
                    dot.node(node_id, label, shape="diamond")

                else:
                    label = node.get("code", "").strip()

                    if label.isdigit():
                        continue
                    if not label:
                        label = " "
                    dot.node(node_id, label, shape="box")
            
            # =========================
            # CREATE SYNTHETIC UPDATE NODES FOR FOR LOOPS (visualization only)
            # =========================
            synthetic_update_nodes = {}
            synthetic_node_counter = 10000

            for i, node in enumerate(nodes_list):
                if node["type"] == "for":
                    var = node.get("var", "i")

                    # 🔍 Check if user already updates variable inside loop
                    has_user_update = False

                    for j in range(i + 1, len(nodes_list)):
                        if nodes_list[j]["type"] == "loop_end":
                            break

                        code = nodes_list[j].get("code", "")
                        if code.startswith(f"{var} ="):
                            has_user_update = True
                            break

                    # ✅ Only add synthetic increment if no user update
                    if not has_user_update:
                        update_code = f"{var} = {var} + 1"
                        synthetic_id = synthetic_node_counter
                        synthetic_node_counter += 1

                        node_name = "upd_" + str(synthetic_id)
                        dot.node(node_name, update_code, shape="box")
                        synthetic_update_nodes[node["id"]] = node_name

            # =========================
            # FIND LOOP BODIES (nodes between loop and loop_end)
            # =========================
            loop_body_nodes = set()
            for i, node in enumerate(nodes_list):
                if node["type"] in ["loop", "for"]:
                    # Mark all nodes between loop/for and its corresponding loop_end
                    for j in range(i + 1, len(nodes_list)):
                        if nodes_list[j]["type"] == "loop_end":
                            # All nodes between i and j are in the loop body
                            for k in range(i + 1, j):
                                loop_body_nodes.add(nodes_list[k]["id"])
                            break

            # =========================
            # FIX DEAD-END NODES ONLY
            # =========================
            extra_edges = []

            for node in nodes_list:
                if node["id"] in hidden_nodes:
                    continue

                node_id = node["id"]

                # Skip decision and loop/for nodes (they handle their own branches)
                # Also skip nodes that are inside loop bodies
                if node["type"] in ["decision", "loop", "for"] or node_id in loop_body_nodes:
                    continue

                if not has_visible_outgoing(node_id):
                    if end_node and node_id != end_node:
                        extra_edges.append((node_id, end_node, ""))

            # =========================
            # DRAW EDGES with Loop Handling
            # =========================
            added = set()

            all_edges = [
                (e["from"], e["to"], e.get("label", ""))
                for e in edges_list
            ] + extra_edges

            # Track which loop nodes need false branches and true labels added
            loop_nodes_map = {}  # loop_id -> end_node_after_loop
            loop_first_body = {}  # loop_id -> first_node_in_body
            
            for i, node in enumerate(nodes_list):
                if node["type"] in ["loop", "for"]:
                    # Find the next visible node (first in loop body)
                    first_body = None
                    for j in range(i + 1, len(nodes_list)):
                        if nodes_list[j]["type"] not in ["else", "end_if", "loop_end"]:
                            first_body = nodes_list[j]["id"]
                            break
                    
                    if first_body:
                        loop_first_body[node["id"]] = first_body
                    
                    # Find the corresponding loop_end
                    for j in range(i + 1, len(nodes_list)):
                        if nodes_list[j]["type"] == "loop_end":
                            # Found loop_end, now find next visible node
                            for k in range(j + 1, len(nodes_list)):
                                if nodes_list[k]["type"] not in ["else", "end_if", "loop_end"]:
                                    loop_nodes_map[node["id"]] = nodes_list[k]["id"]
                                    break
                            if node["id"] not in loop_nodes_map and end_node:
                                loop_nodes_map[node["id"]] = end_node
                            break

            # Add true and false branches for loops
            loop_branches = {}  # (from, to) -> label for loop branches
            for loop_id in loop_nodes_map:
                # Add true branch to first body statement
                if loop_id in loop_first_body:
                    has_true = any(src == loop_id and label == "true" for src, dst, label in all_edges)
                    if not has_true:
                        first_body_id = loop_first_body[loop_id]
                        all_edges.append((loop_id, first_body_id, "true"))
                        loop_branches[(loop_id, first_body_id)] = "true"
                
                # Add false branch to next statement after loop
                next_node_id = loop_nodes_map[loop_id]
                has_false = any(src == loop_id and label == "false" for src, dst, label in all_edges)
                if not has_false:
                    all_edges.append((loop_id, next_node_id, "false"))
                    loop_branches[(loop_id, next_node_id)] = "false"

            # Filter out unlabeled edges that duplicate loop branch endpoints
            # Also filter out edges from loop body nodes to End node
            filtered_edges = []
            for src, dst, label in all_edges:
                # Skip edges from loop body nodes to End (including edges to hidden nodes that resolve to End)
                resolved_dst = resolve(dst) or dst
                if src in loop_body_nodes and resolved_dst == end_node:
                    continue
                
                # If this is an unlabeled edge and we have a labeled loop branch to the same destination from the same source, skip it
                if label == "" and (src, dst) in loop_branches:
                    continue
                filtered_edges.append((src, dst, label))
            
            all_edges = filtered_edges

            for src, dst, label in all_edges:

                actual_from = resolve(src)
                actual_to = resolve(dst)

                if not actual_from or not actual_to:
                    continue

                if actual_from == actual_to:
                    continue
                
                # For loop body nodes with loop_back: route through synthetic update node
                for_loop_id = None
                for loop_id in loop_first_body:
                    if loop_first_body[loop_id] in loop_body_nodes and src in loop_body_nodes:
                        # Check if this node is in a for loop body
                        for i, node in enumerate(nodes_list):
                            if node["id"] == loop_id and node["type"] == "for":
                                for j in range(i + 1, len(nodes_list)):
                                    if nodes_list[j]["type"] == "loop_end":
                                        # Check if src is between loop_id and loop_end
                                        for k in range(i + 1, j):
                                            if nodes_list[k]["id"] == src:
                                                for_loop_id = loop_id
                                                break
                                        break
                                break
                
                # If this is a loop_back edge from a for loop body, route through synthetic node
                if label == "loop_back" and for_loop_id and for_loop_id in synthetic_update_nodes:
                    synthetic_id = synthetic_update_nodes[for_loop_id]

                    key1 = (actual_from, synthetic_id, "")
                    if key1 not in added:
                        dot.edge(str(actual_from), synthetic_update_nodes[loop_id])
                        added.add(key1)

                    key2 = (synthetic_id, actual_to, "")
                    if key2 not in added:
                        dot.edge(str(synthetic_id), str(actual_to))
                        added.add(key2)

                    continue


                # 🔥 FIX: route loop_back through synthetic node (FOR loops only)
                if label == "loop_back":
                    routed = False

                    for loop_id, synthetic_id in synthetic_update_nodes.items():
                        for i, node in enumerate(nodes_list):
                            if node["id"] == loop_id:
                                for j in range(i + 1, len(nodes_list)):
                                    if nodes_list[j]["type"] == "loop_end":
                                        for k in range(i + 1, j):
                                            if nodes_list[k]["id"] == src:

                                                key1 = (actual_from, synthetic_id, "")
                                                if key1 not in added:
                                                    dot.edge(str(actual_from), synthetic_update_nodes[loop_id])
                                                    added.add(key1)

                                                key2 = (synthetic_id, actual_to, "")
                                                if key2 not in added:
                                                    dot.edge(str(synthetic_id), str(actual_to))
                                                    added.add(key2)

                                                routed = True
                                                break
                                        break
                                break

                    if routed:
                        continue

                    # fallback (for while loops)
                    label = ""

                # 🚫 block direct edge from loop body to loop condition (FOR loop only)
                for loop_id in synthetic_update_nodes:
                    for i, node in enumerate(nodes_list):
                        if node["id"] == loop_id:
                            for j in range(i + 1, len(nodes_list)):
                                if nodes_list[j]["type"] == "loop_end":
                                    body_ids = [nodes_list[k]["id"] for k in range(i+1, j)]

                                    if actual_from in body_ids and actual_to == loop_id:
                                        continue  # ❌ skip this edge
                            break

                # =========================
                # 🚫 FILTER WRONG EDGES (FINAL FIX)
                # =========================

                skip_edge = False

                # 🔥 1. Block direct loop-back from body → loop condition (FOR loops)
                for loop_id in synthetic_update_nodes:
                    for i, node in enumerate(nodes_list):
                        if node["id"] == loop_id:
                            for j in range(i + 1, len(nodes_list)):
                                if nodes_list[j]["type"] == "loop_end":
                                    body_ids = [nodes_list[k]["id"] for k in range(i+1, j)]

                                    if actual_from in body_ids and actual_to == loop_id:
                                        skip_edge = True
                                        break
                            break

                # 🔥 2. Block garbage nodes like "7"
                node_map = {n["id"]: n for n in nodes_list}

                if actual_from in node_map:
                    code = node_map[actual_from].get("code", "").strip()
                    if code.isdigit():
                        skip_edge = True

                if actual_to in node_map:
                    code = node_map[actual_to].get("code", "").strip()
                    if code.isdigit():
                        skip_edge = True

                # 🚫 APPLY FILTER
                if not skip_edge:
                    key = (actual_from, actual_to, label)
                    if key not in added:
                        dot.edge(str(actual_from), str(actual_to), label=label)
                        added.add(key)

            # =========================
            # CONNECT LOOP TERMINALS TO SYNTHETIC UPDATE (FIX)
            # =========================
            for loop_id, synthetic_id in synthetic_update_nodes.items():

                # find loop range
                for i, node in enumerate(nodes_list):
                    if node["id"] == loop_id:

                        for j in range(i + 1, len(nodes_list)):
                            if nodes_list[j]["type"] == "loop_end":

                                body_nodes = [nodes_list[k]["id"] for k in range(i+1, j)]

                                for b in body_nodes:
                                    # check if node has outgoing inside loop
                                    has_internal = False

                                    for e in edges_list:
                                        if e["from"] == b:
                                            target = resolve(e["to"])
                                            if target in body_nodes:
                                                has_internal = True
                                                break

                                    # 🔥 TERMINAL NODE → connect to synthetic
                                    if not has_internal:
                                        key = (b, synthetic_update_nodes[loop_id], "")
                                        if key not in added:
                                            dot.edge(str(b), str(synthetic_update_nodes[loop_id]))
                                            added.add(key)

                                break
                        break

            # =========================
            # 🔥 FORCE LOOPBACK FROM SYNTHETIC NODE
            # =========================
            for loop_id, synthetic_id in synthetic_update_nodes.items():

                # find loop condition node (the "for" node)
                loop_node = loop_id

                key = (synthetic_id, loop_node, "")
                if key not in added:
                    dot.edge(str(synthetic_id), str(loop_node))
                    added.add(key)

            # =========================
            # SAVE
            # =========================
            os.makedirs("static", exist_ok=True)
            filepath = "static/flowchart"
            dot.render(filepath, format='png', cleanup=True)

            return "/static/flowchart.png"

        except Exception as e:
            print("🔥 Flowchart Error:", e)
            return ""