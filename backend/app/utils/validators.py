"""
验证工具函数
"""
import re
from typing import Optional

def validate_email(email: str) -> bool:
    """验证邮箱格式"""
    if not email or not isinstance(email, str):
        return False
    
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password(password: str) -> bool:
    """验证密码强度"""
    if not password or not isinstance(password, str):
        return False
    
    # 基本长度要求
    if len(password) < 6:
        return False
    
    # 可以添加更多密码强度要求
    # 例如：必须包含字母和数字
    # has_letter = bool(re.search(r'[a-zA-Z]', password))
    # has_digit = bool(re.search(r'\d', password))
    # return has_letter and has_digit
    
    return True

def validate_username(username: str) -> bool:
    """验证用户名格式"""
    if not username or not isinstance(username, str):
        return False
    
    # 长度检查
    if len(username) < 3 or len(username) > 50:
        return False
    
    # 只允许字母、数字、下划线和连字符
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, username))

def validate_phone(phone: str) -> bool:
    """验证手机号格式"""
    if not phone or not isinstance(phone, str):
        return False
    
    # 简单的手机号验证（支持中国手机号）
    pattern = r'^1[3-9]\d{9}$'
    return bool(re.match(pattern, phone))

def validate_url(url: str) -> bool:
    """验证URL格式"""
    if not url or not isinstance(url, str):
        return False
    
    pattern = r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    return bool(re.match(pattern, url))

def validate_tenant_code(code: str) -> bool:
    """验证租户代码格式"""
    if not code or not isinstance(code, str):
        return False
    
    # 租户代码：3-50个字符，只允许字母、数字、下划线和连字符
    if len(code) < 3 or len(code) > 50:
        return False
    
    pattern = r'^[a-zA-Z0-9_-]+$'
    return bool(re.match(pattern, code))

def validate_file_extension(filename: str, allowed_extensions: list) -> bool:
    """验证文件扩展名"""
    if not filename or not isinstance(filename, str):
        return False
    
    if '.' not in filename:
        return False
    
    extension = filename.rsplit('.', 1)[1].lower()
    return extension in [ext.lower() for ext in allowed_extensions]

def validate_file_size(file_size: int, max_size_mb: int = 50) -> bool:
    """验证文件大小"""
    if not isinstance(file_size, int) or file_size < 0:
        return False
    
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes

def sanitize_filename(filename: str) -> str:
    """清理文件名，移除危险字符"""
    if not filename:
        return ''
    
    # 移除路径分隔符和其他危险字符
    dangerous_chars = ['/', '\\', '..', '<', '>', ':', '"', '|', '?', '*']
    for char in dangerous_chars:
        filename = filename.replace(char, '_')
    
    # 限制长度
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        max_name_length = 255 - len(ext) - 1 if ext else 255
        filename = name[:max_name_length] + ('.' + ext if ext else '')
    
    return filename

def validate_json_structure(data: dict, required_fields: list) -> tuple[bool, Optional[str]]:
    """验证JSON数据结构"""
    if not isinstance(data, dict):
        return False, "数据必须是JSON对象"
    
    for field in required_fields:
        if field not in data:
            return False, f"缺少必需字段: {field}"
    
    return True, None

def validate_question_type(question_type: str) -> bool:
    """验证题目类型"""
    valid_types = ['choice', 'true_false', 'qa', 'math', 'programming']
    return question_type in valid_types

def validate_difficulty(difficulty: str) -> bool:
    """验证难度级别"""
    valid_difficulties = ['easy', 'medium', 'hard']
    return difficulty in valid_difficulties

def validate_points(points: int) -> bool:
    """验证分值"""
    return isinstance(points, int) and 1 <= points <= 100

def validate_tags(tags: list) -> bool:
    """验证标签列表"""
    if not isinstance(tags, list):
        return False
    
    if len(tags) > 10:  # 最多10个标签
        return False
    
    for tag in tags:
        if not isinstance(tag, str) or len(tag) > 20:
            return False
    
    return True

def validate_choice_options(options: list) -> tuple[bool, Optional[str]]:
    """验证选择题选项"""
    if not isinstance(options, list):
        return False, "选项必须是列表"
    
    if len(options) < 2:
        return False, "至少需要2个选项"
    
    if len(options) > 10:
        return False, "最多支持10个选项"
    
    keys = []
    for option in options:
        if not isinstance(option, dict):
            return False, "选项必须是对象"
        
        if 'key' not in option or 'text' not in option:
            return False, "选项必须包含key和text字段"
        
        if option['key'] in keys:
            return False, f"选项键重复: {option['key']}"
        
        keys.append(option['key'])
        
        if not option['text'].strip():
            return False, "选项内容不能为空"
    
    return True, None

def validate_ip_address(ip: str) -> bool:
    """验证IP地址格式"""
    if not ip or not isinstance(ip, str):
        return False
    
    # IPv4验证
    ipv4_pattern = r'^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$'
    if re.match(ipv4_pattern, ip):
        return True
    
    # IPv6验证（简化版）
    ipv6_pattern = r'^(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}$'
    if re.match(ipv6_pattern, ip):
        return True
    
    return False
