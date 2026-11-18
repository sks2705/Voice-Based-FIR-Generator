import warnings
warnings.filterwarnings("ignore")

import whisper
import spacy
import torch
from transformers import pipeline, AutoModelForSeq2SeqLM, AutoTokenizer

_store: dict = {}

def load_all():
    # 1. Load Whisper
    print("[ML] Loading Whisper (base) ...")
    _store["whisper"] = whisper.load_model("base")

    # 2. Load Flan-T5 (Manual Loading to bypass KeyError)
    print("[ML] Loading Flan-T5 ...")
    model_id = "google/flan-t5-base"
    
    # Manually load components
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    model = AutoModelForSeq2SeqLM.from_pretrained(model_id)
    
    device = 0 if torch.cuda.is_available() else -1
    
    # Pass the pre-loaded model/tokenizer to the pipeline
    _store["llm"] = pipeline(
        "text2text-generation", 
        model=model, 
        tokenizer=tokenizer, 
        device=device
    )

    # 3. Load spaCy
    print("[ML] Loading spaCy ...")
    try:
        _store["nlp"] = spacy.load("en_core_web_sm")
    except Exception:
        import spacy.cli
        spacy.cli.download("en_core_web_sm")
        _store["nlp"] = spacy.load("en_core_web_sm")

    print("[ML] All models ready.\n")

def get() -> dict:
    return _store