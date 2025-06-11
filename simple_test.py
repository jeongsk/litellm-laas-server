#!/usr/bin/env python3
"""
간단한 스트리밍 테스트
"""

import asyncio
import sys
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

async def simple_test():
    """간단한 테스트"""
    print("=== 간단한 스트리밍 테스트 ===")
    
    # 환경변수 확인
    project_code = os.getenv("LAAS_PROJECT_CODE")
    api_key = os.getenv("LAAS_API_KEY")
    preset_hash = os.getenv("LAAS_PRESET_HASH")
    
    print(f"LAAS_PROJECT_CODE: {'SET' if project_code else 'NOT SET'}")
    print(f"LAAS_API_KEY: {'SET' if api_key else 'NOT SET'}")
    print(f"LAAS_PRESET_HASH: {'SET' if preset_hash else 'NOT SET'}")
    
    if not all([project_code, api_key, preset_hash]):
        print("❌ 환경변수가 설정되지 않았습니다.")
        return
    
    try:
        from laas_proxy_server import LaaSProxy
        print("✅ LaaSProxy 모듈 임포트 성공")
        
        proxy = LaaSProxy()
        print("✅ LaaSProxy 인스턴스 생성 성공")
        
        # 간단한 메시지 테스트
        test_messages = [{"role": "user", "content": "Hello"}]
        
        print("--- 스트리밍 테스트 시작 ---")
        chunk_count = 0
        
        async for chunk in proxy.astreaming(
            model="test-model",
            messages=test_messages,
            optional_params={}
        ):
            chunk_count += 1
            print(f"청크 {chunk_count}: {chunk}")
            
            if chunk.get("finish_reason") == "stop":
                print("✅ 스트리밍 완료")
                break
                
            if chunk_count > 10:  # 안전장치
                print("⚠️ 최대 청크 수 도달")
                break
        
        print("=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())
