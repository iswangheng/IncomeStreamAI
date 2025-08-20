import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, Response, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_required, login_user, logout_user, current_user
from sqlalchemy.orm import DeclarativeBase

# Configure logging
logging.basicConfig(level=logging.DEBUG)

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

# 导入所有模型
from models import User, KnowledgeItem, AnalysisResult

@login_manager.user_loader
def load_user(user_id):
    """Flask-Login用户加载回调"""
    return User.query.get(int(user_id))

with app.app_context():
    db.create_all()
    
    # 创建默认登录账号
    default_user = User.query.filter_by(phone='18302196515').first()
    if not default_user:
        default_user = User(phone='18302196515', name='默认用户')
        default_user.set_password('aibenzong9264')
        db.session.add(default_user)
        db.session.commit()
        print("已创建默认登录账号: 18302196515 / aibenzong9264")

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

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    """修改密码页面"""
    if request.method == 'POST':
        current_password = request.form.get('current_password', '').strip()
        new_password = request.form.get('new_password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # 验证输入
        if not current_password or not new_password or not confirm_password:
            flash('请填写所有密码字段', 'error')
            return render_template('change_password.html')
        
        # 验证当前密码
        if not current_user.check_password(current_password):
            flash('当前密码错误，请重新输入', 'error')
            return render_template('change_password.html')
        
        # 验证新密码长度
        if len(new_password) < 6:
            flash('新密码长度至少为6位', 'error')
            return render_template('change_password.html')
        
        # 验证新密码与确认密码一致
        if new_password != confirm_password:
            flash('两次输入的新密码不一致，请重新输入', 'error')
            return render_template('change_password.html')
        
        # 验证新密码与当前密码不同
        if current_user.check_password(new_password):
            flash('新密码不能与当前密码相同', 'error')
            return render_template('change_password.html')
        
        # 更新密码
        try:
            current_user.set_password(new_password)
            db.session.commit()
            flash('密码修改成功！', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Password change error for user {current_user.id}: {str(e)}")
            flash('密码修改失败，请稍后重试', 'error')
            return render_template('change_password.html')
    
    return render_template('change_password.html')

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """编辑个人资料页面"""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # 验证输入
        if not phone:
            flash('手机号不能为空', 'error')
            return render_template('profile.html')
        
        # 验证手机号格式（简单验证）
        if len(phone) != 11 or not phone.isdigit():
            flash('请输入有效的11位手机号', 'error')
            return render_template('profile.html')
        
        # 检查手机号是否被其他用户使用
        if phone != current_user.phone:
            existing_user = User.query.filter_by(phone=phone).first()
            if existing_user:
                flash('该手机号已被其他用户使用', 'error')
                return render_template('profile.html')
        
        # 更新用户信息
        try:
            current_user.name = name if name else None
            current_user.phone = phone
            db.session.commit()
            flash('个人资料更新成功！', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Profile update error for user {current_user.id}: {str(e)}")
            flash('个人资料更新失败，请稍后重试', 'error')
            return render_template('profile.html')
    
    return render_template('profile.html')

def save_session_in_ajax():
    """辅助函数：确保AJAX请求中session被正确保存"""
    from flask import session
    session.permanent = True
    session.modified = True
    # 这会强制Flask重新计算session并设置cookie
    app.logger.debug(f"Forcing session save - Status: {session.get('analysis_status')}, Result ID: {session.get('analysis_result_id')}")

@app.route('/thinking')
@login_required
def thinking_process():
    """AI thinking process visualization page"""
    from flask import session, redirect, url_for, flash
    
    # Get form data from session
    form_data = session.get('analysis_form_data')
    app.logger.info(f"Thinking page - session data exists: {form_data is not None}")
    
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
        form_data = session.get('analysis_form_data')
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
            analysis_result = AnalysisResult(
                id=fallback_id,
                form_data=json.dumps(form_data, ensure_ascii=False),
                result_data=json.dumps(fallback_result, ensure_ascii=False),
                project_name=form_data.get('projectName', ''),
                project_description=form_data.get('projectDescription', ''),
                project_stage=form_data.get('projectStage', ''),
                team_size=len(form_data.get('keyPersons', [])),
                analysis_type='fallback'
            )
            db.session.add(analysis_result)
            db.session.commit()
            
            # 更新session状态
            session['analysis_form_data'] = form_data  # 保存form_data
            session['analysis_status'] = 'completed'
            session['analysis_result_id'] = fallback_id
            session['analysis_result'] = fallback_result
            
            # 使用辅助函数确保session在AJAX中被保存
            save_session_in_ajax()
            
            app.logger.info(f"Fallback solution generated and saved with ID: {fallback_id}")
            
            # 创建response并确保session被保存
            response = jsonify({
                'status': 'completed', 
                'redirect_url': '/results',
                'message': '已生成备用方案，正在跳转...'
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
    
    # 处理需要开始或重试的分析
    if status == 'not_started' or (status == 'processing' and result is None and not result_id):
        return _handle_analysis_execution(form_data, session)
    
    # 默认处理中状态 - 返回真实进度
    progress = session.get('analysis_progress', 50)
    stage = session.get('analysis_stage', '分析正在进行中...')
    app.logger.info(f"Analysis in progress - Progress: {progress}%, Stage: {stage}")
    return jsonify({
        'status': 'processing', 
        'progress': progress,
        'stage': stage,
        'message': stage
    })

def _handle_analysis_execution(form_data, session):
    """处理AI分析执行"""
    import traceback
    import json
    
    try:
        # 设置状态为处理中
        session['analysis_status'] = 'processing'
        session['analysis_progress'] = 10
        session['analysis_stage'] = '开始AI分析...'
        save_session_in_ajax()  # 使用辅助函数确保session被保存
        app.logger.info("Starting AI analysis in request context")
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
            
            # 保存完整的分析结果到数据库
            try:
                from models import AnalysisResult
                import json
                
                # 创建AnalysisResult实例
                analysis_result = AnalysisResult(
                    id=result_id,
                    form_data=json.dumps(form_data, ensure_ascii=False),
                    result_data=json.dumps(suggestions, ensure_ascii=False),
                    project_name=form_data.get('projectName', ''),
                    project_description=form_data.get('projectDescription', ''),
                    project_stage=form_data.get('projectStage', ''),
                    team_size=len(form_data.get('keyPersons', [])),
                    analysis_type='ai_analysis'
                )
                
                db.session.add(analysis_result)
                db.session.commit()
            except Exception as db_error:
                app.logger.error(f"Failed to store result in database: {str(db_error)}")
                # 如果数据库存储失败，回退到session存储
                session['analysis_result'] = suggestions
            
            # 在session中存储必要的数据
            session['analysis_form_data'] = form_data  # 关键！必须保存form_data
            session['analysis_result_id'] = result_id
            session['analysis_status'] = 'completed'
            session['analysis_progress'] = 100
            session['analysis_stage'] = '分析完成！'
            # 保留一份备份在session中以防数据库读取失败
            session['analysis_result'] = suggestions
            
            # 使用辅助函数确保session在AJAX中被保存
            save_session_in_ajax()
            
            app.logger.info(f"AI analysis completed successfully, result stored with ID: {result_id}")
            app.logger.info(f"Session updated - Status: {session.get('analysis_status')}, Result ID: {session.get('analysis_result_id')}")
            app.logger.info(f"Session state after update - Permanent: {session.permanent}, Modified: {session.modified}")
            
            # 创建response并确保session被保存
            response = jsonify({
                'status': 'completed', 
                'redirect_url': '/results',
                'message': '分析完成，正在跳转到结果页面...'
            })
            
            # 确保会话cookie被正确设置
            from flask import make_response
            response = make_response(response)
            
            return response
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
        if 'timeout' in error_msg.lower() or 'connection' in error_msg.lower() or 'ssl' in error_msg.lower():
            session['analysis_status'] = 'timeout'
            app.logger.info("Network timeout detected, immediately generating fallback")
            
            try:
                fallback_result = generate_fallback_suggestions(form_data)
                
                # 保存备用方案到数据库
                import uuid
                import json
                from models import AnalysisResult
                
                fallback_id = str(uuid.uuid4())
                analysis_result = AnalysisResult(
                    id=fallback_id,
                    form_data=json.dumps(form_data, ensure_ascii=False),
                    result_data=json.dumps(fallback_result, ensure_ascii=False),
                    project_name=form_data.get('projectName', ''),
                    project_description=form_data.get('projectDescription', ''),
                    project_stage=form_data.get('projectStage', ''),
                    team_size=len(form_data.get('keyPersons', [])),
                    analysis_type='fallback'
                )
                db.session.add(analysis_result)
                db.session.commit()
                
                # 更新session状态为完成
                session['analysis_form_data'] = form_data  # 保存form_data
                session['analysis_status'] = 'completed'
                session['analysis_result_id'] = fallback_id
                session['analysis_result'] = fallback_result
                
                # 使用辅助函数确保session在AJAX中被保存
                save_session_in_ajax()
                
                app.logger.info(f"Fallback generated immediately due to timeout, ID: {fallback_id}")
                
                # 创建response并确保session被保存
                response = jsonify({
                    'status': 'completed', 
                    'redirect_url': '/results',
                    'message': '网络不稳定，已生成备用方案...'
                })
                
                from flask import make_response
                response = make_response(response)
                
                return response
                
            except Exception as fallback_error:
                app.logger.error(f"Fallback generation failed: {str(fallback_error)}")
                session['analysis_status'] = 'error'
                session['analysis_error'] = '网络超时且备用方案生成失败，请重试'
                return jsonify({
                    'status': 'error', 
                    'message': '网络连接问题，请检查网络后重试',
                    'error_code': 'NETWORK_AND_FALLBACK_FAILED'
                })
        else:
            session['analysis_status'] = 'error'
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
        form_data = session.get('analysis_form_data')
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
                        session['analysis_form_data'] = form_data
                        session.permanent = True
                        session.modified = True
                        app.logger.info(f"Recovered form data from database for result ID: {result_id}")
                    
                    if analysis_record.result_data:
                        result_data = json.loads(analysis_record.result_data)
                        session['analysis_result'] = result_data
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
        
        # 如果有表单数据但result_id指向的是备用方案，尝试找到真正的AI分析结果
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

        # 如果没有表单数据，不要随意从其他记录中恢复，应该重定向到首页
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
                return render_template('result_apple_redesigned.html', 
                                     form_data=form_data, 
                                     result=suggestions,
                                     status='completed')
            else:
                # 分析标记为完成但没有结果数据，显示错误状态
                app.logger.error("Analysis completed but no result data available")
                return render_template('result_apple_redesigned.html',
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
                        from models import AnalysisResult
                        import uuid
                        fallback_id = str(uuid.uuid4())
                        
                        analysis_result = AnalysisResult(
                            id=fallback_id,
                            form_data=json.dumps(form_data, ensure_ascii=False),
                            result_data=json.dumps(fallback_result, ensure_ascii=False),
                            project_name=form_data.get('projectName', ''),
                            project_description=form_data.get('projectDescription', ''),
                            project_stage=form_data.get('projectStage', ''),
                            team_size=len(form_data.get('keyPersons', [])),
                            analysis_type='fallback'
                        )
                        
                        db.session.add(analysis_result)
                        db.session.commit()
                        app.logger.info(f"Fallback result saved with ID: {fallback_id}")
                    except Exception as db_error:
                        app.logger.error(f"Failed to save fallback result: {str(db_error)}")
                    
                    return render_template('result_apple_redesigned.html',
                                         form_data=form_data,
                                         result=fallback_result,
                                         status='completed',
                                         fallback_mode=True)
                except Exception as e:
                    app.logger.error(f"Fallback generation failed: {str(e)}")
            
            return render_template('result_apple_redesigned.html',
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
                    import json
                    
                    analysis_record = AnalysisResult.query.filter_by(id=result_id).first()
                    if analysis_record and analysis_record.result_data:
                        suggestions = json.loads(analysis_record.result_data)
                        app.logger.info(f"Found existing result in database for ID: {result_id}")
                        return render_template('result_apple_redesigned.html', 
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
                    from models import AnalysisResult
                    import uuid
                    import json
                    
                    emergency_id = str(uuid.uuid4())
                    analysis_result = AnalysisResult(
                        id=emergency_id,
                        form_data=json.dumps(form_data, ensure_ascii=False),
                        result_data=json.dumps(fallback_result, ensure_ascii=False),
                        project_name=form_data.get('projectName', ''),
                        project_description=form_data.get('projectDescription', ''),
                        project_stage=form_data.get('projectStage', ''),
                        team_size=len(form_data.get('keyPersons', [])),
                        analysis_type='emergency_fallback'
                    )
                    db.session.add(analysis_result)
                    db.session.commit()
                    
                    # 更新session
                    session['analysis_form_data'] = form_data  # 保存form_data
                    session['analysis_status'] = 'completed'
                    session['analysis_result_id'] = emergency_id
                    session['analysis_result'] = fallback_result
                    
                    app.logger.info(f"Emergency fallback generated with ID: {emergency_id}")
                except Exception as db_error:
                    app.logger.error(f"Failed to save emergency fallback: {str(db_error)}")
                
                return render_template('result_apple_redesigned.html',
                                     form_data=form_data,
                                     result=fallback_result,
                                     status='completed',
                                     fallback_mode=True)
                                     
            except Exception as fallback_error:
                app.logger.error(f"Emergency fallback generation failed: {str(fallback_error)}")
                return render_template('result_apple_redesigned.html',
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
        project_stage = request.form.get('project_stage', '')
        
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
                key_persons.append({
                    "name": person_names[i].strip(),
                    "role": person_roles[i].strip() if i < len(person_roles) else "",
                    "resources": [r.strip() for r in person_resources[i].split(',') if r.strip()] if i < len(person_resources) else [],
                    "make_happy": person_needs[i].strip() if i < len(person_needs) else ""
                })
        
        # Create JSON structure as per PRD
        form_data = {
            "projectName": project_name,
            "projectDescription": project_description,
            "projectStage": project_stage,
            "keyPersons": key_persons
        }
        
        # Store form data in session 
        from flask import session
        session['analysis_form_data'] = form_data
        
        # 清理所有旧的分析相关数据，确保新项目不会使用旧的result_id
        session['analysis_status'] = 'not_started'
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
        app.logger.info(f"Session data stored successfully")
        
        # 跳转到新的Matrix风格思考页面
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
        # 设置90秒超时，给重试机制和网络延迟留足够时间
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(90)
        
        from openai_service import AngelaAI
        
        # 使用真正的AI服务生成方案
        angela_ai = AngelaAI()
        
        # 转换数据格式以匹配openai_service的预期格式
        converted_data = {
            'projectName': form_data.get('projectName', form_data.get('project_name', '')),
            'projectDescription': form_data.get('projectDescription', form_data.get('project_description', '')),
            'projectStage': form_data.get('projectStage', form_data.get('project_stage', '')),
            'keyPersons': form_data.get('keyPersons', form_data.get('key_persons', [])),
            'externalResources': form_data.get('externalResources', form_data.get('external_resources', []))
        }
        
        app.logger.info(f"Calling Angela AI with data: {json.dumps(converted_data, ensure_ascii=False)}")
        
        # 更新进度：开始AI分析
        if session:
            session['analysis_progress'] = 50
            session['analysis_stage'] = '正在调用AI分析引擎...'
        
        start_time = time.time()
        # 调用AI生成服务，添加SSL错误处理
        try:
            ai_result = angela_ai.generate_income_paths(converted_data, db)
        except (ConnectionError, OSError) as ssl_error:
            # SSL或网络连接错误
            app.logger.error(f"SSL/Network error during AI call: {str(ssl_error)}")
            # 取消超时
            signal.alarm(0)
            # 返回网络错误的备用方案
            return generate_fallback_result(form_data, "网络连接问题，为您提供基础建议")
        
        # 更新进度：AI分析完成
        if session:
            session['analysis_progress'] = 90
            session['analysis_stage'] = '正在生成分析报告...'
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

# Helper functions
def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size(file_obj):
    """获取文件大小"""
    if hasattr(file_obj, 'seek') and hasattr(file_obj, 'tell'):
        file_obj.seek(0, 2)  # 移到文件末尾
        size = file_obj.tell()
        file_obj.seek(0)  # 回到文件开头
        return size
    return 0

# Knowledge Base Management Routes
@app.route('/history')
@login_required
def analysis_history():
    """历史分析记录页面"""
    try:
        from models import AnalysisResult
        
        # 获取所有分析记录，按创建时间倒序
        analysis_records = AnalysisResult.query.order_by(AnalysisResult.created_at.desc()).all()
        
        app.logger.info(f"Found {len(analysis_records)} analysis records")
        
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
        
        # 解析JSON数据
        form_data = json.loads(record.form_data) if record.form_data else {}
        result_data = json.loads(record.result_data) if record.result_data else {}
        
        app.logger.info(f"Viewing analysis record: {record_id}")
        
        return render_template('result_apple_redesigned.html',
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

@app.route('/admin')
@login_required
def admin_dashboard():
    """后台管理主页 - 直接显示文件列表"""
    # 查询条件
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    
    query = KnowledgeItem.query
    
    if status_filter:
        query = query.filter_by(status=status_filter)
    
    if search_query:
        query = query.filter(KnowledgeItem.original_filename.contains(search_query))
    
    # 按上传时间倒序排列，只显示未删除的文件
    knowledge_items = query.filter(KnowledgeItem.status != 'deleted').order_by(KnowledgeItem.upload_time.desc()).all()
    
    return render_template('admin/dashboard_apple.html', 
                         knowledge_items=knowledge_items,
                         status_filter=status_filter,
                         search_query=search_query)



@app.route('/admin/knowledge/upload', methods=['POST'])
@login_required
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

def generate_fallback_suggestions(form_data):
    """当AI服务不可用时生成基础建议"""
    # 修复字段名：使用正确的驼峰命名
    project_name = form_data.get('projectName', form_data.get('project_name', '您的项目'))
    people = form_data.get('keyPersons', form_data.get('key_persons', []))
    
    # 基于表单数据生成基础建议
    fallback_suggestions = {
        "situation_analysis": f"根据您提交的项目信息「{project_name}」和团队配置，我们为您准备了以下基础收入路径建议。虽然当前AI深度分析服务暂时不可用，但基于常见的非劳务收入模式，为您提供这些可行的起步方案。",
        "missing_gaps": [
            "建立标准化流程体系",
            "设计自动化收入机制", 
            "构建客户获取渠道",
            "完善产品服务体系"
        ],
        "income_paths": []
    }
    
    # 生成基础路径建议
    if people:
        # 基于人员配置生成建议
        path1 = {
            "path_title": "知识产品化收入",
            "path_scene": "将团队专业知识转化为可复制的数字产品",
            "who_moves_first": f"{people[0].get('name', '团队负责人')}率先整理核心知识体系",
            "execution_steps": [
                {"owner": people[0].get('name', '负责人'), "action": "梳理并文档化核心专业知识和经验"},
                {"owner": "团队", "action": "设计在线课程或知识付费产品"},
                {"owner": "市场推广", "action": "建立内容营销和客户获取渠道"},
                {"owner": "运营", "action": "建立自动化销售和交付系统"}
            ],
            "mvp_content": "在24小时内：选择一个最有把握的专业话题，录制15分钟的试听课程，发布到社交平台测试反响。"
        }
        
        path2 = {
            "path_title": "服务标准化收入",
            "path_scene": "将现有服务流程标准化，实现规模化复制",
            "who_moves_first": "运营负责人设计标准化服务流程",
            "execution_steps": [
                {"owner": "运营", "action": "分析现有服务流程，制定标准化作业指导"},
                {"owner": "技术", "action": "开发或选择支持工具，提高服务效率"},
                {"owner": "销售", "action": "设计可复制的客户获取和转化流程"},
                {"owner": "管理", "action": "建立质量控制和客户满意度跟踪系统"}
            ],
            "mvp_content": "在24小时内：选择一项核心服务，编写详细的标准作业流程，并用实际客户测试一遍完整流程。"
        }
        
        fallback_suggestions["income_paths"] = [path1, path2]
    else:
        # 没有人员信息时的通用建议
        path1 = {
            "path_title": "个人品牌变现",
            "path_scene": "基于个人专业能力建立品牌影响力",
            "who_moves_first": "项目发起人开始内容输出",
            "execution_steps": [
                {"owner": "个人", "action": "确定专业定位和目标受众"},
                {"owner": "个人", "action": "制定内容输出计划，持续分享专业见解"},
                {"owner": "个人", "action": "建立社交媒体矩阵，扩大影响力"},
                {"owner": "个人", "action": "设计变现产品（咨询、课程、工具等）"}
            ],
            "mvp_content": "在24小时内：在主要社交平台发布一篇专业观点文章，观察互动反馈。"
        }
        
        fallback_suggestions["income_paths"] = [path1]
    
    return fallback_suggestions

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
