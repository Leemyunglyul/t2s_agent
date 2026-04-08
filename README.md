# LangGraph Text-to-SQL Agent

이 프로젝트는 LangGraph와 Google Gemini 모델을 활용하여 사용자의 자연어 질문을 SQL 쿼리로 변환하고, SQLite 데이터베이스에서 실행하여 결과를 도출하는 에이전트 시스템입니다.

## 주요 기능

- **다중 에이전트 아키텍처**: Planner(계획), Schema Linker, Writer, Modifier, Critic 역할 분리
- **자동 스키마 추출**: DB 파일에서 메타데이터 자동 추출 및 필터링
- **사전 구문 검증**: `sqlglot`을 활용하여 위험한 쿼리 차단 및 Syntax Error 사전 방지
- **자가 교정(Self-Correction)**: 실행 에러 또는 논리적 오류 발생 시 원인을 분석하여 쿼리 수정 후 재실행

## 실행 방법

1. 의존성 설치: `pip install -r requirements.txt`
2. 환경 변수 설정 (GCP 인증 또는 API 키)
3. 메인 스크립트 실행: `python main.py ...`
