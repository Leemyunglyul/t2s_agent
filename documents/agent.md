### Workflow

```txt
[ START ]
          │
          ▼
    1. Query_Analysis ─────┐
          │                │ (Gemini 2.5 Flash 기반 분석)
          ▼                │
    2. Schema_Linking <────┘
          │ (SQLite 자동 스키마 추출 + LLM 필터링)
          ▼
    3. Data_Profiling
          │ (데이터 샘플링 및 형식 확인)
          ▼
┌── 4. SQL_Generation <───────────────────────────┐
│         │ (Template 주입 및 Global/Domain Rule 적용)
│         ▼                                       │
│   5. Execution ─────────────────┐               │
│         │ (SQL 실행 및 CSV 저장) │               │
│         ▼                       │               │
│   [ route_after_execution ]     │               │ "retry"
│         │                       │               │ (문법 에러 시 재작성)
│         ├─ "retry" ─────────────┘               │
│         │                                       │
│         └─ "critic" ──▶ 6. Critic (비평가) ───────┤
│                             │ (로직 검증: 누적합 여부 등)
│                             ▼                   │
│                   [ route_after_critic ]        │
│                             │                   │
│                             ├─ "retry" ─────────┘
│                             │ (로직 오류 시 비평 결과 들고 재작성)
▼                             ▼
[ END ] <───────────────── "end" (최종 정답 통과 또는 Max Step 도달)
```

### Workflow

```txt
[ START ]
    │
    ▼
1. Query_Analysis ─────┐
    │                  │ (사용자 의도, 키워드, 실행 계획 분석)
    ▼                  │
2. Schema_Linking <────┘
    │ (DB 스키마 조회 및 필요 테이블/컬럼 매핑)
    ▼
3. Data_Profiling
    │ (데이터 샘플링을 통한 실제 값 형식 확인)
    ▼
4. SQL_Writer
    │ (최초 SQL 작성 및 [EXPLORE SQL] 또는 [FINAL SQL] 태그 생성)
    ▼
┌▶ 5. Execution ──────────────────────────────┐
│   │ (SQL 실행, sqlglot 구문 검사, 결과 Preview) │
│   │                                         │
│   ▼                                         │
│ [ route_after_execution ]                   │
│   │                                         │
│   ├─ "retry" (에러 발생 시) ───────────────────┼──▶ 7. SQL_Modifier
│   │                                         │     │ (에러/반려 피드백 기반 쿼리 수정)
│   └─ "critic" (성공 및 FINAL SQL인 경우) ───────┤     │
│                                             │     ▼
│ 6. Critic (비평가)                          │  (Execution으로 다시 루프)
│   │ (결과 논리 검증 및 벤치마크 룰 체크)      │
│   ▼                                         │
│ [ route_after_critic ]                      │
│   │                                         │
│   ├─ "retry" (Critic 반려 시) ────────────────┘
│   │
│   └─ "end" (Critic 통과 시) ────────────────┐
│                                             │
└─────────────────────────────────────────────┼─────▶ [ END ]
                                              │ (또는 Max Step 10회 도달 시 강제 종료)
```
