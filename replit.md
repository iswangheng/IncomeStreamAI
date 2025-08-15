# Angela - 非劳务收入路径设计师

## Overview

Angela is a Flask-based web application designed to help users generate non-labor income pathways. It allows users to input project information, key personnel, and resources, then leverages AI to provide customized suggestions for alternative income streams. The project aims to offer a world-class user experience, focusing on intuitive interaction and visually appealing design, with a strong business vision to empower users in creating diverse income opportunities.

## User Preferences

- **Communication Style**: 使用中文交流，简单易懂的日常用语
- **UI Design Style**: Apple级别设计系统。遵循Apple Human Interface Guidelines，采用系统级设计令牌体系。主色调为iOS蓝(#007AFF)配合中性灰色系，实现简洁、优雅、功能性和高可访问性的完美平衡。设计哲学注重内容优先、直观交互和视觉层次，为用户提供世界顶级的使用体验。
- **Agent Workflow**:
    - 严格禁止修改未明确要求的代码，删除、重命名、重构现有功能，引入/移除/更换依赖包，或改动数据库结构。
    - 仅对用户明确要求的部分进行代码补全、修复或添加新功能。
    - 需在生成代码中加入必要的注释、打印语句或TODO提示。
    - 在用户需求不清时，先提问确认。
    - 执行修改前，需提供“高阶操作计划”并获得确认。
    - 每次仅关注当前任务范围内的文件和函数，保持最小变动原则。
    - 遵循现有项目的命名、缩进、文件结构和框架习惯。
    - 每段代码需附中文简短注释说明作用。
    - 编写逻辑前优先生成单元测试，且测试不可跳过。
    - 使用`edit_file`方式局部修补，不得使用`write_file`重写整个文件，除非有充分说明。

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 with Flask for server-side rendering.
- **UI Framework**: Bootstrap 5 with a custom warm theme for responsiveness.
- **Design System**: Apple-level design system adhering to Apple Human Interface Guidelines.
    - **Color Palette**: iOS Blue (#007AFF), system gray cascade, semantic state colors.
    - **Layout**: Apple-style card system, frosted glass navigation bar, precise 8pt spacing grid.
    - **Typography**: Apple system font stack (-apple-system, SF Pro Display style).
    - **Animations**: Apple-level micro-interactions, elastic transitions, parallax scrolling effects.
    - **Styling**: Apple-level CSS design system with a complete design token library, responsive grid, accessibility optimization, and Bootstrap 5 integration.
- **JavaScript**: Vanilla JavaScript for dynamic form interactions (e.g., adding/removing person cards).
- **Icons**: Font Awesome 6.
- **Language**: Chinese (zh-CN) interface with a warm, friendly tone.

### Backend Architecture
- **Web Framework**: Flask, configured for rapid development.
- **Database**: PostgreSQL with SQLAlchemy ORM for knowledge base management.
- **Routing**: Simple route-based architecture with endpoints for form processing.
- **Data Processing**: Collects form data and structures it into JSON for AI processing.
- **Session Management**: Flask sessions using configurable secret keys.
- **Error Handling**: Flash messaging system for user feedback.
- **File Management**: Supports knowledge base file uploads in various formats (txt, pdf, doc, docx, xlsx, csv, md, json).
- **Form Processing System**: JavaScript-powered dynamic forms with client-side and server-side validation, multi-step data collection, and JSON serialization.

### File Organization
- **Static Assets**: Separate CSS and JavaScript files.
- **Templates**: Modular HTML templates (index, result, etc.).
- **Application Logic**: Clear separation between main application logic and execution entry point.

### AI Thinking Process Visualization
- A dedicated page to display Angela AI's analytical steps (5 stages: Project Info, Person Resources, Income Model, Execution Plan, Full Report) with progressive activation, progress bars, and estimated time.

### Result Display and Sharing
- Redesigned results page (`result_apple_redesigned.html`) with frosted glass effects, gradient backgrounds, and a refined card system.
- Includes professional social media sharing (copy link, WeChat QR, Weibo, QQ) and PDF export functionality (using jsPDF).

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: Via CDN for UI components.
- **Font Awesome 6**: Via CDN for icons.
- **jsPDF**: For client-side PDF generation.

### Backend Dependencies
- **Flask**: Core web framework.
- **Flask-SQLAlchemy**: ORM for database integration.
- **PostgreSQL**: Production database with `psycopg2-binary` driver.
- **Werkzeug**: For file upload security utilities.
- **Python Standard Library**: JSON, logging, and OS modules.

### AI Integration Points
- **OpenAI API**: For real-time AI conversation and income pathway generation (supports models like `gpt-4o-2024-11-20`).
- **Enhanced Knowledge Base System**: Intelligent knowledge retrieval with priority for non-labor income content, supports 800-character detailed snippets for richer context.
- **Advanced Prompt Engineering**: Incorporates core non-labor income formula (意识+能量+能力=结果), seven income types, and proven success methodologies.
- **Knowledge Base Management System**: Admin interface at `/admin` for managing knowledge files (upload, enable/disable, search/filter).

## Recent Enhancements (2025-08-15)

### UI Simplification
- **External Resources Module Removal**: Completely removed the "外部资源与合作" module from the main form
  - Cleaned up HTML structure by removing the external resources card and all related input fields
  - Updated backend `/generate` route to remove external_resources processing logic
  - Removed JavaScript handling for external resource input toggles and validation
  - Updated demo case data to remove external resources references
  - **Impact**: Simplified user experience by focusing only on project info and key personnel
- **Key Personnel Options Reduction**: Removed two categories from "如何让此人高兴" section
  - Removed "想主导项目 / 有话语权" category (control_pace, choose_partners, decide_content, own_planning options)
  - Removed "在乎人脉 / 感受" category (expand_network, sense_of_participation, talk_value, feel_invited, learn_info options)
  - Updated demo case data to remove references to deleted options
  - **Impact**: Streamlined the person needs selection to focus on most essential categories

## Recent Enhancements (2025-08-14)

### Session Persistence Improvements
- **Fixed Critical Bug**: Session data not properly persisting, causing analysis_status to show as 'not_started' even after completion
- **Root Cause**: Missing `session.permanent = True` and `session.modified = True` flags in multiple critical locations
- **Solution Implemented**:
  - Added proper session persistence flags in all session modification points
  - Fixed `/generate` route: Added both permanent and modified flags after clearing old data
  - Fixed `_handle_analysis_execution`: Ensured session persistence when storing analysis results
  - Fixed data recovery logic: Added persistence flags when recovering from database
  - Fixed data validation: Added persistence when switching between analysis records
  - Removed duplicate code: Eliminated redundant `analysis_stage` setting
  - Improved exception handling: Replaced bare except with proper exception catching
- **Impact**: Session data now reliably persists across requests, preventing lost analysis results

### Session Management Fix
- **Fixed Critical Bug**: Result pages showing wrong project analysis due to stale session data
- **Root Cause**: `/generate` route wasn't clearing old `analysis_result_id` when processing new projects
- **Solution Implemented**:
  - Added complete session cleanup in `/generate` route, including `analysis_result_id` reset
  - Enhanced data consistency validation in `/results` route
  - Modified validation logic to preserve `analysis_status` instead of resetting it
- **Impact**: Each new project submission now gets fresh analysis without contamination from previous sessions

### AI Analysis Trigger Fix
- **Fixed Issue**: AI analysis not being triggered properly from thinking page
- **Root Cause**: Session state management and error handling issues
- **Solution Implemented**:
  - Fixed fallback function field names (projectName vs project_name)
  - Enhanced error logging in AI analysis pipeline
  - Added session.modified flags to ensure state persistence
  - Improved data consistency checks between form data and database
- **Impact**: AI analysis now properly triggers when thinking page loads, reducing emergency_fallback generation

## Recent Enhancements (2025-08-13)

### Non-Labor Income Pipeline Generation Improvements
- **Knowledge Base Integration**: Deep study and extraction of non-labor income core theories from knowledge base
- **Core Formula Implementation**: Integrated "意识+能量+能力（行动）=结果" formula into AI analysis logic
- **Seven Income Types Framework**: Added support for 租金、利息、股份/红利、版权、专利、企业连锁、团队收益
- **Three-Step Success Methodology**: Implemented "盘资源→搭管道→动真格" framework in prompt design
- **Enhanced Knowledge Retrieval**: 
  - Prioritizes non-labor income related content from knowledge base
  - Increased snippet length from 200 to 800 characters for richer context
  - Added intelligent fallback with core knowledge when database retrieval fails
- **Improved AI Prompts**:
  - System prompt now includes proven methodologies and success patterns
  - Assistant prompt requires three-party structure analysis for sustainable income streams
  - Added "make_who_happy" analysis framework for each action step
  - Enhanced MVP validation requirements (24-hour testable actions)
- **Professional Analysis Structure**: New output format includes income mechanisms, scaling potential, and bypass-prevention measures

### Performance & Reliability Fixes
- **Network Error Handling**: Enhanced network timeout detection including SSL connection errors
- **Immediate Fallback Generation**: When AI services fail due to network issues, system immediately generates backup solutions instead of getting stuck in loading state
- **Mobile Responsive Design**: Fixed button clustering issues on mobile devices with proper vertical stacking layout
- **Error Recovery System**: Complete fault tolerance with automatic database storage of fallback solutions
- **User Experience Optimization**: Eliminated loading state hang-ups and provided smooth fallback transitions

These enhancements make the non-labor income pathway generation significantly more professional and reliable, based on proven successful cases and methodologies, while ensuring consistent availability even during network instability.