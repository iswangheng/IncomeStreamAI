import os
import json
import logging
from datetime import datetime
from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, send_from_directory
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
    """Main form page for user input"""
    return render_template('index.html')

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
        
        external_resources = request.form.getlist('external_resources')
        
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
        
        return render_template('result.html', 
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
    
    # Suggestion 1: Revenue Sharing Model
    suggestion1 = {
        "title": "收益分成模式",
        "description": f"基于{project_name}项目，建立多方收益分成机制",
        "details": [
            "与品牌方建立产品销售分成关系，获得销售额的10-15%分成",
            "整合渠道资源，为品牌方提供精准流量导入",
            "建立长期合作关系，确保持续收益流"
        ],
        "key_roles": [person["name"] for person in key_persons[:2]],
        "revenue_potential": "中等-稳定",
        "implementation_difficulty": "中等"
    }
    
    # Suggestion 2: Platform Integration Model
    suggestion2 = {
        "title": "平台整合变现模式",
        "description": "通过整合多方资源，搭建收益分发平台",
        "details": [
            "建立资源整合平台，连接品牌方、渠道方和内容方",
            "收取平台服务费和交易佣金",
            "提供增值服务，如数据分析、营销策划等"
        ],
        "key_roles": [person["name"] for person in key_persons],
        "revenue_potential": "高-可扩展",
        "implementation_difficulty": "较高"
    }
    
    # Suggestion 3: Consulting & Advisory Model
    suggestion3 = {
        "title": "顾问咨询收费模式",
        "description": "基于项目经验，提供专业咨询服务",
        "details": [
            "为类似项目提供策划和执行咨询服务",
            "建立行业专家网络，收取介绍费和咨询费",
            "开发标准化解决方案，实现规模化收费"
        ],
        "key_roles": ["项目负责人", "行业专家"],
        "revenue_potential": "中等-专业化",
        "implementation_difficulty": "较低"
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
    
    return render_template('admin/dashboard.html', 
                         knowledge_items=knowledge_items,
                         status_filter=status_filter,
                         search_query=search_query)



@app.route('/admin/knowledge/upload', methods=['GET', 'POST'])
def upload_knowledge():
    """上传知识库文件"""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件', 'error')
            return redirect(request.url)
        
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
                knowledge_item = KnowledgeItem(
                    filename=filename,
                    original_filename=file.filename,
                    file_path=file_path,
                    file_type=file_extension,
                    file_size=file_size,
                    content_summary=request.form.get('summary', ''),
                    status='active'
                )
                
                db.session.add(knowledge_item)
                db.session.commit()
                
                flash(f'文件 "{file.filename}" 上传成功', 'success')
                return redirect(url_for('admin_dashboard'))
                
            except Exception as e:
                flash(f'上传失败: {str(e)}', 'error')
                # 删除已保存的文件
                if os.path.exists(file_path):
                    os.remove(file_path)
        else:
            flash('不支持的文件类型。支持的格式: txt, pdf, doc, docx, xlsx, csv, md, json', 'error')
    
    return render_template('admin/upload_knowledge.html')

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



@app.route('/result')
def result():
    """Results page (in case of direct access)"""
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
