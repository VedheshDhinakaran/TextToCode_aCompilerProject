class IRBuilder:

    def __init__(self):
        self.node_id = 1

    def new_node(self, type_, **kwargs):
        node = {
            "id": self.node_id,
            "type": type_,
            **kwargs
        }
        self.node_id += 1
        return node

    def build(self, tokens):
        nodes = []
        edges = []

        prev_id = None
        stack = []

        for token in tokens:
            t = token["type"]

            # =========================
            # START / END
            # =========================
            if t == "START":
                node = self.new_node("start")

            elif t == "END":
                node = self.new_node("end")

            # =========================
            # ASSIGNMENT
            # =========================
            elif t == "ASSIGN":
                code = f"{token['data']['var']} = {token['data']['value']}"
                node = self.new_node("process", code=code)

            # =========================
            # OUTPUT
            # =========================
            elif t == "OUTPUT":
                code = f"print({token['data']['value']})"
                node = self.new_node("output", code=code)

            # =========================
            # IF
            # =========================
            elif t == "IF":
                node = self.new_node("decision", condition=token['data']['condition'])

                stack.append({
                    "type": "IF",
                    "node_id": node["id"]
                })

            # =========================
            # ELSE
            # =========================
            elif t == "ELSE":
                node = self.new_node("else")

            # =========================
            # WHILE
            # =========================
            elif t == "WHILE":
                node = self.new_node("loop", condition=token['data']['condition'])

                stack.append({
                    "type": "LOOP",
                    "start_id": node["id"]
                })

            # =========================
            # FOR LOOP ✅ FIXED
            # =========================
            elif t == "FOR":
                node = self.new_node(
                    "for",
                    var=token["data"]["var"],
                    start=token["data"]["start"],
                    end=token["data"]["end"]
                )

                stack.append({
                    "type": "FOR",
                    "start_id": node["id"]
                })

            # =========================
            # LOOP END ✅ FIXED
            # =========================
            elif t == "LOOP_END":
                node = self.new_node("loop_end")

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

            else:
                continue

            # =========================
            # ADD NODE
            # =========================
            nodes.append(node)

            # =========================
            # NORMAL FLOW EDGE
            # =========================
            if prev_id:
                edges.append({
                    "from": prev_id,
                    "to": node["id"]
                })

            # =========================
            # IF / ELSE EDGES
            # =========================
            if stack:
                top = stack[-1]

                if top["type"] == "IF":
                    if t != "ELSE":
                        edges.append({
                            "from": top["node_id"],
                            "to": node["id"],
                            "label": "true"
                        })

                if t == "ELSE":
                    if stack and stack[-1]["type"] == "IF":
                        edges.append({
                            "from": stack[-1]["node_id"],
                            "to": node["id"],
                            "label": "false"
                        })

            prev_id = node["id"]

        return {
            "nodes": nodes,
            "edges": edges
        }