"""
API模块
"""
from .auth import auth_bp
from .users import users_bp
from .banks import banks_bp
from .questions import questions_bp
from .files import files_bp
from .exams import exams_bp

__all__ = ['auth_bp', 'users_bp', 'banks_bp', 'questions_bp', 'files_bp', 'exams_bp']
