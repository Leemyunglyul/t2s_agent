import operator
from typing import TypedDict, Annotated, List, Dict, Any, Optional

class AgentState(TypedDict):
    # 1. 태스크 기본 정보
    question: str              # 사용자의 원본 질문 (instruction)
    analyzed_query: Dict[str, Any]
    working_dir: str           # 현재 작업 디렉토리 경로
    
    # 2. 컨텍스트
    retrieved_schema: str      # RAG로 검색해온 DB 스키마 및 메타데이터 정보
    
    profiled_data: str # 프로파일링 데이터 저장 공간
    
    # 3. 대화 기록 및 메모리
    history_messages: Annotated[List[Dict[str, Any]], operator.add] 
    
    # 4. 현재 스텝의 생성 결과 
    current_thought: Optional[str]   # LLM의 현재 사고 과정 (Thought)
    current_action: Optional[str]    # 파싱된 액션 타입 (예: LOCAL_DB_SQL, Bash)
    generated_code: Optional[str]    # 실제로 실행할 SQL 쿼리문 또는 코드
    
    # 5. 환경(Env) 실행 결과
    observation: str           # DB 쿼리 실행 결과 또는 에러 로그
    has_error: bool            # 쿼리 실행 중 에러가 발생했는지 여부 (이 값으로 라우팅 분기)
    
    # 6. 무한 루프 제어 변수
    step_count: int            # 전체 진행 스텝 수 (기존 max_steps 도달 시 강제 종료용)
    retry_count: int           # 파싱 에러나 동일 액션 반복 시 증가하는 카운트
    max_steps: int             # 최대 허용 스텝 수
    
    instance_id: str  
    db_id: str        
    
    execution_history: List[Dict[str, str]] 
    is_final_answer: bool
    
    run_name: str 