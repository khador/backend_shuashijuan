from django.db import models
from django.contrib.auth.models import AbstractUser

class ClassInfo(models.Model):
    """班级信息表"""
    name = models.CharField(max_length=50, verbose_name="班级名称")
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    """自定义用户模型"""
    ROLE_CHOICES = (
        ('admin', '管理员'),
        ('teacher', '教师'),
        ('student', '学生'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student', verbose_name="角色")
    
    # 班级绑定逻辑
    # 学生与班级：一对一 (一个学生只属于一个班级)
    # 教师与班级：多对多 (一个教师带多个班，一个班多个老师)
    classes = models.ManyToManyField(ClassInfo, blank=True, related_name="users", verbose_name="负责/所属班级")

    class Meta:
        verbose_name = "用户"
        verbose_name_plural = verbose_name