from jsonschema import Draft202012Validator

TEXT = {"type": "string", "minLength": 1, "pattern": r"\S"}
COLUMN = {"type": "object", "required": ["heading", "items"], "additionalProperties": False,
          "properties": {"heading": TEXT, "items": {"type": "array", "minItems": 1, "items": TEXT}}}
BASE = {"slide_number": {"type": "integer", "minimum": 1}, "title": TEXT, "lead": TEXT,
        "show_footer": {"type": "boolean"}}

def variant(layout, fields, required):
    return {"type": "object", "additionalProperties": False,
            "required": ["slide_number", "layout", "title"] + required,
            "properties": {**BASE, "layout": {"const": layout}, **fields}}

SLIDE_SCHEMA = {"oneOf": [
    variant("title", {"subtitle": TEXT}, []),
    variant("comparison_2col", {"left": COLUMN, "right": COLUMN}, ["left", "right"]),
    variant("cards_3col", {"cards": {"type": "array", "minItems": 3, "maxItems": 3, "items": COLUMN}}, ["cards"]),
    variant("role_split", {
        "sections": {"type": "array", "minItems": 5, "maxItems": 5, "items": {
            "type": "object", "additionalProperties": False, "required": ["name", "rows"],
            "properties": {"name": TEXT, "rows": {"type": "array", "minItems": 1, "items": {
                "type": "object", "additionalProperties": False,
                "required": ["process", "ai", "rule", "human", "rationale"],
                "properties": {"process": TEXT, "ai": {"enum": ["●", "○", "－"]},
                    "rule": {"enum": ["●", "○", "－"]}, "human": {"enum": ["●", "○", "－"]},
                    "rationale": TEXT}
            }}}
        }},
        "key_message": TEXT, "key_note": TEXT
    }, ["sections", "key_message", "key_note"]),
]}
PRESENTATION_SCHEMA = {"$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object", "additionalProperties": False, "required": ["presentation", "slides"],
    "properties": {"presentation": {"type": "object", "additionalProperties": False,
        "required": ["title"], "properties": {"title": TEXT, "audience": TEXT, "purpose": TEXT}},
        "slides": {"type": "array", "minItems": 1, "items": SLIDE_SCHEMA}}}

def validate(data):
    Draft202012Validator(PRESENTATION_SCHEMA).validate(data)
    if [s['slide_number'] for s in data['slides']] != list(range(1, len(data['slides']) + 1)):
        raise ValueError('slide_number must be consecutive, starting at 1')
