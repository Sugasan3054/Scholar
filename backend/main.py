import os
import requests
import fitz  # PyMuPDF
from typing import Optional, List, Dict
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from serpapi import GoogleSearch
from google import genai
from services.arxiv_service import fetch_arxiv_papers
from services.semantic_scholar_service import fetch_semantic_scholar_metadata, determine_badges
from utils.date_utils import normalize_date
from utils.prompt_manager import PromptManager
import asyncio
import json
import hashlib
from database import init_db, get_paper, save_paper, get_all_papers, update_chat_history, check_rate_limit
from config import config

app = FastAPI(title="Scholar AI Translator API")

# --------- CORS Configuration ---------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# --------------------------------------

@app.on_event("startup")
def startup_event():
    init_db()

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
    published_date: Optional[str] = None
    source: Optional[str] = None
    mode: str 

class QARequest(BaseModel):
    question: str
    context: str
    history: List[Dict[str, str]] = []

class QAChatUpdateRequest(BaseModel):
    paper_id: str
    chat_history: list

@app.get("/")
def read_root():
    return {"message": "Welcome to Scholar AI Translator API"}

@app.post("/search")
async def search_papers(request: SearchRequest):
    if not config.SERPAPI_API_KEY or config.SERPAPI_API_KEY.startswith("your_"):
         raise HTTPException(status_code=500, detail="SERPAPI_API_KEY is not configured correctly.")
         
    params = {
      "engine": "google_scholar",
      "q": request.query,
      "api_key": config.SERPAPI_API_KEY,
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
def translate_paper(request: TranslateRequest, req: Request):
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.startswith("your_"):
        raise HTTPException(status_code=500, detail="GEMINI_API_KEY is not configured correctly.")
        
    if not request.pdf_url and not request.snippet:
        raise HTTPException(status_code=400, detail="PDF URL or Snippet is required")

    # 1. Check DB Cache
    title_str = request.title or "Unknown Title"
    url_str = request.pdf_url or "No URL provided."
    paper_id_str = f"{title_str}_{url_str}"
    paper_id = hashlib.md5(paper_id_str.encode('utf-8')).hexdigest()
    
    cached = get_paper(paper_id)
    if cached:
        try:
            translation = json.loads(cached['summary_json'])
            chat_hist = []
            if cached.get('chat_history'):
                chat_hist = json.loads(cached['chat_history'])
                
            return {
                "status": "success",
                "pdf_url": request.pdf_url,
                "mode": request.mode,
                "translation": translation,
                "glossary": translation.get("glossary", []),
                "paper_id": paper_id,
                "chat_history": chat_hist
            }
        except Exception as e:
            print(f"Cache parse error: {e}")

    client_ip = req.client.host if req.client else "unknown_ip"
    
    # 2. Rate Limit check before invoking expensive Gemini API
    if not check_rate_limit(user_id=client_ip, action="translate", limit=5):
        raise HTTPException(status_code=429, detail="本日の翻訳利用上限(5回)に達しました。明日またご利用ください。")

    # 3. Download PDF (Best effort)
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
    paper_meta = {
        "published_date": request.published_date,
        "source": request.source
    }
    system_instruction = PromptManager.get_prompt(paper_metadata=paper_meta)

    # 4. Gemini API Call
    try:
        client = genai.Client(api_key=config.GEMINI_API_KEY)
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
            translation = data
            glossary = data.get("glossary", [])
            
            # Save to DB
            save_paper(
                paper_id=paper_id,
                title_jp=data.get('title_jp', title_str),
                title_en=data.get('title_en', title_str),
                published_date=request.published_date or "YYYY/MM/DD",
                source_url=request.pdf_url or "Unknown",
                summary_json=translation,
                user_id=client_ip
            )
        except Exception as parse_e:
            translation = {"error": "JSON解析エラー", "raw": response.text}
            glossary = []
            
        return {
            "status": "success",
            "pdf_url": request.pdf_url,
            "mode": request.mode,
            "translation": translation,
            "glossary": glossary,
            "paper_id": paper_id,
            "chat_history": []
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Gemini API Error: {e}")

@app.post("/qa")
def qa_paper(request: QARequest):
    if not config.GEMINI_API_KEY or config.GEMINI_API_KEY.startswith("your_"):
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
        client = genai.Client(api_key=config.GEMINI_API_KEY)
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

@app.post("/update_chat")
def update_chat(request: QAChatUpdateRequest):
    try:
        update_chat_history(request.paper_id, request.chat_history)
        return {"status": "success"}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/history")
def get_history(req: Request):
    client_ip = req.client.host if req.client else "unknown_ip"
    papers = get_all_papers(user_id=client_ip)
    return {
        "status": "success",
        "history": papers
    }
