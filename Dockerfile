FROM python:3.11-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 업데이트 및 필요한 패키지 설치
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# uv 설치
RUN pip install uv

# 프로젝트 파일 복사
COPY pyproject.toml uv.lock* ./

# 의존성 설치
RUN uv sync --frozen

# 애플리케이션 코드 복사
COPY . .

# 파이썬이 현재 디렉토리에서 모듈을 찾을 수 있도록 PYTHONPATH 설정
ENV PYTHONPATH /app

# 로그 디렉토리 생성
RUN mkdir -p /app/logs

# 포트 노출 (Docker 내부 포트 고정)
EXPOSE 4000

# 애플리케이션 실행 (LiteLLM 프록시 서버를 config.yaml로 실행)
CMD ["uv", "run", "litellm", "--config", "/app/config.yaml", "--port", "4000", "--host", "0.0.0.0"]
