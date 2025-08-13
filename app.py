import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory, Response
from flask_sqlalchemy import SQLAlchemy
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

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 定义模型直接在这里避免循环导入
class KnowledgeItem(db.Model):
    """AI知识库条目模型"""
    __tablename__ = 'knowledge_items'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False, comment='文件名')
    original_filename = db.Column(db.String(255), nullable=False, comment='原始文件名')
    file_path = db.Column(db.String(500), nullable=False, comment='文件存储路径')
    file_type = db.Column(db.String(50), nullable=False, comment='文件类型')
    file_size = db.Column(db.Integer, nullable=False, comment='文件大小(字节)')
    content_summary = db.Column(db.Text, comment='文件内容摘要')
    status = db.Column(db.String(20), nullable=False, default='active', comment='状态: active/paused/deleted')
    upload_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, comment='上传时间')
    last_modified = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, comment='最后修改时间')
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    
    def __repr__(self):
        return f'<KnowledgeItem {self.original_filename}>'
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'content_summary': self.content_summary,
            'status': self.status,
            'upload_time': self.upload_time.isoformat() if self.upload_time else None,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'usage_count': self.usage_count
        }
    
    @property
    def status_display(self):
        """状态显示文本"""
        status_map = {
            'active': '使用中',
            'paused': '已暂停',
            'deleted': '已删除'
        }
        return status_map.get(self.status, self.status)
    
    @property
    def file_size_display(self):
        """文件大小显示"""
        if self.file_size < 1024:
            return f"{self.file_size} B"
        elif self.file_size < 1024 * 1024:
            return f"{self.file_size / 1024:.1f} KB"
        else:
            return f"{self.file_size / (1024 * 1024):.1f} MB"

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    """Main form page for user input - Apple design"""
    return render_template('index_apple.html')

@app.route('/thinking')
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
    
    app.logger.info(f"Thinking page loaded with status: {session.get('analysis_status')}")
    return render_template('thinking_process.html')

@app.route('/analysis_status', methods=['GET'])
def analysis_status():
    """检查AI分析状态的AJAX端点 - 确保始终返回JSON"""
    return check_analysis_status()

@app.route('/check_analysis_status', methods=['GET'])
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
    
    # 处理需要开始或重试的分析
    if status == 'not_started' or (status == 'processing' and result is None):
        return _handle_analysis_execution(form_data, session)
    
    # 默认处理中状态
    app.logger.info("Analysis in progress - returning processing status")
    return jsonify({
        'status': 'processing', 
        'progress': 50,
        'message': '分析正在进行中，请稍候...'
    })

def _handle_analysis_execution(form_data, session):
    """处理AI分析执行"""
    import traceback
    
    try:
        # 设置状态为处理中
        session['analysis_status'] = 'processing'
        app.logger.info("Starting AI analysis in request context")
        
        # 执行AI分析
        suggestions = generate_ai_suggestions(form_data)
        
        if suggestions and isinstance(suggestions, dict):
            # 分析成功 - 将结果存储到数据库而不是session，避免session过大
            import uuid
            result_id = str(uuid.uuid4())
            
            # 直接使用SQL插入结果到数据库
            try:
                from sqlalchemy import text
                form_data_json = json.dumps(form_data, ensure_ascii=False)
                result_data_json = json.dumps(suggestions, ensure_ascii=False)
                
                db.session.execute(text("""
                    INSERT INTO analysis_results (id, form_data, result_data, created_at)
                    VALUES (:id, :form_data, :result_data, NOW())
                """), {
                    'id': result_id,
                    'form_data': form_data_json,
                    'result_data': result_data_json
                })
                db.session.commit()
            except Exception as db_error:
                app.logger.error(f"Failed to store result in database: {str(db_error)}")
                # 如果数据库存储失败，回退到session存储
                session['analysis_result'] = suggestions
            
            # 在session中只存储结果ID
            session['analysis_result_id'] = result_id
            session['analysis_status'] = 'completed'
            # 清理session中的大数据
            if 'analysis_result' in session:
                del session['analysis_result']
            
            app.logger.info(f"AI analysis completed successfully, result stored with ID: {result_id}")
            return jsonify({
                'status': 'completed', 
                'redirect_url': '/results',
                'message': '分析完成，正在跳转到结果页面...'
            })
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
        
        session['analysis_status'] = 'error'
        session['analysis_error'] = error_msg
        
        return jsonify({
            'status': 'error', 
            'message': f'分析过程遇到问题: {error_msg}',
            'error_code': 'EXECUTION_ERROR'
        })

@app.route('/results')
def results():
    """Display AI analysis result page with dynamic loading"""
    try:
        from flask import session
        
        # Get form data and analysis status from session
        form_data = session.get('analysis_form_data')
        status = session.get('analysis_status', 'not_started')
        result_id = session.get('analysis_result_id')
        
        app.logger.info(f"Results page - Status: {status}, Form data exists: {form_data is not None}, Result ID: {result_id}")
        
        # 如果没有表单数据，说明会话过期或直接访问
        if not form_data:
            app.logger.warning("No form data found in session for result page")
            flash('会话已过期，请重新提交表单', 'error')
            return redirect(url_for('index'))
        
        # 根据分析状态决定显示内容
        if status == 'completed' and result_id:
            # 从数据库读取分析结果
            try:
                import json
                from sqlalchemy import text
                
                result = db.session.execute(text("""
                    SELECT result_data FROM analysis_results WHERE id = :id
                """), {'id': result_id}).fetchone()
                
                if result:
                    suggestions = json.loads(result[0])
                    app.logger.info("Analysis completed - showing full results from database")
                    return render_template('result_apple_redesigned.html', 
                                         form_data=form_data, 
                                         result=suggestions,
                                         status='completed')
                else:
                    app.logger.warning(f"Analysis result not found in database: {result_id}")
                    suggestions = None
            except Exception as e:
                app.logger.error(f"Error reading analysis result from database: {str(e)}")
                suggestions = None
            
            # 如果数据库读取失败，继续尝试从session读取（兼容性）
            if not suggestions:
                suggestions = session.get('analysis_result')
                if suggestions:
                    app.logger.info("Analysis completed - showing full results from session")
                    return render_template('result_apple_redesigned.html', 
                                         form_data=form_data, 
                                         result=suggestions,
                                         status='completed')
        
        elif status == 'error':
            # 分析出错，显示错误信息
            error_msg = session.get('analysis_error', '分析过程中发生未知错误')
            app.logger.info(f"Analysis error - showing error page: {error_msg}")
            return render_template('result_apple_redesigned.html',
                                 form_data=form_data,
                                 status='error',
                                 error_message=error_msg)
        
        else:
            # 分析未开始或正在进行，显示骨架屏
            app.logger.info("Analysis not completed - showing loading skeleton")
            return render_template('result_apple_redesigned.html',
                                 form_data=form_data,
                                 status='loading',
                                 current_status=status)
    
    except Exception as e:
        app.logger.error(f"Error displaying results: {str(e)}")
        flash('显示结果时发生错误，请重试', 'error')
        return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
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
        
        # Process external resources
        external_resources = request.form.getlist('external_resources')
        
        # Handle other resource input
        other_resource_text = request.form.get('other_resource_text', '').strip()
        if other_resource_text and request.form.get('other_resource_checkbox'):
            external_resources.append(other_resource_text)
        
        # Create JSON structure as per PRD
        form_data = {
            "projectName": project_name,
            "projectDescription": project_description,
            "projectStage": project_stage,
            "keyPersons": key_persons,
            "externalResources": external_resources
        }
        
        # Store form data in session 
        from flask import session
        session['analysis_form_data'] = form_data
        
        # 设置分析状态为未开始，等待thinking页面触发
        session['analysis_status'] = 'not_started'
        session['analysis_result'] = None
        
        # 详细调试session存储
        app.logger.info(f"Generate route - Before storing - Full session: {dict(session)}")
        session.permanent = True  # 设置session为永久性
        app.logger.info(f"Generate route - After storing - Full session: {dict(session)}")
        app.logger.info(f"Generate route - Session modified: {session.modified}")
        
        # Log the received data
        app.logger.info(f"Received form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        app.logger.info(f"Session data stored successfully")
        
        # 跳转到新的Matrix风格思考页面
        return redirect(url_for('thinking_process'))
    
    except Exception as e:
        app.logger.error(f"Error processing form: {str(e)}")
        flash('处理表单时发生错误，请重试', 'error')
        return redirect(url_for('index'))

def generate_ai_suggestions(form_data):
    """Generate AI suggestions using OpenAI API with timeout and error handling"""
    import signal
    import time
    
    def timeout_handler(signum, frame):
        raise TimeoutError("AI分析超时")
    
    try:
        # 设置35秒超时，给OpenAI客户端留足够时间
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(35)
        
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
        
        start_time = time.time()
        # 调用AI生成服务
        ai_result = angela_ai.generate_income_paths(converted_data, db)
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
@app.route('/admin')
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
def result_preview():
    """展示新设计的结果页面预览"""
    # 模拟数据用于展示新设计
    mock_result = {
        "overview": {
            "situation": "当前资源集中在张三的微信群和视频号粉丝，暂无其他明确资源，张三动机偏向经济收益和名声。",
            "gaps": ["缺少产品或服务可供推广", "缺少明确的分成模式", "缺少高黏性流量合作方或内容创作者"],
            "suggested_roles_to_hunt": [
                {
                    "role": "内容创作者/KOL",
                    "why": "可提供吸引流量的内容，补充张三的渠道资源",
                    "where_to_find": "短视频平台（如抖音、快手）或微博，搜索相关领域小V",
                    "outreach_script": "您好，我们有一个合作项目，需要优质内容创作，愿提供分成及长期合作机会，方便聊聊吗？"
                }
            ]
        },
        "paths": [
            {
                "id": "path_1",
                "name": "视频号带货分成",
                "scene": "通过张三的视频号进行商品推广",
                "who_moves_first": "你先与张三对接分成模式",
                "action_steps": [
                    {
                        "owner": "你",
                        "step": "联系张三，商讨视频号推广分成模式，确定商品类型和分成比例",
                        "why_it_works": "张三资源集中在视频号，分成满足其经济动机"
                    },
                    {
                        "owner": "张三",
                        "step": "发布带货视频内容（每周2条），并在视频中附带商品购买链接",
                        "why_it_works": "利用视频号粉丝进行精准推广，直接触发转化"
                    },
                    {
                        "owner": "你",
                        "step": "通过电商平台联系小商家，获取试用品或样品以备推广",
                        "why_it_works": "补充具体可推广的产品资源，降低启动门槛"
                    }
                ],
                "use_key_person_resources": ["张三的视频号粉丝5万"],
                "use_external_resources": ["电商平台商家资源"],
                "revenue_trigger": "通过视频号带货产生销售分成",
                "mvp": "联系3个商家，成功完成至少1个商品推广视频并获得首批订单（目标≥10单）",
                "risks": ["商品质量不佳导致负面评价", "视频号带货效果不理想"],
                "plan_b": "若商品效果不佳，改为推广虚拟商品或服务，如课程或会员卡",
                "kpis": ["完成视频数量≥2条/周", "商品转化率≥2%"]
            },
            {
                "id": "path_2", 
                "name": "微信群活动引流",
                "scene": "利用张三的微信群进行活动引流",
                "who_moves_first": "你设计活动方案并提供宣传文案",
                "action_steps": [
                    {
                        "owner": "你",
                        "step": "设计一个简单的社群活动（如抽奖或秒杀），编写活动文案并提供给张三",
                        "why_it_works": "社群活动可以快速激活微信群成员，带来初步参与度"
                    },
                    {
                        "owner": "张三", 
                        "step": "在微信群发布活动信息，并引导群成员参与活动（每个群发送频次每天1次）",
                        "why_it_works": "张三的社群资源高效触达潜在用户"
                    },
                    {
                        "owner": "你",
                        "step": "同步监测参与数据，及时优化活动流程（如调整奖品或规则）",
                        "why_it_works": "实时调整可提升活动效果，挖掘更多用户兴趣点"
                    }
                ],
                "use_key_person_resources": ["张三的3个微信群"],
                "use_external_resources": ["免费活动工具（如抽奖助手）"],
                "revenue_trigger": "通过活动增加用户留存，引导后续消费或转化",
                "mvp": "完成1次微信群活动，吸引至少50人参与并成功转化≥5人",
                "risks": ["活动设计吸引力不足", "活动执行成本超预算"],
                "plan_b": "若微信群效果差，可尝试视频号同步推广活动方案",
                "kpis": ["活动参与人数≥50", "活动转化率≥10%"]
            }
        ],
        "notes": "建议尽早补齐产品提供方资源，确保推广内容有明确载体。"
    }
    
    return render_template('result_apple_redesigned.html', result=mock_result)



@app.route('/admin/ai-chat', methods=['POST'])
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
