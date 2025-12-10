"""
BureauBot Chatbot Core Logic
Extracted from Kanav_Guardrails_Addition.ipynb for web deployment
"""

import json, re, time, textwrap, pathlib
import fitz
# from google import genai
import google.generativeai as genai
import os

import pathlib
import fitz  # PyMuPDF
from collections import defaultdict

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Configuration
PROJECT_ID = "adsp-34002-ip07-the-four-musk"
LOCATION   = "us-central1"
MODEL      = "gemini-2.5-flash"
# GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key="AIzaSyAcI0HYFFuFDZBLGMyzuAuMtUn4GsUH-1o")
# client = genai.Client(api_key="AIzaSyAcI0HYFFuFDZBLGMyzuAuMtUn4GsUH-1o", vertexai=False)#, project=PROJECT_ID, location=LOCATION)
# upload = client.files.upload(file="../data/reference.txt")
# REFERENCE_ID = upload.name
client = genai.GenerativeModel(MODEL)

# Paths - adjusted for web deployment
BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
REFERENCE_PATH = BASE_DIR / "data" / "reference_UPDATED.txt"

def load_reference() -> dict:
    """reference_UPDATED.txt"""
    reference = {}
    try:
        if REFERENCE_PATH.exists():
            for line in REFERENCE_PATH.read_text(encoding="utf-8").splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    reference[k.strip().lower()] = v.strip()
        else:
            print("[ERROR] reference.txt not found")
    except Exception as e:
        print(f"[ERROR] Failed to read reference.txt: {e}")
    return reference

# ---------- Question rules + normalization ----------

import re, json
from typing import List, Dict, Any

OFFICER_PATTERNS = [
    r"\bauthorized officer\b",
    r"\bofficer signature\b",
    r"\bsignature of authorized officer\b",
    r"\bprinted name and title of authorized officer\b",
    r"\boffice use only\b",
]

def _is_officer_field(meta_field: dict) -> bool:
    text = " ".join(str(meta_field.get(k,"")) for k in ("name","label","desc","pdf_label","title")).lower()
    return any(re.search(p, text) for p in OFFICER_PATTERNS)

def _norm(s: str) -> str:
    s = (s or "").strip()
    return re.sub(r"\s+", " ", s)

def _has_if_applicable(meta_field: dict) -> bool:
    hay = " ".join([str(meta_field.get(k,"")) for k in ("label","name","desc")]).lower()
    return "(if applicable)" in hay or bool(meta_field.get("if_applicable"))

def _field_kind(meta_field: dict) -> str:
    # Try to infer: "checkbox" with Yes/No, "multicheck", "radio", or "text"
    t = (meta_field.get("type") or meta_field.get("field_type") or "").lower()
    opts = meta_field.get("options") or meta_field.get("choices") or []
    nm = (meta_field.get("name") or "").lower()
    if "checkbox" in t:
        # two boxes with Yes/No words? treat as yesno
        if re.search(r"\byes\b", nm) or re.search(r"\bno\b", nm):
            return "yesno"
        return "multicheck" if opts else "checkbox"
    if "radio" in t:
        return "radio"
    return "text"

def _label(meta_field: dict) -> str:
    for k in ("label","question","name","title","desc"):
        v = meta_field.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return meta_field.get("name","(unnamed)").strip()

def generate_question_plan(fields: List[dict]) -> List[Dict[str, Any]]:
    """
    Enforces your 4 rules when asking users:
      1) Officer-only fields → never asked (left blank).
      2) Yes/No → ask as confirmation only (Yes/No).
      3) Multi-select → list out the choices.
      4) (if applicable) → tell user they can answer 'N/A'; if N/A then skip filling.
    Returns a list of {"name","prompt","kind","options","if_applicable"} items.
    """
    plan = []
    for f in fields:
        if _is_officer_field(f):
            continue  # Rule 1

        kind = _field_kind(f)
        lab  = _label(f)
        prompt = lab

        if kind == "yesno":
            prompt = f"Confirm — {_label(f)} (Yes/No)"  # Rule 2
            opts = ["Yes","No"]
        elif kind in ("multicheck","radio"):
            options = f.get("options") or f.get("choices") or []
            opts = [str(o) for o in options]
            prompt = f"{_label(f)} — choose from: {', '.join(opts)}"  # Rule 3
        else:
            opts = None

        if _has_if_applicable(f):
            prompt += " (You may answer 'N/A' if not applicable.)"  # Rule 4

        plan.append({
            "name": f.get("name"),
            "prompt": _norm(prompt),
            "kind": kind,
            "options": opts,
            "if_applicable": _has_if_applicable(f),
        })
    return plan

def normalize_user_answers(raw_answers: Dict[str, Any], fields: List[dict]) -> Dict[str, Any]:
    """
    - 'N/A' (if applicable) → None (skip)
    - Yes/No → True/False
    - Validate multi-selects against options
    """
    index = { (f.get("name") or "").strip(): f for f in fields }
    out = {}
    for k, v in (raw_answers or {}).items():
        f = index.get(k)
        if not f:
            # allow chat-keys that aren't exact 'name' to pass through untouched; build_kv will fuzzy-map later
            out[k] = v
            continue

        if _is_officer_field(f):
            continue  # never fill

        if _has_if_applicable(f) and isinstance(v, str) and v.strip().lower() in {"n/a","na","not applicable"}:
            out[k] = None
            continue

        kind = _field_kind(f)
        if kind == "yesno":
            if isinstance(v, str):
                vv = v.strip().lower()
                out[k] = True if vv in {"y","yes"} else False if vv in {"n","no"} else None
            elif isinstance(v, bool):
                out[k] = v
            else:
                out[k] = None
        elif kind in ("multicheck","radio"):
            opts = [str(o) for o in (f.get("options") or f.get("choices") or [])]
            if kind == "multicheck":
                seq = v if isinstance(v, list) else [v]
                seq = [str(x).strip() for x in seq if x is not None]
                out[k] = [x for x in seq if not opts or x in opts]
            else:  # radio
                s = (str(v).strip() if v is not None else "")
                out[k] = s if (not opts or s in opts) else None
        else:
            out[k] = (None if v is None else str(v).strip())
    return out


PROMPT_VALIDATE_ANSWER = """
You are a strict data entry validator for immigration forms.

CONTEXT:
Field Name: "{field_label}"
User Answer: "{user_answer}"

YOUR TASK:
Determine if the answer is valid based on the Field Name.

GUARDRAILS (Apply the rule that matches the Field Name):

1. **Personal Names** (First, Middle, Last Name): 
   - MUST contain letters only (spaces, hyphens, apostrophes allowed).
   - REJECT if it contains numbers (e.g., "John123" is INVALID).
   - REJECT if it contains symbols (e.g., "John@" is INVALID).

2. **Alien Number (A-Number)**: 
   - MUST be strictly 7, 8, or 9 digits. 
   - REJECT if 10+ digits.

3. **Social Security Number (SSN)**: 
   - MUST be exactly 9 digits.

4. **Email Address**: 
   - MUST look like an email (e.g., user@domain.com).
   - REJECT if missing "@" or ".".

5. **Phone Number**: 
   - MUST contain at least 10 digits.

6. **Zip Code**: 
   - MUST be 5 digits (or 9 digits). REJECT letters.

7. **Dates (DOB, Expiration)**:
   - If the answer is a date, ensure it is a real date (e.g., not "February 30").
   - If the field implies a past event (e.g., Date of Birth), warn if the date is in the future.

8. **"Skip" / "N/A"**:
   - If the user types "skip", "pass", "N/A", "none", or "unknown", it is ALWAYS VALID.

OUTPUT FORMAT:
- If Valid: Return exactly the string "VALID".
- If Invalid: Return a short, polite error message explaining WHY (e.g., "Names cannot contain numbers. Please enter a valid Last Name.").
"""

def llm_validate_answer(field_label: str, user_answer: str) -> str:
    """
    Returns 'VALID' or an error message string.
    """
    # Fast exit for obvious skips to save time/cost
    if user_answer.lower() in ["skip", "n/a", "none", "no", "yes", "y", "n"]:
        return "VALID"

    prompt = PROMPT_VALIDATE_ANSWER.format(
        field_label=field_label, 
        user_answer=user_answer
    )
    
    # We use a very low temperature for strict logic
    # Using the existing call_gemini function
    response = call_gemini(SYSTEM_PROMPT, prompt, history=None)
    
    clean_resp = response.strip().replace('"', '').replace("'", "")
    
    if "VALID" in clean_resp.upper() and len(clean_resp) < 10:
        return "VALID"
    
    return clean_resp

# # 1. Handle Answer to PREVIOUS question (if applicable)
#         if session.fill_index > 0 or (session.fill_index == 0 and user_msg.lower() not in ["yes", "y"]):
#             
#             # Handle Help
#             if user_msg.strip() in ["?", "help"] or _looks_like_help_question(user_msg):
#                 curr_field = field_list[session.fill_index]
#                 expl = call_gemini(SYSTEM_PROMPT, f"Explain field: {curr_field}", history)
#                 return expl + "\n\nTry answering again (or 'skip')."
#             
#             # === GUARDRAIL CHECK START ===
#             # Only validate if they aren't skipping
#             if user_msg.lower() != "skip":
#                 curr_field = field_list[session.fill_index]
#                 label = pretty_field_label(curr_field)
#                 
#                 # Ask LLM if this answer makes sense
#                 validation_result = llm_validate_answer(label, user_msg)
#                 
#                 if validation_result != "VALID":
#                     # If invalid, STOP. Do not increment index. Return error to user.
#                     return f"⚠️ **Correction needed:** {validation_result}\n\nPlease try answering **{label}** again."
#             # === GUARDRAIL CHECK END ===
#
#             # If we passed validation (or skipped), save and continue
#             if not (session.fill_index == 0 and user_msg.lower() in ["yes", "y"]):
#                 if user_msg.lower() != "skip":
#                     curr_field = field_list[session.fill_index]
#                     val = convert_human_answer_to_metadata_value(curr_field, user_msg)
#                     session.answers[curr_field.get("name")] = val
#                 session.fill_index += 1

# ---------- Session ----------
@dataclass
class SessionState:
    stage: str = "select_form"

    # Form selection
    form_key: Optional[str] = None
    case_info: str = ""
    confirm_answers: str = ""

    # Legacy
    fields: List[Any] = field(default_factory=list)
    list_phase: str = "show"
    scoping_answers: str = ""
    scoping_questions: List[str] = field(default_factory=list)
    confirm_questions: List[str] = field(default_factory=list)
    last_checklist_text: str = ""

    # Field-by-field filling
    fill_fields: List[dict] = field(default_factory=list)
    fill_index: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    review_summary: str = ""
    filled_pdf_path: Optional[str] = None

    # NEW LOGIC
    decision_item5: Optional[str] = None
    has_attorney: Optional[bool] = None

    human_questions: Dict[str, str] = field(default_factory=dict)
    q_index: int = 0

# ---------- I/O ----------
def fetch_meta(form_key: str) -> str:
    """
    Load metadata JSON as raw text.
    """
    if not form_key:
        return json.dumps({"form_key": str(form_key), "fields": []})

    base_dir = BASE_DIR / "data"
    if form_key.startswith("eoir_form"):
        meta_path = base_dir / "EOIR" / f"{form_key}_meta.json"
    else:
        meta_path = base_dir / "all" / f"{form_key}_meta.json"

    try:
        return meta_path.read_text(encoding="utf-8")
    except:
        return json.dumps({
            "form_key": form_key,
            "title": load_reference().get(form_key, form_key),
            "fields": []
        })
        
def parse_pdf(form_key: str) -> str:
    if not form_key:
        return ""

    base = BASE_DIR / "data"
    if form_key.startswith("eoir_form"):
        pdf_path = base / "EOIR" / f"{form_key}.pdf"
    else:
        pdf_path = base / "all" / f"{form_key}.pdf"

    print("[DEBUG] parse_pdf using:", pdf_path)

    try:
        doc = fitz.open(pdf_path)
        text = "".join(page.get_text() for page in doc)
        doc.close()
        return text
    except Exception as e:
        print("[WARN] parse_pdf failed:", e)
        return f"Dummy text for {form_key}"
              
        
def load_meta_dict(form_key: str) -> dict:
    """
    Load the metadata JSON file as a Python dict.
    Falls back to an empty structure if missing/broken.
    """
    try:
        meta_json = fetch_meta(form_key)  # existing helper that returns JSON text
        return json.loads(meta_json)
    except Exception:
        return {"form_key": form_key, "fields": []}


def map_answers_to_payload(form_key: str, answers: dict) -> dict:
    """
    Our `answers` dict is already keyed by metadata `name`.
    Just filter to valid field names for this form and drop empty answers.
    """
    meta = load_meta_dict(form_key)

    if isinstance(meta, list):
        fields = meta
    else:
        fields = meta.get("fields", [])

    valid_names = {
        f.get("name")
        for f in fields
        if isinstance(f, dict) and f.get("name")
    }

    payload = {
        k: v
        for k, v in answers.items()
        if k in valid_names and v not in (None, "")
    }

    return payload

def _rect_from_meta(f: dict):
    """Try to get a rectangle for this field from metadata."""
    if isinstance(f.get("rect"), (list, tuple)) and len(f["rect"]) == 4:
        return tuple(float(x) for x in f["rect"])
    if isinstance(f.get("bbox"), (list, tuple)) and len(f["bbox"]) == 4:
        return tuple(float(x) for x in f["bbox"])
    if all(k in f for k in ("x", "y", "w", "h")):
        x, y, w, h = float(f["x"]), float(f["y"]), float(f["w"]), float(f["h"])
        return (x, y, x + w, y + h)
    return None

def _page_index_from_meta(f: dict) -> int:
    """1-based or 0-based page index → 0-based page index."""
    if "page_index" in f:
        try:
            return int(f["page_index"])
        except:
            pass
    if "page" in f:
        try:
            return max(0, int(f["page"]) - 1)
        except:
            pass
    return 0

def is_checkbox_like_label(label: str) -> bool:
    """Return True if the label looks like a yes/no checkbox, etc."""
    if not label:
        return False
    l = str(label).lower()
    return any(
        token in l
        for token in ["yes", "no", "☐", "check box", "check this box"]
    )

def llm_build_pdf_payload(form_key: str, user_block: str, tries: int = 3) -> dict:
    meta_json = fetch_meta(form_key)
    pdf_text = parse_pdf(form_key)

    base_prompt = textwrap.dedent(f"""
        You are a CBP/EOIR/USCIS/ICE-form-filling expert.

        Form metadata:
        {meta_json}
        
        Form text:
        {pdf_text}
        User answers:
        \"\"\"{user_block}\"\"\"
        TASK
        ----
        Return ONE JSON object.
        • Keys = field "name" from metadata that the user clearly answered
        • Values = the user's answer exactly as written
        • Omit every un-answered field (do NOT output nulls)
        No markdown, no code fences, no prose.
    """)

    for attempt in range(1, tries + 1):
        raw = call_gemini(SYSTEM_PROMPT, base_prompt)
        clean = re.sub(r"^[`]{3}json|[`]{3}$", "", raw.strip(), flags=re.I|re.M).strip()

        try:
            return json.loads(clean)
        except json.JSONDecodeError as e:
            print(f"attempt {attempt}: invalid JSON → {e}")
            if attempt == tries:
                raise
            time.sleep(0.5)                # tiny back-off
            base_prompt = (
                "Your previous reply was not valid JSON. "
                "PLEASE resend only the JSON object, nothing else.\n\n"
                + base_prompt
            )


def fill_pdf_from_payload(form_key: str, payload: dict, output_dir: str = "filled_pdfs") -> str:
    """
    Fill a PDF using either real AcroForm widgets (preferred) or,
    if we can't match any widgets, overlay 'field: value' lines as a fallback.

    form_key  – internal key, e.g. 'eoir_form_26'
    payload   – dict { metadata_field_name : answer }
    """
    if not form_key:
        return ""

    base = BASE_DIR / "data"
    if form_key.startswith("eoir_form"):
        pdf_dir = base / "EOIR"
    else:
        pdf_dir = base / "all"

    in_pdf_path = pdf_dir / f"{form_key}.pdf"
    out_dir = pathlib.Path(output_dir)
    out_dir.mkdir(exist_ok=True)
    out_pdf_path = out_dir / f"{form_key}_filled.pdf"

    print(f"[DEBUG] Opening PDF for fill: {in_pdf_path}")
    print(f"[DEBUG] Payload keys: {list(payload.keys())[:20]}")

    doc = fitz.open(in_pdf_path)

    # ---------- 1) Try to fill real widgets ----------
    widgets_filled = 0

    for page_index, page in enumerate(doc):
        w_iter = page.widgets() or []
        w_list = list(w_iter)  # materialize generator

        for w in w_list:
            w_name = (w.field_name or "").strip()
            if not w_name:
                continue

            # direct match or "2B" substring match
            value = None
            if w_name in payload:
                value = payload[w_name]
            else:
                for k, v in payload.items():
                    if k and k in w_name:
                        value = v
                        break

            if value is None:
                continue

            value_str = str(value)

            # Text field
            if w.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                w.field_value = value_str
                w.update()
                widgets_filled += 1

            # Checkbox-ish
            elif w.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                yn = value_str.strip().lower()
                wname = (w.field_name or "").lower()

                # For Item 5, any non-empty value means "checked"
                if wname in {"5a", "5b", "5c"}:
                    is_no = yn in {"", "no", "n", "false", "0", "off", "skip"}
                    w.field_value = "Yes" if not is_no else "Off"
                else:
                    is_no = yn in {"", "no", "n", "false", "0", "off", "skip"}
                    w.field_value = "Yes" if not is_no else "Off"

                w.update()
                widgets_filled += 1


    print(f"[DEBUG] widgets_filled = {widgets_filled}")

    # ---------- 2) Fallback: overlay debug text if nothing matched ----------
    if widgets_filled == 0 and payload:
        print("[WARN] No widgets matched payload – overlaying debug text instead.")
        page = doc[0]
        y = 72
        for field, value in payload.items():
            line = f"{field}: {value}"
            if y > 780:
                page = doc.new_page(width=595, height=842)
                y = 72
            page.insert_text((72, y), line, fontsize=10)
            y += 14

    # ---------- 3) Save ----------
    doc.save(out_pdf_path)
    doc.close()
    print(f"[DEBUG] Saved filled PDF → {out_pdf_path}")
    return str(out_pdf_path)
# ---------- Form key normalization ----------
ALIAS_MAP = {
    "ar11": "uscis_form_ar11",
    "i246": "ice_form_i246",
    "i589": "uscis_form_i589",
    "i129": "uscis_form_i129",
    "26": "eoir_form_26",
    "42": "eoir_form_42",
    "1300": "cbp_form_1300",
    "h1b": "uscis_form_i129",
    "f1": "uscis_form_i129",
}

def normalize_form_key(text: str) -> str | None:
    reference = load_reference()
    s = text.lower().strip().replace("-", "").replace(" ", "")
    
    for k, v in ALIAS_MAP.items():
        if k in s:
            if v in reference:
                # print(f"[DEBUG] Alias: '{text}' → '{v}'")
                return v
    
    m = re.search(r'\b(eoir|cbp|uscis|ice)[\s_-]*(form)?[\s_-]*([a-z]?\d+[a-z]?)\b', s)
    if m:
        agency = m.group(1)
        code = m.group(3)
        candidate = f"{agency}_form_{code}"
        if candidate in reference:
            print(f"[DEBUG] Pattern: '{text}' → '{candidate}'")
            return candidate
    
    text_words = set(s.split())
    for catalog_key in reference:
        if text_words & set(catalog_key.split("_")):
            print(f"[DEBUG] Fuzzy: '{text}' → '{catalog_key}'")
            return catalog_key
    
    return None

# ---------- LLM call ----------
def call_gemini(system_prompt: str, user_prompt: str, history=None, last_n_turns: int = 10) -> str:
    """Robust Gemini call: fully compatible with google.generativeai SDK"""
    combined_prompt = f"{system_prompt.strip()}\n\n{user_prompt.strip()}"

    contents = []
    if history:
    #     trimmed = history[-(last_n_turns * 2):]
    #     for h in trimmed:
    #         if isinstance(h, dict) and "role" in h:
    #             contents.append(h)
    #         elif hasattr(h, "role") and hasattr(h, "parts"):
    #             # convert legacy Content -> dict
    #             parts = []
    #             for p in getattr(h, "parts", []):
    #                 if hasattr(p, "text"):
    #                     parts.append({"text": p.text})
    #             contents.append({"role": h.role, "parts": parts})
        trimmed = history[-(last_n_turns*2):]
        contents.extend(trimmed)    
    # contents.append(Content(role="user", parts=[Part(text=combined_prompt)]))
    contents.append({"role": "user", "parts": [{"text": combined_prompt}]})

    config = genai.types.GenerationConfig(
        temperature=0.3,
        top_p=0.9,
        max_output_tokens=8048,
    )

    try:
        response = client.generate_content(
            contents=contents,
            generation_config=config,
        )
        return response.text.strip()
    except Exception as e:
        print(f"[ERROR] Gemini call failed: {e}")

        return "I need more details. What is your situation?"
# ---------- Prompts ----------

#System
SYSTEM_PROMPT = """
You are a U.S. immigration and customs form expert with 30 years of experience.
Be empathetic, confident, and clear. Always maintain the context.
If the user challenges your choice, explain your reasoning but do not apologize unless an actual mistake was made.; if they are right, update your suggestion.
"""

# Form Selection

PROMPT_SELECT_FORM_CHAT = """
You are a routing assistant that chooses which official immigration or customs form the user needs.

CONTEXT FROM USER AND PRIOR Q&A:
{context}

AVAILABLE INTERNAL FORM KEYS (you may ONLY choose from these):
{forms_list}

YOUR RESPONSE MUST BE A SINGLE JSON OBJECT WITH THIS SHAPE:
- Top-level keys:
  - "questions": a list of zero, one, or two short clarifying questions (strings).
  - "suggestion": an object with:
      - "form_key": a string.
      - "reason": a short explanation of why that form was chosen.

RULES FOR THE JSON YOU RETURN:

0. First-turn behavior (mandatory)
   - Treat the `CONTEXT FROM USER AND PRIOR Q&A` as the full conversation so far.
   - If the context does NOT contain any lines starting with "Q:" then no
     clarifying questions have been asked yet. In that case:
       - You MUST put 1–2 short clarifying questions in "questions".
       - You MUST set "suggestion.form_key" to the empty string "".
       - You MUST NOT recommend any form yet.
   - Only when the context DOES contain at least one line starting with "Q:"
     are you allowed to recommend a form by setting a non-empty "suggestion.form_key".

1. Clarifying questions
   - If you do NOT yet have enough information to choose a form, put up to 2
     short clarifying questions in "questions".
   - In that case, set "suggestion.form_key" to the empty string "" for now.
   - Questions must be concise and directly related to picking the correct form.

2. Final recommendation
   - If you DO have enough information to recommend a form, then:
       - Set "questions" to an empty list [].
       - Set "suggestion.form_key" to the best matching internal form key.
   - "form_key" MUST be exactly one of the strings listed in {forms_list}.
   - NEVER return values such as "unknown", "none", "n/a", or any other free text
     as the form_key. If no form is appropriate, use the empty string "".

3. No suitable form
   - If none of the available forms is appropriate for the user's situation,
     leave "suggestion.form_key" as the empty string "" and in "reason" explain
     briefly why none of the forms fits.

5. Output format
   - Return ONLY the JSON object described above.
   - Do NOT include any extra explanation, markdown, or text outside the JSON.
"""


# Scoping (Form + Field)

PROMPT_SCOPING_QUESTIONS = """
You are an immigration paralegal.

You have a reference catalog entry for an immigration form.

Form key: {form_key}
Catalog description (how/when this form is used):
{description}

Your job:
- Write the 1–2 most essential scoping questions to confirm this form is actually the right one for the user.
- Questions should be short and natural.
- Prefer yes/no or short-answer questions that clarify eligibility or filing posture
  (e.g., who made the decision, what type of decision, timing, status, etc.).
- Do NOT mention form numbers in the question text.

Return ONLY a JSON array of strings, for example:
["Was the decision you are appealing made by an Immigration Judge?",
 "Did you receive a written denial notice for this case?"]
"""

PROMPT_FIELDS_FROM_ANS = """
Form: {form_key}
Metadata: {meta_json}
Form text: {pdf_text}
User answers: {scoping_answers}

Your job:
- List ONLY the metadata field names that should be filled (exclude agency-only fields).

Return ONLY a JSON object in this exact format:

{{
  "fields": ["FieldName1", "FieldName2", "..."]
}}
"""

PROMPT_FIELD_HELP = """
You are an immigration legal forms assistant.

The user is filling out this form: {form_key}
Current field: {field_name}

Field metadata (JSON):
{field_meta_json}

User's question about this field:
"{user_msg}"

Your job:
- Explain in simple terms what information belongs in this field.
- Clarify where they can usually find this information (e.g., passport, denial notice, charging document).
- Give 1–2 concrete example answers if helpful.
- Do NOT make up their actual answer.
- Keep it under 3 short paragraphs.
"""

# Ad hoc questions

PROMPT_FORM_QA = """
You are an immigration forms assistant.

Form key: {form_key}
Catalog description (how/when this form is used):
{description}

User question:
\"\"\"{user_msg}\"\"\"

Your job:
- Answer the user's question clearly and accurately in plain language.
- Use the catalog description as the primary source of truth.
- Keep the answer brief (1–3 short paragraphs).
- If relevant, explain what the form does, who typically uses it, and what it does NOT do.

End your answer with this sentence:
"When you're ready, you can say **yes** if you want to fill this form, or **no** if you'd like me to reconsider."
"""

PROMPT_ROUTER_QA = """
You are an immigration forms assistant.

Conversation so far:
{context}

User question:
\"\"\"{user_msg}\"\"\"

Your job:
- If they ask about an acronym (e.g., "BIA", "EOIR", "USCIS") or a concept, explain it in clear terms.
- Keep the answer short (1–3 short paragraphs).
- Do NOT choose or change any form recommendations in this response.
- Do NOT ask new clarifying questions yourself.

Just answer the question and stop.
"""
# ---------- Payload builder ----------
def llm_build_pdf_payload(form_key: str, user_block: str, history=None, tries: int = 3) -> dict:
    """
    Maps user answers to metadata fields. 
    Optimized: Does NOT use chat history to save tokens and reduce confusion.
    """
    # 1. Load only the metadata (skip PDF text to save tokens)
    meta_json = fetch_meta(form_key)
    
    base_prompt = f"""
    You are a form data processor.
    
    TASK: Map the User Answers to the correct "name" from the Field Metadata.
    
    Field Metadata:
    {meta_json}
    
    User Answers:
    {user_block}
    
    RULES:
    1. Return a SINGLE JSON object.
    2. Keys must match the "name" field from the metadata EXACTLY.
    3. Values must be the answer from the user.
    4. Ignore fields that the user did not answer.
    5. Output JSON only. No markdown, no explanations.
    """

    for attempt in range(tries):
        # PASS history=None explicitly. We want a fresh context for this data processing task.
        try:
            raw = call_gemini(SYSTEM_PROMPT, base_prompt, history=None)
            
            # Clean up markdown
            clean = re.sub(r"^[`]{3}json|[`]{3}$", "", raw.strip(), flags=re.I|re.M).strip()
            
            if not clean:
                print(f"[WARN] Payload generation returned empty string (Attempt {attempt+1})")
                time.sleep(1)
                continue

            return json.loads(clean)

        except json.JSONDecodeError:
            print(f"[WARN] Invalid JSON from payload gen (Attempt {attempt+1}). Raw: {raw[:100]}...")
            if attempt == tries - 1:
                print("[ERROR] Could not generate valid JSON payload. Returning empty.")
                return {} 
            time.sleep(0.5)
        except Exception as e:
            print(f"[ERROR] Unexpected error in payload gen: {e}")
            return {}
            
    return {}
# ---------- Conversation orchestrator ----------


import re

def normalize_form_key(text: str) -> str | None:
    reference = load_reference()
    s = text.lower().strip().replace("-", "").replace(" ", "")

    # fix "form_eoir_26" → "eoir_form_26" up front
    s = s.replace("formeoir", "eoirform")

    for k, v in ALIAS_MAP.items():
        if k in s and v in reference:
            return v

    m = re.search(r'\b(eoir|cbp|uscis|ice)[\s_-]*(form)?[\s_-]*([a-z]?\d+[a-z]?)\b', s)
    if m:
        agency = m.group(1)
        code = m.group(3)
        candidate = f"{agency}_form_{code}"
        if candidate in reference:
            return candidate

    text_words = set(s.split())
    for catalog_key in reference:
        if text_words & set(catalog_key.split("_")):
            return catalog_key

    return None

def _looks_like_help_question(text: str) -> bool:
    t = text.strip().lower()
    if not t:
        return False
    return (
        "what is " in t
        or "what's " in t
        or "what does" in t
        or "what do you mean" in t
        or "can you explain" in t
        or t.endswith("?")
    )

def generate_scoping_questions_for_form(form_key: str, history):
    """
    Use PROMPT_SCOPING_QUESTIONS + reference.txt to get 1–2 scoping questions
    for ANY form in the reference catalog.
    """
    reference = load_reference()

    # Get a description if we have one, but don't bail if we don't
    if form_key:
        desc = reference.get(form_key) or reference.get(form_key.lower()) or ""
    else:
        desc = ""

    prompt = PROMPT_SCOPING_QUESTIONS.format(
        form_key=form_key,
        description=desc,
    )

    reply = call_gemini(SYSTEM_PROMPT, prompt, history or [])

    import json, re

    match = re.search(r"\[.*\]", reply, re.DOTALL)
    if not match:
        print("[WARN] No JSON array found in scoping reply:", reply[:200])
        return []

    try:
        arr = json.loads(match.group())
        return [q.strip() for q in arr if isinstance(q, str) and q.strip()][:2]
    except Exception as e:
        print("[WARN] scoping JSON parse failed:", e)
        return []

def pretty_field_label(meta_field: dict) -> str:
    """
    Prefer human labels, fall back to the internal name like '2B' only if we must.
    """
    return (
        meta_field.get("label")
        or meta_field.get("pdf_label")
        or meta_field.get("title")
        or meta_field.get("name")
        or "this field"
    )
 
def convert_human_answer_to_metadata_value(meta_field, user_answer):
    """
    Convert natural-language answers to metadata-expected values.
    Handles checkbox, yes/no, multiple options, etc.
    """
    name = meta_field.get("name", "").lower()

    # Yes/No to checkbox
    if "detained" in name:
        if user_answer.lower() in ["yes", "y"]:
            return "Yes"
        else:
            return "Off"

    # generic yes/no fields
    if user_answer.lower() in ["yes", "y"]:
        return "Yes"
    if user_answer.lower() in ["no", "n"]:
        return "Off"

    # otherwise treat as free text
    return user_answer


def on_user_message(user_msg: str, session: SessionState, history) -> str:
    # ---------- Stage guard ----------
    VALID_STAGES = {
        "select_form", "confirm_form", "scoping", "list_fields", 
        "await_fill_ready", "ask_has_attorney", "fill_fields", 
        "review_answers", "complete"
    }

    if session.stage not in VALID_STAGES:
        print("[INFO] Session had an unknown stage; resetting to select_form.")
        session.stage = "select_form"
        session.case_info = ""
        session.confirm_answers = ""
        session.confirm_questions = []
        session.q_index = 0

    # Use internal form KEYS for the router
    ref_catalog = load_reference()
    forms_list = "\n".join([f"- {k}: {v}" for k, v in ref_catalog.items()])

    # ======================================================
    # STAGE 1: SELECT_FORM
    # ======================================================
    if session.stage == "select_form":
        session.case_info += "\n" + user_msg
        prompt = PROMPT_SELECT_FORM_CHAT.format(
            context=session.case_info + "\n" + session.confirm_answers,
            forms_list=forms_list,
        )
        reply = call_gemini(SYSTEM_PROMPT, prompt, history)
        
        try:
            m = re.search(r"\{.*\}", reply, re.DOTALL)
            if not m: return "I need a bit more detail about your situation."
            data = json.loads(m.group())
            
            if data.get("questions"):
                session.confirm_questions = data["questions"]
                session.q_index = 0
                session.stage = "confirm_form"
                return f"**Q1:** {session.confirm_questions[0]}"
            
            suggestion = data.get("suggestion", {})
            raw_key = suggestion.get("form_key", "")
            
            if raw_key:
                normalized = normalize_form_key(raw_key)
                session.form_key = normalized or raw_key.lower().replace(" ", "_")
                
                # Validate Key
                if session.form_key not in ref_catalog:
                     return f"I tried to pick form '{session.form_key}', but I don't have the metadata for it. Please clarify."

                session.stage = "confirm_form"
                session.confirm_questions = []
                session.q_index = 0
                return f"**I recommend:** {session.form_key}\n\nReason: {suggestion.get('reason')}\n\n**Do you want to fill this form?** *(yes/no)*"
            
            return suggestion.get("reason", "I couldn't find a form.")
        except Exception as e:
            print(f"[WARN] Select Error: {e}")
            return reply

    # ======================================================
    # STAGE 2: CONFIRM_FORM
    # ======================================================
    if session.stage == "confirm_form":
        if session.confirm_questions and session.q_index < len(session.confirm_questions):
            session.confirm_answers += f"\nQ: {session.confirm_questions[session.q_index]}\nA: {user_msg}"
            session.q_index += 1
            if session.q_index < len(session.confirm_questions):
                return f"**Q{session.q_index+1}:** {session.confirm_questions[session.q_index]}"
            return on_user_message("", session, history) # Re-run select logic

        msg = user_msg.strip().lower()
        if msg in ["yes", "y"]:
            session.scoping_questions = generate_scoping_questions_for_form(session.form_key, history)
            session.scoping_answers = ""
            session.q_index = 0
            if session.scoping_questions:
                session.stage = "scoping"
                return f"Before we start, a few checks.\n\n**Q1:** {session.scoping_questions[0]}"
            else:
                session.stage = "list_fields"
                return on_user_message("", session, history) # Auto-advance
        elif msg in ["no", "n"]:
            session.stage = "select_form"
            return "Okay, let's try again. Describe your situation."
        else:
            qa_prompt = PROMPT_FORM_QA.format(form_key=session.form_key, description=ref_catalog.get(session.form_key,""), user_msg=user_msg)
            return call_gemini(SYSTEM_PROMPT, qa_prompt, history)

    # ======================================================
    # STAGE 2.5: SCOPING
    # ======================================================
    if session.stage == "scoping":
        session.scoping_answers += f"Q: {session.scoping_questions[session.q_index]}\nA: {user_msg}\n"
        session.q_index += 1
        if session.q_index < len(session.scoping_questions):
            return f"**Q{session.q_index+1}:** {session.scoping_questions[session.q_index]}"
        session.stage = "list_fields"
        # Fallthrough to list_fields

    # ======================================================
    # STAGE 3: LIST FIELDS (HYBRID BATCH/LOOP)
    # ======================================================
    if session.stage == "list_fields":
        if not session.fill_fields:
            print(f"[DEBUG] Attempting to fetch meta for form_key: '{session.form_key}'")
            meta_json = fetch_meta(session.form_key)
            print(f"[DEBUG] Meta JSON length: {len(meta_json)}")
            try:
                meta = json.loads(meta_json)
                all_fields = meta if isinstance(meta, list) else meta.get("fields", [])
                print(f"[DEBUG] Found {len(all_fields)} raw fields in metadata")
                session.fill_fields = [f for f in all_fields if isinstance(f, dict) and not _is_officer_field(f)]
                print(f"[DEBUG] Filtered to {len(session.fill_fields)} fillable fields")
            except Exception as e:
                print(f"[ERROR] Failed to parse metadata: {e}")
                session.fill_fields = []
            
            if not session.fill_fields:
                print(f"[ERROR] No fields found for form_key: {session.form_key}")
                return "Error: No fields found for this form."

        session.human_questions = {}
        seen = set()
        batch_success = False
        
        # Attempt Batch
        try:
            field_list_text = ""
            for idx, f in enumerate(session.fill_fields):
                label = f.get("label") or f.get("pdf_label") or f.get("name") or f"Field_{idx}"
                field_list_text += f"ID: {f.get('name')} | Label: {label}\n"

            prompt = f"""
            You are an immigration paralegal.
            Here is a list of fields from Form {session.form_key}.
            
            FIELD LIST:
            {field_list_text}

            TASK:
            For every field, write ONE natural-language question (e.g., "Are you detained?").
            If multiple fields belong to the same question (like Yes/No checkboxes), give them the EXACT SAME question text.

            OUTPUT FORMAT:
            Return valid JSON only. No markdown.
            {{
                "Field_Name_From_ID": "Your Question Here",
                ...
            }}
            """
            
            raw_resp = call_gemini(SYSTEM_PROMPT, prompt)
            clean = re.sub(r"^[`]{3}json|[`]{3}$", "", raw_resp.strip(), flags=re.I|re.M).strip()
            batch_map = json.loads(clean)
            batch_success = True
            print("[DEBUG] Batch generation successful.")
        except Exception as e:
            print(f"[WARN] Batch JSON failed ({e}). Switching to Item-by-Item generation...")
            batch_map = {}

        # Apply and Deduplicate
        checklist = []
        for idx, f in enumerate(session.fill_fields):
            name = f.get("name")
            
            # Skip if we already handled this field name (e.g. duplicate checkboxes)
            if name in session.human_questions: 
                continue 

            q = batch_map.get(name)
            
            # Fallback logic if batch failed or missed this specific field
            if not q:
                if not batch_success: # Only do slow call if batch totally failed
                    label = f.get("label") or name
                    q_prompt = f"Rewrite this form field label into a question: '{label}'"
                    q = call_gemini(SYSTEM_PROMPT, q_prompt).strip()
                    time.sleep(0.2) # Be nice to API
                else:
                    q = f.get("label") or f.get("pdf_label") or name

            # Deduplication
            if q in seen:
                session.human_questions[name] = None # Mark as duplicate question
            else:
                seen.add(q)
                session.human_questions[name] = q
                checklist.append(f"* {q}")

        session.last_checklist_text = "\n".join(checklist)
        session.stage = "await_fill_ready"
        return f"Checklist for {session.form_key}:\n\n{session.last_checklist_text}\n\nReady to fill? (yes/no)"

    # ======================================================
    # STAGE 3.5: READY
    # ======================================================
    if session.stage == "await_fill_ready":
        if user_msg.lower() in ["yes", "y"]:
            session.stage = "fill_fields"
            session.fill_index = 0
            # IMPORTANT: Do not return here! We want to fall through to STAGE 4 immediately.
        elif user_msg.lower() in ["no", "n"]:
            session.stage = "select_form"
            return "Okay, stopped."
        else:
            return call_gemini(SYSTEM_PROMPT, user_msg, history)

    # ======================================================
    # STAGE 4: FILL FIELDS
    # ======================================================
    # NOTE: This MUST be an 'if', not 'elif', so it runs immediately after Stage 3.5
    if session.stage == "fill_fields":
        field_list = session.fill_fields
        
        # 1. Handle Answer to PREVIOUS question
        # We only process an answer if we are NOT in the very first 'yes' trigger
        is_start_signal = (session.fill_index == 0 and user_msg.lower() in ["yes", "y"])
        
        if not is_start_signal:
            # Handle Help
            if user_msg.strip() in ["?", "help"] or _looks_like_help_question(user_msg):
                curr_field = field_list[session.fill_index]
                expl = call_gemini(SYSTEM_PROMPT, f"Explain field: {curr_field}", history)
                return expl + "\n\nTry answering again (or 'skip')."
            
            # === GUARDRAIL CHECK START ===
            # Only validate if they aren't skipping
            if user_msg.lower() != "skip":
                curr_field = field_list[session.fill_index]
                label = pretty_field_label(curr_field)
                
                # Ask LLM if this answer makes sense
                validation_result = llm_validate_answer(label, user_msg)
                
                if validation_result != "VALID":
                    # If invalid, STOP. Do not increment index. Return error to user.
                    return f"⚠️ **Correction needed:** {validation_result}\n\nPlease try answering **{label}** again."
            # === GUARDRAIL CHECK END ===

            # Save Answer
            if user_msg.lower() != "skip":
                curr_field = field_list[session.fill_index]
                val = convert_human_answer_to_metadata_value(curr_field, user_msg)
                session.answers[curr_field.get("name")] = val
            
            # Move to next
            session.fill_index += 1

        # 2. Find NEXT valid question
        while session.fill_index < len(field_list):
            curr_field = field_list[session.fill_index]
            name = curr_field.get("name")
            
            # If we already have an answer (e.g. from checkboxes sharing names), skip
            if session.answers.get(name):
                session.fill_index += 1
                continue

            q = session.human_questions.get(name)
            
            # If Duplicate (None), skip automatically
            if q is None and name in session.human_questions: 
                session.fill_index += 1
                continue
            
            # Fallback if q missing
            if not q: q = pretty_field_label(curr_field)
            
            # Found valid question
            return f"**Q{session.fill_index+1}:** {q} (or 'skip')"

        # 3. Done
        session.stage = "review_answers"
        summary = "\n".join([f"- {k}: {v}" for k,v in session.answers.items()])
        session.review_summary = summary
        return f"✅ Done! Summary:\n{summary}\n\nIs this correct? (yes/no)"

    # ======================================================
    # STAGE 5: REVIEW & BUILD
    # ======================================================
    if session.stage == "review_answers":
        if user_msg.lower() in ["yes", "y"]:
            user_block = "\n".join([f"{k}: {v}" for k,v in session.answers.items()])
            payload = llm_build_pdf_payload(session.form_key, user_block)
            pdf_path = fill_pdf_from_payload(session.form_key, payload)
            session.filled_pdf_path = pdf_path
            session.stage = "complete"
            
            # Extract just the filename for the download link
            import os
            pdf_filename = os.path.basename(pdf_path)
            download_url = f"/api/download/{pdf_filename}"
            
            return f"✅ **Your form is ready!**\n\n[📥 Click here to download your filled PDF]({download_url})\n\nFilename: `{pdf_filename}`"
        else:
            session.stage = "fill_fields"
            session.fill_index = 0
            session.answers = {}
            return "Okay, restarting fill process."

    return "Session finished."


def chat_with_agent(user_message: str, session: SessionState, history: list):
    """Chat wrapper for the agent"""
    history.append({"role": "user", "parts": [{"text": user_message}]})
    backend_reply = on_user_message(user_message, session, history)
    history.append({"role": "model", "parts": [{"text": backend_reply}]})
    return backend_reply, history
