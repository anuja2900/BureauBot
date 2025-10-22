from __future__ import annotations
import os, json, re, uuid, textwrap
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
import google.generativeai as genai

# --------------------------- GEMINI SETUP (取代所有 Llama) ---------------------------
# 設定 Google API Key (從 Google AI Studio 拿)
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY", "AIzaSyAcI0HYFFuFDZBLGMyzuAuMtUn4GsUH-1o")  # 暫時放這裡，之後設環境變數
genai.configure(api_key=GOOGLE_API_KEY)
gemini_model = genai.GenerativeModel('gemini-2.5-flash')

History = List[Tuple[str, str]]  # (role, content)

def llama_chat(system_prompt: str, user_prompt: str, history: Optional[History] = None) -> str:
    """使用 Gemini 取代 Llama"""
    # 建構完整 prompt
    full_prompt = f"{system_prompt}\n\n{user_prompt}"
    if history:
        for role, content in history[-6:]:  # 只取最近 6 輪，避免 token 超限
            full_prompt += f"\nUser: {content if role == 'user' else ''}"
            full_prompt += f"\nAssistant: {content if role == 'assistant' else ''}"
    
    response = gemini_model.generate_content(full_prompt)
    return response.text.strip()

# Paths (保持不變)
BASE_DIR = Path("/home/jupyter/adsp-bureaubot-bucket")
DATA_DIR = BASE_DIR / "data"
REF_PATH = DATA_DIR / "forms_reference.txt"
AGENCY_DIRS = ["CBP", "EOIR", "ICE", "USCIS"]

# -------------------------
# Reference + Metadata (保持不變)
# -------------------------
DISCLAIMER = (
    "I’m an informational assistant, not a lawyer. I can help organize info and fill "
    "official PDFs you provide, but I don’t give legal advice."
)

def ensure_reference() -> None:
    REF_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not REF_PATH.exists():
        REF_PATH.write_text("cbp_form_101: CBP ATC Event Application\n", encoding="utf-8")

def read_catalog() -> Dict[str, str]:
    ensure_reference()
    out = {}
    for line in REF_PATH.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip().lower()] = v.strip()
        else:
            k = line.strip().lower()
            if k:
                out[k] = k
    return out

def safe_exists(p: Path) -> bool:
    try:
        return p.exists()
    except OSError:
        return False

def find_meta_path(key: str) -> Path | None:
    candidates = (f"{key}.json", f"{key}_meta.json", f"{key}_meta.main.json")
    for d in [DATA_DIR / "meta", DATA_DIR / "all"]:
        for name in candidates:
            p = d / name
            if safe_exists(p):
                return p
    agency = key.split("_", 1)[0].upper()
    for ad in AGENCY_DIRS:
        d = DATA_DIR / ad
        for name in candidates:
            p = d / name
            if safe_exists(p):
                return p
    return None

def resolve_pdf_path(meta_any, key: str) -> Path | None:
    if isinstance(meta_any, dict):
        pdf_rel = meta_any.get("pdf_path")
        if pdf_rel:
            p = Path(pdf_rel)
            if not p.is_absolute():
                p = DATA_DIR / pdf_rel
            if safe_exists(p):
                return p
    p = DATA_DIR / "pdfs" / f"{key}.pdf"
    if safe_exists(p):
        return p
    agency = key.split("_", 1)[0].upper()
    for ad in AGENCY_DIRS:
        p = DATA_DIR / ad / f"{key}.pdf"
        if safe_exists(p):
            return p
    return None

def ready_forms() -> Dict[str, str]:
    cat = read_catalog()
    ready = {}
    for key, title in cat.items():
        mp = find_meta_path(key)
        if not mp:
            continue
        try:
            meta_any = json.loads(mp.read_text(encoding="utf-8"))
        except Exception:
            continue
        pdf_p = resolve_pdf_path(meta_any, key)
        if pdf_p:
            ready[key] = title
    print(f"[scan] catalog: {len(cat)} | ready: {len(ready)}")
    return ready

def load_meta(form_key: str) -> Dict[str, Any]:
    p = find_meta_path(form_key)
    if p:
        return json.loads(p.read_text(encoding="utf-8"))
    raise ValueError(f"Meta not found for {form_key}")

def read_pdf_text(pdf_path: Path) -> str:
    try:
        import fitz
        doc = fitz.open(pdf_path)
        chunks = [pg.get_text("text") or "" for pg in doc]
        doc.close()
        return "\n".join(chunks)[:5000]
    except Exception:
        return ""

# -------------------------
# PDF filling (保持不變)
# -------------------------
def fill_pdf_acroform(input_pdf: str, output_pdf: str, acro_data: Dict[str, str]) -> bool:
    try:
        from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName
        tpl = PdfReader(input_pdf)
        if not getattr(tpl.Root, "AcroForm", None):
            return False
        for page in tpl.pages:
            ann = getattr(page, "Annots", None) or []
            for a in ann:
                if a.Subtype == PdfName.Widget and a.T:
                    name = a.T.to_unicode().strip("()")
                    val = acro_data.get(name)
                    if val is not None:
                        a.update(PdfDict(V=f"({val})"))
        tpl.Root.AcroForm.update(PdfDict(NeedAppearances=True))
        PdfWriter().write(output_pdf, tpl)
        return True
    except Exception:
        return False

def stamp_pdf_text(input_pdf: str, output_pdf: str, coords_map: Dict[str, Any], values: Dict[str, Any]) -> None:
    import fitz
    doc = fitz.open(input_pdf)
    for k, v in values.items():
        info = coords_map.get(k) or {}
        try:
            page = doc[int(info.get("page", 0))]
            x, y, size = float(info.get("x", 72)), float(info.get("y", 72)), float(info.get("size", 10))
            text = "✓" if isinstance(v, bool) and v else str(v)
            page.insert_text((x, y), text, fontsize=size)
        except Exception:
            continue
    doc.save(output_pdf)
    doc.close()

def save_filled_pdf(meta: Dict[str, Any], answers: Dict[str, Any]) -> Dict[str, Any]:
    from datetime import datetime
    key = (meta.get("form_key") or "form").lower()
    out_dir = DATA_DIR / key
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf_p = resolve_pdf_path(meta, key)
    if not pdf_p:
        raise ValueError("PDF not found")
    input_pdf = str(pdf_p.resolve())
    ts = datetime.now().strftime("%Y%m%d_%H%M")
    output_pdf = str(out_dir / f"{key}_{ts}_{uuid.uuid4().hex[:8]}.pdf")
    
    field_map = meta.get("field_map", {})
    coords_map = meta.get("coords_map", {})
    acro: Dict[str, str] = {}
    for human, val in answers.items():
        if human in field_map and isinstance(val, (str, int, float)):
            acro[field_map[human]] = str(val)
        if isinstance(val, (list, tuple)):
            for opt in val:
                mkey = f"{human}:{opt}"
                if mkey in field_map:
                    acro[field_map[mkey]] = "Yes"
    
    used_acro = fill_pdf_acroform(input_pdf, output_pdf, acro)
    if not used_acro:
        stamp_vals: Dict[str, Any] = {}
        for human, val in answers.items():
            if isinstance(val, (list, tuple)):
                for opt in val:
                    mkey = f"{human}:{opt}"
                    if mkey in coords_map:
                        stamp_vals[mkey] = True
            else:
                if human in coords_map:
                    stamp_vals[human] = val
        stamp_pdf_text(input_pdf, output_pdf, coords_map, stamp_vals)
    
    return {"output_pdf": output_pdf, "used_acroform": used_acro}

# -------------------------
# Prompts (保持不變)
# -------------------------
SYSTEM_PROMPT = (
    "You help users choose and complete official forms. Be neutral and concise. "
    "Ask for clarification when needed. Avoid legal advice."
)

PROMPT_SELECT_FORM = """\
Consider ONLY this catalog (key : title):
{catalog}

User context:
{context}

Return the SINGLE best form key from the catalog.
If you need more info, ask ONE short clarifying question instead of guessing.
"""

PROMPT_SCOPING = """\
Form key: {key}
Metadata JSON:
{meta_json}

PDF text excerpt (optional):
{pdf_text}

Return 3–6 concise scoping questions as a JSON array of strings.
"""

PROMPT_FIELDS = """\
Form key: {key}
Metadata JSON:
{meta_json}

Given the scoping Q&A:
{qa}

Return a JSON array of the field identifiers we must ask the user, in order.
Use identifiers present in metadata (field_order or fields keys).
"""

PROMPT_INLINE_QA = """\
Form key: {key}
Metadata JSON:
{meta_json}
PDF text (optional):
{pdf_text}

User asked:
{user}
Answer concisely based on metadata/text only. If unsure, say what is missing.
"""

def _json_extract(s: str) -> Any:
    s = s.strip()
    s = re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$", "", s, flags=re.I | re.M)
    return json.loads(s)

# -------------------------
# Session + Agent (保持不變)
# -------------------------
@dataclass
class SessionState:
    stage: str = "greet"
    form_key: Optional[str] = None
    case_info: str = ""
    scoping_questions: List[str] = field(default_factory=list)
    scoping_answers: Dict[str, str] = field(default_factory=dict)
    q_index: int = 0
    pending_fields: List[str] = field(default_factory=list)
    f_index: int = 0
    answers: Dict[str, Any] = field(default_factory=dict)
    waiting_for_clarify: Optional[str] = None

class FormsAgent:
    def __init__(self):
        self.s = SessionState()
        self.ready = ready_forms()

    def _meta(self) -> Dict[str, Any]:
        assert self.s.form_key, "form_key not set"
        return load_meta(self.s.form_key)

    def on_user(self, msg: str, history: History) -> str:
        msg = msg.strip()

        if self.s.stage == "greet":
            self.s.stage = "select_form"
            if not self.ready:
                return f"{DISCLAIMER}\n\nI can't find any ready forms. Please add metadata and PDFs under {DATA_DIR}."
            return (
                f"{DISCLAIMER}\n\n"
                f"I can help with these ready forms: {', '.join(sorted(self.ready.keys()))}.\n"
                f"Tell me your situation or type a form key to proceed."
            )

        if self.s.stage == "select_form":
            rf = self.ready
            key = msg.lower()
            if key in rf:
                self.s.form_key = key
                self.s.stage = "confirm_form"
                return f"Suggested form: {key} ({rf[key]}). Confirm? (yes/no)"
            prompt = PROMPT_SELECT_FORM.format(
                catalog="\n".join(f"- {k}: {v}" for k, v in rf.items()),
                context=msg
            )
            reply = llama_chat(SYSTEM_PROMPT, prompt, history)
            choice = reply.strip().lower().split()[0]
            if choice in rf:
                self.s.form_key = choice
                self.s.stage = "confirm_form"
                return f"Suggested form: {choice} ({rf[choice]}). Confirm? (yes/no)"
            return reply

        if self.s.stage == "confirm_form":
            if msg.lower() in ("yes", "y"):
                self.s.stage = "list_fields"
                return self._start_scoping(history)
            else:
                self.s.form_key = None
                self.s.stage = "select_form"
                return "OK, let's try again. Describe your situation."

        if self.s.stage == "list_fields":
            if self.s.q_index < len(self.s.scoping_questions):
                q = self.s.scoping_questions[self.s.q_index]
                self.s.scoping_answers[q] = msg
                self.s.q_index += 1
            if self.s.q_index < len(self.s.scoping_questions):
                return f"Q{self.s.q_index+1}: {self.s.scoping_questions[self.s.q_index]}"
            return self._derive_fields(history)

        if self.s.stage == "fill":
            if "?" in msg:
                m = self._meta()
                pdf_p = resolve_pdf_path(m, self.s.form_key)
                pdf_text = read_pdf_text(pdf_p) if pdf_p else ""
                prompt = PROMPT_INLINE_QA.format(
                    key=self.s.form_key, meta_json=json.dumps(m, indent=2),
                    pdf_text=pdf_text, user=msg
                )
                ans = llama_chat(SYSTEM_PROMPT, prompt, history)
                field = self.s.pending_fields[self.s.f_index]
                return f"{ans}\nNow, what's your {field}?"
            field = self.s.pending_fields[self.s.f_index]
            self._store_answer(field, msg)
            self.s.f_index += 1
            if self.s.f_index < len(self.s.pending_fields):
                nxt = self.s.pending_fields[self.s.f_index]
                return f"Got it. What's your {nxt}?"
            m = self._meta()
            out = save_filled_pdf(m, self.s.answers)
            self.s.stage = "complete"
            return f"All set! **Download your filled form**: {out['output_pdf']}"

        if self.s.stage == "complete":
            if msg.lower() == "restart":
                self.__init__()
                return "Restarted. Tell me your situation or type a form key."
            return "We're finished. Type 'restart' to start over."

        return "I didn't catch that. Please try again."

    def _start_scoping(self, history: History) -> str:
        m = self._meta()
        pdf_p = resolve_pdf_path(m, self.s.form_key)
        pdf_text = read_pdf_text(pdf_p) if pdf_p else ""
        prompt = PROMPT_SCOPING.format(
            key=self.s.form_key, meta_json=json.dumps(m, indent=2), pdf_text=pdf_text
        )
        try:
            qs = _json_extract(llama_chat(SYSTEM_PROMPT, prompt, history))
            self.s.scoping_questions = [str(x).strip() for x in qs if str(x).strip()][:6]
        except Exception:
            self.s.scoping_questions = m.get("scoping_questions", [])[:6]
        self.s.q_index = 0
        self.s.scoping_answers = {}
        if self.s.scoping_questions:
            return f"Q1: {self.s.scoping_questions[0]}"
        return self._derive_fields(history)

    def _derive_fields(self, history: History) -> str:
        m = self._meta()
        qa_text = "\n".join(f"- {q}: {a}" for q, a in self.s.scoping_answers.items())
        fields = []
        try:
            raw = llama_chat(
                SYSTEM_PROMPT,
                PROMPT_FIELDS.format(key=self.s.form_key, meta_json=json.dumps(m, indent=2), qa=qa_text),
                history
            )
            fields = [str(x).strip() for x in _json_extract(raw) if str(x).strip()]
        except Exception:
            pass
        if not fields:
            fields = list(m.get("field_order", []))
        self.s.pending_fields = fields
        self.s.f_index = 0
        self.s.stage = "fill"
        if fields:
            return f"I'll collect {len(fields)} fields. What's your {fields[0]}?"
        return "No fields found in metadata. Please update the meta JSON."

    def _store_answer(self, field: str, raw: str) -> None:
        m = self._meta()
        kind_def = (m.get("fields", {}).get(field) or {})
        kind = (kind_def.get("kind") or "text").lower()
        if kind in ("radio", "select", "choice"):
            opts = [str(o) for o in kind_def.get("options", [])]
            pick = raw.strip()
            if opts and pick not in opts:
                match = next((o for o in opts if o.lower() == pick.lower()), None)
                if match:
                    pick = match
            self.s.answers[field] = pick
            self.s.answers[field + f":{pick}"] = True
        elif kind in ("checkbox", "multi", "multiselect"):
            opts = [str(o) for o in kind_def.get("options", [])]
            picks = [x.strip() for x in raw.split(",") if x.strip()]
            normed = []
            for p in picks:
                match = next((o for o in opts if o.lower() == p.lower()), p)
                normed.append(match)
                self.s.answers[field + f":{match}"] = True
            self.s.answers[field] = normed
        elif kind == "date":
            self.s.answers[field] = raw.strip()
        else:
            self.s.answers[field] = raw.strip()

def chat_with_agent(user_message: str, history: Optional[History] = None, agent: Optional[FormsAgent] = None):
    if agent is None:
        agent = FormsAgent()
    if history is None:
        history = []
    reply = agent.on_user(user_message, history)
    history.append(("user", user_message))
    history.append(("assistant", reply))
    return reply, history, agent