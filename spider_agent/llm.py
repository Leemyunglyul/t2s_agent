import logging
import os
from typing import Dict, Tuple, Any
from google import genai
from google.genai import types

logger = logging.getLogger("langgraph_agent")

"""
client = genai.Client(
    vertexai=True,
    project="project-9bda5f3a-eeae-4c70-b8a",  # 예: "my-awesome-project-123456"
    location="us-central1"            # 리전 설정 (us-central1 추천)
)
"""

client = genai.Client(
    api_key=os.environ.get("GOOGLE_API_KEY") 
)

def call_llm(params: Dict[str, Any]) -> Tuple[bool, str]:
    model_name = params.get("model", "gemini-2.5-flash")  # 기본 모델 설정, 필요에 따라 변경 가능
    messages = params.get("messages", [])
    temperature = params.get("temperature", 0.0)
    max_tokens = params.get("max_tokens", 8192)
    
    try:
        logger.debug(f"Gemini API 호출 시작 (Model: {model_name})")
        
        system_instruction = None
        gemini_contents = []
        
        # 1. 메시지 파싱
        for msg in messages:
            role = msg.get("role")
            content = msg.get("content")
            
            if role == "system":
                system_instruction = content
            elif role == "user":
                gemini_contents.append(
                    types.Content(role="user", parts=[types.Part.from_text(text=content)])
                )
            elif role in ["assistant", "model"]:
                gemini_contents.append(
                    types.Content(role="model", parts=[types.Part.from_text(text=content)])
                )
        
        # 2. 설정값(Config) 세팅
        config_args = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        if system_instruction:
            config_args["system_instruction"] = system_instruction
            
        # "application/json"이 들어오면 모델이 무조건 JSON 형식으로만 대답하게 강제
        if "response_mime_type" in params:
            config_args["response_mime_type"] = params["response_mime_type"]
            
        config = types.GenerateContentConfig(**config_args)
        
        # 3. 모델 호출
        response = client.models.generate_content(
            model=model_name,
            contents=gemini_contents,
            config=config
        )
        
        try:
            result_text = response.text if response.text else ""
        except ValueError:
            # 안전 필터 등에 의해 텍스트 출력이 차단된 경우
            logger.error("Gemini API 출력 차단 (Safety Filter).")
            return False, "ERROR: Output blocked by safety settings."
        
        return True, result_text
        
    except Exception as e:
        error_msg = f"Gemini API 에러: {str(e)}"
        logger.error(error_msg)
        return False, error_msg 