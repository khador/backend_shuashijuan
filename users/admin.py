from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ClassInfo

class CustomUserAdmin(UserAdmin):
    # 将自定义的 role 和 classes 字段加入到后台编辑页面
    fieldsets = UserAdmin.fieldsets + (
        ('角色与班级信息', {'fields': ('role', 'classes')}),
    )
    # 列表页展示的字段
    list_display = ('username', 'role', 'is_staff', 'is_active')
    # 多对多字段的左右穿梭框 UI
    filter_horizontal = ('classes',)

admin.site.register(User, CustomUserAdmin)
admin.site.register(ClassInfo)