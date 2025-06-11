이 예제 코드는 LaaS에서 preset API를 활용하는 방법을 설명합니다.

## 1\. 배포된 프리셋 조회

- 배포된 프리셋의 정보를 조회 할 때 사용
  

## 2\. Chat 호출

- 배포된 프리셋을 사용하여 LLM의 chat API를 호출

### case1) 기본 프리셋 호출

위의 코드는 에디터를 다음과 같이 설정 했을 때와 동일하게 처리됩니다.

![image-20241105-043122.png](https://wanteddev.github.io/laas-docs/img/image-20241105-043122.png)

  

### case2) 가변 포함 프리셋 호출

- 가변값 `question` 을 `원티드랩` 으로 설정한 예시입니다.

API 호출시 프리셋의 가변값이, `params` 에 전달한 값으로 설정되어 호출됩니다.  
에디터에서 설정한 값은 API 호출시 사용 되지 않기 때문에 `params` 를 설정하지 않을 경우, 빈 값으로 설정되어 호출됩니다.

![image-20241105-050819.png](https://wanteddev.github.io/laas-docs/img/image-20241105-050819.png)

### case3) 추가 메시지를 전달하는 호출

- 배포된 프리셋에는 시스템 메시지만 설정 되어 있다는 것을 가정하고 있습니다.
- 배포된 프리셋에 `원티드의 서비스를 알려줘` 라는 유저 메시지를 추가하는 예시입니다.

프리셋에 포함시키지 않은 메시지를 추가할때 사용됩니다.  
다음과 같이 유저 메시지를 추가한 것과 동일합니다.

![image-20241105-144518.png](https://wanteddev.github.io/laas-docs/img/image-20241105-144518.png)

  

### case4) 추가 메시지에 이미지를 포함한 호출

- 유저 메시지에 이미지를 포함하는 예시입니다.
- image\_url에 image가 저장된 url을 설정한 예시입니다.

```markdown
import requests

def create_chat_completion_with_image():
    project_code = "YOUR_PROJECT_CODE"
    api_key = "YOUR_API_KEY"
    hash = "YOUR_PRESET_HASH"

    # Set request url
    laas_chat_url = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"

    # Set the headers
    headers = {
        "project": project_code,
        "apiKey": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }

    # Set the request
    data = {
        "hash": hash,
        "messages": [
            {
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
                        "text": "해당 이미지의 기업은 어디인지 알려주세요."
                    }
                ]
            }
        ]
    }

    try:
        # Make the POST request
        response = requests.post(laas_chat_url, headers=headers, json=data)

        # Print the response or handle it as needed
        print("Response:", response.text)

    except Exception as e:
        # Handle any exceptions
        print("An error occurred:", e)
```

유저 메시지에 이미지를 추가할때 사용됩니다.  
다음과 같이 유저 메시지를 추가한 것과 동일합니다.

![image-20241105-152558.png](https://wanteddev.github.io/laas-docs/img/image-20241105-152558.png)

  
- image\_url에 base64 인코딩 이미지 데이터를 설정한 예시입니다.
- base64 데이터는 [**data URLs**](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs) 포맷으로 구성되어야 합니다.

```markdown
import requests

def create_chat_completion_with_base64_image():
    project_code = "YOUR_PROJECT_CODE"
    api_key = "YOUR_API_KEY"
    hash = "YOUR_PRESET_HASH"

    # Set request url
    laas_chat_url = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"

    # Set the headers
    headers = {
        "project": project_code,
        "apiKey": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }

    # Set the request
    data = {
        "hash": hash,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": "data:image/jpeg;base64,{base64_jpeg_image}"
                        }
                    },
                    {
                        "type": "text",
                        "text": "해당 이미지의 기업은 어디인지 알려주세요."
                    }
                ]
            }
        ]
    }

    try:
        # Make the POST request
        response = requests.post(laas_chat_url, headers=headers, json=data)

        # Print the response or handle it as needed
        print("Response:", response.text)

    except Exception as e:
        # Handle any exceptions
        print("An error occurred:", e)
```

> 이미지 사용시 꼭 확인해주세요!
> 
> 지원 이미지 형식
> 
> - **jpeg** (image/jpeg)
> - **png** (image/png)
> 
> 권장 이미지 크기
> 
> - 가로/세로 중 더 긴 면 기준 **1568** 이하
> 
> 이미지당 용량
> 
> - **4MB** 이하
> 
> 메시지 당 이미지 개수
> 
> - **최대 3개**

  
  

### case5) 추가 메시지에 PDF 문서를 포함한 호출

- pdf 문서는 base64 인코딩된 [**data URLs**](https://developer.mozilla.org/en-US/docs/Web/HTTP/Basics_of_HTTP/Data_URLs) 만 지원합니다.
- 프리셋에 이미 pdf 문서가 포함된 경우 호출이 제한됩니다.
- document\_url에 base64 인코딩 PDF 데이터를 설정한 예시입니다.

```markdown
import requests

def create_chat_completion_with_base64_image():
    project_code = "YOUR_PROJECT_CODE"
    api_key = "YOUR_API_KEY"
    hash = "YOUR_PRESET_HASH"

    # Set request url
    laas_chat_url = "https://api-laas.wanted.co.kr/api/preset/v2/chat/completions"

    # Set the headers
    headers = {
        "project": project_code,
        "apiKey": api_key,
        "Content-Type": "application/json; charset=utf-8"
    }

    # Set the request
    data = {
        "hash": hash,
        "messages": [
            {
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
                        "text": "이 문서의 내용을 요약해주세요"
                    }
                ]
            }
        ]
    }

    try:
        # Make the POST request
        response = requests.post(laas_chat_url, headers=headers, json=data)

        # Print the response or handle it as needed
        print("Response:", response.text)

    except Exception as e:
        # Handle any exceptions
        print("An error occurred:", e)
```

> PDF 사용시 꼭 확인해주세요!
> 
> 최대 용량
> 
> - **32MB** 이하
> 
> 페이지 수
> 
> - **20장** 이하

  

## 응답 Response

호출된 API는 해당 LLM에서 전달해주는 response와 동일하게 전달해줍니다.

```markdown
{
  "id": "string", 
  "object": "string", 
  "created": 0, 
  "model": "string", 
  "choices": 
  [
    {
      "index": 0,
      "message": {
        "role": "string",
        "content": "string" 
      },
      "finish_reason": "string" 
    }
  ], 
  "usage": {
    "prompt_tokens": 0, 
    "completion_tokens": 0, 
    "total_tokens": 0
  } 
}
```