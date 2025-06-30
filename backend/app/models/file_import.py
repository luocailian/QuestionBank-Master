"""
文件导入记录模型
"""
from datetime import datetime
from app import db

class FileImport(db.Model):
    """文件导入记录模型"""
    __tablename__ = 'file_imports'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'))
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.Enum('pdf', 'docx', 'xlsx', 'json'), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'), default='pending')
    questions_imported = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'status': self.status,
            'total_questions': self.questions_imported,
            'success_count': self.questions_imported,
            'error_count': 0 if self.status == 'completed' else None,
            'error_details': self.error_message,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
    
    def mark_completed(self, questions_count=0):
        """标记为完成"""
        self.status = 'completed'
        self.questions_imported = questions_count
        self.completed_at = datetime.utcnow()
    
    def mark_failed(self, error_message):
        """标记为失败"""
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = datetime.utcnow()
    
    def __repr__(self):
        return f'<FileImport {self.filename}>'
