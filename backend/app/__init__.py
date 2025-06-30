"""
Flask应用工厂函数
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_restx import Api

from config import config

# 初始化扩展
db = SQLAlchemy()
migrate = Migrate()
cors = CORS()
jwt = JWTManager()

def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    
    # 加载配置
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    cors.init_app(app, origins=app.config['CORS_ORIGINS'])
    jwt.init_app(app)

    # 注册JWT回调
    register_jwt_callbacks(jwt)
    
    # 创建API实例
    api = Api(
        app,
        version='1.0',
        title='QuestionBank Master API',
        description='智能题库系统API文档',
        doc='/api/docs/',
        prefix='/api/v1'
    )
    
    # 注册蓝图
    from app.api import auth_bp, users_bp, banks_bp, questions_bp, files_bp, exams_bp

    # 注册API命名空间
    api.add_namespace(auth_bp, path='/auth')
    api.add_namespace(users_bp, path='/users')
    api.add_namespace(banks_bp, path='/banks')
    api.add_namespace(questions_bp, path='/questions')
    api.add_namespace(files_bp, path='/files')
    api.add_namespace(exams_bp, path='/exams')
    
    # 注册错误处理器
    register_error_handlers(app)
    
    # 注册JWT回调
    register_jwt_callbacks(jwt)

    # 注册CLI命令
    from app.commands import register_commands
    register_commands(app)

    return app

def register_error_handlers(app):
    """注册错误处理器"""
    
    @app.errorhandler(400)
    def bad_request(error):
        return {'message': '请求参数错误', 'error': str(error)}, 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        return {'message': '未授权访问', 'error': str(error)}, 401
    
    # 添加健康检查端点
    @app.route('/health')
    def health_check():
        return {'status': 'healthy', 'message': 'QuestionBank Master API is running'}

    @app.route('/api/v1/health')
    def api_health_check():
        return {'status': 'healthy', 'message': 'QuestionBank Master API v1 is running'}

    @app.errorhandler(403)
    def forbidden(error):
        return {'message': '禁止访问', 'error': str(error)}, 403

    @app.errorhandler(404)
    def not_found(error):
        return {'message': '资源不存在', 'error': str(error)}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'message': '服务器内部错误', 'error': str(error)}, 500

def register_jwt_callbacks(jwt):
    """注册JWT回调函数"""

    @jwt.user_identity_loader
    def user_identity_lookup(user):
        """用户身份加载器"""
        return str(user.id) if hasattr(user, 'id') else str(user)

    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        """用户查找回调"""
        identity = jwt_data["sub"]
        # identity现在是字符串，需要转换为整数
        try:
            user_id = int(identity)
            from app.models import User
            return User.query.filter_by(id=user_id).one_or_none()
        except (ValueError, TypeError):
            return None

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return {'message': 'Token已过期'}, 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return {'message': 'Token无效'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return {'message': '缺少Token'}, 401
