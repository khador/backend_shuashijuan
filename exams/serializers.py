"""
================================================================================
试卷系统序列化器模块
================================================================================

【重要提示 - 给运维人员】
本文件负责 Django 模型与 JSON 数据之间的转换（序列化/反序列化）。
包括：
- QuestionSerializer: 题目序列化器
- ExamSerializer: 试卷序列化器
- SubmissionSerializer: 提交记录序列化器
- WrongQuestionSerializer: 错题本序列化器

⚠️ 修改前请务必联系开发人员，随意修改可能导致：
- API 返回数据格式错误
- 前端无法正常显示数据
- 敏感信息泄露（如标准答案）
- 数据验证失败

【序列化器说明】
序列化器（Serializer）的作用：
1. 模型 -> JSON：将数据库中的数据转换为前端可用的JSON格式
2. JSON -> 模型：将前端传来的JSON数据转换为数据库模型实例
3. 数据验证：验证输入数据的合法性

作者: [你的名字]
最后修改: 2026-05-22
================================================================================
"""

from rest_framework import serializers
from .models import Exam, Question, Submission, WrongQuestion
import re


class QuestionSerializer(serializers.ModelSerializer):
    """
    ================================================================================
    题目序列化器
    ================================================================================
    
    【功能说明】
    将 Question 模型转换为 JSON 格式，供前端显示题目信息。
    
    【安全设计】
    ⚠️ 注意：answer_data（标准答案）不会在此序列化器中返回！
    
    返回给前端的字段：
    - id: 题目数据库ID
    - q_id: 题目编号（如 "q1", "q2"）
    - q_type: 题目类型
    - stem: 题干内容（HTML格式）
    - options: 选项数据（选择题专用）
    - analysis: 答案解析
    - order: 题目顺序
    - blank_configs: 填空题配置
    
    【不返回的字段】
    - answer_data: 标准答案（防止学生作弊）
    
    【使用场景】
    - 试卷详情接口（ExamSerializer 嵌套使用）
    - 错题本接口（WrongQuestionSerializer 嵌套使用）
    
    ⚠️ 运维注意：
    - 不要在此序列化器中添加 answer_data 字段
    - 如果需要返回答案，请在 WrongQuestionSerializer 中添加
    - 修改 fields 会影响 API 返回的数据结构
    ================================================================================
    """
    
    class Meta:
        model = Question
        # 🔒 明确指定返回字段，避免泄露不必要的信息
        # 注意：没有包含 answer_data（标准答案），防止学生作弊
        fields = [
            'id', 
            'q_id', 
            'q_type', 
            'stem', 
            'options', 
            'analysis', 
            'order',
            'blank_configs'  # 填空题配置，前端需要
        ]
        # read_only_fields 表示这些字段只读，不能通过API修改
        read_only_fields = fields


class ExamSerializer(serializers.ModelSerializer):
    """
    ================================================================================
    试卷序列化器
    ================================================================================
    
    【功能说明】
    将 Exam 模型转换为 JSON 格式，同时嵌套返回试卷的所有题目。
    
    【返回数据】
    {
        "id": 1,
        "exam_id": "exam_001",
        "title": "数学测试卷",
        "subject": "math",
        "visible_date": "2024-01-01",
        "created_at": "2024-01-01T00:00:00Z",
        "questions": [QuestionSerializer的返回数据...]
    }
    
    【嵌套说明】
    - questions: 嵌套了 QuestionSerializer，返回试卷的所有题目
    - read_only=True: 题目只能通过后台管理添加，不能通过API修改
    
    【使用场景】
    - 试卷列表接口
    - 试卷详情接口
    
    ⚠️ 运维注意：
    - 不要修改 fields = '__all__'，否则可能丢失某些字段
    - questions 字段是嵌套序列化，不要轻易修改
    ================================================================================
    """
    
    # 🔗 嵌套题目列表
    # 作用：返回试卷时同时返回所有题目
    # read_only=True: 表示只能读取，不能通过API修改
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Exam
        # 返回所有字段
        fields = '__all__'


class SubmissionSerializer(serializers.ModelSerializer):
    """
    ================================================================================
    提交记录序列化器
    ================================================================================
    
    【功能说明】
    将 Submission 模型转换为 JSON 格式，用于：
    1. 学生查看自己的答题结果
    2. 教师查看学生的答题统计
    3. API 返回提交结果
    
    【返回数据】
    包含学生提交的答案、统计数据、时间信息等。
    
    【设计理念】
    - 使用正确率统计而非分数，适合刷题练习场景
    - 统计数据字段为只读，由系统自动计算
    
    【字段说明】
    - id: 提交记录ID
    - student: 学生ID
    - exam: 试卷ID
    - student_answers: 学生的答案（JSON）
    - total_scoreable: 可判分总题数
    - correct_count: 答对题数
    - wrong_count: 答错题数
    - empty_count: 未答题数
    - correct_rate: 正确率
    - is_completed: 是否完成
    - submit_time: 提交时间
    - updated_time: 更新时间
    
    ⚠️ 运维注意：
    - 不要修改 read_only_fields，这些字段由系统自动计算
    - student_answers 是敏感数据，不要泄露给其他学生
    ================================================================================
    """
    
    class Meta:
        model = Submission
        fields = '__all__'
        
        # 🔒 以下字段为自动计算，前端只需提交 exam 和 student_answers
        # 这些字段只能通过 API 返回，不能通过 API 修改
        read_only_fields = [
            'student',              # 学生ID，由登录用户自动填充
            'total_scoreable',      # 可判分总题数（自动计算）
            'correct_count',        # 答对题数（自动计算）
            'wrong_count',          # 答错题数（自动计算）
            'empty_count',          # 未答题数（自动计算）
            'correct_rate',         # 正确率（自动计算）
            'is_completed',         # 完成状态（自动计算）
            'submit_time',          # 提交时间（自动记录）
            'updated_time'          # 更新时间（自动更新）
        ]

    def validate(self, data):
        """
        ================================================================================
        数据验证方法
        ================================================================================
        
        【功能说明】
        在创建或更新提交记录之前验证数据的合法性。
        
        【验证规则】
        - 本系统支持重新提交（使用 update_or_create）
        - 所以移除了原来的重复提交验证
        - 重复提交时会更新统计信息并更新错题本
        
        【返回值】
        - data: 验证通过的数据
        - ValidationError: 验证失败时的错误信息
        
        ⚠️ 运维注意：
        - 不要在此添加严格的重复提交验证，否则会破坏重新提交功能
        - 如需修改验证规则，请与前端开发人员同步
        ================================================================================
        """
        # 注意：本系统支持重新提交（update_or_create），所以移除了原来的重复提交验证
        # 重新提交时会更新统计信息并更新错题本
        return data




# ⚠️ 注意：下面有两行重复的 import 语句，这是代码风格问题，不影响功能
# 如果需要优化，可以删除下面两行并保留文件开头的 import
from rest_framework import serializers
from .models import WrongQuestion, Question


class WrongQuestionSerializer(serializers.ModelSerializer):
    """
    ================================================================================
    错题本序列化器
    ================================================================================
    
    【功能说明】
    将 WrongQuestion 模型转换为 JSON 格式，用于学生查看错题。
    
    【返回数据】
    {
        "id": 1,
        "question": 123,
        "exam": 1,
        "exam_title": "数学测试卷",
        "student_answer": {"b1": "错误答案"},
        "question_details": {
            "id": 123,
            "q_id": "q1",
            "q_type": "fill_in_blank",
            "stem": "题干内容",
            "options": null,
            "answer_data": {"b1": ["正确答案"]},
            "analysis": "解析内容"
        },
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    【嵌套设计】
    - question_details: 嵌套题目详情，包含标准答案和解析
    - 这是故意设计的，因为错题本需要显示正确答案给学生复习
    
    【安全说明】
    ⚠️ 注意：错题本需要显示正确答案，所以会返回 answer_data
    但学生只能查看自己的错题（在 views.py 中过滤），
    所以不会泄露给其他学生。
    
    ⚠️ 运维注意：
    - question_details 包含标准答案，只有错题本接口返回
    - 不要在其他接口（如试卷详情）中泄露 answer_data
    - 确保 views.py 中的 get_queryset 正确过滤了学生
    ================================================================================
    """
    
    # 🌟 嵌套题目详情，这样前端才能显示题干和标准答案
    # SerializerMethodField: 自定义序列化方法，可以访问完整对象
    question_details = serializers.SerializerMethodField()
    
    # 📝 来源试卷的标题（方便前端显示）
    exam_title = serializers.ReadOnlyField(source='exam.title')

    class Meta:
        model = WrongQuestion
        fields = [
            'id', 
            'question', 
            'exam', 
            'exam_title', 
            'student_answer', 
            'question_details', 
            'created_at'
        ]
        read_only_fields = fields

    def get_question_details(self, obj):
        """
        ================================================================================
        获取题目详情
        ================================================================================
        
        【功能说明】
        返回错题的完整信息，包括题干、选项、标准答案、解析等。
        这是 SerializerMethodField 的实现方法，会为每条记录调用一次。
        
        【参数说明】
        - obj: WrongQuestion 实例，包含了关联的 Question 对象
        
        【返回值】
        包含以下字段的字典：
        - id: 题目ID
        - q_id: 题目编号
        - q_type: 题目类型
        - stem: 题干内容
        - options: 选项数据
        - answer_data: 标准答案（这是故意返回的，用于学生复习）
        - analysis: 答案解析
        
        【为什么在错题本中返回 answer_data？】
        - 错题本是学生复习的工具，需要显示正确答案
        - 学生只能查看自己的错题（在 views.py 中过滤）
        - 所以不会泄露给其他学生
        
        ⚠️ 运维注意：
        - 不要在其他序列化器中返回 answer_data
        - 只有错题本需要显示标准答案
        ================================================================================
        """
        q = obj.question
        return {
            "id": q.id,
            "q_id": getattr(q, 'q_id', q.id),
            "q_type": getattr(q, 'q_type', getattr(q, 'question_type', '')),
            "stem": q.stem,
            "options": q.options,
            "answer_data": q.answer_data,  # ✅ 标准答案（用于学生复习）
            "analysis": getattr(q, 'analysis', '暂无解析')  # 答案解析
        }
