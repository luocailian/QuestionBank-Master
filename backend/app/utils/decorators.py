"""
装饰器工具
"""
from functools import wraps
from flask import current_app, request
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt, verify_jwt_in_request
from app.models import User

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user or not user.is_admin():
            return {'message': '需要管理员权限'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def tenant_required(f):
    """租户权限装饰器 - 确保用户只能访问自己租户的数据"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {'message': '用户不存在'}, 404
        
        # 将当前用户的租户ID添加到请求上下文
        request.current_tenant_id = user.tenant_id
        request.current_user = user
        
        return f(*args, **kwargs)
    return decorated_function

def active_user_required(f):
    """活跃用户装饰器 - 确保用户账户处于活跃状态"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {'message': '用户不存在'}, 404
        
        if not user.is_active:
            return {'message': '账户已被禁用'}, 403
        
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user_id = get_jwt_identity()
            user = User.query.get(current_user_id)
            
            if not user:
                return {'message': '用户不存在'}, 404
            
            if user.role not in roles:
                return {'message': f'需要以下角色之一: {", ".join(roles)}'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def optional_jwt(f):
    """可选JWT装饰器 - 如果提供了token则验证，否则继续执行"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request(optional=True)
            current_user_id = get_jwt_identity()
            if current_user_id:
                user = User.query.get(current_user_id)
                request.current_user = user
            else:
                request.current_user = None
        except Exception:
            request.current_user = None
        
        return f(*args, **kwargs)
    return decorated_function

def rate_limit(max_requests=100, window=3600):
    """简单的速率限制装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 这里可以实现基于Redis的速率限制
            # 暂时跳过实现
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_tenant_access(resource_tenant_id):
    """验证租户访问权限"""
    def decorator(f):
        @wraps(f)
        @tenant_required
        def decorated_function(*args, **kwargs):
            current_tenant_id = getattr(request, 'current_tenant_id', None)
            
            # 管理员可以访问所有租户的数据
            if hasattr(request, 'current_user') and request.current_user.is_admin():
                return f(*args, **kwargs)
            
            # 普通用户只能访问自己租户的数据
            if current_tenant_id != resource_tenant_id:
                return {'message': '无权访问该资源'}, 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_user_action(action_type):
    """用户行为日志装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                result = f(*args, **kwargs)
                
                # 记录用户行为（可以扩展为写入数据库或日志文件）
                if hasattr(request, 'current_user') and request.current_user:
                    current_app.logger.info(
                        f"User {request.current_user.id} performed action: {action_type}"
                    )
                
                return result
            except Exception as e:
                # 记录错误
                if hasattr(request, 'current_user') and request.current_user:
                    current_app.logger.error(
                        f"User {request.current_user.id} failed action: {action_type}, error: {str(e)}"
                    )
                raise
        return decorated_function
    return decorator
