# exams/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExamViewSet, SubmissionViewSet, WrongQuestionViewSet

router = DefaultRouter()

# 1. 试卷接口 (最终 URL: /api/exams/)
router.register(r'exams', ExamViewSet, basename='exam')

# 2. 提交答案接口 (最终 URL: /api/submissions/)
router.register(r'submissions', SubmissionViewSet, basename='submission')

# 3. 错题集接口 (最终 URL: /api/wrong_questions/)
router.register(r'wrong-questions', WrongQuestionViewSet, basename='wrong-question')

urlpatterns = [
    path('', include(router.urls)),
]