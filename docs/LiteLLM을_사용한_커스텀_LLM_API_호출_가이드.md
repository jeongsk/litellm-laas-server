# LiteLLM을 사용한 커스텀 LLM API 호출 가이드

## Custom API 서버 (Custom Format)
Call your custom torch-serve / internal LLM APIs via LiteLLM
#### 참고
- For calling an openai-compatible endpoint, [여기](https://docs.litellm.ai/docs/providers/openai_compatible)로 이동합니다.
- For modifying incoming/outgoing calls on proxy, [여기](https://docs.litellm.ai/docs/proxy/call_hooks)로 이동합니다.
## Quick Start
```python
import litellm
from litellm import CustomLLM, completion, get_llm_provider

class MyCustomLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            mock_response="Hi!",
        )  # type: ignore

my_custom_llm = MyCustomLLM()
litellm.custom_provider_map = [  # 👈 KEY STEP - HANDLER 등록
    {"provider": "my-custom-llm", "custom_handler": my_custom_llm}
]
resp = completion(
    model="my-custom-llm/my-fake-model",
    messages=[{"role": "user", "content": "Hello world!"}],
)
assert resp.choices[0].message.content == "Hi!"
```
## OpenAI 프록시 사용법
#### 1. custom_handler.py 파일 설정
```python
import litellm
from litellm import CustomLLM, completion, get_llm_provider

class MyCustomLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            mock_response="Hi!",
        )  # type: ignore

    async def acompletion(self, *args, **kwargs) -> litellm.ModelResponse:
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            mock_response="Hi!",
        )  # type: ignore

my_custom_llm = MyCustomLLM()
```
#### 2. config.yaml에 추가
```yaml
model_list:
  - model_name: "test-model"
    litellm_params:
      model: "openai/text-embedding-ada-002"
  - model_name: "my-custom-model"
    litellm_params:
      model: "my-custom-llm/my-model"
litellm_settings:
  custom_provider_map:
    - {"provider": "my-custom-llm", "custom_handler": custom_handler.my_custom_llm}
```
```
litellm --config /path/to/config.yaml
```
#### 3. 테스트
```bash
curl -X POST 'http://0.0.0.0:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer sk-1234' \
-d '{
    "model": "my-custom-model",
    "messages": [{"role": "user", "content": "Say \"this is a test\" in JSON!"}]
}'
```
### 기대 응답
```json
{
  "id": "chatcmpl-06f1b9cd-08bc-43f7-9814-a69173921216",
  "choices": [
    {
      "finish_reason": "stop",
      "index": 0,
      "message": {
        "content": "Hi!",
        "role": "assistant",
        "tool_calls": null,
        "function_call": null
      }
    }
  ],
  "created": 1721955063,
  "model": "gpt-3.5-turbo",
  "object": "chat.completion",
  "system_fingerprint": null,
  "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
}
```
## 스트리밍 지원 추가
```python
import time
from typing import Iterator, AsyncIterator
from litellm.types.utils import GenericStreamingChunk, ModelResponse
from litellm import CustomLLM, completion, acompletion

class UnixTimeLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> ModelResponse:
        return completion(
            model="test/unixtime",
            mock_response=str(int(time.time())),
        )  # type: ignore

    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        return await acompletion(
            model="test/unixtime",
            mock_response=str(int(time.time())),
        )  # type: ignore

    def streaming(self, *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": str(int(time.time())),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        return generic_streaming_chunk  # type: ignore

    async def astreaming(self, *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        generic_streaming_chunk: GenericStreamingChunk = {
            "finish_reason": "stop",
            "index": 0,
            "is_finished": True,
            "text": str(int(time.time())),
            "tool_use": None,
            "usage": {"completion_tokens": 0, "prompt_tokens": 0, "total_tokens": 0},
        }
        yield generic_streaming_chunk  # type: ignore

unixtime = UnixTimeLLM()
```
## 이미지 생성
#### 1. custom_handler.py 파일 설정
```python
import litellm
from litellm import CustomLLM
from litellm.types.utils import ImageResponse, ImageObject
import time
from typing import Any, Optional, Union
from litellm.llms.base import BaseLLM
from httpx import AsyncClient as AsyncHTTPHandler

class MyCustomLLM(CustomLLM):
    async def aimage_generation(
        self, model: str, prompt: str, model_response: ImageResponse,
        optional_params: dict, logging_obj: Any,
        timeout: Optional[Union[float, AsyncHTTPHandler]] = None,
        client: Optional[AsyncHTTPHandler] = None,
    ) -> ImageResponse:
        return ImageResponse(
            created=int(time.time()),
            data=[ImageObject(url="https://example.com/image.png")],
        )

my_custom_llm = MyCustomLLM()
```
#### 2. config.yaml에 추가
```yaml
model_list:
  - model_name: "test-model"
    litellm_params:
      model: "openai/text-embedding-ada-002"
  - model_name: "my-custom-model"
    litellm_params:
      model: "my-custom-llm/my-model"
litellm_settings:
  custom_provider_map:
    - {"provider": "my-custom-llm", "custom_handler": custom_handler.my_custom_llm}
```
#### 3. 테스트
```bash
curl -X POST 'http://0.0.0.0:4000/v1/images/generations' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer sk-1234' \
-d '{
    "model": "my-custom-model",
    "prompt": "A cute baby sea otter"
}'
```
### 기대 응답
```json
{
  "created": 1721955063,
  "data": [{"url": "https://example.com/image.png"}]
}
```
## 추가 파라미터
```python
import litellm
from litellm import CustomLLM, completion, get_llm_provider

class MyCustomLLM(CustomLLM):
    def completion(self, *args, **kwargs) -> litellm.ModelResponse:
        assert kwargs["optional_params"] == {"my_custom_param": "my-custom-param"}  # 👈 검증
        return litellm.completion(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello world"}],
            mock_response="Hi!",
        )  # type: ignore

my_custom_llm = MyCustomLLM()
litellm.custom_provider_map = [
    {"provider": "my-custom-llm", "custom_handler": my_custom_llm}
]
resp = completion(model="my-custom-llm/my-model", my_custom_param="my-custom-param")
```
## 커스텀 핸들러 사양
```python
from litellm.types.utils import GenericStreamingChunk, ModelResponse, ImageResponse
from typing import Iterator, AsyncIterator, Any, Optional, Union
from litellm.llms.base import BaseLLM
from httpx import AsyncClient as AsyncHTTPHandler

class CustomLLMError(Exception):
    def __init__(self, status_code, message):
        self.status_code = status_code
        self.message = message
        super().__init__(self.message)

class CustomLLM(BaseLLM):
    def __init__(self) -> None:
        super().__init__()
    def completion(self, *args, **kwargs) -> ModelResponse:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
    def streaming(self, *args, **kwargs) -> Iterator[GenericStreamingChunk]:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
    async def acompletion(self, *args, **kwargs) -> ModelResponse:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
    async def astreaming(self, *args, **kwargs) -> AsyncIterator[GenericStreamingChunk]:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
    def image_generation(
        self, model: str, prompt: str, model_response: ImageResponse,
        optional_params: dict, logging_obj: Any,
        timeout: Optional[Union[float, AsyncHTTPHandler]] = None,
        client: Optional[HTTPHandler] = None,
    ) -> ImageResponse:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
    async def aimage_generation(
        self, model: str, prompt: str, model_response: ImageResponse,
        optional_params: dict, logging_obj: Any,
        timeout: Optional[Union[float, AsyncHTTPHandler]] = None,
        client: Optional[AsyncHTTPHandler] = None,
    ) -> ImageResponse:
        raise CustomLLMError(status_code=500, message="Not implemented yet!")
```