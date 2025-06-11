#!/usr/bin/env python3
"""
LaaS API를 LiteLLM CustomLLM으로 제공하는 커스텀 핸들러
"""

import os
import logging
import asyncio
from typing import List, Dict, Union, AsyncIterator
from dotenv import load_dotenv
import httpx
import litellm
from litellm import CustomLLM
from litellm.types.utils import ModelResponse, GenericStreamingChunk


# .env 파일에서 환경 변수 로드
load_dotenv()

# 상수 정의
DEFAULT_TIMEOUT = 600.0  # 10분 (초 단위)

# 로거 설정
os.environ["LITELLM_LOG"] = os.getenv("LITELLM_LOG", "INFO")
logger = logging.getLogger(__name__)


class CustomLLMError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)


class LaaSProxy(CustomLLM):
    def __init__(self):
        super().__init__()

        self.base_url = "https://api-laas.wanted.co.kr/api/preset/v2"

        # 환경변수 로드
        self.project_code = os.getenv("LAAS_PROJECT_CODE")
        self.api_key = os.getenv("LAAS_API_KEY")
        self.preset_hash = os.getenv("LAAS_PRESET_HASH")

        # 환경변수 확인 로그
        logger.info(
            f"LAAS_PROJECT_CODE 설정됨: {'예' if self.project_code else '아니오'}"
        )
        logger.info(f"LAAS_API_KEY 설정됨: {'예' if self.api_key else '아니오'}")
        logger.info(
            f"LAAS_PRESET_HASH 설정됨: {'예' if self.preset_hash else '아니오'}"
        )

        if not self.project_code or not self.api_key:
            missing = []
            if not self.project_code:
                missing.append("LAAS_PROJECT_CODE")
            if not self.api_key:
                missing.append("LAAS_API_KEY")
            if not self.preset_hash:
                missing.append("LAAS_PRESET_HASH")
            error_msg = f"Missing Laas credentials in environment variables: {', '.join(missing)}"
            logger.error(error_msg)
            raise CustomLLMError(status_code=500, message=error_msg)

    def _validate_messages(self, messages: List[Dict]) -> None:
        """메시지 역할 유효성 검사"""
        logger.debug("메시지 역할 유효성 검사 시작")
        valid_roles = {"user", "assistant", "system"}
        for i, msg in enumerate(messages):
            if msg.get("role") not in valid_roles:
                logger.error(f"잘못된 역할 발견 - 메시지 {i}: '{msg['role']}'")
                raise CustomLLMError(
                    status_code=400,
                    message=f"Invalid role '{msg['role']}'. Only 'user', 'assistant', 'system' allowed",
                )
        logger.debug("메시지 역할 유효성 검사 완료")

    def _validate_tool_calls(self, messages: List[Dict]) -> None:
        """도구 호출 지원 확인"""
        if any("tool_calls" in msg for msg in messages):
            logger.warning(
                "도구 호출 요청이 거부됨 - LaaS API는 도구 호출을 지원하지 않음"
            )
            raise CustomLLMError(
                status_code=400, message="LaaS API does not support tool calls"
            )

    def completion(self, *args, **kwargs) -> ModelResponse:
        """동기 completion 메서드 - 비동기 메서드 호출"""
        import asyncio

        return asyncio.run(self.acompletion(*args, **kwargs))

    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        """비동기 completion 메서드"""
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])
        optional_params = kwargs.get("optional_params", {})

        logger.info(
            f"Chat completion 요청 시작 - 모델: {model}, 메시지 수: {len(messages)}"
        )
        logger.debug(f"요청 파라미터: {optional_params}")

        # 스트리밍 요청은 별도의 astreaming 메서드에서 처리
        if kwargs.get("stream", False):
            logger.error("스트리밍 요청은 astreaming() 메서드를 사용해야 합니다")
            raise CustomLLMError(
                status_code=400,
                message="Streaming requests should use astreaming() method",
            )

        # 유효성 검사
        self._validate_messages(messages)
        self._validate_tool_calls(messages)

        try:
            # LaaS API 호출하여 전체 응답 받기
            response_data = await self._call_laas_api(model, messages, optional_params)

            # 응답을 LiteLLM ModelResponse로 변환
            model_response = self._transform_to_model_response(response_data, model)

            return model_response

        except Exception as e:
            logger.error(f"예상치 못한 오류 발생: {str(e)}")
            raise

    async def astreaming(self, *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        """비동기 스트리밍 메서드 - LiteLLM CustomLLM 표준 인터페이스"""
        model = kwargs.get("model", "")
        messages = kwargs.get("messages", [])
        optional_params = kwargs.get("optional_params", {})

        # 유효성 검사
        self._validate_messages(messages)
        self._validate_tool_calls(messages)

        try:
            full_response_data = await self._call_laas_api(
                model, messages, optional_params
            )

            # 응답 내용 추출
            content = full_response_data["choices"][0]["message"]["content"]
            usage = full_response_data.get("usage", {})

            # 응답을 청크로 분할하여 스트리밍
            async for chunk in self._stream_generic_chunks(content, usage):
                yield chunk

        except Exception as e:
            logger.error(f"스트리밍 처리 중 오류 발생: {str(e)}")
            raise

    async def _stream_generic_chunks(
        self, content: str, usage: Dict
    ) -> AsyncIterator[GenericStreamingChunk]:
        """응답 내용을 GenericStreamingChunk로 분할하여 스트리밍"""

        # 응답을 문자 단위로 분할 (더 세밀한 스트리밍)
        chunk_size = max(1, len(content) // 30)  # 약 30개의 청크로 분할

        for i in range(0, len(content), chunk_size):
            chunk_content = content[i : i + chunk_size]

            # GenericStreamingChunk 생성
            generic_chunk: GenericStreamingChunk = {
                "finish_reason": None,
                "index": 0,
                "is_finished": False,
                "text": chunk_content,
                "tool_use": None,
                "usage": None,
            }

            yield generic_chunk

            # 자연스러운 스트리밍을 위한 짧은 지연
            await asyncio.sleep(0.01)

        # 마지막 청크 - 종료 신호와 사용량 정보
        final_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": "",
            "tool_use": None,
            "usage": {
                "completion_tokens": usage.get("completion_tokens", 0),
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0),
            },
        }

        yield final_chunk

    async def _call_laas_api(
        self, model: str, messages: List[Dict], optional_params: Dict
    ) -> Dict:
        """LaaS API 호출하여 전체 응답 받기"""
        # 요청 헤더 준비
        headers = {
            "Content-Type": "application/json",
            "project": self.project_code,
            "apiKey": self.api_key,
        }

        # 메시지 변환
        transformed_messages = self._transform_messages(messages)

        # optional_params에서 LaaS API의 params로 매핑
        laas_params = {}
        if optional_params:
            for key, value in optional_params.items():
                if key not in ["model", "messages", "stream"]:
                    laas_params[key] = value

        # LaaS API 요청 데이터 구성
        data = {
            **laas_params,
            "hash": self.preset_hash,
            "messages": transformed_messages,
        }

        try:
            api_url = f"{self.base_url}/chat/completions"

            async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
                response = await client.post(api_url, headers=headers, json=data)

            response.raise_for_status()
            return response.json()

        except httpx.TimeoutException as e:
            logger.error(f"LaaS API 타임아웃 오류: {str(e)}")
            raise CustomLLMError(status_code=504, message=f"LaaS API timeout: {str(e)}")
        except httpx.ConnectError as e:
            logger.error(f"LaaS API 연결 오류: {str(e)}")
            raise CustomLLMError(
                status_code=503, message=f"LaaS API connection error: {str(e)}"
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"LaaS API HTTP 오류: {str(e)}, 응답: {e.response.text}")
            raise CustomLLMError(
                status_code=e.response.status_code,
                message=f"LaaS API HTTP error: {str(e)}",
            )
        except Exception as e:
            logger.error(f"LaaS API 호출 중 오류: {str(e)}")
            raise CustomLLMError(status_code=500, message=f"LaaS API error: {str(e)}")


    def _transform_messages(self, messages: List[Dict]) -> List[Dict]:
        """메시지를 LaaS API 형식으로 변환"""
        transformed = []

        for i, msg in enumerate(messages):
            new_msg = {"role": msg["role"]}

            if isinstance(msg["content"], str):
                new_msg["content"] = [{"type": "text", "text": msg["content"]}]
            elif isinstance(msg["content"], list):
                new_msg["content"] = [
                    self._transform_content_item(item) for item in msg["content"]
                ]
            else:
                # 다른 형식의 콘텐츠는 그대로 유지
                new_msg["content"] = msg["content"]

            transformed.append(new_msg)
        return transformed

    def _transform_content_item(self, item: Union[str, Dict]) -> Dict:
        """콘텐츠 항목을 LaaS API 형식으로 변환"""
        if isinstance(item, str):
            return {"type": "text", "text": item}

        if isinstance(item, dict):
            # 이미지 URL 처리
            if item.get("type") == "image_url" and "image_url" in item:
                return {
                    "type": "image_url",
                    "image_url": {"url": item["image_url"]["url"]},
                }

            # 문서 처리
            if item.get("type") == "document" and "document_url" in item:
                return {
                    "type": "document",
                    "document_url": {"url": item["document_url"]["url"]},
                }

            # 텍스트 처리
            if item.get("type") == "text" and "text" in item:
                return item

        return item

    def _transform_to_model_response(self, response: Dict, model: str) -> ModelResponse:
        """LaaS API 응답을 LiteLLM ModelResponse로 변환"""

        try:
            # 응답 내용 추출
            content = response["choices"][0]["message"]["content"]

            # 사용량 정보 추출
            usage = response.get("usage", {})

            # LiteLLM ModelResponse 생성
            model_response = ModelResponse(
                id=response.get("id", ""),
                object="chat.completion",
                created=response.get("created", 0),
                model=model,
                choices=[
                    litellm.Choices(
                        index=0,
                        message=litellm.Message(role="assistant", content=content),
                        finish_reason="stop",
                    )
                ],
                usage=litellm.Usage(
                    prompt_tokens=usage.get("prompt_tokens", 0),
                    completion_tokens=usage.get("completion_tokens", 0),
                    total_tokens=usage.get("total_tokens", 0),
                )
            )

            return model_response

        except KeyError as e:
            raise CustomLLMError(
                status_code=500, message=f"Invalid response structure: {str(e)}"
            )
        except Exception as e:
            raise CustomLLMError(
                status_code=500, message=f"Response transformation error: {str(e)}"
            )


# LaaS 프록시 인스턴스 생성
laas = LaaSProxy()
