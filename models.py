from datetime import datetime, timezone, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash


class User(UserMixin, db.Model):
    """用户登录模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    phone = db.Column(db.String(11), unique=True, nullable=False, comment='手机号')
    password_hash = db.Column(db.String(256), nullable=False, comment='密码哈希')
    name = db.Column(db.String(100), nullable=True, comment='用户姓名')
    active = db.Column(db.Boolean, default=True, comment='账户是否激活')
    is_admin = db.Column(db.Boolean, default=False, comment='是否为管理员用户')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, comment='创建时间')
    last_login = db.Column(db.DateTime, comment='最后登录时间')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.utcnow()
    
    @property
    def created_at_display(self):
        """格式化的创建时间 (UTC+8)"""
        if self.created_at:
            utc8_time = self.created_at + timedelta(hours=8)
            return utc8_time.strftime('%Y年%m月%d日 %H:%M:%S')
        return ''
    
    @property
    def last_login_display(self):
        """格式化的最后登录时间 (UTC+8)"""
        if self.last_login:
            utc8_time = self.last_login + timedelta(hours=8)
            return utc8_time.strftime('%Y年%m月%d日 %H:%M:%S')
        return '从未登录'
    
    @property
    def user_type_display(self):
        """用户类型显示文本"""
        return '管理员' if self.is_admin else '普通用户'
    
    def __repr__(self):
        return f'<User {self.phone}>'


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


class AnalysisResult(db.Model):
    """存储AI分析结果，避免session过大的问题"""
    __tablename__ = 'analysis_results'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 关联用户
    form_data = db.Column(db.Text, nullable=False)  # JSON格式的表单数据
    result_data = db.Column(db.Text, nullable=False)  # JSON格式的分析结果
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 添加项目基本信息字段，便于历史页面展示
    project_name = db.Column(db.String(255), nullable=True)
    project_description = db.Column(db.Text, nullable=True)
    project_stage = db.Column(db.String(100), nullable=True)
    team_size = db.Column(db.Integer, nullable=True, default=0)
    analysis_type = db.Column(db.String(50), nullable=False, default='ai_analysis')  # ai_analysis, fallback
    
    # 添加关联关系
    user = db.relationship('User', backref='analysis_results', lazy=True)
    
    def __repr__(self):
        return f'<AnalysisResult {self.project_name} - {self.created_at}>'
    
    def to_dict(self):
        """转换为字典格式，便于API返回"""
        import json
        return {
            'id': self.id,
            'project_name': self.project_name,
            'project_description': self.project_description,
            'project_stage': self.project_stage,
            'team_size': self.team_size,
            'analysis_type': self.analysis_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'form_data': json.loads(self.form_data) if self.form_data else {},
            'result_data': json.loads(self.result_data) if self.result_data else {}
        }
    
    @property
    def created_at_display(self):
        """格式化的创建时间"""
        if self.created_at:
            return self.created_at.strftime('%Y年%m月%d日 %H:%M')
        return ''
    
    @property
    def analysis_type_display(self):
        """分析类型显示"""
        type_map = {
            'ai_analysis': 'AI深度分析',
            'fallback': '基础建议方案'
        }
        return type_map.get(self.analysis_type, self.analysis_type)