import sys
import os
import json
import asyncio
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from frontend.app import run_search, make_loading_fn, make_translate_fn, DummyRequest
from backend.database import init_db

init_db()

res_search = run_search("attention is all you need", "指定なし", "関連度順 (Relevance)")
state_results = res_search[0] # state_search_results is the 1st element!

print("RESULTS:", len(state_results))

# Test loading fn
load_fn = make_loading_fn(0)
res_load = load_fn(state_results)
print("LOADING FN RETURN LENGTH:", len(res_load))
print("LOADING FN RETURNS:", res_load)

# Test translate fn
trans_fn = make_translate_fn(0)
res_trans = trans_fn(state_results)
print("TRANSLATE FN RETURN LENGTH:", len(res_trans))
print("TRANSLATE FN RETURNS:")
for i, r in enumerate(res_trans):
    print(f"[{i}] type:", type(r))
    if isinstance(r, dict):
        print(f"[{i}] keys:", r.keys())
    if hasattr(r, '__class__'):
        print(f"[{i}] class:", r.__class__)
    print(f"[{i}] value (truncated):", str(r)[:200])

