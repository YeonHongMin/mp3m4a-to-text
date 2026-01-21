"""
MP3 to Text Converter - Tkinter GUI
====================================
Native desktop GUI using Python's built-in Tkinter.
No additional GUI library installation required.

Usage:
    python app_tkinter.py
"""

import os
import sys
import threading
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, scrolledtext, messagebox
except ImportError:
    print("❌ Tkinter를 사용할 수 없습니다.")
    sys.exit(1)

try:
    from faster_whisper import WhisperModel
except ImportError:
    print("❌ 'faster-whisper' 라이브러리가 설치되지 않았습니다.")
    print("   설치: pip install faster-whisper")
    sys.exit(1)


class MP3ToTextApp:
    """Tkinter 기반 MP3 → 텍스트 변환 GUI 앱"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🎤 MP3 → 텍스트 변환기")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # 모델 인스턴스
        self.model = None
        self.current_model_size = None
        self.is_processing = False
        
        # 테마 색상 정의
        self.colors = {
            "bg": "#1a1a2e",
            "fg": "#eaeaea",
            "accent": "#7c3aed",
            "accent_hover": "#8b5cf6",
            "card": "#16213e",
            "input_bg": "#0f3460",
            "success": "#10b981",
            "error": "#ef4444",
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        # 메인 컨테이너
        self.root.configure(bg=self.colors["bg"])
        
        # 스타일 설정
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background=self.colors["bg"])
        style.configure("TLabel", background=self.colors["bg"], foreground=self.colors["fg"])
        style.configure("TButton", padding=10)
        style.configure("Accent.TButton", background=self.colors["accent"])
        
        # 헤더
        header = tk.Frame(self.root, bg=self.colors["bg"])
        header.pack(fill="x", padx=20, pady=20)
        
        title_label = tk.Label(
            header,
            text="🎤 MP3 → 텍스트 변환기",
            font=("맑은 고딕", 24, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["fg"]
        )
        title_label.pack()
        
        subtitle_label = tk.Label(
            header,
            text="완전 무료 · 로컬 실행 · 한국어 최적화",
            font=("맑은 고딕", 11),
            bg=self.colors["bg"],
            fg="#9ca3af"
        )
        subtitle_label.pack()
        
        # 설정 영역
        settings_frame = tk.Frame(self.root, bg=self.colors["card"], padx=15, pady=15)
        settings_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # 모델 선택
        model_label = tk.Label(
            settings_frame,
            text="모델:",
            font=("맑은 고딕", 10),
            bg=self.colors["card"],
            fg=self.colors["fg"]
        )
        model_label.grid(row=0, column=0, sticky="w", pady=5)
        
        self.model_var = tk.StringVar(value="medium")
        model_options = [
            ("base (빠름)", "base"),
            ("small (양호)", "small"),
            ("medium (추천)", "medium"),
            ("large-v3 (최고)", "large-v3"),
        ]
        
        for i, (text, value) in enumerate(model_options):
            rb = tk.Radiobutton(
                settings_frame,
                text=text,
                variable=self.model_var,
                value=value,
                font=("맑은 고딕", 9),
                bg=self.colors["card"],
                fg=self.colors["fg"],
                selectcolor=self.colors["input_bg"],
                activebackground=self.colors["card"],
                activeforeground=self.colors["fg"]
            )
            rb.grid(row=0, column=i+1, padx=10, sticky="w")
        
        # 언어 선택
        lang_label = tk.Label(
            settings_frame,
            text="언어:",
            font=("맑은 고딕", 10),
            bg=self.colors["card"],
            fg=self.colors["fg"]
        )
        lang_label.grid(row=1, column=0, sticky="w", pady=5)
        
        self.lang_var = tk.StringVar(value="ko")
        lang_combo = ttk.Combobox(
            settings_frame,
            textvariable=self.lang_var,
            values=["ko (한국어)", "en (영어)", "ja (일본어)", "zh (중국어)", "auto (자동)"],
            state="readonly",
            width=15
        )
        lang_combo.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)
        
        # 타임스탬프 옵션
        self.timestamp_var = tk.BooleanVar(value=False)
        timestamp_cb = tk.Checkbutton(
            settings_frame,
            text="타임스탬프 표시",
            variable=self.timestamp_var,
            font=("맑은 고딕", 9),
            bg=self.colors["card"],
            fg=self.colors["fg"],
            selectcolor=self.colors["input_bg"],
            activebackground=self.colors["card"],
            activeforeground=self.colors["fg"]
        )
        timestamp_cb.grid(row=1, column=3, padx=10, sticky="w")
        
        # 파일 선택 버튼
        button_frame = tk.Frame(self.root, bg=self.colors["bg"])
        button_frame.pack(fill="x", padx=20, pady=10)
        
        self.select_btn = tk.Button(
            button_frame,
            text="📁 파일 선택 및 변환",
            font=("맑은 고딕", 12, "bold"),
            bg=self.colors["accent"],
            fg="white",
            activebackground=self.colors["accent_hover"],
            activeforeground="white",
            relief="flat",
            padx=30,
            pady=10,
            cursor="hand2",
            command=self.select_and_convert
        )
        self.select_btn.pack(side="left")
        
        # 저장 버튼
        self.save_btn = tk.Button(
            button_frame,
            text="💾 저장",
            font=("맑은 고딕", 10),
            bg=self.colors["card"],
            fg=self.colors["fg"],
            activebackground=self.colors["input_bg"],
            activeforeground=self.colors["fg"],
            relief="flat",
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.save_result
        )
        self.save_btn.pack(side="left", padx=10)
        
        # 상태 표시
        self.status_var = tk.StringVar(value="준비됨")
        status_label = tk.Label(
            button_frame,
            textvariable=self.status_var,
            font=("맑은 고딕", 10),
            bg=self.colors["bg"],
            fg="#9ca3af"
        )
        status_label.pack(side="right")
        
        # 결과 영역
        result_frame = tk.Frame(self.root, bg=self.colors["bg"])
        result_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        result_label = tk.Label(
            result_frame,
            text="📝 변환 결과",
            font=("맑은 고딕", 11, "bold"),
            bg=self.colors["bg"],
            fg=self.colors["fg"]
        )
        result_label.pack(anchor="w")
        
        self.result_text = scrolledtext.ScrolledText(
            result_frame,
            wrap=tk.WORD,
            font=("맑은 고딕", 11),
            bg=self.colors["input_bg"],
            fg=self.colors["fg"],
            insertbackground=self.colors["fg"],
            relief="flat",
            padx=10,
            pady=10
        )
        self.result_text.pack(fill="both", expand=True, pady=(5, 0))
        
    def get_device(self):
        """장치 감지"""
        try:
            import torch
            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"
    
    def load_model(self, model_size):
        """모델 로딩"""
        if self.model is not None and self.current_model_size == model_size:
            return self.model
        
        device = self.get_device()
        compute_type = "float16" if device == "cuda" else "int8"
        
        self.update_status(f"모델 로딩 중: {model_size} ({device})...")
        self.model = WhisperModel(model_size, device=device, compute_type=compute_type)
        self.current_model_size = model_size
        
        return self.model
    
    def update_status(self, message):
        """상태 업데이트 (스레드 안전)"""
        self.root.after(0, lambda: self.status_var.set(message))
    
    def select_and_convert(self):
        """파일 선택 및 변환"""
        if self.is_processing:
            return
        
        file_path = filedialog.askopenfilename(
            title="오디오 파일 선택",
            filetypes=[
                ("Audio files", "*.mp3 *.wav *.m4a *.flac *.ogg"),
                ("MP3 files", "*.mp3"),
                ("WAV files", "*.wav"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            # 별도 스레드에서 변환 실행
            thread = threading.Thread(target=self.convert_audio, args=(file_path,))
            thread.start()
    
    def convert_audio(self, file_path):
        """오디오 변환 (백그라운드 스레드)"""
        self.is_processing = True
        self.root.after(0, lambda: self.select_btn.config(state="disabled"))
        
        try:
            model_size = self.model_var.get()
            lang = self.lang_var.get().split()[0]  # "ko (한국어)" → "ko"
            if lang == "auto":
                lang = None
            show_timestamps = self.timestamp_var.get()
            
            model = self.load_model(model_size)
            
            self.update_status(f"변환 중: {Path(file_path).name}")
            
            segments, info = model.transcribe(
                file_path,
                language=lang,
                beam_size=5,
                vad_filter=True
            )
            
            # 결과 조합
            if show_timestamps:
                result_lines = []
                for segment in segments:
                    timestamp = f"[{segment.start:.2f}s → {segment.end:.2f}s]"
                    result_lines.append(f"{timestamp}\n{segment.text}\n")
                result_text = "\n".join(result_lines)
            else:
                result_text = " ".join([seg.text for seg in segments])
            
            # UI 업데이트
            self.root.after(0, lambda: self.display_result(result_text))
            self.update_status(f"✅ 완료! (언어: {info.language}, 확률: {info.language_probability:.1%})")
            
        except Exception as e:
            self.update_status(f"❌ 오류: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("오류", str(e)))
        
        finally:
            self.is_processing = False
            self.root.after(0, lambda: self.select_btn.config(state="normal"))
    
    def display_result(self, text):
        """결과 표시"""
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, text)
    
    def save_result(self):
        """결과 저장"""
        text = self.result_text.get(1.0, tk.END).strip()
        
        if not text:
            messagebox.showwarning("경고", "저장할 텍스트가 없습니다.")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="텍스트 파일 저장",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(text)
            self.update_status(f"💾 저장됨: {Path(file_path).name}")


def main():
    """앱 실행"""
    print("🎤 MP3 → 텍스트 변환기 (Tkinter GUI) 시작")
    
    root = tk.Tk()
    app = MP3ToTextApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
