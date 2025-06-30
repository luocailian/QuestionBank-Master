"""
题目模型
"""
from datetime import datetime
from app import db

class Question(db.Model):
    """题目模型 - 支持多种题型"""
    __tablename__ = 'questions'
    
    id = db.Column(db.Integer, primary_key=True)
    bank_id = db.Column(db.Integer, db.ForeignKey('question_banks.id'), nullable=False)
    type = db.Column(db.Enum('choice', 'true_false', 'qa', 'math', 'programming'), nullable=False)
    title = db.Column(db.Text, nullable=False)
    content = db.Column(db.JSON, nullable=False)  # 题目内容，根据类型不同结构不同
    answer = db.Column(db.JSON, nullable=False)   # 答案
    explanation = db.Column(db.Text)              # 题目解析
    difficulty = db.Column(db.Enum('easy', 'medium', 'hard'), default='medium')
    tags = db.Column(db.JSON)                     # 题目标签
    points = db.Column(db.Integer, default=1)     # 题目分值
    order_index = db.Column(db.Integer, default=0)  # 题目顺序
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关系
    user_answers = db.relationship('UserAnswer', backref='question', lazy='dynamic')
    favorites = db.relationship('UserFavorite', backref='question', lazy='dynamic')
    
    def to_dict(self, include_answer=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'bank_id': self.bank_id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'explanation': self.explanation,
            'difficulty': self.difficulty,
            'tags': self.tags or [],
            'points': self.points,
            'order_index': self.order_index,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if include_answer:
            data['answer'] = self.answer
            
        return data
    
    def check_answer(self, user_answer):
        """检查用户答案是否正确"""
        if self.type == 'choice':
            # 选择题：比较选项索引或选项内容
            correct_answer = self.answer.get('correct_option')
            if isinstance(user_answer, dict):
                user_selected = user_answer.get('selected_option')
            else:
                user_selected = user_answer

            # 处理多选题（正确答案包含多个字符）
            if len(str(correct_answer)) > 1:
                # 多选题：用户答案应该是字符串或列表
                if isinstance(user_selected, list):
                    user_selected = ''.join(sorted(user_selected))
                user_selected = ''.join(sorted(str(user_selected)))
                correct_answer = ''.join(sorted(str(correct_answer)))
                return user_selected == correct_answer
            else:
                # 单选题
                return str(user_selected) == str(correct_answer)
            
        elif self.type == 'true_false':
            # 判断题：比较布尔值
            # 兼容不同的答案格式
            correct_answer = self.answer.get('is_true') or self.answer.get('correct_answer')
            if isinstance(user_answer, dict):
                user_bool = user_answer.get('answer') or user_answer.get('is_true')
            else:
                user_bool = user_answer

            # 转换为布尔值进行比较
            if isinstance(user_bool, str):
                user_bool = user_bool.lower() in ['true', '1', 'yes', '是', '对', '正确']

            return bool(user_bool) == bool(correct_answer)
            
        elif self.type == 'qa':
            # 问答题：关键词匹配或完全匹配
            # 兼容不同的答案格式
            correct_answers = self.answer.get('keywords', [])
            sample_answer = self.answer.get('sample_answer', '')

            if isinstance(user_answer, dict):
                user_text = user_answer.get('answer', '').lower()
            else:
                user_text = str(user_answer).lower()

            # 如果没有关键词但有示例答案，从示例答案中提取关键词
            if not correct_answers and sample_answer:
                # 简单的关键词提取（实际应用中可以使用更复杂的NLP方法）
                import re
                keywords = re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', sample_answer)
                correct_answers = [kw for kw in keywords if len(kw) > 1]

            # 检查是否包含关键词
            if correct_answers:
                for keyword in correct_answers:
                    if keyword.lower() in user_text:
                        return True

            # 如果没有关键词，进行简单的相似度匹配
            if sample_answer:
                # 简单的相似度检查（包含主要词汇）
                sample_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', sample_answer.lower()))
                user_words = set(re.findall(r'[\u4e00-\u9fff]+|[a-zA-Z]+', user_text))
                if sample_words and user_words:
                    overlap = len(sample_words & user_words)
                    return overlap >= min(3, len(sample_words) // 2)

            return False
            
        elif self.type == 'math':
            # 数学题：数值比较（考虑精度）
            correct_answer = self.answer.get('result')
            if isinstance(user_answer, dict):
                user_result = user_answer.get('result') or user_answer.get('answer')
            else:
                user_result = user_answer

            try:
                # 处理字符串中的数字提取
                if isinstance(user_result, str):
                    import re
                    numbers = re.findall(r'-?\d+\.?\d*', user_result)
                    if numbers:
                        user_result = float(numbers[0])

                correct_num = float(correct_answer)
                user_num = float(user_result)

                # 根据数值大小调整精度
                if abs(correct_num) < 1:
                    tolerance = 0.001
                elif abs(correct_num) < 100:
                    tolerance = 0.01
                else:
                    tolerance = abs(correct_num) * 0.001

                return abs(user_num - correct_num) <= tolerance
            except (ValueError, TypeError):
                return False
                
        elif self.type == 'programming':
            # 编程题：需要运行测试用例（这里简化处理）
            # 实际应用中需要代码执行环境
            return False  # 暂时返回False，需要专门的代码执行模块
            
        return False
    
    def get_statistics(self):
        """获取题目统计信息"""
        total_attempts = self.user_answers.count()
        correct_attempts = self.user_answers.filter_by(is_correct=True).count()
        
        accuracy_rate = 0
        if total_attempts > 0:
            accuracy_rate = round((correct_attempts / total_attempts) * 100, 2)
        
        avg_time = 0
        if total_attempts > 0:
            total_time = sum([answer.time_spent for answer in self.user_answers])
            avg_time = round(total_time / total_attempts, 2)
        
        return {
            'total_attempts': total_attempts,
            'correct_attempts': correct_attempts,
            'accuracy_rate': accuracy_rate,
            'avg_time': avg_time,
            'favorites_count': self.favorites.count()
        }
    
    @staticmethod
    def create_from_dict(data):
        """从字典创建题目"""
        question = Question(
            bank_id=data.get('bank_id'),
            type=data.get('type'),
            title=data.get('title'),
            content=data.get('content'),
            answer=data.get('answer'),
            explanation=data.get('explanation'),
            difficulty=data.get('difficulty', 'medium'),
            tags=data.get('tags'),
            points=data.get('points', 1),
            order_index=data.get('order_index', 0)
        )
        return question
    
    def __repr__(self):
        return f'<Question {self.id}: {self.title[:50]}>'
