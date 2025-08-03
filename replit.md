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
- **按模块作业**：每次仅关注当前任务范围内的文件和函数
- **保持最小变动原则**：尽量减少代码变动范围，确保已有功能不被破坏
- **尊重已有风格**：遵循当前项目的命名、缩进、文件结构和框架习惯
- **生成代码需附说明**：每段代码都需要用中文简短注释说明作用，便于人工审查

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
- **Routing Structure**: Simple route-based architecture with form processing endpoints
- **Data Processing**: Form data collection and JSON structuring for AI processing
- **Session Management**: Flask sessions with configurable secret keys
- **Error Handling**: Flash messaging system for user feedback

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
- **Python Standard Library**: JSON, logging, and OS modules for basic functionality

### Development Environment
- **Python Runtime**: Flask development server configuration
- **Environment Variables**: Session secret key management
- **Logging**: Built-in Python logging for debugging and monitoring

### Potential AI Integration Points
- **Form Data Structure**: Prepared JSON format suggests integration with AI services for income pathway generation
- **Result Processing**: Template structure indicates AI-generated content display capabilities