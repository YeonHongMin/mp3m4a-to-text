"""
MP3 to Text Converter - Web UI with Progress Monitoring
========================================================
Flask 기반 웹 UI로 MP3 변환 진행 상황을 실시간 모니터링합니다.
파일 경로 입력 또는 파일 업로드 두 가지 방식을 지원합니다.

Usage:
    python web_ui.py
    # 브라우저에서 http://localhost:5001 접속
"""

import os
import sys
import json
import threading
import time
import tempfile
import uuid
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename

# Flask 설치 확인
try:
    from flask import Flask, render_template_string, jsonify, request
except ImportError:
    print("❌ Flask가 설치되지 않았습니다.")
    print("   설치: pip install flask")
    sys.exit(1)

# 상위 디렉토리 모듈 import
sys.path.insert(0, str(Path(__file__).parent))
from mp3_to_text import MP3ToTextConverter

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB 제한
app.config['UPLOAD_FOLDER'] = tempfile.gettempdir()

# 허용 확장자
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'm4a', 'ogg', 'wma'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# 전역 상태 관리
conversion_state = {
    "status": "idle",  # idle, loading_model, transcribing, completed, error
    "progress": 0,
    "current_segment": 0,
    "total_segments": 0,
    "elapsed_time": 0,
    "current_text": "",
    "full_text": "",
    "error_message": "",
    "file_name": "",
    "model": "",
    "start_time": None,
    "segments": []
}

# 상태 잠금
state_lock = threading.Lock()


def update_state(**kwargs):
    """스레드 안전하게 상태 업데이트"""
    with state_lock:
        conversion_state.update(kwargs)


def get_state():
    """현재 상태 반환"""
    with state_lock:
        return dict(conversion_state)


def run_conversion(audio_path: str, model_size: str = "large-v3", language: str = "ko"):
    """백그라운드에서 변환 실행"""
    try:
        update_state(
            status="loading_model",
            progress=5,
            file_name=os.path.basename(audio_path),
            model=model_size,
            start_time=time.time(),
            segments=[],
            full_text="",
            error_message=""
        )
        
        # 모델 로딩
        converter = MP3ToTextConverter(
            model_size=model_size,
            language=language
        )
        
        update_state(status="transcribing", progress=10)
        
        # 변환 실행
        start_time = time.time()
        
        segments_gen, info = converter.model.transcribe(
            audio_path,
            language=language,
            beam_size=5,
            vad_filter=True,
        )
        
        segment_list = []
        full_text_parts = []
        
        for i, segment in enumerate(segments_gen):
            seg_data = {
                "id": i + 1,
                "start": round(segment.start, 2),
                "end": round(segment.end, 2),
                "text": segment.text.strip()
            }
            segment_list.append(seg_data)
            full_text_parts.append(segment.text)
            
            elapsed = time.time() - start_time
            # 진행률: 세그먼트 수 기반 (10~90%)
            progress = min(10 + (i + 1) * 2, 90)
            
            update_state(
                current_segment=i + 1,
                progress=progress,
                elapsed_time=round(elapsed, 1),
                current_text=segment.text.strip(),
                segments=segment_list.copy()
            )
        
        full_text = " ".join(full_text_parts).strip()
        total_time = time.time() - start_time
        
        update_state(
            status="completed",
            progress=100,
            elapsed_time=round(total_time, 1),
            full_text=full_text,
            total_segments=len(segment_list),
            segments=segment_list
        )
        
    except Exception as e:
        update_state(
            status="error",
            error_message=str(e),
            progress=0
        )


# HTML 템플릿
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎤 MP3 → Text Converter</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary: #6366f1;
            --primary-dark: #4f46e5;
            --primary-light: #818cf8;
            --success: #10b981;
            --warning: #f59e0b;
            --error: #ef4444;
            --bg-dark: #0f172a;
            --bg-card: #1e293b;
            --bg-input: #334155;
            --text-primary: #f1f5f9;
            --text-secondary: #94a3b8;
            --border: #475569;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: linear-gradient(135deg, var(--bg-dark) 0%, #1a1a2e 100%);
            min-height: 100vh;
            color: var(--text-primary);
            padding: 2rem;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            margin-bottom: 2rem;
            animation: fadeInDown 0.6s ease-out;
        }
        
        .header h1 {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-light), var(--primary));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.5rem;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .card {
            background: var(--bg-card);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 1.5rem;
            border: 1px solid var(--border);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3);
            animation: fadeInUp 0.6s ease-out;
        }
        
        .card-title {
            font-size: 1.25rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        
        /* Tab Styles */
        .tab-container {
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1.5rem;
            background: var(--bg-input);
            border-radius: 10px;
            padding: 0.25rem;
        }
        
        .tab-btn {
            flex: 1;
            padding: 0.75rem 1rem;
            background: transparent;
            border: none;
            color: var(--text-secondary);
            font-size: 0.95rem;
            font-weight: 500;
            cursor: pointer;
            border-radius: 8px;
            transition: all 0.2s;
        }
        
        .tab-btn.active {
            background: var(--primary);
            color: white;
        }
        
        .tab-btn:hover:not(.active) {
            background: rgba(99, 102, 241, 0.2);
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        .form-group {
            margin-bottom: 1.5rem;
        }
        
        .form-group label {
            display: block;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 0.5rem;
            color: var(--text-secondary);
        }
        
        .form-group input[type="text"],
        .form-group select {
            width: 100%;
            padding: 0.875rem 1rem;
            background: var(--bg-input);
            border: 1px solid var(--border);
            border-radius: 10px;
            color: var(--text-primary);
            font-size: 1rem;
            transition: all 0.2s;
        }
        
        .form-group input:focus,
        .form-group select:focus {
            outline: none;
            border-color: var(--primary);
            box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
        }
        
        /* File Upload Styles */
        .file-upload-area {
            border: 2px dashed var(--border);
            border-radius: 12px;
            padding: 2rem;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
            background: var(--bg-input);
        }
        
        .file-upload-area:hover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.1);
        }
        
        .file-upload-area.dragover {
            border-color: var(--primary);
            background: rgba(99, 102, 241, 0.2);
            transform: scale(1.02);
        }
        
        .file-upload-area.has-file {
            border-color: var(--success);
            background: rgba(16, 185, 129, 0.1);
        }
        
        .file-upload-icon {
            font-size: 3rem;
            margin-bottom: 1rem;
        }
        
        .file-upload-text {
            color: var(--text-secondary);
            margin-bottom: 0.5rem;
        }
        
        .file-upload-text strong {
            color: var(--primary-light);
        }
        
        .file-upload-hint {
            font-size: 0.8rem;
            color: var(--text-secondary);
            opacity: 0.7;
        }
        
        .file-info {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 1rem;
            background: var(--bg-dark);
            border-radius: 8px;
            margin-top: 1rem;
        }
        
        .file-info-icon {
            font-size: 2rem;
        }
        
        .file-info-details {
            flex: 1;
            text-align: left;
        }
        
        .file-info-name {
            font-weight: 600;
            color: var(--text-primary);
            word-break: break-all;
        }
        
        .file-info-size {
            font-size: 0.85rem;
            color: var(--text-secondary);
        }
        
        .file-info-remove {
            background: none;
            border: none;
            color: var(--error);
            cursor: pointer;
            font-size: 1.25rem;
            padding: 0.5rem;
        }
        
        #fileInput {
            display: none;
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            padding: 1rem 2rem;
            font-size: 1rem;
            font-weight: 600;
            border: none;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.2s;
            width: 100%;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, var(--primary), var(--primary-dark));
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px -10px rgba(99, 102, 241, 0.5);
        }
        
        .btn-primary:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        /* Progress Section */
        .progress-section {
            display: none;
        }
        
        .progress-section.active {
            display: block;
        }
        
        .progress-bar-container {
            background: var(--bg-input);
            border-radius: 999px;
            height: 12px;
            overflow: hidden;
            margin-bottom: 1rem;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--primary), var(--primary-light));
            border-radius: 999px;
            transition: width 0.3s ease;
            position: relative;
        }
        
        .progress-bar::after {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: linear-gradient(
                90deg,
                transparent,
                rgba(255, 255, 255, 0.2),
                transparent
            );
            animation: shimmer 1.5s infinite;
        }
        
        @keyframes shimmer {
            0% { transform: translateX(-100%); }
            100% { transform: translateX(100%); }
        }
        
        .progress-info {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
        }
        
        .progress-percent {
            font-size: 2rem;
            font-weight: 700;
            color: var(--primary-light);
        }
        
        .progress-stats {
            text-align: right;
            color: var(--text-secondary);
            font-size: 0.875rem;
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            padding: 0.5rem 1rem;
            border-radius: 999px;
            font-size: 0.875rem;
            font-weight: 500;
            margin-bottom: 1rem;
        }
        
        .status-loading {
            background: rgba(99, 102, 241, 0.2);
            color: var(--primary-light);
        }
        
        .status-transcribing {
            background: rgba(245, 158, 11, 0.2);
            color: var(--warning);
        }
        
        .status-completed {
            background: rgba(16, 185, 129, 0.2);
            color: var(--success);
        }
        
        .status-error {
            background: rgba(239, 68, 68, 0.2);
            color: var(--error);
        }
        
        .spinner {
            width: 16px;
            height: 16px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        /* Live Text */
        .live-text {
            background: var(--bg-input);
            border-radius: 10px;
            padding: 1rem;
            min-height: 60px;
            font-size: 0.95rem;
            line-height: 1.6;
            color: var(--text-secondary);
            border-left: 3px solid var(--primary);
        }
        
        /* Segments Log */
        .segments-log {
            max-height: 400px;
            overflow-y: auto;
            background: var(--bg-input);
            border-radius: 10px;
            padding: 1rem;
        }
        
        .segment-item {
            padding: 0.75rem;
            border-bottom: 1px solid var(--border);
            animation: fadeIn 0.3s ease-out;
        }
        
        .segment-item:last-child {
            border-bottom: none;
        }
        
        .segment-time {
            font-size: 0.75rem;
            color: var(--primary-light);
            font-weight: 500;
            margin-bottom: 0.25rem;
        }
        
        .segment-text {
            color: var(--text-primary);
            font-size: 0.9rem;
            line-height: 1.5;
        }
        
        /* Result Section */
        .result-section {
            display: none;
        }
        
        .result-section.active {
            display: block;
        }
        
        .result-text {
            background: var(--bg-input);
            border-radius: 10px;
            padding: 1.5rem;
            max-height: 500px;
            overflow-y: auto;
            font-size: 1rem;
            line-height: 1.8;
            white-space: pre-wrap;
        }
        
        .btn-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }
        
        .btn-copy {
            background: var(--bg-input);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 0.75rem 1.5rem;
            width: auto;
            flex: 1;
            min-width: 120px;
        }
        
        .btn-copy:hover {
            background: var(--border);
        }
        
        /* Animations */
        @keyframes fadeInUp {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeInDown {
            from {
                opacity: 0;
                transform: translateY(-20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        /* Responsive */
        @media (max-width: 640px) {
            body {
                padding: 1rem;
            }
            
            .header h1 {
                font-size: 1.75rem;
            }
            
            .card {
                padding: 1.5rem;
            }
            
            .btn-group {
                flex-direction: column;
            }
            
            .btn-copy {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎤 MP3 → Text Converter</h1>
            <p>로컬에서 실행되는 무료 음성-텍스트 변환기</p>
        </div>
        
        <!-- Input Form -->
        <div class="card" id="inputCard">
            <h2 class="card-title">📁 오디오 파일 선택</h2>
            
            <!-- Tab Navigation -->
            <div class="tab-container">
                <button class="tab-btn active" onclick="switchTab('upload')">📤 파일 업로드</button>
                <button class="tab-btn" onclick="switchTab('path')">📂 경로 입력</button>
            </div>
            
            <!-- Tab: File Upload -->
            <div class="tab-content active" id="tab-upload">
                <div class="file-upload-area" id="dropZone" onclick="document.getElementById('fileInput').click()">
                    <div class="file-upload-icon">📁</div>
                    <div class="file-upload-text">
                        <strong>클릭</strong>하거나 파일을 <strong>드래그</strong>하세요
                    </div>
                    <div class="file-upload-hint">MP3, WAV, FLAC, M4A, OGG 지원 (최대 500MB)</div>
                </div>
                <input type="file" id="fileInput" accept=".mp3,.wav,.flac,.m4a,.ogg,.wma">
                <div class="file-info" id="fileInfo" style="display: none;">
                    <div class="file-info-icon">🎵</div>
                    <div class="file-info-details">
                        <div class="file-info-name" id="fileName"></div>
                        <div class="file-info-size" id="fileSize"></div>
                    </div>
                    <button class="file-info-remove" onclick="removeFile()" title="파일 제거">✕</button>
                </div>
            </div>
            
            <!-- Tab: Path Input -->
            <div class="tab-content" id="tab-path">
                <div class="form-group">
                    <label for="audioPath">오디오 파일 경로</label>
                    <input type="text" id="audioPath" placeholder="/path/to/audio.mp3">
                </div>
            </div>
            
            <div class="form-group">
                <label for="modelSelect">모델 선택</label>
                <select id="modelSelect">
                    <option value="small">Small (~250MB) - 빠름, 양호한 정확도</option>
                    <option value="medium">Medium (~750MB) - 보통, 좋은 정확도</option>
                    <option value="large">Large (~1.5GB) - 느림, 매우 좋은 정확도</option>
                    <option value="large-v3" selected>Large-v3 (~3GB) - 가장 느림, 최고 정확도 (추천)</option>
                </select>
            </div>
            
            <button class="btn btn-primary" id="startBtn" onclick="startConversion()">
                🚀 변환 시작
            </button>
        </div>
        
        <!-- Progress Section -->
        <div class="card progress-section" id="progressSection">
            <h2 class="card-title">📊 진행 상황</h2>
            
            <div id="statusBadge" class="status-badge status-loading">
                <div class="spinner"></div>
                <span>모델 로딩 중...</span>
            </div>
            
            <div class="progress-bar-container">
                <div class="progress-bar" id="progressBar" style="width: 0%"></div>
            </div>
            
            <div class="progress-info">
                <div class="progress-percent" id="progressPercent">0%</div>
                <div class="progress-stats">
                    <div id="segmentCount">세그먼트: 0개</div>
                    <div id="elapsedTime">경과 시간: 0초</div>
                </div>
            </div>
            
            <div class="form-group">
                <label>🎯 현재 처리 중</label>
                <div class="live-text" id="liveText">대기 중...</div>
            </div>
        </div>
        
        <!-- Segments Log -->
        <div class="card progress-section" id="logSection">
            <h2 class="card-title">📜 실시간 로그</h2>
            <div class="segments-log" id="segmentsLog"></div>
        </div>
        
        <!-- Result Section -->
        <div class="card result-section" id="resultSection">
            <h2 class="card-title">✅ 변환 완료</h2>
            
            <div class="btn-group">
                <button class="btn btn-copy" onclick="copyResult()">📋 복사</button>
                <button class="btn btn-copy" onclick="downloadResult()">💾 다운로드</button>
                <button class="btn btn-copy" onclick="resetForm()">🔄 새로 시작</button>
            </div>
            
            <div class="result-text" id="resultText"></div>
        </div>
    </div>
    
    <script>
        let pollInterval = null;
        let selectedFile = null;
        let currentTab = 'upload';
        
        // Tab switching
        function switchTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            if (tab === 'upload') {
                document.querySelectorAll('.tab-btn')[0].classList.add('active');
                document.getElementById('tab-upload').classList.add('active');
            } else {
                document.querySelectorAll('.tab-btn')[1].classList.add('active');
                document.getElementById('tab-path').classList.add('active');
            }
        }
        
        // File upload handling
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.classList.add('dragover');
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.classList.remove('dragover');
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                handleFile(fileInput.files[0]);
            }
        });
        
        function handleFile(file) {
            const allowedExtensions = ['mp3', 'wav', 'flac', 'm4a', 'ogg', 'wma'];
            const ext = file.name.split('.').pop().toLowerCase();
            
            if (!allowedExtensions.includes(ext)) {
                alert('지원하지 않는 파일 형식입니다.\\n지원 형식: MP3, WAV, FLAC, M4A, OGG, WMA');
                return;
            }
            
            selectedFile = file;
            dropZone.classList.add('has-file');
            document.getElementById('fileInfo').style.display = 'flex';
            document.getElementById('fileName').textContent = file.name;
            document.getElementById('fileSize').textContent = formatFileSize(file.size);
        }
        
        function removeFile() {
            selectedFile = null;
            fileInput.value = '';
            dropZone.classList.remove('has-file');
            document.getElementById('fileInfo').style.display = 'none';
        }
        
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }
        
        async function startConversion() {
            const model = document.getElementById('modelSelect').value;
            let audioPath = '';
            
            if (currentTab === 'upload') {
                if (!selectedFile) {
                    alert('파일을 선택하세요.');
                    return;
                }
                
                // Upload file first
                document.getElementById('startBtn').disabled = true;
                document.getElementById('startBtn').textContent = '📤 파일 업로드 중...';
                
                const formData = new FormData();
                formData.append('file', selectedFile);
                
                try {
                    const uploadResponse = await fetch('/api/upload', {
                        method: 'POST',
                        body: formData
                    });
                    
                    if (!uploadResponse.ok) {
                        const error = await uploadResponse.json();
                        throw new Error(error.error || '파일 업로드 실패');
                    }
                    
                    const uploadResult = await uploadResponse.json();
                    audioPath = uploadResult.path;
                } catch (e) {
                    alert('파일 업로드 오류: ' + e.message);
                    document.getElementById('startBtn').disabled = false;
                    document.getElementById('startBtn').textContent = '🚀 변환 시작';
                    return;
                }
            } else {
                audioPath = document.getElementById('audioPath').value.trim();
                if (!audioPath) {
                    alert('오디오 파일 경로를 입력하세요.');
                    return;
                }
            }
            
            // Start conversion
            document.getElementById('startBtn').disabled = true;
            document.getElementById('startBtn').textContent = '🚀 변환 시작';
            document.getElementById('progressSection').classList.add('active');
            document.getElementById('logSection').classList.add('active');
            document.getElementById('resultSection').classList.remove('active');
            document.getElementById('segmentsLog').innerHTML = '';
            
            try {
                const response = await fetch('/api/convert', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ audio_path: audioPath, model: model })
                });
                
                if (response.ok) {
                    startPolling();
                } else {
                    const error = await response.json();
                    alert('오류: ' + error.message);
                    document.getElementById('startBtn').disabled = false;
                }
            } catch (e) {
                alert('서버 연결 오류: ' + e.message);
                document.getElementById('startBtn').disabled = false;
            }
        }
        
        function startPolling() {
            pollInterval = setInterval(async () => {
                try {
                    const response = await fetch('/api/status');
                    const state = await response.json();
                    updateUI(state);
                    
                    if (state.status === 'completed' || state.status === 'error') {
                        clearInterval(pollInterval);
                        pollInterval = null;
                    }
                } catch (e) {
                    console.error('Polling error:', e);
                }
            }, 500);
        }
        
        function updateUI(state) {
            // Progress bar
            document.getElementById('progressBar').style.width = state.progress + '%';
            document.getElementById('progressPercent').textContent = state.progress + '%';
            
            // Stats
            document.getElementById('segmentCount').textContent = `세그먼트: ${state.current_segment}개`;
            document.getElementById('elapsedTime').textContent = `경과 시간: ${state.elapsed_time}초`;
            
            // Live text
            if (state.current_text) {
                document.getElementById('liveText').textContent = state.current_text;
            }
            
            // Status badge
            const badge = document.getElementById('statusBadge');
            if (state.status === 'loading_model') {
                badge.className = 'status-badge status-loading';
                badge.innerHTML = '<div class="spinner"></div><span>모델 로딩 중...</span>';
            } else if (state.status === 'transcribing') {
                badge.className = 'status-badge status-transcribing';
                badge.innerHTML = '<div class="spinner"></div><span>변환 중...</span>';
            } else if (state.status === 'completed') {
                badge.className = 'status-badge status-completed';
                badge.innerHTML = '<span>✅ 완료</span>';
                showResult(state);
            } else if (state.status === 'error') {
                badge.className = 'status-badge status-error';
                badge.innerHTML = '<span>❌ 오류: ' + state.error_message + '</span>';
                document.getElementById('startBtn').disabled = false;
            }
            
            // Segments log
            updateSegmentsLog(state.segments);
        }
        
        function updateSegmentsLog(segments) {
            const log = document.getElementById('segmentsLog');
            const currentCount = log.children.length;
            
            for (let i = currentCount; i < segments.length; i++) {
                const seg = segments[i];
                const item = document.createElement('div');
                item.className = 'segment-item';
                item.innerHTML = `
                    <div class="segment-time">[${seg.start}s → ${seg.end}s]</div>
                    <div class="segment-text">${seg.text}</div>
                `;
                log.appendChild(item);
                log.scrollTop = log.scrollHeight;
            }
        }
        
        function showResult(state) {
            document.getElementById('resultSection').classList.add('active');
            document.getElementById('resultText').textContent = state.full_text;
            document.getElementById('startBtn').disabled = false;
        }
        
        function copyResult() {
            const text = document.getElementById('resultText').textContent;
            navigator.clipboard.writeText(text).then(() => {
                alert('클립보드에 복사되었습니다!');
            });
        }
        
        function downloadResult() {
            const text = document.getElementById('resultText').textContent;
            const blob = new Blob([text], { type: 'text/plain;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'transcription.txt';
            a.click();
            URL.revokeObjectURL(url);
        }
        
        function resetForm() {
            document.getElementById('progressSection').classList.remove('active');
            document.getElementById('logSection').classList.remove('active');
            document.getElementById('resultSection').classList.remove('active');
            document.getElementById('segmentsLog').innerHTML = '';
            document.getElementById('progressBar').style.width = '0%';
            document.getElementById('progressPercent').textContent = '0%';
            document.getElementById('liveText').textContent = '대기 중...';
            removeFile();
            document.getElementById('audioPath').value = '';
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """메인 페이지"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/upload', methods=['POST'])
def api_upload():
    """파일 업로드 API"""
    if 'file' not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400
    
    # 안전한 파일명 생성
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
    
    # 파일 저장
    file.save(filepath)
    
    return jsonify({"path": filepath, "filename": filename})


@app.route('/api/convert', methods=['POST'])
def api_convert():
    """변환 시작 API"""
    data = request.get_json()
    audio_path = data.get('audio_path')
    model = data.get('model', 'large-v3')
    
    if not audio_path:
        return jsonify({"error": "audio_path is required"}), 400
    
    if not os.path.exists(audio_path):
        return jsonify({"error": f"File not found: {audio_path}"}), 404
    
    # 백그라운드 스레드에서 변환 실행
    thread = threading.Thread(target=run_conversion, args=(audio_path, model))
    thread.daemon = True
    thread.start()
    
    return jsonify({"status": "started"})


@app.route('/api/status')
def api_status():
    """현재 변환 상태 반환"""
    return jsonify(get_state())


def main():
    """웹 서버 시작"""
    print("=" * 50)
    print("🎤 MP3 → Text Converter Web UI")
    print("=" * 50)
    print("\n📡 서버 시작 중...")
    print("🌐 브라우저에서 접속: http://localhost:5001")
    print("\n종료하려면 Ctrl+C를 누르세요.\n")
    
    app.run(host='0.0.0.0', port=5001, debug=False, threaded=True)


if __name__ == "__main__":
    main()
