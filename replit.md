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
- **UI Design Style**: 已完全重新设计为世界顶级现代化风格。采用深色主题配合霓虹色彩系统，玻璃态效果(Glassmorphism)和流体渐变设计。主色调为深蓝黑背景(#0a0a0f)搭配霓虹蓝(#00d4ff)、紫色(#8b5cf6)和粉色(#f472b6)渐变。卡片采用毛玻璃效果，圆角设计，微交互动画，整体风格现代、酷炫、科技感强。

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with custom warm theme for responsive design
- **Design System**: 
  - Color Palette: 深蓝黑背景 (#0a0a0f), 霓虹蓝 (#00d4ff), 紫色 (#8b5cf6), 粉色 (#f472b6)
  - Layout: 玻璃态卡片布局，流体渐变背景，现代圆角设计
  - Typography: Inter font family for modern readability
  - Animations: 微交互动画，悬停效果，流体过渡，打字动画
- **JavaScript**: Vanilla JavaScript for dynamic form interactions (adding/removing person cards)
- **Styling**: 现代化CSS样式系统，深色主题，霓虹色彩系统，Bootstrap集成，Font Awesome图标
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

## Recent Changes (2025-08-07)
- ✅ **重大UI重新设计：世界顶级现代化界面升级**
  - 全面采用深色主题配合霓虹色彩系统 (#0a0a0f + #00d4ff + #8b5cf6 + #f472b6)
  - 实现玻璃态效果(Glassmorphism)和流体渐变设计
  - 现代化卡片布局和微交互动画系统
  - 重新设计首页表单界面，采用顶级视觉风格
  - 重新设计管理后台，现代化仪表板界面
  - 重新设计结果页面，高端展示效果
  - 创建现代化CSS样式系统(modern-style.css, admin-modern.css)
- ✅ 完成AI对话测试模块集成，支持OpenAI多模型选择
- ✅ 新增知识库上下文切换功能，可测试知识库效果
- ✅ 实现对话历史管理、清空对话、Enter键发送等功能
- ✅ 修复模型构造问题，确保KnowledgeItem正确继承SQLAlchemy Base类
- ✅ AI对话API成功连接OpenAI服务，支持实时知识库验证
- ✅ **重大升级：实时Markdown流式渲染** - AI回答在流式输出过程中就能实时显示Markdown格式，包括标题、粗体、列表、代码块等，提供更好的用户体验
- ✅ 完善流式输出效果，添加打字指示器和动画效果
- ✅ 集成代码高亮功能，支持多种编程语言语法高亮
- ✅ 优化Markdown样式，确保在流式输出时保持良好的视觉效果
- 简化后台管理界面，移除复杂统计页面，只保留核心的文件管理和上传功能
- 整合管理仪表板，直接显示文件列表而不是单独的统计页面
- 精简导航结构，只保留"知识库管理"和"上传文件"两个主要功能
- 在文件列表底部添加简洁的使用说明
- 优化界面布局，减少不必要的复杂性，提升用户体验