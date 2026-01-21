# 🎤 MP3 to Text Converter

**완전 무료 · 로컬 실행 · 한국어 최적화**

MP3/WAV/M4A/ASF 등 오디오 파일을 텍스트로 변환하는 도구입니다.  
[faster-whisper](https://github.com/guillaumekln/faster-whisper) 엔진을 사용하여 높은 정확도와 빠른 속도를 제공합니다.

---

## ✨ 특징

- **100% 무료**: API 비용 없이 로컬에서 실행
- **오프라인 지원**: 인터넷 연결 없이 사용 가능
- **한국어 최적화**: large-v3 모델로 최고 수준의 한국어 인식
- **실시간 저장**: 변환 중 중단해도 그때까지의 결과 보존
- **환각 필터링**: "한글자막 by..." 등 불필요한 텍스트 자동 제거
- **BGM 모드**: 배경음악 위 음성 추출 최적화
- **다양한 인터페이스**: CLI, Gradio GUI, Flask Web UI, Tkinter GUI 지원

---

## 🚀 빠른 시작

### 1. 요구 사항

- Python 3.10+
- ffmpeg (오디오 전처리용 - **필수 권장**)

**ffmpeg 설치 (성능 향상을 위해 필수):**

ffmpeg가 없으면 전처리가 실패하여 변환 속도가 매우 느려집니다.

```bash
# Windows (권장: winget)
winget install "Gyan.FFmpeg"

# Windows (Chocolatey)
choco install ffmpeg

# Mac
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

**설치 확인:**
```bash
ffmpeg -version
```

### 2. 설치

```bash
# 프로젝트 디렉토리로 이동
cd mp3_to_text

# 가상환경 생성 및 활성화
python -m venv .venv
source .venv/bin/activate  # Mac/Linux
# .venv\Scripts\activate   # Windows

# 의존성 설치
pip install -r requirements.txt
```

---

## 📂 사용법 1: 디렉터리 일괄 변환 (권장)

특정 폴더 내의 **모든 MP3/WAV/M4A/ASF 파일을 한 번에 변환**합니다.

```bash
python src/mp3_to_text.py --dir ./mp3
```

### 옵션
```bash
# VAD 활성화 (음성 구간만 처리, 속도 향상)
python src/mp3_to_text.py --dir ./mp3 --vad

# 시간 구간 조정 (60초 단위)
python src/mp3_to_text.py --dir ./mp3 --interval 60

# BGM 모드 비활성화 (일반 음성용)
python src/mp3_to_text.py --dir ./mp3 --no-bgm

# 할루시네이션 자동 제거 비활성화
python src/mp3_to_text.py --dir ./mp3 --no-clean
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
    └── 2026-01-21.md   # 변환 로그
```

---

## 📄 사용법 2: 개별 파일 변환

### 기본 변환 (자동 파일 생성)
```bash
python src/mp3_to_text.py audio.mp3
```
→ `audio_full.md`, `audio_time.md` 자동 생성

### 옵션 모음
```bash
# 기본 변환 (자동으로 _time.md, _full.md 생성)
python src/mp3_to_text.py audio.mp3

# 단일 파일로 저장 (txt 형식)
python src/mp3_to_text.py audio.mp3 -o result.txt

# VAD 활성화 (음성 구간만 처리, 속도 향상)
python src/mp3_to_text.py audio.mp3 --vad

# 이전 문맥 참조 활성화 (정확도 향상, 속도 저하 가능)
python src/mp3_to_text.py audio.mp3 --context

# 타임스탬프 표시
python src/mp3_to_text.py audio.mp3 -t

# 다른 모델 사용 (기본값: large-v3)
python src/mp3_to_text.py audio.mp3 -m small
```

### 전체 CLI 옵션
| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `-o, --output` | 단일 파일로 저장 (txt 형식) | (자동: _time.md, _full.md) |
| `-m, --model` | 모델 크기 | `large-v3` |
| `-l, --language` | 언어 코드 | `ko` |
| `--device` | 실행 장치 (auto/cuda/cpu) | `auto` |
| `--dual` | 듀얼 출력 (_time.md, _full.md) | (기본 동작) |
| `--vad` | VAD 활성화 (음성 구간만 처리, 속도 향상) | 비활성화 |
| `--context` | 이전 문맥 참조 활성화 (정확도 향상) | 비활성화 |
| `--no-bgm` | 배경음악 모드 비활성화 | (기본: BGM 모드 활성화) |
| `--no-clean` | 할루시네이션 자동 제거 비활성화 | (기본: 자동 제거) |
| `--interval` | 시간 구간 (초) | `30` |
| `-t, --timestamps` | 타임스탬프 표시 | - |
| `--dir` | 디렉터리 일괄 변환 | - |

---

## 🌐 사용법 3: GUI (Gradio 웹 브라우저)

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

## 🖥️ 사용법 4: Flask Web UI (실시간 모니터링)

### 실행
```bash
python src/web_ui.py
```
→ 브라우저에서 **http://localhost:5001** 접속

### 특징
- **탭 전환**: 파일 업로드 / 경로 입력 두 가지 방식 지원
- **실시간 진행률**: 변환 진행 상황 실시간 모니터링
- **세그먼트 로그**: 변환된 텍스트 실시간 표시
- **결과 복사/다운로드**: 변환 완료 후 클립보드 복사 또는 파일 다운로드

---

## 🖼️ 사용법 5: Tkinter GUI (네이티브 데스크톱)

### 실행
```bash
python src/app_tkinter.py
```

### 특징
- **추가 설치 불필요**: Python 기본 Tkinter 사용
- **네이티브 UI**: 운영체제 기본 파일 선택 대화상자
- **다크 테마**: 눈이 편한 다크 모드 UI
- **저장 기능**: 결과를 텍스트 파일로 저장

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
- **비활성화 (기본값)**: 전체 오디오 처리 → 배경음악 포함 모든 구간 처리
- **활성화 (`--vad`)**: 음성 구간만 처리 → 속도 향상, 정확한 음성 구간 추출

### BGM 모드 (배경음악 위 음성 추출)
- **활성화 (기본값)**: 배경음악이 있는 오디오에서 음성 추출 최적화
- **비활성화 (`--no-bgm`)**: 일반 음성 녹음용 설정

### 문맥 참조 (`--context`)
- **비활성화 (기본값)**: 속도 우선, 각 세그먼트 독립 처리
- **활성화**: 이전 문맥 기반 추론으로 정확도 향상 (속도 저하 가능)

### 환각 필터링 (실시간)
변환 중 다음 패턴은 자동으로 제거됩니다:
- "한글자막", "자막 by", "한글자막 by 한효정"
- "시청해주셔서 감사합니다", "구독과 좋아요" 등

### 환각 필터링 (후처리)
변환 후 반복 패턴이 남아있는 경우 `fix_hallucination.py`로 추가 정리할 수 있습니다:

```bash
# 기본 사용법 (백업 자동 생성)
python src/fix_hallucination.py audio_time.md

# 상세 정보 출력
python src/fix_hallucination.py audio_time.md -v

# 백업 없이 처리
python src/fix_hallucination.py audio_time.md --no-backup

# 반복 횟수 임계값 조정 (기본값: 3)
python src/fix_hallucination.py audio_time.md --threshold 5
```

**주요 기능:**
- 연속 반복 문장 감지 및 제거 (예: 같은 문장이 3번 이상 반복)
- 짧은 구문 반복 패턴 정리 (예: "그녀는 그녀는 그녀는" → "그녀는")
- 의미 없는 반복 패턴 제거
- 원본 백업 자동 생성 (`.backup.md`)

### Python API
```python
from src.mp3_to_text import MP3ToTextConverter

converter = MP3ToTextConverter(
    model_size="large-v3",
    language="ko",
    use_vad=False,       # False: 전체 오디오 처리, True: 음성 구간만 처리
    bgm_mode=True,       # True: 배경음악 모드, False: 일반 음성용
    use_context=False,   # True: 이전 문맥 참조, False: 독립 처리
    auto_clean_hallucination=True  # 변환 후 자동 할루시네이션 제거
)

result = converter.transcribe("audio.mp3")
print(result['text'])
```

---

## 📁 프로젝트 구조

```
mp3_to_text/
├── src/
│   ├── mp3_to_text.py      # 핵심 변환 모듈 + CLI
│   ├── app_gui.py          # Gradio 웹 GUI (port 7860)
│   ├── web_ui.py           # Flask 웹 UI (port 5001)
│   ├── app_tkinter.py      # Tkinter 네이티브 GUI
│   └── fix_hallucination.py # 할루시네이션 후처리 도구
├── mp3/                    # 오디오 파일 및 결과
│   └── log/                # 변환 로그
├── convert_all.sh          # 일괄 변환 스크립트
├── docs/                   # 문서
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

### 배경음악이 있는 오디오에서 인식률이 낮을 때
BGM 모드가 기본 활성화되어 있습니다. 일반 음성 녹음인 경우 `--no-bgm` 옵션 사용:
```bash
python src/mp3_to_text.py audio.mp3 --no-bgm
```

---

## 📜 라이선스

MIT License

---

*Powered by [faster-whisper](https://github.com/guillaumekln/faster-whisper) & [OpenAI Whisper](https://github.com/openai/whisper)*
