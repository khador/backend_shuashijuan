import json
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from exams.models import Exam, Question

class Command(BaseCommand):
    help = '从 AI 生成的 JSON 文件导入试卷数据'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='JSON 文件的绝对或相对路径')

    def handle(self, *args, **options):
        json_file_path = options['json_file']

        if not os.path.exists(json_file_path):
            self.stdout.write(self.style.ERROR(f'致命错误：找不到文件 "{json_file_path}"'))
            return

        try:
            with open(json_file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR('致命错误：JSON 格式不合法，请检查标点或转义字符。'))
            return

        # 开启数据库事务：要么全成功，要么全失败回滚
        try:
            with transaction.atomic():
                # 1. 创建或更新试卷主体
                # update_or_create 的好处是：如果你发现 JSON 有错改了重新导，它会覆盖而不是报错重复
                exam, created = Exam.objects.update_or_create(
                    exam_id=data['exam_id'],
                    defaults={
                        'title': data['title'],
                        'subject': data['subject'],
                        'visible_date': data['visible_date']
                    }
                )

                action = "创建" if created else "更新"
                self.stdout.write(self.style.SUCCESS(f'成功{action}试卷: {exam.title}'))

                # 2. 清理旧题目（防重复）
                if not created:
                    deleted_count, _ = exam.questions.all().delete()
                    self.stdout.write(self.style.WARNING(f'已清理关联的 {deleted_count} 道旧题目，准备重新导入...'))

                # 3. 解析并批量创建题目
                questions_to_create = []
                for index, q_data in enumerate(data.get('questions', [])):
                    # 提取填空题特有的配置
                    blank_configs = q_data.get('blanks', None)
                    options_data = q_data.get('options', None)

                    question = Question(
                        exam=exam,
                        q_id=q_data['id'],
                        q_type=q_data['type'],
                        stem=q_data['stem'],
                        answer_data=q_data['answer'],
                        blank_configs=blank_configs,
                        options=options_data,
                        analysis=q_data.get('analysis', ''),
                        knowledge_point=q_data.get('knowledge_point', ''),
                        exam_point=q_data.get('exam_point', ''),
                        order=index + 1  # 强制按 JSON 里的顺序排序
                    )
                    questions_to_create.append(question)

                # bulk_create 可以极大减少 SQL 语句数量，性能拉满
                Question.objects.bulk_create(questions_to_create)
                self.stdout.write(self.style.SUCCESS(f'🎉 成功导入 {len(questions_to_create)} 道题目！'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入失败，数据库已安全回滚！错误详情: {str(e)}'))