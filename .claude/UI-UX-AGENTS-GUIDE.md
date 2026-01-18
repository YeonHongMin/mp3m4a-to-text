# UI/UX 에이전트 가이드

MP3 to Text Converter 프로젝트를 위한 전문화된 UI/UX 에이전트 팀입니다.

---

## 📋 에이전트 목록

### 1. **CSS Architecture Specialist** ([css-architecture-specialist.md](agents/css-architecture-specialist.md))

**전문 분야:** 확장 가능한 CSS 아키텍처 설계

**사용 시기:**
- Gradio GUI의 CSS 구조 개선이 필요할 때
- 스타일링 시스템의 일관성을 확립할 때
- 유지보수 가능한 CSS 조직이 필요할 때
- 팀 협업을 위한 CSS 표준을 만들 때

**프로젝트 활용 예시:**
```
"src/app_gui.py의 Gradio CSS 커스텀 스타일을 위한
아키텍처를 설계해줘. 다크 모드, 반응형 레이아웃,
컴포넌트 기반 스타일링이 필요해."
```

---

### 2. **Mobile-First Layout Expert** ([mobile-first-layout-expert.md](agents/mobile-first-layout-expert.md))

**전문 분야:** 모바일 우선 반응형 레이아웃

**사용 시기:**
- 모바일 사용자를 위한 GUI 최적화가 필요할 때
- 반응형 디자인을 구현할 때
- 터치 인터페이스를 개선할 때
- 다양한 화면 크기 대응이 필요할 때

**프로젝트 활용 예시:**
```
"Gradio 웹 인터페이스를 모바일에서도
잘 작동하도록 반응형으로 만들어줘.
파일 업로드, 결과 표시, 설정 패널이
모바일에서도 사용하기 쉬워야 해."
```

---

### 3. **Micro-Interactions Expert** ([micro-interactions-expert.md](agents/micro-interactions-expert.md))

**전문 분야:** 미세 인터랙션 및 애니메이션

**사용 시기:**
- 로딩 상태 표시가 필요할 때
- 사용자 피드백 애니메이션을 추가할 때
- 버튼/카드 호버 효과를 만들 때
- 부드러운 상태 전환을 구현할 때

**프로젝트 활용 예시:**
```
"오디오 변환 진행률 표시, 변환 완료 애니메이션,
버튼 호버 효과 같은 마이크로 인터랙션을
추가해줘. 성능에 영향을 주지 않으면서
사용자 경험을 개선하고 싶어."
```

---

### 4. **ARIA Implementation Specialist** ([aria-implementation-specialist.md](agents/aria-implementation-specialist.md))

**전문 분야:** 웹 접근성 및 ARIA 구현

**사용 시기:**
- 스크린 리더 지원이 필요할 때
- 키보드 내비게이션을 개선할 때
- WCAG 준수가 필요할 때
- 접근 가능한 UI 컴포넌트를 만들 때

**프로젝트 활용 예시:**
```
"Gradio GUI를 WCAG 2.1 AA 수준으로
접근 가능하게 만들어줘. 파일 업로드,
설정 변경, 결과 다운로드 기능이
키보드와 스크린 리더로도
사용 가능해야 해."
```

---

## 🚀 빠른 시작

### 에이전트 호출 방법

```bash
# 방법 1: 직접 에이전트 파일 참조
.claude/agents/css-architecture-specialist.md 내용을 복사해서 사용

# 방법 2: Task 도구로 에이전트 실행
"CSS Architecture Specialist 에이전트를 사용해서
Gradio GUI의 스타일링을 개선해줘."

# 방법 3: 구체적인 요청과 함께 에이전트 지정
"Mobile-First Layout Expert 에이전트가
모바일 반응형 GUI를 만들어줘."
```

---

## 📊 프로젝트별 추천 작업

### GUI 개선 (v1.1)

**1단계: CSS 아키텍처**
```
CSS Architecture Specialist 에이전트에게 요청:
"Gradio 커스텀 CSS를 위한 아키텍처를 설계해줘.
다음을 지원해야 해:
- 다크/라이트 모드 테마
- 컴포넌트 기반 스타일링
- 다크 모드 전환 애니메이션
- 반응형 브레이크포인트"
```

**2단계: 모바일 최적화**
```
Mobile-First Layout Expert 에이전트에게 요청:
"Gradio 인터페이스를 모바일 최적화해줘.
핵심 기능: 파일 드래그 앤 드롭, 진행률 표시,
결과 다운로드가 모바일에서도 잘 작동해야 해."
```

**3단계: 인터랙션 추가**
```
Micro-Interactions Expert 에이전트에게 요청:
"변환 진행률 애니메이션, 완료 시 피드백,
파일 업로드 시 비주얼 피드백을 추가해줘."
```

**4단계: 접근성 확보**
```
ARIA Implementation Specialist 에이전트에게 요청:
"모든 GUI 컴포넌트를 WCAG AA 준수로
접근 가능하게 만들어줘."
```

---

## 🎯 현재 프로젝트 적용 가능성

### Gradio GUI 개선 기회

1. **반응형 레이아웃**
   - 현재: 데스크톱 중심
   - 개선: 모바일/태블릿 지원

2. **사용자 피드백**
   - 현재: 기본적인 진행률 표시
   - 개선: 애니메이션, 마이크로 인터랙션

3. **접근성**
   - 현재: Gradio 기본 접근성
   - 개선: 완전한 WCAG 준수, 키보드 내비게이션

4. **시스템 일관성**
   - 현재: 인라인 CSS
   - 개선: 구조화된 CSS 아키텍처

---

## 💡 팁

- **에이전트 순서:** CSS 아키텍처 → 모바일 레이아웃 → 인터랙션 → 접근성
- **반복 작업:** 각 에이전트가 작업한 결과를 다른 에이전트가 검토하도록 요청
- **문서화:** 각 에이전트의 결정을 [docs/5_Design_System.md](../docs/5_Design_System.md)에 기록

---

## 📚 관련 문서

- [PRD](../docs/1_PRD.md) - 제품 요구사항
- [TRD](../docs/2_TRD.md) - 기술 요구사항
- [Design System](../docs/5_Design_System.md) - 디자인 시스템
- [TASKS](../docs/6_TASKS.md) - 개발 태스크

---

*마지막 수정: 2026-01-14*
