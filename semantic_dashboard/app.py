import streamlit as st
import yaml
import os
import glob
from collections import defaultdict

st.set_page_config(layout="wide", page_title="Cortex Analyst Semantic View")

st.markdown("""
<style>
    [data-testid="stSidebar"][data-collapsed="false"] {
        min-width: 230px !important;
        max-width: 260px !important;
    }
    
    /* 헤더 영역 컴팩트화 */
    .main-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0c192c; /* Snowflake Deep Navy */
        margin-top: -20px;
        margin-bottom: 2px;
    }
    .sub-title {
        font-size: 0.95rem;
        color: #5a6e85;
        margin-bottom: 15px;
    }
    .sub-title strong {
        color: #0369a1;
    }
    
    /* DB 정보 태그 스타일 */
    .db-badge {
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-right: 6px;
        margin-bottom: 10px;
        border: 1px solid #bae6fd;
    }
    
    /* 컬럼 사전 라인 스타일 */
    .col-row {
        padding: 6px 10px;
        border-bottom: 1px solid #f1f5f9;
        display: flex;
        align-items: flex-start;
    }
    .col-name {
        font-weight: 600;
        color: #0074b7;
        min-width: 150px;
        font-size: 0.9rem;
    }
    .col-meaning {
        color: #334155;
        font-size: 0.9rem;
    }
    
    /* 관계(Join) 및 동의어 카드 디자인 정돈 */
    .relation-box {
        background-color: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 6px;
        padding: 12px;
        margin-bottom: 10px;
    }
    .synonym-row {
        display: flex;
        align-items: center;
        padding: 8px 10px;
        background: #ffffff;
        border-bottom: 1px solid #f1f5f9;
    }
    .synonym-badge {
        color: white;
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 0.7rem;
        font-weight: 600;
        min-width: 65px;
        text-align: center;
        text-transform: uppercase;
    }
</style>
""", unsafe_allow_html=True)

SEMANTIC_DIR = "semantic_models"

def get_functional_groups():
    if not os.path.exists(SEMANTIC_DIR): return []
    files = glob.glob(os.path.join(SEMANTIC_DIR, "*.yaml"))
    return sorted([os.path.basename(f).replace(".yaml", "") for f in files])

def load_yaml(func_group):
    path = os.path.join(SEMANTIC_DIR, f"{func_group}.yaml")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def extract_databases(yaml_data):
    """모델 내 테이블 명세에서 대상 Database 이름을 파싱 및 추출합니다."""
    dbs = set()
    
    # 1. builder.py가 저장한 최상위 databases 리스트 우선 확인
    if "databases" in yaml_data:
        for db in yaml_data["databases"]:
            dbs.add(db)
            
    # 2. 테이블 설명 명세 파싱 (LLM이 DB.TABLE 형태로 적었을 경우)
    for d in yaml_data.get("descriptions", []):
        table = d.get("table", "")
        if "." in table:
            dbs.add(table.split(".")[0])
            
    # 3. 조인 관계 명세 파싱
    for r in yaml_data.get("relations", []):
        t1, t2 = r.get("table_1", ""), r.get("table_2", "")
        if "." in t1: dbs.add(t1.split(".")[0])
        if "." in t2: dbs.add(t2.split(".")[0])
        
    return sorted(list(dbs))

functional_groups = get_functional_groups()

if not functional_groups:
    st.markdown('<div class="main-title">Semantic View</div>', unsafe_allow_html=True)
    st.info("💡 아직 생성된 시맨틱 모델이 없습니다. `builder.py`를 실행해 주세요.")
else:
    # [사이드바]
    st.sidebar.markdown("### 비즈니스 기능 단위")
    
    # 💡 [피드백 반영] format_func를 사용하여 사이드바 메뉴에서도 언더바를 공백으로 치환
    selected_group = st.sidebar.radio(
        "Semantic Model 선택", 
        functional_groups, 
        format_func=lambda x: x.replace("_", " ").title(),
        label_visibility="collapsed"
    )
    
    # 상단 헤더 영역 렌더링 (타이틀 + 포맷팅된 소제목)
    display_group_name = selected_group.replace("_", " ").title()
    st.markdown(f'''
        <div class="main-title">Semantic View</div>
        <div class="sub-title">비즈니스 기능: <strong>{display_group_name}</strong></div>
    ''', unsafe_allow_html=True)
    
    yaml_data = load_yaml(selected_group)
    
    if yaml_data:
        # 1. 포함 데이터베이스 배지 표시 생성
        detected_dbs = extract_databases(yaml_data)
        if detected_dbs:
            badge_html = "".join([f'<span class="db-badge">DB: {db}</span>' for db in detected_dbs])
            st.markdown(badge_html, unsafe_allow_html=True)
        else:
            st.markdown('<span class="db-badge">DB: 미지정 (기본 컨텍스트 사용)</span>', unsafe_allow_html=True)

        # 2. 대형 탭 구조 구조화
        tab1, tab2, tab3 = st.tabs([
            "데이터 사전 및 조인 관계 (Dictionary & Relations)", 
            "자연어 동의어 및 비즈니스 로직 (Synonyms & Logic)", 
            "원본 YAML 소스 (Raw Source)"
        ])
        
        # [Tab 1]: 데이터 사전 및 테이블 관계
        with tab1:
            col1, col2 = st.columns([1.3, 1], gap="medium")
            
            with col1:
                st.markdown("#### Table & Column Descriptions")
                descriptions = yaml_data.get("descriptions", [])
                
                if descriptions:
                    grouped_data = defaultdict(list)
                    for d in descriptions:
                        grouped_data[d.get('table', 'UNKNOWN_TABLE')].append(d)
                    
                    for table_name, columns in grouped_data.items():
                        with st.expander(f"Table: {table_name}", expanded=True):
                            st.markdown("<div style='background:#ffffff; border-radius:4px;'>", unsafe_allow_html=True)
                            for c in columns:
                                st.markdown(f"""
                                <div class="col-row">
                                    <div class="col-name">{c.get('column')}</div>
                                    <div class="col-meaning">{c.get('meaning')}</div>
                                </div>
                                """, unsafe_allow_html=True)
                            st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption("정의된 메타데이터 정보가 없습니다.")
                    
            with col2:
                st.markdown("#### Complex Relations (Joins)")
                relations = yaml_data.get("relations", [])
                if relations:
                    for r in relations:
                        st.markdown(f"""
                        <div class="relation-box">
                            <div style="font-family: monospace; font-size:0.9rem; background:#edf2f7; padding:6px 10px; border-radius:4px; margin-bottom:6px;">
                                <span style="color:#1e3a8a; font-weight:600;">{r.get('table_1')}</span>.{r.get('column_1')} 
                                <span style="color:#b91c1c; font-weight:bold;">=</span> 
                                <span style="color:#1e3a8a; font-weight:600;">{r.get('table_2')}</span>.{r.get('column_2')}
                            </div>
                            <div style="font-size:0.85rem; color:#475569;"> {r.get('meaning')}</div>
                        </div>
                        """, unsafe_allow_html=True)
                else:
                    st.caption("정의된 조인 관계가 없습니다.")

        # [Tab 2]: 자연어 동의어 매핑 및 복합 로직
        with tab2:
            col1, col2 = st.columns([1, 1.2], gap="medium")
            
            with col1:
                st.markdown("#### NL Synonyms (자연어 질의 매핑)")
                synonyms = yaml_data.get("synonyms", [])
                if synonyms:
                    color_map = {"value": "#2563eb", "column": "#16a34a", "condition": "#ea580c"}
                    
                    st.markdown("<div style='border: 1px solid #e2e8f0; border-radius:6px; overflow:hidden;'>", unsafe_allow_html=True)
                    for s in synonyms:
                        t = s.get("type", "unknown")
                        c = color_map.get(t, "#64748b")
                        st.markdown(f"""
                        <div class="synonym-row">
                            <span class="synonym-badge" style="background-color: {c};">{t}</span>
                            <span style="margin-left: 12px; font-weight:600; color:#1e293b; font-size:0.9rem;">"{s.get('nl_term')}"</span>
                            <span style="margin: 0 8px; color:#cbd5e1;">➔</span>
                            <code style="background:#f8fafc; color:#0f172a; padding:2px 6px; border-radius:4px; font-size:0.85rem; border:1px solid #e2e8f0;">{s.get('db_target')}</code>
                        </div>
                        """, unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
                else:
                    st.caption("정의된 동의어가 없습니다.")
                    
            with col2:
                st.markdown("#### Derived Metrics & Business Logic")
                biz_logic = yaml_data.get("biz_logic", [])
                if biz_logic:
                    for m in biz_logic:
                        with st.container(border=True):
                            st.markdown(f"**Metric: {m.get('metric_name')}**")
                            
                            sql_code = m.get('sql_logic', '').strip()
                            sql_lines = sql_code.split('\n')
                            
                            # 피드백 반영: SQL이 5줄을 초과할 경우 축약 및 전체보기 창 제공
                            if len(sql_lines) > 5:
                                preview_code = '\n'.join(sql_lines[:3])
                                st.code(preview_code + '\n\n-- [... 이하 생략 ...] --', language="sql")
                                with st.expander("전체 SQL 로직 펼치기", expanded=False):
                                    st.code(sql_code, language="sql")
                            else:
                                st.code(sql_code, language="sql")
                else:
                    st.caption("정의된 비즈니스 파생 로직이 없습니다.")

        # [Tab 3]: 원본 YAML 코드 확인
        with tab3:
            st.markdown("#### Snowflake Cortex Analyst YAML Source")
            st.code(yaml.dump(yaml_data, allow_unicode=True, sort_keys=False, default_flow_style=False), language="yaml")