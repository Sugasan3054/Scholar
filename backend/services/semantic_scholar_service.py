import httpx
from typing import Dict, Any, List

SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper"

TOP_CONFERENCES = {
    "CVPR", "ICCV", "ECCV", "NeurIPS", "NIPS", "ICML", "ICLR", 
    "AAAI", "IJCAI", "ACL", "EMNLP", "NAACL", "KDD", "WWW", "SIGIR", "CHI", 
    "SIGCOMM", "NSDI", "OSDI", "SOSP", "CCS", "USENIX", "ISCA", "MICRO", "PLDI", "POPL"
}

TRENDING_KEYWORDS = {
    "llm": "LLM", 
    "large language model": "LLM",
    "diffusion": "Diffusion",
    "transformer": "Transformer",
    "rag": "RAG",
    "retrieval-augmented": "RAG",
    "agent": "Agent",
    "rlhf": "RLHF",
    "lora": "LoRA",
    "generative ai": "GenAI"
}

async def fetch_semantic_scholar_metadata(arxiv_id: str) -> Dict[str, Any]:
    """
    Given an arXiv ID, fetch metadata from Semantic Scholar including venue and citation count.
    """
    if not arxiv_id:
        return {}
        
    # Semantic Scholar supports querying by ArXiv ID prefix
    query_id = f"ARXIV:{arxiv_id}"
    
    # We want venue (to check top conference), citationCount, year, and publicationDate
    params = {
        "fields": "venue,citationCount,year,publicationDate"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{SEMANTIC_SCHOLAR_URL}/{query_id}", params=params, timeout=5.0)
            if response.status_code == 200:
                return response.json()
            return {}
    except Exception as e:
        print(f"Error fetching Semantic Scholar metadata for {arxiv_id}: {e}")
        return {}

def determine_badges(venue: str, title: str, snippet: str) -> List[str]:
    """
    Determine if a paper gets a 'Top Conference' badge or specific trend tags.
    """
    badges = []
    
    # 1. Top Conference Badge
    if venue:
        venue_upper = venue.upper()
        # Direct match or substring match for well known acronyms
        for conf in TOP_CONFERENCES:
            if conf in venue_upper:
                badges.append(f"Top Conf ({conf})")
                break
                
    # 2. Trend Tags (Auto-tagging based on title/snippet)
    text_to_check = f"{title} {snippet}".lower()
    for keyword, tag in TRENDING_KEYWORDS.items():
        if keyword in text_to_check and tag not in badges:
             badges.append(tag)
             
    # Limit number of badges to keep UI clean
    return badges[:3]
