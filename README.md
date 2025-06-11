# LiteLLM-LaaS 커스텀 핸들러

이 프로젝트는 Wanted LaaS API를 LiteLLM의 커스텀 핸들러로 통합하여 OpenAI 호환 API로 서비스하는 모듈입니다.

## 📋 개요

- LaaS API를 LiteLLM CustomLLM으로 통합
- OpenAI API 스펙 호환
- 비동기 처리 지원 (httpx 사용)
- 멀티모달 메시지(이미지, 문서) 지원
- LaaS API의 params 기능 지원
- 표준 로깅 시스템 통합

## ⚙️ 전제 조건

- Python 3.8+
- uv 패키지 관리자 (설치 방법)
  - **macOS/Linux**:
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
  - **Windows**:
    ```powershell
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```

## 📥 설치 방법

```bash
# 리포지토리 복제
git clone https://github.com/your-repo/litellm-laas-server.git
cd litellm-laas-server

# 프로젝트 초기화 및 종속성 설치
uv sync
```

> 📌 **uv sync 명령어**: 
> - 가상 환경(.venv)이 없으면 자동 생성
> - pyproject.toml에 정의된 의존성 설치
> - lockfile(uv.lock) 자동 생성으로 재현 가능한 빌드 보장

수동으로 가상 환경을 활성화하려면:
```bash
# 가상 환경 활성화
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate    # Windows
```

## 🔧 환경 설정

`.env` 파일 생성 후 LaaS 인증 정보 및 프리셋 해시 추가:

```env
LAAS_PROJECT_CODE=your_project_code
LAAS_API_KEY=your_api_key
LAAS_PRESET_HASH=your_preset_hash
```

## 🚀 사용 방법

### 1. LiteLLM 프록시 서버 실행

```bash
# config.yaml을 사용하여 LiteLLM 프록시 서버 실행
uv run litellm --config config.yaml

# 또는 직접 실행
litellm --config config.yaml
```

### 2. API 호출

#### OpenAI 클라이언트 사용

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:4000",
    api_key="sk-1234"  # 더미 키
)

# 기본 채팅 요청
response = client.chat.completions.create(
    model="claude-3.5-sonnet",
    messages=[{"role": "user", "content": "안녕하세요!"}]
)
print(response.choices[0].message.content)
```

#### 이미지 포함 요청

```python
response = client.chat.completions.create(
    model="claude-3.5-sonnet",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "image_url",
                "image_url": {
                    "url": "https://static.wanted.co.kr/images/wdes/0_4.d217341b.jpg"
                }
            },
            {
                "type": "text",
                "text": "이 이미지에 대해 설명해주세요."
            }
        ]
    }]
)
```

#### PDF 문서 포함 요청

```python
response = client.chat.completions.create(
    model="claude-3.5-sonnet",
    messages=[{
        "role": "user",
        "content": [
            {
                "type": "document",
                "document_url": {
                    "url": "data:application/pdf;base64,{base64_pdf_data}"
                }
            },
            {
                "type": "text",
                "text": "이 문서의 내용을 요약해주세요."
            }
        ]
    }]
)
```

#### cURL 사용

```bash
curl -X POST 'http://localhost:4000/chat/completions' \
-H 'Content-Type: application/json' \
-H 'Authorization: Bearer sk-1234' \
-d '{
    "model": "claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "안녕하세요!"}]
}'
```

### 3. 직접 핸들러 테스트

```bash
# 커스텀 핸들러 직접 테스트
uv run python test_laas_handler.py
```

## 🧪 테스트 실행

```bash
# 전체 테스트 실행
uv run pytest test_api.py -v

# 커스텀 핸들러 테스트
uv run python test_laas_handler.py

# 특정 테스트 실행
uv run pytest test_api.py::test_valid_request
```

> 📌 **uv run 명령어**: 프로젝트 가상 환경에서 명령어를 실행합니다.

## 📝 설정 파일 구조

### config.yaml

```yaml
model_list:
  - model_name: claude-3.5-sonnet
    litellm_params:
      model: laas/claude-3.5-sonnet
  - model_name: claude-3.7-sonnet
    litellm_params:
      model: laas/claude-3.7-sonnet
  - model_name: claude-4-sonnet
    litellm_params:
      model: laas/claude-4-sonnet
      
litellm_settings:
  set_verbose: True
  custom_provider_map:
    - provider: "laas"
      custom_handler: laas_proxy_server.laas_proxy
```

## 🔧 커스텀 핸들러 구조

### LaaSProxy 클래스

```python
from litellm import CustomLLM
from laas_proxy_server import LaaSProxy

# 커스텀 핸들러 인스턴스
laas_proxy = LaaSProxy()

# LiteLLM에서 자동으로 호출되는 메서드들:
# - completion(): 동기 호출
# - acompletion(): 비동기 호출 (권장)
```

### 주요 기능

1. **비동기 처리**: `httpx`를 사용한 비동기 HTTP 클라이언트
2. **메시지 변환**: OpenAI 형식을 LaaS API 형식으로 변환
3. **에러 처리**: LiteLLM의 `CustomLLMError` 사용
4. **로깅**: 상세한 디버그 로깅 지원
5. **파라미터 매핑**: `optional_params`를 LaaS API의 `params`로 매핑

## 🚀 배포 방법

### 1. 로컬 배포

```bash
# 환경변수 설정
export LAAS_PROJECT_CODE=your_project_code
export LAAS_API_KEY=your_api_key
export LAAS_PRESET_HASH=your_preset_hash

# LiteLLM 프록시 서버 실행
uv run litellm --config config.yaml --port 4000
```

### 2. Docker 배포

#### Docker Compose 사용 (권장)

```bash
# .env 파일 생성 후 환경변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 서비스 빌드 및 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down
```

#### Docker 직접 사용

```bash
# 이미지 빌드
docker build -t litellm-laas-server .

# 컨테이너 실행
docker run -d \
  --name litellm-laas-server \
  -p 4000:4000 \
  -e LAAS_PROJECT_CODE=your_project_code \
  -e LAAS_API_KEY=your_api_key \
  -e LAAS_PRESET_HASH=your_preset_hash \
  litellm-laas-server

# 로그 확인
docker logs -f litellm-laas-server
```

### 3. 헬스체크

```bash
# 서버 상태 확인
curl http://localhost:4000/health

# 모델 목록 확인
curl http://localhost:4000/v1/models
```

## 🔍 LaaS API 기능 지원

### 지원되는 기능

1. **기본 채팅**: 텍스트 메시지 처리
2. **가변값 처리**: LaaS API의 `params` 필드 지원
3. **이미지 처리**: URL 및 base64 이미지 지원
4. **PDF 문서**: base64 인코딩된 PDF 처리
5. **멀티모달**: 텍스트, 이미지, 문서 혼합 메시지

### 제한 사항

1. **스트리밍 미지원**: LaaS API가 스트리밍을 지원하지 않음
2. **도구 호출 미지원**: Function calling 기능 없음
3. **역할 제한**: `user`, `assistant`, `system`만 허용
4. **이미지 제한**: 
   - 지원 형식: JPEG, PNG
   - 최대 크기: 4MB
   - 메시지당 최대 3개
   - 권장 해상도: 1568px 이하
5. **PDF 제한**:
   - 최대 용량: 32MB
   - 최대 페이지: 20장
   - base64 인코딩만 지원

## 📊 로깅 설정

```python
import logging

# DEBUG 레벨 로깅 활성화
logging.basicConfig(level=logging.DEBUG)

# 또는 config.yaml에서 설정
litellm_settings:
  set_verbose: True
```

## 🛠️ 개발 및 디버깅

### 환경변수 확인

```bash
# 필수 환경변수 확인
echo $LAAS_PROJECT_CODE
echo $LAAS_API_KEY
echo $LAAS_PRESET_HASH
```

### 로그 레벨 조정

```python
# laas_proxy_server.py에서 로그 레벨 변경
logging.basicConfig(level=logging.DEBUG)  # 상세 로그
logging.basicConfig(level=logging.INFO)   # 기본 로그
```

### 직접 테스트

```python
import asyncio
from laas_proxy_server import LaaSProxy

async def test():
    proxy = LaaSProxy()
    response = await proxy.acompletion(
        model="claude-3.5-sonnet",
        messages=[{"role": "user", "content": "테스트"}]
    )
    print(response.choices[0].message.content)

asyncio.run(test())
```

## 📚 참고 문서

- [LiteLLM 커스텀 핸들러 가이드](https://docs.litellm.ai/docs/providers/custom_llm_server)
- [LaaS API 사용 방법](docs/LaaS_API_사용_방법.md)
- [LiteLLM을 사용한 커스텀 LLM API 호출 가이드](docs/LiteLLM을_사용한_커스텀_LLM_API_호출_가이드.md)
