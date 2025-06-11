#!/usr/bin/env python3
"""
LaaS 프록시 서버의 스트리밍 기능을 테스트하는 스크립트
"""

import asyncio
import os
from dotenv import load_dotenv
from laas_proxy_server import LaaSProxy

# .env 파일 로드
load_dotenv()

async def test_streaming():
    """스트리밍 기능 테스트"""
    print("=== LaaS 프록시 스트리밍 테스트 시작 ===")
    
    # 환경변수 확인
    required_vars = ["LAAS_PROJECT_CODE", "LAAS_API_KEY", "LAAS_PRESET_HASH"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ 필수 환경변수가 설정되지 않았습니다: {', '.join(missing_vars)}")
        print("   .env 파일을 확인해주세요.")
        return
    
    try:
        # LaaSProxy 인스턴스 생성
        proxy = LaaSProxy()
        print("✅ LaaSProxy 인스턴스 생성 완료")
        
        # 테스트 메시지
        test_messages = [
            {"role": "user", "content": "안녕하세요! 간단한 인사말을 해주세요."}
        ]
        
        print("\n--- 일반 요청 테스트 ---")
        # 일반 요청 테스트
        response = await proxy.acompletion(
            model="test-model",
            messages=test_messages,
            stream=False
        )
        print(f"✅ 일반 응답: {response.choices[0].message.content[:100]}...")
        
        print("\n--- 스트리밍 요청 테스트 ---")
        # 스트리밍 요청 테스트
        chunk_count = 0
        full_content = ""
        
        async for chunk in proxy.astreaming(
            model="test-model",
            messages=test_messages,
            optional_params={}
        ):
            chunk_count += 1
            if chunk["text"]:
                content = chunk["text"]
                full_content += content
                print(f"청크 {chunk_count}: '{content}'")
            
            if chunk["finish_reason"] == "stop":
                print(f"✅ 스트리밍 완료 - 총 {chunk_count}개 청크")
                if chunk["usage"]:
                    print(f"   토큰 사용량: {chunk['usage']['total_tokens']}")
                break
        
        print(f"\n전체 스트리밍 내용: {full_content}")
        print("\n=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_streaming())
