#!/usr/bin/env python3
"""
디버그 테스트 스크립트
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

def check_env_vars():
    """환경변수 확인"""
    print("=== 환경변수 확인 ===")
    
    project_code = os.getenv("LAAS_PROJECT_CODE")
    api_key = os.getenv("LAAS_API_KEY")
    preset_hash = os.getenv("LAAS_PRESET_HASH")
    
    print(f"LAAS_PROJECT_CODE: {'설정됨' if project_code else '미설정'}")
    print(f"LAAS_API_KEY: {'설정됨' if api_key else '미설정'}")
    print(f"LAAS_PRESET_HASH: {'설정됨' if preset_hash else '미설정'}")
    
    if not all([project_code, api_key, preset_hash]):
        print("❌ 일부 환경변수가 설정되지 않았습니다.")
        return False
    
    print("✅ 모든 환경변수가 설정되었습니다.")
    return True

async def test_laas_proxy():
    """LaaSProxy 테스트"""
    print("\n=== LaaSProxy 테스트 ===")
    
    try:
        from laas_proxy_server import LaaSProxy
        print("✅ LaaSProxy 모듈 임포트 성공")
        
        proxy = LaaSProxy()
        print("✅ LaaSProxy 인스턴스 생성 성공")
        
        # 간단한 메시지 테스트
        test_messages = [{"role": "user", "content": "안녕하세요"}]
        
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
                
            if chunk_count > 5:  # 안전장치
                print("⚠️ 최대 청크 수 도달")
                break
        
        print("=== 테스트 완료 ===")
        
    except Exception as e:
        print(f"❌ 오류 발생: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    """메인 함수"""
    print("디버그 테스트 시작")
    
    # 환경변수 확인
    if not check_env_vars():
        sys.exit(1)
    
    # LaaSProxy 테스트
    asyncio.run(test_laas_proxy())

if __name__ == "__main__":
    main()
