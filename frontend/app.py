import streamlit as st
import requests
import os
from datetime import datetime, timedelta, date
import os
import json

BACKEND_URL = os.getenv("BACKEND_URL", "http://backend:8000")

st.set_page_config(
    page_title="ScholarStream",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif !important;
    }
    
    .stApp {
        background-color: #F8FAFC;
    }

    /* Main Header Container */
    .brand-header {
        display: flex;
        align-items: center;
        gap: 12px;
        margin-bottom: 24px;
        padding-top: 1rem;
    }
    .brand-icon {
        background: #2563EB;
        color: white;
        width: 36px;
        height: 36px;
        border-radius: 8px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 20px;
        font-weight: bold;
    }
    .brand-title {
        font-size: 24px;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    
    /* Result Cards */
    .result-card {
        background: white;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 16px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06);
    }
    
    /* Translation Output Container */
    .translation-output {
        background-color: white;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        color: #0F172A;
        line-height: 1.6;
        font-size: 15px;
    }
    .translation-output h1 { font-size: 22px; color: #1E293B; border-bottom: 2px solid #E2E8F0; padding-bottom: 8px; margin-top: 16px; font-weight: 700; }
    .translation-output h2 { font-size: 18px; color: #2563EB; margin-top: 24px; margin-bottom: 12px; font-weight: 600; }
    .translation-output p { font-size: 15px; color: #334155; line-height: 1.6; margin-bottom: 12px; }
    .translation-output blockquote { border-left: 4px solid #3B82F6; background-color: #F8FAFC; padding: 12px 16px; margin: 0 0 16px 0; color: #475569; font-style: normal; }
    .translation-output blockquote p { margin-bottom: 0; font-weight: 500; }
    .translation-output ul { margin-bottom: 16px; padding-left: 24px; }
    .translation-output li { margin-bottom: 8px; font-size: 15px; color: #334155; line-height: 1.6; }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin-right: 6px;
        margin-bottom: 8px;
    }
    .badge-top-conf {
        background-color: #FEF2F2;
        color: #DC2626;
        border: 1px solid #FECACA;
    }
    .badge-trend {
        background-color: #F0FDF4;
        color: #16A34A;
        border: 1px solid #BBF7D0;
    }
    .badge-source {
        background-color: #F8FAFC;
        color: #475569;
        border: 1px solid #E2E8F0;
    }

    /* Hide standard Streamlit elements */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}

    /* Custom Radio (USAGE MODE) */
    div.row-widget.stRadio > div {
        display: flex;
        flex-direction: row;
        gap: 10px;
        background-color: transparent;
    }

    /* Buttons */
    div.stButton > button:first-child[kind="primary"] {
        background-color: #1D4ED8 !important;
        color: white !important;
        font-weight: 600 !important;
        border: none !important;
        border-radius: 8px;
        min-height: 48px;
    }
    div.stButton > button:first-child[kind="primary"]:hover {
        background-color: #1E40AF !important;
    }
    
    /* Input border */
    .stTextInput input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
        padding: 12px 16px;
    }
    
    /* Section Headers */
    .section-header-en {
        color: #64748B;
        text-align: center;
        font-size: 14px;
        font-weight: 700;
        margin: 0 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #E2E8F0;
    }
    .section-header-jp {
        color: #2563EB;
        text-align: center;
        font-size: 14px;
        font-weight: 700;
        margin: 0 0 16px 0;
        padding-bottom: 8px;
        border-bottom: 2px solid #2563EB;
    }
    
    /* Text rendering tweaks */
    p { margin-bottom: 0.5rem; }
    h3 { margin-bottom: 0.5rem; margin-top: 0; }
    
    /* Title Link */
    .title-link {
        color: #0F172A;
        text-decoration: none;
        transition: color 0.2s ease;
    }
    .title-link:hover {
        color: #2563EB;
        text-decoration: underline;
    }

    /* Glossary Tooltips */
    .glossary-term {
        position: relative;
        display: inline-block;
        border-bottom: 1px dashed #3B82F6;
        color: #3B82F6;
        cursor: help;
        margin-right: 12px;
        margin-bottom: 8px;
        font-weight: 500;
    }
    .glossary-term .tooltip-text {
        visibility: hidden;
        width: 250px;
        background-color: #1E293B;
        color: #F8FAFC;
        text-align: left;
        border-radius: 6px;
        padding: 8px 12px;
        position: absolute;
        z-index: 10;
        bottom: 125%;
        left: 50%;
        transform: translateX(-50%);
        opacity: 0;
        transition: opacity 0.2s;
        font-size: 13px;
        font-weight: 400;
        line-height: 1.4;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .glossary-term .tooltip-text::after {
        content: "";
        position: absolute;
        top: 100%;
        left: 50%;
        margin-left: -5px;
        border-width: 5px;
        border-style: solid;
        border-color: #1E293B transparent transparent transparent;
    }
    .glossary-term:hover .tooltip-text {
        visibility: visible;
        opacity: 1;
    }
    .glossary-category {
        font-size: 14px;
        font-weight: 700;
        color: #475569;
        margin-top: 16px;
        margin-bottom: 8px;
        padding-bottom: 4px;
        border-bottom: 1px solid #E2E8F0;
    }
</style>
""", unsafe_allow_html=True)

# State Management
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_paper" not in st.session_state:
    st.session_state.selected_paper = None
if "translation_result" not in st.session_state:
    st.session_state.translation_result = None
if "is_searching" not in st.session_state:
    st.session_state.is_searching = False
if "is_translating" not in st.session_state:
    st.session_state.is_translating = False

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "glossary_result" not in st.session_state:
    st.session_state.glossary_result = []
if "current_paper_id" not in st.session_state:
    st.session_state.current_paper_id = None

# -----------------
# App Logic

@st.dialog("📖 閲覧中", width="large")
def show_translation_dialog(paper):

    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<p class='section-header-en'>原文</p>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style='border-left: 4px solid #3B82F6; padding-left: 16px; margin-top: 16px; background-color: #F8FAFC; padding: 24px; border-radius: 0 8px 8px 0; color: #334155; height: 60vh; overflow-y: auto;'>
            <p style='font-size: 15px; line-height: 1.6;'><b>Snippet:</b><br/>{paper.get('snippet')}</p>
        </div>
        """, unsafe_allow_html=True)
        if paper.get('pdf_url'):
             st.markdown(f"<div style='margin-top: 24px; text-align: center;'><a href='{paper.get('pdf_url')}' target='_blank' style='display: inline-block; padding: 10px 20px; background-color: #F1F5F9; color: #0F172A; text-decoration: none; border-radius: 8px; font-weight: 500; border: 1px solid #E2E8F0;'>元のPDFを開く</a></div>", unsafe_allow_html=True)

    with col2:
        st.markdown("<p class='section-header-jp'>翻訳・要約結果</p>", unsafe_allow_html=True)
        
        if st.session_state.is_translating:
            with st.spinner("翻訳・要約中..."):
                try:
                    res = requests.post(f"{BACKEND_URL}/translate", json={
                        "pdf_url": paper.get("pdf_url") or "",
                        "title": paper.get("title") or "",
                        "snippet": paper.get("snippet") or "",
                        "published_date": paper.get("published_date") or "",
                        "source": paper.get("source") or "",
                        "mode": "研究用 (詳細な翻訳と考察)"
                    })
                    res.raise_for_status()
                    data = res.json()
                    st.session_state.translation_result = data.get("translation")
                    st.session_state.glossary_result = data.get("glossary", [])
                    st.session_state.current_paper_id = data.get("paper_id")
                    st.session_state.chat_history = data.get("chat_history", [])
                except requests.exceptions.HTTPError as e:
                    if res.status_code == 429:
                        st.warning("本日の利用上限に達しました。明日またご利用ください。")
                    elif res.status_code == 500:
                        st.error("Backend Error: Please check if GEMINI_API_KEY is correctly set in .env")
                    else:
                        st.error(f"Translation failed: {res.json().get('detail', 'Unknown error')}")
                except Exception as e:
                    st.error(f"Translation failed: {e}")
            st.session_state.is_translating = False

        if st.session_state.translation_result:
            res = st.session_state.translation_result
            if isinstance(res, dict) and "tldr" in res:
                title_jp = res.get('title_jp', '無題')
                title_en = res.get('title_en', '')
                date_str = paper.get('published_date') or "YYYY/MM/DD"
                source_str = paper.get('source') or "Unknown"
                
                # Title
                st.markdown(f"### 📄 {title_jp}")
                st.caption(f"Original: {title_en} | {date_str} | {source_str}")
                
                # TL;DR (強調表示)
                with st.container():
                    tldr_value = res.get('tldr', '')
                    if isinstance(tldr_value, list):
                        tldr_text = "<br/><br/>".join([str(item) for item in tldr_value])
                    else:
                        tldr_text = str(tldr_value).replace('\n', '<br/><br/>')
                        
                    st.markdown(f"""
                    <div style='background-color: #F8FAFC; border-left: 6px solid #3B82F6; padding: 20px 24px; border-radius: 8px; margin-bottom: 24px; box-shadow: 0 2px 4px rgba(0,0,0,0.05);'>
                        <h3 style='margin-top: 0; color: #1E293B; font-size: 1.25em; margin-bottom: 16px; border-bottom: none;'>📝 3行でわかる今回の研究</h3>
                        <div style='display: flex; gap: 12px; align-items: flex-start;'>
                            <div style='font-size: 1.4em; margin-top: 2px;'>💡</div>
                            <div style='font-size: 1.1em; line-height: 1.8; font-weight: 600; color: #334155;'>
                                {tldr_text}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                st.divider()
                
                # Sections
                st.markdown("#### 🔍 研究の背景と目的")
                st.write(res.get('background', ''))
                st.divider()
                
                st.markdown("#### ⚙️ 提案手法（メソッド）")
                st.write(res.get('method', ''))
                st.divider()
                
                st.markdown("#### 📊 実験と結果")
                st.write(res.get('result', ''))
                st.divider()
                
                st.markdown("#### 💡 考察・今後の課題")
                st.write(res.get('discussion', ''))
                st.divider()
                
                # Markdown Copy
                copy_tldr = tldr_value if isinstance(tldr_value, list) else [res.get('tldr', '')]
                copy_tldr_str = "\n".join([str(item) for item in copy_tldr])
                
                copy_text = f"# {title_jp}\n*Original Title: {title_en}*\n\n## 📝 3行でわかる今回の研究（TL;DR）\n{copy_tldr_str}\n\n## 🔍 研究の背景と目的\n{res.get('background')}\n\n## ⚙️ 提案手法（メソッド）\n{res.get('method')}\n\n## 📊 実験と結果\n{res.get('result')}\n\n## 💡 考察・今後の課題\n{res.get('discussion')}"
                with st.expander("📝 翻訳結果をMarkdownとしてコピーする"):
                     st.code(copy_text, language="markdown")
                     
                # Terms
                st.session_state.glossary_result = res.get('glossary', [])
            else:
                # Fallback
                text_content = res if isinstance(res, str) else res.get("raw", str(res))
                st.markdown(f"""
                <div class='translation-output' style='height: 60vh; overflow-y: auto;'>
                    {text_content.replace(chr(10), '<br/>')}
                </div>
                """, unsafe_allow_html=True)
                
                st.divider()
                with st.expander("📝 翻訳結果をMarkdownとしてコピーする"):
                     st.code(text_content, language="markdown")

    # -----------------
    # Glossary Section
    # -----------------
    if st.session_state.translation_result and st.session_state.glossary_result:
        st.markdown("<br><br>", unsafe_allow_html=True)
        with st.expander("📚 主要用語集の解説を表示", expanded=False):
            st.markdown("<p style='font-size: 13px; color: #64748B; margin-bottom: 16px;'>※ 用語にカーソルを合わせると説明が表示されます。</p>", unsafe_allow_html=True)
            
            glossary_html = "<div style='background: white; padding: 24px; border-radius: 12px; border: 1px solid #E2E8F0;'>"
            for cat_data in st.session_state.glossary_result:
                cat_name = cat_data.get("category", "その他")
                terms = cat_data.get("terms", [])
                if terms:
                    glossary_html += f"<div class='glossary-category'>■ {cat_name}</div>"
                    glossary_html += "<div style='margin-bottom: 12px;'>"
                    for term_data in terms:
                        term = term_data.get("term", "")
                        exp = term_data.get("explanation", "")
                        glossary_html += f"<div class='glossary-term'>{term}<span class='tooltip-text'>{exp}</span></div>"
                    glossary_html += "</div>"
            glossary_html += "</div>"
            st.markdown(glossary_html, unsafe_allow_html=True)

    # -----------------
    # Chat QA Section
    # -----------------
    if st.session_state.translation_result:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<p class='section-header-jp'>論文Q&A (AIアシスタントに質問)</p>", unsafe_allow_html=True)
        
        chat_container = st.container()
                
        # Inline Chat Input Form
        form_key = f"qa_form_{st.session_state.current_paper_id}" if st.session_state.current_paper_id else "qa_form_default"
        with st.form(key=form_key, clear_on_submit=True, border=False):
            col1, col2 = st.columns([8, 2])
            with col1:
                prompt = st.text_input("質問", placeholder="この論文について質問する...", label_visibility="collapsed")
            with col2:
                submit = st.form_submit_button("送信", type="primary", use_container_width=True)
                
        if submit and prompt:
            st.session_state.chat_history.append({"role": "user", "content": prompt})
            
            with chat_container:
                # Render the history immediately
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])
                        
                with st.chat_message("assistant"):
                    with st.spinner("思考中..."):
                        try:
                            payload = {
                                "question": prompt,
                                "context": str(st.session_state.translation_result), 
                                "history": st.session_state.chat_history[:-1]
                            }
                            res = requests.post(f"{BACKEND_URL}/qa", json=payload)
                            res.raise_for_status()
                            answer = res.json().get("answer", "")
                            st.markdown(answer)
                            # Save assistant response to history
                            st.session_state.chat_history.append({"role": "assistant", "content": answer})
                            
                            # Sync chat history back to database
                            if st.session_state.current_paper_id:
                                try:
                                    requests.post(f"{BACKEND_URL}/update_chat", json={
                                        "paper_id": st.session_state.current_paper_id,
                                        "chat_history": st.session_state.chat_history
                                    }, timeout=3)
                                except Exception as db_e:
                                    st.error(f"チャット履歴の保存に失敗しました: {db_e}")
                                    
                        except Exception as e:
                            st.error(f"エラーが発生しました: {e}")
        else:
            with chat_container:
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

# -----------------
# Main Search View
# -----------------
head_col1, head_col2 = st.columns([9, 1])
with head_col1:
    st.markdown('<div class="brand-header"><div class="brand-icon">S</div><h1 class="brand-title">ScholarStream</h1></div>', unsafe_allow_html=True)
    st.caption(f"🔧 Debug: Connecting to backend at `{BACKEND_URL}`")

with head_col2:
    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)
    with st.popover("☰ 履歴", use_container_width=True):
        st.markdown("<h3 style='text-align: center; color: #1E293B; margin-bottom: 0;'>📚 翻訳履歴</h3>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #64748B; font-size: 13px; margin-bottom: 24px; margin-top: 4px;'>過去に確認した論文</p>", unsafe_allow_html=True)
        
        try:
            res = requests.get(f"{BACKEND_URL}/history", timeout=5)
            if res.status_code == 200:
                history_data = res.json().get("history", [])
                if not history_data:
                    st.info("まだ翻訳履歴がありません。")
                else:
                    for idx, item in enumerate(history_data):
                        title_display = item.get("title_jp") or item.get("title_en") or "名称不明"
                        if len(title_display) > 35:
                            title_display = title_display[:35] + "..."
                            
                        button_label = f"📄 {title_display}"
                        if st.button(button_label, key=f"hist_btn_{item.get('paper_id')}_{idx}", use_container_width=True):
                            st.session_state.selected_paper = {
                                "title": item.get('title_en'),
                                "pdf_url": item.get('source_url'),
                                "published_date": item.get('published_date'),
                                "source": "History",
                                "snippet": "データベースから読み込みました（キャッシュ）。"
                            }
                            
                            try:
                                summary_json = json.loads(item.get('summary_json'))
                                st.session_state.translation_result = summary_json
                                st.session_state.glossary_result = summary_json.get('glossary', [])
                            except Exception:
                                st.session_state.translation_result = {"error": "解析エラー", "raw": item.get('summary_json')}
                                st.session_state.glossary_result = []
                                
                            st.session_state.current_paper_id = item.get("paper_id")
                            try:
                                chat_hist_raw = item.get("chat_history")
                                st.session_state.chat_history = json.loads(chat_hist_raw) if chat_hist_raw else []
                            except Exception:
                                st.session_state.chat_history = []
                                
                            st.session_state.is_translating = False
                            show_translation_dialog(st.session_state.selected_paper)
        except Exception as e:
            st.error("履歴の取得に失敗しました。サーバーが起動していない可能性があります。")

search_query = st.text_input("検索", value=st.session_state.get("last_query", ""), placeholder="例: attention is all you need", label_visibility="collapsed")
    
    
# Filters
col_time, col_sort, col_custom_time, _ = st.columns([2, 2, 4, 2])
with col_time:
    time_preset = st.selectbox(
        "期間指定", 
        options=["指定なし", "過去1年間", "過去5年間", "過去10年間", "カスタム期間指定"],
        index=0
    )

with col_sort:
    sort_by = st.selectbox(
        "並び替え",
        options=["関連度順 (Relevance)", "最新順 (Newest)", "古い順 (Oldest)"],
        index=0
    )
    
start_year_val = None
end_year_val = None
current_year = date.today().year

if time_preset == "カスタム期間指定":
    with col_custom_time:
        st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
        custom_years = st.slider(
            "年代を指定",
            min_value=1990,
            max_value=current_year,
            value=(current_year - 5, current_year),
            step=1,
            label_visibility="collapsed"
        )
        # st.slider returns a tuple when you provide a tuple as value
        start_year_val = str(custom_years[0])
        end_year_val = str(custom_years[1])
             
elif time_preset == "過去1年間":
    start_year_val = str(current_year - 1)
    end_year_val = str(current_year)
elif time_preset == "過去5年間":
    start_year_val = str(current_year - 5)
    end_year_val = str(current_year)
elif time_preset == "過去10年間":
    start_year_val = str(current_year - 10)
    end_year_val = str(current_year)
    
# Sort parsed values
sort_by_val = "relevance"
if "Newest" in sort_by: sort_by_val = "newest"
elif "Oldest" in sort_by: sort_by_val = "oldest"

col_search, _ = st.columns([1, 5])
with col_search:
    if st.button("検索", type="primary", use_container_width=True):
        st.session_state.last_query = search_query
        st.session_state.is_searching = True
        st.session_state.search_results = []
        st.session_state.translation_result = None
        st.session_state.glossary_result = []

if st.session_state.is_searching:
    if not search_query:
        st.error("検索キーワードを入力してください。")
        st.session_state.is_searching = False
    else:
        with st.spinner("論文を検索中（arXiv & Google Scholar）..."):
            try:
                payload = {
                    "query": search_query,
                    "start_year": start_year_val,
                    "end_year": end_year_val,
                    "sort_by": sort_by_val
                }
                res = requests.post(f"{BACKEND_URL}/search", json=payload)
                res.raise_for_status()
                data = res.json()
                st.session_state.search_results = data.get("results", [])
            except requests.exceptions.HTTPError as e:
                if res.status_code == 500:
                    st.error("Backend Error: Please check if SERPAPI_API_KEY is correctly set in .env")
                else:
                    st.error(f"Search failed: HTTP {res.status_code}")
            except Exception as e:
                st.error(f"Search request failed: {e}")
        st.session_state.is_searching = False
        
        if st.session_state.search_results is not None and len(st.session_state.search_results) == 0:
            st.info("条件に一致する論文が見つかりませんでした。別のキーワードや期間でお試しください。")

st.divider()

results = st.session_state.search_results
if results:
    # Sort explicitly in UI to guarantee standard behavior as requested
    # Dates that are None will be treated as very old so they go to the bottom of Newest
    if sort_by_val == "newest":
        results = sorted(results, key=lambda x: x.get('published_date') or '0000', reverse=True)
    elif sort_by_val == "oldest":
        results = sorted(results, key=lambda x: x.get('published_date') or '9999')
        
    st.markdown(f"<p style='color: #64748B; font-size: 14px;'>「{st.session_state.last_query}」の検索結果 {len(results)}件</p>", unsafe_allow_html=True)
    for idx, paper in enumerate(results):
        paper_url = paper.get('link') or paper.get('pdf_url') or '#'
            
        # Construct Badges HTML
        badges_html = ""
        for badge in paper.get("badges", []):
            if "Top Conf" in badge:
                badges_html += f"<span class='badge badge-top-conf'>🔥 {badge}</span>"
            else:
                badges_html += f"<span class='badge badge-trend'>💡 {badge}</span>"
                
        if paper.get("citation_count"):
            badges_html += f"<span class='badge' style='background-color:#F8FAFC; color:#64748B; border:1px solid #E2E8F0'>📈 Citations: {paper.get('citation_count')}</span>"

        # Parse and format Japanese date label
        source_badge = paper.get('source', 'Unknown')
        date_str = paper.get('published_date')
        if date_str:
            date_str = f"{date_str}年"
        else:
            # If backend failed to parse it entirely
            date_str = "発行年不明"
        
        source_date_label = f"Source: {source_badge} | Year: {date_str}"

        # Wrap content manually so we don't break Streamlit layouts
        st.markdown(f"""
        <div class="result-card">
            <div>{badges_html}</div>
            <h3 style='margin-top: 8px; margin-bottom: 4px; font-size: 18px;'><a href='{paper_url}' target='_blank' class='title-link'>{paper.get('title')}</a></h3>
            <p style='color: #2563EB; font-size: 14px; margin-bottom: 4px;'>{paper.get('authors')}</p>
            <p style='color: #64748B; font-size: 13px; font-weight: 500; margin-bottom: 8px;'>📅 {source_date_label}</p>
            <p style='color: #475569; font-size: 14px; margin-bottom: 16px; margin-top: 8px;'>{paper.get('snippet')}</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.button("翻訳・要約", key=f"btn_translate_{idx}", type="primary"):
            st.session_state.selected_paper = paper
            st.session_state.is_translating = True
            st.session_state.chat_history = []  # Clear chat history for new paper
            st.session_state.glossary_result = [] # Clear glossary
            st.session_state.current_paper_id = None
            st.session_state.translation_result = None # Clear old translation results
            show_translation_dialog(st.session_state.selected_paper)
