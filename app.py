# 首先加载环境变量
from dotenv import load_dotenv
load_dotenv()

import os
import json
import logging
import traceback
import uuid
import time
import signal
from datetime import datetime
from urllib.parse import urlparse
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

# 启用调试模式以显示详细错误信息
app.config['DEBUG'] = True

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
            "sslmode": "disable",
            "connect_timeout": 10,
            "application_name": "incomestreamai_app"
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
        # 兼容性修复：使用 pbkdf2_sha256 而不是 scrypt，避免 Python 3.9.6 兼容性问题
        try:
            default_user.set_password('aibenzong9264')
        except Exception as e:
            logger.warning(f"默认密码哈希失败，使用兼容模式: {e}")
            # 手动设置密码哈希，使用更兼容的方法
            from werkzeug.security import generate_password_hash
            default_user.password_hash = generate_password_hash('aibenzong9264', method='pbkdf2:sha256')
        default_user.is_admin = True
        db.session.add(default_user)
        db.session.commit()
        logger.info("已创建默认管理员账号: 18302196515 / aibenzong9264")
    elif not default_user.is_admin:
        # 确保18302196515用户是管理员
        default_user.is_admin = True
        default_user.name = '系统管理员'
        db.session.commit()
        logger.info("已将18302196515用户设置为管理员")

    # 初始化默认模型配置
    default_configs = [
        ('main_analysis', 'gpt-4o', 0.7, 2500, 45),
        ('chat', 'gpt-4o', 0.7, 1500, 30),
        ('fallback', 'gpt-4o-mini', 0.5, 2000, 60)
    ]

    for config_name, model_name, temperature, max_tokens, timeout in default_configs:
        existing_config = ModelConfig.query.filter_by(config_name=config_name).first()
        if not existing_config:
            ModelConfig.set_config(config_name, model_name, temperature, max_tokens, timeout)
            logger.info(f"已创建默认模型配置: {config_name} -> {model_name}")

@app.route('/')
@login_required
def index():
    """Main form page for user input - Apple design"""
    # 检查用户AI分析额度
    has_quota = current_user.has_quota()
    remaining_quota = current_user.remaining_quota
    quota_info = {
        'has_quota': has_quota,
        'remaining': remaining_quota,
        'total': current_user.ai_quota,
        'used': current_user.used_quota,
        'quota_display': current_user.quota_display
    }
    return render_template('index_apple.html', quota_info=quota_info)

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
                # 验证重定向URL以防止开放重定向攻击
                parsed_url = urlparse(next_page)
                # 只允许相对URL或同域名URL
                if not parsed_url.netloc or parsed_url.netloc == request.host:
                    return redirect(next_page)
                # 如果是外部URL，重定向到首页
                flash('无效的重定向URL，已重定向到首页', 'warning')
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
    """从FormSubmission表获取表单数据，优先获取用户最新提交的数据"""
    try:
        app.logger.info(f"📍 get_form_data_from_db调用 - Session内容: {dict(session)}")
        
        # 总是优先查找当前用户最新的表单提交记录，而不是依赖session
        if current_user and current_user.is_authenticated:
            from models import FormSubmission

            
            # 直接查找当前用户最新的表单提交记录
            recent_submission = FormSubmission.query.filter_by(
                user_id=current_user.id,
                status='submitted'
            ).order_by(FormSubmission.created_at.desc()).first()
            
            app.logger.info(f"📍 查找用户{current_user.id}的最新FormSubmission: {recent_submission is not None}")
            
            if recent_submission and recent_submission.form_data_complete:
                form_data = json.loads(recent_submission.form_data_complete)
                app.logger.info(f"✅ 获取到最新表单数据: {form_data.get('projectName', 'Unknown')} (ID: {recent_submission.id})")
                
                # 确保session与最新数据同步
                session['form_submission_id'] = recent_submission.id
                session['analysis_project_name'] = form_data.get('projectName', '')
                session.modified = True
                return form_data
            else:
                app.logger.warning("⚠️ 没有找到有效的FormSubmission记录")
        
        # 备用方案：从session获取submission_id（仅在用户未登录时使用）
        submission_id = session.get('form_submission_id')
        if submission_id:
            from models import FormSubmission

            form_submission = FormSubmission.query.get(submission_id)
            app.logger.info(f"📍 备用方案：通过submission_id查询: {form_submission is not None}")
            
            if form_submission and form_submission.form_data_complete:
                form_data = json.loads(form_submission.form_data_complete)
                app.logger.info(f"✅ 通过submission_id找到表单数据: {form_data.get('projectName', 'Unknown')}")
                return form_data
        
        # 最后尝试从session获取（向后兼容和备用存储）
        legacy_data = session.get('analysis_form_data')
        if legacy_data:
            app.logger.info("✅ 从session的backup存储找到表单数据")
            return legacy_data
        
        app.logger.error("❌ 所有方法都未能获取到表单数据")
        return None
        
    except Exception as e:
        app.logger.error(f"Failed to get form data from FormSubmission: {str(e)}")
        return session.get('analysis_form_data')

def save_session_in_ajax():
    """辅助函数：确保AJAX请求中session被正确保存，监控session大小"""
    from flask import session

    
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

@app.route('/thinking-demo')
def thinking_demo():
    """独立的thinking页面演示 - 无需登录和表单数据"""
    # 模拟session数据用于演示
    session['analysis_status'] = 'processing'
    session['analysis_progress'] = 50
    session['analysis_stage'] = '演示模式 - AI分析进行中...'
    
    app.logger.info("Thinking demo page loaded - standalone demo mode")
    return render_template('thinking_process.html')

@app.route('/debug_session_reset')
@login_required
def debug_session_reset():
    """临时调试工具：重置session并显示用户的所有表单提交记录"""
    from models import FormSubmission

    
    # 清理所有session数据
    keys_to_clear = ['form_submission_id', 'analysis_project_name', 'analysis_status', 
                     'analysis_result_id', 'analysis_started', 'analysis_progress']
    for key in keys_to_clear:
        session.pop(key, None)
    
    # 获取用户所有表单提交记录
    submissions = FormSubmission.query.filter_by(user_id=current_user.id).order_by(
        FormSubmission.created_at.desc()).all()
    
    result = {
        'session_cleared': True,
        'user_submissions': []
    }
    
    for sub in submissions:
        result['user_submissions'].append({
            'id': sub.id,
            'project_name': sub.project_name,
            'created_at': sub.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'description': sub.project_description[:100] + '...' if len(sub.project_description or '') > 100 else sub.project_description
        })
    
    return jsonify(result)

@app.route('/start_analysis', methods=['POST'])
@login_required
def start_analysis():
    """专门用于启动AI分析的接口 - 增强错误处理，确保始终返回JSON"""
    # 最外层错误捕获 - 防止任何错误导致前端收到空响应
    try:
        # 检查用户AI分析额度
        if not current_user.has_quota():
            app.logger.warning(f"User {current_user.id} has no quota left: {current_user.quota_display}")
            return jsonify({
                'status': 'error',
                'message': f'您的AI分析额度已用完（{current_user.quota_display}），请联系管理员增加额度',
                'error_code': 'NO_QUOTA',
                'quota_info': {
                    'used': current_user.used_quota,
                    'total': current_user.ai_quota,
                    'remaining': current_user.remaining_quota
                }
            })
        
        form_data = get_form_data_from_db(session)
        if not form_data:
            return jsonify({
                'status': 'error',
                'message': '没有找到表单数据',
                'error_code': 'NO_FORM_DATA'
            })
        
        # 重要：每次启动分析都强制重置状态，确保真正执行OpenAI API调用
        app.logger.info(f"Force reset analysis status - Current: {session.get('analysis_status')}")
        session['analysis_status'] = 'not_started'
        session['analysis_started'] = False
        session['analysis_progress'] = 0
        if 'analysis_result_id' in session:
            del session['analysis_result_id']
        save_session_in_ajax()
        
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
        
        # 网络错误时，立即尝试生成备用方案
        error_str = str(e).lower()
        if any(keyword in error_str for keyword in ['ssl', 'timeout', 'connection', 'network', 'recv', 'read', 'socket', 'systemexit']):
            app.logger.info(f"Network error detected in start_analysis: {str(e)}, generating immediate fallback")
            try:
                # 获取表单数据用于备用方案
                local_form_data = get_form_data_from_db(session)
                if not local_form_data:
                    # 如果数据库中没有表单数据，使用空字典
                    local_form_data = {}
                
                # 直接生成备用方案并设置为completed状态
                fallback_result = generate_fallback_result(local_form_data)
                
                # 保存到数据库（添加重复性检查）
                from models import AnalysisResult
                from datetime import datetime, timedelta
                
                # 检查是否已存在相同项目的fallback结果（防止重复保存）
                project_name = local_form_data.get('projectName', '') if local_form_data else ''
                existing_fallback = AnalysisResult.query.filter_by(
                    user_id=current_user.id,
                    project_name=project_name,
                    analysis_type='fallback_network'
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                # 如果2分钟内已有相同的fallback，使用现有的
                if existing_fallback:
                    time_diff = datetime.utcnow() - existing_fallback.created_at
                    if time_diff < timedelta(minutes=2):
                        app.logger.info(f"⚠️ 检测到2分钟内的重复fallback，使用现有记录: {existing_fallback.id}")
                        fallback_id = existing_fallback.id
                    else:
                        # 超过2分钟，创建新的
                        fallback_id = str(uuid.uuid4())
                        analysis_result = AnalysisResult()
                        analysis_result.id = fallback_id
                        analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                        analysis_result.user_id = current_user.id
                        analysis_result.form_data = json.dumps(local_form_data, ensure_ascii=False)
                        analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                        analysis_result.project_name = project_name
                        analysis_result.project_description = local_form_data.get('projectDescription', '') if local_form_data else ''
                        analysis_result.team_size = len(local_form_data.get('keyPersons', [])) if local_form_data else 0
                        analysis_result.analysis_type = 'fallback_network'
                        db.session.add(analysis_result)
                        db.session.commit()
                else:
                    # 没有现有fallback，创建新的
                    fallback_id = str(uuid.uuid4())
                    analysis_result = AnalysisResult()
                    analysis_result.id = fallback_id
                    analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                    analysis_result.user_id = current_user.id
                    analysis_result.form_data = json.dumps(local_form_data, ensure_ascii=False)
                    analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                    analysis_result.project_name = project_name
                    analysis_result.project_description = local_form_data.get('projectDescription', '') if local_form_data else ''
                    analysis_result.team_size = len(local_form_data.get('keyPersons', [])) if local_form_data else 0
                    analysis_result.analysis_type = 'fallback_network'
                    db.session.add(analysis_result)
                    db.session.commit()
                
                # 设置session为completed状态
                session['analysis_status'] = 'completed'
                session['analysis_result_id'] = fallback_id
                session['analysis_progress'] = 100
                save_session_in_ajax()
                
                app.logger.info(f"Network error fallback generated successfully, ID: {fallback_id}")
                
                return jsonify({
                    'status': 'completed',
                    'message': '网络不稳定，已生成备用方案...',
                    'progress': 100
                })
                
            except Exception as fallback_error:
                app.logger.error(f"Fallback generation in start_analysis failed: {str(fallback_error)}")
        
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
    """AI思考流端点 - 为思考过程页面提供实时AI思考内容"""
    try:
        import random
        # 检查分析状态
        status = session.get('analysis_status', 'not_started')
        
        if status == 'completed':
            return jsonify({
                'status': 'completed',
                'content': '✨ 分析完成，正在为您呈现结果...'
            })
        elif status == 'error':
            return jsonify({
                'status': 'error',
                'content': '❌ 分析遇到问题，请稍后重试'
            })
        elif status in ['running', 'processing', 'not_started']:  # 增加not_started状态也能获取AI思考流
            # 生成更丰富的AI思考内容，模拟真实的分析过程
            thinking_content = [
                '🧠 正在深度分析项目的市场潜力和可行性...',
                '💡 构建非劳务收入管道的最优路径...',
                '⚡ 评估各种资源组合的投资回报率...',
                '🔍 识别潜在风险点并制定应对策略...',
                '📊 计算预期收益和时间投入比例...',
                '🎯 优化人员配置和资源分配方案...',
                '🌟 寻找项目的独特竞争优势...',
                '💰 设计可持续的盈利模式...',
                '🚀 制定项目启动和扩张计划...',
                '🔮 预测市场趋势和机会窗口...',
                '⚙️ 整合资源链条，建立协作框架...',
                '🎨 设计品牌价值和市场定位策略...',
                '📈 制定收入阶梯和增长曲线...',
                '🔬 研究用户需求和市场空白...',
                '💎 挖掘隐藏的价值创造机会...',
                '🌐 构建可扩展的商业生态系统...',
                '⚡ OpenAI正在深度思考您的项目方案...',
                '🤖 AI算法正在匹配最优收入模式...',
                '📋 正在生成个性化的实施建议...'
            ]
            
            content = random.choice(thinking_content)
            return jsonify({
                'status': 'available',
                'content': content
            })
        else:
            # 为其他状态也提供AI思考内容，确保用户能看到内容
            fallback_content = [
                '🧠 正在深度分析项目的市场潜力和可行性...',
                '💡 构建非劳务收入管道的最优路径...',
                '⚡ 评估各种资源组合的投资回报率...',
                '🔍 识别潜在风险点并制定应对策略...',
                '🤖 AI算法正在匹配最优收入模式...'
            ]
            content = random.choice(fallback_content)
            return jsonify({
                'status': 'available',  # 改为available确保内容被显示
                'content': content
            })
            
    except Exception as e:
        logger.error(f"Error in get_ai_thinking_stream: {e}")
        return jsonify({
            'status': 'error',
            'content': '⚠️ 思考流暂时不可用，请稍后重试'
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
            fallback_result = generate_fallback_result(form_data)

            # 保存备用方案到数据库
            import uuid

            from models import AnalysisResult
            fallback_id = str(uuid.uuid4())
            analysis_result = AnalysisResult()
            analysis_result.id = fallback_id
            analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
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
        
        # 使用强化的多层错误处理机制调用AI分析
        suggestions = None
        max_ai_retries = 2
        for retry_count in range(max_ai_retries):
            try:
                app.logger.info(f"🚀 AI分析尝试 {retry_count + 1}/{max_ai_retries} - 即将调用generate_ai_suggestions")
                suggestions = generate_ai_suggestions(form_data, session)
                app.logger.info(f"✅ generate_ai_suggestions成功返回，数据类型: {type(suggestions)}")
                if suggestions:
                    app.logger.info("🎯 获得有效suggestions，跳出重试循环")
                    break  # 成功获得结果，跳出重试循环
                else:
                    app.logger.warning("⚠️ generate_ai_suggestions返回了空结果")
            except Exception as ai_error:
                app.logger.error(f"💥 AI分析失败 (尝试 {retry_count + 1}): {str(ai_error)}")
                app.logger.error(f"💥 异常类型: {type(ai_error).__name__}")
                import traceback
                app.logger.error(f"💥 完整错误堆栈: {traceback.format_exc()}")
                if retry_count == max_ai_retries - 1:
                    # 最后一次尝试失败，生成备用方案
                    app.logger.info("🛡️ 最后尝试失败，生成备用方案")
                    suggestions = generate_fallback_result(form_data, "分析过程遇到技术问题，为您提供基础建议")
                    session['analysis_fallback'] = True
                    save_session_in_ajax()
                else:
                    # 等待后重试
                    app.logger.warning(f"⏳ 等待3秒后进行第{retry_count + 2}次重试...")
                    time.sleep(3)
                    continue

        if suggestions and isinstance(suggestions, dict):
            # 分析成功 - 将结果存储到数据库而不是session，避免session过大
            import uuid
            result_id = str(uuid.uuid4())

            # 创建AnalysisResult实例（添加重复性检查）
            from datetime import datetime, timedelta
            
            # 使用数据库锁防止并发重复保存
            project_name = form_data.get('projectName', '')
            
            # 防止并发创建重复记录
            try:
                # 查询现有记录，检查是否存在重复
                existing_result = AnalysisResult.query.filter_by(
                    user_id=current_user.id,
                    project_name=project_name,
                    analysis_type='ai_analysis'
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                # 如果2分钟内已有相同的分析结果，使用现有的
                if existing_result:
                    time_diff = datetime.utcnow() - existing_result.created_at
                    if time_diff < timedelta(minutes=2):
                        app.logger.info(f"⚠️ 检测到2分钟内的重复分析，使用现有记录: {existing_result.id}")
                        result_id = existing_result.id
                        # 使用现有记录，无需操作数据库
                    else:
                        # 超过2分钟，创建新的分析结果
                        analysis_result = AnalysisResult()
                        analysis_result.id = result_id
                        analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                        analysis_result.user_id = current_user.id  # 关联当前用户
                        analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                        analysis_result.result_data = json.dumps(suggestions, ensure_ascii=False)
                        analysis_result.project_name = project_name
                        analysis_result.project_description = form_data.get('projectDescription', '')
                        analysis_result.team_size = len(form_data.get('keyPersons', []))
                        analysis_result.analysis_type = 'ai_analysis'
                        db.session.add(analysis_result)
                        db.session.commit()
                        # 成功创建新记录后，消耗用户AI分析额度
                        if current_user.consume_quota():
                            db.session.commit()  # 保存额度变更
                            app.logger.info(f"✅ 创建新的分析记录: {result_id}，消耗额度1次，剩余: {current_user.remaining_quota}")
                        else:
                            app.logger.warning(f"⚠️ 额度消耗失败，用户当前额度: {current_user.quota_display}")
                else:
                    # 没有现有分析结果，创建新的
                    analysis_result = AnalysisResult()
                    analysis_result.id = result_id
                    analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                    analysis_result.user_id = current_user.id  # 关联当前用户
                    analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                    analysis_result.result_data = json.dumps(suggestions, ensure_ascii=False)
                    analysis_result.project_name = project_name
                    analysis_result.project_description = form_data.get('projectDescription', '')
                    analysis_result.team_size = len(form_data.get('keyPersons', []))
                    analysis_result.analysis_type = 'ai_analysis'
                    db.session.add(analysis_result)
                    db.session.commit()
                    # 成功创建新记录后，消耗用户AI分析额度
                    if current_user.consume_quota():
                        db.session.commit()  # 保存额度变更
                        app.logger.info(f"✅ 创建首个分析记录: {result_id}，消耗额度1次，剩余: {current_user.remaining_quota}")
                    else:
                        app.logger.warning(f"⚠️ 额度消耗失败，用户当前额度: {current_user.quota_display}")
                    
            except Exception as db_error:
                app.logger.error(f"❌ 数据库操作失败: {str(db_error)}")
                db.session.rollback()
                # 如果数据库操作失败，重新检查是否有其他并发请求已经创建了记录
                existing_result = AnalysisResult.query.filter_by(
                    user_id=current_user.id,
                    project_name=project_name,
                    analysis_type='ai_analysis'
                ).order_by(AnalysisResult.created_at.desc()).first()
                
                if existing_result:
                    app.logger.info(f"⚠️ 并发冲突，使用已存在的记录: {existing_result.id}")
                    result_id = existing_result.id
                else:
                    # 重新抛出异常，因为确实有问题
                    raise db_error

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
            'read timeout' in error_msg.lower() or 'connect timeout' in error_msg.lower() or
            'recv' in error_msg.lower() or 'systemexit' in error_msg.lower() or 'socket' in error_msg.lower()):
            session['analysis_status'] = 'timeout'
            app.logger.info(f"Network/timeout error detected: {error_msg}, immediately generating fallback")

            try:
                fallback_result = generate_fallback_result(form_data)

                # 保存备用方案到数据库（添加重复性检查）
                from datetime import datetime, timedelta
                import uuid

                # 使用数据库锁防止并发重复保存fallback
                project_name = form_data.get('projectName', '')
                
                try:
                    # 查询现有fallback记录
                    existing_fallback = AnalysisResult.query.filter_by(
                        user_id=current_user.id,
                        project_name=project_name,
                        analysis_type='fallback'
                    ).order_by(AnalysisResult.created_at.desc()).first()
                    
                    # 如果2分钟内已有相同的fallback，使用现有的
                    if existing_fallback:
                        time_diff = datetime.utcnow() - existing_fallback.created_at
                        if time_diff < timedelta(minutes=2):
                            app.logger.info(f"⚠️ 检测到2分钟内的重复fallback，使用现有记录: {existing_fallback.id}")
                            fallback_id = existing_fallback.id
                            # 使用现有记录，无需操作数据库
                        else:
                            # 超过2分钟，创建新的
                            fallback_id = str(uuid.uuid4())
                            analysis_result = AnalysisResult()
                            analysis_result.id = fallback_id
                            analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                            analysis_result.user_id = current_user.id  # 关联当前用户
                            analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                            analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                            analysis_result.project_name = project_name
                            analysis_result.project_description = form_data.get('projectDescription', '')
                            analysis_result.team_size = len(form_data.get('keyPersons', []))
                            analysis_result.analysis_type = 'fallback'
                            db.session.add(analysis_result)
                            db.session.commit()
                            app.logger.info(f"✅ 创建新的fallback记录: {fallback_id}")
                    else:
                        # 没有现有fallback，创建新的
                        fallback_id = str(uuid.uuid4())
                        analysis_result = AnalysisResult()
                        analysis_result.id = fallback_id
                        analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
                        analysis_result.user_id = current_user.id  # 关联当前用户
                        analysis_result.form_data = json.dumps(form_data, ensure_ascii=False)
                        analysis_result.result_data = json.dumps(fallback_result, ensure_ascii=False)
                        analysis_result.project_name = project_name
                        analysis_result.project_description = form_data.get('projectDescription', '')
                        analysis_result.team_size = len(form_data.get('keyPersons', []))
                        analysis_result.analysis_type = 'fallback'
                        db.session.add(analysis_result)
                        db.session.commit()
                        app.logger.info(f"✅ 创建首个fallback记录: {fallback_id}")
                        
                except Exception as db_error:
                    app.logger.error(f"❌ Fallback数据库操作失败: {str(db_error)}")
                    db.session.rollback()
                    # 查找是否有其他并发请求已经创建了记录
                    existing_fallback = AnalysisResult.query.filter_by(
                        user_id=current_user.id,
                        project_name=project_name,
                        analysis_type='fallback'
                    ).order_by(AnalysisResult.created_at.desc()).first()
                    
                    if existing_fallback:
                        app.logger.info(f"⚠️ Fallback并发冲突，使用已存在的记录: {existing_fallback.id}")
                        fallback_id = existing_fallback.id
                    else:
                        # 重新抛出异常
                        raise db_error

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
        from flask import session, request

        # 检查URL参数中的result_id
        url_result_id = request.args.get('result_id')
        
        # 详细记录session状态和URL参数
        app.logger.info(f"Results page accessed - Full session: {dict(session)}")
        app.logger.info(f"Results page - Session ID: {request.cookies.get('session', 'No session cookie')}")
        app.logger.info(f"Results page - URL result_id parameter: {url_result_id}")

        # 如果URL中有result_id参数，优先使用它
        if url_result_id:
            app.logger.info(f"Using result_id from URL parameter: {url_result_id}")
            try:
                from models import AnalysisResult
    
                
                # 直接通过URL参数中的ID获取分析记录
                analysis_record = AnalysisResult.query.filter_by(id=url_result_id).first()
                
                if analysis_record:
                    # 权限检查：普通用户只能查看自己的记录，管理员可以查看所有记录
                    if not current_user.is_admin and analysis_record.user_id != current_user.id:
                        flash('您没有权限查看此分析记录', 'error')
                        return redirect(url_for('analysis_history'))
                    
                    # 解析数据并直接显示
                    form_data = json.loads(analysis_record.form_data) if analysis_record.form_data else {}
                    result_data = json.loads(analysis_record.result_data) if analysis_record.result_data else {}
                    
                    app.logger.info(f"Successfully loaded analysis record from URL parameter: {url_result_id}")
                    
                    return render_template('result_pipeline_redesigned.html',
                                         form_data=form_data,
                                         result=result_data,
                                         status='completed',
                                         history_mode=True,
                                         analysis_id=analysis_record.id,
                                         record_info={
                                             'id': analysis_record.id,
                                             'created_at': analysis_record.created_at_display,
                                             'analysis_type': analysis_record.analysis_type_display
                                         })
                else:
                    app.logger.warning(f"Analysis record not found for URL result_id: {url_result_id}")
                    flash('找不到指定的分析记录', 'error')
                    return redirect(url_for('analysis_history'))
                    
            except Exception as e:
                app.logger.error(f"Error loading analysis record from URL parameter {url_result_id}: {str(e)}")
                flash('加载分析记录时发生错误', 'error')
                return redirect(url_for('analysis_history'))

        # 如果没有URL参数，继续使用原有的session逻辑
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
                # 尝试获取analysis_id
                analysis_id = session.get('analysis_result_id', None)
                return render_template('result_pipeline_redesigned.html', 
                                     form_data=form_data, 
                                     result=suggestions,
                                     status='completed',
                                     analysis_id=analysis_id)
            else:
                # 分析标记为完成但没有结果数据，显示错误状态
                app.logger.error("Analysis completed but no result data available")
                return render_template('result_pipeline_redesigned.html',
                                     form_data=form_data,
                                     status='error',
                                     analysis_id=None,
                                     error_message='分析完成但结果数据丢失，请重新分析')

        elif status == 'error' or status == 'timeout':
            # 分析出错或超时，显示错误信息或备用方案
            error_msg = session.get('analysis_error', '分析过程中发生未知错误')
            app.logger.info(f"Analysis {status} - showing fallback page: {error_msg}")

            # 如果是超时，生成基础建议作为备用方案
            if status == 'timeout':
                try:
                    fallback_result = generate_fallback_result(form_data)

                    # 将备用方案也保存到数据库
                    try:
                        import uuid
            
                        from models import AnalysisResult
                        fallback_id = str(uuid.uuid4())

                        analysis_result = AnalysisResult()
                        analysis_result.id = fallback_id
                        analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
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
                                         analysis_id=fallback_id if 'fallback_id' in locals() else None,
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
                fallback_result = generate_fallback_result(form_data)

                # 保存到数据库
                try:
                    import uuid
        
                    from models import AnalysisResult

                    emergency_id = str(uuid.uuid4())
                    analysis_result = AnalysisResult()
                    analysis_result.id = emergency_id
                    analysis_result.sequence_id = AnalysisResult.get_next_sequence_id()
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
                                     analysis_id=emergency_id if 'emergency_id' in locals() else None,
                                     fallback_mode=True)

            except Exception as fallback_error:
                app.logger.error(f"Emergency fallback generation failed: {str(fallback_error)}")
                return render_template('result_pipeline_redesigned.html',
                                     form_data=form_data,
                                     status='error',
                                     analysis_id=None,
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
        app.logger.info(f"Generate route - All form data: {dict(request.form)}")
        
        # 初始化变量
        project_name = ''
        project_description = ''
        key_persons = []
        
        # 检查是否是JSON格式的form_data提交
        form_data_json = request.form.get('form_data', '')
        if form_data_json:
            try:
                parsed_form_data = json.loads(form_data_json)
                app.logger.info(f"🎯 解析JSON格式的form_data成功: {parsed_form_data.get('projectName', '未知项目')}")
                
                # 从解析的JSON中提取数据
                project_name = parsed_form_data.get('projectName', '').strip()
                project_description = parsed_form_data.get('projectDescription', '').strip()
                key_persons = parsed_form_data.get('keyPersons', [])
                
                app.logger.info(f"📋 提取的数据 - 项目名: {project_name}, 人员数: {len(key_persons)}")
            except json.JSONDecodeError as e:
                app.logger.error(f"❌ JSON form_data解析失败: {e}")
                # 继续使用普通表单解析
        
        # 如果JSON解析失败或没有JSON数据，使用传统表单解析
        if not project_name or not project_description:
            # Get form data - 修复字段名匹配问题
            if not project_name:
                project_name = request.form.get('projectName', '').strip()
                if not project_name:
                    project_name = request.form.get('project_name', '').strip()
            
            if not project_description:
                project_description = request.form.get('projectDescription', '').strip()
                if not project_description:
                    project_description = request.form.get('project_description', '').strip()

        # Validate required fields
        if not project_name or not project_description:
            app.logger.error(f"❌ 验证失败 - 项目名: '{project_name}', 描述: '{project_description[:50]}...'")
            flash('项目名称和背景描述不能为空', 'error')
            return redirect(url_for('index'))
        
        # Process key persons data - 支持JSON格式输入
        if 'key_persons' not in locals():
            key_persons = []
            
            # 尝试从JSON字段获取（前端提交的格式）
            key_persons_json = request.form.get('keyPersons', '')
            if key_persons_json:
                try:
                    key_persons = json.loads(key_persons_json)
                    app.logger.info(f"Parsed key persons from JSON: {len(key_persons)} persons")
                except json.JSONDecodeError as e:
                    app.logger.error(f"Failed to parse keyPersons JSON: {e}")
                    key_persons = []
        
        # 如果JSON解析失败，尝试传统表单字段
        if not key_persons:
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
        
        # 保存表单数据到FormSubmission表（添加重复性检查）
        try:
            from models import FormSubmission
            from datetime import datetime
            
            # 检查是否已存在相同的表单提交（防止重复提交）
            existing_submission = FormSubmission.query.filter_by(
                user_id=current_user.id,
                project_name=form_data.get('projectName', ''),
                status='submitted'
            ).order_by(FormSubmission.created_at.desc()).first()
            
            # 如果5分钟内有相同项目的提交，使用现有的而不是创建新的
            if existing_submission:
                from datetime import datetime, timedelta
                time_diff = datetime.utcnow() - existing_submission.created_at
                if time_diff < timedelta(minutes=5):
                    app.logger.info(f"⚠️ 检测到5分钟内的重复提交，使用现有记录: {existing_submission.id}")
                    submission_id = existing_submission.id
                else:
                    # 超过5分钟，创建新的提交
                    submission_id = str(uuid.uuid4())
                    form_submission = FormSubmission()
                    form_submission.id = submission_id
                    form_submission.user_id = current_user.id
                    form_submission.project_name = form_data.get('projectName', '')
                    form_submission.project_description = form_data.get('projectDescription', '')
                    form_submission.key_persons_data = json.dumps(form_data.get('keyPersons', []), ensure_ascii=False)
                    form_submission.form_data_complete = json.dumps(form_data, ensure_ascii=False)
                    form_submission.status = 'submitted'
                    form_submission.created_at = datetime.utcnow()
                    form_submission.updated_at = datetime.utcnow()
                    
                    db.session.add(form_submission)
                    db.session.commit()
            else:
                # 没有现有提交，创建新的
                submission_id = str(uuid.uuid4())
                form_submission = FormSubmission()
                form_submission.id = submission_id
                form_submission.user_id = current_user.id
                form_submission.project_name = form_data.get('projectName', '')
                form_submission.project_description = form_data.get('projectDescription', '')
                form_submission.key_persons_data = json.dumps(form_data.get('keyPersons', []), ensure_ascii=False)
                form_submission.form_data_complete = json.dumps(form_data, ensure_ascii=False)
                form_submission.status = 'submitted'
                form_submission.created_at = datetime.utcnow()
                form_submission.updated_at = datetime.utcnow()
                
                db.session.add(form_submission)
                db.session.commit()
            
            # Session中保存submission ID和项目名称
            session['form_submission_id'] = submission_id
            session['analysis_project_name'] = project_name
            app.logger.info(f"✅ 表单数据保存成功，ID: {submission_id}")
            
        except Exception as e:
            app.logger.error(f"❌ FormSubmission表存储失败: {str(e)}")
            # 回滚事务并重新抛出异常
            db.session.rollback()
            raise

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
        app.logger.info(f"Received form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        app.logger.info(f"Session data stored successfully - Temp ID: {session.get('analysis_form_id')}, Project: {session.get('analysis_project_name')}")
        
        # 验证session存储是否成功
        verification_data = get_form_data_from_db(session)
        if verification_data:
            app.logger.info("✅ Session数据存储验证成功")
        else:
            app.logger.error("❌ Session数据存储验证失败，数据未能正确保存")

        # 跳转到新的Matrix风格思考页面，同时启动分析
        return redirect(url_for('thinking_process'))

    except Exception as e:
        app.logger.error(f"Error processing form: {str(e)}")
        flash('处理表单时发生错误，请重试', 'error')
        return redirect(url_for('index'))

def generate_ai_suggestions(form_data, session=None):
    """Generate AI suggestions using OpenAI API with enhanced error handling"""
    import time
    import threading
    import concurrent.futures

    try:

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
        app.logger.info("=== 开始调用OpenAI API ===")
        # 调用AI生成服务，添加SSL错误处理
        try:
            app.logger.info("调用 angela_ai.generate_income_paths() 开始...")
            ai_result = angela_ai.generate_income_paths(converted_data, db.session)
            app.logger.info(f"=== OpenAI API调用成功，返回数据类型: {type(ai_result)}, 数据长度: {len(str(ai_result)) if ai_result else 0} ===")
            
            # 验证返回结果的有效性
            if not ai_result or not isinstance(ai_result, dict):
                app.logger.error(f"OpenAI API返回了无效数据: {ai_result}")
                raise ValueError(f"OpenAI API返回无效数据: {type(ai_result)}")
            
            # 检查是否是真正的AI生成结果还是内部备用方案
            if ai_result.get('overview', {}).get('situation', '').startswith('设计者作为统筹方'):
                app.logger.warning("⚠️ 检测到可能是内部备用方案，而非真实OpenAI生成内容")
            else:
                app.logger.info("✅ 确认是真实OpenAI生成的内容")
            
        except Exception as network_error:
            # 检查是否是SSL/网络相关错误
            error_str = str(network_error).lower()
            app.logger.error(f"💥 AI调用异常详细信息: {str(network_error)}")
            app.logger.error(f"💥 异常类型: {type(network_error).__name__}")
            import traceback
            app.logger.error(f"💥 完整调用堆栈: {traceback.format_exc()}")
            # 取消超时
            signal.alarm(0)
            
            if any(keyword in error_str for keyword in ['ssl', 'timeout', 'connection', 'network', 'recv', 'read', 'httpx', 'httpcore', 'systemexit', 'socket']):
                # 网络/SSL/超时错误
                app.logger.error(f"🌐 网络相关错误，使用备用方案: {str(network_error)}")
                # 更新session状态为timeout
                if session:
                    session['analysis_status'] = 'timeout'
                    session['analysis_error'] = f'网络连接问题: {str(network_error)[:100]}'  # 限制错误信息长度
                    save_session_in_ajax()
                # 返回网络错误的备用方案
                return generate_fallback_result(form_data, "网络连接问题，为您提供基础建议")
            else:
                # 其他类型的错误
                app.logger.error(f"❌ 非网络错误，使用备用方案: {str(network_error)}")
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

        app.logger.info(f"AI analysis completed in {elapsed_time:.2f} seconds")
        app.logger.info(f"AI generated result: {json.dumps(ai_result, ensure_ascii=False)}")

        return ai_result

    except TimeoutError as e:
        app.logger.error(f"AI analysis timeout: {str(e)}")
        # 设置超时状态到session，让前端显示
        from flask import session
        session['analysis_status'] = 'timeout'
        session['analysis_error'] = '分析超时，为您提供基础建议'
        return generate_fallback_result(form_data, "分析超时，为您提供基础建议")

    except Exception as e:
        app.logger.error(f"Error generating AI suggestions: {str(e)}")
        app.logger.error(f"Error type: {type(e).__name__}")
        import traceback
        app.logger.error(f"Traceback: {traceback.format_exc()}")
        # 设置错误状态到session
        from flask import session
        session['analysis_status'] = 'error'
        session['analysis_error'] = f'分析遇到问题: {str(e)}'
        return generate_fallback_result(form_data, f"分析遇到问题，为您提供基础建议")

def generate_fallback_result(form_data, reason="AI服务暂时不可用"):
    """生成备用分析结果 - 统一的【默认】fallback方案生成函数
    当AI分析服务不可用时，提供基础的非劳务收入管道建议
    """
    project_name = form_data.get('projectName', form_data.get('project_name', '您的项目'))
    key_persons = form_data.get('keyPersons', form_data.get('key_persons', []))

    # 构建参与方结构 - 包含设计者和所有关键人物
    parties_structure = [
        {
            "party": "设计者（您）",
            "role_type": "统筹方",
            "resources": [
                "【默认】整合协调权",
                "【默认】规则制定权", 
                "【默认】结算管理权"
            ],
            "role_value": "【默认】作为统筹方负责整合各方资源，制定合作规则，管理收益分配",
            "make_them_happy": "【默认】通过统筹位置获得稳定的非劳务收入分成，确保不被绕过"
        }
    ]

    # 添加用户提供的关键人物
    for i, person in enumerate(key_persons):
        party_name = person.get("name", f"关键人物{i+1}")
        parties_structure.append({
            "party": party_name,
            "role_type": "交付方",  # 默认角色类型
            "resources": person.get("resources", ["待明确的专业资源"]),
            "role_value": f"【默认】{party_name}在合作框架中提供专业支持和资源对接",
            "make_them_happy": f"【默认】通过合作获得相应的收益分成或价值交换"
        })

    # 如果关键人物不足，添加待补齐角色
    suggested_roles = []
    gaps = []
    
    if len(key_persons) < 2:
        gaps.extend([
            "【默认】缺少足够的核心合作伙伴",
            "【默认】需要补充市场推广角色",
            "【默认】需要补充资金管理角色"
        ])
        suggested_roles.extend([
            {
                "role": "【待补齐】市场推广专员",
                "role_type": "交付方",
                "why": "【默认】需要专业的市场推广和客户获取能力来扩大业务规模",
                "where_to_find": "行业社群、营销公司、商业协会",
                "outreach_script": "您好，我们有个资源整合项目，需要市场推广方面的专业支持，希望能与您探讨合作可能。"
            },
            {
                "role": "【待补齐】财务管理方",
                "role_type": "资金方",
                "why": "【默认】需要专业的财务管理和风险控制能力来确保项目稳健发展",
                "where_to_find": "会计师事务所、金融机构、投资公司",
                "outreach_script": "您好，我们在设计一个多方合作的收益模式，希望获得财务管理方面的专业建议。"
            }
        ])
        
        # 添加待补齐角色到参与方结构
        parties_structure.extend([
            {
                "party": "【待补齐】市场推广专员",
                "role_type": "交付方",
                "resources": ["【默认】市场推广渠道", "【默认】客户获取能力"],
                "role_value": "【默认】负责市场开拓和客户获取，扩大业务规模",
                "make_them_happy": "【默认】通过业绩提成获得收益激励"
            },
            {
                "party": "【待补齐】财务管理方", 
                "role_type": "资金方",
                "resources": ["【默认】资金管理能力", "【默认】风险控制经验"],
                "role_value": "【默认】提供财务管理和风险控制支持",
                "make_them_happy": "【默认】通过管理费或投资收益获得回报"
            }
        ])

    # 生成符合新assistant_prompt格式的【默认】备用结果
    return {
        "overview": {
            "situation": f"【默认方案】由于{reason}，基于您的项目「{project_name}」和现有{len(key_persons)}位关键人物，设计者处于统筹位置，通过整合各方资源形成非劳务收入管道。当前局势下需要明确各方动机匹配度并补齐关键角色。",
            "core_insight": "【默认】通过设计者的统筹位置，将各方资源串联形成闭环，设计者获得居间撮合费用和团队协作分成，避免纯劳务付出。",
            "gaps": gaps,
            "suggested_roles_to_hunt": suggested_roles
        },
        "pipelines": [
            {
                "id": "pipeline_1",
                "name": "【默认】资源整合居间模式",
                "income_mechanism": {
                    "type": "居间收益",
                    "trigger": "【默认】每次成功撮合资源对接时产生居间费",
                    "settlement": "【默认】按对接成功单数结算，每单收取5-10%居间费"
                },
                "parties_structure": parties_structure,
                "framework_logic": {
                    "resource_chain": "【默认】设计者统筹 → 梳理各方资源 → 建立对接规则 → 撮合资源交换 → 收取居间费用 → 持续循环",
                    "motivation_match": "【默认】各方通过资源互换获得所需价值，设计者通过统筹获得居间收益，形成多赢局面",
                    "designer_position": "【默认】设计者掌控对接规则和结算口径，所有交易必须通过设计者确认，防止被绕过",
                    "designer_income": "【默认】居间收益类型，通过撮合服务获得非劳务收入"
                },
                "mvp": "【默认】组织一次小型资源对接会，验证撮合模式可行性，成功撮合2-3个资源对接即为有效验证。",
                "weak_link": "【默认】各方参与积极性可能不均，需要明确激励机制确保持续参与",
                "revenue_trigger": "【默认】资源对接成功时的居间费收入（居间收益类型）",
                "risks_and_planB": [
                    {
                        "risk": "【默认】参与方积极性不足，资源对接效率低",
                        "mitigation": "【默认】建立激励机制，成功对接方获得优先推荐权，提升参与动力"
                    },
                    {
                        "risk": "【默认】被各方绕过，失去统筹地位",
                        "mitigation": "【默认】掌控关键资源信息和结算环节，建立制度化依赖"
                    }
                ],
                "first_step": "【默认】召集所有关键人物开一次资源盘点会，明确各方可提供和需要的资源，建立初步对接规则。",
                "labor_load_estimate": {
                    "hours_per_week": "【默认】3-5小时",
                    "level": "轻度(<5小时)",
                    "alternative": "【默认】建立标准化对接流程和在线撮合平台，减少人工协调工作量"
                }
            },
            {
                "id": "pipeline_2",
                "name": "【默认】联合服务团队模式", 
                "income_mechanism": {
                    "type": "团队收益",
                    "trigger": "【默认】对外提供联合服务时的团队分成收入",
                    "settlement": "【默认】按项目收入分成，设计者获得15-25%统筹分成"
                },
                "parties_structure": parties_structure,
                "framework_logic": {
                    "resource_chain": "【默认】设计者统筹 → 整合各方专业能力 → 包装联合服务 → 对外承接项目 → 按贡献分成 → 持续扩展",
                    "motivation_match": "【默认】各方发挥专业优势获得项目分成，设计者通过统筹获得固定比例收益",
                    "designer_position": "【默认】设计者负责项目获取和整体协调，掌控客户关系和分成规则",
                    "designer_income": "【默认】团队收益类型，通过统筹团队服务获得分成"
                },
                "mvp": "【默认】设计一个简化服务包，寻找1-2个试点客户，验证团队协作和分成模式的可行性。",
                "weak_link": "【默认】服务质量标准化困难，需要建立统一的交付标准",
                "revenue_trigger": "【默认】联合服务项目收入的团队分成（团队收益类型）",
                "risks_and_planB": [
                    {
                        "risk": "【默认】服务质量不一致，影响客户满意度",
                        "mitigation": "【默认】建立标准作业流程和质量检查机制，确保服务标准化"
                    },
                    {
                        "risk": "【默认】团队成员直接接单，绕过设计者",
                        "mitigation": "【默认】设计者掌控客户资源和品牌，建立长期合作协议"
                    }
                ],
                "first_step": "【默认】调研市场需求，设计标准化服务包，明确各方分工和分成比例。",
                "labor_load_estimate": {
                    "hours_per_week": "【默认】5-8小时", 
                    "level": "中度(5-10小时)",
                    "alternative": "【默认】建立项目管理模板和自动化流程，减少协调成本"
                }
            }
        ]
    }

# Knowledge Base Management Routes
@app.route('/history')
@login_required
def analysis_history():
    """历史分析记录页面"""
    try:
        from models import AnalysisResult

        # 根据用户身份显示不同的记录，使用 joinedload 预加载用户信息避免 N+1 查询
        from sqlalchemy.orm import joinedload

        if current_user.is_admin:
            # 管理员可以看到所有分析记录
            analysis_records = AnalysisResult.query.options(
                joinedload(AnalysisResult.user)
            ).order_by(AnalysisResult.created_at.desc()).all()
            app.logger.info(f"Admin user viewing {len(analysis_records)} analysis records")
        else:
            # 普通用户只能看到自己的分析记录
            analysis_records = AnalysisResult.query.options(
                joinedload(AnalysisResult.user)
            ).filter_by(user_id=current_user.id).order_by(AnalysisResult.created_at.desc()).all()
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
                             analysis_id=record.id,
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
                'current_user_id': current_user.id,
                # AI分析额度信息
                'ai_quota': user.ai_quota,
                'used_quota': user.used_quota,
                'remaining_quota': user.remaining_quota,
                'quota_display': user.quota_display,
                'quota_usage_percentage': user.quota_usage_percentage
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
        app.logger.error(f"获取用户数据失败: {e}")
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
            # 根据用户角色设置默认AI分析额度
            user.ai_quota = User.get_default_quota_for_role(is_admin)
            user.used_quota = 0

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
        # AI分析额度调整
        ai_quota = request.form.get('ai_quota', '')
        used_quota = request.form.get('used_quota', '')
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
            
            # 处理AI分析额度调整
            if ai_quota.isdigit():
                new_ai_quota = int(ai_quota)
                if 0 <= new_ai_quota <= 100000:
                    user.ai_quota = new_ai_quota
                    app.logger.info(f"管理员调整用户 {user.id} 的AI总额度为: {new_ai_quota}")
                else:
                    flash('AI分析总额度必须在0-100000范围内', 'error')
                    return render_template('admin/edit_user.html', user=user)
            
            if used_quota.isdigit():
                new_used_quota = int(used_quota)
                if 0 <= new_used_quota <= 100000:
                    user.used_quota = new_used_quota
                    app.logger.info(f"管理员调整用户 {user.id} 的已使用额度为: {new_used_quota}")
                else:
                    flash('已使用额度必须在0-100000范围内', 'error')
                    return render_template('admin/edit_user.html', user=user)
            
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
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    # 防止删除当前登录用户
    if user.id == current_user.id:
        error_msg = '不能删除当前登录的用户'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')
        return redirect(url_for('admin_dashboard') + '?tab=users')

    try:
        username = user.name
        db.session.delete(user)
        db.session.commit()

        success_msg = f'用户 "{username}" 已删除'
        if is_ajax:
            return jsonify({'success': True, 'message': success_msg})
        flash(success_msg, 'success')

    except Exception as e:
        error_msg = f'删除用户失败: {str(e)}'
        if is_ajax:
            return jsonify({'success': False, 'message': error_msg})
        flash(error_msg, 'error')

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


@app.route('/profile')
@login_required  
def user_profile():
    """普通用户的个人信息页面"""
    try:
        # 检查并修复用户配额数据
        if current_user.ai_quota is None:
            current_user.ai_quota = User.get_default_quota_for_role(current_user.is_admin)
            app.logger.warning(f"用户 {current_user.phone} 的ai_quota为空，已设置默认值: {current_user.ai_quota}")
        
        if current_user.used_quota is None:
            current_user.used_quota = 0
            app.logger.warning(f"用户 {current_user.phone} 的used_quota为空，已设置为0")
        
        # 提交修复
        db.session.commit()
        
        return render_template('user_profile_apple.html')
    except Exception as e:
        app.logger.error(f"Profile页面错误 - 用户: {current_user.phone if current_user else 'Unknown'}, 错误: {str(e)}")
        flash('个人信息页面加载失败，请稍后重试', 'error')
        return redirect(url_for('index'))

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


@app.route('/update_income_mechanism', methods=['POST'])
@login_required
def update_income_mechanism():
    """更新收入类型配置"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        pipeline_id = data.get('pipeline_id')
        income_mechanism = data.get('income_mechanism')
        
        # 验证输入
        if not pipeline_id or not income_mechanism:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        if not all(key in income_mechanism for key in ['type', 'trigger', 'settlement']):
            return jsonify({'success': False, 'error': '收入机制数据不完整'}), 400
        
        # 从session或URL获取当前的分析记录ID
        analysis_id = None
        
        # 尝试从session获取
        if 'analysis_result_id' in session:
            analysis_id = session['analysis_result_id']
        
        # 如果session中没有，尝试从request args获取
        if not analysis_id:
            analysis_id = request.args.get('result_id')
        
        # 如果还是没有，从referer URL中解析
        if not analysis_id:
            referer = request.headers.get('Referer', '')
            if '/history/' in referer:
                analysis_id = referer.split('/history/')[-1].split('?')[0]
            elif 'result_id=' in referer:
                analysis_id = referer.split('result_id=')[-1].split('&')[0]
        
        if not analysis_id:
            return jsonify({'success': False, 'error': '无法确定当前分析记录'}), 400
        
        app.logger.info(f"更新收入机制 - 分析ID: {analysis_id}, 管道ID: {pipeline_id}")
        
        # 查找分析记录
        from models import AnalysisResult
        analysis_record = AnalysisResult.query.filter_by(id=analysis_id).first()
        
        if not analysis_record:
            return jsonify({'success': False, 'error': '找不到分析记录'}), 404
        
        # 权限检查
        if not current_user.is_admin and analysis_record.user_id != current_user.id:
            return jsonify({'success': False, 'error': '无权限修改此记录'}), 403
        
        # 解析现有的result_data
        try:
            result_data = json.loads(analysis_record.result_data) if analysis_record.result_data else {}
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '分析数据格式错误'}), 500
        
        # 更新收入机制
        if 'pipelines' in result_data:
            for i, pipeline in enumerate(result_data['pipelines']):
                # 匹配管道ID（支持多种ID格式）
                current_pipeline_id = pipeline.get('id', f'pipeline_{i+1}')
                if pipeline_id.endswith(str(i+1)) or current_pipeline_id == pipeline_id or pipeline_id == f'pipeline_{i+1}':
                    if 'income_mechanism' not in pipeline:
                        pipeline['income_mechanism'] = {}
                    
                    # 更新收入机制数据
                    pipeline['income_mechanism']['type'] = income_mechanism['type']
                    pipeline['income_mechanism']['trigger'] = income_mechanism['trigger']
                    pipeline['income_mechanism']['settlement'] = income_mechanism['settlement']
                    
                    app.logger.info(f"已更新管道 {i+1} 的收入机制")
                    break
            else:
                return jsonify({'success': False, 'error': '找不到指定的管道'}), 404
        else:
            return jsonify({'success': False, 'error': '分析结果中没有管道数据'}), 404
        
        # 保存更新后的数据
        analysis_record.result_data = json.dumps(result_data, ensure_ascii=False)
        analysis_record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        app.logger.info(f"收入机制更新成功 - 用户: {current_user.phone}, 分析ID: {analysis_id}")
        
        return jsonify({
            'success': True,
            'message': '收入类型更新成功',
            'updated_mechanism': income_mechanism
        })
        
    except Exception as e:
        app.logger.error(f"更新收入机制失败: {str(e)}")
        app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/update_core_insight', methods=['POST'])
@login_required
def update_core_insight():
    """更新核心洞察内容"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        analysis_id = data.get('analysis_id')
        content = data.get('content')
        
        # 验证输入
        if not analysis_id or not content:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        if len(content.strip()) == 0:
            return jsonify({'success': False, 'error': '核心洞察内容不能为空'}), 400
        
        app.logger.info(f"更新核心洞察 - 分析ID: {analysis_id}")
        
        # 查找分析记录
        from models import AnalysisResult
        analysis_record = AnalysisResult.query.filter_by(id=analysis_id).first()
        
        if not analysis_record:
            return jsonify({'success': False, 'error': '找不到分析记录'}), 404
        
        # 权限检查
        if not current_user.is_admin and analysis_record.user_id != current_user.id:
            return jsonify({'success': False, 'error': '无权限修改此记录'}), 403
        
        # 解析现有的result_data
        try:
            result_data = json.loads(analysis_record.result_data) if analysis_record.result_data else {}
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '分析数据格式错误'}), 500
        
        # 更新核心洞察
        if 'overview' not in result_data:
            result_data['overview'] = {}
        
        result_data['overview']['core_insight'] = content.strip()
        
        app.logger.info(f"已更新核心洞察内容")
        
        # 保存更新后的数据
        analysis_record.result_data = json.dumps(result_data, ensure_ascii=False)
        analysis_record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        app.logger.info(f"核心洞察更新成功 - 用户: {current_user.phone}, 分析ID: {analysis_id}")
        
        return jsonify({
            'success': True,
            'message': '核心洞察更新成功',
            'updated_content': content.strip()
        })
        
    except Exception as e:
        app.logger.error(f"更新核心洞察失败: {str(e)}")
        app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/update_current_situation', methods=['POST'])
@login_required
def update_current_situation():
    """更新当前现状内容"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        analysis_id = data.get('analysis_id')
        content = data.get('content')
        
        # 验证输入
        if not analysis_id or not content:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        if len(content.strip()) == 0:
            return jsonify({'success': False, 'error': '当前现状内容不能为空'}), 400
        
        app.logger.info(f"更新当前现状 - 分析ID: {analysis_id}")
        
        # 查找分析记录
        from models import AnalysisResult
        analysis_record = AnalysisResult.query.filter_by(id=analysis_id).first()
        
        if not analysis_record:
            return jsonify({'success': False, 'error': '找不到分析记录'}), 404
        
        # 权限检查
        if not current_user.is_admin and analysis_record.user_id != current_user.id:
            return jsonify({'success': False, 'error': '无权限修改此记录'}), 403
        
        # 解析现有的result_data
        try:
            result_data = json.loads(analysis_record.result_data) if analysis_record.result_data else {}
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '分析数据格式错误'}), 500
        
        # 更新当前现状
        if 'overview' not in result_data:
            result_data['overview'] = {}
        
        result_data['overview']['situation'] = content.strip()
        
        app.logger.info(f"已更新当前现状内容")
        
        # 保存更新后的数据
        analysis_record.result_data = json.dumps(result_data, ensure_ascii=False)
        analysis_record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        app.logger.info(f"当前现状更新成功 - 用户: {current_user.phone}, 分析ID: {analysis_id}")
        
        return jsonify({
            'success': True,
            'message': '当前现状更新成功',
            'updated_content': content.strip()
        })
        
    except Exception as e:
        app.logger.error(f"更新当前现状失败: {str(e)}")
        app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


@app.route('/update_core_resources', methods=['POST'])
@login_required
def update_core_resources():
    """更新核心资源内容"""
    try:
        # 获取请求数据
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': '无效的请求数据'}), 400
        
        analysis_id = data.get('analysis_id')
        content = data.get('content')
        
        # 验证输入
        if not analysis_id or not content:
            return jsonify({'success': False, 'error': '缺少必要参数'}), 400
        
        if len(content.strip()) == 0:
            return jsonify({'success': False, 'error': '核心资源内容不能为空'}), 400
        
        app.logger.info(f"更新核心资源 - 分析ID: {analysis_id}")
        
        # 查找分析记录
        from models import AnalysisResult
        analysis_record = AnalysisResult.query.filter_by(id=analysis_id).first()
        
        if not analysis_record:
            return jsonify({'success': False, 'error': '找不到分析记录'}), 404
        
        # 权限检查
        if not current_user.is_admin and analysis_record.user_id != current_user.id:
            return jsonify({'success': False, 'error': '无权限修改此记录'}), 403
        
        # 解析现有的result_data
        try:
            result_data = json.loads(analysis_record.result_data) if analysis_record.result_data else {}
        except json.JSONDecodeError:
            return jsonify({'success': False, 'error': '分析数据格式错误'}), 500
        
        # 解析新的资源列表
        resources_list = [r.strip() for r in content.split(',') if r.strip()]
        
        # 更新核心资源（在统筹方的resources字段中）
        if 'pipelines' in result_data and result_data['pipelines']:
            for pipeline in result_data['pipelines']:
                if 'parties_structure' in pipeline:
                    for party in pipeline['parties_structure']:
                        if party.get('role_type') == '统筹方':
                            party['resources'] = resources_list
                            app.logger.info(f"已更新统筹方核心资源: {resources_list}")
                            break
        
        # 保存更新后的数据
        analysis_record.result_data = json.dumps(result_data, ensure_ascii=False)
        analysis_record.updated_at = datetime.utcnow()
        
        db.session.commit()
        
        app.logger.info(f"核心资源更新成功 - 用户: {current_user.phone}, 分析ID: {analysis_id}")
        
        return jsonify({
            'success': True,
            'message': '核心资源更新成功',
            'updated_resources': resources_list
        })
        
    except Exception as e:
        app.logger.error(f"更新核心资源失败: {str(e)}")
        app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'服务器错误: {str(e)}'}), 500


# ==================== 用户数据分析功能 ====================

import csv
from io import StringIO
from sqlalchemy import func
from datetime import timedelta


# 注意：用户数据分析功能已集成到 /admin/dashboard 页面中
# 以下独立页面路由已注释，如需使用独立页面可取消注释
#
# @app.route('/admin/users-analytics')
# @login_required
# @admin_required
# def users_analytics():
#     """用户数据分析页面（已集成到dashboard）"""
#     return render_template('admin_users_analytics.html')


@app.route('/admin/api/users/analytics/stats')
@login_required
@admin_required
def api_users_analytics_stats():
    """获取用户统计数据"""
    try:
        # 计算30天前的日期
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # 高价值用户：分析次数 > 3 且 30天内有登录
        # 使用子查询统计每个用户的分析次数
        user_analysis_count = db.session.query(
            AnalysisResult.user_id,
            func.count(AnalysisResult.id).label('analysis_count')
        ).group_by(AnalysisResult.user_id).subquery()

        high_value_query = db.session.query(User).join(
            user_analysis_count,
            User.id == user_analysis_count.c.user_id
        ).filter(
            User.last_login >= thirty_days_ago,
            user_analysis_count.c.analysis_count > 3
        )

        high_value_users = high_value_query.count()

        # 活跃用户：7天内有登录的用户
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = User.query.filter(
            User.last_login >= seven_days_ago
        ).count()

        # 已耗尽额度：剩余额度 <= 0 的用户
        exhausted_users = User.query.filter(
            (User.ai_quota - User.used_quota) <= 0
        ).count()

        stats = {
            'high_value_users': high_value_users,
            'active_users': active_users,
            'exhausted_users': exhausted_users
        }

        return jsonify(stats)

    except Exception as e:
        app.logger.error(f"获取统计数据失败: {str(e)}")
        return jsonify({'error': '获取统计数据失败'}), 500


@app.route('/admin/api/users/analytics/list')
@login_required
@admin_required
def api_users_analytics_list():
    """获取用户列表（支持分页、筛选、排序、搜索）"""
    try:
        # 获取参数
        page = request.args.get('page', 1, type=int)
        per_page = 20
        filter_type = request.args.get('filter', 'all')  # all/high_value/active/silent/exhausted
        search = request.args.get('search', '').strip()
        sort_by = request.args.get('sort', 'analysis_count')  # analysis_count/last_login
        order = request.args.get('order', 'desc')  # asc/desc

        # 计算时间阈值
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # 构建基础查询 - 统计每个用户的分析次数
        user_analysis_count = db.session.query(
            AnalysisResult.user_id,
            func.count(AnalysisResult.id).label('analysis_count')
        ).group_by(AnalysisResult.user_id).subquery()

        # 主查询
        query = db.session.query(
            User,
            func.coalesce(user_analysis_count.c.analysis_count, 0).label('analysis_count')
        ).outerjoin(
            user_analysis_count,
            User.id == user_analysis_count.c.user_id
        )

        # 应用筛选条件
        if filter_type == 'high_value':
            # 高价值用户：分析次数 > 3 且 30天内有登录
            query = query.filter(
                func.coalesce(user_analysis_count.c.analysis_count, 0) > 3,
                User.last_login >= thirty_days_ago
            )
        elif filter_type == 'active':
            # 活跃用户：7天内有登录
            query = query.filter(User.last_login >= seven_days_ago)
        elif filter_type == 'silent':
            # 沉默用户：30天未登录
            query = query.filter(User.last_login < thirty_days_ago)
        elif filter_type == 'exhausted':
            # 已耗尽额度：剩余额度 = 0
            query = query.filter(
                (User.ai_quota - User.used_quota) <= 0
            )

        # 应用搜索条件
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    User.phone.like(search_pattern),
                    User.name.like(search_pattern)
                )
            )

        # 应用排序
        if sort_by == 'analysis_count':
            order_column = func.coalesce(user_analysis_count.c.analysis_count, 0)
        elif sort_by == 'last_login':
            order_column = User.last_login
        else:
            order_column = User.id

        if order == 'asc':
            query = query.order_by(order_column.asc())
        else:
            query = query.order_by(order_column.desc())

        # 分页查询
        total = query.count()
        users_data = query.offset((page - 1) * per_page).limit(per_page).all()

        # 构建返回数据
        users_list = []
        for user, analysis_count in users_data:
            # 计算用户状态标签
            badges = []

            # 高价值用户
            if analysis_count > 3 and user.last_login and user.last_login >= thirty_days_ago:
                badges.append('高价值')

            # 活跃用户
            if user.last_login and user.last_login >= seven_days_ago:
                badges.append('活跃')

            # 沉默用户
            if not user.last_login or user.last_login < thirty_days_ago:
                badges.append('沉默')

            # 已耗尽额度
            if user.remaining_quota <= 0:
                badges.append('已耗尽')

            # 格式化最后登录时间（相对时间）
            last_login_display = '从未登录'
            if user.last_login:
                time_diff = datetime.utcnow() - user.last_login
                hours = time_diff.total_seconds() / 3600

                if hours < 1:
                    last_login_display = '刚刚'
                elif hours < 24:
                    last_login_display = f'{int(hours)}小时前'
                elif hours < 24 * 2:
                    last_login_display = '昨天'
                elif hours < 24 * 7:
                    days = int(hours / 24)
                    last_login_display = f'{days}天前'
                else:
                    last_login_display = user.last_login_display.split(' ')[0]  # 只显示日期部分

            users_list.append({
                'id': user.id,
                'phone': user.phone,
                'name': user.name or '未设置',
                'analysis_count': analysis_count,
                'last_login': last_login_display,
                'badges': badges,
                'remaining_quota': user.remaining_quota,
                'ai_quota': user.ai_quota,
                'used_quota': user.used_quota
            })

        return jsonify({
            'users': users_list,
            'total': total,
            'page': page,
            'pages': (total + per_page - 1) // per_page,
            'per_page': per_page
        })

    except Exception as e:
        app.logger.error(f"获取用户列表失败: {str(e)}")
        app.logger.error(f"错误详情: {traceback.format_exc()}")
        return jsonify({'error': '获取用户列表失败'}), 500


@app.route('/admin/api/users/<int:user_id>/detail')
@login_required
@admin_required
def api_user_detail(user_id):
    """获取用户详情"""
    try:
        user = User.query.get_or_404(user_id)

        # 获取分析次数
        analysis_count = AnalysisResult.query.filter_by(user_id=user_id).count()

        # 获取最近10条分析记录
        recent_activities = AnalysisResult.query.filter_by(user_id=user_id)\
            .order_by(AnalysisResult.created_at.desc())\
            .limit(10).all()

        activities_data = []
        for activity in recent_activities:
            # 直接使用AnalysisResult的project_name字段
            activities_data.append({
                'id': activity.id,
                'project_name': activity.project_name or '未命名项目',
                'created_at': activity.created_at_display if hasattr(activity, 'created_at_display') else activity.created_at.strftime('%Y-%m-%d %H:%M') if activity.created_at else '未知'
            })

        # 计算使用率
        usage_percentage = user.quota_usage_percentage

        return jsonify({
            'user': {
                'id': user.id,
                'name': user.name or '未设置',
                'phone': user.phone,
                'created_at': user.created_at_display,
                'last_login': user.last_login_display,
                'is_admin': user.is_admin,
                'active': user.active
            },
            'analysis_count': analysis_count,
            'remaining_quota': user.remaining_quota,
            'total_quota': user.ai_quota,
            'used_quota': user.used_quota,
            'usage_percentage': usage_percentage,
            'recent_activities': activities_data
        })

    except Exception as e:
        app.logger.error(f"获取用户详情失败: {str(e)}")
        return jsonify({'error': '获取用户详情失败'}), 500


@app.route('/admin/api/users/export')
@login_required
@admin_required
def export_users_data():
    """导出用户数据为CSV"""
    try:
        # 获取筛选参数
        filter_type = request.args.get('filter', 'all')
        search = request.args.get('search', '').strip()

        # 计算时间阈值
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)

        # 构建查询
        user_analysis_count = db.session.query(
            AnalysisResult.user_id,
            func.count(AnalysisResult.id).label('analysis_count')
        ).group_by(AnalysisResult.user_id).subquery()

        query = db.session.query(
            User,
            func.coalesce(user_analysis_count.c.analysis_count, 0).label('analysis_count')
        ).outerjoin(
            user_analysis_count,
            User.id == user_analysis_count.c.user_id
        )

        # 应用筛选
        if filter_type == 'high_value':
            query = query.filter(
                func.coalesce(user_analysis_count.c.analysis_count, 0) > 3,
                User.last_login >= thirty_days_ago
            )
        elif filter_type == 'active':
            query = query.filter(User.last_login >= seven_days_ago)
        elif filter_type == 'silent':
            query = query.filter(User.last_login < thirty_days_ago)
        elif filter_type == 'exhausted':
            query = query.filter((User.ai_quota - User.used_quota) <= 0)

        # 应用搜索
        if search:
            search_pattern = f'%{search}%'
            query = query.filter(
                db.or_(
                    User.phone.like(search_pattern),
                    User.name.like(search_pattern)
                )
            )

        # 获取所有数据（不分页）
        users_data = query.all()

        # 创建CSV文件
        output = StringIO()
        writer = csv.writer(output)

        # 写入表头（UTF-8 BOM for Excel）
        output.write('\ufeff')
        writer.writerow([
            '手机号', '姓名', '分析次数', '剩余额度', '总额度',
            '使用率', '注册时间', '最后登录时间'
        ])

        # 写入数据
        for user, analysis_count in users_data:
            usage_percentage = user.quota_usage_percentage
            writer.writerow([
                user.phone,
                user.name or '未设置',
                analysis_count,
                user.remaining_quota,
                user.ai_quota,
                f'{usage_percentage:.1f}%',
                user.created_at_display,
                user.last_login_display
            ])

        # 生成文件名
        filename = f'users_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'

        # 返回CSV文件
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename="{filename}"'
            }
        )

    except Exception as e:
        app.logger.error(f"导出用户数据失败: {str(e)}")
        return jsonify({'error': '导出用户数据失败'}), 500


