from typing import List, Dict, Optional
from dataclasses import dataclass
import re

try:
    from PIL import Image
    import pytesseract
    OCR_AVAILABLE = True
except Exception:
    OCR_AVAILABLE = False

@dataclass
class MedItem:
    nom: str
    frequence: str  # ex: "1/jour", "2/jour", "1/semaine"

FREQ_PATTERNS = [
    (r"\b(\d+)\s*/\s*jour\b", "{}/jour"),
    (r"\b(\d+)\s*/\s*semaine\b", "{}/semaine"),
    (r"\b(\d+)\s*/\s*sem\b", "{}/semaine"),
    (r"\b(\d+)\s*x\s*par\s*jour\b", "{}/jour"),
    (r"\b(\d+)\s*fois\s*par\s*jour\b", "{}/jour"),
    (r"\bquotidien(ne)?\b", "1/jour"),
]

def _parse_meds_from_text(text: str) -> List[MedItem]:
    """
    Extraction par regex : lignes du type
    - "Paracétamol 1/jour"
    - "Ibuprofène 2/jour"
    - "Amoxicilline 3 x par jour"
    """
    meds: List[MedItem] = []
    # découpe en lignes, on ignore les trop courtes
    for raw in [l.strip() for l in text.splitlines() if len(l.strip()) > 2]:
        # heuristique : nom = début de ligne jusqu’à fréquence
        freq: Optional[str] = None
        for pat, fmt in FREQ_PATTERNS:
            m = re.search(pat, raw, flags=re.IGNORECASE)
            if m:
                if m.groups() and m.group(1) and "{}" in fmt:
                    freq = fmt.format(m.group(1))
                else:
                    freq = fmt
                break
        if not freq:
            # autre pattern type "1 / jour ?" 
            m = re.search(r"(\d+)\s*/\s*jour", raw, flags=re.IGNORECASE)
            if m:
                freq = f"{m.group(1)}/jour"

        # nom = texte avant la fréquence trouvée sinon la ligne entière
        if freq:
            # coupe la ligne au début du match
            cut = re.split(r"(\d+\s*/\s*jour|\d+\s*/\s*semaine|\d+\s*x\s*par\s*jour|\d+\s*fois\s*par\s*jour|quotidien(ne)?)",
                           raw, flags=re.IGNORECASE)[0].strip(" -•:\t")
            nom = re.sub(r"^\d+[\.\)-]\s*", "", cut)  # supprime "1) " ou "1. " en début
        else:
            # si pas de fréquence détectée, on saute
            continue

        # nettoyage nom (retire symboles trop communs)
        nom = re.sub(r"[\?\!]+$", "", nom).strip()
        if len(nom) < 2:
            continue

        meds.append(MedItem(nom=nom, frequence=freq))
    return meds

def extract_text_from_image(image_bytes: bytes) -> str:
    if not OCR_AVAILABLE:
        return ""
    from io import BytesIO
    img = Image.open(BytesIO(image_bytes))
    txt = pytesseract.image_to_string(img, lang="fra")
    return txt

def extract_meds(image_bytes: Optional[bytes], typed_text: Optional[str] = None) -> List[Dict]:
    """
    - Si image fournie et OCR dispo, on OCRise puis on parse
    - Sinon, on parse ce qui est envoyé en texte (ex: OCR côté mobile)
    Retour: liste de dict [{"nom": "...", "frequence": "1/jour"}, ...]
    """
    text = ""
    if image_bytes and OCR_AVAILABLE:
        text = extract_text_from_image(image_bytes)
    if not text and typed_text:
        text = typed_text

    if not text:
        return []

    meds = _parse_meds_from_text(text)
    return [ {"nom": m.nom, "frequence": m.frequence, "dose": m.dose} for m in meds ]
