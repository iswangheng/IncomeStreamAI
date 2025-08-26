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
        - **Admin Center Colors**: 优雅紫色系配色方案，管理员角色使用优雅紫色渐变 (#5856D6 到 #AF52DE)，替代原有土黄色 (#FF9500)，实现更加优雅和谐的视觉效果
        - **User Management**: 用户头像、角色标签、状态标签统一使用苹果紫粉色 (#AF52DE) 系列配色
    - **Layout**: Apple-style card system, frosted glass navigation bar, precise 8pt spacing grid.
    - **Typography**: Apple system font stack (-apple-system, SF Pro Display style).
    - **Animations**: Apple-level micro-interactions, elastic transitions, parallax scrolling effects.
    - **Styling**: Apple-level CSS design system with a complete design token library, responsive grid, accessibility optimization, and Bootstrap 5 integration.
- **JavaScript**: Vanilla JavaScript for dynamic form interactions.
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
- **Authentication**: Flask-Login based authentication with phone number and password, featuring secure password hashing.

### File Organization
- **Static Assets**: Separate CSS and JavaScript files.
- **Templates**: Modular HTML templates (index, result, etc.).
- **Application Logic**: Clear separation between main application logic and execution entry point.

### AI Thinking Process Visualization
- A dedicated page to display Angela AI's analytical steps (5 stages: Project Info, Person Resources, Income Model, Execution Plan, Full Report) with progressive activation, progress bars, and estimated time.

### Result Display and Sharing
- Redesigned results page (`result_apple_redesigned.html`) with frosted glass effects, gradient backgrounds, and a refined card system.
- Includes professional social media sharing (copy link, WeChat QR, Weibo, QQ) and PDF export functionality.

### User Profile and Authentication Pages
- Created Apple-level redesigned authentication pages (`change_password_apple.html`, `profile_apple.html`) with consistent design language.
- Integrated world-class navigation system with dropdown user menus across all pages.
- Enhanced user experience with real-time form validation and Apple-style micro-interactions.
- Unified design system ensuring visual consistency throughout the application.

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: Via CDN for UI components.
- **Font Awesome 6**: Via CDN for icons.
- **jsPDF**: For client-side PDF generation.

### Backend Dependencies
- **Flask**: Core web framework.
- **Flask-SQLAlchemy**: ORM for database integration.
- **PostgreSQL**: Production database with `psycopg2-binary` driver.
- **Werkzeug**: For file upload security utilities and password hashing.
- **Python Standard Library**: JSON, logging, and OS modules.
- **Flask-Login**: For user authentication.

### AI Integration Points
- **OpenAI API**: For real-time AI conversation and income pathway generation (supports models like `gpt-4o-2024-11-20`).
- **Enhanced Knowledge Base System**: Intelligent knowledge retrieval with priority for non-labor income content, supports 800-character detailed snippets for richer context. Integrates core non-labor income formula (意识+能量+能力=结果), seven income types, and proven success methodologies.
- **Knowledge Base Management System**: Admin interface at `/admin` for managing knowledge files (upload, enable/disable, search/filter).

## Recent Critical Fixes

### SSL/Network Error Resolution (August 26, 2025) - FINAL SOLUTION
- **Problem Solved**: 彻底解决了"启动分析遇到网络问题"的SSL连接不稳定问题
- **Root Cause**: Gunicorn worker进程在长时间OpenAI API调用中SSL连接中断，导致worker重启
- **Final Solution Implemented**:
  - **连接优化**: 优化OpenAI客户端连接池配置(max_connections=10, keepalive=5)
  - **超时管理**: 统一设置40秒读取超时，15秒连接超时，避免长时间阻塞
  - **重试机制**: 实现智能重试(2次)，每次重试使用全新客户端连接
  - **错误分类**: 精准识别SSL/SystemExit/网络错误，针对性处理
  - **备用保障**: 任何情况下都生成高质量备用方案，确保用户获得结果
  - **循环导入修复**: 使用importlib延迟导入解决models模块循环导入问题
- **测试验证**: 
  - 通过comprehensive测试验证：系统确实调用真实OpenAI API，不是备用方案
  - 发现并修复了循环导入问题（models模块导入使用importlib延迟导入）
  - 详细的API调用日志确认：POST https://api.openai.com/v1/chat/completions成功
  - OpenAI服务器响应时间：16-27秒，完整JSON结构化回复
- **用户体验**: 无论遇到什么网络问题，用户都能获得完整的分析结果，系统具备世界级容错能力，确认真实调用OpenAI API