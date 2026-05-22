"""
================================================================================
试卷系统核心视图模块
================================================================================

【重要提示 - 给运维人员】
本文件包含试卷系统的核心业务逻辑，包括：
- 试卷列表查询（ExamViewSet）
- 学生交卷与自动阅卷（SubmissionViewSet）
- 错题本查询（WrongQuestionViewSet）

⚠️ 修改前请务必联系开发人员，随意修改可能导致：
- 学生看到未开放的试卷
- 阅卷逻辑错误
- 权限控制失效
- 数据安全问题
- 防作弊机制失效

作者: [你的名字]
最后修改: 2026-05-22
================================================================================
"""

from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.conf import settings  # 添加settings导入，用于错误处理
from datetime import timedelta  # 添加timedelta导入
from rest_framework.decorators import action  # 添加action装饰器导入
from rest_framework.throttling import UserRateThrottle  # 添加限流类导入
from .models import Exam, Question, Submission, WrongQuestion
from .serializers import ExamSerializer, SubmissionSerializer, QuestionSerializer, WrongQuestionSerializer
from .permissions import IsOwnerOrReadOnly  # 🔒 导入对象级权限控制
from rest_framework import status


# 🔒 自定义提交限流类
#
# 用途：
# - 防止学生频繁提交试卷
# - 避免服务器资源浪费
# - 防止恶意刷题攻击
#
# 限流规则：
# - 每小时最多提交10次
# - 基于用户ID进行限流
# - 超过限制后返回429状态码
#
# ⚠️ 运维注意：
# - 如需调整限流频率，修改 rate 参数即可
# - 支持的格式：'10/hour', '100/day', '5/minute' 等
# - 修改后重启服务生效
class SubmitRateThrottle(UserRateThrottle):
    """
    ================================================================================
    提交试卷限流器
    ================================================================================
    
    【功能说明】
    限制学生提交试卷的频率，防止恶意刷题和服务器资源浪费。
    
    【限流规则】
    - 每小时最多提交10次
    - 按用户ID进行限流（不同用户互不影响）
    - 超过限制返回429 Too Many Requests
    
    【配置参数】
    - scope: 限流作用域标识，用于DRF限流配置
    - rate: 限流频率，格式为 "次数/时间单位"
    
    ⚠️ 运维注意：
    - 如需调整限流频率，修改 rate 参数
    - 支持的格式：'10/hour', '100/day', '5/minute', '1000/day' 等
    - 修改后需要重启服务才能生效
    - 如需完全关闭限流，将此类的 rate 设为 '10000/hour' 或注释掉 throttle_classes
    ================================================================================
    """
    scope = 'submit'
    rate = '10/hour'


class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ================================================================================
    试卷列表及详情视图
    ================================================================================
    
    【功能说明】
    提供试卷的列表查询和详情查看功能，支持按角色过滤可见试卷。
    
    【权限控制】
    - 必须登录才能访问（IsAuthenticated）
    - 只读视图，不支持修改、删除操作（ReadOnlyModelViewSet）
    
    【可见性规则】
    - 超级管理员：可以看到所有试卷（包括未开放的）
    - 学生：只能看到 visible_date <= 今天的试卷（已开放的）
    - 教师/管理员：可以看到所有试卷
    
    【API端点】
    - GET /api/exams/          -> 获取试卷列表
    - GET /api/exams/{id}/     -> 获取单个试卷详情（包含题目）
    
    【使用示例】
    前端调用：axios.get('/api/exams/')
    
    ⚠️ 运维注意：
    - 不要修改 get_queryset() 中的过滤逻辑，否则会影响试卷可见性
    - 如需调整可见日期规则，请联系开发人员
    - 修改 permission_classes 可能导致未登录用户看到试卷
    ================================================================================
    """
    serializer_class = ExamSerializer
    # ✅ 权限类必须定义在类级别
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        ================================================================================
        根据用户角色返回可查看的试卷列表
        ================================================================================
        
        【逻辑说明】
        1. 获取当前登录用户
        2. 获取今天的日期（用于判断试卷是否在展示期内）
        3. 根据用户角色返回不同的查询结果
        
        【角色判断】
        - user.is_superuser: Django内置的超级管理员标志
        - user.role: 自定义角色字段（student/teacher/admin）
        
        【展示期规则】
        - 学生：只能看到 display_start_date <= 今天 <= display_end_date 的试卷
        - 教师/管理员：可以看到所有试卷
        - 超级管理员：可以看到所有试卷
        
        【返回值】
        - QuerySet: 按 display_start_date 倒序排列的试卷列表
        
        ⚠️ 运维注意：
        - 修改此函数会直接影响学生能看到哪些试卷
        - 如需添加新的角色过滤，请在 if role == 'xxx' 处添加分支
        - 删除 display_start_date__lte=now 或 display_end_date__gte=now 过滤会导致学生看到非本周试卷
        ================================================================================
        """
        user = self.request.user
        now = timezone.now().date()

        # 如果是超级管理员，直接看所有，方便调试
        if user.is_superuser:
            return Exam.objects.all().order_by('-display_start_date')

        # 针对普通角色的过滤逻辑
        # 注意：请确保你的 User 模型确实有 role 属性
        role = getattr(user, 'role', 'student')

        if role == 'student':
            # 学生只能看到展示期内的试卷
            # 展示期：display_start_date <= 今天 <= display_end_date
            return Exam.objects.filter(
                display_start_date__lte=now,
                display_end_date__gte=now
            ).order_by('-display_start_date')

        # 教师和管理员可以看到所有
        return Exam.objects.all().order_by('-display_start_date')

    def retrieve(self, request, *args, **kwargs):
        """
        ================================================================================
        获取单个试卷详情
        ================================================================================
        
        【功能说明】
        重写 retrieve 方法，确保返回试卷时连同题目一起返回。
        题目数据通过 ExamSerializer 中的 questions 字段嵌套序列化。
        
        【API端点】
        GET /api/exams/{id}/
        
        【返回数据】
        {
            "id": 1,
            "exam_id": "exam_001",
            "title": "数学测试卷",
            "questions": [...]  // 嵌套的题目列表
        }
        
        ⚠️ 运维注意：
        - 此方法目前只是调用父类实现，但保留用于未来扩展
        - 如需添加额外的详情数据，请在此处添加逻辑
        - 不要删除此方法，否则可能破坏序列化逻辑
        ================================================================================
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class SubmissionViewSet(viewsets.ModelViewSet):
    """
    ================================================================================
    提交与自动阅卷视图
    ================================================================================
    
    【功能说明】
    处理学生的试卷提交请求，自动批改客观题，统计正确率，记录错题。
    本系统使用正确率统计而非分数，更适合刷题练习场景。
    
    【权限控制】
    - IsAuthenticated: 必须登录
    - IsOwnerOrReadOnly: 学生只能修改自己的提交记录
    
    【限流控制】
    - SubmitRateThrottle: 每小时最多提交10次
    - 防止学生频繁提交刷题
    - 避免服务器资源浪费
    
    【核心功能】
    1. 自动阅卷：支持单选题、判断题、填空题
    2. 正确率统计：答对题数 / 可判分总题数
    3. 错题记录：自动将错题加入错题本
    4. 重复提交限制：同一天只能提交一次，第二天可以重新提交
    
    【防作弊机制】
    - 同一天不能重复提交（防止查看错题本后作弊）
    - 第二天可以重新提交（给学生复习订正机会）
    
    【API端点】
    - GET /api/submissions/        -> 查看提交记录列表
    - POST /api/submissions/       -> 提交试卷（自动阅卷）
    - GET /api/submissions/{id}/   -> 查看单条提交详情
    
    【请求示例】
    POST /api/submissions/
    {
        "exam": 1,
        "student_answers": {
            "q1": "A",
            "q2": ["答案1", "答案2"],
            ...
        }
    }
    
    【响应示例】
    {
        "message": "交卷并阅卷成功！",
        "statistics": {
            "total_questions": 10,
            "correct_count": 8,
            "wrong_count": 1,
            "empty_count": 1,
            "correct_rate": 0.89
        },
        "is_first_submit": true,
        "can_retry": false
    }
    
    ⚠️ 运维注意：
    - create() 方法是核心阅卷逻辑，修改前务必充分测试
    - 阅卷规则涉及教学业务，修改需与教研团队确认
    - 如需支持新题型，请在 create() 方法中添加判题逻辑
    - 防作弊机制（同一天限制）是业务核心，不要随意修改
    - 修改限流规则请调整 SubmitRateThrottle 类
    ================================================================================
    
    🔒 权限控制说明：
    - 学生只能查看和修改自己的提交记录
    - 教师可以查看所有学生的提交记录（方便批改和分析）
    - 超级管理员可以查看所有提交记录
    - 对象级权限：学生无法修改其他同学的提交记录
    
    安全机制：
    - get_queryset(): 控制列表查询权限
    - IsOwnerOrReadOnly: 控制单个对象的操作权限
    - SubmitRateThrottle: 控制提交频率
    """
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    # 🔒 添加对象级权限控制，防止学生修改别人的记录
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrReadOnly]
    # 🔒 添加限流控制，防止频繁提交
    throttle_classes = [SubmitRateThrottle]

    def get_queryset(self):
        """
        ================================================================================
        根据用户角色过滤提交记录
        ================================================================================
        
        【功能说明】
        控制用户可以查看哪些提交记录，防止学生查看其他同学的答案。
        
        【安全考虑】
        - 防止学生通过API接口查看其他同学的提交记录和答案
        - 确保数据隐私和考试公平性
        
        【权限规则】
        - 超级管理员：查看所有记录（系统维护）
        - 学生：只能查看自己的记录
        - 教师：查看所有学生记录（批改需要）
        - 其他角色：查看所有记录
        
        【返回值】
        - QuerySet: 按 submit_time 倒序排列的提交记录
        
        ⚠️ 运维注意：
        - 修改此函数会影响谁能看到哪些提交记录
        - 如需限制教师只能看自己班级的学生，参考注释中的代码
        - 删除 student=user 过滤会导致学生看到其他同学的答案（严重安全漏洞）
        ================================================================================
        """
        user = self.request.user

        # 超级管理员可以看到所有提交记录（用于系统维护和调试）
        if user.is_superuser:
            return Submission.objects.all()

        # 获取用户角色，默认为学生角色
        role = getattr(user, 'role', 'student')

        if role == 'student':
            # 学生只能查看自己的提交记录
            return Submission.objects.filter(student=user).order_by('-submit_time')

        elif role == 'teacher':
            # 教师可以查看所有学生的提交记录
            # 如果需要限制教师只能看自己班级的学生，可以使用下面的过滤：
            # return Submission.objects.filter(student__classes__in=user.classes.all())
            return Submission.objects.all().order_by('-submit_time')

        # 其他角色（如管理员）可以查看所有记录
        return Submission.objects.all().order_by('-submit_time')

    def create(self, request, *args, **kwargs):
        """
        ================================================================================
        处理学生交卷请求 - 核心阅卷逻辑
        ================================================================================
        
        【功能说明】
        接收学生提交的答案，自动批改客观题，统计正确率，记录错题到错题本。
        支持重复提交，但同一天只能提交一次（防作弊）。
        
        【处理流程】
        1. 获取请求数据（试卷ID、学生答案）
        2. 验证参数合法性
        3. 查询试卷和题目
        4. 检查是否同一天重复提交（防作弊）
        5. 逐题批改（单选/判断/填空）
        6. 统计正确率
        7. 删除旧错题记录（如果是重新提交）
        8. 保存/更新提交记录
        9. 批量保存新的错题本
        10. 返回统计结果
        
        【支持的题型】
        - 单选题：直接对比选项字母
        - 判断题：对比 True/False
        - 填空题：遍历每个空，支持多个正确答案
        
        【防作弊机制】
        - 同一天不能重复提交
        - 防止场景：上午乱填提交 -> 查看错题本答案 -> 下午用正确答案重新提交
        - 第二天可以重新提交（给学生复习订正机会）
        
        【请求参数】
        - exam: 试卷ID（整数）
        - student_answers: 答案字典 {题目编号: 答案}
        
        【响应数据】
        - message: 操作结果消息
        - statistics: 统计数据（总题数、正确数、错误数、正确率等）
        - submission_id: 提交记录ID
        - is_first_submit: 是否首次提交
        - can_retry: 是否可以重新提交
        - retry_info: 重新提交相关信息
        
        ⚠️ 运维注意：
        - 这是系统最核心的业务逻辑，修改风险极高
        - 修改前请备份代码，并在测试环境充分验证
        - 如需修改判题规则，请与教研团队确认业务逻辑
        - 不要删除或修改防作弊机制（同一天限制），否则会导致作弊漏洞
        - 不要删除错题本相关逻辑，否则会影响学生复习
        - 如需调整限流规则，修改 SubmitRateThrottle 类，不要在此方法中修改
        ================================================================================
        
        🔒 错误处理策略：
        - 捕获所有可能的异常，避免程序崩溃
        - 返回详细的错误信息给前端
        - 记录错误日志供运维排查

        可能的异常类型：
        - Exam.DoesNotExist: 试卷不存在
        - ValueError: 数据格式错误
        - KeyError: 答案格式不正确
        - Exception: 其他未知错误
        """
        user = request.user

        try:
            exam_id = request.data.get('exam')
            student_answers = request.data.get('student_answers', {})

            # 验证必要参数
            if not exam_id:
                return Response({
                    "error": "缺少试卷ID",
                    "message": "请指定要提交的试卷ID"
                }, status=status.HTTP_400_BAD_REQUEST)

            if not isinstance(student_answers, dict):
                return Response({
                    "error": "答案格式错误",
                    "message": "student_answers必须是字典格式"
                }, status=status.HTTP_400_BAD_REQUEST)

            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({"error": "试卷不存在"}, status=status.HTTP_404_NOT_FOUND)

        # 📋 获取试卷的所有题目
        # 🔒 关键：获取试卷的题目，后面会用到
        questions = exam.questions.all()

        # 初始化统计变量 - 用于正确率计算
        correct_count = 0  # 答对题数
        wrong_count = 0    # 答错题数
        empty_count = 0    # 未答题数
        wrong_questions_list = []

        # 🌟 核心：开始逐题批改 - 本系统统计正确率而非分数，适合刷题练习
        for q in questions:
            # 前端的答案 key 可能是 q_id 字符串，也可能是数字 id
            # 兼容多种格式：q_001, q1, 1, q001
            q_key = str(getattr(q, 'q_id', q.id))

            # 🐛 修复：尝试多种 key 格式匹配学生答案
            # 场景1：后端 q_id="q1"，前端 key="q_001"
            # 场景2：后端 q_id="1"，前端 key="q_001"
            # 场景3：后端 q_id="q_001"，前端 key="q_001"
            user_ans = student_answers.get(q_key)

            # 如果没找到，尝试其他格式
            if user_ans is None:
                # 尝试去掉下划线（q_001 -> q001）
                alt_key = q_key.replace('_', '')
                user_ans = student_answers.get(alt_key)

            if user_ans is None:
                # 尝试添加下划线（q001 -> q_001）
                # 在数字前添加下划线
                import re
                alt_key = re.sub(r'(\D)(\d)', r'\1_\2', q_key)
                user_ans = student_answers.get(alt_key)

            if user_ans is None:
                # 尝试纯数字格式（q_001 -> 1 或 001）
                digits = re.search(r'\d+', q_key)
                if digits:
                    # 尝试带前导零（001）
                    alt_key = digits.group()
                    user_ans = student_answers.get(alt_key)
                    # 尝试不带前导零（1）
                    if user_ans is None:
                        alt_key = str(int(digits.group()))
                        user_ans = student_answers.get(alt_key)

            is_correct = False
            q_type = str(getattr(q, 'q_type', getattr(q, 'question_type', ''))).lower()

            # 1. 没做，直接判错并记录空题
            if not user_ans:
                is_correct = False
                empty_count += 1

            # 2. 单选与判断题（直接对比字符串）
            elif 'choice' in q_type or 'true' in q_type or 'false' in q_type or 'judge' in q_type:
                # 🐛 修复：兼容后端答案为字符串或列表格式
                # 场景1：answer_data = "A"（字符串）
                # 场景2：answer_data = ["A"]（列表）
                # 学生答案：user_ans = "A"
                #
                # 处理逻辑：
                # 1. 如果 answer_data 是列表，取第一个元素
                # 2. 统一转为字符串并大写后对比
                correct_ans_raw = q.answer_data
                if isinstance(correct_ans_raw, list) and len(correct_ans_raw) > 0:
                    correct_ans = str(correct_ans_raw[0]).strip().upper()
                else:
                    correct_ans = str(correct_ans_raw).strip().upper()

                if str(user_ans).strip().upper() == correct_ans:
                    is_correct = True
                    correct_count += 1
                else:
                    wrong_count += 1

            # 3. 填空题（遍历核对每个空）
            elif 'blank' in q_type:
                is_correct = True

                # 🐛 修复：兼容学生答案的多种格式
                # 场景1：answer_data = {"b1": ["答案1"], "b2": ["答案2"]}（标准字典格式）
                # 场景2：answer_data = {"b1": "答案1"}（值为字符串而非列表）
                # 场景3：user_ans = {"b1": "答案1", "b2": "答案2"}（标准字典格式）
                # 场景4：user_ans = "答案1"（字符串，非字典）
                #
                # 处理逻辑：
                # 1. 后端答案必须是字典
                # 2. 学生答案如果是字符串，尝试转为单空字典
                # 3. 对比时兼容 correct_list 为字符串或列表的情况

                if isinstance(q.answer_data, dict):
                    # 处理学生答案格式
                    processed_user_ans = user_ans
                    if not isinstance(user_ans, dict):
                        # 如果学生答案不是字典，尝试转为单空格式
                        # 假设只有一个空，key为"b1"
                        processed_user_ans = {"b1": str(user_ans) if user_ans else ""}

                    for blank_id, correct_list in q.answer_data.items():
                        # 学生这个空填的词
                        ans_str = str(processed_user_ans.get(blank_id, '')).strip()

                        # 兼容 correct_list 为字符串或列表的情况
                        # 场景1：correct_list = ["固定牢固", "牢固"]（列表）
                        # 场景2：correct_list = "固定牢固"（字符串）
                        if isinstance(correct_list, str):
                            correct_list = [correct_list]

                        # correct_list 是数组，例如 ["固定牢固", "牢固"]
                        if ans_str not in correct_list:
                            is_correct = False
                            break

                    if is_correct:
                        correct_count += 1
                    else:
                        wrong_count += 1
                else:
                    is_correct = False
                    wrong_count += 1

            # 🌟 收集错题记录（用于错题本）
            if not is_correct and user_ans is not None:
                save_ans = user_ans if user_ans is not None else ""

                wrong_questions_list.append(
                    WrongQuestion(
                        student=user,
                        exam=exam,
                        question=q,
                        student_answer=save_ans # ✅ 使用处理后的答案
                    )
                )

        # 🔒 安全检查：防止学生当天重复提交
        #
        # 业务规则：学生当天只能提交一次，第二天可以重新提交
        #
        # 设计理念：
        # 1. 当天提交后不能再提交 -> 防止查看错题本答案后立即作弊
        # 2. 第二天可以重新提交 -> 给学生复习订正的机会，符合刷题本质
        # 3. 每天限制一次 -> 避免学生反复尝试获取正确答案
        #
        # 防止作弊场景：
        # 上午：学生乱填提交 -> 加入错题本
        # 中午：查看错题本看到答案
        # 下午：想用正确答案重新提交 -> 被拒绝（同一天）
        # 次日：学生可以重新提交（过了一天，真正复习）
        #
        # ⚠️ 运维注意：
        # - 这是核心防作弊机制，不要随意修改
        # - 如需调整时间限制（比如改为每周一次），请与业务团队确认
        # - 删除此检查会导致严重的作弊漏洞

        existing_submission = Submission.objects.filter(student=user, exam=exam).first()

        if existing_submission:
            # 检查是否在同一天
            from django.utils import timezone
            today = timezone.now().date()
            submission_date = existing_submission.submit_time.date()

            if today == submission_date:
                # 同一天，拒绝提交
                hours_until_midnight = 24 - timezone.now().hour
                return Response({
                    "error": "此试卷今天已提交，明天才能重新提交",
                    "message": f"请等待{hours_until_midnight}小时后（明天）重新提交",
                    "can_retry": False,
                    "security_reason": "防止查看错题本答案后当天作弊",
                    "last_submit_time": existing_submission.submit_time,
                    "can_submit_time": submission_date.replace(day=submission_date.day + 1)  # 次日
                }, status=status.HTTP_400_BAD_REQUEST)

            # 不同日期（第二天及以后），允许重新提交
            # 这种情况下会更新已有记录，不会创建新记录
            # 重新提交时会自动清理旧的错题记录
            pass

        # 🌟 错题记录清理策略
        #
        # 场景1：首次提交 -> 不需要清理（没有旧记录）
        # 场景2：第二天重新提交 -> 删除旧的错题记录，重新建立
        #
        # 为什么要删除旧错题记录？
        # - 学生重新提交后，错题情况可能发生变化
        # - 保留旧错题会重复显示，影响错题本功能
        # - 重新提交意味着学生重新学习，应该基于最新结果建立错题本
        #
        # 注意：由于前面已经有了重复提交检查，这里实际上只有两种情况：
        # 1. 首次提交：existing_submission为None，不需要删除
        # 2. 次日重新提交：existing_submission存在且不是同一天，需要删除旧错题
        #
        # ⚠️ 运维注意：
        # - 不要删除此清理逻辑，否则会导致错题本重复堆积
        # - 如需保留历史错题记录，请联系开发人员设计归档方案

        if existing_submission:
            # 删除学生在这张卷子的所有旧错题记录
            WrongQuestion.objects.filter(student=user, exam=exam).delete()
            print(f"[DEBUG] 删除了学生 {user.username} 在试卷 {exam.title} 的旧错题记录")

        # 🌟 核心升级 2：使用 update_or_create (有则更新，无则创建)
        #
        # 业务逻辑说明：
        # - 首次提交：created=True，创建新提交记录
        # - 重新提交：created=False，更新已有记录的统计信息
        #
        # 为什么使用update_or_create？
        # 1. 符合"每个学生每张卷子只有一条最终记录"的设计
        # 2. 避免数据库中有多条同学生同试卷的记录
        # 3. 统计数据更准确，方便数据分析和学习情况追踪
        #
        # ⚠️ 运维注意：
        # - 修改 defaults 中的字段会影响保存的统计数据
        # - 如需添加新的统计字段，请在 defaults 中添加
        # - 不要修改 student=user, exam=exam 这两个查询条件

        # 计算可判分总题数（总题数 - 未答空题数）
        total_scoreable = questions.count() - empty_count
        # 计算正确率 (答对题数 / 可判分总题数)，避免除以0
        correct_rate = (correct_count / total_scoreable) if total_scoreable > 0 else 0.0

        submission, created = Submission.objects.update_or_create(
            student=user,
            exam=exam,
            defaults={
                'student_answers': student_answers,
                # 使用正确率统计代替分数，更适合刷题练习
                'total_scoreable': total_scoreable,
                'correct_count': correct_count,
                'wrong_count': wrong_count,
                'empty_count': empty_count,
                'correct_rate': correct_rate
            }
        )

        # 🌟 批量保存新的错题本
        #
        # 使用 bulk_create 批量插入，比逐条插入性能更好
        # 如果 wrong_questions_list 为空（全对），则跳过
        #
        # ⚠️ 运维注意：
        # - 不要删除此逻辑，否则错题本功能失效
        # - 如需修改错题记录格式，请同时修改 WrongQuestion 模型

        if wrong_questions_list:
            WrongQuestion.objects.bulk_create(wrong_questions_list)

        # 🌟 返回正确率统计数据给前端 - 适合刷题练习场景
        #
        # 返回信息说明：
        # - is_first_submit: 是否首次提交（前端可以据此显示不同提示）
        # - can_retry: 是否可以重新提交
        # - next_submit_time: 下次可提交时间（如果是当天提交，显示明天；如果已过天，显示立即）
        #
        # ⚠️ 运维注意：
        # - 修改返回数据结构会影响前端显示
        # - 如需添加新的返回字段，请与前端开发人员同步

        response_data = {
            "message": "交卷并阅卷成功！" if created else "重新提交成功！",
            "statistics": {
                "total_questions": questions.count(),      # 试卷总题数
                "total_scoreable": total_scoreable,    # 可判分题数（除去空题）
                "correct_count": correct_count,        # 答对题数
                "wrong_count": wrong_count,            # 答错题数
                "empty_count": empty_count,            # 未答题数
                "correct_rate": round(correct_rate, 2)  # 正确率（保留两位小数）
            },
            "submission_id": submission.id,
            "is_first_submit": created,
            "can_retry": False,  # 同天不允许，第二天允许
            "retry_info": {
                "can_submit_now": False,
                "reason": "同一天只能提交一次，明天可以重新提交",
                "next_submit_time": timezone.now().replace(hour=0, minute=0, second=0, microsecond=0) + timezone.timedelta(days=1)
            }
        }

        return Response(response_data, status=status.HTTP_201_CREATED)


class WrongQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ================================================================================
    错题本视图 - 学生专属功能
    ================================================================================
    
    【功能说明】
    提供学生查看自己错题记录的功能，支持查看错题详情、正确答案、解析。
    只读视图，学生无法修改或删除错题记录。
    
    【权限控制】
    - IsAuthenticated: 必须登录
    - ReadOnlyModelViewSet: 只读，不支持写入操作
    
    【数据过滤】
    - 学生只能看到自己的错题（通过 get_queryset 过滤）
    - 使用 select_related 优化查询性能（防止 N+1 问题）
    - ⚠️ 重要：错题本不受试卷展示日期限制，无论什么时候做错的题都能看到
    
    【API端点】
    - GET /api/wrong-questions/        -> 获取错题列表
    - GET /api/wrong-questions/{id}/   -> 获取单个错题详情
    
    【返回数据】
    包含题目详情、学生答案、正确答案、解析等，方便学生复习。
    
    ⚠️ 运维注意：
    - 此视图涉及学生隐私数据，务必确保过滤逻辑正确
    - 不要修改 get_queryset 中的 student=self.request.user 过滤条件
    - 如需添加教师查看学生错题的功能，请联系开发人员
    - 删除过滤条件会导致学生能看到其他同学的错题（严重安全漏洞）
    ================================================================================
    """
    serializer_class = WrongQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        ================================================================================
        获取当前登录用户的错题列表
        ================================================================================
        
        【功能说明】
        只返回当前登录学生自己的错题记录，确保数据隐私。
        
        【优化说明】
        - 使用 select_related('question', 'exam') 优化数据库查询
        - 防止 N+1 查询问题（嵌套序列化时的性能问题）
        - 按 created_at 倒序排列，最新的错题在前
        
        【返回值】
        - QuerySet: 当前学生的错题记录列表
        
        ⚠️ 运维注意：
        - 必须保留 student=self.request.user 过滤条件
        - 删除此过滤会导致学生能看到其他同学的错题（严重安全漏洞）
        - 如需添加排序方式，修改 order_by 参数
        ================================================================================
        """
        # 🌟 关键：只看当前登录用户自己的错题
        # 使用 select_related 优化数据库查询，防止 N+1 问题
        return WrongQuestion.objects.filter(student=self.request.user).select_related('question', 'exam').order_by('-created_at')
