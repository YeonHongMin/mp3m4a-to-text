# Skills Configuration

This directory contains custom skills and agent configurations for this project.

## Available Skills

The following skills are configured for this project:

### 1. deep-research
- **Purpose**: Comprehensive research using 5 parallel search APIs
- **Trigger**: "리서치해줘", "조사해줘", "찾아봐", "검색해줘", "deep dive"
- **Use Case**: Research audio processing, speech-to-text technologies, optimization techniques

### 2. project-bootstrap
- **Purpose**: Auto-generate AI agent team structure (.claude/agents/)
- **Trigger**: "에이전트 팀 만들어줘", "에이전트 팀 구성", "에이전트 팀 생성"
- **Use Case**: Create specialized agents for audio processing, GUI development, testing

### 3. socrates
- **Purpose**: Socratic 1:1 planning consultation for vibe coders
- **Trigger**: "/socrates"
- **Use Case**: Plan new features, architecture improvements, technical decisions
- **Output**: 6 structured documents (PRD, TRD, User Flow, Database Design, Design System, TASKS)

### 4. tasks-generator
- **Purpose**: Generate TASKS.md with TDD workflow, Git Worktree, Phase numbering
- **Trigger**: "/tasks-generator" or auto-called after /socrates
- **Use Case**: Create detailed task breakdowns for implementation

## Project-Specific Skills

This project (MP3 to Text Converter) can benefit from:

1. **Deep Research**: For exploring audio processing optimization, speech recognition improvements
2. **Socrates**: For planning v1.1 features (GPU acceleration, speaker diarization)
3. **Tasks Generator**: For breaking down complex features into implementable tasks

## Custom Agent Team

The project includes specialized UI/UX agents located in `.claude/agents/`:

### 1. CSS Architecture Specialist ([css-architecture-specialist.md](agents/css-architecture-specialist.md))
- **Purpose**: Design scalable CSS architecture for Gradio GUI
- **Use Cases**: Refactor GUI styling, establish CSS standards, implement dark/light themes
- **Model**: Sonnet
- **Example**: "CSS Architecture Specialist 에이전트를 사용해서 Gradio GUI의 스타일링 시스템을 개선해줘."

### 2. Mobile-First Layout Expert ([mobile-first-layout-expert.md](agents/mobile-first-layout-expert.md))
- **Purpose**: Create responsive layouts optimized for mobile devices
- **Use Cases**: Mobile-friendly GUI, responsive design, touch interface optimization
- **Model**: Sonnet
- **Example**: "Mobile-First Layout Expert 에이전트가 모바일 반응형 인터페이스를 만들어줘."

### 3. Micro-Interactions Expert ([micro-interactions-expert.md](agents/micro-interactions-expert.md))
- **Purpose**: Design subtle animations and user feedback interactions
- **Use Cases**: Loading animations, hover effects, progress indicators, smooth transitions
- **Model**: Sonnet
- **Example**: "Micro-Interactions Expert 에이전트가 변환 진행률 애니메이션을 추가해줘."

### 4. ARIA Implementation Specialist ([aria-implementation-specialist.md](agents/aria-implementation-specialist.md))
- **Purpose**: Ensure WCAG compliance and accessibility for GUI components
- **Use Cases**: Screen reader support, keyboard navigation, ARIA attributes
- **Model**: Sonnet
- **Example**: "ARIA Implementation Specialist 에이전트가 GUI를 WCAG AA 준수로 만들어줘."

### Agent Team Workflow
For comprehensive GUI improvements, use agents in this order:
1. **CSS Architecture** → Establish styling system foundation
2. **Mobile-First Layout** → Responsive design implementation
3. **Micro-Interactions** → Add polish and feedback
4. **ARIA Implementation** → Ensure accessibility compliance

📖 **Full Guide**: See [UI-UX-AGENTS-GUIDE.md](UI-UX-AGENTS-GUIDE.md) for detailed usage instructions.

## Usage Examples

```bash
# Research optimization techniques
/deep-research faster-whisper GPU optimization CUDA

# Plan new speaker diarization feature
/socrates

# Generate tasks for next phase
/tasks-generator
```

## Custom Skills (Optional)

You can add project-specific skills by creating files in this directory following the Claude Skills specification.
