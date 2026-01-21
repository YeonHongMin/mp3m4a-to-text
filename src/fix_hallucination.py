#!/usr/bin/env python3
"""
STT 결과에서 할루시네이션(반복 패턴) 자동 감지 및 제거 스크립트
"""

import re
from pathlib import Path
from collections import Counter
import argparse


def detect_repeated_content(lines, threshold=3):
    """
    반복되는 내용을 감지합니다.
    
    Args:
        lines: 분석할 라인 리스트
        threshold: 반복으로 간주할 최소 횟수
    
    Returns:
        반복 구간 리스트 [(start_idx, end_idx, repeated_text), ...]
    """
    repeated_sections = []
    i = 0
    
    while i < len(lines):
        # 현재 라인부터 연속된 동일/유사 내용 찾기
        current_content = lines[i].strip()
        if not current_content or len(current_content) < 5:
            i += 1
            continue
        
        # 같은 내용이 연속으로 나오는지 확인
        repeat_count = 1
        j = i + 1
        
        while j < len(lines):
            next_content = lines[j].strip()
            # 완전히 같거나 매우 유사한 경우 (80% 이상 일치)
            if next_content == current_content or similarity(current_content, next_content) > 0.8:
                repeat_count += 1
                j += 1
            else:
                break
        
        if repeat_count >= threshold:
            repeated_sections.append((i, j - 1, current_content))
            i = j
        else:
            i += 1
    
    return repeated_sections


def similarity(s1, s2):
    """두 문자열의 유사도를 계산 (0.0 ~ 1.0)"""
    if not s1 or not s2:
        return 0.0
    
    # 간단한 Jaccard 유사도
    set1 = set(s1)
    set2 = set(s2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    
    return intersection / union if union > 0 else 0.0


def detect_short_repeats(content, threshold=5):
    """
    짧은 구문이 반복되는 패턴 감지 (예: "오퍼를 좋아해?" 반복)
    
    Args:
        content: 전체 내용
        threshold: 반복으로 간주할 최소 횟수
    
    Returns:
        반복 패턴 리스트
    """
    # 짧은 구문 패턴 찾기 (2-15자 정도)
    patterns = re.findall(r'(.{2,15}?)\1{' + str(threshold-1) + r',}', content)
    return list(set(patterns))  # 중복 제거


def parse_time_md_file(file_path):
    """
    time.md 파일을 파싱합니다.
    
    Returns:
        (header_lines, entries): 헤더와 엔트리 리스트
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # 헤더 부분 찾기 (테이블 시작 전까지)
    table_start = -1
    for i, line in enumerate(lines):
        if line.strip().startswith('| 시간 | 내용 |') or \
           re.match(r'\|\s*\d{2}:\d{2}', line):
            # 테이블 헤더 다음에 구분선이 있는지 확인
            if i > 0 and '|---|---|' in lines[i-1]:
                table_start = i
                break
            elif i < len(lines) - 1 and '|---|---|' in lines[i+1]:
                table_start = i + 2
                break
    
    if table_start == -1:
        return lines, []
    
    header_lines = lines[:table_start]
    
    # 테이블 엔트리 파싱
    entries = []
    for line in lines[table_start:]:
        match = re.match(r'\|\s*(\d{2}:\d{2})\s*\|\s*(.+?)\s*\|', line)
        if match:
            time_str = match.group(1)
            content = match.group(2).strip()
            entries.append({
                'time': time_str,
                'content': content,
                'original_line': line
            })
    
    return header_lines, entries


def clean_repeated_words(text):
    """
    텍스트에서 연속으로 반복되는 단어나 구문을 제거합니다.
    예: "그녀는 그녀는 그녀는" -> "그녀는"
    """
    # 공백으로 구분된 단어 반복 제거
    words = text.split()
    cleaned_words = []
    i = 0
    
    while i < len(words):
        word = words[i]
        # 같은 단어가 연속으로 3번 이상 나오면 1번만 남김
        repeat_count = 1
        j = i + 1
        
        while j < len(words) and words[j] == word:
            repeat_count += 1
            j += 1
        
        if repeat_count >= 3:
            cleaned_words.append(word)
            i = j
        else:
            cleaned_words.append(word)
            i += 1
    
    result = ' '.join(cleaned_words)
    
    # 문자 단위 반복 패턴 제거 (예: "불에 불에 불을")
    # 2-10자 정도의 짧은 구문이 2번 이상 반복되는 경우
    result = re.sub(r'(.{2,10}?)\1{2,}', r'\1', result)
    
    return result.strip()


def is_likely_hallucination(content):
    """
    할루시네이션일 가능성이 높은 내용인지 판단합니다.
    """
    # 너무 짧거나 비정상적으로 긴 경우
    if len(content) < 2:
        return True
    
    # 같은 글자가 80% 이상인 경우
    if len(content) > 10:
        char_counts = Counter(content)
        most_common_char, count = char_counts.most_common(1)[0]
        if count / len(content) > 0.8:
            return True
    
    # 의미 없는 반복 패턴
    meaningless_patterns = [
        r'^(.{1,3})\1{5,}',  # 1-3글자가 5번 이상 반복
        r'^[ㄱ-ㅎㅏ-ㅣ]+$',  # 자음/모음만
        r'^([a-zA-Z])\1{10,}',  # 같은 알파벳 10번 이상
    ]
    
    for pattern in meaningless_patterns:
        if re.match(pattern, content):
            return True
    
    return False


def clean_entries(entries, verbose=False):
    """
    엔트리에서 반복 패턴을 제거합니다.
    """
    if not entries:
        return entries
    
    cleaned = []
    contents = [e['content'] for e in entries]
    
    # 1. 연속된 동일 내용 감지
    repeated_sections = detect_repeated_content(contents, threshold=3)
    
    if verbose and repeated_sections:
        print("\n🔍 감지된 반복 구간:")
        for start, end, text in repeated_sections:
            print(f"  - 라인 {start+1}~{end+1}: \"{text[:50]}...\" ({end-start+1}회 반복)")
    
    # 2. 짧은 구문 반복 패턴 감지
    full_content = ' '.join(contents)
    short_patterns = detect_short_repeats(full_content, threshold=5)
    
    if verbose and short_patterns:
        print("\n🔍 감지된 짧은 반복 패턴:")
        for pattern in short_patterns:
            print(f"  - \"{pattern}\"")
    
    # 3. 제거할 라인 인덱스 수집
    skip_indices = set()
    for start, end, _ in repeated_sections:
        # 첫 번째는 남기고 나머지는 제거
        for idx in range(start + 1, end + 1):
            skip_indices.add(idx)
    
    # 4. 클린한 엔트리 생성
    for i, entry in enumerate(entries):
        if i in skip_indices:
            continue
        
        content = entry['content']
        original_content = content
        
        # 할루시네이션 가능성 체크
        if is_likely_hallucination(content):
            if verbose:
                print(f"\n🗑️  라인 {i+1} 제거 (할루시네이션 의심):")
                print(f"   내용: {content[:80]}...")
            continue
        
        # 짧은 패턴 반복 제거
        for pattern in short_patterns:
            if pattern in content:
                parts = content.split(pattern)
                if len(parts) > 2:  # 2번 이상 반복
                    content = pattern + ''.join(parts[1:]).replace(pattern, '').strip()
        
        # 연속 반복 단어 정리
        content = clean_repeated_words(content)
        
        # 너무 짧아진 경우 제거
        if len(content.strip()) < 3:
            if verbose:
                print(f"\n🗑️  라인 {i+1} 제거 (내용이 너무 짧음):")
                print(f"   원본: {original_content[:80]}...")
            continue
        
        if content != original_content and verbose:
            print(f"\n✂️  라인 {i+1} 정리:")
            print(f"   이전: {original_content[:80]}...")
            print(f"   이후: {content[:80]}...")
        
        cleaned.append({
            'time': entry['time'],
            'content': content,
            'original_line': entry['original_line']
        })
    
    return cleaned


def write_cleaned_file(file_path, header_lines, cleaned_entries, backup=True):
    """
    정리된 내용을 파일로 저장합니다.
    """
    # 백업 생성
    if backup:
        backup_path = str(file_path).replace('.md', '.backup.md')
        with open(backup_path, 'w', encoding='utf-8') as f:
            with open(file_path, 'r', encoding='utf-8') as original:
                f.write(original.read())
        print(f"\n💾 백업 저장: {backup_path}")
    
    # 새 파일 작성
    with open(file_path, 'w', encoding='utf-8') as f:
        # 헤더 작성
        f.writelines(header_lines)
        
        # 엔트리 작성
        for entry in cleaned_entries:
            f.write(f"| {entry['time']} | {entry['content']} |\n")
    
    print(f"✅ 정리 완료: {file_path}")


def main():
    parser = argparse.ArgumentParser(
        description='STT 결과 파일에서 할루시네이션(반복 패턴) 제거'
    )
    parser.add_argument('file', type=str, help='처리할 *_time.md 파일 경로')
    parser.add_argument('--no-backup', action='store_true', help='백업 파일 생성 안 함')
    parser.add_argument('-v', '--verbose', action='store_true', help='상세 정보 출력')
    parser.add_argument('--threshold', type=int, default=3, 
                        help='반복으로 간주할 최소 횟수 (기본값: 3)')
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    
    if not file_path.exists():
        print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
        return 1
    
    print(f"📄 분석 중: {file_path.name}")
    
    # 파일 파싱
    header_lines, entries = parse_time_md_file(file_path)
    
    if not entries:
        print("❌ 테이블 엔트리를 찾을 수 없습니다.")
        return 1
    
    print(f"📊 총 {len(entries)}개 엔트리 발견")
    
    # 클리닝
    cleaned_entries = clean_entries(entries, verbose=args.verbose)
    
    removed_count = len(entries) - len(cleaned_entries)
    print(f"\n📈 통계:")
    print(f"   원본: {len(entries)}개 엔트리")
    print(f"   정리 후: {len(cleaned_entries)}개 엔트리")
    print(f"   제거됨: {removed_count}개 ({removed_count/len(entries)*100:.1f}%)")
    
    # 저장
    if removed_count > 0:
        write_cleaned_file(file_path, header_lines, cleaned_entries, backup=not args.no_backup)
    else:
        print("\n✨ 제거할 반복 패턴이 없습니다!")
    
    return 0


if __name__ == '__main__':
    exit(main())
