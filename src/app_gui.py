"""
MP3 to Text Converter - Gradio GUI
===================================
Modern web-style GUI for audio-to-text conversion.
Launch this to get a beautiful browser-based interface.

Usage:
    python app_gui.py
    
Then open http://localhost:7860 in your browser.
"""

import os
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

# Check dependencies
try:
    import gradio as gr
except ImportError:
    print("❌ 'gradio' 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install gradio")
    sys.exit(1)

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ 'faster-whisper' 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install faster-whisper")
    sys.exit(1)


# Global model instance (lazy loading)
_model = None
_current_model_size = None


def get_device():
    """자동 장치 감지"""
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except ImportError:
        return "cpu"


def load_model(model_size: str, progress=None):
    """모델 로딩 (캐싱 적용)"""
    global _model, _current_model_size
    
    if _model is not None and _current_model_size == model_size:
        return _model
    
    device = get_device()
    compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"🔧 모델 로딩: {model_size} ({device})")
    _model = WhisperModel(model_size, device=device, compute_type=compute_type)
    _current_model_size = model_size
    print(f"✅ 모델 로딩 완료!")
    
    return _model


def transcribe_audio_with_progress(audio_file, model_size: str, language: str, 
                                   show_timestamps: bool, vad_filter: bool, 
                                   progress=gr.Progress()):
    """
    오디오 파일을 텍스트로 변환 (진행상황 표시).
    
    Args:
        audio_file: 업로드된 오디오 파일 경로
        model_size: 모델 크기
        language: 언어 코드
        show_timestamps: 타임스탬프 표시 여부
        vad_filter: 음성 구간 필터링 사용 여부
        progress: Gradio 진행상황 tracker
    
    Returns:
        tuple: (변환된 텍스트, 상태 메시지)
    """
    if audio_file is None:
        return "", "⚠️ 오디오 파일을 업로드하거나 마이크로 녹음하세요."
    
    try:
        # 1단계: 모델 로딩
        progress(0.05, desc="🔧 모델 로딩 중...")
        model = load_model(model_size)
        
        # 오디오 길이 확인 (진행률 계산용)
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(audio_file)
            total_duration = len(audio) / 1000.0  # 밀리초 → 초
        except:
            total_duration = 0
        
        # 자동 언어 감지 옵션
        lang_param = None if language == "auto" else language
        
        # 2단계: 변환 시작
        progress(0.1, desc="🎵 오디오 분석 중...")
        segments, info = model.transcribe(
            audio_file,
            language=lang_param,
            beam_size=5,
            vad_filter=vad_filter,
            vad_parameters=dict(threshold=0.05, min_speech_duration_ms=50, min_silence_duration_ms=50) if vad_filter else None
        )
        
        # 3단계: 세그먼트 처리 (실시간 진행상황)
        result_lines = []
        segment_count = 0
        
        for segment in segments:
            segment_count += 1
            
            # 오디오 시간 기반 진행률 (10% ~ 95%)
            if total_duration > 0:
                current_progress = 0.1 + (0.85 * min(segment.end / total_duration, 1.0))
                time_str = f"{int(segment.end//60)}:{int(segment.end%60):02d}/{int(total_duration//60)}:{int(total_duration%60):02d}"
            else:
                current_progress = min(0.1 + (segment_count * 0.01), 0.9)
                time_str = f"{segment_count}개"
            
            progress(current_progress, desc=f"📝 변환 중... {time_str}")
            
            if show_timestamps:
                timestamp = f"[{segment.start:.2f}s → {segment.end:.2f}s]"
                result_lines.append(f"{timestamp}\n{segment.text}\n")
            else:
                result_lines.append(segment.text)
        
        # 4단계: 완료
        progress(1.0, desc="✅ 완료!")
        
        if show_timestamps:
            result_text = "\n".join(result_lines)
        else:
            result_text = " ".join(result_lines)
        
        status = f"✅ 완료! | 언어: {info.language} ({info.language_probability:.1%}) | {segment_count}개 세그먼트 | {get_device()}"
        
        return result_text.strip(), status
        
    except Exception as e:
        return "", f"❌ 오류 발생: {str(e)}"


def save_result(text: str, audio_file):
    """결과를 파일로 저장 (원본 파일 위치에 저장)"""
    if not text:
        return "⚠️ 저장할 텍스트가 없습니다."
    
    # 파일명 생성
    if audio_file:
        audio_path = Path(audio_file)
        # 원본 파일명 + _transcript.txt
        output_path = audio_path.parent / f"{audio_path.stem}_transcript.txt"
    else:
        output_path = Path("transcript.txt")
    
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        return f"📄 저장 완료: {output_path.name}"
    except Exception as e:
        return f"❌ 저장 실패: {e}" 


# Gradio 테마 설정 (밝은 테마)
theme = gr.themes.Soft(
    primary_hue="violet",
    secondary_hue="slate",
    neutral_hue="gray",
).set(
    # 밝은 배경
    body_background_fill="*neutral_50",
    body_background_fill_dark="*neutral_100",
    block_background_fill="white",
    block_background_fill_dark="*neutral_50",
    # 텍스트 색상
    block_title_text_color="*neutral_800",
    block_label_text_color="*neutral_600",
    body_text_color="*neutral_800",
    # 입력 필드
    input_background_fill="white",
    input_background_fill_dark="white",
    input_border_color="*neutral_300",
    # 버튼
    button_primary_background_fill="*primary_500",
    button_primary_text_color="white",
)

# 커스텀 CSS
custom_css = """
.gradio-container {
    max-width: 100% !important;
    width: 100% !important;
    margin: 0 !important;
    padding: 15px !important;
}
.main-row {
    display: flex !important;
    flex-direction: row !important;
    flex-wrap: nowrap !important;
    min-height: 80vh !important;
    gap: 20px !important;
    width: 100% !important;
}
.input-panel {
    flex: 0 0 350px !important;
    width: 350px !important;
    min-width: 350px !important;
    max-width: 350px !important;
}
.output-panel {
    flex: 1 1 auto !important;
    min-width: 400px !important;
    width: auto !important;
}
"""

# Gradio 인터페이스 구성
with gr.Blocks(theme=theme, title="MP3 → Text Converter", css=custom_css) as demo:
    gr.Markdown("# 🎤 MP3 → 텍스트 변환기")
    
    with gr.Row(elem_classes=["main-row"]):
        # ========== 왼쪽: 입력 ==========
        with gr.Column(scale=1, elem_classes=["input-panel"]):
            gr.Markdown("## 📁 입력")
            
            audio_input = gr.Audio(
                type="filepath",
                label="오디오 파일",
                sources=["upload", "microphone"],
            )
            
            gr.Markdown("---")
            
            model_dropdown = gr.Dropdown(
                choices=[
                    ("base (~75MB) - 빠름", "base"),
                    ("small (~250MB) - 양호", "small"),
                    ("medium (~750MB) - 균형", "medium"),
                    ("large-v3 (~3GB) - 최고 ⭐", "large-v3"),
                ],
                value="large-v3",
                label="🤖 모델",
            )
            
            language_dropdown = gr.Dropdown(
                choices=[
                    ("자동", "auto"),
                    ("한국어", "ko"),
                    ("영어", "en"),
                    ("일본어", "ja"),
                ],
                value="ko",
                label="🌐 언어",
            )
            
            with gr.Row():
                show_timestamps = gr.Checkbox(value=False, label="⏱️ 타임스탬프")
                vad_filter = gr.Checkbox(value=True, label="🎯 VAD")
            
            convert_btn = gr.Button("🔄 변환 시작", variant="primary", size="lg")
            
            status_text = gr.Textbox(
                label="📊 상태",
                interactive=False,
                lines=1,
                value="대기 중...",
            )
        
        # ========== 오른쪽: 결과 ==========
        with gr.Column(scale=2, elem_classes=["output-panel"]):
            gr.Markdown("## 📝 변환 결과")
            
            output_text = gr.Textbox(
                label="",
                lines=30,
                max_lines=2000,
                placeholder="변환된 텍스트가 여기에 표시됩니다...",
            )
            
            with gr.Row():
                save_btn = gr.Button("💾 파일로 저장", variant="secondary", size="lg")
    
    # 이벤트 연결
    convert_btn.click(
        fn=transcribe_audio_with_progress,
        inputs=[audio_input, model_dropdown, language_dropdown, show_timestamps, vad_filter],
        outputs=[output_text, status_text],
    )
    
    save_btn.click(
        fn=save_result,
        inputs=[output_text, audio_input],
        outputs=[status_text],  # 저장 상태도 왼쪽 상태창에 표시
    )


if __name__ == "__main__":
    print("=" * 50)
    print("🎤 MP3 → 텍스트 변환기 GUI 시작")
    print("=" * 50)
    print(f"장치: {get_device()}")
    print("브라우저에서 http://localhost:7860 을 열어주세요")
    print("=" * 50)
    
    demo.launch(
        server_name="0.0.0.0",  # 로컬 네트워크에서도 접근 가능
        server_port=7860,
        share=False,  # True로 하면 외부 공유 링크 생성
        inbrowser=True,  # 자동으로 브라우저 열기
    )
