import os
import requests
import fitz  # PyMuPDF
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from serpapi import GoogleSearch
from google import genai
from dotenv import load_dotenv
from services.arxiv_service import fetch_arxiv_papers
from services.semantic_scholar_service import fetch_semantic_scholar_metadata, determine_badges
from utils.date_utils import normalize_date
import asyncio
import json

load_dotenv()

app = FastAPI(title="Scholar AI Translator API")

SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class SearchRequest(BaseModel):
    query: str
    time_filter: Optional[str] = None # Deprecated, keeping for backwards compatibility
    start_year: Optional[str] = None # YYYY
    end_year: Optional[str] = None # YYYY
    sort_by: Optional[str] = "relevance" # "relevance", "newest", "oldest"

class TranslateRequest(BaseModel):
    pdf_url: Optional[str] = None
    title: Optional[str] = None
    snippet: Optional[str] = None
    mode: str 

class QARequest(BaseModel):
    question: str
    context: str
    history: List[Dict[str, str]] = []

@app.get("/")
def read_root():
    return {"message": "Welcome to Scholar AI Translator API"}

@app.post("/search")
async def search_papers(request: SearchRequest):
    if not SERPAPI_API_KEY or SERPAPI_API_KEY.startswith("your_"):
         raise HTTPException(status_code=500, detail="SERPAPI_API_KEY is not configured correctly.")
         
    params = {
      "engine": "google_scholar",
      "q": request.query,
      "api_key": SERPAPI_API_KEY,
      "num": 5  # fetch top 5
    }

    # Add time filtering to Google Scholar
    if request.time_filter == "past_7_days":
        params["as_ylo"] = 2024 # Needs a better dynamic year
        # Better Serper approach for time: "q=...+&as_ylo=..." but it's tricky. Let's just pass basic query
        
    papers = []
    
    # 1. Fetch from arXiv (Computer Science prioritized)
    print(f"Fetching arXiv papers for: {request.query} from {request.start_year} to {request.end_year}")
    arxiv_papers = fetch_arxiv_papers(request.query, start_year=request.start_year, end_year=request.end_year, max_results=5)
    
    # Enrich arXiv papers with Semantic Scholar metadata (in parallel ideally, but simple for now)
    for p in arxiv_papers:
         meta = await fetch_semantic_scholar_metadata(p["arxiv_id"])
         venue = meta.get("venue", "")
         citation_count = meta.get("citationCount", 0)
         
         p["badges"] = determine_badges(venue, p["title"], p["snippet"])
         if citation_count > 0:
             p["citation_count"] = citation_count
         
         # Fallback published_date if arXiv missed it but SS has the year
         target_date = meta.get("year") or meta.get("publicationDate")
         if target_date:
             p["published_date"] = normalize_date(target_date, debug_source="Semantic Scholar API")
         
         papers.append(p)
         
    # 2. Fetch from Google Scholar via SerpApi
    try:
        print(f"Fetching Google Scholar papers via SerpApi...")
        search = GoogleSearch(params)
        results = search.get_dict()
        organic_results = results.get("organic_results", [])
        
        for i, res in enumerate(organic_results):
            # Try to get PDF link if available
            resources = res.get("resources", [])
            pdf_url = None
            for resource in resources:
                if resource.get("file_format") == "PDF":
                    pdf_url = resource.get("link")
                    break
            
            p = {
                "id": f"scholar_{i}",
                "title": res.get("title"),
                "link": res.get("link"),
                "authors": res.get("publication_info", {}).get("summary", "Unknown Authors"),
                "pdf_url": pdf_url, 
                "snippet": res.get("snippet", ""),
                "source": "Google Scholar",
                "badges": determine_badges("", res.get("title") or "", res.get("snippet") or "")
            }
            
            # Attempt to extract year from Google Scholar publication info if available
            pub_info = res.get("publication_info", {}).get("summary", "")
            snippet = res.get("snippet", "")
            date_hint = pub_info + " " + snippet
            p["published_date"] = normalize_date(date_hint, debug_source="Google Scholar Snippet")
                 
            papers.append(p)

    except Exception as e:
        import traceback
        print(f"ERROR in Google Scholar /search: {e}")
        traceback.print_exc()
        
    # Filter in-memory for Google Scholar (and as fallback for arXiv)
    if request.start_year and request.end_year:
        filtered_papers = []
        for p in papers:
            p_year_str = p.get("published_date")
            if not p_year_str:
                continue
            
            # Compare YYYY strings (works lexicographically)
            if request.start_year <= p_year_str <= request.end_year:
                filtered_papers.append(p)
        papers = filtered_papers

    # Sort papers
    if request.sort_by == "newest":
        papers.sort(key=lambda x: x.get("published_date") or "0000", reverse=True)
    elif request.sort_by == "oldest":
        papers.sort(key=lambda x: x.get("published_date") or "9999")
        
    return {
        "status": "success",
        "query": request.query,
        "results": papers
    }

@app.post("/translate")
def translate_paper(request: TranslateRequest):
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured correctly.")
        
    if not request.pdf_url and not request.snippet:
        raise HTTPException(status_code=400, detail="PDF URL or Snippet is required")

    # 1. Download PDF (Best effort)
    text = ""
    download_success = False
    
    if request.pdf_url and not request.pdf_url.startswith("NO_PDF_URL"):
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
                "Accept": "application/pdf"
            }
            response = requests.get(request.pdf_url, headers=headers, timeout=10)
            
            # Check if response is actually a PDF
            content_type = response.headers.get("Content-Type", "").lower()
            if response.status_code == 200 and "application/pdf" in content_type:
                pdf_bytes = response.content
                # Extract Text with PyMuPDF
                doc = fitz.open(stream=pdf_bytes, filetype="pdf")
                for page in doc[:3]:  # Read first 3 pages
                    text += page.get_text()
                if text.strip():
                    download_success = True
        except Exception as e:
            print(f"PDF Parsing Failed: {e}")
            pass

    # 2. Fallback if PDF fetch/extraction failed
    if not download_success:
        title = request.title or "Unknown Title"
        snippet = request.snippet or "No abstract/snippet provided."
        url = request.pdf_url or "No URL provided."
        text = f"Title: {title}\nURL: {url}\nAbstract/Snippet: {snippet}\n\n(Note: The original PDF could not be directly downloaded due to publisher restrictions or non-PDF format. Please base the summary and translation on the provided title and abstract/snippet metadata, which describe a research paper. Provide a comprehensive overview of what this paper discusses based on these metadata.)"


    # 3. Prompt setup
    prompts = {
        "研究用 (詳細な翻訳と考察)": "あなたはシニア研究者です。以下の論文の抜粋を読み、研究目的（背景、提案手法、実験結果、貢献）を詳細に日本語で翻訳・要約し、専門的な視点からの深い考察を加えてください。\n\n",
        "レポート用 (要点と構成の整理)": "あなたは優秀なアシスタントです。以下の論文の抜粋を読み、学生がレポートにまとめやすいように、①背景と目的、②提案手法、③実験と結果の3項目で見出しをつけて、分かりやすい日本語で要約してください。\n\n",
        "速読用 (TL;DR・ハイライト)": "忙しい専門家向けに、以下の論文の最も重要なポイント（TL;DR）を3つの箇条書きで日本語で簡潔にまとめてください。\n\n",
    }
    
    system_instruction = prompts.get(request.mode, "以下の論文を日本語で要約してください。\n\n")
    
    system_instruction += """
さらに、論文内で使われている「専門用語（キーワード）」を抽出し、それらの簡単な説明文を付与してください。
用語は分野（物理、数学、情報、電子工学など）ごとに分類してください。

【重要】
抽出した用語名が日本語ではない場合（英語などの場合）は、必ずその横に「(訳: 〇〇)」という形式で日本語訳を付与してください。
例: 
- Attention mechanism (訳: 注意機構)
- Latent Space (訳: 潜在空間)
※ 元から日本語の用語の場合は、単に日本語の用語名のみを出力し、「(訳: )」などを付与しないでください（例: "用語名"）。

出力は必ず以下のJSONフォーマットのみで行ってください（Markdownブロック ```json などは含めないでください）：
{
  "translation": "<翻訳・要約テキスト（Markdownの改行を含む）>",
  "glossary": [
    {
      "category": "分野名（例：情報）",
      "terms": [
        {"term": "用語名 (訳: 日本語訳)", "explanation": "用語の簡潔な説明"}
      ]
    }
  ]
}
"""

    # 4. Gemini API Call
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=system_instruction + "\n\n---\n" + text,
            config={
                "response_mime_type": "application/json"
            }
        )
        
        try:
            # Parse json from gemini
            data = json.loads(response.text)
            translation = data.get("translation", "翻訳データが見つかりませんでした。")
            glossary = data.get("glossary", [])
        except Exception as parse_e:
            translation = response.text
            glossary = []
            
        return {
            "status": "success",
            "pdf_url": request.pdf_url,
            "mode": request.mode,
            "translation": translation,
            "glossary": glossary
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {e}")

@app.post("/qa")
def qa_paper(request: QARequest):
    if not GEMINI_API_KEY or GEMINI_API_KEY.startswith("your_"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured correctly.")
        
    system_instruction = "あなたは論文の内容について答えるAIアシスタントです。以下の「現在参照している論文の要約・文脈」を踏まえてユーザーの質問に日本語で簡潔に答えてください。\n\n"
    system_instruction += f"[現在参照している論文の要約・文脈]\n{request.context[:3000]}\n\n"  # truncate if too long
    
    # Build prompt with history
    prompt = system_instruction
    if request.history:
        prompt += "[過去のやり取り]\n"
        # Only take last few messages to save context length if needed
        for msg in request.history[-5:]:
            role = "ユーザー" if msg.get("role") == "user" else "アシスタント"
            prompt += f"{role}: {msg.get('content')}\n"
        prompt += "\n"
        
    prompt += f"[新しい質問]\nユーザー: {request.question}\nアシスタント:"
    
    try:
        client = genai.Client(api_key=GEMINI_API_KEY)
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        return {
            "status": "success",
            "answer": response.text
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
