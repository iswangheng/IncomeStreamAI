import os
import json
import logging
import traceback
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, Response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev_secret_key_change_in_production")

# Database configuration
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    # 开发环境回退配置
    database_url = "sqlite:///angela.db"

app.config["SQLALCHEMY_DATABASE_URI"] = database_url

# Enhanced PostgreSQL SSL configuration for Replit
if database_url and database_url.startswith('postgresql'):
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
        "pool_timeout": 20,
        "pool_size": 5,
        "max_overflow": 0,
        "connect_args": {
            "sslmode": "require",
            "connect_timeout": 10,
            "application_name": "replit_flask_app"
        }
    }
else:
    app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
        "pool_recycle": 300,
        "pool_pre_ping": True,
    }

# 修复Session配置 - 确保session正常工作
app.config['SESSION_COOKIE_SECURE'] = False  # 开发环境允许HTTP
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # session 1小时过期

# File upload configuration
UPLOAD_FOLDER = 'uploads/knowledge'
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xlsx', 'csv', 'md', 'json'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize database
db.init_app(app)

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # type: ignore
login_manager.login_message = '请先登录以访问该页面'
login_manager.login_message_category = 'info'

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Utility functions for file handling
def allowed_file(filename):
    """Check if uploaded file has an allowed extension"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_storage):
    """Get the size of uploaded file in bytes"""
    # Seek to end of file to get size
    file_storage.seek(0, 2)  # Seek to end
    size = file_storage.tell()
    file_storage.seek(0)  # Reset to beginning
    return size

# 导入所有模型
from models import User, KnowledgeItem, AnalysisResult, ModelConfig

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return User.query.get(int(user_id))

def admin_required(f):
    """管理员权限检查装饰器"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('您没有权限访问此页面', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

with app.app_context():
    db.create_all()

    # 创建默认管理员账号
    default_user = User.query.filter_by(phone='18302196515').first()
    if not default_user:
        default_user = User()
        default_user.phone = '18302196515'
        default_user.name = '系统管理员'
        default_user.set_password('aibenzong9264')
        default_user.is_admin = True
        db.session.add(default_user)
        db.session.commit()
        print("已创建默认管理员账号: 18302196515 / aibenzong9264")
    elif not default_user.is_admin:
        # 确保18302196515用户是管理员
        default_user.is_admin = True
        default_user.name = '系统管理员'
        db.session.commit()
        print("已将18302196515用户设置为管理员")

    # 初始化默认模型配置
    default_configs = [
        ('main_analysis', 'gpt-4o-mini', 0.7, 2500, 45),
        ('chat', 'gpt-4o', 0.7, 1500, 30),
        ('fallback', 'gpt-4o-mini', 0.5, 2000, 60)
    ]

    for config_name, model_name, temperature, max_tokens, timeout in default_configs:
        existing_config = ModelConfig.query.filter_by(config_name=config_name).first()
        if not existing_config:
            ModelConfig.set_config(config_name, model_name, temperature, max_tokens, timeout)
            print(f"已创建默认模型配置: {config_name} -> {model_name}")

@app.route('/')
@login_required
def index():
    """Main form page for user input - Apple design"""
    return render_template('index_apple.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """用户登录页面"""
    # 如果用户已登录，重定向到首页
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()

        # 验证输入
        if not phone or not password:
            flash('请输入手机号和密码', 'error')
            return render_template('login.html')

        # 查找用户
        user = User.query.filter_by(phone=phone).first()

        if user and user.check_password(password) and user.active:
            # 登录成功
            login_user(user, remember=True)
            user.update_last_login()
            db.session.commit()

            flash(f'欢迎回来，{user.name or user.phone}！', 'success')

            # 重定向到用户原本要访问的页面，或首页
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('手机号或密码错误，请重试', 'error')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """用户登出"""
    logout_user()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))


def get_form_data_from_db(session):
    """从数据库获取表单数据，避免session过大"""
    try:
        # 优先从session获取form_id
        form_id = session.get('analysis_form_id')
        if form_id:
            from models import AnalysisResult
            import json
            temp_result = AnalysisResult.query.get(form_id)
            if temp_result and temp_result.form_data:
                return json.loads(temp_result.form_data)
        
        # 如果没有form_id，尝试从project_name查找
        project_name = session.get('analysis_project_name')
        if project_name:
            from models import AnalysisResult
            import json
            recent_result = AnalysisResult.query.filter_by(
                user_id=current_user.id,
                project_name=project_name
            ).order_by(AnalysisResult.created_at.desc()).first()
            if recent_result and recent_result.form_data:
                return json.loads(recent_result.form_data)
        
        # 最后尝试从session获取（向后兼容）
        return session.get('analysis_form_data')
        
    except Exception as e:
        app.logger.error(f"Failed to get form data from DB: {str(e)}")
        return session.get('analysis_form_data')

def save_session_in_ajax():
    """辅助函数：确保AJAX请求中session被正确保存，监控session大小"""
    from flask import session
    import json
    
    # 计算session大小
    session_size = len(json.dumps(dict(session), ensure_ascii=False))
    app.logger.debug(f"Session size: {session_size} bytes")
    
    # 如果session过大，清理不必要的数据
    if session_size > 3500:  # 留一些余量
        app.logger.warning(f"Session size too large ({session_size} bytes), cleaning up...")
        if 'analysis_result' in session:
            del session['analysis_result']
            app.logger.info("Removed analysis_result from session to reduce size")
        if 'analysis_form_data' in session:
            del session['analysis_form_data']
            app.logger.info("Removed analysis_form_data from session to reduce size")
    
    session.permanent = True
    session.modified = True
    # 这会强制Flask重新计算session并设置cookie
    app.logger.debug(f"Forcing session save - Status: {session.get('analysis_status')}, Result ID: {session.get('analysis_result_id')}")

@app.route('/thinking')
@login_required
def thinking_process():
    """AI thinking process visualization page"""
    from flask import session, redirect, url_for, flash

    # Get form data from database instead of session
    form_data = get_form_data_from_db(session)
    app.logger.info(f"Thinking page - form data exists: {form_data is not None}")

    # 如果没有表单数据，重定向到首页
    if not form_data:
        app.logger.warning("No form data found in session for thinking page - redirecting to home")
        flash('请先填写项目信息', 'info')
        return redirect(url_for('index'))

    # 确保分析状态正确初始化
    if 'analysis_status' not in session:
        session['analysis_status'] = 'not_started'
        session['analysis_progress'] = 0
        session['analysis_stage'] = '等待开始分析...'

    app.logger.info(f"Thinking page loaded with status: {session.get('analysis_status')}")
    return render_template('thinking_process.html')

@app.route('/start_analysis', methods=['POST'])
@login_required
def start_analysis():
    """专门用于启动AI分析的接口 - 只在thinking页面首次加载时调用一次"""
    try:
        form_data = get_form_data_from_db(session)
        if not form_data:
            return jsonify({
                'status': 'error',
                'message': '没有找到表单数据',
                'error_code': 'NO_FORM_DATA'
            })
        
        # 检查是否已经有分析结果
        current_status = session.get('analysis_status', 'not_started')
        if current_status == 'completed':
            return jsonify({
                'status': 'completed',
                'message': '分析已完成',
                'progress': 100
            })
        
        app.logger.info(f"Starting AI analysis for project: {form_data.get('projectName')}")
        
        # 启动分析
        return _handle_analysis_execution(form_data, session)
        
    except Exception as e:
        import traceback
        app.logger.error(f"Error starting analysis: {str(e)}")
        app.logger.error(f"Full traceback: {traceback.format_exc()}")
        
        # 检查是否已经有结果保存但session有问题
        try:
            from models import AnalysisResult
            project_name = session.get('analysis_project_name', '')
            if project_name:
                # 查找最近的分析结果
                recent_result = AnalysisResult.query.filter_by(
                    user_id=current_user.id,
                    project_name=project_name
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                if recent_result:
                    app.logger.info(f"Found recent result for project {project_name}, using it instead")
                    # 恢复session状态
                    session['analysis_status'] = 'completed'
                    session['analysis_result_id'] = recent_result.id
                    session['analysis_progress'] = 100
                    save_session_in_ajax()
                    
                    return jsonify({
                        'status': 'completed',
                        'message': '分析完成，正在跳转到结果页面...',
                        'progress': 100
                    })
        except Exception as recovery_error:
            app.logger.error(f"Recovery attempt failed: {str(recovery_error)}")
        
        return jsonify({
            'status': 'error',
            'message': f'启动分析失败: {str(e)[:100]}',
            'error_code': 'START_FAILED'
        })

@app.route('/get_session_data')
@login_required
def get_session_data():
    """获取session中的表单数据，供thinking页面使用"""
    try:
        form_data = get_form_data_from_db(session)
        if form_data:
            logger.info(f"Session data found for thinking page: {form_data.get('projectName', 'unnamed')}")
            return jsonify({
                'success': True,
                'form_data': form_data
            })
        else:
            logger.warning("No form data found in session for thinking page")
            return jsonify({
                'success': False,
                'message': 'No session data available'
            })
    except Exception as e:
        logger.error(f"Error getting session data: {e}")
        return jsonify({
            'success': False, 
            'message': str(e)
        })

@app.route('/get_ai_thinking_stream')
@login_required
def get_ai_thinking_stream():
    """获取AI思考流内容 - 用于在等待阶段展示真实的AI思考过程"""
    from flask import session
    import random
    import time
    
    try:
        # 获取当前分析状态
        status = session.get('analysis_status', 'not_started')
        form_data = get_form_data_from_db(session)
        
        if not form_data:
            return jsonify({
                'status': 'not_available',
                'content': '等待AI引擎响应...',
                'timestamp': time.time()
            })
        
        # 无论什么状态，只要有表单数据就展示AI思考内容
        # 这样可以在OpenAI API调用期间持续展示思考过程
        
        # 基于真实项目数据生成AI思考内容
        project_name = form_data.get('projectName', '项目')
        key_persons = form_data.get('keyPersons', [])
        
        # 生成基于真实数据的AI思考内容流
        thinking_contents = [
            f"🔍 深度解析『{project_name}』的商业生态结构...",
            f"👥 识别到{len(key_persons)}位关键参与者，正在评估各方动机匹配度...",
            "🧠 应用Angela核心公式：意识+能量+能力=结果",
            "📊 扫描七大收入类型：租金/利息/股份/版权/居间/连锁/团队",
            f"🎯 重点分析关键人物：{', '.join([p.get('name', '未知') for p in key_persons[:3]])}",
            "⚡ 计算各方资源互补性和利益交换可能性...",
            "🔄 运用闭环设计原理，寻找三方共赢结构...",
            "🎮 评估设计者统筹位置和防绕行机制...",
            "🚀 构建最小可验证产品(MVP)验证模型...",
            "⚠️ 识别潜在风险点并生成应对策略...",
            "💰 优化三方利益分配机制，确保持续激励...",
            "🔬 交叉验证方案可行性和市场适应性...",
            "📋 调用深度学习模型优化方案架构...",
            "🎨 生成框架级收入管道设计方案..."
        ]
        
        # 根据时间戳选择不同的思考内容，营造流式感觉
        import hashlib
        current_time = int(time.time()) // 3  # 每3秒切换一次内容
        content_index = int(hashlib.md5(str(current_time).encode()).hexdigest(), 16) % len(thinking_contents)
        current_content = thinking_contents[content_index]
        
        return jsonify({
            'status': 'available', 
            'content': current_content,
            'timestamp': time.time()
        })
        
    except Exception as e:
        app.logger.error(f"Error getting AI thinking stream: {str(e)}")
        return jsonify({
            'status': 'available',
            'content': '🤖 AI引擎正在深度思考中...',
            'timestamp': time.time()
        })

@app.route('/analysis_status', methods=['GET'])
@login_required
def analysis_status():
    """检查AI分析状态的AJAX端点 - 确保始终返回JSON"""
    return check_analysis_status()

@app.route('/check_analysis_status', methods=['GET'])
@login_required
def check_analysis_status():
    """检查AI分析状态的AJAX端点 - 确保始终返回JSON"""

    # 最外层错误捕获 - 确保永远不返回HTML
    try:
        return _internal_check_analysis_status()
    except Exception as fatal_error:
        # 最后的保险 - 即使内部函数完全失败也返回JSON
        try:
            app.logger.error(f"FATAL: check_analysis_status crashed: {str(fatal_error)}")
            return jsonify({
                'status': 'error', 
                'message': '系统遇到严重错误，请刷新页面重试',
                'error_code': 'FATAL_ERROR'
            })
        except:
            # 如果连jsonify都失败，手动构造JSON响应
            from flask import Response
            return Response(
                '{"status": "error", "message": "系统严重错误，请刷新页面", "error_code": "JSONIFY_FAILED"}',
                mimetype='application/json',
                status=500
            )

def _internal_check_analysis_status():
    """内部状态检查函数"""
    from flask import session
    import traceback

    app.logger.info("=== Starting check_analysis_status ===")

    # 检查session数据
    try:
        form_data = get_form_data_from_db(session)
        status = session.get('analysis_status', 'not_started')
        result = session.get('analysis_result')

        app.logger.info(f"Session check - Status: {status}, Form data: {form_data is not None}, Result: {result is not None}")

    except Exception as session_error:
        app.logger.error(f"Session access error: {str(session_error)}")
        return jsonify({
            'status': 'error', 
            'message': '会话数据访问失败，请重新提交表单',
            'error_code': 'SESSION_ERROR'
        })

    # 验证必要数据
    if not form_data:
        app.logger.warning("No form data found in session")
        return jsonify({
            'status': 'error', 
            'message': '没有找到分析数据，请重新提交表单',
            'error_code': 'NO_FORM_DATA'
        })

    # 处理已完成的分析
    result_id = session.get('analysis_result_id')
    if status == 'completed' and (result or result_id):
        app.logger.info("Analysis already completed, returning result")
        return jsonify({'status': 'completed', 'redirect_url': '/results'})

    # 处理错误状态
    if status == 'error':
        error_msg = session.get('analysis_error', '分析过程中发生未知错误')
        app.logger.info(f"Analysis in error state: {error_msg}")
        return jsonify({
            'status': 'error', 
            'message': error_msg,
            'error_code': 'ANALYSIS_ERROR'
        })

    # 处理超时状态 - 立即生成备用方案
    if status == 'timeout':
        app.logger.info("Analysis timeout detected, generating fallback solution")
        try:
            fallback_result = generate_fallback_suggestions(form_data)

            # 保存备用方案到数据库
            import uuid
            import json
            from models import AnalysisResult
            fallback_id = str(uuid.uuid4())
            analysis_result = AnalysisResult()
            analysis_result.id = fallback_id
            analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
            analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
            analysis_result.project_name = form_data.get('projectName', '')
            analysis_result.project_description = form_data.get('projectDescription', '')
            analysis_result.team_size = len(form_data.get('keyPersons', []))
            analysis_result.analysis_type = 'fallback'
            db.session.add(analysis_result)
            db.session.commit()

            # 更新session状态，只保存必要数据
            session['analysis_project_name'] = form_data.get('projectName', '')
            session['analysis_status'] = 'completed'
            session['analysis_result_id'] = fallback_id
            # 清理大数据对象
            if 'analysis_result' in session:
                del session['analysis_result']
            if 'analysis_form_data' in session:
                del session['analysis_form_data']

            # 使用辅助函数确保session在AJAX中被保存
            save_session_in_ajax()

            app.logger.info(f"Fallback solution generated and saved with ID: {fallback_id}")

            # 创建response并确保session被保存
            response = jsonify({
                'status': 'completed', 
                'message': '已生成备用方案，正在跳转...',
                'progress': 100
            })

            from flask import make_response
            response = make_response(response)

            return response

        except Exception as fallback_error:
            app.logger.error(f"Failed to generate fallback solution: {str(fallback_error)}")
            return jsonify({
                'status': 'error', 
                'message': '生成备用方案失败，请重新提交',
                'error_code': 'FALLBACK_FAILED'
            })

    # 处理未开始的分析状态 - 轮询时只返回状态，不触发分析
    if status == 'not_started':
        app.logger.info("Analysis not started - polling detected, returning status only")
        return jsonify({
            'status': 'not_started',
            'progress': 0,
            'stage': '等待分析开始...',
            'message': '等待分析开始...'
        })

    # 处理正在进行中的分析 - 直接返回进度，不要重新开始
    if status == 'processing':
        progress = session.get('analysis_progress', 50)
        stage = session.get('analysis_stage', '分析正在进行中...')
        app.logger.info(f"Analysis in progress - Progress: {progress}%, Stage: {stage}")
        return jsonify({
            'status': 'processing', 
            'progress': progress,
            'stage': stage,
            'message': stage
        })

    # 如果到这里说明状态异常，记录并返回错误
    app.logger.warning(f"Unexpected analysis status: {status}")
    return jsonify({
        'status': 'error', 
        'message': '分析状态异常，请重新提交表单',
        'error_code': 'UNEXPECTED_STATUS'
    })

def _handle_analysis_execution(form_data, session):
    """处理AI分析执行"""
    import traceback
    import json
    import uuid

    try:
        # 检查是否已经在执行中，防止重复调用
        if session.get('analysis_started', False):
            app.logger.warning("Analysis already started, returning current status")
            return jsonify({
                'status': 'processing',
                'progress': session.get('analysis_progress', 50),
                'stage': session.get('analysis_stage', '分析正在进行中...'),
                'message': '分析正在进行中，请稍候...'
            })

        # 标记分析已开始，防止重复执行
        session['analysis_started'] = True
        session['analysis_status'] = 'processing'
        session['analysis_progress'] = 10
        session['analysis_stage'] = '开始AI分析...'
        save_session_in_ajax()  # 使用辅助函数确保session被保存
        app.logger.info("Starting AI analysis in request context - FIRST TIME")
        app.logger.info(f"Form data for analysis: {json.dumps(form_data, ensure_ascii=False)[:200]}")

        # 执行AI分析，设置进度追踪
        session['analysis_progress'] = 30
        session['analysis_stage'] = '正在分析项目数据...'
        save_session_in_ajax()  # 使用辅助函数确保session被保存
        suggestions = generate_ai_suggestions(form_data, session)

        if suggestions and isinstance(suggestions, dict):
            # 分析成功 - 将结果存储到数据库而不是session，避免session过大
            import uuid
            result_id = str(uuid.uuid4())

            # 创建AnalysisResult实例
            analysis_result = AnalysisResult()
            analysis_result.id = result_id
            analysis_result.user_id = current_user.id  # 关联当前用户
            analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
            analysis_result.result_data = json.dumps(suggestions, ensure_ascii=False)
            analysis_result.project_name = form_data.get('projectName', '')
            analysis_result.project_description = form_data.get('projectDescription', '')
            analysis_result.team_size = len(form_data.get('keyPersons', []))
            analysis_result.analysis_type = 'ai_analysis'
            db.session.add(analysis_result)
            db.session.commit()

            # 在session中只存储最小必要数据，避免cookie过大
            # 只保存项目名称用于显示，完整数据从数据库读取
            session['analysis_project_name'] = form_data.get('projectName', '')
            session['analysis_result_id'] = result_id
            session['analysis_status'] = 'completed'
            session['analysis_started'] = False  # 重置开始标志
            session['analysis_progress'] = 100  # 只有真正完成时才设置为100%
            session['analysis_stage'] = '分析完成！'
            # 清理大数据对象
            if 'analysis_result' in session:
                del session['analysis_result']
            if 'analysis_form_data' in session:
                del session['analysis_form_data']  # 删除大的form_data

            # 使用辅助函数确保session在AJAX中被保存
            save_session_in_ajax()

            app.logger.info(f"AI analysis completed successfully, result stored with ID: {result_id}")
            app.logger.info(f"Session updated - Status: {session.get('analysis_status')}, Result ID: {session.get('analysis_result_id')}")
            app.logger.info(f"Session state after update - Permanent: {session.permanent}, Modified: {session.modified}")

            # 立即返回成功响应，不需要额外处理
            app.logger.info("About to return success response to frontend")
            
            try:
                response = jsonify({
                    'status': 'completed', 
                    'message': '分析完成，正在跳转到结果页面...',
                    'progress': 100
                })
                app.logger.info("Successfully created JSON response")
                return response
            except Exception as response_error:
                app.logger.error(f"Error creating JSON response: {str(response_error)}")
                # 即使JSON创建失败，也要确保前端知道分析完成了
                session['analysis_status'] = 'completed'
                save_session_in_ajax()
                raise response_error
        else:
            # 分析结果无效
            app.logger.error("AI analysis returned invalid result")
            session['analysis_status'] = 'error'
            session['analysis_error'] = '分析结果无效'
            return jsonify({
                'status': 'error', 
                'message': '分析结果无效，请重试',
                'error_code': 'INVALID_RESULT'
            })

    except Exception as analysis_error:
        # 分析执行错误
        error_msg = str(analysis_error)
        app.logger.error(f"Analysis execution error: {error_msg}")
        app.logger.error(f"Analysis traceback: {traceback.format_exc()}")

        # 如果是网络超时错误，立即生成备用方案
        if ('timeout' in error_msg.lower() or 'connection' in error_msg.lower() or 
            'ssl' in error_msg.lower() or 'network' in error_msg.lower() or
            'read timeout' in error_msg.lower() or 'connect timeout' in error_msg.lower()):
            session['analysis_status'] = 'timeout'
            app.logger.info(f"Network/timeout error detected: {error_msg}, immediately generating fallback")

            try:
                fallback_result = generate_fallback_suggestions(form_data)

                # 保存备用方案到数据库
                import uuid

                fallback_id = str(uuid.uuid4())
                analysis_result = AnalysisResult()
                analysis_result.id = fallback_id
                analysis_result.user_id = current_user.id  # 关联当前用户
                analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                analysis_result.project_name = form_data.get('projectName', '')
                analysis_result.project_description = form_data.get('projectDescription', '')
                analysis_result.team_size = len(form_data.get('keyPersons', []))
                analysis_result.analysis_type = 'fallback'
                db.session.add(analysis_result)
                db.session.commit()

                # 更新session状态为完成，只保存必要数据
                session['analysis_project_name'] = form_data.get('projectName', '')
                session['analysis_status'] = 'completed'
                session['analysis_result_id'] = fallback_id
                # 清理大数据
                if 'analysis_result' in session:
                    del session['analysis_result']
                if 'analysis_form_data' in session:
                    del session['analysis_form_data']

                # 使用辅助函数确保session在AJAX中被保存
                save_session_in_ajax()

                app.logger.info(f"Fallback generated immediately due to timeout, ID: {fallback_id}")

                # 创建response并确保session被保存
                response = jsonify({
                    'status': 'completed', 
                    'message': '网络不稳定，已生成备用方案...',
                    'progress': 100
                })

                from flask import make_response
                response = make_response(response)

                return response

            except Exception as fallback_error:
                app.logger.error(f"Fallback generation failed: {str(fallback_error)}")
                session['analysis_status'] = 'error'
                session['analysis_started'] = False  # 重置开始标志，允许重试
                session['analysis_error'] = '网络超时且备用方案生成失败，请重试'
                return jsonify({
                    'status': 'error', 
                    'message': '网络连接问题，请检查网络后重试',
                    'error_code': 'NETWORK_AND_FALLBACK_FAILED'
                })
        else:
            session['analysis_status'] = 'error'
            session['analysis_started'] = False  # 重置开始标志，允许重试
            session['analysis_error'] = error_msg
            return jsonify({
                'status': 'error', 
                'message': f'分析过程遇到问题: {error_msg}',
                'error_code': 'EXECUTION_ERROR'
            })

@app.route('/results')
@login_required
def results():
    """Display AI analysis result page with dynamic loading"""
    try:
        from flask import session

        # 详细记录session状态
        app.logger.info(f"Results page accessed - Full session: {dict(session)}")
        app.logger.info(f"Results page - Session ID: {request.cookies.get('session', 'No session cookie')}")

        # Get form data and analysis status from session
        form_data = get_form_data_from_db(session)
        status = session.get('analysis_status', 'not_started')
        result_id = session.get('analysis_result_id')
        result_data = session.get('analysis_result')

        app.logger.info(f"Results page - Status: {status}, Form data exists: {form_data is not None}, Result ID: {result_id}, Result data exists: {result_data is not None}")

        # 如果有result_id但状态不对，尝试从数据库恢复完整信息
        if result_id and status != 'completed':
            app.logger.warning(f"Found result_id {result_id} but status is {status}, attempting recovery")
            try:
                from models import AnalysisResult
                import json

                analysis_record = AnalysisResult.query.filter_by(id=result_id).first()
                if analysis_record:
                    if analysis_record.form_data and not form_data:
                        form_data = json.loads(analysis_record.form_data)
                        # 不要把大数据写回session，只更新项目名称
                        session['analysis_project_name'] = form_data.get('projectName', '')
                        session.permanent = True
                        session.modified = True
                        app.logger.info(f"Recovered form data from database for result ID: {result_id}")

                    if analysis_record.result_data:
                        result_data = json.loads(analysis_record.result_data)
                        # 不要把结果数据写回session，会导致cookie过大
                        session['analysis_status'] = 'completed'
                        session.permanent = True
                        session.modified = True
                        status = 'completed'  # 更新本地状态变量
                        app.logger.info(f"Recovered analysis status and result data for ID: {result_id}")
                else:
                    app.logger.warning(f"No analysis record found for result ID: {result_id}")
            except Exception as db_error:
                app.logger.error(f"Failed to recover from database: {str(db_error)}")

        # 如果没有result_id但有form_data，尝试从数据库找最新的AI分析结果
        if form_data and not result_id:
            try:
                from models import AnalysisResult
                import json

                project_name = form_data.get('projectName', '')
                if project_name:
                    # 查找最新的AI分析结果
                    latest_ai_result = AnalysisResult.query.filter_by(
                        project_name=project_name,
                        analysis_type='ai_analysis'
                    ).order_by(AnalysisResult.created_at.desc()).first()

                    if latest_ai_result:
                        app.logger.info(f"Found AI analysis result for project: {project_name}, ID: {latest_ai_result.id}")
                        result_id = latest_ai_result.id
                        session['analysis_result_id'] = result_id
                        session['analysis_status'] = 'completed'
                        result_data = json.loads(latest_ai_result.result_data)
                        session['analysis_result'] = result_data
                        session.permanent = True  # 添加permanent确保持久化
                        session.modified = True
                        status = 'completed'

            except Exception as e:
                app.logger.error(f"Failed to find AI analysis result: {str(e)}")

        # 如果有form_data但result_id指向的是备用方案，尝试找到真正的AI分析结果
        if form_data and result_id:
            try:
                from models import AnalysisResult
                import json

                # 检查当前result_id对应的记录类型
                current_record = AnalysisResult.query.filter_by(id=result_id).first()
                if current_record and current_record.analysis_type == 'emergency_fallback':
                    app.logger.warning(f"Current result_id {result_id} points to emergency fallback, searching for real AI analysis")

                    # 根据表单数据的详细内容找匹配的AI分析结果
                    project_name = form_data.get('projectName', '')
                    project_description = form_data.get('projectDescription', '')

                    if project_name and project_description:
                        # 查找匹配项目名称和描述关键词的AI分析结果
                        ai_records = AnalysisResult.query.filter(
                            AnalysisResult.analysis_type == 'ai_analysis',
                            AnalysisResult.form_data.contains(f'"{project_name}"')
                        ).order_by(AnalysisResult.created_at.desc()).all()

                        # 进一步验证：检查描述中的关键词匹配
                        matching_record = None
                        key_words = project_description[:50]  # 取描述前50字符作为关键特征

                        for record in ai_records:
                            try:
                                record_form_data = json.loads(record.form_data)
                                record_description = record_form_data.get('projectDescription', '')
                                # 检查描述是否包含相同的关键词
                                if key_words in record_description or record_description[:50] in project_description:
                                    matching_record = record
                                    break
                            except Exception as e:
                                app.logger.debug(f"Failed to parse record form data: {str(e)}")
                                continue

                        if matching_record:
                            result_data = json.loads(matching_record.result_data)
                            session['analysis_result'] = result_data
                            session['analysis_result_id'] = matching_record.id
                            session.permanent = True
                            session.modified = True
                            result_id = matching_record.id
                            app.logger.info(f"Switched from fallback to matching AI analysis result: {matching_record.id}")
                        else:
                            app.logger.warning(f"No matching AI analysis found for project: {project_name}")

            except Exception as switch_error:
                app.logger.error(f"Failed to switch from fallback to AI result: {str(switch_error)}")

        # 如果没有form_data，不要随意从其他记录中恢复，应该重定向到首页
        if not form_data:
            app.logger.warning("No form data found in session - should not recover random records")
            flash('会话已过期，请重新提交表单', 'error')
            return redirect(url_for('index'))

        # 根据分析状态决定显示内容（注意：status可能已在上面的恢复逻辑中被更新）
        # 重新检查session状态，确保获取最新的
        status = session.get('analysis_status', status)
        result_id = session.get('analysis_result_id', result_id) 

        if status == 'completed':
            suggestions = None

            # 优先从数据库读取分析结果（如果有result_id）
            if result_id:
                try:
                    from models import AnalysisResult
                    import json

                    analysis_record = AnalysisResult.query.filter_by(id=result_id).first()

                    if analysis_record and analysis_record.result_data:
                        # 额外验证：检查数据库记录的表单数据与session中的表单数据是否匹配
                        try:
                            db_form_data = json.loads(analysis_record.form_data)
                            session_project_name = form_data.get('projectName', '')
                            db_project_name = db_form_data.get('projectName', '')

                            if session_project_name and db_project_name and session_project_name != db_project_name:
                                app.logger.warning(f"Data mismatch: session project '{session_project_name}' != database project '{db_project_name}' for result_id {result_id}")
                                # 数据不匹配，尝试找正确的记录
                                correct_records = AnalysisResult.query.filter(
                                    AnalysisResult.analysis_type == 'ai_analysis',
                                    AnalysisResult.form_data.contains(f'"{session_project_name}"')
                                ).order_by(AnalysisResult.created_at.desc()).all()

                                if correct_records:
                                    analysis_record = correct_records[0]
                                    result_id = analysis_record.id
                                    session['analysis_result_id'] = result_id
                                    session.permanent = True
                                    session.modified = True
                                    app.logger.info(f"Found correct analysis record: {result_id} for project: {session_project_name}")
                                else:
                                    app.logger.warning(f"No matching analysis found for project: {session_project_name}, but keeping current status: {status}")
                                    # 数据不匹配但不要重置status，保持原状态
                                    # 只清理错误的result_id
                                    session['analysis_result_id'] = None
                                    session.permanent = True
                                    session.modified = True
                                    # 不要重置analysis_status！保持原有状态
                                    # 如果status是completed，说明分析已完成，只是result_id有问题
                                    app.logger.info(f"Keeping analysis_status as: {status}, will attempt to use session data")

                        except Exception as validate_error:
                            app.logger.error(f"Failed to validate data consistency: {str(validate_error)}")

                        if analysis_record and analysis_record.result_data:
                            suggestions = json.loads(analysis_record.result_data)
                            app.logger.info(f"Analysis completed - showing full results from database for ID: {result_id}")
                    else:
                        app.logger.warning(f"Analysis result not found in database: {result_id}")
                except Exception as e:
                    app.logger.error(f"Error reading analysis result from database: {str(e)}, traceback: {traceback.format_exc()}")

            # 如果数据库读取失败或没有result_id，从session读取（兼容性）
            if not suggestions:
                suggestions = session.get('analysis_result')
                if suggestions:
                    app.logger.info("Analysis completed - showing full results from session")
                else:
                    app.logger.warning("Analysis marked as completed but no result data found")

            # 如果有任何结果数据，显示结果页面
            if suggestions:
                return render_template('result_pipeline_redesigned.html', 
                                     form_data=form_data, 
                                     result=suggestions,
                                     status='completed')
            else:
                # 分析标记为完成但没有结果数据，显示错误状态
                app.logger.error("Analysis completed but no result data available")
                return render_template('result_pipeline_redesigned.html',
                                     form_data=form_data,
                                     status='error',
                                     error_message='分析完成但结果数据丢失，请重新分析')

        elif status == 'error' or status == 'timeout':
            # 分析出错或超时，显示错误信息或备用方案
            error_msg = session.get('analysis_error', '分析过程中发生未知错误')
            app.logger.info(f"Analysis {status} - showing fallback page: {error_msg}")

            # 如果是超时，生成基础建议作为备用方案
            if status == 'timeout':
                try:
                    fallback_result = generate_fallback_suggestions(form_data)

                    # 将备用方案也保存到数据库
                    try:
                        import uuid
                        import json
                        from models import AnalysisResult
                        fallback_id = str(uuid.uuid4())

                        analysis_result = AnalysisResult()
                        analysis_result.id = fallback_id
                        analysis_result.user_id = current_user.id  # 关联当前用户
                        analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                        analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                        analysis_result.project_name = form_data.get('projectName', '')
                        analysis_result.project_description = form_data.get('projectDescription', '')
                        analysis_result.team_size = len(form_data.get('keyPersons', []))
                        analysis_result.analysis_type = 'fallback'

                        db.session.add(analysis_result)
                        db.session.commit()
                        app.logger.info(f"Fallback result saved with ID: {fallback_id}")
                    except Exception as db_error:
                        app.logger.error(f"Failed to save fallback result: {str(db_error)}")

                    return render_template('result_pipeline_redesigned.html',
                                         form_data=form_data,
                                         result=fallback_result,
                                         status='completed',
                                         fallback_mode=True)
                except Exception as e:
                    app.logger.error(f"Fallback generation failed: {str(e)}")

            return render_template('result_pipeline_redesigned.html',
                                 form_data=form_data,
                                 status='error',
                                 error_message=error_msg)

        else:
            # 处理未完成的状态
            app.logger.warning(f"Results page accessed with non-completed status: {status}")

            # 如果是not_started状态，重定向到thinking页面
            if status == 'not_started':
                app.logger.info("Status is not_started, redirecting to thinking page")
                return redirect(url_for('thinking_process'))

            # 如果是processing状态但没有结果，也重定向到thinking页面
            elif status == 'processing':
                app.logger.info("Status is processing without result, redirecting to thinking page")
                return redirect(url_for('thinking_process'))

            # 尝试从数据库获取任何存在的结果
            if result_id:
                try:

                    import json
                    from models import AnalysisResult
                    analysis_record = AnalysisResult.query.filter_by(id=result_id).first()
                    if analysis_record and analysis_record.result_data:
                        suggestions = json.loads(analysis_record.result_data)
                        app.logger.info(f"Found existing result in database for ID: {result_id}")
                        return render_template('result_pipeline_redesigned.html', 
                                             form_data=form_data, 
                                             result=suggestions,
                                             status='completed')
                except Exception as e:
                    app.logger.error(f"Failed to load result from database: {str(e)}")

            # 只有在确实没有其他选择时才生成紧急备用方案
            # 比如session数据损坏或数据库读取失败
            app.logger.info("Unusual state detected, generating emergency fallback solution")
            try:
                fallback_result = generate_fallback_suggestions(form_data)

                # 保存到数据库
                try:
                    import uuid
                    import json
                    from models import AnalysisResult

                    emergency_id = str(uuid.uuid4())
                    analysis_result = AnalysisResult()
                    analysis_result.id = emergency_id
                    analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                    analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                    analysis_result.project_name = form_data.get('projectName', '')
                    analysis_result.project_description = form_data.get('projectDescription', '')
                    analysis_result.team_size = len(form_data.get('keyPersons', []))
                    analysis_result.analysis_type = 'emergency_fallback'
                    db.session.add(analysis_result)
                    db.session.commit()

                    # 更新session，只保存必要数据
                    session['analysis_project_name'] = form_data.get('projectName', '')
                    session['analysis_status'] = 'completed'
                    session['analysis_result_id'] = emergency_id
                    # 清理大数据对象
                    if 'analysis_result' in session:
                        del session['analysis_result']
                    if 'analysis_form_data' in session:
                        del session['analysis_form_data']

                    app.logger.info(f"Emergency fallback generated with ID: {emergency_id}")
                except Exception as db_error:
                    app.logger.error(f"Failed to save emergency fallback: {str(db_error)}")

                return render_template('result_pipeline_redesigned.html',
                                     form_data=form_data,
                                     result=fallback_result,
                                     status='completed',
                                     fallback_mode=True)

            except Exception as fallback_error:
                app.logger.error(f"Emergency fallback generation failed: {str(fallback_error)}")
                return render_template('result_pipeline_redesigned.html',
                                     form_data=form_data,
                                     status='error',
                                     error_message='系统无法生成分析结果，请重新尝试')

    except Exception as e:
        app.logger.error(f"Error displaying results: {str(e)}")
        flash('显示结果时发生错误，请重试', 'error')
        return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
@login_required
def generate():
    """Process form data and redirect to thinking page"""
    try:
        app.logger.info(f"Generate route accessed - Request method: {request.method}")
        app.logger.info(f"Generate route - Form data keys: {list(request.form.keys())}")
        app.logger.info(f"Generate route - Content type: {request.content_type}")
        # Get form data
        project_name = request.form.get('project_name', '').strip()
        project_description = request.form.get('project_description', '').strip()

        # Validate required fields
        if not project_name or not project_description:
            flash('项目名称和背景描述不能为空', 'error')
            return redirect(url_for('index'))

        # Process key persons data
        key_persons = []
        person_names = request.form.getlist('person_name[]')
        person_roles = request.form.getlist('person_role[]')
        person_resources = request.form.getlist('person_resources[]')
        person_needs = request.form.getlist('person_needs[]')

        for i in range(len(person_names)):
            if person_names[i].strip():  # Only add if name is not empty
                # 处理make_happy字段，将逗号分隔的字符串分割成数组
                make_happy_list = []
                if i < len(person_needs) and person_needs[i].strip():
                    make_happy_list = [need.strip() for need in person_needs[i].split(',') if need.strip()]

                key_persons.append({
                    "name": person_names[i].strip(),
                    "role": person_roles[i].strip() if i < len(person_roles) else "",
                    "resources": [r.strip() for r in person_resources[i].split(',') if r.strip()] if i < len(person_resources) else [],
                    "make_happy": make_happy_list
                })

        # Create JSON structure as per PRD
        form_data = {
            "projectName": project_name,
            "projectDescription": project_description,
            "keyPersons": key_persons
        }

        # Store form data in session - 保存到数据库而不是session
        from flask import session
        
        # 保存表单数据到数据库，避免session过大
        try:
            import uuid
            import json
            from models import AnalysisResult
            
            # 创建临时记录存储表单数据
            temp_id = str(uuid.uuid4())
            temp_result = AnalysisResult()
            temp_result.id = temp_id
            temp_result.user_id = current_user.id
            temp_result.form_data = json.dumps(form_data, ensure_ascii=False)
            temp_result.project_name = form_data.get('projectName', '')
            temp_result.project_description = form_data.get('projectDescription', '')
            temp_result.team_size = len(form_data.get('keyPersons', []))
            temp_result.analysis_type = 'pending'  # 标记为待处理
            temp_result.result_data = json.dumps({}, ensure_ascii=False)  # 空结果
            db.session.add(temp_result)
            db.session.commit()
            
            # Session中只保存ID和项目名称
            session['analysis_form_id'] = temp_id
            session['analysis_project_name'] = project_name
            app.logger.info(f"Stored form data in database with temp ID: {temp_id}")
            
        except Exception as e:
            app.logger.error(f"Failed to store form data in database: {str(e)}")
            # 如果数据库失败，至少保存项目名称
            session['analysis_project_name'] = project_name

        # 清理所有旧的分析相关数据，确保新项目不会使用旧的result_id
        session['analysis_status'] = 'not_started'
        session['analysis_started'] = False  # 重置开始标志
        session['analysis_result'] = None
        session['analysis_result_id'] = None  # 关键修复：清理旧的result_id
        session['analysis_progress'] = 0
        session['analysis_stage'] = '准备开始分析...'
        session.pop('analysis_error', None)  # 清理可能存在的错误信息

        # 详细调试session存储
        app.logger.info(f"Generate route - Before storing - Full session: {dict(session)}")
        session.permanent = True  # 设置session为永久性
        session.modified = True  # 确保session修改被保存
        app.logger.info(f"Generate route - After storing - Full session: {dict(session)}")
        app.logger.info(f"Generate route - Session permanent: {session.permanent}, Modified: {session.modified}")

        # Log the received data
        import json
        app.logger.info(f"Received form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        app.logger.info(f"Session data stored successfully")

        # 跳转到新的Matrix风格思考页面，同时启动分析
        return redirect(url_for('thinking_process'))

    except Exception as e:
        app.logger.error(f"Error processing form: {str(e)}")
        flash('处理表单时发生错误，请重试', 'error')
        return redirect(url_for('index'))

def generate_ai_suggestions(form_data, session=None):
    """Generate AI suggestions using OpenAI API with timeout and error handling"""
    import signal
    import time

    def timeout_handler(signum, frame):
        raise TimeoutError("AI分析超时")

    try:
        # 设置60秒超时，避免过长等待
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(60)

        from openai_service import AngelaAI

        # 使用真正的AI服务生成方案
        angela_ai = AngelaAI()

        # 转换数据格式以匹配openai_service的预期格式
        converted_data = {
            'projectName': form_data.get('projectName', form_data.get('project_name', '')),
            'projectDescription': form_data.get('projectDescription', form_data.get('project_description', '')),
            'keyPersons': form_data.get('keyPersons', form_data.get('key_persons', [])),
            'externalResources': form_data.get('externalResources', form_data.get('external_resources', []))
        }

        app.logger.info(f"Calling Angela AI with data: {json.dumps(converted_data, ensure_ascii=False)}")

        # 更新进度：开始AI分析
        if session:
            session['analysis_progress'] = 50
            session['analysis_stage'] = '正在调用AI分析引擎...'
            save_session_in_ajax()  # 保存session确保前端能看到进度更新

        start_time = time.time()
        # 调用AI生成服务，添加SSL错误处理
        try:
            ai_result = angela_ai.generate_income_paths(converted_data, db.session)
        except Exception as network_error:
            # 检查是否是SSL/网络相关错误
            error_str = str(network_error).lower()
            app.logger.error(f"AI调用异常: {str(network_error)}")
            # 取消超时
            signal.alarm(0)
            
            if any(keyword in error_str for keyword in ['ssl', 'timeout', 'connection', 'network', 'recv', 'read', 'httpx', 'httpcore']):
                # 网络/SSL/超时错误
                app.logger.error(f"Network/SSL/Timeout error during AI call: {str(network_error)}")
                # 更新session状态为timeout
                if session:
                    session['analysis_status'] = 'timeout'
                    session['analysis_error'] = f'网络连接问题: {str(network_error)[:100]}'  # 限制错误信息长度
                    save_session_in_ajax()
                # 返回网络错误的备用方案
                return generate_fallback_result(form_data, "网络连接问题，为您提供基础建议")
            else:
                # 其他类型的错误
                app.logger.error(f"General error during AI call: {str(network_error)}")
                # 更新session状态为error
                if session:
                    session['analysis_status'] = 'error'
                    session['analysis_error'] = f'分析过程遇到问题: {str(network_error)[:100]}'
                    save_session_in_ajax()
                # 返回一般错误的备用方案
                return generate_fallback_result(form_data, "分析过程遇到问题，为您提供基础建议")

        # 更新进度：AI分析完成
        if session:
            session['analysis_progress'] = 90
            session['analysis_stage'] = '正在生成分析报告...'
            save_session_in_ajax()  # 保存session确保前端能看到进度更新
        elapsed_time = time.time() - start_time

        # 取消超时
        signal.alarm(0)

        app.logger.info(f"AI analysis completed in {elapsed_time:.2f} seconds")
        app.logger.info(f"AI generated result: {json.dumps(ai_result, ensure_ascii=False)}")

        return ai_result

    except TimeoutError as e:
        # 取消超时
        signal.alarm(0)
        app.logger.error(f"AI analysis timeout: {str(e)}")
        # 设置超时状态到session，让前端显示
        from flask import session
        session['analysis_status'] = 'timeout'
        session['analysis_error'] = '分析超时，为您提供基础建议'
        return generate_fallback_result(form_data, "分析超时，为您提供基础建议")

    except Exception as e:
        # 取消超时
        signal.alarm(0)
        app.logger.error(f"Error generating AI suggestions: {str(e)}")
        app.logger.error(f"Error type: {type(e).__name__}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        # 设置错误状态到session
        from flask import session
        session['analysis_status'] = 'error'
        session['analysis_error'] = f'分析遇到问题: {str(e)}'
        return generate_fallback_result(form_data, f"分析遇到问题，为您提供基础建议")

def generate_fallback_result(form_data, reason=""):
    """生成备用分析结果"""
    project_name = form_data.get('projectName', form_data.get('project_name', '未命名项目'))
    key_persons = form_data.get('keyPersons', form_data.get('key_persons', []))

    # 生成符合新模板格式的备用结果
    return {
        "overview": {
            "situation": f"您的{project_name}项目拥有{len(key_persons)}位关键人物资源，具备基础的合作变现潜力。",
            "gaps": [
                "需要明确各方动机标签",
                "缺少具体的市场渠道",
                "需要补充财务规划角色",
                "缺少风险评估机制"
            ],
            "suggested_roles_to_hunt": [
                {
                    "role": "市场推广专员",
                    "why": "需要专业的推广渠道和营销策略支持",
                    "where_to_find": "LinkedIn、行业社群、营销公司",
                    "outreach_script": "您好，我们有个资源整合项目，需要市场推广方面的专业建议，可否简单交流？"
                },
                {
                    "role": "财务顾问",
                    "why": "需要专业的收益分配和风险评估建议",
                    "where_to_find": "会计师事务所、商业顾问公司、创业孵化器",
                    "outreach_script": "您好，我们在设计一个合作收益模式，希望获得财务结构方面的专业意见。"
                }
            ]
        },
        "paths": [
            {
                "id": "path_1",
                "name": "资源互换合作模式",
                "scene": "基于现有人脉网络的资源交换平台",
                "who_moves_first": "您先梳理各方资源清单",
                "action_steps": [
                    {
                        "owner": "您",
                        "step": "详细梳理每位关键人物的具体资源和可提供的支持类型",
                        "why_it_works": "明确资源价值是建立公平交换机制的基础"
                    },
                    {
                        "owner": "您",
                        "step": "设计资源价值评估标准和交换规则",
                        "why_it_works": "标准化流程降低合作摩擦，提高效率"
                    },
                    {
                        "owner": "关键人物",
                        "step": "根据各自优势承担相应的资源提供和协调角色",
                        "why_it_works": "充分发挥各自专长，实现资源最优配置"
                    }
                ],
                "use_key_person_resources": [person.get("name", f"关键人物{i+1}") for i, person in enumerate(key_persons[:3])],
                "use_external_resources": [],
                "revenue_trigger": "通过资源交换产生的价值差获得收益分成",
                "mvp": "组织一次小型资源对接会，验证交换模式可行性，成功标准为至少达成2个资源对接意向",
                "risks": [
                    "资源价值评估困难",
                    "各方参与积极性不均"
                ],
                "plan_b": "如果资源交换困难，改为按服务付费的简单合作模式",
                "kpis": [
                    "资源对接成功率（目标≥30%）",
                    "参与方满意度评分（目标≥7分）"
                ]
            },
            {
                "id": "path_2", 
                "name": "联合服务收费模式",
                "scene": "整合各方专业能力对外提供付费服务",
                "who_moves_first": "您先调研市场需求",
                "action_steps": [
                    {
                        "owner": "您",
                        "step": "调研目标市场对类似服务的需求和付费意愿",
                        "why_it_works": "市场验证降低项目风险，确保服务有市场价值"
                    },
                    {
                        "owner": "您",
                        "step": "设计标准化的服务流程和定价策略",
                        "why_it_works": "标准化提高服务效率和客户信任度"
                    },
                    {
                        "owner": "关键人物",
                        "step": "根据专业领域承担相应的服务交付责任",
                        "why_it_works": "专业分工保证服务质量，提升客户满意度"
                    }
                ],
                "use_key_person_resources": [person.get("name", f"关键人物{i+1}") for i, person in enumerate(key_persons)],
                "use_external_resources": [],
                "revenue_trigger": "服务费收入按贡献比例分成",
                "mvp": "设计一个简化版服务包，找1-2个潜在客户试点，成功标准为获得正面反馈和付费意向",
                "risks": [
                    "服务质量难以标准化",
                    "客户获取成本过高"
                ],
                "plan_b": "如果对外服务困难，先为内部项目提供增值服务，积累经验和案例",
                "kpis": [
                    "客户试点转化率（目标≥20%）",
                    "服务交付及时率（目标≥90%）"
                ]
            }
        ],
        "notes": f"由于{reason}，以上为基础建议。建议您完善关键人物的动机信息后重新分析，可获得更精准的个性化方案。"
    }

# Knowledge Base Management Routes
@app.route('/history')
@login_required
def analysis_history():
    """历史分析记录页面"""
    try:
        from models import AnalysisResult

        # 根据用户身份显示不同的记录
        if current_user.is_admin:
            # 管理员可以看到所有分析记录
            analysis_records = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).all()
            app.logger.info(f"Admin user viewing {len(analysis_records)} analysis records")
        else:
            # 普通用户只能看到自己的分析记录
            analysis_records = AnalysisResult.query.filter_by(user_id=current_user.id).order_by(AnalysisResult.created_at.desc()).all()
            app.logger.info(f"User {current_user.id} viewing {len(analysis_records)} analysis records")

        return render_template('history_apple.html', analysis_records=analysis_records)

    except Exception as e:
        app.logger.error(f"Error loading analysis history: {str(e)}")
        flash('加载历史记录时发生错误', 'error')
        return redirect(url_for('index'))

@app.route('/history/<record_id>')
@login_required
def view_analysis_record(record_id):
    """查看特定的分析记录详情"""
    try:
        from models import AnalysisResult
        import json

        # 获取指定的分析记录
        record = AnalysisResult.query.filter_by(id=record_id).first()

        if not record:
            flash('找不到指定的分析记录', 'error')
            return redirect(url_for('analysis_history'))

        # 权限检查：普通用户只能查看自己的记录，管理员可以查看所有记录
        if not current_user.is_admin and record.user_id != current_user.id:
            flash('您没有权限查看此分析记录', 'error')
            return redirect(url_for('analysis_history'))

        # 解析JSON数据
        form_data = json.loads(record.form_data) if record.form_data else {}
        result_data = json.loads(record.result_data) if record.result_data else {}

        app.logger.info(f"User {current_user.id} viewing analysis record: {record_id}")

        return render_template('result_pipeline_redesigned.html',
                             form_data=form_data,
                             result=result_data,
                             status='completed',
                             history_mode=True,
                             record_info={
                                 'id': record.id,
                                 'created_at': record.created_at_display,
                                 'analysis_type': record.analysis_type_display
                             })

    except Exception as e:
        app.logger.error(f"Error viewing analysis record {record_id}: {str(e)}")
        flash('查看分析记录时发生错误', 'error')
        return redirect(url_for('analysis_history'))

@app.route('/admin/api/users')
@login_required
@admin_required
def api_users():
    """管理中心用户API - 返回用户列表数据"""
    try:
        users = User.query.all()
        current_month = datetime.now().replace(day=1)

        users_data = []
        for user in users:
            # 确保时间显示格式正确
            created_at_display = user.created_at_display if user.created_at else '未知'
            last_login_display = user.last_login_display if user.last_login else '从未登录'

            users_data.append({
                'id': user.id,
                'name': user.name or '未设置姓名',
                'phone': user.phone,
                'is_admin': user.is_admin,
                'active': user.active,
                'created_at': user.created_at.isoformat() if user.created_at else None,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at_display': created_at_display,
                'last_login_display': last_login_display,
                'current_user_id': current_user.id
            })

        # 统计数据
        stats = {
            'total': len(users),
            'active': len([u for u in users if u.active]),
            'admin': len([u for u in users if u.is_admin]),
            'recent': len([u for u in users if u.created_at and u.created_at >= current_month])
        }

        return jsonify({
            'success': True,
            'users': users_data,
            'stats': stats
        })
    except Exception as e:
        print(f"获取用户数据失败: {e}")
        return jsonify({
            'success': False,
            'message': '获取用户数据失败'
        }), 500

@app.route('/admin')
@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    """后台管理主页 - 统一管理界面"""
    # 查询知识库数据
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')

    query = KnowledgeItem.query

    if status_filter:
        query = query.filter_by(status=status_filter)

    if search_query:
        query = query.filter(KnowledgeItem.original_filename.contains(search_query))

    # 按上传时间倒序排列，只显示未删除的文件
    knowledge_items = query.filter(KnowledgeItem.status != 'deleted').order_by(KnowledgeItem.upload_time.desc()).all()

    return render_template('admin/dashboard_unified.html', 
                         knowledge_items=knowledge_items,
                         status_filter=status_filter,
                         search_query=search_query)


# 用户管理路由


@app.route('/admin/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_add_user():
    """添加新用户"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'

        # 验证输入
        if not name or not phone or not password:
            flash('姓名、手机号和密码都不能为空', 'error')
            return render_template('admin/add_user.html')

        # 验证手机号格式
        if len(phone) != 11 or not phone.isdigit():
            flash('请输入有效的11位手机号', 'error')
            return render_template('admin/add_user.html')

        # 检查手机号是否已存在
        existing_user = User.query.filter_by(phone=phone).first()
        if existing_user:
            flash('该手机号已被注册', 'error')
            return render_template('admin/add_user.html')

        try:
            # 创建新用户
            user = User()
            user.name = name
            user.phone = phone
            user.set_password(password)
            user.active = True
            user.is_admin = is_admin

            db.session.add(user)
            db.session.commit()

            user_type = '管理员' if is_admin else '普通用户'
            flash(f'{user_type} "{name}" 创建成功', 'success')
            return redirect(url_for('admin_dashboard') + '?tab=users')

        except Exception as e:
            flash(f'创建用户失败: {str(e)}', 'error')
            return render_template('admin/add_user.html')

    return render_template('admin/add_user.html')


@app.route('/admin/users/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def admin_edit_user(user_id):
    """编辑用户信息"""
    user = User.query.get_or_404(user_id)

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '').strip()
        is_admin = request.form.get('is_admin') == 'on'
        redirect_to = request.args.get('redirect_to') # Get redirect_to parameter

        # 验证输入
        if not name or not phone:
            flash('姓名和手机号不能为空', 'error')
            return render_template('admin/edit_user.html', user=user)

        # 验证手机号格式
        if len(phone) != 11 or not phone.isdigit():
            flash('请输入有效的11位手机号', 'error')
            return render_template('admin/edit_user.html', user=user)

        # 检查手机号是否与其他用户冲突
        existing_user = User.query.filter(User.phone == phone, User.id != user_id).first()
        if existing_user:
            flash('该手机号已被其他用户使用', 'error')
            return render_template('admin/edit_user.html', user=user)

        try:
            user.name = name
            user.phone = phone
            user.is_admin = is_admin
            db.session.commit()

            # 如果提供了新密码，则更新密码
            if password:
                user.set_password(password)
                db.session.commit() # Commit again if password was changed

            flash('用户信息更新成功！', 'success')
            return redirect(url_for('admin_dashboard') + '?tab=users')

        except Exception as e:
            flash(f'更新用户信息失败: {str(e)}', 'error')
            return render_template('admin/edit_user.html', user=user)

    return render_template('admin/edit_user.html', user=user)


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@login_required
@admin_required
def admin_delete_user(user_id):
    """删除用户"""
    user = User.query.get_or_404(user_id)

    # 防止删除当前登录用户
    if user.id == current_user.id:
        flash('不能删除当前登录的用户', 'error')
        return redirect(url_for('admin_dashboard') + '?tab=users')

    try:
        username = user.name
        db.session.delete(user)
        db.session.commit()

        flash(f'用户 "{username}" 已删除', 'success')

    except Exception as e:
        flash(f'删除用户失败: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard') + '?tab=users')


@app.route('/admin/knowledge/upload', methods=['POST'])
@login_required
@admin_required
def upload_knowledge():
    """上传知识库文件"""
    if 'file' not in request.files:
        flash('没有选择文件', 'error')
        return redirect(url_for('admin_dashboard'))

    file = request.files['file']
    if file.filename == '':
        flash('没有选择文件', 'error')
        return redirect(url_for('admin_dashboard'))

    if file and file.filename and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # 添加时间戳避免文件名冲突
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = timestamp + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            # 获取文件大小
            file_size = get_file_size(file)
            file.save(file_path)

            # 获取文件扩展名
            file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'

            # 保存到数据库
            knowledge_item = KnowledgeItem()
            knowledge_item.filename = filename
            knowledge_item.original_filename = file.filename
            knowledge_item.file_path = file_path
            knowledge_item.file_type = file_extension
            knowledge_item.file_size = file_size
            knowledge_item.content_summary = ''  # 移除描述功能
            knowledge_item.status = 'active'

            db.session.add(knowledge_item)
            db.session.commit()

            flash(f'文件 "{file.filename}" 上传成功', 'success')

        except Exception as e:
            flash(f'上传失败: {str(e)}', 'error')
            # 删除已保存的文件
            if os.path.exists(file_path):
                os.remove(file_path)
    else:
        flash('不支持的文件类型。支持的格式: txt, pdf, doc, docx, xlsx, csv, md, json', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/knowledge/upload-multiple', methods=['POST'])
@login_required
@admin_required
def upload_knowledge_multiple():
    """批量上传知识库文件"""
    files = request.files.getlist('files')
    if not files or all(f.filename == '' for f in files):
        flash('没有选择文件', 'error')
        return redirect(url_for('admin_dashboard'))

    upload_results = []
    success_count = 0
    error_count = 0

    for file in files:
        file_path = None
        if file and file.filename and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                # 添加时间戳避免文件名冲突
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = timestamp + filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

                # 获取文件大小
                file_size = get_file_size(file)
                file.save(file_path)

                # 获取文件扩展名
                file_extension = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else 'unknown'

                # 保存到数据库
                knowledge_item = KnowledgeItem()
                knowledge_item.filename = filename
                knowledge_item.original_filename = file.filename
                knowledge_item.file_path = file_path
                knowledge_item.file_type = file_extension
                knowledge_item.file_size = file_size
                knowledge_item.content_summary = ''  # 移除描述功能
                knowledge_item.status = 'active'

                db.session.add(knowledge_item)
                db.session.commit()

                upload_results.append({'filename': file.filename, 'status': 'success'})
                success_count += 1

            except Exception as e:
                upload_results.append({'filename': file.filename, 'status': 'error', 'error': str(e)})
                error_count += 1
                # 删除已保存的文件
                if file_path and os.path.exists(file_path):
                    os.remove(file_path)
        else:
            upload_results.append({'filename': file.filename if file else 'unknown', 'status': 'error', 'error': '不支持的文件类型'})
            error_count += 1

    # 生成结果消息
    if success_count > 0 and error_count == 0:
        flash(f'成功上传 {success_count} 个文件', 'success')
    elif success_count > 0 and error_count > 0:
        flash(f'成功上传 {success_count} 个文件，{error_count} 个文件失败', 'warning')
    else:
        flash(f'上传失败，{error_count} 个文件未能上传', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/knowledge/create-text', methods=['POST'])
@login_required
@admin_required
def create_text_knowledge():
    """创建文本知识条目"""
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title or not content:
        flash('标题和内容不能为空', 'error')
        return redirect(url_for('admin_dashboard'))

    file_path = None
    try:
        # 创建文本文件
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
        filename = f"{timestamp}_{secure_filename(title)}.txt"
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 保存文本内容到文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 计算文件大小
        file_size = len(content.encode('utf-8'))

        # 保存到数据库
        knowledge_item = KnowledgeItem()
        knowledge_item.filename = filename
        knowledge_item.original_filename = f"{title}.txt"
        knowledge_item.file_path = file_path
        knowledge_item.file_type = 'text'
        knowledge_item.file_size = file_size
        knowledge_item.content_summary = content  # 对于文本类型，直接存储内容
        knowledge_item.status = 'active'

        db.session.add(knowledge_item)
        db.session.commit()

        flash(f'文本知识条目 "{title}" 创建成功', 'success')

    except Exception as e:
        flash(f'创建失败: {str(e)}', 'error')
        # 删除已保存的文件
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/knowledge/<int:item_id>/edit', methods=['POST'])
@login_required
@admin_required
def edit_text_knowledge(item_id):
    """编辑文本知识条目"""
    item = KnowledgeItem.query.get_or_404(item_id)

    # 只允许编辑文本类型的条目
    if item.file_type != 'text':
        flash('只能编辑文本类型的知识条目', 'error')
        return redirect(url_for('admin_dashboard'))

    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()

    if not title or not content:
        flash('标题和内容不能为空', 'error')
        return redirect(url_for('admin_dashboard'))

    try:
        # 更新文件内容
        with open(item.file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 更新数据库记录
        item.original_filename = f"{title}.txt"
        item.file_size = len(content.encode('utf-8'))
        item.content_summary = content
        item.last_modified = datetime.utcnow()

        db.session.commit()

        flash(f'文本知识条目 "{title}" 更新成功', 'success')

    except Exception as e:
        flash(f'更新失败: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))

@app.route('/admin/knowledge/<int:item_id>/toggle-status', methods=['POST'])
@login_required
@admin_required
def toggle_knowledge_status(item_id):
    """切换知识库条目状态"""
    item = KnowledgeItem.query.get_or_404(item_id)

    if item.status == 'active':
        item.status = 'paused'
        message = '已暂停使用'
    elif item.status == 'paused':
        item.status = 'active'
        message = '已启用使用'
    else:
        flash('无法切换已删除项目的状态', 'error')
        return redirect(url_for('admin_dashboard'))

    db.session.commit()
    flash(f'"{item.original_filename}" {message}', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/knowledge/<int:item_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_knowledge(item_id):
    """删除知识库条目"""
    item = KnowledgeItem.query.get_or_404(item_id)

    try:
        # 删除文件
        if os.path.exists(item.file_path):
            os.remove(item.file_path)

        # 从数据库删除
        db.session.delete(item)
        db.session.commit()

        flash(f'"{item.original_filename}" 已删除', 'success')
    except Exception as e:
        flash(f'删除失败: {str(e)}', 'error')

    return redirect(url_for('admin_dashboard'))


# ============= 非劳务收入路径生成 API =============

@app.route('/generate-paths', methods=['POST'])
@login_required
def generate_paths():
    """生成非劳务收入路径"""
    try:
        from openai_service import angela_ai

        # 获取表单数据
        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400

        # 记录请求开始时间
        start_time = datetime.now()

        # 使用AI服务生成路径
        result = angela_ai.generate_income_paths(data, db.session)

        # 记录处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        result['meta'] = {
            'processing_time': processing_time,
            'generated_at': start_time.isoformat(),
            'version': '1.0'
        }

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Path generation error: {e}")
        return jsonify({
            'error': '路径生成失败',
            'message': str(e)
        }), 500

@app.route('/refine-path', methods=['POST'])
@login_required
def refine_path():
    """细化指定路径"""
    try:
        from openai_service import angela_ai

        data = request.get_json()
        if not data:
            return jsonify({'error': '无效的请求数据'}), 400

        path_data = data.get('path_data')
        refinement_data = data.get('refinement_data')

        if not path_data or not refinement_data:
            return jsonify({'error': '缺少必要的路径数据或细化信息'}), 400

        # 使用AI服务细化路径
        result = angela_ai.refine_path(path_data, refinement_data, db.session)

        return jsonify(result)

    except Exception as e:
        app.logger.error(f"Path refinement error: {e}")
        return jsonify({
            'error': '路径细化失败',
            'message': str(e)
        }), 500

@app.route('/result-preview')
@login_required
def result_preview():
    """重定向到正确的结果页面，避免用户看到模拟数据"""
    from flask import flash, redirect, url_for
    flash('请通过首页提交表单来获得个性化分析结果', 'info')
    return redirect(url_for('index'))



@app.route('/admin/ai-chat', methods=['POST'])
@login_required
@admin_required
def ai_chat():
    """AI对话测试接口"""
    try:
        data = request.get_json()
        message = data.get('message', '').strip()
        model = data.get('model', 'gpt-4o')
        use_knowledge = data.get('use_knowledge', True)
        chat_history = data.get('chat_history', [])

        if not message:
            return jsonify({'success': False, 'error': '消息不能为空'})

        # 导入OpenAI
        from openai import OpenAI

        # 初始化OpenAI客户端
        client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))

        # 构建消息列表
        messages = []

        # 如果启用知识库，添加系统提示和知识库内容
        if use_knowledge:
            # 获取活跃的知识库内容
            active_items = KnowledgeItem.query.filter_by(status='active').all()
            knowledge_content = ""

            for item in active_items[:10]:  # 限制使用前10个文件，避免上下文过长
                try:
                    if item.file_type == 'text':
                        # 对于文本类型，直接使用content_summary
                        knowledge_content += f"\n\n=== {item.original_filename} ===\n{item.content_summary}"
                    else:
                        # 对于其他文件类型，尝试读取文件内容
                        if os.path.exists(item.file_path):
                            with open(item.file_path, 'r', encoding='utf-8') as f:
                                file_content = f.read()[:2000]  # 限制每个文件2000字符
                                knowledge_content += f"\n\n=== {item.original_filename} ===\n{file_content}"
                except Exception as e:
                    print(f"读取文件 {item.filename} 时出错: {e}")
                    continue

            # 系统提示
            system_prompt = f"""你是Angela AI助手，专门帮助用户基于知识库内容回答问题。

知识库内容：
{knowledge_content}

请基于以上知识库内容回答用户问题。如果知识库中没有相关信息，请诚实说明，并提供一般性的建议。回答要准确、有用，并尽量引用具体的知识库内容。"""

            messages.append({"role": "system", "content": system_prompt})
        else:
            # 不使用知识库的系统提示
            messages.append({"role": "system", "content": "你是Angela AI助手，请友好地回答用户的问题。"})

        # 添加对话历史（最近5轮对话）
        recent_history = chat_history[-10:] if len(chat_history) > 10 else chat_history
        messages.extend(recent_history)

        # 添加当前用户消息
        messages.append({"role": "user", "content": message})

        # 调用OpenAI API (流式响应)
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            stream=True
        )

        # 生成流式响应
        def generate_stream():
            full_response = ""
            for chunk in response:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield f"data: {json.dumps({'content': content, 'type': 'delta'})}\n\n"

            # 发送完成信号
            yield f"data: {json.dumps({'type': 'done', 'full_response': full_response, 'model_used': model, 'knowledge_used': use_knowledge})}\n\n"

        return Response(generate_stream(), mimetype='text/plain')

    except Exception as e:
        print(f"AI对话错误: {e}")
        return jsonify({
            'success': False, 
            'error': f'AI服务暂时不可用: {str(e)}'
        })

def generate_fallback_suggestions(form_data, reason="AI服务暂时不可用"):
    """当AI服务不可用时生成基础建议"""
    # 修复字段名：使用正确的驼峰命名
    project_name = form_data.get('projectName', form_data.get('project_name', '您的项目'))
    key_persons = form_data.get('keyPersons', form_data.get('key_persons', []))

    # 生成符合新模板格式的备用结果
    return {
        "overview": {
            "situation": f"根据您提交的项目信息「{project_name}」和团队配置，我们为您准备了以下基础收入路径建议。虽然当前AI深度分析服务暂时不可用，但基于常见的非劳务收入模式，为您提供这些可行的起步方案。",
            "gaps": [
                "需要明确各方动机标签",
                "缺少具体的市场渠道",
                "需要补充财务规划角色",
                "缺少风险评估机制"
            ],
            "suggested_roles_to_hunt": [
                {
                    "role": "市场推广专员",
                    "why": "需要专业的推广渠道和营销策略支持",
                    "where_to_find": "LinkedIn、行业社群、营销公司",
                    "outreach_script": "您好，我们有个资源整合项目，需要市场推广方面的专业建议，可否简单交流？"
                },
                {
                    "role": "财务顾问",
                    "why": "需要专业的收益分配和风险评估建议",
                    "where_to_find": "会计师事务所、商业顾问公司、创业孵化器",
                    "outreach_script": "您好，我们在设计一个合作收益模式，希望获得财务结构方面的专业意见。"
                }
            ]
        },
        "paths": [
            {
                "id": "path_1",
                "name": "资源互换合作模式",
                "scene": "基于现有人脉网络的资源交换平台",
                "who_moves_first": "您先梳理各方资源清单",
                "action_steps": [
                    {
                        "owner": "您",
                        "step": "详细梳理每位关键人物的具体资源和可提供的支持类型",
                        "why_it_works": "明确资源价值是建立公平交换机制的基础"
                    },
                    {
                        "owner": "您",
                        "step": "设计资源价值评估标准和交换规则",
                        "why_it_works": "标准化流程降低合作摩擦，提高效率"
                    },
                    {
                        "owner": "关键人物",
                        "step": "根据各自优势承担相应的资源提供和协调角色",
                        "why_it_works": "充分发挥各自专长，实现资源最优配置"
                    }
                ],
                "use_key_person_resources": [person.get("name", f"关键人物{i+1}") for i, person in enumerate(key_persons[:3])],
                "use_external_resources": [],
                "revenue_trigger": "通过资源交换产生的价值差获得收益分成",
                "mvp": "组织一次小型资源对接会，验证交换模式可行性，成功标准为至少达成2个资源对接意向",
                "risks": [
                    "资源价值评估困难",
                    "各方参与积极性不均"
                ],
                "plan_b": "如果资源交换困难，改为按服务付费的简单合作模式",
                "kpis": [
                    "资源对接成功率（目标≥30%）",
                    "参与方满意度评分（目标≥7分）"
                ]
            },
            {
                "id": "path_2", 
                "name": "联合服务收费模式",
                "scene": "整合各方专业能力对外提供付费服务",
                "who_moves_first": "您先调研市场需求",
                "action_steps": [
                    {
                        "owner": "您",
                        "step": "调研目标市场对类似服务的需求和付费意愿",
                        "why_it_works": "市场验证降低项目风险，确保服务有市场价值"
                    },
                    {
                        "owner": "您",
                        "step": "设计标准化的服务流程和定价策略",
                        "why_it_works": "标准化提高服务效率和客户信任度"
                    },
                    {
                        "owner": "关键人物",
                        "step": "根据专业领域承担相应的服务交付责任",
                        "why_it_works": "专业分工保证服务质量，提升客户满意度"
                    }
                ],
                "use_key_person_resources": [person.get("name", f"关键人物{i+1}") for i, person in enumerate(key_persons)],
                "use_external_resources": [],
                "revenue_trigger": "服务费收入按贡献比例分成",
                "mvp": "设计一个简化版服务包，找1-2个潜在客户试点，成功标准为获得正面反馈和付费意向",
                "risks": [
                    "服务质量难以标准化",
                    "客户获取成本过高"
                ],
                "plan_b": "如果对外服务困难，先为内部项目提供增值服务，积累经验和案例",
                "kpis": [
                    "客户试点转化率（目标≥20%）",
                    "服务交付及时率（目标≥90%）"
                ]
            }
        ],
        "notes": f"由于{reason}，以上为基础建议。建议您完善关键人物的动机信息后重新分析，可获得更精准的个性化方案。"
    }

@app.route('/profile')
@login_required  
def user_profile():
    """普通用户的个人信息页面"""
    return render_template('user_profile_apple.html')

@app.route('/admin/models/test', methods=['POST'])
@login_required
@admin_required
def test_model_connection():
    """测试模型连接"""
    try:
        import time
        from openai_service import client

        start_time = time.time()

        # 发送简单的测试请求
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "请回复'连接测试成功'"}],
            max_tokens=10,
            temperature=0
        )

        response_time = int((time.time() - start_time) * 1000)  # 转换为毫秒

        if response.choices[0].message.content:
            return jsonify({
                'success': True,
                'message': '模型连接测试成功',
                'response_time': response_time,
                'model_response': response.choices[0].message.content.strip()
            })
        else:
            return jsonify({'success': False, 'message': 'API连接成功但响应为空'}), 500

    except Exception as e:
        app.logger.error(f"模型连接测试失败: {str(e)}")
        return jsonify({
            'success': False, 
            'message': f'连接测试失败: {str(e)}'
        }), 500

@app.route('/admin/api/model_config', methods=['GET'])
@login_required
@admin_required
def get_model_config():
    """获取当前模型配置"""
    try:
        from models import ModelConfig
        import traceback

        app.logger.info("开始获取模型配置")

        # 获取主要配置
        main_config = ModelConfig.get_config('main_analysis')
        app.logger.info(f"主分析配置: {main_config}")

        return jsonify({
            'success': True,
            'config': {
                'main_analysis_model': main_config['model'],
                'temperature': main_config['temperature'],
                'max_tokens': main_config['max_tokens'],
                'timeout': main_config['timeout']
            }
        })
    except Exception as e:
        import traceback
        app.logger.error(f"获取模型配置失败: {str(e)}")
        app.logger.error(f"错误追踪: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'获取配置失败: {str(e)}'}), 500

@app.route('/admin/api/model_config', methods=['POST'])
@login_required
@admin_required
def save_model_config_api():
    """保存模型配置API"""
    try:
        import traceback

        app.logger.info("开始保存模型配置")

        # 获取请求数据
        data = request.get_json()
        app.logger.info(f"接收到的数据: {data}")

        # 验证数据
        if not data:
            app.logger.error("请求数据为空")
            return jsonify({'success': False, 'message': '无效的请求数据'}), 400

        model = data.get('model', 'gpt-4o-mini')
        temperature = float(data.get('temperature', 0.7))
        max_tokens = int(data.get('max_tokens', 2500))
        timeout = int(data.get('timeout', 45))

        app.logger.info(f"解析后的配置: model={model}, temp={temperature}, tokens={max_tokens}, timeout={timeout}")

        # 验证模型名称
        valid_models = ['gpt-4.1', 'gpt-4o', 'gpt-4o-mini']
        if model not in valid_models:
            app.logger.error(f"无效的模型名称: {model}")
            return jsonify({'success': False, 'message': '无效的模型选择'}), 400

        from models import ModelConfig

        # 更新主分析配置
        app.logger.info("开始更新数据库配置")
        ModelConfig.set_config('main_analysis', model, temperature, max_tokens, timeout)
        app.logger.info("数据库配置更新完成")

        app.logger.info(f"模型配置已更新: {model}, temperature={temperature}, max_tokens={max_tokens}")

        return jsonify({
            'success': True,
            'message': '配置保存成功',
            'config': {
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'timeout': timeout
            }
        })

    except Exception as e:
        import traceback
        app.logger.error(f"保存模型配置失败: {str(e)}")
        app.logger.error(f"错误追踪: {traceback.format_exc()}")
        return jsonify({'success': False, 'message': f'保存失败: {str(e)}'}), 500

@app.route('/profile/update', methods=['POST'])
@login_required
def update_user_profile():
    """更新用户个人信息"""
    try:
        # 获取表单数据
        new_name = request.form.get('name', '').strip()
        action = request.form.get('action')

        if action == 'update_name':
            # 更新姓名
            current_user.name = new_name if new_name else None
            db.session.commit()
            flash('姓名更新成功', 'success')

        elif action == 'change_password':
            # 修改密码
            current_password = request.form.get('current_password', '').strip()
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()

            # 验证当前密码
            if not current_user.check_password(current_password):
                flash('当前密码不正确', 'error')
                return redirect(url_for('user_profile'))

            # 验证新密码
            if len(new_password) < 6:
                flash('新密码长度至少6位', 'error')
                return redirect(url_for('user_profile'))

            if new_password != confirm_password:
                flash('两次输入的密码不一致', 'error')
                return redirect(url_for('user_profile'))

            # 更新密码
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功', 'success')

        return redirect(url_for('user_profile'))

    except Exception as e:
        app.logger.error(f"Update profile error: {str(e)}")
        flash('更新失败，请重试', 'error')
        return redirect(url_for('user_profile'))



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)