"""
URL configuration for shuashijuan_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

# 🔒 添加DRF-Spectacular导入，用于生成OpenAPI文档
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # 业务接口大门：凡是以 api/ 开头的，都去 exams.urls 里面找具体房间
    # 比如 /api/exams/ 会找到 ExamViewSet
    path('api/', include('exams.urls')),
    
    # 身份认证大门：也是 api/ 开头，但专门指路到 token
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # 🔒 OpenAPI文档大门：提供自动生成的API文档
    # 前端可以访问这些URL获取最新的API定义
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),  # OpenAPI JSON格式
    path('api/docs/', SpectacularRedocView.as_view(), name='docs'),  # 交互式文档界面
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)