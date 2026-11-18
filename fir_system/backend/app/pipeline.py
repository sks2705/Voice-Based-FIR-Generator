"""
app/pipeline.py
Full NLP pipeline:
  audio file  →  Whisper  →  Flan-T5  →  spaCy  →  FIR dict
"""

import re
import datetime


# ── Step 1: Transcribe ────────────────────────────────────────────────────────

def transcribe(whisper_model, audio_path: str) -> tuple[str, str]:
    result = whisper_model.transcribe(
        audio_path,
        task="transcribe",
        temperature=0.0,
        beam_size=5,
        best_of=5,
    )
    return result.get("text", "").strip(), result.get("language", "unknown")


# ── Step 2: Normalise ─────────────────────────────────────────────────────────

def normalize(llm, raw_text: str) -> str:
    prompt = (
        "Convert the following mixed-language speech into clear, correct English. "
        "Fix grammar, remove repetition, and keep all important details.\n\n"
        f"Text:\n{raw_text}"
    )
    out   = llm(prompt, max_length=512, do_sample=False)
    clean = out[0]["generated_text"].strip()
    return clean if len(clean) > 30 else raw_text


# ── Step 3: Extract entities ──────────────────────────────────────────────────

def extract(nlp, text: str) -> dict:
    doc        = nlp(text)
    text_lower = text.lower()

    # Name
    name = None
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            name = ent.text.strip().title()
            break
    if not name:
        m = re.search(r"my name is ([a-zA-Z\s]{2,30}?)(?: and| i |,|\.|$)", text_lower)
        if m:
            name = m.group(1).strip().title()

    # Date
    date = None
    if "today" in text_lower or "tonight" in text_lower:
        date = str(datetime.date.today())
    elif "yesterday" in text_lower:
        date = str(datetime.date.today() - datetime.timedelta(days=1))
    if not date:
        for ent in doc.ents:
            if ent.label_ == "DATE":
                date = ent.text.strip(); break

    # Time
    time_val = None
    tm = re.search(r"\b\d{1,2}[:.]?\d{0,2}\s?(am|pm)\b", text_lower)
    if tm:
        time_val = tm.group().replace(".", ":").strip()
    if not time_val:
        for ent in doc.ents:
            if ent.label_ == "TIME":
                time_val = ent.text.strip(); break

    # Location
    locs = []
    for ent in doc.ents:
        if ent.label_ in ("GPE", "LOC", "FAC"):
            locs.append(ent.text.strip())
    lm = re.search(r"near ([a-zA-Z0-9\s]{2,40}?)(?: around| at| on|\.|,|$)", text_lower)
    if lm:
        locs.append(lm.group(1).strip().title())
    seen, clean_locs = set(), []
    for l in locs:
        if l.lower() not in seen:
            seen.add(l.lower()); clean_locs.append(l)
    location = ", ".join(clean_locs) if clean_locs else None
    if location:
        location = re.sub(r"\bin noise\b", "", location, flags=re.I)
        location = re.sub(r"\baround \d+.*", "", location, flags=re.I)
        location = location.strip(", ").strip()

    # Incident type
    if any(k in text_lower for k in ("stolen","theft","robbed","snatched","snatch")):
        itype = "theft"
    elif any(k in text_lower for k in ("accident","crash","hit and run","hit-and-run")):
        itype = "accident"
    elif any(k in text_lower for k in ("attack","assault","beaten","stabbed","molested")):
        itype = "assault"
    elif any(k in text_lower for k in ("murder","killed","dead body")):
        itype = "murder"
    elif any(k in text_lower for k in ("fraud","cheated","scam","fake")):
        itype = "fraud"
    elif any(k in text_lower for k in ("harassment","harassed","stalking")):
        itype = "harassment"
    else:
        itype = "unknown"

    # Objects stolen
    kws = ["phone","mobile","wallet","bag","laptop","jewellery","jewelry",
           "cash","money","watch","purse","car","bike","gold","chain",
           "passport","documents"]
    objects = sorted({w for w in kws if w in text_lower})
    for b in re.findall(
        r"\b(samsung[\s\w]*?s\d+|iphone[\s\d]+|redmi[\s\w]*?|oneplus[\s\w]*?)\b",
        text_lower
    ):
        obj = b.strip().title()
        if obj.lower() not in [o.lower() for o in objects]:
            objects.append(obj)

    # Suspect
    suspect_info = None
    sm = re.search(
        r"(one|two|three|four|\d+)?\s?(men|man|boys|boy|persons?|individuals?|males?)"
        r".*?(bike|motorcycle|scooter|car|van|auto)?",
        text_lower,
    )
    if sm:
        suspect_info = sm.group().strip()

    # Evidence
    evidence = []
    for kw, lbl in [("cctv","CCTV footage"),("camera","Camera footage"),
                    ("witness","Witness statement"),("photo","Photograph"),
                    ("video","Video recording"),("receipt","Receipt/document")]:
        if kw in text_lower:
            evidence.append(lbl)

    return {
        "name": name, "incident_type": itype,
        "date": date, "time": time_val, "location": location,
        "description": text.strip(), "suspect_info": suspect_info,
        "objects_stolen": objects, "evidence": evidence,
    }


# ── Step 4: Run full pipeline ─────────────────────────────────────────────────

def run(ml: dict, audio_path: str) -> dict:
    raw_text, _lang = transcribe(ml["whisper"], audio_path)
    clean_text      = normalize(ml["llm"], raw_text)
    entities        = extract(ml["nlp"], clean_text)
    now             = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return {
        "complainant": {
            "name":    entities.get("name") or "",
            "phone":   "",
            "address": "",
        },
        "incident": {
            "type":        entities.get("incident_type") or "",
            "date":        entities.get("date") or "",
            "time":        entities.get("time") or "",
            "location":    entities.get("location") or "",
            "description": entities.get("description") or "",
        },
        "suspect":        {"info": entities.get("suspect_info") or ""},
        "evidence":        entities.get("evidence") or [],
        "objects_stolen":  entities.get("objects_stolen") or [],
        "metadata":        {"reported_at": now, "status": "pending"},
    }
