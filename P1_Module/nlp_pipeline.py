import re

class NLPProcessor:

    def __init__(self):
        self.synonyms = {
            "display": "print",
            "show": "print",
            "initialize": "set",
            "assign": "set"
        }

        self.condition_map = {
            "greater than": ">",
            "less than": "<",
            "equal to": "==",
            "not equal to": "!=",
            "greater than or equal to": ">=",
            "less than or equal to": "<="
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
            intent, confidence, data = self.classify(sentence)

            if confidence < 0.7:
                suggestions.append({
                    "sentence": sentence,
                    "suggested_intent": intent,
                    "confidence": confidence
                })

            if intent == "UNKNOWN":
                errors.append(f"Could not understand: '{sentence}'")
                continue

            tokens.append({
                "type": intent,
                "data": data,
                "raw": sentence
            })

        return {
            "tokens": tokens,
            "errors": errors,
            "suggestions": suggestions
        }

    # -------------------------
    # PREPROCESSOR
    # -------------------------
    def preprocess(self, text):
        text = text.lower()

        for k, v in self.synonyms.items():
            text = text.replace(k, v)

        sentences = re.split(r'[.?!]\s*', text)
        return [s.strip() for s in sentences if s.strip()]

    # -------------------------
    # INTENT CLASSIFIER
    # -------------------------
    def classify(self, sentence):

        # START
        if re.match(r'^start$', sentence):
            return "START", 1.0, {}

        # END
        if re.match(r'^end$', sentence):
            return "END", 1.0, {}

        # FOR LOOP (FIXED POSITION ✅)
        match = re.match(r"for (\w+) from (\d+) to (\d+)", sentence)
        if match:
            var, start, end = match.groups()
            return "FOR", 0.95, {
                "var": var,
                "start": start,
                "end": end
            }

        # ASSIGN
        match = re.match(r'set (\w+) to (.+)', sentence)
        if match:
            var, value = match.groups()
            return "ASSIGN", 0.95, {
                "var": var,
                "value": value
            }

        # IF
        match = re.match(r'if (.+)', sentence)
        if match:
            condition = self.translate_condition(match.group(1))
            return "IF", 0.9, {"condition": condition}

        # ELSE
        if "otherwise" in sentence or "else" in sentence:
            return "ELSE", 0.9, {}

        # WHILE
        match = re.match(r'while (.+)', sentence)
        if match:
            condition = self.translate_condition(match.group(1))
            return "WHILE", 0.9, {"condition": condition}

        # LOOP END
        if "end while" in sentence or "end loop" in sentence:
            return "LOOP_END", 0.9, {}

        # OUTPUT
        match = re.match(r'print (.+)', sentence)
        if match:
            return "OUTPUT", 0.95, {"value": match.group(1)}

        return "UNKNOWN", 0.0, {}

    # -------------------------
    # CONDITION TRANSLATOR
    # -------------------------
    def translate_condition(self, text):
        for phrase, symbol in self.condition_map.items():
            text = text.replace(phrase, symbol)

        text = text.replace(" is ", " ")
        return text.strip()