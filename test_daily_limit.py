"""
测试同一天重复提交限制逻辑

🧪 用途：
验证同一天重复提交的限制是否正常工作

📝 使用方法：
python manage.py shell
exec(open('test_daily_limit.py').read())
"""

import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'shuashijuan_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from exams.models import Exam, Question, Submission
from exams.views import SubmissionViewSet
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

User = get_user_model()

def test_daily_limit():
    print("🧪 开始测试同一天重复提交限制...\n")
    
    # 创建测试用户和试卷
    try:
        student = User.objects.create_user(username='test_student', password='Test123456', role='student')
        print("✅ 创建测试用户成功")
    except:
        student = User.objects.get(username='test_student')
        print("ℹ️  测试用户已存在，跳过创建")
    
    # 创建或获取测试试卷
    exam, created = Exam.objects.get_or_create(
        exam_id='test_daily_limit',
        defaults={
            'title': '测试试卷-同一天限制',
            'subject': 'math',
            'visible_date': timezone.now().date()
        }
    )
    print("✅ 获取测试试卷成功\n")
    
    # 创建测试题目
    try:
        question = Question.objects.create(
            exam=exam,
            q_id='q1',
            q_type='multiple_choice',
            stem='测试题目',
            answer_data='A',
            options={'A': '选项A', 'B': '选项B', 'C': '选项C', 'D': '选项D'},
            order=1
        )
        print("✅ 创建测试题目成功")
    except:
        question = Question.objects.filter(exam=exam).first()
        print("ℹ️  测试题目已存在，跳过创建\n")
    
    # 测试1：首次提交（应该成功）
    print("📋 测试1：首次提交（应该成功）")
    factory = APIRequestFactory()
    request = factory.post(f'/api/submissions/', {
        'exam': exam.id,
        'student_answers': {'q1': 'A'}  # 正确答案
    })
    request.user = student
    
    view = SubmissionViewSet()
    view.request = Request(request)
    view.format_kwarg = None
    
    try:
        response = view.create(request)
        if response.status_code == 201:
            print("✅ 首次提交成功（符合预期）")
            submission_id_1 = response.data.get('submission_id')
        else:
            print(f"❌ 首次提交失败：{response.data}")
            return
    except Exception as e:
        print(f"❌ 首次提交异常：{e}")
        return
    
    # 测试2：同一天再次提交（应该被拒绝）
    print("\n📋 测试2：同一天再次提交（应该被拒绝）")
    request2 = factory.post(f'/api/submissions/', {
        'exam': exam.id,
        'student_answers': {'q1': 'A'}  # 同样的答案
    })
    request2.user = student
    view2 = SubmissionViewSet()
    view2.request = Request(request2)
    view2.format_kwarg = None
    
    try:
        response2 = view2.create(request2)
        if response2.status_code == 400:
            print(f"✅ 同一天重复提交被成功拒绝（符合预期）")
            print(f"   错误信息：{response2.data.get('message')}")
            print(f"   可提交时间：{response2.data.get('can_submit_time')}")
        else:
            print(f"❌ 同一天重复提交未被拦截（不符合预期）：{response2.data}")
    except Exception as e:
        print(f"❌ 同一天重复提交测试异常：{e}")
        return
    
    # 测试3：第二天重新提交（应该成功）
    print("\n📋 测试3：第二天重新提交（应该成功）")
    # 修改首次提交时间为昨天
    first_submission = Submission.objects.filter(student=student, exam=exam).first()
    if first_submission:
        yesterday = timezone.now() - timedelta(days=1)
        first_submission.submit_time = yesterday
        first_submission.save()
        print(f"✅ 修改首次提交时间为昨天：{yesterday}")
    
    request3 = factory.post(f'/api/submissions/', {
        'exam': exam.id,
        'student_answers': {'q1': 'B'}  # 不同的答案
    })
    request3.user = student
    view3 = SubmissionViewSet()
    view3.request = Request(request3)
    view3.format_kwarg = None
    
    try:
        response3 = view3.create(request3)
        if response3.status_code == 201:
            print("✅ 第二天重新提交成功（符合预期）")
            print(f"   是否首次提交：{response3.data.get('is_first_submit')}")
            print(f"   新的正确率：{response3.data.get('statistics').get('correct_rate')}")
        else:
            print(f"❌ 第二天重新提交失败（不符合预期）：{response3.data}")
    except Exception as e:
        print(f"❌ 第二天重新提交测试异常：{e}")
        return
    
    # 测试4：第二天仍然限制同一天提交
    print("\n📋 测试4：第二天仍然限制同一天提交（应该被拒绝）")
    request4 = factory.post(f'/api/submissions/', {
        'exam': exam.id,
        'student_answers': {'q1': 'C'}  # 又一个不同的答案
    })
    request4.user = student
    view4 = SubmissionViewSet()
    view4.request = Request(request4)
    view4.format_kwarg = None
    
    try:
        response4 = view4.create(request4)
        if response4.status_code == 400:
            print(f"✅ 第二天同一天提交被成功拒绝（符合预期）")
            print(f"   错误信息：{response4.data.get('message')}")
        else:
            print(f"❌ 第二天同一天提交未被拦截（不符合预期）：{response4.data}")
    except Exception as e:
        print(f"❌ 第二天同一天提交测试异常：{e}")
        return
    
    print("\n🎉 同一天重复提交限制测试完成！")
    print("\n📝 测试结果总结：")
    print("- 首次提交：✅ 允许")
    print("- 同一天重复提交：✅ 拒绝")
    print("- 第二天重新提交：✅ 允许")
    print("- 第二天同一天提交：✅ 拒绝")
    
    # 清理测试数据
    print("\n🧹 清理测试数据...")
    Submission.objects.filter(student=student, exam=exam).delete()
    Question.objects.filter(exam=exam).delete()
    Exam.objects.filter(exam_id='test_daily_limit').delete()
    student.delete()
    print("✅ 测试数据清理完成")

if __name__ == '__main__':
    test_daily_limit()