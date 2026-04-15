import re

class NLPProcessor:

    def __init__(self):
        self.synonyms = {
            # Output/print synonyms
            "display": "print",
            "show": "print",
            "output": "print",
            "write": "print",
            "put": "print",
            "say": "print",
            "tell": "print",
            "echo": "print",
            
            # Assignment/set synonyms
            "initialize": "set",
            "assign": "set",
            "let": "set",
            "make": "set",
            "create": "set",
            "define": "set",
            "declare": "set",
            "put": "set",
            "store": "set",
            
            # Start/begin synonyms
            "begin": "start",
            "commence": "start",
            "initiate": "start",
            "launch": "start",
            
            # End/finish synonyms
            "finish": "end",
            "terminate": "end",
            "stop": "end",
            "complete": "end",
            "conclude": "end",
            "halt": "end",
            
            # Else synonyms
            "otherwise": "else",
            "or": "else",
            "or else": "else",
            "in other cases": "else",
            "alternative": "else",
            "alternatively": "else",
            
            # While/repeat synonyms
            "repeat": "while",
            "loop": "while",
            "as long as": "while",
            "until": "while",
            "whilst": "while",
            
            # For/iterate synonyms
            "iterate": "for",
            "for each": "for",
            "repeat for": "for",
            
            # If/conditional synonyms
            "when": "if",
            "in case": "if",
            "provided that": "if",
            "assuming": "if",
            "suppose": "if"
        }

        self.condition_map = {
            "is greater than or equal to": ">=",
            "is less than or equal to": "<=",
            "is greater than": ">",
            "is less than": "<",
            "is equal to": "==",
            "is not equal to": "!=",
            "greater than or equal to": ">=",
            "less than or equal to": "<=",
            "greater than": ">",
            "less than": "<",
            "equal to": "==",
            "not equal to": "!=",
            "equals": "==",
            "is": "==",
            "is not": "!=",
            "more than": ">",
            "bigger than": ">",
            "smaller than": "<",
            "lesser than": "<"
        }

    # -------------------------
    # MAIN PIPELINE
    # -------------------------
    def process(self, text):
        sentences = self.preprocess(text)

        tokens = []
        errors = []
        suggestions = []

        for sentence in sentences:
            text = sentence["text"]
            indent = sentence["indent"]
            line = sentence["line"]

            while text.strip():
                intent, confidence, data, remaining = self.classify(text)

                if confidence < 0.7:
                    suggestions.append({
                        "sentence": text,
                        "suggested_intent": intent,
                        "confidence": confidence
                    })

                if intent == "UNKNOWN":
                    errors.append(f"Could not understand: '{text}'")
                    break

                matched_part = text[:len(text) - len(remaining)]
                tokens.append({
                    "type": intent,
                    "data": data,
                    "raw": matched_part.strip(),
                    "indent": indent,
                    "line": line
                })

                text = remaining

        return {
            "tokens": tokens,
            "errors": errors,
            "suggestions": suggestions
        }

    # -------------------------
    # PREPROCESSOR
    # -------------------------
    def preprocess(self, text):
        text = text.replace('\r\n', '\n').replace('\r', '\n')

        sentences = []
        for line_no, raw_line in enumerate(text.split('\n')):
            indent = len(raw_line) - len(raw_line.lstrip(' '))
            line = raw_line.strip().lower()

            if not line:
                continue

            for k, v in self.synonyms.items():
                line = re.sub(r'\b' + re.escape(k) + r'\b', v, line)

            # allow inline `then`, comma-separated bodies, and inline else clauses
            line = re.sub(r'\bthen\b', ' ', line)
            line = re.sub(r',\s*', ' ', line)
            line = re.sub(r'\belse\b', ' else ', line)
            line = re.sub(r'\b(set|assign|let|make) (\w+) as\b', r'\1 \2 to', line)  # "set x as 5" -> "set x to 5"
            line = re.sub(r'\b(set|assign|let|make) (\w+) equal to\b', r'\1 \2 to', line)  # "set x equal to 5" -> "set x to 5"
            line = re.sub(r'\b(set|assign|let|make) (\w+) be\b', r'\1 \2 to', line)  # "let x be 5" -> "let x to 5"
            line = re.sub(r'\s+', ' ', line)

            sentences.append({
                "text": line,
                "indent": indent,
                "line": line_no
            })

        return sentences

    # -------------------------
    # INTENT CLASSIFIER
    # -------------------------
    def classify(self, sentence):
        sentence = sentence.strip()
        sentence = re.sub(r'^[\.\s]+', '', sentence)

        # START
        match = re.match(r'(?:begin|start|commence)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "START", 1.0, {}, remaining

        # END IF
        match = re.match(r'end (?:if|condition)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "END_IF", 0.9, {}, remaining

        # LOOP END
        match = re.match(r'(?:end (?:while|loop|for)|stop)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "LOOP_END", 0.9, {}, remaining

        # END
        match = re.match(r'(?:end|finish|terminate)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "END", 1.0, {}, remaining

        # FOR LOOP
        match = re.match(r"(?:for|iterate) (\w+) (?:from|starting from|starting at) (\d+) (?:to|up to|until) (\d+)", sentence)
        if match:
            var, start, end = match.groups()
            remaining = sentence[match.end():].strip()
            return "FOR", 0.95, {
                "var": var,
                "start": start,
                "end": end
            }, remaining

        # ASSIGN
        match = re.match(r'(?:set|assign|let|make) (\w+) to (.+?)(?=\b(?:if|else|for|while|print|set|assign|let|make|end)\b|$)', sentence)
        if match:
            var, value = match.groups()
            remaining = sentence[match.end():].strip()
            return "ASSIGN", 0.95, {
                "var": var,
                "value": value.strip()
            }, remaining

        # INPUT
        match = re.match(r'(?:input|get) (\w+)', sentence)
        if match:
            var = match.group(1)
            remaining = sentence[match.end():].strip()
            return "ASSIGN", 0.95, {
                "var": var,
                "value": "input()"
            }, remaining

        # IF
        match = re.match(r'if (.+?)(?=\b(?:print|set|if|else|for|while|end)\b|$)', sentence)
        if match:
            condition = self.translate_condition(match.group(1).strip())
            remaining = sentence[match.end():].strip()
            return "IF", 0.9, {"condition": condition}, remaining

        # ELSE
        match = re.match(r'(?:otherwise|else)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "ELSE", 0.9, {}, remaining

        # WHILE
        match = re.match(r'(?:while|repeat|loop) (.+?)(?=\b(?:print|set|if|else|for|end)\b|$)', sentence)
        if match:
            condition = self.translate_condition(match.group(1).strip())
            remaining = sentence[match.end():].strip()
            return "WHILE", 0.9, {"condition": condition}, remaining

        # OUTPUT
        match = re.match(r'(?:print|display|show|output) (.+?)(?=\b(?:if|else|for|while|set|assign|let|make|print|display|show|output|end)\b|$)', sentence)
        if match:
            remaining = sentence[match.end():].strip()
            return "OUTPUT", 0.95, {"value": match.group(1).strip()}, remaining

        return "UNKNOWN", 0.0, {}, ""

    # -------------------------
    # CONDITION TRANSLATOR
    # -------------------------
    def translate_condition(self, text):
        text = text.replace(" mod ", " % ")

        # replace longer phrases first
        for phrase, symbol in sorted(self.condition_map.items(), key=lambda kv: len(kv[0]), reverse=True):
            text = text.replace(phrase, symbol)

        text = text.replace(" and ", " && ")
        text = text.replace(" or ", " || ")
        return text.strip()