from datetime import datetime

# 使用延迟导入避免循环导入
def get_db():
    from app import db
    return db

# 定义模型时使用字符串表名，避免直接继承
class KnowledgeItem:
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