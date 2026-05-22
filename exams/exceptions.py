"""
Django REST Framework 自定义异常处理器

🔒 用途：
提供更友好的错误信息，提升用户体验

📝 功能：
- 统一错误格式
- 隐藏敏感信息
- 记录错误日志
- 返回详细的错误信息
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger(__name__)

def custom_exception_handler(exc, context):
    """
    🔒 自定义异常处理器
    
    功能说明：
    - 统一所有异常的响应格式
    - 记录错误日志供运维排查
    - 生产环境隐藏敏感信息
    - 开发环境返回详细调试信息
    
    参数：
    - exc: 异常对象
    - context: 上下文信息（包含request等）
    """
    
    # 首先调用DRF默认的异常处理器
    response = exception_handler(exc, context)
    
    # 如果响应不是HTTPResponse，需要自定义处理
    if not isinstance(response, Response):
        return response
    
    # 🎯 自定义错误响应格式
    custom_response_data = {
        'error': True,
        'timestamp': context.get('request').META.get('REQUEST_TIME', '') if context.get('request') else '',
        'status_code': response.status_code
    }
    
    # 根据错误类型添加不同信息
    if hasattr(exc, 'detail'):
        custom_response_data['message'] = exc.detail
    elif hasattr(exc, 'message'):
        custom_response_data['message'] = exc.message
    else:
        custom_response_data['message'] = '服务器处理请求时发生错误'
    
    # 🔍 开发环境返回详细错误，生产环境隐藏
    from django.conf import settings
    if settings.DEBUG:
        custom_response_data['debug_info'] = str(exc)
        custom_response_data['error_type'] = type(exc).__name__
        custom_response_data['traceback'] = str(exc.__traceback__) if hasattr(exc, '__traceback__') else None
    else:
        # 生产环境只返回基本的错误信息
        # 移除可能包含敏感信息的详细信息
        custom_response_data.pop('traceback', None)
    
    # 📊 记录错误日志
    request = context.get('request')
    if request:
        user_info = f"用户: {request.user}" if request.user.is_authenticated else "匿名用户"
        logger.error(
            f"API错误 - {type(exc).__name__}: {str(exc)} | "
            f"请求路径: {request.path} | "
            f"请求方法: {request.method} | "
            f"{user_info} | "
            f"IP地址: {get_client_ip(request)}",
            exc_info=exc
        )
    
    # 构建新的响应
    response.data = custom_response_data
    
    return response

def get_client_ip(request):
    """
    获取客户端IP地址
    
    用途：
    - 记录请求来源
    - 安全审计
    - 防止恶意访问
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    return ip