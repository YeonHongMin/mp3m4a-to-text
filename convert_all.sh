#!/bin/bash
# =============================================================================
# MP3 to Text 일괄 변환 스크립트
# mp3 디렉터리의 모든 하위 디렉터리에 있는 오디오 파일을 텍스트로 변환
# =============================================================================

# nohup으로 실행 중인지 확인하고 로그 파일 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -t 0 ]; then
    # 인터랙티브 모드 (터미널 연결됨)
    LOG_FILE=""
else
    # nohup 모드 (터미널 연결 안됨)
    LOG_FILE="${SCRIPT_DIR}/convert_all.log"
    exec > >(tee -a "$LOG_FILE") 2>&1
fi

set -e  # 오류 발생 시 중단

# CUDA 라이브러리 경로 설정 (CTranslate2 CUDA 빌드용)
export LD_LIBRARY_PATH=/tmp/CTranslate2/install/lib:$LD_LIBRARY_PATH

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 스크립트 위치 기준으로 프로젝트 루트 설정
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$SCRIPT_DIR"
MP3_DIR="$PROJECT_ROOT/mp3"
SRC_DIR="$PROJECT_ROOT/src"

# 기본 설정
USE_VAD=false
INTERVAL=30
AUTO_YES=false

# 사용법 출력
usage() {
    echo -e "${BLUE}사용법:${NC} $0 [옵션]"
    echo ""
    echo "옵션:"
    echo "  --vad           VAD 활성화 (음성 구간만 처리, 속도 향상)"
    echo "  --interval N    시간 구간 (초, 기본값: 30)"
    echo "  --yes, -y       확인 없이 바로 실행 (백그라운드용)"
    echo "  --help, -h      도움말 출력"
    echo ""
    echo "예제:"
    echo "  $0                    # 기본 설정으로 변환"
    echo "  $0 --vad              # VAD 활성화"
    echo "  $0 --interval 60      # 60초 간격으로 분할"
    echo "  $0 --vad --yes        # 백그라운드 실행"
    echo ""
    echo "nohup 실행 (백그라운드):"
    echo "  nohup $0 --yes > convert_all.log 2>&1 &"
    echo "  # 또는 (스크립트가 자동으로 로그 파일 생성)"
    echo "  nohup $0 --yes &"
    exit 0
}

# 인자 파싱
while [[ $# -gt 0 ]]; do
    case $1 in
        --vad)
            USE_VAD=true
            shift
            ;;
        --interval)
            INTERVAL="$2"
            shift 2
            ;;
        -y|--yes)
            AUTO_YES=true
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            echo -e "${RED}알 수 없는 옵션: $1${NC}"
            usage
            ;;
    esac
done

# 환경 확인
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   MP3 to Text 일괄 변환 스크립트${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Python 환경 확인
if [ -d "$PROJECT_ROOT/.venv" ]; then
    echo -e "${GREEN}✓ 가상환경 발견: .venv${NC}"
    source "$PROJECT_ROOT/.venv/bin/activate"
elif [ -d "$PROJECT_ROOT/venv" ]; then
    echo -e "${GREEN}✓ 가상환경 발견: venv${NC}"
    source "$PROJECT_ROOT/venv/bin/activate"
else
    echo -e "${YELLOW}⚠ 가상환경 없음 - 시스템 Python 사용${NC}"
fi

# 디렉터리 확인
if [ ! -d "$MP3_DIR" ]; then
    echo -e "${RED}✗ mp3 디렉터리를 찾을 수 없습니다: $MP3_DIR${NC}"
    exit 1
fi

if [ ! -f "$SRC_DIR/mp3_to_text.py" ]; then
    echo -e "${RED}✗ mp3_to_text.py를 찾을 수 없습니다: $SRC_DIR/mp3_to_text.py${NC}"
    exit 1
fi

# 오디오 파일이 있는 모든 디렉터리 목록 가져오기 (깊은 depth 포함)
# 먼저 오디오 파일을 찾고, 해당 파일이 있는 디렉터리만 추출
# mapfile을 사용하여 공백이 있는 경로도 올바르게 처리
mapfile -t SUBDIRS < <(find "$MP3_DIR" -type f \( -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" -o -name "*.asf" \) -printf '%h\n' 2>/dev/null | sort -u)
TOTAL_DIRS=${#SUBDIRS[@]}

if [ $TOTAL_DIRS -eq 0 ]; then
    echo -e "${YELLOW}변환할 디렉터리가 없습니다.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}설정:${NC}"
echo "  - 대상 디렉터리: $MP3_DIR"
echo "  - 하위 디렉터리 수: $TOTAL_DIRS"
echo "  - VAD: $([ "$USE_VAD" = true ] && echo '활성화' || echo '비활성화')"
echo "  - 시간 구간: ${INTERVAL}초"
echo ""

# 옵션 문자열 생성
OPTIONS=""
if [ "$USE_VAD" = true ]; then
    OPTIONS="$OPTIONS --vad"
fi
OPTIONS="$OPTIONS --interval $INTERVAL"

# 변환 시작 확인
echo -e "${YELLOW}변환할 디렉터리 목록:${NC}"
total_unprocessed=0
for dir in "${SUBDIRS[@]}"; do
    dir_name=$(basename "$dir")
    audio_files=($(find "$dir" -maxdepth 1 \( -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" -o -name "*.asf" \) -type f -printf '%f\n' 2>/dev/null))
    file_count=${#audio_files[@]}
    
    # 변환되지 않은 파일 수 계산
    unprocessed=0
    for audio_file in "${audio_files[@]}"; do
        base_name="${dir}/${audio_file%.*}"
        if [ ! -f "${base_name}_time.md" ] && [ ! -f "${base_name}_full.md" ]; then
            unprocessed=$((unprocessed + 1))
        fi
    done
    
    total_unprocessed=$((total_unprocessed + unprocessed))
    
    if [ $unprocessed -eq 0 ] && [ $file_count -gt 0 ]; then
        echo "  - $dir_name (파일 수: $file_count, 모두 변환 완료)"
    elif [ $unprocessed -gt 0 ]; then
        echo "  - $dir_name (파일 수: $file_count, 변환 필요: $unprocessed개)"
    else
        echo "  - $dir_name (파일 수: $file_count)"
    fi
done
echo ""
if [ $total_unprocessed -gt 0 ]; then
    echo -e "${BLUE}총 변환 필요 파일: ${total_unprocessed}개${NC}"
fi
echo ""

# 변환 시작 확인
if [ "$AUTO_YES" = false ] && [ -t 0 ]; then
    # 인터랙티브 모드일 때만 확인
    read -p "변환을 시작하시겠습니까? (y/n): " confirm
    if [[ ! "$confirm" =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}취소되었습니다.${NC}"
        exit 0
    fi
elif [ "$AUTO_YES" = false ] && [ ! -t 0 ]; then
    # nohup 모드에서는 자동으로 시작
    echo -e "${BLUE}백그라운드 모드로 자동 시작합니다.${NC}"
fi

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   변환 시작${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""

# 시작 시간
START_TIME=$(date +%s)

# 각 디렉터리 처리
CURRENT=0
SUCCESS=0
FAILED=0
SKIPPED=0

for dir in "${SUBDIRS[@]}"; do
    CURRENT=$((CURRENT + 1))
    dir_name=$(basename "$dir")
    
    echo -e "${BLUE}[$CURRENT/$TOTAL_DIRS] 처리 중: $dir_name${NC}"
    
    # 오디오 파일 찾기
    audio_files=($(find "$dir" -maxdepth 1 \( -name "*.mp3" -o -name "*.wav" -o -name "*.m4a" -o -name "*.asf" \) -type f 2>/dev/null | sort))
    
    if [ ${#audio_files[@]} -eq 0 ]; then
        echo -e "${YELLOW}  → 오디오 파일 없음, 건너뜀${NC}"
        continue
    fi
    
    echo "  → ${#audio_files[@]}개 파일 발견"
    
    # 변환되지 않은 파일만 찾기
    unprocessed_files=()
    processed_count=0
    
    for audio_file in "${audio_files[@]}"; do
        # 파일명에서 확장자 제거
        base_name="${audio_file%.*}"
        time_file="${base_name}_time.md"
        full_file="${base_name}_full.md"
        
        # _time.md 또는 _full.md 파일이 있으면 이미 변환된 것으로 간주
        if [ -f "$time_file" ] || [ -f "$full_file" ]; then
            processed_count=$((processed_count + 1))
        else
            unprocessed_files+=("$audio_file")
        fi
    done
    
    if [ $processed_count -gt 0 ]; then
        echo -e "${YELLOW}  → 이미 변환된 파일: ${processed_count}개${NC}"
    fi
    
    if [ ${#unprocessed_files[@]} -eq 0 ]; then
        echo -e "${GREEN}  ✓ 모든 파일 변환 완료, 건너뜀${NC}"
        SKIPPED=$((SKIPPED + 1))
        echo ""
        continue
    fi
    
    echo -e "${BLUE}  → 변환 필요: ${#unprocessed_files[@]}개${NC}"
    
    # 디렉터리 단위로 변환 (--dir 옵션 사용)
    # 미변환 파일이 있는 디렉터리는 전체를 다시 처리 (이미 변환된 파일도 덮어쓰기)
    echo -e "    📂 디렉터리 전체 변환 시작 (기존 파일 포함)..."
    
    if python "$SRC_DIR/mp3_to_text.py" --dir "$dir" $OPTIONS; then
        echo -e "${GREEN}  ✓ 디렉터리 완료${NC}"
        SUCCESS=$((SUCCESS + 1))
    else
        echo -e "${RED}  ✗ 디렉터리 실패${NC}"
        FAILED=$((FAILED + 1))
    fi
    
    echo ""
done

# 종료 시간 및 소요 시간 계산
END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
HOURS=$((ELAPSED / 3600))
MINUTES=$(((ELAPSED % 3600) / 60))
SECONDS=$((ELAPSED % 60))

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}   변환 완료${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "결과:"
echo "  - 성공: $SUCCESS"
echo "  - 실패: $FAILED"
if [ $SKIPPED -gt 0 ]; then
    echo "  - 건너뜀: $SKIPPED (이미 변환 완료)"
fi
echo "  - 총 소요 시간: ${HOURS}시간 ${MINUTES}분 ${SECONDS}초"
echo ""
echo -e "${BLUE}결과 파일은 각 디렉터리에 저장되었습니다.${NC}"

# 로그 파일 정보 출력
if [ -n "$LOG_FILE" ]; then
    echo ""
    echo -e "${BLUE}로그 파일: $LOG_FILE${NC}"
fi
