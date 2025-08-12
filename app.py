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

@app.route('/generate', methods=['POST'])
def generate():
    """Process form data and generate AI suggestions"""
    try:
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
            "project_name": project_name,
            "project_description": project_description,
            "project_stage": project_stage,
            "key_persons": key_persons,
            "external_resources": external_resources
        }
        
        # Log the received data
        app.logger.info(f"Received form data: {json.dumps(form_data, ensure_ascii=False, indent=2)}")
        
        # Generate AI suggestions (simulated for demo)
        suggestions = generate_ai_suggestions(form_data)
        
        return render_template('result_apple.html', 
                             form_data=form_data, 
                             suggestions=suggestions)
    
    except Exception as e:
        app.logger.error(f"Error processing form: {str(e)}")
        flash('处理表单时发生错误，请重试', 'error')
        return redirect(url_for('index'))

def generate_ai_suggestions(form_data):
    """Generate AI suggestions based on form data"""
    # This is where you would integrate with an actual LLM API
    # For now, we'll return realistic suggestions based on the input
    
    project_name = form_data.get('project_name', '')
    key_persons = form_data.get('key_persons', [])
    
    suggestions = []
    
    # Generate AI suggestions with proper format for Apple design templates
    suggestion1 = {
        "title": "收益分成合作模式",
        "description": f"基于{project_name}项目建立多方收益分成机制，与合作伙伴共享收益，降低风险的同时确保持续收入流。",
        "implementation_steps": [
            "分析项目核心价值点，确定可分成的收益环节",
            "识别潜在合作伙伴，建立初步接触渠道", 
            "制定公平透明的收益分成比例方案",
            "签署正式合作协议，明确各方权责",
            "建立收益监控和分配机制"
        ],
        "required_resources": ["法务支持", "财务系统", "合作伙伴网络"],
        "key_roles": [person["name"] for person in key_persons[:3] if person.get("name")],
        "estimated_revenue": "月收入 3-8万元"
    }
    
    suggestion2 = {
        "title": "知识产权授权模式",
        "description": f"将{project_name}的核心技术、方法论或品牌价值进行标准化，通过授权许可获得持续收入。",
        "implementation_steps": [
            "梳理项目中的核心知识产权和可复制资产",
            "完善知识产权保护，申请相关专利或版权",
            "开发标准化授权方案和培训体系",
            "寻找目标授权客户，进行市场推广",
            "建立授权管理和技术支持体系"
        ],
        "required_resources": ["知识产权律师", "标准化文档", "培训材料"],
        "key_roles": [person["name"] for person in key_persons if person.get("name") and "技术" in person.get("role", "")],
        "estimated_revenue": "年收入 15-50万元"
    }
    
    suggestion3 = {
        "title": "顾问咨询服务模式", 
        "description": f"基于{project_name}的成功经验，为同行业客户提供专业咨询服务，建立专家品牌价值。",
        "implementation_steps": [
            "总结项目成功经验，形成方法论体系",
            "建立个人或团队专业品牌形象",
            "开发咨询服务产品线和定价体系",
            "通过内容营销建立行业影响力",
            "建立客户获取和服务交付流程"
        ],
        "required_resources": ["品牌建设", "内容创作", "客户关系管理"],
        "key_roles": [person["name"] for person in key_persons[:2] if person.get("name")],
        "estimated_revenue": "项目收入 5-20万元"
    }
    
    suggestions = [suggestion1, suggestion2, suggestion3]
    
    return suggestions

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


@app.route('/result')
def result():
    """Results page (in case of direct access)"""
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
