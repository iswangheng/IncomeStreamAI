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
- **UI Design Style**: Apple级别设计系统。遵循Apple Human Interface Guidelines，采用系统级设计令牌体系。主色调为iOS蓝(#007AFF)配合中性灰色系，实现简洁、优雅、功能性和高可访问性的完美平衡。设计哲学注重内容优先、直观交互和视觉层次，为用户提供世界顶级的使用体验。

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templating with Flask for server-side rendering
- **UI Framework**: Bootstrap 5 with custom warm theme for responsive design
- **Design System**: 
  - Color Palette: iOS蓝 (#007AFF), 系统灰色级联, 语义化状态色彩
  - Layout: Apple风格卡片系统，毛玻璃导航栏，精确间距网格 (8pt系统)
  - Typography: Apple系统字体栈 (-apple-system, SF Pro Display风格)
  - Animations: Apple级别微交互，弹性过渡，视差滚动效果
- **JavaScript**: Vanilla JavaScript for dynamic form interactions (adding/removing person cards)
- **Styling**: Apple级别CSS设计系统，完整设计令牌库，响应式网格，无障碍优化，Bootstrap 5集成，Font Awesome 6图标
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

## Recent Changes (2025-08-12)
- ✅ **重大升级：世界级结果展示页面全面重设计** - 完全替换简陋的结果页面，实现Apple级别的优雅界面
  - 创建result_apple_redesigned.html，采用毛玻璃效果、渐变背景、精美卡片系统
  - 实现现代化视觉层次结构：英雄区域、概览卡片、路径方案展示
  - 添加精致交互动画：淡入动画、悬停效果、缩放过渡、响应式设计
  - 优化内容结构：清晰步骤展示、资源使用分析、风险管理、MVP验证区域
- ✅ **完整分享功能开发** - 实现专业级社交媒体分享系统
  - 创建Apple风格分享模态框，支持复制链接、社交媒体分享
  - 集成微信二维码生成、微博、QQ、QQ空间分享API
  - 实现链接复制成功反馈、社交按钮交互动画
  - 毛玻璃背景遮罩、平滑显示隐藏动画、响应式适配
- ✅ **专业PDF导出功能实现** - 基于jsPDF的客户端PDF生成系统
  - 集成jsPDF库，实现完整的结果页面PDF导出
  - 专业报告格式：标题、概览、路径方案、执行步骤、MVP验证
  - Apple设计系统色彩应用：iOS蓝标题、语义化颜色系统
  - 智能分页处理、页脚信息、自动文件命名（按日期）
  - 导出进度指示、错误处理、按钮状态管理
- ✅ **Apple风格导航栏添加** - 为结果页面添加固定顶部导航系统
  - 毛玻璃效果导航栏，固定定位不遮挡内容
  - 左侧返回按钮和品牌标识，右侧管理后台入口
  - 返回按钮悬停动画效果，向左滑动视觉反馈
  - 响应式设计适配，移动端优化布局调整
  - 移除页面底部重复的返回按钮，优化操作流程
- ✅ **AI思考过程可视化系统** - 解决长时间等待问题，提升用户体验
  - 创建独立思考过程页面，展示Angela AI分析步骤
  - 5个分析阶段：项目信息、人物资源、收入模式、执行方案、完整报告
  - 渐进式步骤激活、进度条显示、剩余时间预估
  - 浮动装饰动画、毛玻璃卡片设计、Apple风格视觉效果
  - 实时后台AI处理，完成后自动跳转结果页面
- ✅ **关键Bug修复：资源输入功能完全修复** - 解决第二个人物的手动资源输入被错误添加到第一个人物的问题
  - 修复JavaScript选择器逻辑，使用.resource-input[data-person-id]确保精确定位
  - 更正四个核心函数：addSelectedResource, removeSelectedResource, showResourceValidation, updateResourcesData
  - 资源输入现在完全按照人物卡片正确归属，支持回车添加、粘贴批量添加、退格删除
- ✅ **表单提交流程彻底重构** - 解决用户点击提交后卡在"AI正在智能分析"界面无法跳转的问题
  - 重写JavaScript数据收集逻辑，正确获取人物姓名、角色、资源、需求数据
  - 实现完整的AJAX提交流程，使用fetch API替代直接表单提交
  - 优化结果页面数据传递，支持直接使用AI返回结果避免重复请求
  - 添加完整错误处理和用户反馈机制
- ✅ **OpenAI模型升级** - 更新到最新稳定版本gpt-4o-2024-11-20，确保API调用兼容性
  - 验证新模型完全支持JSON结构化输出和复杂提示处理
  - 后端API测试通过，17秒内成功生成完整的收入路径方案
  - 知识库集成和多人物分析功能验证正常

## Previous Changes (2025-08-09)
- ✅ **重大升级：资源输入系统完全重构** - 基于世界一流UI设计准则的直观资源输入界面
  - 三个清晰分区：智能推荐区（蓝色）、手动输入区（绿色）、已选资源区（橙色）
  - 每个区域都有明确的视觉提示和操作说明，无需学习即可使用
  - 候选标签显示"点击添加"提示，输入框显示操作提示（回车、粘贴、退格）
  - 实时资源计数、空状态引导、操作按钮工具提示
- ✅ **修复JavaScript错误** - 解决变量重复声明、updateRoleSummary未定义等问题
- ✅ **智能推荐系统优化** - 9种身份角色对应的专属资源候选标签，多选时显示并集
- ✅ **用户体验大幅提升** - 每个交互元素都有明确的视觉反馈和操作指引
- ✅ **身份角色系统重构** - 实施MECE化角色分类，9个优化类别，支持多选功能
- ✅ **角色选择UI优化** - 改进工具提示位置，添加帮助图标，紧凑摘要显示
- ✅ **需求选项内容更新** - 按新结构重组"如何让此人开心"选项，规范化数据值
- ✅ **分类说明文字增强** - 为每个需求分类添加优雅的说明文字，提升用户理解
- ✅ **UI文案优化** - 更新页面副标题文案，突出关键人物分析功能
- ✅ **按钮可见性修复** - 创建专门的按钮修复样式，解决按钮显示问题
- ✅ **页面间距优化** - 调整提交按钮区域间距，提升界面紧凑性
- ✅ **移除鼠标特效** - 去除自定义鼠标跟随圆圈效果，保持标准交互体验

## Previous Changes (2025-08-07)
- ✅ **重大升级：Apple级别UI设计系统实施**
  - 创建世界一流的Apple风格设计系统 (apple-design-system.css)
  - 实施完整的设计令牌系统：颜色、字体、间距、阴影、动画
  - 重新设计首页界面 (index_apple.html) - 现代Apple风格表单设计
  - 重新设计结果页面 (result_apple.html) - 优雅的数据展示和交互
  - 重新设计管理后台 (dashboard_apple.html, base_apple.html) - 专业级管理界面
  - 采用Apple Human Interface Guidelines标准
  - 实现无障碍优化和响应式设计
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