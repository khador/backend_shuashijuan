from rest_framework import viewsets, permissions
from rest_framework.response import Response
from django.utils import timezone
from .models import Exam, Question, Submission, WrongQuestion
from .serializers import ExamSerializer, SubmissionSerializer, QuestionSerializer, WrongQuestionSerializer
from rest_framework import status

class ExamViewSet(viewsets.ReadOnlyModelViewSet):
    """试卷列表及详情视图"""
    serializer_class = ExamSerializer
    # ✅ 权限类必须定义在类级别
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        now = timezone.now().date()
        
        # 如果是超级管理员，直接看所有，方便调试
        if user.is_superuser:
            return Exam.objects.all().order_by('-visible_date')

        # 针对普通角色的过滤逻辑
        # 注意：请确保你的 User 模型确实有 role 属性
        role = getattr(user, 'role', 'student') 
        
        if role == 'student':
            # 学生只能看到今天及以前开放的试卷
            return Exam.objects.filter(visible_date__lte=now).order_by('-visible_date')
        
        # 教师和管理员可以看到所有
        return Exam.objects.all().order_by('-visible_date')

    def retrieve(self, request, *args, **kwargs):
        """详情页额外逻辑：确保返回试卷时连同题目一起返回"""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)




class SubmissionViewSet(viewsets.ModelViewSet):
    """提交与自动阅卷视图"""
    queryset = Submission.objects.all()
    serializer_class = SubmissionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = request.user
        exam_id = request.data.get('exam')
        student_answers = request.data.get('student_answers', {})

        try:
            exam = Exam.objects.get(id=exam_id)
        except Exam.DoesNotExist:
            return Response({"error": "试卷不存在"}, status=status.HTTP_404_NOT_FOUND)

        questions = exam.questions.all()
        total_score = 0
        wrong_questions_list = []

        # 🌟 核心：开始逐题批改
        for q in questions:
            # 前端的答案 key 可能是 q_id 字符串，也可能是数字 id
            q_key = str(getattr(q, 'q_id', q.id)) 
            user_ans = student_answers.get(q_key)
            
            is_correct = False
            q_type = str(getattr(q, 'q_type', getattr(q, 'question_type', ''))).lower()

            # 1. 没做，直接判错
            if not user_ans:
                is_correct = False
            
            # 2. 单选与判断题（直接对比字符串）
            elif 'choice' in q_type or 'true' in q_type or 'false' in q_type or 'judge' in q_type:
                correct_ans = str(q.answer_data).strip().upper()
                if str(user_ans).strip().upper() == correct_ans:
                    is_correct = True
            
            # 3. 填空题（遍历核对每个空）
            elif 'blank' in q_type:
                is_correct = True
                # 确保后端答案是字典，且前端传来的也是字典
                if isinstance(q.answer_data, dict) and isinstance(user_ans, dict):
                    for blank_id, correct_list in q.answer_data.items():
                        # 学生这个空填的词
                        ans_str = str(user_ans.get(blank_id, '')).strip()
                        # correct_list 是数组，例如 ["固定牢固", "牢固"]
                        if ans_str not in correct_list:
                            is_correct = False
                            break
                else:
                    is_correct = False

            # 🌟 算分与错题记录
            if is_correct:
                # 如果你的题目模型里有 score 字段就用 q.score，没有默认加 2 分
                total_score += getattr(q, 'score', 2) 
            else:
                save_ans = user_ans if user_ans is not None else ""
                
                wrong_questions_list.append(
                    WrongQuestion(
                        student=user, 
                        exam=exam, 
                        question=q, 
                        student_answer=save_ans # ✅ 使用处理后的答案
                    )
                )

       # 🌟 核心升级 1：如果学生是重新交卷，先把他上次做这张卷子留下的错题删掉，避免错题本重复堆积！
        WrongQuestion.objects.filter(student=user, question__in=questions).delete()

        # 🌟 核心升级 2：使用 update_or_create (有则更新，无则创建)
        submission, created = Submission.objects.update_or_create(
            student=user,
            exam=exam,
            defaults={
                'student_answers': student_answers,
                'score': total_score
            }
        )

        # 🌟 批量保存新的错题本
        if wrong_questions_list:
            WrongQuestion.objects.bulk_create(wrong_questions_list)

        # 把成绩直接返回给前端
        return Response({
            "message": "交卷并阅卷成功！",
            "score": total_score,
            "submission_id": submission.id
        }, status=status.HTTP_201_CREATED)

class WrongQuestionViewSet(viewsets.ReadOnlyModelViewSet):
    """查看自己的错题本"""
    serializer_class = WrongQuestionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # 🌟 关键：只看当前登录用户自己的错题
        # 使用 select_related 优化数据库查询，防止 N+1 问题
        return WrongQuestion.objects.filter(student=self.request.user).select_related('question', 'exam').order_by('-created_at')