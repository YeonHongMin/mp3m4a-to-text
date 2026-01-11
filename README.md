# 🎤 MP3/M4A/WAV to Text Converter

**완전 무료 · 로컬 실행 · 한국어 최적화**

MP3/WAV 오디오 파일을 텍스트로 변환하는 도구입니다.  
[faster-whisper](https://github.com/guillaumekln/faster-whisper) 엔진을 사용하여 높은 정확도와 빠른 속도를 제공합니다.

---

## ✨ 특징

- **100% 무료**: API 비용 없이 로컬에서 실행
- **오프라인 지원**: 인터넷 연결 없이 사용 가능
- **한국어 최적화**: large-v3 모델로 최고 수준의 한국어 인식
- **실시간 저장**: 변환 중 중단해도 그때까지의 결과 보존
- **환각 필터링**: "한글자막 by..." 등 불필요한 텍스트 자동 제거

---

## 🚀 빠른 시작

### 1. 요구 사항

- Python 3.10+
- ffmpeg (오디오 처리용)

**ffmpeg 설치:**
```bash
# Mac
brew install ffmpeg

# Windows (Chocolatey)
choco install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

### 2. 설치

```bash
# 프로젝트 디렉토리로 이동
cd antigravity

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

---

## 📂 사용법 1: 디렉터리 일괄 변환 (권장)

특정 폴더 내의 **모든 MP3/WAV 파일을 한 번에 변환**합니다.

```bash
python src/mp3_to_text.py --dir ./mp3
```

### 옵션
```bash
# VAD 비활성화 (배경음악 있는 파일)
python src/mp3_to_text.py --dir ./mp3 --no-vad

# 시간 구간 조정 (60초 단위)
python src/mp3_to_text.py --dir ./mp3 --interval 60
```

### 출력 결과
```
mp3/
├── audio1.mp3
├── audio1_full.md      # 전체 텍스트
├── audio1_time.md      # 시간대별 텍스트
├── audio2.mp3
├── audio2_full.md
├── audio2_time.md
└── log/
    └── 2026-01-11.md   # 변환 로그
```

---

## 📄 사용법 2: 개별 파일 변환

### 기본 변환 (듀얼 출력)
```bash
python src/mp3_to_text.py audio.mp3 --dual
```
→ `audio_full.md`, `audio_time.md` 생성

### 옵션 모음
```bash
# 기본 변환 (콘솔 출력)
python src/mp3_to_text.py audio.mp3

# 파일로 저장
python src/mp3_to_text.py audio.mp3 -o result.txt

# VAD 비활성화 (배경음악/BGM 있는 경우)
python src/mp3_to_text.py audio.mp3 --dual --no-vad

# 타임스탬프 표시
python src/mp3_to_text.py audio.mp3 -t

# 다른 모델 사용 (기본값: large-v3)
python src/mp3_to_text.py audio.mp3 -m small
```

### 전체 CLI 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o, --output` | 출력 파일 경로 | (콘솔 출력) |
| `-m, --model` | 모델 크기 | `large-v3` |
| `-l, --language` | 언어 코드 | `ko` |
| `--dual` | 듀얼 출력 (_time.md, _full.md) | - |
| `--no-vad` | VAD 비활성화 (음성 누락 방지) | - |
| `--interval` | 시간 구간 (초) | `30` |
| `-t, --timestamps` | 타임스탬프 표시 | - |
| `--dir` | 디렉터리 일괄 변환 | - |

---

## 🌐 사용법 3: GUI (웹 브라우저)

### 실행
```bash
python src/app_gui.py
```
→ 브라우저에서 **http://localhost:7860** 접속

### 화면 구성
```
┌────────────────────────┬─────────────────────────────────┐
│  📁 파일 업로드        │  📝 변환 결과                   │
│  ⚙️ 설정 (모델, VAD)   │  (실시간 표시)                  │
│  [🎯 변환 시작]        │                                 │
│  ⏳ 진행률             │  [💾 저장]                      │
└────────────────────────┴─────────────────────────────────┘
```

### 주요 기능
- 파일 드래그 앤 드롭 업로드
- 모델/VAD 설정 변경
- 실시간 진행률 표시
- 결과 파일 저장

---

## 📊 모델 선택 가이드

| 모델 | 크기 | 속도 | 정확도 | 추천 |
|------|------|------|--------|------|
| `small` | ~250MB | ⚡⚡⚡ | ★★★☆☆ | 빠른 테스트, 저사양 PC |
| `medium` | ~750MB | ⚡⚡ | ★★★★☆ | 균형 잡힌 성능 |
| **`large-v3`** | ~3GB | ⚡ | ★★★★★ | **한국어 최고 (기본값)** |

> 💡 GPU가 있으면 large-v3도 빠르게 실행됩니다!

---

## 🔧 고급 설정

### VAD (Voice Activity Detection)
- **활성화 (기본)**: 음성 구간만 처리 → 빠름
- **비활성화 (`--no-vad`)**: 전체 오디오 처리 → 배경음악 있을 때 사용

### 환각 필터링
다음 패턴은 자동으로 제거됩니다:
- "한글자막", "자막 by", "한글자막 by 한효정"
- "시청해주셔서 감사합니다", "구독과 좋아요" 등

### Python API
```python
from src.mp3_to_text import MP3ToTextConverter

converter = MP3ToTextConverter(
    model_size="large-v3",
    language="ko",
    use_vad=True
)

result = converter.transcribe("audio.mp3")
print(result['text'])
```

---

## 📁 프로젝트 구조

```
antigravity/
├── src/
│   ├── mp3_to_text.py    # 핵심 변환 모듈 + CLI
│   └── app_gui.py        # Gradio 웹 GUI
├── mp3/                  # 오디오 파일 및 결과
│   └── log/              # 변환 로그
├── docs/                 # 문서
├── requirements.txt
└── README.md
```

---

## ❓ 문제 해결

### "ffmpeg not found" 오류
ffmpeg가 PATH에 없습니다. 위 설치 방법 참조.

### 첫 실행이 느린 경우
모델을 다운로드하기 때문입니다. 이후에는 캐시되어 빠르게 로드됩니다.

### 환각(이상한 텍스트)이 나올 때
`src/mp3_to_text.py`의 `HALLUCINATION_PATTERNS`에 패턴 추가:
```python
HALLUCINATION_PATTERNS = [
    "한글자막", "새로운 패턴",  # ← 여기에 추가
]
```

---

## 📜 라이선스

MIT License

---

*Powered by [faster-whisper](https://github.com/guillaumekln/faster-whisper) & [OpenAI Whisper](https://github.com/openai/whisper)*

