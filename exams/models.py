from django.db import models
from django.conf import settings

class Exam(models.Model):
    """试卷元数据"""
    SUBJECT_CHOICES = (
        ('math', '数学'),
        ('science', '科学'),
    )
    exam_id = models.CharField(max_length=100, unique=True, verbose_name="试卷唯一ID")
    title = models.CharField(max_length=200, verbose_name="试卷标题")
    subject = models.CharField(max_length=10, choices=SUBJECT_CHOICES, verbose_name="学科")
    visible_date = models.DateField(verbose_name="可见日期")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

class Question(models.Model):
    """题目信息"""
    TYPE_CHOICES = (
        ('multiple_choice', '选择题'),
        ('fill_in_blank', '填空题'),
        ('true_or_false', '判断题'),
        ('drawing', '画图题'),
        ('essay', '论述题'),
    )
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name="questions")
    q_id = models.CharField(max_length=20, verbose_name="题目编号") # 如 q1, q2
    q_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    stem = models.TextField(verbose_name="题干(HTML)")
    
    # 存储选项、标准答案、填空题的 is_ordered 属性等
    # 填空题答案示例: {"b1": ["答案1"], "b2": ["答案2"]}
    answer_data = models.JSONField(verbose_name="标准答案数据")
    
    # 存储填空题每个空的配置，如 [{"blank_id": "b1", "is_ordered": true}]
    blank_configs = models.JSONField(null=True, blank=True, verbose_name="填空配置")
    
    options = models.JSONField(null=True, blank=True, verbose_name="选项数据")
    analysis = models.TextField(blank=True, verbose_name="解析")
    knowledge_point = models.CharField(max_length=100, blank=True, verbose_name="知识点")
    exam_point = models.CharField(max_length=100, blank=True, verbose_name="考查点")
    order = models.PositiveIntegerField(default=0, verbose_name="题目顺序")

    class Meta:
        ordering = ['order']

class Submission(models.Model):
    """学生整卷提交记录"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    
    # 存储学生所有题目的答案，格式同 Question.answer_data
    student_answers = models.JSONField(verbose_name="学生提交的答案")
    
    # 统计数据
    total_scoreable = models.IntegerField(default=0, verbose_name="可判分总题数")
    correct_count = models.IntegerField(default=0, verbose_name="答对题数")
    empty_count = models.IntegerField(default=0, verbose_name="空值题数")
    correct_rate = models.FloatField(default=0.0, verbose_name="正确率")
    
    is_completed = models.BooleanField(default=False, verbose_name="是否完成(含画图题已读)")
    submit_time = models.DateTimeField(auto_now_add=True, verbose_name="提交时间")
    score = models.IntegerField(verbose_name="总分", null=True, blank=True, default=0)

    class Meta:
        unique_together = ('student', 'exam') # 每个学生每张卷子只有一条最终记录

class WrongQuestion(models.Model):
    """错题集"""
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, verbose_name="来源试卷")
    student_answer = models.JSONField(verbose_name="学生答案", null=True, blank=True, default=dict)
    created_at = models.DateTimeField(auto_now_add=True)