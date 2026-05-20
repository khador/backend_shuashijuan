from django.contrib import admin
from .models import Exam, Question, Submission, WrongQuestion

# 简单的注册，方便后台查看录入的 JSON 数据是否正确
admin.site.register(Exam)
admin.site.register(Question)
admin.site.register(Submission)
admin.site.register(WrongQuestion)