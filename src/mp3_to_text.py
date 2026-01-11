"""
MP3 to Text Converter - Core Module
===================================
Converts MP3/WAV audio files to text using faster-whisper.
Completely free and runs locally (offline).

Usage:
    python mp3_to_text.py                    # Interactive mode
    python mp3_to_text.py audio.mp3          # CLI mode
    python mp3_to_text.py audio.mp3 -o out.txt  # Save to file
"""

import os
import sys
import argparse
import warnings
from pathlib import Path

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore")

# Optional: Progress bar
try:
    from tqdm import tqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False

# Check if faster-whisper is installed
try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ 'faster-whisper' 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install faster-whisper")
    print("   또한 ffmpeg가 시스템에 설치되어 있어야 합니다.")
    print("   또한 ffmpeg가 시스템에 설치되어 있어야 합니다.")
    sys.exit(1)

# Audio preprocessing
try:
    from pydub import AudioSegment
    import tempfile
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


def preprocess_audio(audio_path: str, target_sample_rate: int = 16000) -> str:
    """
    오디오를 Whisper 최적 포맷으로 전처리.
    - 16kHz 샘플레이트
    - 모노 채널
    - WAV 포맷
    """
    if not PYDUB_AVAILABLE:
        return audio_path
    
    try:
        print(f"🔄 오디오 전처리 중... (16kHz 모노 변환)")
        # 오디오 로드
        audio = AudioSegment.from_file(audio_path)
        
        # 모노 변환
        if audio.channels > 1:
            audio = audio.set_channels(1)
        
        # 16kHz 리샘플링
        if audio.frame_rate != target_sample_rate:
            audio = audio.set_frame_rate(target_sample_rate)
        
        # 임시 파일 저장
        temp_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        audio.export(temp_file.name, format="wav")
        temp_file.close()
        
        return temp_file.name
        
    except Exception as e:
        print(f"⚠️ 전처리 실패, 원본 사용: {e}")
        return audio_path


def get_audio_duration(audio_path: str) -> float:
    """
    오디오 파일의 총 길이(초)를 반환.
    """
    if not PYDUB_AVAILABLE:
        return 0.0
    
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # 밀리초 → 초
    except Exception as e:
        print(f"⚠️ 오디오 길이 확인 실패: {e}")
        return 0.0


def format_time(seconds: float) -> str:
    """초를 MM:SS 또는 HH:MM:SS 형식으로 변환."""
    if seconds < 0:
        return "--:--"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


class MP3ToTextConverter:
    """
    MP3/WAV 파일을 텍스트로 변환하는 클래스.
    
    Attributes:
        model_size: 모델 크기 ('small', 'medium', 'large', 'large-v3')
        device: 실행 장치 ('cuda' or 'cpu')
        language: 변환 언어 (기본값: 'ko' 한국어)
    """
    
    # 모델 크기별 특성
    MODEL_INFO = {
        "small": {"size": "~250MB", "speed": "빠름", "accuracy": "양호"},
        "medium": {"size": "~750MB", "speed": "보통", "accuracy": "좋음"},
        "large": {"size": "~1.5GB", "speed": "느림", "accuracy": "매우 좋음"},
        "large-v3": {"size": "~3GB", "speed": "가장 느림", "accuracy": "최고 (한국어 추천)"},
    }
    
    def __init__(self, model_size: str = "large-v3", device: str = "auto", 
                 language: str = "ko", use_vad: bool = True, use_context: bool = False):
        """
        변환기 초기화.
        
        Args:
            model_size: 모델 크기 (small, medium, large, large-v3)
            device: 'cuda', 'cpu', 또는 'auto' (자동 감지)
            language: 변환 언어 코드 (ko, en, ja 등)
            use_vad: VAD 필터 사용 여부 (기본: True, 음성 누락 시 False)
            use_context: 이전 문맥 기반 추론 여부 (기본: False, 속도 우선)
        """
        self.model_size = model_size
        self.language = language
        self.use_vad = use_vad
        self.use_context = use_context
        
        # 자동 장치 감지
        if device == "auto":
            try:
                import torch
                self.device = "cuda" if torch.cuda.is_available() else "cpu"
            except ImportError:
                self.device = "cpu"
        else:
            self.device = device
        
        # 장치에 따른 최적 계산 타입
        self.compute_type = "float16" if self.device == "cuda" else "int8"
        
        vad_status = "활성화" if use_vad else "비활성화"
        print(f"🔧 설정: 모델={model_size}, 장치={self.device}, 언어={language}, VAD={vad_status}")
        print(f"📥 모델 로딩 중... (첫 실행 시 다운로드가 필요합니다)")
        
        self.model = WhisperModel(
            model_size,
            device=self.device,
            compute_type=self.compute_type
        )
        
        print(f"✅ 모델 로딩 완료!")
    
    # 환각(Hallucination)으로 자주 등장하는 패턴들
    HALLUCINATION_PATTERNS = [
        "한글자막", "자막 제작", "자막 by", "수고하셨습니다", 
        "시청해주셔서 감사합니다", "MBC", "구독과 좋아요", 
        "영상 편집", "제작 지원", "번역 :", "싱크 :", "배급 :",
        "한글 자막", "by 한효정", "한글자막 by 한효정"
    ]

    def is_hallucination(self, text: str) -> bool:
        """텍스트가 환각인지 판별"""
        if not text or len(text.strip()) == 0:
            return True
            
        # 1. 반복 패턴 체크 (예: "...." 또는 "??" 반복)
        if len(text) > 10 and len(set(text)) < 5:
            return True
            
        # 2. 알려진 환각 문구 체크
        for pattern in self.HALLUCINATION_PATTERNS:
            if pattern in text:
                return True
                
        return False

    def _transcribe_generator(self, audio_path: str, show_progress: bool = True):
        """
        오디오 파일을 변환하는 제너레이터 (스트리밍용).
        Yields:
            (segment, info, total_duration, processed_path)
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"파일을 찾을 수 없습니다: {audio_path}")
        
        # 오디오 길이 확인
        total_duration = get_audio_duration(audio_path)
        if total_duration > 0:
            print(f"🎵 변환 중: {audio_path} (총 {format_time(total_duration)})")
        else:
            print(f"🎵 변환 중: {audio_path}")
        
        # 오디오 전처리 수행
        processed_path = preprocess_audio(audio_path)
        process_audio_path = processed_path if processed_path != audio_path else audio_path
        
        # 설정 가져오기
        use_vad = getattr(self, 'use_vad', True)
        use_context = getattr(self, 'use_context', False)
        
        # 한국어 인식 유도를 위한 프롬프트 (환각 방지용)
        initial_prompt = "[한글 음성 추출]" if self.language == 'ko' else None

        if use_vad:
            segments, info = self.model.transcribe(
                process_audio_path,
                language=self.language,
                beam_size=5,
                condition_on_previous_text=use_context,
                temperature=0,  # 반복 탐색 방지
                initial_prompt=initial_prompt,
                vad_filter=True,
                vad_parameters=dict(threshold=0.05, min_speech_duration_ms=50, min_silence_duration_ms=50),
            )
        else:
            print("⚠️ VAD 비활성화: 전체 오디오 처리")
            segments, info = self.model.transcribe(
                process_audio_path,
                language=self.language,
                beam_size=5,
                condition_on_previous_text=use_context,
                temperature=0,
                initial_prompt=initial_prompt,
                vad_filter=False,
            )
        
        if show_progress:
            print("📊 실시간 진행 상황:")
            print("   ⏳ 모델 처리 중... (첫 결과까지 잠시 대기)", end="", flush=True)
        
        first_segment = True
        for segment in segments:
            # 환각 필터링
            if self.is_hallucination(segment.text):
                continue
            
            # 첫 세그먼트 시 대기 메시지 지우기
            if first_segment and show_progress:
                print("\r" + " " * 50 + "\r", end="", flush=True)
                first_segment = False
                
            yield segment, info, total_duration, processed_path

    def transcribe(self, audio_path: str, show_timestamps: bool = False, 
                   show_progress: bool = True) -> dict:
        """
        오디오 파일을 텍스트로 변환.
        
        Args:
            audio_path: MP3/WAV 파일 경로
            show_timestamps: 타임스탬프 표시 여부
            show_progress: 진행 상황 실시간 표시 여부
            
        Returns:
            dict: {
                'text': 전체 텍스트,
                'language': 감지된 언어,
                'language_probability': 언어 감지 확률,
                'segments': 세그먼트 목록 (타임스탬프 포함)
            }
        """
        segment_list = []
        full_text_parts = []
        info = None
        segment_count = 0
        processed_path = audio_path # Default, will be updated by generator
        
        import time as time_module
        start_time = time_module.time()
        
        for segment, info_obj, total_duration, gen_processed_path in self._transcribe_generator(audio_path, show_progress):
            if info is None: info = info_obj
            if processed_path == audio_path: processed_path = gen_processed_path # Capture processed_path once
            
            segment_count += 1
            segment_list.append({
                "start": segment.start,
                "end": segment.end,
                "text": segment.text
            })
            full_text_parts.append(segment.text)
            
            # 진행 상황 표시
            if show_progress:
                current_audio_time = segment.end
                elapsed_real_time = time_module.time() - start_time
                
                if total_duration > 0:
                    # 진행률 계산
                    progress_pct = min(100, (current_audio_time / total_duration) * 100)
                    
                    # ETA 계산 (현재 속도 기준)
                    if current_audio_time > 0:
                        speed_ratio = elapsed_real_time / current_audio_time
                        remaining_audio = total_duration - current_audio_time
                        eta_seconds = remaining_audio * speed_ratio
                    else:
                        eta_seconds = -1
                    
                    # 진행 바 표시
                    bar_width = 20
                    filled = int(bar_width * progress_pct / 100)
                    bar = "█" * filled + "░" * (bar_width - filled)
                    
                    # 텍스트 미리보기 (30자 제한)
                    text_preview = segment.text[:25] + "..." if len(segment.text) > 25 else segment.text
                    
                    # 상태 라인 출력 (같은 줄 덮어쓰기)
                    status = f"\r[{bar}] {progress_pct:5.1f}% | {format_time(current_audio_time)}/{format_time(total_duration)} | ETA: {format_time(eta_seconds)} | {text_preview}"
                    print(status.ljust(120), end="", flush=True)
                else:
                    # 오디오 길이를 모를 때는 세그먼트 수와 처리 시간만 표시
                    text_preview = segment.text[:30] + "..." if len(segment.text) > 30 else segment.text
                    print(f"\r세그먼트 {segment_count} | {format_time(current_audio_time)} | {text_preview}".ljust(100), end="", flush=True)
            
            if show_timestamps:
                print(f"\n  [{segment.start:.2f}s → {segment.end:.2f}s] {segment.text}")
        
        # 진행 표시 종료 (줄바꿈)
        if show_progress:
            print()  # 새 줄로 이동
            
        # 임시 파일 정리
        if processed_path != audio_path and os.path.exists(processed_path):
            try:
                os.unlink(processed_path)
            except:
                pass
        
        full_text = " ".join(full_text_parts).strip()
        
        result = {
            "text": full_text,
            "language": info.language,
            "language_probability": info.language_probability,
            "segments": segment_list
        }
        
        print(f"\n✅ 변환 완료! (총 {segment_count}개 세그먼트, 감지 언어: {info.language}, 확률: {info.language_probability:.2%})")
        
        return result
    
    def transcribe_to_file(self, audio_path: str, output_path: str, 
                           include_timestamps: bool = False) -> str:
        """
        오디오 파일을 텍스트로 변환하고 파일로 저장.
        
        Args:
            audio_path: 입력 오디오 파일 경로
            output_path: 출력 텍스트 파일 경로
            include_timestamps: 타임스탬프 포함 여부
            
        Returns:
            str: 저장된 파일 경로
        """
        result = self.transcribe(audio_path, show_timestamps=False)
        
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# Audio Transcription\n")
            f.write(f"# Source: {audio_path}\n")
            f.write(f"# Language: {result['language']} ({result['language_probability']:.2%})\n")
            f.write(f"# ---\n\n")
            
            if include_timestamps:
                for seg in result['segments']:
                    f.write(f"[{seg['start']:.2f}s - {seg['end']:.2f}s]\n")
                    f.write(f"{seg['text']}\n\n")
            else:
                f.write(result['text'])
        
        print(f"📄 결과 저장됨: {output_path}")
        
        try:
            for segment, info_obj, total_duration, _ in self._transcribe_generator(audio_path, show_progress=True):
                if info is None:
                    info = info_obj
                    # 언어 정보 등 파일에 업데이트 (선택 사항, 복잡해지므로 생략하거나 나중에 추가)

                # 1. 전체 텍스트 파일에 추가 (Append)
                with open(full_file, "a", encoding="utf-8") as f:
                    text_chunk = segment.text.strip()
                    if text_chunk:
                        # 문장 끝에 마침표가 있으면 줄바꿈
                        if text_chunk.endswith('.'):
                            f.write(f"{text_chunk}\n\n")
                        else:
                            f.write(f"{text_chunk} ")

                # 2. 시간 구간 파일에 추가 (Append)
                with open(time_file, "a", encoding="utf-8") as f:
                    start_str = format_time(segment.start)
                    # end_str = format_time(segment.end) # 필요한 경우 사용
                    f.write(f"| {start_str} | {segment.text.strip()} |\n")

        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단되었습니다. 현재까지의 결과는 저장되었습니다.")
            with open(full_file, "a", encoding="utf-8") as f:
                f.write("\n\n> **⚠️ 중단됨: 사용자에 의해 작업이 취소되었습니다.**\n")
            with open(time_file, "a", encoding="utf-8") as f:
                f.write("\n> **⚠️ 중단됨: 사용자에 의해 작업이 취소되었습니다.**\n")
            return time_file, full_file, log_file

        # 종료 처리
        end_time = time.time()
        elapsed_str = format_time(end_time - start_time)
        
        # 로그에 결과 업데이트
        with open(log_file, "a", encoding="utf-8") as f:
            if info:
                f.write(f"| **언어** | {info.language} ({info.language_probability:.1%}) |\n")
            f.write(f"| **소요 시간** | {elapsed_str} |\n\n")

        # 파일 상단 정보 업데이트 (선택적: 파일을 다시 읽어서 헤더 수정은 복잡하므로 꼬리말 추가)
        with open(full_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n✅ **변환 완료** (소요 시간: {elapsed_str})")
            
        with open(time_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n✅ **변환 완료** (소요 시간: {elapsed_str})")

        print(f"\n✅ 변환 완료! (총 {elapsed_str})")
        print(f"📄 전체 내용: {full_file}")
        print(f"📄 시간 구간: {time_file}")
        
        return time_file, full_file, log_file
    
    def transcribe_to_files(self, audio_path: str, output_base: str, 
                            time_interval: int = 30) -> tuple:
        """
        오디오 파일을 텍스트로 변환하고 두 가지 형식으로 저장 (실시간 기록).
        """
        import time
        from datetime import datetime
        
        # 시작 시간 기록
        start_time = time.time()
        start_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 파일 경로 생성
        time_file = f"{output_base}_time.md"
        full_file = f"{output_base}_full.md"
        
        # 로그 파일 준비
        log_dir = os.path.join(os.path.dirname(output_base) or ".", "log")
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, f"{date_str}.md")
        
        # 로그 파일 헤더 (append)
        is_new_log = not os.path.exists(log_file) or os.path.getsize(log_file) == 0
        with open(log_file, "a", encoding="utf-8") as f:
            if is_new_log:
                f.write(f"# 📋 Transcription Log - {date_str}\n\n")
            f.write(f"---\n\n")
            f.write(f"## 🎵 {os.path.basename(audio_path)}\n\n")
            f.write(f"| 항목 | 값 |\n|---|---|\n")
            f.write(f"| **파일** | `{audio_path}` |\n")
            f.write(f"| **시작 시간** | {start_datetime} |\n")
            f.write(f"| **VAD** | {'활성화' if self.use_vad else '비활성화'} |\n")
        
        # 출력 파일 초기화
        with open(full_file, "w", encoding="utf-8") as f:
            f.write(f"# 📝 Audio Transcription - Full Text\n\n")
            f.write(f"> **파일**: `{audio_path}`  \n")
            f.write(f"> **상태**: 변환 중... (실시간 업데이트)\n\n---\n\n")
            
        with open(time_file, "w", encoding="utf-8") as f:
            f.write(f"# ⏱️ Audio Transcription - Time Intervals\n\n")
            f.write(f"> **파일**: `{audio_path}`  \n")
            f.write(f"> **상태**: 변환 중... (실시간 업데이트)\n\n---\n\n")
            f.write(f"| 시간 | 내용 |\n|---|---|\n")

        # 실시간 변환 및 저장
        info = None
        logged_progress = set()  # 이미 로그에 기록한 진행률
        segment_count = 0
        
        try:
            for segment, info_obj, total_duration, _ in self._transcribe_generator(audio_path, show_progress=True):
                segment_count += 1
                
                if info is None:
                    info = info_obj
                    # 언어 정보 로그에 업데이트
                    with open(log_file, "a", encoding="utf-8") as f:
                         f.write(f"| **언어** | {info.language} ({info.language_probability:.1%}) |\n")

                # 진행률 계산
                if total_duration > 0:
                    progress = segment.end / total_duration * 100
                    progress_int = int(progress)
                    elapsed = time.time() - start_time
                    
                    # ETA 계산
                    if progress > 0:
                        eta = elapsed * (100 - progress) / progress
                        eta_str = format_time(eta)
                    else:
                        eta_str = "?"
                    
                    # 콘솔에 진행률 바 출력
                    bar_length = 20
                    filled = int(bar_length * progress / 100)
                    bar = "█" * filled + "░" * (bar_length - filled)
                    time_info = f"{format_time(segment.end)}/{format_time(total_duration)}"
                    text_preview = segment.text.strip()[:25]
                    print(f"\r[{bar}] {progress:5.1f}% | {time_info} | ETA: {eta_str} | {text_preview:<25}", end="", flush=True)
                    
                    # 로그 기록 (10% 단위)
                    for milestone in range(10, 100, 10):
                        if progress_int >= milestone and milestone not in logged_progress:
                            logged_progress.add(milestone)
                            with open(log_file, "a", encoding="utf-8") as f:
                                f.write(f"| **진행률** | {milestone}% ({format_time(segment.end)}/{format_time(total_duration)}) |\n")
                else:
                    # total_duration을 모를 때
                    print(f"\r세그먼트 {segment_count} | {format_time(segment.end)} | {segment.text.strip()[:30]:<30}", end="", flush=True)

                # 1. 전체 텍스트 파일에 추가 (Append)
                with open(full_file, "a", encoding="utf-8") as f:
                    text_chunk = segment.text.strip()
                    if text_chunk:
                        if text_chunk.endswith('.'):
                            f.write(f"{text_chunk}\n\n")
                        else:
                            f.write(f"{text_chunk} ")

                # 2. 시간 구간 파일에 추가 (Append)
                with open(time_file, "a", encoding="utf-8") as f:
                    start_str = format_time(segment.start)
                    f.write(f"| {start_str} | {segment.text.strip()} |\n")

        except KeyboardInterrupt:
            print("\n🛑 사용자에 의해 중단되었습니다. 현재까지의 결과는 저장되었습니다.")
            with open(full_file, "a", encoding="utf-8") as f:
                f.write("\n\n> **⚠️ 중단됨: 사용자에 의해 작업이 취소되었습니다.**\n")
            with open(time_file, "a", encoding="utf-8") as f:
                f.write("\n> **⚠️ 중단됨: 사용자에 의해 작업이 취소되었습니다.**\n")
            return time_file, full_file, log_file

        # 종료 처리
        end_time = time.time()
        elapsed_str = format_time(end_time - start_time)
        
        # 로그에 결과 업데이트
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"| **소요 시간** | {elapsed_str} |\n\n")

        # 파일 상단 정보 업데이트 (꼬리말 추가)
        with open(full_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n✅ **변환 완료** (소요 시간: {elapsed_str})")
            
        with open(time_file, "a", encoding="utf-8") as f:
            f.write(f"\n\n---\n✅ **변환 완료** (소요 시간: {elapsed_str})")

        print(f"\n✅ 변환 완료! (총 {elapsed_str})")
        print(f"📄 전체 내용: {full_file}")
        print(f"📄 시간 구간: {time_file}")
        
        return time_file, full_file, log_file



def main():
    """CLI 엔트리 포인트."""
    parser = argparse.ArgumentParser(
        description="MP3/WAV 파일을 텍스트로 변환합니다 (무료, 로컬 실행)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python mp3_to_text.py audio.mp3                    # 기본 변환
  python mp3_to_text.py audio.mp3 -o result.txt      # 파일로 저장
  python mp3_to_text.py audio.mp3 -o result --dual   # 두 가지 버전 저장 (_time.md, _full.md)
  python mp3_to_text.py audio.mp3 -m large-v3        # 최고 정확도 모델
  python mp3_to_text.py audio.mp3 -t                 # 타임스탬프 표시
  python mp3_to_text.py --dir ./mp3                  # 디렉터리 내 모든 파일 일괄 변환
        """
    )
    
    parser.add_argument("audio_file", nargs="?", help="변환할 MP3/WAV 파일 경로")
    parser.add_argument("-o", "--output", help="출력 파일 경로 (생략 시 콘솔 출력)")
    parser.add_argument("-m", "--model", default="large-v3",
                        choices=["small", "medium", "large", "large-v3"],
                        help="모델 크기 (기본: large-v3)")
    parser.add_argument("-l", "--language", default="ko",
                        help="언어 코드 (기본: ko 한국어)")
    parser.add_argument("--device", default="auto",
                        choices=["auto", "cuda", "cpu"],
                        help="실행 장치 (기본: auto)")
    parser.add_argument("-t", "--timestamps", action="store_true",
                        help="타임스탬프 표시")
    parser.add_argument("--dual", action="store_true",
                        help="두 가지 버전 저장 (_time.md, _full.md)")
    parser.add_argument("--interval", type=int, default=30,
                        help="시간 구간 (초, 기본: 30)")
    parser.add_argument("--no-vad", action="store_true",
                        help="VAD 비활성화 (음성 누락 방지, 처리 시간 증가)")
    parser.add_argument("--context", action="store_true",
                        help="이전 문맥 참조 활성화 (정확도 향상, 속도 저하 가능)")
    parser.add_argument("--dir", metavar="DIRECTORY",
                        help="디렉터리 내 모든 MP3/WAV 파일 일괄 변환")
    
    args = parser.parse_args()
    
    # 디렉터리 모드 (--dir 옵션)
    if args.dir:
        import glob
        
        dir_path = args.dir
        if not os.path.isdir(dir_path):
            print(f"❌ 디렉터리를 찾을 수 없습니다: {dir_path}")
            sys.exit(1)
        
        # MP3/WAV/M4A 파일 검색
        audio_files = []
        for ext in ['*.mp3', '*.MP3', '*.wav', '*.WAV', '*.m4a', '*.M4A']:
            audio_files.extend(glob.glob(os.path.join(dir_path, ext)))
        
        if not audio_files:
            print(f"⚠️ 디렉터리에 오디오 파일이 없습니다 (mp3/wav/m4a): {dir_path}")
            sys.exit(1)
        
        audio_files.sort()
        print(f"\n📂 디렉터리: {dir_path}")
        print(f"🎵 발견된 파일: {len(audio_files)}개")
        print("=" * 50)
        
        for i, audio_file in enumerate(audio_files):
            print(f"  {i+1}. {os.path.basename(audio_file)}")
        print("=" * 50 + "\n")
        
        # 변환기 초기화 (1회)
        use_vad = not getattr(args, 'no_vad', False)
        use_context = getattr(args, 'context', False)
        
        converter = MP3ToTextConverter(
            model_size=args.model,
            device=args.device,
            language=args.language,
            use_vad=use_vad,
            use_context=use_context
        )
        
        # 각 파일 변환
        success_count = 0
        fail_count = 0
        
        for i, audio_file in enumerate(audio_files):
            print(f"\n[{i+1}/{len(audio_files)}] 처리 중: {os.path.basename(audio_file)}")
            print("-" * 50)
            
            try:
                # 출력 파일 경로 생성 (확장자 제거)
                base_name = os.path.splitext(audio_file)[0]
                
                converter.transcribe_to_files(
                    audio_file,
                    base_name,
                    time_interval=args.interval
                )
                success_count += 1
                
            except Exception as e:
                print(f"❌ 오류: {e}")
                fail_count += 1
        
        # 최종 요약
        print(f"\n" + "=" * 50)
        print(f"🎉 일괄 변환 완료!")
        print(f"   ✅ 성공: {success_count}개")
        if fail_count > 0:
            print(f"   ❌ 실패: {fail_count}개")
        print("=" * 50)
    
    # 인터랙티브 모드
    elif args.audio_file is None:
        print("=" * 50)
        print("🎤 MP3 → 텍스트 변환기 (무료 로컬 실행)")
        print("=" * 50)
        print("\n모델 크기 옵션:")
        for name, info in MP3ToTextConverter.MODEL_INFO.items():
            print(f"  • {name}: {info['size']} / {info['speed']} / 정확도: {info['accuracy']}")
        
        print("\n파일 경로를 입력하세요 (종료: q):")
        
        converter = None
        while True:
            audio_path = input("\n📁 오디오 파일: ").strip()
            
            if audio_path.lower() == 'q':
                print("👋 종료합니다.")
                break
            
            if not audio_path:
                continue
                
            # 첨 번째 파일 처리 시 모델 로드
            if converter is None:
                model_choice = input("모델 선택 (small/medium/large/large-v3) [large-v3]: ").strip()
                if model_choice not in MP3ToTextConverter.MODEL_INFO:
                    model_choice = "large-v3"
                
                converter = MP3ToTextConverter(model_size=model_choice)
            
            try:
                result = converter.transcribe(audio_path, show_timestamps=args.timestamps)
                print("\n📝 변환 결과:")
                print("-" * 40)
                print(result['text'])
                print("-" * 40)
            except Exception as e:
                print(f"❌ 오류: {e}")
    else:
        # CLI 모드 (단일 파일)
        use_vad = not getattr(args, 'no_vad', False)
        use_context = getattr(args, 'context', False)
        
        converter = MP3ToTextConverter(
            model_size=args.model,
            device=args.device,
            language=args.language,
            use_vad=use_vad,
            use_context=use_context
        )
        
        if args.dual:
            # 두 가지 버전 저장 (_time.md, _full.md)
            # -o 옵션이 있으면 그 값 사용, 없으면 입력 파일명에서 자동 생성
            if args.output:
                output_base = args.output
                if output_base.endswith('.txt') or output_base.endswith('.md'):
                    output_base = output_base[:-4] if output_base.endswith('.txt') else output_base[:-3]
            else:
                # 입력 파일명에서 확장자 제거하여 출력 경로 생성
                output_base = os.path.splitext(args.audio_file)[0]
            
            converter.transcribe_to_files(
                args.audio_file,
                output_base,
                time_interval=args.interval
            )
        elif args.output:
            # 단일 파일 저장
            converter.transcribe_to_file(
                args.audio_file, 
                args.output,
                include_timestamps=args.timestamps
            )
        else:
            result = converter.transcribe(args.audio_file, show_timestamps=args.timestamps)
            print("\n📝 변환 결과:")
            print("=" * 50)
            print(result['text'])
            print("=" * 50)


if __name__ == "__main__":
    main()
