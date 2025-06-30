"""
用户答题记录模型
"""
from datetime import datetime
from app import db

class UserAnswer(db.Model):
    """用户答题记录模型"""
    __tablename__ = 'user_answers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'), nullable=False)
    user_answer = db.Column(db.JSON, nullable=False)  # 用户答案
    is_correct = db.Column(db.Boolean, nullable=False)
    score = db.Column(db.Integer, default=0)          # 得分
    time_spent = db.Column(db.Integer, default=0)     # 答题耗时(秒)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'question_id': self.question_id,
            'bank_id': self.bank_id,
            'user_answer': self.user_answer,
            'is_correct': self.is_correct,
            'score': self.score,
            'time_spent': self.time_spent,
            'answered_at': self.answered_at.isoformat() if self.answered_at else None
        }
    
    def __repr__(self):
        return f'<UserAnswer {self.user_id}-{self.question_id}>'
