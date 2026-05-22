"""
================================================================================
试卷系统数据模型模块
================================================================================

【重要提示 - 给运维人员】
本文件定义了试卷系统的核心数据表结构，包括：
- Exam（试卷）：存储试卷元数据
- Question（题目）：存储题目内容和答案
- Submission（提交记录）：存储学生答题结果
- WrongQuestion（错题本）：存储学生错题记录

⚠️ 修改前请务必联系开发人员，随意修改可能导致：
- 数据库结构损坏
- 历史数据丢失
- 业务逻辑错误
- 系统无法正常运行

【模型关系图】
    Exam (试卷) 1 ---- N Question (题目)
      |                    |
      |                    |
      N                    N
    Submission (提交记录)  WrongQuestion (错题本)
      |
      N
    User (学生)

作者: [你的名字]
最后修改: 2026-05-22
================================================================================
"""

from django.db import models
from django.conf import settings


class Exam(models.Model):
    """
    ================================================================================
    试卷元数据模型
    ================================================================================
    
    【功能说明】
    存储试卷的基本信息，包括试卷ID、标题、学科、开放日期等。
    一张试卷包含多道题目（通过外键关联 Question 模型）。
    
    【字段说明】
    - exam_id: 试卷唯一标识（如 "math_2024_001"）
    - title: 试卷标题（显示给学生看）
    - subject: 学科（数学/科学等）
    - display_start_date: 展示开始日期（学生从此日期开始能看到试卷）
    - display_end_date: 展示结束日期（学生到此日期后不能再看到试卷）
    - created_at: 创建时间（自动记录）
    
    【关联关系】
    - questions: 一对多关联 Question 模型（related_name="questions"）
    
    【使用示例】
    exam = Exam.objects.create(
        exam_id="math_001",
        title="数学测试卷",
        subject="math",
        visible_date="2024-01-01"
    )
    
    ⚠️ 运维注意：
    - 不要修改 exam_id 字段的 unique=True 属性，否则会导致重复试卷ID
    - display_start_date 和 display_end_date 控制学生何时能看到试卷
    - 学生只能看到展示开始日期 <= 今天 <= 展示结束日期 的试卷
    - 删除试卷会级联删除所有关联的题目和提交记录（谨慎操作）
    ================================================================================
    """
    
    # 学科选项定义
    # 如需添加新学科，请在此添加选项并同步修改前端代码
    SUBJECT_CHOICES = (
        ('math', '数学'),
        ('science', '科学'),
    )
    
    # 🔑 试卷唯一标识符
    # 作用：前端通过此ID识别试卷，导入试卷时使用
    # 格式建议：学科_年份_序号，如 "math_2024_001"
    exam_id = models.CharField(
        max_length=100, 
        unique=True, 
        verbose_name="试卷唯一ID",
        help_text="试卷的唯一标识符，用于导入和查询"
    )
    
    # 📄 试卷标题
    # 作用：显示给学生看的试卷名称
    title = models.CharField(
        max_length=200, 
        verbose_name="试卷标题",
        help_text="试卷的显示名称"
    )
    
    # 📚 学科
    # 作用：分类试卷，影响试卷列表的筛选
    subject = models.CharField(
        max_length=10, 
        choices=SUBJECT_CHOICES, 
        verbose_name="学科",
        help_text="试卷所属学科"
    )
    
    # 📅 试卷展示开始日期（新增）
    # 作用：控制学生何时开始能看到试卷
    # 规则：学生只能看到 display_start_date <= 今天 的试卷
    display_start_date = models.DateField(
        default='2024-01-01',  # 默认值，用于迁移旧数据
        verbose_name="展示开始日期",
        help_text="试卷开始对学生展示的日期（包含当天）"
    )

    # 📅 试卷展示结束日期（新增）
    # 作用：控制学生何时不能再看到试卷
    # 规则：学生只能看到 display_end_date >= 今天 的试卷
    display_end_date = models.DateField(
        default='2099-12-31',  # 默认值，用于迁移旧数据，设置一个较远的日期
        verbose_name="展示结束日期",
        help_text="试卷结束对学生展示的日期（包含当天），过了这天学生就看不到了"
    )

    # ⏰ 创建时间（自动）
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间"
    )

    # 📝 保留旧字段用于兼容（可选，如果不需要可以删除）
    # visible_date 将被 display_start_date 替代
    # 为了兼容旧数据，暂时保留，但不再使用
    visible_date = models.DateField(
        null=True,
        blank=True,
        verbose_name="可见日期（旧字段，已废弃）",
        help_text="此字段已废弃，请使用展示开始日期和展示结束日期"
    )

    def __str__(self) -> str:
        """
        返回试卷的字符串表示（用于后台管理显示）
        
        ⚠️ 运维注意：
        - 修改返回值会影响 Django 后台的显示
        - 不要返回过长的字符串，否则后台显示会混乱
        """
        return self.title
    
    class Meta:
        """模型元数据配置"""
        verbose_name = "试卷"
        verbose_name_plural = "试卷"
        ordering = ['-display_start_date']  # 默认按展示开始日期倒序排列


class Question(models.Model):
    """
    ================================================================================
    题目模型
    ================================================================================
    
    【功能说明】
    存储每道题目的详细信息，包括题干、选项、答案、解析等。
    每道题目属于一张试卷（通过外键关联 Exam 模型）。
    
    【支持的题型】
    - multiple_choice: 选择题（单选）
    - fill_in_blank: 填空题（支持多空）
    - true_or_false: 判断题
    - drawing: 画图题（暂不支持自动阅卷）
    - essay: 论述题（暂不支持自动阅卷）
    
    【字段说明】
    - exam: 所属试卷（外键）
    - q_id: 题目编号（如 "q1", "q2"，用于前端标识）
    - q_type: 题目类型（选择题/填空题/判断题等）
    - stem: 题干内容（支持HTML格式）
    - answer_data: 标准答案（JSON格式，不同题型格式不同）
    - blank_configs: 填空题配置（是否按顺序判题等）
    - options: 选项数据（JSON格式，选择题使用）
    - analysis: 答案解析
    - knowledge_point: 知识点标签
    - exam_point: 考查点标签
    - order: 题目顺序（用于排序）
    
    【答案数据格式】
    - 选择题："A" 或 "B" 等单个字母
    - 判断题："TRUE" 或 "FALSE"
    - 填空题：{"b1": ["答案1", "同义词"], "b2": ["答案2"]}
    
    ⚠️ 运维注意：
    - 不要直接修改 answer_data 字段的内容，否则会影响已提交答案的判卷
    - 如需修改答案，建议创建新题目并废弃旧题目
    - 删除题目会级联删除所有关联的错题记录
    ================================================================================
    """
    
    # 题型选项定义
    # 如需添加新题型，请在此添加选项并同步修改 views.py 中的判题逻辑
    TYPE_CHOICES = (
        ('multiple_choice', '选择题'),
        ('fill_in_blank', '填空题'),
        ('true_or_false', '判断题'),
        ('drawing', '画图题'),
        ('essay', '论述题'),
    )
    
    # 🔗 所属试卷
    # related_name="questions" 允许通过 exam.questions.all() 获取试卷的所有题目
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE, 
        related_name="questions",
        verbose_name="所属试卷",
        help_text="这道题目属于哪张试卷"
    )
    
    # 🏷️ 题目编号
    # 作用：前端通过此ID标识题目，与学生答案中的key对应
    # 格式建议：q1, q2, q3... 或 1, 2, 3...
    q_id = models.CharField(
        max_length=20, 
        verbose_name="题目编号",
        help_text="题目的唯一编号，如 q1, q2"
    )
    
    # 📝 题目类型
    q_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES,
        verbose_name="题目类型"
    )
    
    # 📄 题干内容
    # 支持HTML格式，可以包含图片、公式等
    stem = models.TextField(
        verbose_name="题干(HTML)",
        help_text="题目内容，支持HTML格式"
    )

    # ✅ 标准答案数据（JSON格式）
    # 
    # 存储格式说明：
    # - 选择题："A" 或 "B"
    # - 判断题："TRUE" 或 "FALSE"  
    # - 填空题：{"b1": ["答案1", "同义词"], "b2": ["答案2"]}
    #   * b1, b2 是空的标识符
    #   * 数组表示该空可以有多个正确答案（同义词）
    #
    # ⚠️ 运维注意：
    # - 修改此字段会影响所有未提交和已提交的答案判卷
    # - 建议不要修改已有题目的答案，而是创建新题目
    answer_data = models.JSONField(
        verbose_name="标准答案数据",
        help_text="JSON格式，选择题为字母，填空题为字典格式"
    )

    # ⚙️ 填空题配置（JSON格式）
    #
    # 存储格式：
    # [
    #   {"blank_id": "b1", "is_ordered": true},
    #   {"blank_id": "b2", "is_ordered": false}
    # ]
    #
    # is_ordered: 是否按顺序判题
    # - true: 学生必须按顺序填空
    # - false: 学生可以乱序填空，系统会自动匹配
    #
    # ⚠️ 运维注意：
    # - 只有填空题使用此字段，其他题型为null
    # - 修改此字段会影响填空题的判题逻辑
    blank_configs = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="填空配置",
        help_text="填空题专用配置，如 [{\"blank_id\": \"b1\", \"is_ordered\": true}]"
    )

    # 🔘 选项数据（JSON格式）
    #
    # 存储格式（选择题）：
    # {
    #   "A": "选项A的内容",
    #   "B": "选项B的内容",
    #   "C": "选项C的内容",
    #   "D": "选项D的内容"
    # }
    #
    # ⚠️ 运维注意：
    # - 只有选择题使用此字段，其他题型为null
    # - 修改选项会影响题目显示，但不会影响已提交的答案
    options = models.JSONField(
        null=True, 
        blank=True, 
        verbose_name="选项数据",
        help_text="选择题的选项，如 {\"A\": \"选项A\", \"B\": \"选项B\"}"
    )
    
    # 📖 答案解析
    # 显示在错题本中，帮助学生理解正确答案
    analysis = models.TextField(
        blank=True, 
        verbose_name="解析",
        help_text="答案解析，显示在错题本中"
    )
    
    # 🏷️ 知识点标签
    # 用于分类和统计，如 "代数", "几何" 等
    knowledge_point = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="知识点",
        help_text="题目所属知识点，用于分类统计"
    )
    
    # 🏷️ 考查点标签
    # 用于更细粒度的分类，如 "一元一次方程", "三角形性质" 等
    exam_point = models.CharField(
        max_length=100, 
        blank=True, 
        verbose_name="考查点",
        help_text="题目考查的具体知识点"
    )
    
    # 🔢 题目顺序
    # 用于控制题目在试卷中的显示顺序
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name="题目顺序",
        help_text="题目在试卷中的显示顺序，数字越小越靠前"
    )

    def __str__(self) -> str:
        """
        返回题目的字符串表示
        
        格式：试卷标题 - 题目编号
        示例：数学测试卷 - q1
        
        ⚠️ 运维注意：
        - 修改返回值会影响 Django 后台的显示
        - 如果试卷标题很长，可以考虑只返回题目编号
        """
        return f"{self.exam.title} - {self.q_id}"

    class Meta:
        """模型元数据配置"""
        verbose_name = "题目"
        verbose_name_plural = "题目"
        ordering = ['order']  # 默认按题目顺序排列
        # 联合唯一约束：同一张试卷内题目编号不能重复
        unique_together = ['exam', 'q_id']


class Submission(models.Model):
    """
    ================================================================================
    学生提交记录模型
    ================================================================================
    
    【功能说明】
    存储学生提交试卷后的答题结果和统计数据。
    每个学生每张试卷只有一条记录（使用 update_or_create 实现）。
    
    【核心设计】
    - 使用正确率统计而非分数，更适合刷题练习场景
    - 支持重复提交（第二天可以重新提交）
    - 自动记录错题到错题本
    
    【字段说明】
    - student: 提交的学生（外键关联 User 模型）
    - exam: 提交的试卷（外键关联 Exam 模型）
    - student_answers: 学生的答案（JSON格式）
    - total_scoreable: 可判分总题数（总题数 - 未答题数）
    - correct_count: 答对题数
    - wrong_count: 答错题数
    - empty_count: 未答题数
    - correct_rate: 正确率（0-1之间）
    - is_completed: 是否完成（包含画图题已读标记）
    - submit_time: 首次提交时间
    - updated_time: 最后更新时间
    
    【唯一约束】
    - student + exam：每个学生每张试卷只有一条记录
    
    ⚠️ 运维注意：
    - 不要手动修改 correct_rate 等统计字段，应该重新提交试卷
    - 删除提交记录不会删除错题本记录（需要手动清理）
    - 如需导出学生成绩，请查询此模型
    ================================================================================
    """
    
    # 👤 提交学生
    # settings.AUTH_USER_MODEL 使用项目的自定义用户模型
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="学生",
        help_text="提交试卷的学生"
    )
    
    # 📝 提交的试卷
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE,
        verbose_name="试卷",
        help_text="提交的试卷"
    )

    # 📝 学生答案（JSON格式）
    #
    # 存储格式：
    # {
    #   "q1": "A",
    #   "q2": {"b1": "答案1", "b2": "答案2"},
    #   "q3": "TRUE"
    # }
    #
    # ⚠️ 运维注意：
    # - 此字段存储学生的原始答案，不要轻易修改
    # - 修改此字段后需要重新判卷才能更新统计数据
    student_answers = models.JSONField(
        verbose_name="学生提交的答案",
        help_text="JSON格式，key为题目编号，value为答案"
    )

    # 📊 统计数据 - 用于刷题练习，关注正确率而非分数
    #
    # 设计理念：
    # - 传统分数制：满分100分，答错扣分
    # - 正确率制：关注知识掌握程度，答对比例
    # - 本系统使用正确率，更适合刷题练习场景
    
    # 可判分总题数（总题数 - 未答空题数）
    # 作用：计算正确率时的分母
    total_scoreable = models.IntegerField(
        default=0, 
        verbose_name="可判分总题数",
        help_text="总题数减去未答题数，用于计算正确率"
    )
    
    # 答对题数
    correct_count = models.IntegerField(
        default=0, 
        verbose_name="答对题数",
        help_text="学生答对的题目数量"
    )
    
    # 未答题数（空题）
    empty_count = models.IntegerField(
        default=0, 
        verbose_name="空值题数",
        help_text="学生未作答的题目数量"
    )
    
    # 答错题数
    wrong_count = models.IntegerField(
        default=0, 
        verbose_name="答错题数",
        help_text="学生答错的题目数量"
    )
    
    # 正确率（0-1之间）
    # 计算公式：correct_count / total_scoreable
    # 示例：0.85 表示 85% 正确率
    correct_rate = models.FloatField(
        default=0.0, 
        verbose_name="正确率(0-1)",
        help_text="答对题数除以可判分总题数，范围0-1"
    )

    # ✅ 完成状态
    # 作用：标记学生是否已完成整张试卷（包括画图题已读）
    # 注意：目前主要用于标记，不影响判卷逻辑
    is_completed = models.BooleanField(
        default=False, 
        verbose_name="是否完成(含画图题已读)",
        help_text="标记学生是否已完成整张试卷"
    )

    # ⏰ 时间记录
    submit_time = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="首次提交时间",
        help_text="第一次提交的时间，用于防作弊检查"
    )
    updated_time = models.DateTimeField(
        auto_now=True, 
        verbose_name="最后更新时间",
        help_text="最后一次提交或修改的时间"
    )

    # 说明：本系统使用正确率而非分数进行统计，适合刷题练习场景

    def __str__(self) -> str:
        """
        返回提交记录的字符串表示
        
        格式：学生用户名 - 试卷标题
        
        ⚠️ 运维注意：
        - 修改返回值会影响 Django 后台的显示
        """
        return f"{self.student.username} - {self.exam.title}"

    class Meta:
        """模型元数据配置"""
        verbose_name = "提交记录"
        verbose_name_plural = "提交记录"
        ordering = ['-submit_time']  # 默认按提交时间倒序排列
        # 🔒 唯一约束：每个学生每张卷子只有一条最终记录
        # 
        # 为什么需要唯一约束？
        # 1. 避免数据库中有多条同学生同试卷的记录
        # 2. 确保 update_or_create 能正常工作
        # 3. 方便查询学生的最新答题情况
        #
        # ⚠️ 运维注意：
        # - 不要删除此约束，否则会导致数据重复
        # - 如需保留历史记录，请联系开发人员设计归档方案
        unique_together = ('student', 'exam')


class WrongQuestion(models.Model):
    """
    ================================================================================
    错题本模型
    ================================================================================
    
    【功能说明】
    自动记录学生答错的题目，方便学生复习和巩固。
    每次提交试卷后，系统会自动将错题添加到此表。
    
    【核心设计】
    - 自动记录：提交试卷时自动识别错题并记录
    - 自动清理：重新提交时删除旧错题，避免重复
    - 学生专属：每个学生只能看到自己的错题
    
    【字段说明】
    - student: 错题所属学生（外键关联 User 模型）
    - question: 错题对应的题目（外键关联 Question 模型）
    - exam: 错题来源的试卷（外键关联 Exam 模型）
    - student_answer: 学生的错误答案（JSON格式）
    - created_at: 记录创建时间
    
    【唯一约束】
    - student + question + exam：同一学生同一试卷同一题目只有一条记录
    
    ⚠️ 运维注意：
    - 不要手动删除错题记录，应该让学生重新提交试卷
    - 删除试卷或题目会级联删除关联的错题记录
    - 如需导出学生错题数据，请查询此模型
    ================================================================================
    """
    
    # 👤 错题所属学生
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        verbose_name="学生",
        help_text="错题所属的学生"
    )
    
    # ❓ 错题对应的题目
    question = models.ForeignKey(
        Question, 
        on_delete=models.CASCADE,
        verbose_name="题目",
        help_text="答错的题目"
    )
    
    # 📝 错题来源的试卷
    exam = models.ForeignKey(
        Exam, 
        on_delete=models.CASCADE, 
        verbose_name="来源试卷",
        help_text="这道错题来自哪张试卷"
    )
    
    # 📝 学生的错误答案（JSON格式）
    #
    # 存储格式与 student_answers 相同
    # 作用：在错题本中显示学生当时的答案，方便对比
    #
    # ⚠️ 运维注意：
    # - 此字段记录学生答错时的答案
    # - 学生重新提交后，此字段会被更新为最新答案
    student_answer = models.JSONField(
        verbose_name="学生答案", 
        null=True, 
        blank=True, 
        default=dict,
        help_text="学生的错误答案，JSON格式"
    )
    
    # ⏰ 记录创建时间
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="创建时间",
        help_text="错题记录创建的时间"
    )

    def __str__(self) -> str:
        """
        返回错题记录的字符串表示
        
        格式：学生用户名 - 题目编号
        
        ⚠️ 运维注意：
        - 修改返回值会影响 Django 后台的显示
        """
        return f"{self.student.username} - {self.question.q_id}"

    class Meta:
        """模型元数据配置"""
        verbose_name = "错题"
        verbose_name_plural = "错题"
        ordering = ['-created_at']  # 默认按创建时间倒序排列（最新的在前）
        
        # 🔒 唯一约束：防止同一个学生对同一道题在同一张试卷中产生多条错题记录
        #
        # 为什么需要唯一约束？
        # - 避免错题本重复显示同一道题
        # - 防止学生多次提交后错题本数据混乱
        # - 确保错题统计的准确性
        #
        # 注意：重新提交时会删除旧错题，所以不会有数据冲突
        #
        # ⚠️ 运维注意：
        # - 不要删除此约束，否则会导致错题重复
        # - 如需保留历史错题记录，请联系开发人员设计归档方案
        unique_together = ('student', 'question', 'exam')
