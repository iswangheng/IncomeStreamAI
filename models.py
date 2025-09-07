from datetime import datetime, timezone, timedelta
from app import db
from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash
import uuid


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
    
    # AI分析额度管理
    ai_quota = db.Column(db.Integer, default=10, nullable=False, comment='AI分析总额度')
    used_quota = db.Column(db.Integer, default=0, nullable=False, comment='已使用的AI分析次数')

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
    
    # AI分析额度相关方法
    @property
    def remaining_quota(self):
        """剩余的AI分析额度"""
        return max(0, self.ai_quota - self.used_quota)
    
    @property
    def quota_usage_percentage(self):
        """额度使用百分比"""
        if self.ai_quota <= 0:
            return 100
        return min(100, (self.used_quota / self.ai_quota) * 100)
    
    @property
    def quota_display(self):
        """额度显示文本"""
        return f"{self.used_quota}/{self.ai_quota}"
    
    def has_quota(self):
        """检查是否还有可用额度"""
        return self.remaining_quota > 0
    
    def consume_quota(self):
        """消耗一次AI分析额度"""
        if self.has_quota():
            self.used_quota += 1
            return True
        return False
    
    def set_quota(self, new_quota):
        """设置新的总额度（保持已使用额度不变）"""
        self.ai_quota = max(0, new_quota)
    
    def reset_quota(self, new_quota=None):
        """重置额度使用情况"""
        if new_quota is not None:
            self.ai_quota = max(0, new_quota)
        self.used_quota = 0
    
    def adjust_quota(self, amount):
        """调整总额度（增加或减少）"""
        self.ai_quota = max(0, self.ai_quota + amount)
    
    @classmethod
    def get_default_quota_for_role(cls, is_admin=False):
        """获取角色对应的默认额度"""
        return 10000 if is_admin else 10

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
    __tablename__ = 'analysis_results'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sequence_id = db.Column(db.Integer, nullable=False, index=True, server_default=db.text("nextval('analysis_results_sequence_id_seq')"), comment='自增数字ID，用于排序和索引')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # 允许null以支持历史数据
    form_data = db.Column(db.Text, nullable=False)  # JSON格式的表单数据
    result_data = db.Column(db.Text, nullable=False)  # JSON格式的分析结果
    project_name = db.Column(db.String(200), nullable=False, index=True)
    project_description = db.Column(db.Text)
    team_size = db.Column(db.Integer, default=0)
    analysis_type = db.Column(db.String(50), default='ai_analysis')  # ai_analysis, fallback, emergency_fallback
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)

    # 关联用户
    user = db.relationship('User', backref='analysis_results')

    @property
    def created_at_display(self):
        """格式化创建时间显示（UTC+8北京时间）"""
        if self.created_at:
            # 将UTC时间转换为UTC+8（北京时间）
            from datetime import timedelta
            beijing_time = self.created_at + timedelta(hours=8)
            return beijing_time.strftime('%Y年%m月%d日 %H:%M')
        return '未知时间'

    @property
    def analysis_type_display(self):
        """格式化分析类型显示"""
        if self.analysis_type == 'ai_analysis':
            return 'AI深度分析'
        elif self.analysis_type == 'fallback':
            return '基础建议方案'
        return '未知类型'

    def __repr__(self):
        return f'<AnalysisResult {self.id}>'

class ModelConfig(db.Model):
    __tablename__ = 'model_configs'

    id = db.Column(db.Integer, primary_key=True)
    config_name = db.Column(db.String(50), nullable=False, unique=True, index=True)  # 配置名称如 'main_analysis', 'chat', 'fallback'
    model_name = db.Column(db.String(50), nullable=False)  # 模型名称如 'gpt-4o-mini'
    temperature = db.Column(db.Float, default=0.7)  # 温度参数
    max_tokens = db.Column(db.Integer, default=2500)  # 最大token数
    timeout = db.Column(db.Integer, default=45)  # 超时时间（秒）
    is_active = db.Column(db.Boolean, default=True)  # 是否启用
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<ModelConfig {self.config_name}: {self.model_name}>'


    @classmethod
    def set_config(cls, config_name, model_name, temperature=0.7, max_tokens=2500, timeout=45):
        """设置或更新配置"""
        config = cls.query.filter_by(config_name=config_name).first()
        if config:
            config.model_name = model_name
            config.temperature = temperature
            config.max_tokens = max_tokens
            config.timeout = timeout
            config.updated_at = datetime.utcnow()
        else:
            config = cls(
                config_name=config_name,
                model_name=model_name,
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=timeout
            )
            db.session.add(config)

        db.session.commit()
        return config

    @classmethod
    def get_config(cls, config_name, default_model='gpt-4o-mini'):
        """获取指定配置，如果不存在则返回默认值"""
        config = cls.query.filter_by(config_name=config_name, is_active=True).first()
        if config:
            return {
                'model': config.model_name,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
                'timeout': config.timeout
            }
        return {
            'model': default_model,
            'temperature': 0.7,
            'max_tokens': 2500,
            'timeout': 45
        }


class FormSubmission(db.Model):
    """表单提交记录模型 - 用于临时存储用户提交的表单数据"""
    __tablename__ = 'form_submissions'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_name = db.Column(db.String(200), nullable=False, index=True)
    project_description = db.Column(db.Text)
    key_persons_data = db.Column(db.Text, nullable=False)  # JSON格式的关键人物数据
    form_data_complete = db.Column(db.Text, nullable=False)  # 完整表单数据JSON
    status = db.Column(db.String(50), default='submitted')  # submitted, processing, completed, error
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联用户
    user = db.relationship('User', backref='form_submissions')

    def __repr__(self):
        return f'<FormSubmission {self.id}: {self.project_name}>'