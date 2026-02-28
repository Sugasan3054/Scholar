import gradio as gr
import os
import sys
import json
import asyncio
from datetime import datetime, timedelta, date

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend')))

from database import init_db
from main import (
    search_papers, 
    translate_paper, 
    qa_paper, 
    get_history, 
    update_chat,
    SearchRequest, 
    TranslateRequest, 
    QARequest, 
    QAChatUpdateRequest
)

# SQLite database table configuration hook for local standalone runs
init_db()

class DummyRequest:
    @property
    def client(self):
        class DummyClient:
            host = "127.0.0.1"
        return DummyClient()

MAX_RESULTS = 20

CSS = """
body, .gradio-container {
    font-family: 'Inter', sans-serif !important;
    background-color: #F8FAFC !important;
}

footer {display: none !important;}

.brand-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 24px;
    padding-top: 1rem;
    padding-bottom: 1rem;
    border-bottom: 1px solid #E2E8F0;
}
.brand-icon {
    background: #0F172A;
    color: white;
    width: 32px;
    height: 32px;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 18px;
    font-weight: 700;
}
.brand-title {
    font-size: 20px;
    font-weight: 600;
    color: #0F172A;
    margin: 0;
    letter-spacing: -0.01em;
}

.tldr-box {
    background-color: #F0F9FF; 
    border-left: 4px solid #0EA5E9; 
    padding: 20px 24px; 
    border-radius: 4px; 
    margin-bottom: 28px; 
    color: #0F172A;
}

.section-header-en {
    color: #64748B;
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin: 0 0 12px 0;
    padding-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
}

.snippet-pane {
    background-color: #FFFFFF;
    border: 1px solid #E2E8F0;
    padding: 20px;
    border-radius: 6px;
    color: #334155;
    font-size: 14px;
    line-height: 1.6;
    margin-top: 12px;
    margin-bottom: 24px;
}
.translation-overlay {
    background: #FFFFFF !important;
    border-radius: 12px !important;
    padding: 24px !important;
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04) !important;
    border: 1px solid #E2E8F0 !important;
    margin-top: 16px !important;
}

/* Tooltip Styles */
.tooltip {
    position: relative;
    display: inline-block;
    border-bottom: 2px dotted #2563EB;
    color: #2563EB;
    cursor: help;
    font-weight: 600;
}
.tooltip::after {
    content: attr(data-tooltip);
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background-color: #1E293B;
    color: white;
    padding: 8px 12px;
    border-radius: 6px;
    font-size: 13px;
    font-weight: 500;
    white-space: normal;
    width: max-content;
    max-width: 250px;
    z-index: 1000;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.2s, visibility 0.2s;
    line-height: 1.4;
}
.tooltip::before {
    content: '';
    position: absolute;
    bottom: 115%;
    left: 50%;
    transform: translateX(-50%);
    border-width: 6px;
    border-style: solid;
    border-color: #1E293B transparent transparent transparent;
    z-index: 1000;
    opacity: 0;
    visibility: hidden;
    transition: opacity 0.2s, visibility 0.2s;
}
.tooltip:hover::after,
.tooltip:hover::before {
    opacity: 1;
    visibility: visible;
}

/* Spinner Styles */
.spinner {
    border: 4px solid rgba(0, 0, 0, 0.1);
    width: 36px;
    height: 36px;
    border-radius: 50%;
    border-left-color: #2563EB;
    animation: spin 1s linear infinite;
    display: inline-block;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

.original-btn {
    display: inline-block;
    margin: 20px 0 0 0;
    padding: 8px 16px;
    background-color: #FFFFFF;
    color: #0F172A;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    font-size: 13px;
    border: 1px solid #CBD5E1;
    transition: all 0.15s ease;
}
.original-btn:hover {
    background-color: #F8FAFC;
    border-color: #94A3B8;
}

.custom-markdown h3 {
    font-size: 18px;
    font-weight: 600;
    color: #0F172A;
    margin-top: 24px;
    margin-bottom: 12px;
}
.custom-markdown h4 {
    font-size: 16px;
    font-weight: 600;
    color: #334155;
    margin-top: 24px;
    margin-bottom: 8px;
    border-bottom: 1px solid #E2E8F0;
    padding-bottom: 8px;
}
.custom-markdown p {
    font-size: 15px;
    line-height: 1.7;
    color: #334155;
}

/* Custom Card Layout */
.card-wrapper {
    background: #FFFFFF !important;
    border: 1px solid #E2E8F0 !important;
    border-radius: 8px !important;
    padding: 20px !important;
    margin-bottom: 16px !important;
    box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05) !important;
    transition: box-shadow 0.2s ease !important;
}
.card-wrapper:hover {
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -1px rgba(0, 0, 0, 0.03) !important;
}

.badge-top-conf {
    background-color: #FEF2F2;
    color: #991B1B;
    border: 1px solid #FECACA;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 6px;
    text-transform: uppercase;
}
.badge-trend {
    background-color: #F0FDF4;
    color: #166534;
    border: 1px solid #BBF7D0;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 11px;
    font-weight: 600;
    margin-right: 6px;
    text-transform: uppercase;
}
.badge-default {
    background-color: #F8FAFC; 
    color: #475569; 
    border: 1px solid #E2E8F0; 
    padding: 2px 8px; 
    border-radius: 4px; 
    font-size: 11px; 
    margin-right: 6px; 
    font-weight: 600;
}
.title-link {
    color: #0F172A;
    text-decoration: none;
    transition: color 0.15s ease;
}
.title-link:hover {
    color: #2563EB;
}
"""

def generate_card_html(paper):
    paper_url = paper.get('link') or paper.get('pdf_url') or '#'
    badges_html = ""
    for badge in paper.get("badges", []):
        if "Top Conf" in badge:
            badges_html += f"<span class='badge-top-conf'>{badge}</span>"
        else:
            badges_html += f"<span class='badge-trend'>{badge}</span>"
    if paper.get("citation_count"):
        badges_html += f"<span class='badge-default'>Citations: {paper.get('citation_count')}</span>"
        
    source_badge = paper.get('source', 'Unknown')
    date_str = paper.get('published_date')
    date_str = f"{date_str}年" if date_str else "発行年不明"
    
    return f"""
    <div style="margin-bottom: 8px;">{badges_html}</div>
    <h3 style='margin-top: 8px; margin-bottom: 4px; font-size: 16px;'><a href='{paper_url}' target='_blank' class='title-link'>{paper.get('title')}</a></h3>
    <p style='color: #2563EB; font-size: 13px; margin-bottom: 6px; font-weight:500;'>{paper.get('authors')}</p>
    <p style='color: #64748B; font-size: 12px; margin-bottom: 12px; font-weight: 500;'>Source: {source_badge} | Year: {date_str}</p>
    <p style='color: #475569; font-size: 14px; margin-bottom: 0px; line-height: 1.5;'>{paper.get('snippet')}</p>
    """

def run_search(query, time_preset, sort_by):
    current_year = date.today().year
    start_year_val = None
    end_year_val = None
    if time_preset == "過去1年間":
        start_year_val = str(current_year - 1)
        end_year_val = str(current_year)
    elif time_preset == "過去5年間":
        start_year_val = str(current_year - 5)
        end_year_val = str(current_year)
    elif time_preset == "過去10年間":
        start_year_val = str(current_year - 10)
        end_year_val = str(current_year)
        
    sort_by_val = "relevance"
    if "Newest" in sort_by: sort_by_val = "newest"
    elif "Oldest" in sort_by: sort_by_val = "oldest"

    try:
        req_obj = SearchRequest(
            query=query,
            start_year=start_year_val,
            end_year=end_year_val,
            sort_by=sort_by_val
        )
        data_dict = asyncio.run(search_papers(req_obj))
        if hasattr(data_dict, "dict"): data_dict = data_dict.dict()
        results = data_dict.get("results", [])
    except Exception as e:
        import traceback
        traceback.print_exc()
        # Default empty returns for blocks
        updates = []
        for i in range(MAX_RESULTS):
            updates.append(gr.update(visible=False))
            updates.append(gr.update(value=""))
        return [
            [], 
            gr.update(visible=True), 
            gr.update(visible=False), 
            gr.update(visible=False),
            f"<div style='color:#DC2626;'>Search failed: {e}</div>"
        ] + updates

    if not results:
        updates = []
        for i in range(MAX_RESULTS):
            updates.append(gr.update(visible=False))
            updates.append(gr.update(value=""))
        return [
            [], 
            gr.update(visible=True), 
            gr.update(visible=False), 
            gr.update(visible=False),
            "<div style='color:#475569;'>条件に一致する論文が見つかりませんでした。別のキーワードや期間でお試しください。</div>"
        ] + updates

    if sort_by_val == "newest":
        results = sorted(results, key=lambda x: x.get('published_date') or '0000', reverse=True)
    elif sort_by_val == "oldest":
        results = sorted(results, key=lambda x: x.get('published_date') or '9999')

    results = results[:MAX_RESULTS]
    status_html = f"<p style='color: #64748B; font-size: 13px; font-weight: 500;'>「{query}」の検索結果 {len(results)}件</p>"
    
    updates = []
    for i in range(MAX_RESULTS):
        if i < len(results):
            paper = results[i]
            html_content = generate_card_html(paper)
            updates.append(gr.update(visible=True))
            updates.append(gr.update(value=html_content))
        else:
            updates.append(gr.update(visible=False))
            updates.append(gr.update(value=""))

    return [
        results,
        gr.update(visible=True),   # view_search_list
        gr.update(visible=False),  # view_translation_result
        gr.update(visible=False),  # view_loading
        status_html
    ] + updates

def replace_terms_with_tooltips(text, glossary_data):
    if not isinstance(glossary_data, list):
        return text
    
    import re
    for cat in glossary_data:
        terms = cat.get("terms", [])
        for t in terms:
            term = t.get("term", "")
            exp = t.get("explanation", "")
            if term and exp:
                escaped_term = re.escape(term)
                # Ensure we only replace outside of HTML tags to avoid breaking existing HTML
                pattern = re.compile(rf'(?<!<[^>]*){escaped_term}(?![^<]*>)', re.IGNORECASE)
                replacement = f"<span class='tooltip' data-tooltip='{exp}'>{term}</span>"
                text = pattern.sub(replacement, text)
    return text

def parse_translation_result(res, paper):
    if isinstance(res, dict) and "tldr" in res:
        title_jp = res.get('title_jp', '無題')
        title_en = res.get('title_en', '')
        date_str = paper.get('published_date') or "YYYY/MM/DD"
        source_str = paper.get('source') or "Unknown"
        glossary = res.get('glossary', [])
        
        tldr_value = res.get('tldr', '')
        if isinstance(tldr_value, list):
            tldr_text = "<br/><br/>".join([str(item) for item in tldr_value])
        else:
            tldr_text = str(tldr_value).replace('\n', '<br/><br/>')
            
        # Apply tooltips
        title_jp = replace_terms_with_tooltips(title_jp, glossary)
        tldr_text = replace_terms_with_tooltips(tldr_text, glossary)
        bg_text = replace_terms_with_tooltips(res.get('background', ''), glossary)
        method_text = replace_terms_with_tooltips(res.get('method', ''), glossary)
        result_text = replace_terms_with_tooltips(res.get('result', ''), glossary)
        disc_text = replace_terms_with_tooltips(res.get('discussion', ''), glossary)
            
        md = f"<div class='custom-markdown'>"
        md += f"<h2 style='margin-top:0; font-size:20px; color:#0F172A;'>{title_jp}</h2>\n<span style='color:#64748B; font-size:13px;'>Original: {title_en} | {date_str} | {source_str}</span>\n\n"
        md += f"<div class='tldr-box'><h3 style='margin-top:0; margin-bottom: 12px; color:#0F172A; font-size:16px;'>3行要約 (TL;DR)</h3>"
        md += f"<div style='font-size:15px; line-height:1.7; color:#334155;'>{tldr_text}</div></div>\n\n"
        
        md += f"<h4>研究の背景と目的</h4>\n<p>{bg_text}</p>\n\n"
        md += f"<h4>提案手法（メソッド）</h4>\n<p>{method_text}</p>\n\n"
        md += f"<h4>実験と結果</h4>\n<p>{result_text}</p>\n\n"
        md += f"<h4>考察・今後の課題</h4>\n<p>{disc_text}</p>\n\n"
        md += f"</div>"
        
        glossary = res.get('glossary', [])
        
        glossary_html = ""
        if glossary:
            glossary_html = "<div style='background: white; padding: 20px; border-radius: 8px; border: 1px solid #E2E8F0;'>"
            glossary_html += "<h4 style='color:#0F172A; font-size: 15px; margin-top:0; margin-bottom:12px;'>用語解説</h4>"
            for cat_data in glossary:
                cat_name = cat_data.get("category", "その他")
                terms = cat_data.get("terms", [])
                if terms:
                    glossary_html += f"<p style='font-size:13px; font-weight:600; color:#64748B; margin-bottom:8px; margin-top:16px; text-transform:uppercase;'>{cat_name}</p><ul style='margin-top:0; padding-left: 20px; font-size:14px; color:#334155; line-height:1.6;'>"
                    for term_data in terms:
                        term = term_data.get("term", "")
                        exp = term_data.get("explanation", "")
                        glossary_html += f"<li style='margin-bottom:6px;'><b style='color:#0F172A;'>{term}</b>: {exp}</li>"
                    glossary_html += "</ul>"
            glossary_html += "</div>"
            
        return md, glossary_html
    else:
        text_content = res if isinstance(res, str) else res.get("raw", str(res))
        return f"<div class='custom-markdown'><p>{text_content}</p></div>", ""

def generate_original_pane(paper):
    url = paper.get('pdf_url', '')
    btn_html = f"<div style='margin-top:20px;'><a href='{url}' target='_blank' class='original-btn'>論文のURL (元のPDF) を開く</a></div>" if url and url != "NO_PDF_URL" else ""
    return f"""
    <div>
        <div style='padding-bottom:12px;'><p class='section-header-en'>Original Source</p></div>
        <div class='snippet-pane'>
            <b style='color:#0F172A; font-size:13px;'>SNIPPET:</b><br/>{paper.get('snippet', '本文情報がありません')}
        </div>
        {btn_html}
    </div>
    """

# Closure generator for mapping button clicks to specific indexes
def make_loading_fn(idx):
    def loading_fn(results_data):
        return (
            gr.update(visible=False), # hide search list
            gr.update(visible=True),  # show loading view
            gr.update(visible=False)  # hide translation view
        )
    return loading_fn

def make_translate_fn(idx):
    def translate_fn(results_data):
        if not results_data or idx >= len(results_data):
            return gr.update(visible=False), gr.update(visible=True), "", "<div style='color:#DC2626;'>エラー: 論文データが見つかりません</div>", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        
        paper = results_data[idx]
        original_html = generate_original_pane(paper)
        
        try:
            req_obj = TranslateRequest(
                pdf_url=paper.get("pdf_url") or "",
                title=paper.get("title") or "",
                snippet=paper.get("snippet") or "",
                published_date=paper.get("published_date") or "",
                source=paper.get("source") or "",
                mode="研究用 (詳細な翻訳と考察)"
            )
            data_dict = asyncio.run(translate_paper(req_obj, req=DummyRequest()))
            if hasattr(data_dict, "dict"): data_dict = data_dict.dict()
            elif isinstance(data_dict, str): data_dict = json.loads(data_dict)
                
            res = data_dict.get("translation")
            paper_id = data_dict.get("paper_id")
            history = data_dict.get("chat_history", [])
            
            md, glossary_html = parse_translation_result(res, paper)
            
            chat_format = []
            if isinstance(history, list):
                for i in range(0, len(history), 2):
                    user_msg = history[i]
                    bot_msg = history[i+1] if i+1 < len(history) else None
                    chat_format.append({"role": "user", "content": user_msg["content"]})
                    if bot_msg:
                        chat_format.append({"role": "assistant", "content": bot_msg["content"]})
                    
            raw_md = f"# {paper.get('title')}\n\n" + str(res.get('tldr', '')) + "\n\n## 背景\n" + str(res.get('background', '')) + "\n\n## 手法\n" + str(res.get('method', '')) + "\n\n## 結果\n" + str(res.get('result', '')) + "\n\n## 考察\n" + str(res.get('discussion', ''))
                    
            return gr.update(visible=False), gr.update(visible=True), original_html, md, glossary_html, paper_id, res, gr.update(value=chat_format), gr.update(value=raw_md)
        except Exception as e:
            import traceback
            traceback.print_exc()
            return gr.update(visible=False), gr.update(visible=True), original_html, f"<div style='color:#DC2626;'>翻訳エラー (Error Info): {e}</div>", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
    return translate_fn

def load_history_dropdown():
    try:
        data_dict = get_history(req=DummyRequest())
        if hasattr(data_dict, "dict"): data_dict = data_dict.dict()
        history_data = data_dict.get("history", [])
        if not history_data:
            return gr.update(choices=["履歴なし"], value="履歴なし"), history_data
        
        choices = []
        for item in history_data:
            t = item.get("title_jp") or item.get("title_en") or "無題"
            choices.append(f"[{item.get('paper_id')}] {t[:40]}")
        return gr.update(choices=choices, value=choices[0] if choices else None), history_data
    except Exception as e:
        return gr.update(choices=[], value=None), []

def do_load_history(selected_hist, history_data):
    if not selected_hist or selected_hist == "履歴なし":
        return (
            gr.update(visible=True), gr.update(visible=False),
            "", "<div style='color:#DC2626;'>履歴が選択されていません</div>", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        )
    pid = selected_hist.split(']')[0][1:]
    
    item = next((x for x in history_data if str(x.get('paper_id')) == pid), None)
    if not item:
        return (
            gr.update(visible=True), gr.update(visible=False),
            "", "<div style='color:#DC2626;'>エラー: データが見つかりません</div>", gr.update(), gr.update(), gr.update(), gr.update(), gr.update()
        )
        
    paper = {
        "title": item.get('title_en'),
        "pdf_url": item.get('source_url'),
        "published_date": item.get('published_date'),
        "source": "History",
        "snippet": "データベースから読み込みました（キャッシュ）。"
    }
    
    try:
        summary_json = json.loads(item.get('summary_json'))
    except:
        summary_json = {"raw": item.get('summary_json')}
        
    try:
        chat_hist = json.loads(item.get("chat_history") or "[]")
    except:
        chat_hist = []
        
    md, glossary_html = parse_translation_result(summary_json, paper)
    original_html = generate_original_pane(paper)
    
    chat_format = []
    for i in range(0, len(chat_hist), 2):
        user_msg = chat_hist[i]
        bot_msg = chat_hist[i+1] if i+1 < len(chat_hist) else None
        chat_format.append({"role": "user", "content": user_msg["content"]})
        if bot_msg:
            chat_format.append({"role": "assistant", "content": bot_msg["content"]})
            
    raw_md = f"# {paper.get('title')}\n\n" + str(summary_json.get('tldr', '')) + "\n\n## 背景\n" + str(summary_json.get('background', '')) + "\n\n## 手法\n" + str(summary_json.get('method', '')) + "\n\n## 結果\n" + str(summary_json.get('result', '')) + "\n\n## 考察\n" + str(summary_json.get('discussion', ''))
            
    # Show translation layout and hide history selector layout
    return (
        gr.update(visible=False), gr.update(visible=True),
        original_html, md, glossary_html, item.get('paper_id'), summary_json, gr.update(value=chat_format), gr.update(value=raw_md)
    )

def do_chat(message, history_ui, paper_id, translation_res):
    if not paper_id or not message:
        return "", history_ui
        
    past_roles = []
    for msg in history_ui:
        if isinstance(msg, dict):
            past_roles.append(msg)
        elif isinstance(msg, list) or isinstance(msg, tuple):
            u, bot = msg
            past_roles.append({"role": "user", "content": u})
            if bot: pass # We'll just collect user and assistant normally from tuples if Gradio hands them back
            
    past_roles.append({"role": "user", "content": message})
    
    try:
        req_obj = QARequest(
            question=message,
            context=str(translation_res), 
            history=past_roles[:-1]
        )
        data_dict = qa_paper(req_obj)
        if hasattr(data_dict, "dict"): data_dict = data_dict.dict()
        
        answer = data_dict.get("answer", "")
        past_roles.append({"role": "assistant", "content": answer})
        
        up_req = QAChatUpdateRequest(paper_id=paper_id, chat_history=past_roles)
        update_chat(up_req)
        
        return "", past_roles
    except Exception as e:
        past_roles.append({"role": "assistant", "content": f"エラーが発生しました: {str(e)}"})
        return "", past_roles

def return_to_search():
    return gr.update(visible=True), gr.update(visible=False)

def return_to_history():
    return gr.update(visible=True), gr.update(visible=False)


with gr.Blocks(theme=gr.themes.Base(primary_hue="blue", neutral_hue="slate"), css=CSS, title="ScholarStream") as demo:
    gr.HTML('<style>@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");</style><div class="brand-header"><div class="brand-icon">S</div><h1 class="brand-title">ScholarStream</h1></div>')
    
    state_search_results = gr.State([])
    state_history_data = gr.State([])
    state_current_paper_id = gr.State(None)
    state_translation_res = gr.State(None)
    
    with gr.Tabs():
        # --- TAB 1: Search & Translate ---
        with gr.Tab("論文を検索する"):
            
            # --- VIEW A: Search List ---
            with gr.Column(visible=True) as view_search_list:
                with gr.Row():
                    with gr.Column(scale=10):
                        query_input = gr.Textbox(placeholder="検索キーワードを入力してください (例: attention is all you need)", show_label=False)
                    with gr.Column(scale=2):
                        search_btn = gr.Button("検索", variant="primary")
                        
                with gr.Row():
                    # Filter elements horizontally aligned under search
                    time_preset = gr.Dropdown(show_label=False, choices=["指定なし", "過去1年間", "過去5年間", "過去10年間"], value="指定なし", container=False)
                    sort_by = gr.Dropdown(show_label=False, choices=["関連度順 (Relevance)", "最新順 (Newest)", "古い順 (Oldest)"], value="関連度順 (Relevance)", container=False)
                
                gr.HTML("<hr style='margin: 24px 0 16px 0; border: none; border-top: 1px solid #E2E8F0;'/>")
                search_status_html = gr.HTML("<div style='color: #64748B; font-size: 13px;'>ここに検索結果が表示されます</div>")
                
                # Dynamic List of fixed capacity (MAX_RESULTS)
                result_card_blocks = []
                for i in range(MAX_RESULTS):
                    with gr.Column(visible=False, elem_classes="card-wrapper") as card_col:
                        card_html = gr.HTML()
                        card_btn = gr.Button(f"この論文を翻訳・要約する", variant="secondary", size="sm")
                        result_card_blocks.append({"col": card_col, "html": card_html, "btn": card_btn})

            # --- VIEW LOADING ---
            with gr.Column(visible=False, elem_classes="translation-overlay") as view_loading:
                gr.HTML("""
                <div style='padding:100px 20px; text-align:center;'>
                    <div class='spinner'></div>
                    <h3 style='color:#2563EB; font-size:22px; margin-top:20px;'>論文を翻訳・要約しています...</h3>
                    <p style='color:#64748B; margin-top:12px; font-size:15px;'>この処理には約30秒〜1分程度かかります。このままお待ちください。</p>
                </div>
                """)

            # --- VIEW B: Translation Full Layout (Overlay alternative) ---
            with gr.Column(visible=False, elem_classes="translation-overlay") as view_translation_result:
                back_to_search_btn = gr.Button("← 検索結果一覧に戻る", size="sm") 
                gr.HTML("<hr style='margin: 16px 0 24px 0; border: none; border-top: 1px solid #E2E8F0;'/>")
                
                with gr.Row():
                    with gr.Column(scale=5):
                        original_html_out = gr.HTML()
                    with gr.Column(scale=7):
                        translation_md = gr.HTML()
                        
                        with gr.Accordion("翻訳結果をMarkdownとしてコピーする", open=False):
                            md_copy_box = gr.Textbox(show_label=False, max_lines=15, interactive=True)
                        
                        with gr.Accordion("主要用語集の解説", open=False):
                            glossary_html_out = gr.HTML()
                        
                        with gr.Accordion("論文Q&A (AIアシスタントに質問)", open=True):
                            chatbot = gr.Chatbot(height=300, show_label=False, value=[])
                            chat_input = gr.Textbox(placeholder="この論文について質問...", show_label=False)

        # --- TAB 2: History ---            
        with gr.Tab("履歴から読み込み"):
            
            # --- VIEW C: History Selection ---
            with gr.Column(visible=True) as view_history_list:
                gr.Markdown("過去に翻訳した論文を読み込みます。")
                with gr.Row():
                    with gr.Column(scale=8):
                        history_dropdown = gr.Dropdown(label="履歴を選択", choices=[], allow_custom_value=True)
                    with gr.Column(scale=4):
                        with gr.Row():
                            load_history_btn = gr.Button("選択した履歴を読み込む", variant="primary")
                            refresh_history_btn = gr.Button("リストを更新")
            
            # --- VIEW D: History Translation ---
            with gr.Column(visible=False) as view_history_result:
                back_to_history_btn = gr.Button("← 履歴選択に戻る", size="sm")
                gr.HTML("<hr style='margin: 16px 0 24px 0; border: none; border-top: 1px solid #E2E8F0;'/>")
                
                with gr.Row():
                    with gr.Column(scale=4):
                        hist_original_html_out = gr.HTML()
                    with gr.Column(scale=8):
                        history_translation_md = gr.HTML()
                        
                        with gr.Accordion("翻訳結果をMarkdownとしてコピーする", open=False):
                            hist_md_copy_box = gr.Textbox(show_label=False, max_lines=15, interactive=True)
                                
                        with gr.Accordion("主要用語集の解説", open=False):
                            history_glossary_html = gr.HTML()
                        
                        with gr.Accordion("論文Q&A (AIアシスタントに質問)", open=True):
                            history_chatbot = gr.Chatbot(height=300, show_label=False, value=[])
                            history_chat_input = gr.Textbox(placeholder="この論文について質問...", show_label=False)

    # --- Events ---
    
    # Compile outputs for search: State + Search View + Translated View + Status + (20 * [Col, Html])
    search_outputs = [state_search_results, view_search_list, view_translation_result, view_loading, search_status_html]
    for block in result_card_blocks:
        search_outputs.append(block["col"])
        search_outputs.append(block["html"])
        
    # 1. Search Submissions
    search_btn.click(
        fn=run_search,
        inputs=[query_input, time_preset, sort_by],
        outputs=search_outputs
    )
    query_input.submit(
        fn=run_search,
        inputs=[query_input, time_preset, sort_by],
        outputs=search_outputs
    )

    # 2. Assign Clicks to All Cards
    for i in range(MAX_RESULTS):
        btn = result_card_blocks[i]["btn"]
        btn.click(
            fn=make_loading_fn(i),
            inputs=[state_search_results],
            outputs=[view_search_list, view_loading, view_translation_result]
        ).then(
            fn=make_translate_fn(i),
            inputs=[state_search_results],
            outputs=[view_loading, view_translation_result, original_html_out, translation_md, glossary_html_out, state_current_paper_id, state_translation_res, chatbot, md_copy_box]
        )
    
    # Navigation Back
    back_to_search_btn.click(
        fn=return_to_search,
        inputs=[],
        outputs=[view_search_list, view_translation_result]
    )
    back_to_history_btn.click(
        fn=return_to_history,
        inputs=[],
        outputs=[view_history_list, view_history_result]
    )
    
    # Q&A Logic for Translation View
    chat_input.submit(
        fn=do_chat,
        inputs=[chat_input, chatbot, state_current_paper_id, state_translation_res],
        outputs=[chat_input, chatbot]
    )
    
    # History Logic
    demo.load(
        fn=load_history_dropdown,
        outputs=[history_dropdown, state_history_data]
    )
    refresh_history_btn.click(
        fn=load_history_dropdown,
        outputs=[history_dropdown, state_history_data]
    )
    
    load_history_btn.click(
        fn=do_load_history,
        inputs=[history_dropdown, state_history_data],
        outputs=[view_history_list, view_history_result, hist_original_html_out, history_translation_md, history_glossary_html, state_current_paper_id, state_translation_res, history_chatbot, hist_md_copy_box]
    )
    
    history_chat_input.submit(
        fn=do_chat,
        inputs=[history_chat_input, history_chatbot, state_current_paper_id, state_translation_res],
        outputs=[history_chat_input, history_chatbot]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=8501)
