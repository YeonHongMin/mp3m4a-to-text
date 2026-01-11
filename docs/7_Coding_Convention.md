# 📐 Coding Convention & AI Collaboration Guide
## 코딩 컨벤션 및 AI 협업 가이드

---

## 1. Python 코딩 컨벤션

### 1.1 스타일 가이드
본 프로젝트는 **PEP 8**을 기본으로 따르며, 다음 추가 규칙을 적용합니다.

### 1.2 들여쓰기 및 포매팅
```python
# ✅ 좋은 예
def transcribe(
    self,
    audio_path: str,
    show_timestamps: bool = False,
    show_progress: bool = True
) -> dict:
    """오디오를 텍스트로 변환."""
    pass

# ❌ 나쁜 예
def transcribe(self, audio_path: str, show_timestamps: bool = False, show_progress: bool = True) -> dict:
    pass
```

### 1.3 임포트 순서
```python
# 1. 표준 라이브러리
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# 2. 서드파티 라이브러리
import gradio as gr
from faster_whisper import WhisperModel

# 3. 로컬 모듈
from utils import format_time
```

### 1.4 타입 힌트
```python
# 모든 함수에 타입 힌트 권장
def format_time(seconds: float) -> str:
    """초를 MM:SS 형식으로 변환."""
    pass

def transcribe_to_files(
    self,
    audio_path: str,
    output_base: str,
    time_interval: int = 30
) -> tuple[str, str, str]:
    """변환 결과를 파일로 저장."""
    pass
```

---

## 2. 문서화 규칙

### 2.1 Docstring 형식
```python
def function_name(param1: str, param2: int = 10) -> dict:
    """함수의 간단한 설명 (한 줄).
    
    더 자세한 설명이 필요한 경우 여기에 작성.
    여러 줄로 작성 가능.
    
    Args:
        param1: 첫 번째 파라미터 설명
        param2: 두 번째 파라미터 설명 (기본값: 10)
        
    Returns:
        반환값에 대한 설명
        
    Raises:
        FileNotFoundError: 파일을 찾을 수 없는 경우
        ValueError: 잘못된 값이 전달된 경우
        
    Example:
        >>> result = function_name("test", 20)
        >>> print(result)
        {'key': 'value'}
    """
    pass
```

### 2.2 인라인 주석
```python
# ✅ 좋은 예: 왜(Why)를 설명
# VAD 비활성화: 배경음악이 있는 오디오에서 음성 누락 방지
use_vad = False

# ❌ 나쁜 예: 무엇(What)만 설명 (코드로 알 수 있음)
# VAD를 False로 설정
use_vad = False
```

---

## 3. 네이밍 규칙

### 3.1 일반 규칙
| 대상 | 규칙 | 예시 |
|------|------|------|
| 모듈 | snake_case | `mp3_to_text.py` |
| 클래스 | PascalCase | `MP3ToTextConverter` |
| 함수/메서드 | snake_case | `transcribe_audio` |
| 변수 | snake_case | `audio_path` |
| 상수 | UPPER_SNAKE | `HALLUCINATION_PATTERNS` |
| Private | _prefix | `_transcribe_generator` |

### 3.2 의미 있는 이름
```python
# ✅ 좋은 예
segment_list = []
full_text_parts = []
audio_duration = get_audio_duration(path)

# ❌ 나쁜 예
sl = []
ftp = []
d = get_audio_duration(path)
```

---

## 4. 에러 처리

### 4.1 예외 처리 패턴
```python
# 특정 예외 캐치
try:
    result = process_audio(path)
except FileNotFoundError:
    print(f"❌ 파일을 찾을 수 없습니다: {path}")
    return None
except Exception as e:
    print(f"❌ 처리 중 오류 발생: {e}")
    raise

# 리소스 정리가 필요한 경우
try:
    file = open(path, 'w')
    file.write(content)
except IOError as e:
    print(f"❌ 파일 쓰기 실패: {e}")
finally:
    file.close()
```

### 4.2 사용자 중단 처리
```python
try:
    for segment in generator:
        process(segment)
except KeyboardInterrupt:
    print("\n🛑 사용자에 의해 중단되었습니다.")
    save_current_progress()  # 현재까지 저장
```

---

## 5. 파일 구조

### 5.1 현재 구조
```
antigravity/
├── src/
│   ├── mp3_to_text.py      # 핵심 변환 모듈
│   └── app_gui.py          # Gradio GUI
├── mp3/                     # 오디오 및 결과
│   └── log/                # 변환 로그
├── docs/                    # 문서
├── .gitignore
├── requirements.txt
└── README.md
```

### 5.2 새 파일 추가 시
- 유틸리티 함수: `src/utils.py`
- 테스트: `tests/test_*.py`
- 설정: `config/` 또는 `config.py`

---

## 6. Git 컨벤션

### 6.1 커밋 메시지 형식
```
<type>: <subject>

<body>
```

### 6.2 타입
| 타입 | 설명 |
|------|------|
| feat | 새 기능 |
| fix | 버그 수정 |
| docs | 문서 변경 |
| style | 포매팅 (기능 변화 없음) |
| refactor | 리팩토링 |
| test | 테스트 추가 |
| chore | 빌드, 설정 등 |

### 6.3 예시
```bash
git commit -m "feat: 실시간 파일 저장 기능 추가"
git commit -m "fix: 환각 필터링에 새 패턴 추가"
git commit -m "docs: PRD 문서 작성"
```

---

## 7. AI 협업 가이드

### 7.1 효과적인 요청 방법

#### ✅ 좋은 요청
```
환각 패턴에 "한글자막 by 한효정" 추가해줘.
파일: src/mp3_to_text.py
위치: HALLUCINATION_PATTERNS 리스트
```

#### ❌ 비효율적인 요청
```
이상한 텍스트 나오는 거 고쳐줘.
```

### 7.2 컨텍스트 제공
1. **파일 경로** 명시
2. **함수/클래스명** 명시
3. **현재 동작** 설명
4. **원하는 동작** 설명

### 7.3 단계적 진행
```
1. 먼저 현재 코드 구조 확인
2. 수정 방향 제안 받기
3. 승인 후 구현
4. 테스트 확인
```

### 7.4 롤백 요청
```
방금 수정한 거 원복해줘.
(파일: src/mp3_to_text.py)
```

---

## 8. 코드 리뷰 체크리스트

### 8.1 기능
- [ ] 요구사항을 충족하는가?
- [ ] 엣지 케이스를 처리하는가?
- [ ] 에러 처리가 적절한가?

### 8.2 품질
- [ ] 타입 힌트가 있는가?
- [ ] Docstring이 있는가?
- [ ] 불필요한 코드가 없는가?

### 8.3 호환성
- [ ] 기존 API가 유지되는가?
- [ ] 하위 호환성이 있는가?
- [ ] 의존성이 최소화되었는가?

---

## 9. 자주 하는 실수

### 9.1 피해야 할 패턴
```python
# ❌ 하드코딩된 경로
path = "/Users/username/project/file.mp3"

# ✅ 상대 경로 또는 파라미터
path = os.path.join(base_dir, filename)
```

```python
# ❌ 광범위한 except
try:
    ...
except:
    pass

# ✅ 특정 예외 처리
try:
    ...
except FileNotFoundError:
    handle_file_error()
```

```python
# ❌ print 대신 로깅 권장 (대규모 프로젝트)
print("Error occurred")

# ✅ 현재 프로젝트는 print + 이모지 사용
print("❌ 에러 발생")
```

---

*문서 버전: 1.0*
*최종 수정: 2026-01-11*
