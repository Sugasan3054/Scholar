import re
from datetime import datetime, timedelta, date
try:
    from dateutil import parser
except ImportError:
    # Fallback if not installed yet
    parser = None

def normalize_date(date_input, debug_source: str = "Unknown") -> str | None:
    """
    Takes an input (string, datetime, etc.) and tries to parse it into YYYY.
    Returns None if the format is unrecognizable or no year is found.
    Logs the extraction process.
    """
    if not date_input:
        return None
        
    print(f"[Date Debug - {debug_source}] Raw input: {date_input}")
        
    if isinstance(date_input, (date, datetime)):
        result = date_input.strftime('%Y')
        print(f"[Date Debug - {debug_source}] Datetime object parsed to: {result}")
        return result
        
    date_str = str(date_input).strip()
    
    # 1. Relative formats like "3 years ago"
    ago_match = re.search(r'(\d+)\s+(day|hour|minute|week|month|year)s?\s+ago', date_str.lower())
    if ago_match:
        val = int(ago_match.group(1))
        unit = ago_match.group(2)
        today = date.today()
        if unit == 'day':
            result = (today - timedelta(days=val)).strftime('%Y')
        elif unit == 'week':
            result = (today - timedelta(days=val*7)).strftime('%Y')
        elif unit == 'month':
            result = (today - timedelta(days=val*30)).strftime('%Y')
        elif unit == 'year':
            result = (today - timedelta(days=val*365)).strftime('%Y')
        else:
            result = today.strftime('%Y') # hour/minute
        print(f"[Date Debug - {debug_source}] Relative date parsed to year: {result}")
        return result

    # 2. Basic year extraction using regex (this is the most robust for just getting YYYY)
    year_match = re.search(r'\b(19|20)\d{2}\b', date_str)
    if year_match:
        year_str = year_match.group(0)
        # Verify it's not a future year like 2099 (unless meant to be)
        current_year = date.today().year
        if int(year_str) <= current_year + 1: # allow slight future dates
            print(f"[Date Debug - {debug_source}] Found year via regex: {year_str}")
            return year_str

    print(f"[Date Debug - {debug_source}] Failed to extract any year. Rejecting.")
    return None
