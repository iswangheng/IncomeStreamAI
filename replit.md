# Angela - 非劳务收入路径设计师

## AI Agent协作规范

### 🚫 严格禁止的行为
- 不要修改任何未被用户明确要求的代码文件或逻辑
- 不要删除、重命名、重构已有函数、类、模块或接口
- 不要擅自引入、移除或更换依赖包（如 npm、pip 模块等）
- 不要改动数据库结构或运行迁移脚本，除非用户特别说明
- 不要优化、简化、重构任何未被请求的业务代码

### ✅ 明确允许的行为
- 只对用户明确要求的部分进行代码补全、修复或添加新功能
- 需要在生成代码中加入必要的注释、打印语句或 TODO 提示（需可被手动移除）
- 可提供逻辑建议，但不能自动修改未被授权的部分

### 💡 开发时需遵循的原则
- **先理解，再编写**：在用户需求不清时，先提问确认，不要擅自假设
- **执行修改前，请先提供 “高阶操作计划”**，涵盖将要改哪些文件、核心步骤、变更理由。获得确认后再变动。
- **按模块作业**：每次仅关注当前任务范围内的文件和函数
- **保持最小变动原则**：尽量减少代码变动范围，确保已有功能不被破坏
- **尊重已有风格**：遵循当前项目的命名、缩进、文件结构和框架习惯
- **生成代码需附说明**：每段代码都需要用中文简短注释说明作用，便于人工审查

### 🧪 Code Safety & Testing — 安全政策

- **编写逻辑前优先生成单元测试**：对每个新函数／临界流程，先写 “失败的测试”，让 Agent 验证 fail，再写实现。禁止 skip 测试。
- **每次新增外部依赖或非 Chef‑approved 库，需说明理由并进行兼容性测试。**
- 使用 `edit_file` 方式局部修补，不得使用 `write_file` 重写整个文件，除非有充分说明。

### 🧩 附加约束（可选）

- 遇到需要修改生产环境配置或 secrets，请先生成 sandbox 环境 demo 进行测试。
- 对于可能引入安全或脱库操作的代码，需要额外写入 “撤回计划”（rollback plan）。
- 如果 AI 预计成功概率不超过 80%，请标注为 `TODO: implement after manual review`；**不得**直接 commit。



## Overview

Angela is a Flask-based web application that serves as a non-labor income pathway designer. The application helps users input project information and receive AI-generated suggestions for creating alternative income streams. Users can describe their projects, add key personnel with their roles and resources, and get customized recommendations based on their specific situation.

## User Preferences

- **Communication Style**: 使用中文交流，简单易懂的日常用语
- **UI Design Style**: 暖色调、卡片式布局，视觉风格简洁清新，带有轻微渐变的背景。页面主色调为米黄色和橙色，搭配圆角白色卡片。表单设计整洁，每个输入框有圆角和浅灰色边框，主按钮为橙色，整体风格给人以温暖、友好、可信赖的感觉。

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with custom warm theme for responsive design
- **Design System**: 
  - Color Palette: 米黄色 (#FFF8E7), 暖橙色 (#FF8C42), 浅橙色 (#FFB380)
  - Layout: 卡片式布局，圆角设计，渐变背景
  - Typography: Segoe UI font family for clean readability
  - Animations: Smooth transitions, hover effects, fade-in animations
- **JavaScript**: Vanilla JavaScript for dynamic form interactions (adding/removing person cards)
- **Styling**: Custom CSS with warm color theme, Bootstrap integration, Font Awesome icons
- **Language**: Chinese (zh-CN) interface with warm, friendly tone

### Backend Architecture
- **Web Framework**: Flask with minimal configuration for rapid development
- **Database**: PostgreSQL with SQLAlchemy ORM for knowledge base management
- **Routing Structure**: Simple route-based architecture with form processing endpoints
- **Data Processing**: Form data collection and JSON structuring for AI processing
- **Session Management**: Flask sessions with configurable secret keys
- **Error Handling**: Flash messaging system for user feedback
- **File Management**: Knowledge base file upload with support for multiple formats

### Form Processing System
- **Dynamic Forms**: JavaScript-powered dynamic addition/removal of person cards
- **Data Validation**: Both client-side and server-side validation
- **Multi-step Data Collection**: Modular form sections for project info, key persons, and external resources
- **JSON Serialization**: Structured data preparation for downstream AI processing

### File Organization
- **Static Assets**: Separated CSS and JavaScript files for maintainability
- **Templates**: Modular HTML templates for different views (index, result)
- **Application Logic**: Clean separation between main application logic and execution entry point

## External Dependencies

### Frontend Libraries
- **Bootstrap 5**: UI component library via CDN
- **Font Awesome 6**: Icon library via CDN
- **Custom Bootstrap Theme**: Replit agent dark theme for consistent styling

### Backend Dependencies
- **Flask**: Core web framework
- **Flask-SQLAlchemy**: Database ORM integration
- **PostgreSQL**: Production database with psycopg2-binary driver
- **Werkzeug**: File upload security utilities
- **Python Standard Library**: JSON, logging, and OS modules for basic functionality

### Development Environment
- **Python Runtime**: Flask development server configuration
- **Environment Variables**: Session secret key management
- **Logging**: Built-in Python logging for debugging and monitoring

### Knowledge Base Management System
- **Admin Interface**: Simplified backend management at `/admin` endpoint
- **File Upload**: Support for txt, pdf, doc, docx, xlsx, csv, md, json formats (max 16MB)
- **Status Management**: Enable/disable knowledge files for AI processing
- **Search & Filter**: Quick file management with status filtering
- **Database Model**: KnowledgeItem with file metadata, status tracking, and usage statistics

### AI Integration Points
- **OpenAI API Integration**: 实时AI对话测试功能，支持GPT-4o等多种模型
- **Knowledge Base Context**: 自动注入知识库内容到AI系统提示
- **Form Data Structure**: Prepared JSON format for income pathway generation
- **Knowledge Base**: File-based knowledge management for AI context
- **Result Processing**: Template structure for AI-generated content display
- **Real-time Testing**: 对话测试模块验证知识库效果，支持开关知识库上下文

## Recent Changes (2025-08-03)
- ✅ 完成AI对话测试模块集成，支持OpenAI多模型选择
- ✅ 新增知识库上下文切换功能，可测试知识库效果
- ✅ 实现对话历史管理、清空对话、Enter键发送等功能
- ✅ 修复模型构造问题，确保KnowledgeItem正确继承SQLAlchemy Base类
- ✅ AI对话API成功连接OpenAI服务，支持实时知识库验证
- 简化后台管理界面，移除复杂统计页面，只保留核心的文件管理和上传功能
- 整合管理仪表板，直接显示文件列表而不是单独的统计页面
- 精简导航结构，只保留"知识库管理"和"上传文件"两个主要功能
- 在文件列表底部添加简洁的使用说明
- 优化界面布局，减少不必要的复杂性，提升用户体验