import pandas as pd
from django.core.management.base import BaseCommand
from users.models import User, ClassInfo

class Command(BaseCommand):
    help = '从 Excel 文件批量导入学生账号'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Excel 文件的绝对或相对路径')

    def handle(self, *args, **kwargs):
        file_path = kwargs['file_path']
        
        try:
            # 读取 Excel，强制将所有列作为字符串读取（防止账号或密码如果是纯数字时丢失前导零）
            df = pd.read_excel(file_path, dtype=str)
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for index, row in df.iterrows():
                # 精确提取这三列
                username = str(row['账号']).strip()
                password = str(row['密码']).strip()
                class_id_str = str(row['所在班级id']).strip()
                
                # 防御性判断：如果读到空行则跳过
                if pd.isna(username) or username == 'nan':
                    continue
                
                # 1. 检查账号是否已存在
                if User.objects.filter(username=username).exists():
                    self.stdout.write(self.style.WARNING(f'跳过: 账号 {username} 已存在。'))
                    skip_count += 1
                    continue
                    
                # 2. 根据 ID 查找班级
                try:
                    class_obj = ClassInfo.objects.get(id=int(class_id_str))
                except ClassInfo.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'错误: 账号 {username} 对应的班级ID ({class_id_str}) 不存在，请先在Admin创建该班级。跳过该生。'))
                    error_count += 1
                    continue
                except ValueError:
                    self.stdout.write(self.style.ERROR(f'错误: 账号 {username} 对应的班级ID格式不正确。跳过该生。'))
                    error_count += 1
                    continue

                # 3. 创建用户对象并加密密码
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    role='student' # 赋予学生角色
                )
                
                # 4. 绑定班级多对多关系
                user.classes.add(class_obj)
                
                success_count += 1
                
            self.stdout.write(self.style.SUCCESS(
                f'\n导入完成！成功添加 {success_count} 个学生，跳过 {skip_count} 个，错误 {error_count} 个。'
            ))
            
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'错误：找不到文件 {file_path}'))
        except KeyError as e:
            self.stdout.write(self.style.ERROR(f'错误：Excel 表头不匹配，找不到列名 {str(e)}，请确认表头是：账号、密码、所在班级id'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'导入过程中发生未知错误: {str(e)}'))
