import arxiv
from datetime import datetime, timezone
from utils.date_utils import normalize_date

def fetch_arxiv_papers(query: str, start_year: str = None, end_year: str = None, max_results: int = 5):
    """
    Fetches papers from arXiv based on a query.
    Prioritizes Computer Science category ('cat:cs.*') and sorts by date descending.
    start_year and end_year should be in YYYY format.
    """
    
    # Enhance query to prioritize Computer Science if the query doesn't already specify a category
    if "cat:" not in query:
       modified_query = f"({query}) AND cat:cs.*"
    else:
        modified_query = query
        
    if start_year and end_year:
        # arXiv date format in query: submittedDate:[YYYYMMDD* TO YYYYMMDD*]
        start_str = f"{start_year}0101"
        end_str = f"{end_year}1231"
        modified_query += f" AND submittedDate:[{start_str}* TO {end_str}*]"
        
    client = arxiv.Client()
    
    search = arxiv.Search(
        query=modified_query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending,
    )

    papers = []
    try:
        results = client.results(search)
        for i, r in enumerate(results):
            # Parse dates using explicit normalizer and prioritize last modified
            published_date = normalize_date(r.updated) if r.updated else normalize_date(r.published)
            
            papers.append({
                "id": f"arxiv_{i}_{r.get_short_id()}",
                "title": r.title,
                "link": r.entry_id,
                "pdf_url": r.pdf_url,
                "authors": ", ".join([author.name for author in r.authors]),
                "snippet": r.summary.replace('\n', ' ')[:300] + "...", 
                "source": "arXiv",
                "published_date": published_date,
                "arxiv_id": r.get_short_id()
            })
    except Exception as e:
        print(f"Error fetching from arXiv: {e}")

    return papers
