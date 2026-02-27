import asyncio
import os
import sys
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))
from database import init_db
from main import translate_paper, TranslateRequest
from frontend.app import DummyRequest, parse_translation_result

init_db()

req = TranslateRequest(
    pdf_url="NO_PDF_URL",
    title="Attention Is All You Need",
    snippet="The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely.",
    published_date="2017",
    source="arXiv",
    mode="研究用 (詳細な翻訳と考察)"
)

paper = {
    "title": "Attention Is All You Need",
    "pdf_url": "NO_PDF_URL",
    "snippet": "The dominant sequence transduction models...",
    "published_date": "2017",
    "source": "arXiv"
}

print("Running translate_paper...")
try:
    data_dict = translate_paper(req, req=DummyRequest())
    if hasattr(data_dict, "dict"): data_dict = data_dict.dict()
    elif isinstance(data_dict, str): data_dict = json.loads(data_dict)
    
    res = data_dict.get("translation")
    print("\n[TRANSLATION RESULT (RAW)]")
    print(res)

    md, glossary_html = parse_translation_result(res, paper)
    print("\n[MD HTML OUTPUT]")
    print(md)

    print("\n[GLOSSARY HTML OUTPUT]")
    print(glossary_html)

except Exception as e:
    import traceback
    traceback.print_exc()
    print("FAILED:", e)
