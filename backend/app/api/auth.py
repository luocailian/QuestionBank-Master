"""
认证相关API - 支持多租户
"""
from datetime import datetime, timedelta
from flask import request, current_app
from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import (
    create_access_token, create_refresh_token, jwt_required,
    get_jwt_identity, get_jwt, verify_jwt_in_request
)
from marshmallow import Schema, fields as ma_fields, validate, ValidationError
import re

from app import db
from app.models import User, UserSession, Tenant
from app.utils.decorators import admin_required, tenant_required
from app.utils.validators import validate_email, validate_password

# 创建命名空间
auth_bp = Namespace('auth', description='用户认证相关接口')

# 请求模型
login_model = auth_bp.model('Login', {
    'username': fields.String(required=True, description='用户名或邮箱'),
    'password': fields.String(required=True, description='密码')
})

register_model = auth_bp.model('Register', {
    'username': fields.String(required=True, description='用户名'),
    'email': fields.String(required=True, description='邮箱'),
    'password': fields.String(required=True, description='密码'),
    'tenant_code': fields.String(description='租户代码（可选）'),
    'invite_code': fields.String(description='邀请码（可选）')
})

password_change_model = auth_bp.model('PasswordChange', {
    'old_password': fields.String(required=True, description='当前密码'),
    'new_password': fields.String(required=True, description='新密码')
})

user_profile_model = auth_bp.model('UserProfile', {
    'username': fields.String(description='用户名'),
    'email': fields.String(description='邮箱'),
    'avatar_url': fields.String(description='头像URL')
})

# 响应模型
token_model = auth_bp.model('Token', {
    'access_token': fields.String(description='访问令牌'),
    'refresh_token': fields.String(description='刷新令牌'),
    'user': fields.Raw(description='用户信息')
})

# Marshmallow验证模式
class LoginSchema(Schema):
    username = ma_fields.Str(required=True, validate=validate.Length(min=1, max=50))
    password = ma_fields.Str(required=True, validate=validate.Length(min=6, max=128))
    remember_me = ma_fields.Bool(missing=False)

class RegisterSchema(Schema):
    username = ma_fields.Str(required=True, validate=validate.Length(min=3, max=50))
    email = ma_fields.Email(required=True)
    password = ma_fields.Str(required=True, validate=validate.Length(min=6, max=128))
    tenant_code = ma_fields.Str(missing=None, validate=validate.Length(max=50))
    invite_code = ma_fields.Str(missing=None, validate=validate.Length(max=100))

class PasswordChangeSchema(Schema):
    old_password = ma_fields.Str(required=True, validate=validate.Length(min=6, max=128))
    new_password = ma_fields.Str(required=True, validate=validate.Length(min=6, max=128))

class UserProfileSchema(Schema):
    username = ma_fields.Str(validate=validate.Length(min=3, max=50))
    email = ma_fields.Email()
    avatar_url = ma_fields.Url()

@auth_bp.route('/login')
class Login(Resource):
    @auth_bp.expect(login_model)
    @auth_bp.marshal_with(token_model)
    def post(self):
        """用户登录"""
        try:
            # 验证请求数据
            schema = LoginSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        username = data['username']
        password = data['password']
        
        # 查找用户（支持用户名或邮箱登录）
        user = User.query.filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user or not user.check_password(password):
            return {'message': '用户名或密码错误'}, 401

        if not user.is_active:
            return {'message': '账户已被禁用，请联系管理员'}, 401

        # 更新最后登录时间和IP
        user.last_login = datetime.utcnow()
        user.last_login_ip = request.remote_addr

        # 设置令牌过期时间
        remember_me = data.get('remember_me', False)
        expires_delta = timedelta(days=30) if remember_me else timedelta(hours=24)

        # 生成令牌（包含用户角色和租户信息）
        additional_claims = {
            'role': user.role,
            'tenant_id': user.tenant_id,
            'username': user.username
        }

        access_token = create_access_token(
            identity=str(user.id),  # JWT identity必须是字符串
            expires_delta=expires_delta,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=str(user.id))

        # 记录用户会话
        session = UserSession(
            user_id=user.id,
            access_token_jti=None,  # 暂时设为None，因为JWT还未在上下文中
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', ''),
            expires_at=datetime.utcnow() + expires_delta
        )

        try:
            db.session.add(session)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to save user session: {e}")

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict(),
            'expires_in': int(expires_delta.total_seconds())
        }

@auth_bp.route('/register')
class Register(Resource):
    @auth_bp.expect(register_model)
    @auth_bp.marshal_with(token_model)
    def post(self):
        """用户注册"""
        try:
            # 验证请求数据
            schema = RegisterSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400
        
        username = data['username']
        email = data['email']
        password = data['password']
        tenant_code = data.get('tenant_code')
        invite_code = data.get('invite_code')

        # 处理租户信息（多租户支持）
        tenant_id = 'default'  # 默认租户
        if tenant_code:
            tenant = Tenant.query.filter_by(code=tenant_code, is_active=True).first()
            if tenant:
                tenant_id = tenant.id
            else:
                return {'message': '无效的租户代码'}, 400

        # 验证邀请码（如果提供）
        if invite_code:
            # 这里可以添加邀请码验证逻辑
            # 例如：检查邀请码是否有效、是否过期等
            pass

        # 检查用户名是否已存在（在同一租户内）
        if User.query.filter_by(username=username, tenant_id=tenant_id).first():
            return {'message': '用户名已存在'}, 400

        # 检查邮箱是否已存在（在同一租户内）
        if User.query.filter_by(email=email, tenant_id=tenant_id).first():
            return {'message': '邮箱已存在'}, 400

        # 创建新用户
        user = User(
            username=username,
            email=email,
            tenant_id=tenant_id,
            registration_ip=request.remote_addr
        )
        user.set_password(password)

        try:
            db.session.add(user)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to create user: {e}")
            return {'message': '注册失败，请稍后重试'}, 500

        # 生成令牌（包含租户信息）
        additional_claims = {
            'role': user.role,
            'tenant_id': user.tenant_id,
            'username': user.username
        }

        access_token = create_access_token(
            identity=user.id,
            additional_claims=additional_claims
        )
        refresh_token = create_refresh_token(identity=user.id)

        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }

@auth_bp.route('/refresh')
class RefreshToken(Resource):
    @jwt_required(refresh=True)
    def post(self):
        """刷新访问令牌"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        user = User.query.get(current_user_id)

        if not user or not user.is_active:
            return {'message': '用户不存在或已被禁用'}, 401

        # 添加用户信息到token claims
        additional_claims = {
            'role': user.role,
            'tenant_id': user.tenant_id,
            'username': user.username
        }

        access_token = create_access_token(
            identity=str(current_user_id),  # JWT identity必须是字符串
            additional_claims=additional_claims
        )

        return {
            'access_token': access_token
        }

@auth_bp.route('/me')
class CurrentUser(Resource):
    @jwt_required()
    def get(self):
        """获取当前用户信息"""
        current_user_id = int(get_jwt_identity())  # 转换为整数
        user = User.query.get(current_user_id)
        
        if not user:
            return {'message': '用户不存在'}, 404
        
        return {
            'user': user.to_dict(),
            'statistics': user.get_statistics()
        }

    @jwt_required()
    @auth_bp.expect(user_profile_model)
    def put(self):
        """更新用户资料"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return {'message': '用户不存在'}, 404

        try:
            schema = UserProfileSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400

        # 检查用户名是否被其他用户使用
        if 'username' in data and data['username'] != user.username:
            existing_user = User.query.filter_by(
                username=data['username'],
                tenant_id=user.tenant_id
            ).first()
            if existing_user:
                return {'message': '用户名已被使用'}, 400
            user.username = data['username']

        # 检查邮箱是否被其他用户使用
        if 'email' in data and data['email'] != user.email:
            existing_user = User.query.filter_by(
                email=data['email'],
                tenant_id=user.tenant_id
            ).first()
            if existing_user:
                return {'message': '邮箱已被使用'}, 400
            user.email = data['email']

        # 更新头像
        if 'avatar_url' in data:
            user.avatar_url = data['avatar_url']

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to update user profile: {e}")
            return {'message': '更新失败，请稍后重试'}, 500

        return {
            'user': user.to_dict(),
            'message': '资料更新成功'
        }

@auth_bp.route('/change-password')
class ChangePassword(Resource):
    @jwt_required()
    @auth_bp.expect(password_change_model)
    def post(self):
        """修改密码"""
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return {'message': '用户不存在'}, 404

        try:
            schema = PasswordChangeSchema()
            data = schema.load(request.json)
        except ValidationError as err:
            return {'message': '请求参数错误', 'errors': err.messages}, 400

        # 验证当前密码
        if not user.check_password(data['old_password']):
            return {'message': '当前密码错误'}, 400

        # 设置新密码
        user.set_password(data['new_password'])

        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Failed to change password: {e}")
            return {'message': '密码修改失败，请稍后重试'}, 500

        return {'message': '密码修改成功'}

@auth_bp.route('/logout')
class Logout(Resource):
    @jwt_required()
    def post(self):
        """用户登出"""
        current_user_id = get_jwt_identity()
        jti = get_jwt().get('jti')

        # 将当前会话标记为已登出
        if jti:
            try:
                session = UserSession.query.filter_by(
                    user_id=current_user_id,
                    access_token_jti=jti
                ).first()
                if session:
                    session.is_active = False
                    db.session.commit()
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Failed to logout user session: {e}")

        return {'message': '登出成功'}
