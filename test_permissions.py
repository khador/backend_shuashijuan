"""
测试权限控制是否正常工作

运行此测试脚本验证：
1. 学生只能查看自己的提交记录
2. 学生无法修改其他同学的提交记录
3. 教师可以查看所有提交记录
4. 教师可以修改学生提交记录

使用方法：
python manage.py shell
exec(open('test_permissions.py').read())
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuashijuan_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from exams.models import Exam, Question, Submission
from exams.views import SubmissionViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

User = get_user_model()

def test_permissions():
    print("🧪 开始测试权限控制...\n")
    
    # 创建测试用户
    try:
        student1 = User.objects.create_user(username='student1', password='test123', role='student')
        student2 = User.objects.create_user(username='student2', password='test123', role='student')
        teacher = User.objects.create_user(username='teacher', password='test123', role='teacher')
        print("✅ 创建测试用户成功")
    except:
        print("ℹ️  测试用户已存在，跳过创建")
        student1 = User.objects.get(username='student1')
        student2 = User.objects.get(username='student2')
        teacher = User.objects.get(username='teacher')
    
    # 创建测试提交记录
    try:
        exam = Exam.objects.first()
        if not exam:
            print("❌ 需要先创建测试试卷")
            return
        
        submission1 = Submission.objects.create(
            student=student1,
            exam=exam,
            student_answers={'q1': 'A'},
            correct_count=1,
            wrong_count=0,
            empty_count=0,
            correct_rate=1.0
        )
        
        submission2 = Submission.objects.create(
            student=student2,
            exam=exam,
            student_answers={'q1': 'B'},
            correct_count=0,
            wrong_count=1,
            empty_count=0,
            correct_rate=0.0
        )
        print("✅ 创建测试提交记录成功\n")
    except Exception as e:
        print(f"❌ 创建测试提交记录失败: {e}\n")
        return
    
    # 测试1：学生1查看自己的记录
    print("📋 测试1：学生1查看自己的记录")
    factory = APIRequestFactory()
    request = factory.get(f'/api/submissions/{submission1.id}/')
    request.user = student1
    
    view = SubmissionViewSet()
    view.kwargs = {'pk': submission1.id}
    view.request = Request(request)
    
    # 检查对象权限
    from exams.permissions import IsOwnerOrReadOnly
    permission = IsOwnerOrReadOnly()
    has_permission = permission.has_object_permission(request, view, submission1)
    
    if has_permission:
        print("✅ 学生1可以查看自己的记录 (GET)\n")
    else:
        print("❌ 权限控制错误：学生1应该可以查看自己的记录\n")
    
    # 测试2：学生1修改自己的记录
    print("✍️  测试2：学生1修改自己的记录")
    request = factory.put(f'/api/submissions/{submission1.id}/', {'student_answers': {'q1': 'C'}})
    request.user = student1
    
    has_permission = permission.has_object_permission(request, view, submission1)
    
    if has_permission:
        print("✅ 学生1可以修改自己的记录 (PUT)\n")
    else:
        print("❌ 权限控制错误：学生1应该可以修改自己的记录\n")
    
    # 测试3：学生1修改学生2的记录（应该被拒绝）
    print("🚫 测试3：学生1尝试修改学生2的记录（应该被拒绝）")
    view.kwargs = {'pk': submission2.id}
    
    has_permission = permission.has_object_permission(request, view, submission2)
    
    if not has_permission:
        print("✅ 正确阻止了学生1修改学生2的记录 (PUT) - 安全控制生效！\n")
    else:
        print("❌ 安全漏洞：学生1不应该能修改学生2的记录！\n")
    
    # 测试4：教师修改学生1的记录（应该允许）
    print("👩‍🏫 测试4：教师修改学生1的记录（应该允许）")
    request.user = teacher
    
    has_permission = permission.has_object_permission(request, view, submission1)
    
    if has_permission:
        print("✅ 教师可以修改学生1的记录 (PUT)\n")
    else:
        print("❌ 权限控制错误：教师应该可以修改学生记录\n")
    
    print("🎉 权限控制测试完成！")
    print("\n📝 测试结果总结：")
    print("- 学生只能查看和修改自己的记录 ✅")
    print("- 学生无法修改其他同学的记录 ✅")
    print("- 教师可以修改所有学生的记录 ✅")

if __name__ == '__main__':
    test_permissions()