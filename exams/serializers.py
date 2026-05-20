from rest_framework import serializers
from .models import Exam, Question, Submission, WrongQuestion
import re

class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = '__all__'

class ExamSerializer(serializers.ModelSerializer):
    # 将 read_all=True 修改为 read_only=True
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exam
        fields = '__all__'

class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = '__all__'
        read_only_fields = ['student', 'total_scoreable', 'correct_count', 'empty_count', 'correct_rate', 'is_completed']

    def validate(self, data):
        # 验证试卷是否已锁定
        student = self.context['request'].user
        exam = data['exam']
        if Submission.objects.filter(student=student, exam=exam).exists():
            raise serializers.ValidationError("该试卷已提交并锁定，不可重复作答。")
        return data

    def create(self, validated_data):
        student = self.context['request'].user
        exam = validated_data['exam']
        student_answers = validated_data['student_answers']
        
        questions = exam.questions.all()
        
        total_scoreable = 0
        correct_count = 0
        empty_count = 0
        drawing_all_read = True
        
        # 自动判分逻辑
        for q in questions:
            q_ans = q.answer_data # 标准答案
            s_ans = student_answers.get(q.q_id) # 学生答案
            
            # 处理展示型题目（画图题）
            if q.q_type == 'drawing':
                if s_ans != 'read':
                    drawing_all_read = False
                continue
            
            # 排除非判分题
            if q.q_type in ['essay']:
                continue
                
            total_scoreable += 1
            
            # 检查是否为空
            if not s_ans or (isinstance(s_ans, dict) and all(not v for v in s_ans.values())):
                empty_count += 1
                continue
            
            # 分题型判分
            is_correct = False
            if q.q_type in ['multiple_choice', 'true_or_false']:
                is_correct = (s_ans == q_ans)
                
            elif q.q_type == 'fill_in_blank':
                is_correct = self.grade_fill_in_blank(q, s_ans, q_ans)
                
            if is_correct:
                correct_count += 1
            else:
                # 记录错题
                WrongQuestion.objects.create(
                    student=student,
                    question=q,
                    exam=exam,
                    student_answer=s_ans
                )

        # 计算正确率
        denominator = total_scoreable - empty_count
        rate = (correct_count / denominator) if denominator > 0 else 0.0

        submission = Submission.objects.create(
            student=student,
            exam=exam,
            student_answers=student_answers,
            total_scoreable=total_scoreable,
            correct_count=correct_count,
            empty_count=empty_count,
            correct_rate=round(rate, 4),
            is_completed=drawing_all_read
        )
        return submission

    def grade_fill_in_blank(self, question, s_ans, q_ans):
        """填空题判分逻辑，支持无序匹配"""
        configs = {c['blank_id']: c['is_ordered'] for c in question.blank_configs}
        
        for bid, is_ordered in configs.items():
            standard = [self.normalize(a) for a in q_ans.get(bid, [])]
            student = self.normalize(s_ans.get(bid, [""])[0])
            
            if is_ordered:
                if student not in standard: return False
            else:
                # 无序匹配逻辑：检查学生提供的答案是否在标准答案池中
                # 简单实现：这里需要根据实际业务决定是全对才给分，还是分空给分
                # MVP 第一版：全对才算对
                if student not in standard: return False
        return True

    def normalize(self, text):
        """标准化字符串：去空格、转小写，应对 LaTeX 差异"""
        if not text: return ""
        return re.sub(r'\s+', '', str(text)).lower()



from rest_framework import serializers
from .models import WrongQuestion, Question

class WrongQuestionSerializer(serializers.ModelSerializer):
    # 🌟 嵌套题目详情，这样前端才能显示题干
    question_details = serializers.SerializerMethodField()
    exam_title = serializers.ReadOnlyField(source='exam.title')

    class Meta:
        model = WrongQuestion
        fields = ['id', 'question', 'exam', 'exam_title', 'student_answer', 'question_details', 'created_at']

    def get_question_details(self, obj):
        q = obj.question
        return {
            "id": q.id,
            "q_id": getattr(q, 'q_id', q.id),
            "q_type": getattr(q, 'q_type', getattr(q, 'question_type', '')),
            "stem": q.stem,
            "options": q.options,
            "answer_data": q.answer_data, # 标准答案
            "analysis": getattr(q, 'analysis', '暂无解析') # 如果你有解析字段的话
        }
