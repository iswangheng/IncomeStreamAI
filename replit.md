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
- **TDD测试驱动开发模式（强制执行）**:
    - **所有测试文件必须放在 `tests/` 文件夹中**，严格禁止在根目录创建test_*.py文件
    - **统一端到端测试文件**：`tests/test_main_e2e.py` 
        - **唯一的全流程测试文件**，禁止创建新的端到端测试文件
        - **所有新功能测试**都在此文件中添加测试用例，保持复用
        - **测试流程**：登录→表单提交→AI分析→结果展示的完整用户流程
        - **Agent记忆约定**：每次都使用这个文件，不得重新创建类似文件
    - **新业务流程开发流程**：Red → Green → Refactor
        1. **Red阶段**：在`test_main_e2e.py`中添加测试用例（会失败）
        2. **Green阶段**：编写最少代码让测试通过
        3. **Refactor阶段**：重构代码提高质量，确保测试依然通过
    - **Agent必须自己测试**：实现新功能前，必须先在`test_main_e2e.py`中添加测试用例并验证功能正确性
    - **测试覆盖要求**：每个新的业务流程都必须在统一测试文件中有对应的测试方法
    - **测试命名规范**：`test_main_e2e.py`中的方法命名为`test_[功能名称]`

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
- **Database Management**: 多环境数据库架构，智能环境检测和数据库切换
  - **生产环境**: PostgreSQL (Neon) 数据库，适用于正式部署
  - **开发环境**: SQLite本地数据库，用于开发和测试
  - **环境检测**: 自动识别 FLASK_ENV、NODE_ENV、REPLIT_ENVIRONMENT 环境变量
  - **环境切换工具**: 提供 `environment_manager.py` 和 `switch_env.sh` 脚本
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
- **Testing**: All test files organized in `tests/` directory following TDD practices.

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

### Database Architecture & Form Processing Resolution (August 26, 2025) - COMPLETE RESOLUTION
- **Problem Solved**: 彻底解决了数据存储架构混乱和表单数据处理问题
- **Root Cause Analysis**: 
  - **架构错误**: 错误使用AnalysisResult表存储临时表单数据（pending类型），而专门的FormSubmission表完全未被使用
  - **数据职责混乱**: 单一表格承担多种职责，导致数据流混乱和查询逻辑复杂
  - **JSON解析缺失**: JSON格式的form_data无法被正确解析，导致"项目名称和背景描述不能为空"错误
- **Final Solution Implemented**:
  - **数据架构重构**: 正确使用FormSubmission表存储用户表单数据，AnalysisResult表专门存储AI分析结果
  - **JSON解析修复**: 在`/generate`路由中增加完整的form_data字段解析逻辑
  - **Session字段调整**: 从analysis_form_id改为form_submission_id，建立正确的数据关联
  - **查询逻辑重写**: get_form_data_from_db函数重构为从FormSubmission表查询数据
  - **职责分离**: FormSubmission表负责表单存储，AnalysisResult表负责结果存储，架构清晰
- **测试验证**: 
  - **架构验证**: FormSubmission表正常工作，存储完整的用户表单数据
  - **真实API调用**: OpenAI API成功调用，测试标识完整保留在分析结果中
  - **端到端流程**: 登录→表单提交→AI分析→结果展示，全链路验证成功
  - **数据完整性**: 表单数据和分析结果正确分离存储，数据流清晰可追踪
- **系统状态**: 
  - **数据架构**: ✅ FormSubmission和AnalysisResult表职责明确，架构合理
  - **表单处理**: ✅ JSON和传统表单格式均支持，解析逻辑完善
  - **数据存储**: ✅ PostgreSQL正常存储，表间关系清晰
  - **API集成**: ✅ OpenAI API稳定工作，生成高质量个性化分析结果
  - **用户体验**: ✅ 完整功能正常，从提交到结果的整个流程顺畅
  - **Prompt管理**: ✅ System prompt和Assistant prompt已提取到独立文件 (prompts/system_prompt.txt, prompts/assistant_prompt.txt)，便于修改和维护

### Database Environment Management (August 27, 2025) - 多环境数据库架构
- **功能目标**: 实现开发和生产环境的数据库完全分离，避免开发操作影响生产数据
- **解决方案**:
  - **环境自动检测**: 基于环境变量智能识别当前环境（development/production）
  - **数据库分离策略**:
    - 🚀 **生产环境**: PostgreSQL (Neon) - `DATABASE_URL` 环境变量
    - 🚧 **开发环境**: SQLite本地数据库 - `angela_dev.db` 文件
  - **环境管理工具**:
    - `environment_manager.py`: Python环境管理脚本，支持状态查看和环境切换
    - `switch_env.sh`: Bash快速切换脚本
- **环境检测逻辑**:
  - 检查 `FLASK_ENV=development` 或 `NODE_ENV=development` → 开发环境
  - 检查 `REPLIT_ENVIRONMENT=production` → 生产环境
  - 默认回退到开发环境，确保安全
- **使用方法**:
  ```bash
  # 查看当前环境状态
  python environment_manager.py status
  
  # 切换到开发环境
  python environment_manager.py dev
  
  # 切换到生产环境  
  python environment_manager.py prod
  ```
- **安全特性**:
  - 开发环境默认使用本地SQLite，完全隔离生产数据
  - 生产环境强制要求 DATABASE_URL 配置
  - 环境切换有明确的状态提示和确认
- **测试兼容**: 端到端测试支持多环境，测试数据与生产数据完全分离