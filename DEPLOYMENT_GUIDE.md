# 刷题系统后端更新部署指南

## 🚨🚨🚨 代码修改禁止警告 🚨🚨🚨

### ⛔ **绝对禁止修改的文件**

**以下文件严禁任何形式的修改，除非获得开发团队明确授权：**

#### 🔒 核心业务逻辑文件（绝对禁止！）
- ❌ `exams/models.py` - 数据库模型定义
- ❌ `exams/views.py` - API视图和业务逻辑  
- ❌ `exams/serializers.py` - 数据序列化器
- ❌ `exams/urls.py` - API路由配置
- ❌ `exams/permissions.py` - 权限控制逻辑
- ❌ `exams/exceptions.py` - 异常处理器
- ❌ `users/models.py` - 用户模型定义
- ❌ `users/views.py` - 用户相关视图
- ❌ `shuashijuan_backend/settings.py` - Django配置文件

#### ⚠️ 配置文件（仅限明确指定的修改）
- ⚠️ `shuashijuan_backend/settings_local.py` - 仅允许修改环境变量配置
- ⚠️ `.env` 或环境变量 - 仅允许修改明确指定的值
- ❌ 其他所有配置文件

### 📝 **可以修改的内容**

**运维可以根据实际情况调整以下内容：**

#### ✅ 允许修改的配置项
1. **环境变量**：
   - `DJANGO_SHUASHIJUAN_SECRET_KEY` - 如果需要更换
   - `DJANGO_SETTINGS_MODULE` - 如果配置路径调整
   - 数据库连接信息 - 如果数据库迁移

2. **部署配置**：
   - `gunicorn.service` - Gunicorn服务配置
   - `nginx.conf` - Nginx配置文件
   - 日志路径和轮转配置

3. **基础设施**：
   - 防火墙规则
   - 负载均衡配置
   - CDN配置

### 🚨 **修改后果**

**如果你修改了禁止修改的文件，可能导致：**

1. **系统功能异常** - 核心业务逻辑被破坏
2. **安全漏洞** - 移除安全防护导致系统被攻击
3. **数据丢失** - 数据库结构被破坏
4. **用户无法使用** - API接口异常
5. **无法回滚** - 修改后无法恢复正常状态

### 📞 **如果需要修改**

**请遵循以下流程：**

1. **记录问题** - 详细记录需要修改的原因和期望效果
2. **联系开发团队** - 通过正式渠道提出修改请求
3. **等待评估** - 开发团队评估修改的必要性和风险
4. **执行修改** - 在开发团队指导下进行修改
5. **测试验证** - 修改后进行充分测试
6. **正式部署** - 确认无误后再部署到生产环境

### 🆘 **紧急情况处理**

**如果遇到紧急问题需要紧急处理：**

1. **立即停止服务** - 使用`systemctl stop gunicorn`停止服务
2. **记录问题** - 详细记录错误信息和操作历史
3. **联系开发团队** - 通过紧急联系方式通知开发人员
4. **等待指示** - 在开发团队指导下处理
5. **不要自行修改** - 紧急情况下也不要修改核心代码

### ⚖️ **责任说明**

**运维责任：**
- ✅ 按照部署指南执行部署步骤
- ✅ 配置环境变量和系统配置
- ✅ 监控系统运行状态
- ✅ 处理基础设施问题
- ✅ 执行备份和恢复操作
- ❌ 修改核心业务逻辑代码
- ❌ 调整安全相关配置
- ❌ 修改数据库结构
- ❌ 调整API接口设计

**开发团队责任：**
- ✅ 开发和维护核心业务逻辑
- ✅ 设计数据库结构
- ✅ 实现安全防护机制
- ✅ 处理代码相关问题
- ✅ 指导运维部署和配置

---

## 📋 更新概述

本次更新包含以下内容：
- ✅ 分数系统改为正确率统计
- ✅ 添加用户权限控制（防止查看修改其他同学记录）
- ✅ 修复SECRET_KEY安全配置
- ✅ 数据库结构变更
- ✅ 新增权限管理模块
- ✅ 修复关键bug（questions未定义）
- ✅ 添加HTTPS和安全配置
- ✅ 添加异常处理器
- ✅ 添加API限流保护
- ✅ 添加同一天重复提交限制

## 🚨 重要提醒

1. **必须按照步骤顺序执行**
2. **每一步完成后检查是否成功再继续下一步**
3. **如果遇到问题，立即停止并联系开发人员**
4. **更新期间系统会暂停服务，建议选择低峰期**
5. **⚠️ 绝对禁止修改核心业务逻辑代码！**
6. **⚠️ 配置修改仅限明确指定的内容！**

---

## 🔧 准备工作

### 1. 登录服务器

```bash
# 使用SSH登录到服务器
ssh your_username@your_server_ip

# 例如：
ssh root@116.62.144.210
```

### 2. 进入项目目录

```bash
# 进入后端项目目录
cd /path/to/backend_shuashijuan

# 检查当前目录是否正确
pwd
# 应该显示：/path/to/backend_shuashijuan
```

### 3. 查看当前git状态

```bash
# 检查是否有未提交的修改
git status

# 如果有未提交的修改，先处理（如果有需要）
# git stash  # 暂存当前修改
```

---

## 💾 第一步：备份当前版本（非常重要！）

### 1.1 备份数据库

```bash
# 备份MySQL数据库
mysqldump -u django -p'DjangoPass123!' my_project_db > backup_$(date +%Y%m%d_%H%M%S).sql

# 检查备份文件是否生成
ls -lh backup_*.sql

# 应该看到类似这样的文件：
# -rw-r--r-- 1 root root 45K May 21 16:30 backup_20260521_163000.sql
```

**如果备份失败：**
```bash
# 检查MySQL服务是否运行
systemctl status mysql

# 如果MySQL没有运行，启动它
systemctl start mysql
```

### 1.2 备份当前代码

```bash
# 创建备份目录
mkdir -p backups

# 备份当前代码
tar -czf backups/code_backup_$(date +%Y%m%d_%H%M%S).tar.gz .

# 检查备份文件
ls -lh backups/
```

### 1.3 记录当前版本

```bash
# 记录当前的git commit ID
git log -1 > backups/current_commit.txt
cat backups/current_commit.txt
```

---

## 🔄 第二步：拉取最新代码

### 2.1 拉取远程仓库最新代码

```bash
# 拉取最新代码
git pull origin main

# 或者如果分支叫master
# git pull origin master

# 检查拉取结果
git log -1
```

**如果git pull失败：**

```bash
# 如果遇到冲突，先备份修改
git stash

# 然后重新拉取
git pull origin main

# 查看冲突
git status
```

### 2.2 检查是否有新增文件

```bash
# 查看新增的文件
git status

# 注意以下新文件：
# - exams/permissions.py          # 权限控制模块
# - SECRET_KEY_SETUP.md           # 密钥配置文档
# - generate_secret_key.py        # 密钥生成工具
```

---

## 🏗️ 第三步：配置环境变量

### 3.1 检查当前环境变量

```bash
# 检查是否已设置SECRET_KEY环境变量
echo $DJANGO_SHUASHIJUAN_SECRET_KEY

# 如果显示为空，需要设置环境变量
# 如果显示有值，记录下来以便回滚
```

### 3.2 设置SECRET_KEY环境变量

```bash
# 设置本项目专用的SECRET_KEY
export DJANGO_SHUASHIJUAN_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3/js'

# 验证设置是否成功
echo $DJANGO_SHUASHIJUAN_SECRET_KEY
# 应该显示：0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3/js
```

### 3.3 永久设置环境变量（重启后仍然有效）

```bash
# 添加到用户的bash配置文件
echo "export DJANGO_SHUASHIJUAN_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3/js'" >> ~/.bashrc

# 重新加载配置文件
source ~/.bashrc

# 再次验证
echo $DJANGO_SHUASHIJUAN_SECRET_KEY
```

**重要：**
- 如果使用systemd管理服务，还需要在服务配置文件中设置
- 如果使用其他方式管理服务，请相应调整

---

## 🐍 第四步：激活虚拟环境

### 4.1 查找虚拟环境

```bash
# 查找Python虚拟环境目录
ls -la | grep venv
ls -la | grep env
ls -la | grep .venv

# 常见的虚拟环境位置：
# - ./venv
# - ./env
# - ./.venv
# - /path/to/venv
```

### 4.2 激活虚拟环境

```bash
# 激活虚拟环境（根据你的实际情况选择）

# 如果虚拟环境在当前目录的venv文件夹
source venv/bin/activate

# 或者
# source env/bin/activate

# 或者
# source .venv/bin/activate

# 验证虚拟环境是否激活成功
which python
# 应该显示：/path/to/backend_shuashijuan/venv/bin/python

# 检查Python版本
python --version
```

**如果找不到虚拟环境：**

```bash
# 创建新的虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate
```

### 4.3 检查pip版本

```bash
# 检查pip版本
pip --version

# 如果pip版本过低，升级pip
pip install --upgrade pip
```

---

## 📦 第五步：安装/更新依赖包

### 5.1 检查requirements.txt

```bash
# 查看依赖包列表
cat requirements.txt

# 确认包含以下新增或更新的包：
# - Django 5.2.14
# - djangorestframework 3.17.1
# - django-cors-headers 4.9.0
# - djangorestframework_simplejwt 5.5.1
# - mysqlclient 2.2.8
```

### 5.2 安装依赖包

```bash
# 安装所有依赖包
pip install -r requirements.txt

# 查看安装过程，确保没有错误
```

**如果安装失败：**

```bash
# 如果mysqlclient安装失败，先安装系统依赖
sudo apt-get update
sudo apt-get install -y python3-dev default-libmysqlclient-dev build-essential

# 然后重新安装
pip install -r requirements.txt
```

### 5.3 验证关键包是否安装成功

```bash
# 验证Django
python -c "import django; print(django.VERSION)"

# 验证DRF
python -c "import rest_framework; print(rest_framework.__version__)"

# 验证MySQL支持
python -c "import MySQLdb; print('MySQL支持正常')"
```

---

## 🗄️ 第六步：数据库迁移

### 6.1 检查数据库连接

```bash
# 验证数据库连接是否正常
python manage.py check

# 应该显示：System check identified no issues (0 silenced).
```

**如果数据库连接失败：**

```bash
# 检查MySQL服务状态
systemctl status mysql

# 如果MySQL没有运行，启动它
sudo systemctl start mysql

# 检查数据库连接配置
# 编辑settings.py或settings_local.py检查数据库配置
```

### 6.2 查看待执行的迁移

```bash
# 查看有哪些迁移需要执行
python manage.py showmigrations

# 注意exam应用的迁移状态
# [X] 0001_initial
# [X] 0002_initial
# [X] 0003_submission_score
# [X] 0004_alter_wrongquestion_student_answer
# [ ] 0005_remove_submission_score_submission_updated_time_and_more  # 新的迁移
```

### 6.3 执行数据库迁移

```bash
# 创建迁移文件（如果需要）
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 查看迁移结果
# 应该看到类似这样的输出：
# Applying exams.0005_remove_submission_score_submission_updated_time_and_more... OK
```

**如果迁移失败：**

```bash
# 查看具体错误信息
# 常见错误和解决方法：

# 1. 字段冲突错误
# 解决：检查是否有重复的迁移，可能需要回滚

# 2. 数据类型不兼容
# 解决：备份数据后手动调整数据

# 3. 迁移文件缺失
# 解决：检查git pull是否完整，重新拉取

# 如果迁移失败，可以使用以下命令回滚
python manage.py migrate exams 0004  # 回滚到上一个迁移
```

### 6.4 验证迁移结果

```bash
# 检查数据库结构
python manage.py dbshell

# 在MySQL命令行中：
# show tables;
# describe exams_submission;

# 退出MySQL
# exit;
```

---

## 🔧 第七步：收集静态文件

### 7.1 创建静态文件目录（如果不存在）

```bash
# 创建static目录
mkdir -p static

# 确认目录权限
chmod 755 static
```

### 7.2 收集静态文件

```bash
# 收集所有静态文件
python manage.py collectstatic --noinput

# 查看收集结果
ls -lh static/

# 应该看到admin和rest_framework等静态文件
```

**如果静态文件收集失败：**

```bash
# 确保settings.py中STATIC_ROOT配置正确
# STATIC_ROOT = BASE_DIR / 'static'

# 检查static目录权限
ls -ld static/
# 应该有写入权限
```

---

## 🧪 第八步：测试应用

### 8.1 测试Django应用启动

```bash
# 启动开发服务器测试（不生产环境使用）
python manage.py runserver 0.0.0.0:8000 &

# 记录进程ID
echo $! > /tmp/test_server.pid

# 等待几秒钟让服务启动
sleep 5

# 测试访问
curl http://localhost:8000/api/

# 如果返回401或403，说明JWT认证正常工作
# 如果返回404，检查URL配置

# 停止测试服务器
kill $(cat /tmp/test_server.pid)
rm /tmp/test_server.pid
```

### 8.2 测试数据库连接

```bash
# 创建测试用户
python manage.py shell << EOF
from users.models import User
try:
    # 创建测试学生用户
    student = User.objects.create_user(
        username='test_student',
        password='Test123456',
        role='student'
    )
    print(f"测试学生用户创建成功: {student.username}")
except Exception as e:
    print(f"创建用户时出错: {e}")

# 测试权限模块
from exams.permissions import IsOwnerOrReadOnly
print("权限模块导入成功")
EOF
```

### 8.3 检查应用健康状态

```bash
# 测试应用健康检查
python manage.py check --deploy

# 检查是否有部署警告
# 警告信息可以暂时忽略，但需要记录下来
```

---

## 🚀 第九步：重启Gunicorn服务

### 9.1 查找Gunicorn进程

```bash
# 查找Gunicorn进程
ps aux | grep gunicorn

# 记录进程ID（PID）
# 可能看到类似这样的输出：
# root       12345  0.0  1.2  123456  78900 ?        S    16:00   0:05 gunicorn: master [backend_shuashijuan]
# root       12346  0.0  0.8  124567  54321 ?        S    16:00   0:03 gunicorn: worker [backend_shuashijuan]
```

### 9.2 停止旧的Gunicorn进程

```bash
# 方法1：如果使用systemd管理（推荐）
sudo systemctl stop gunicorn
sudo systemctl status gunicorn

# 方法2：如果使用supervisor
sudo supervisorctl stop gunicorn

# 方法3：如果手动启动，使用kill命令
# kill 12345  # 杀掉主进程（master进程）
# 或者优雅停止
# kill -TERM 12345

# 等待进程完全停止
sleep 5

# 再次检查进程是否还在
ps aux | grep gunicorn
```

**如果进程无法停止：**

```bash
# 强制杀死进程
kill -9 12345

# 或者找到所有gunicorn进程并杀掉
pkill -9 gunicorn
```

### 9.3 启动新的Gunicorn服务

**如果使用systemd管理：**

```bash
# 启动Gunicorn服务
sudo systemctl start gunicorn

# 检查服务状态
sudo systemctl status gunicorn

# 查看服务日志
sudo journalctl -u gunicorn -n 50
```

**如果使用supervisor管理：**

```bash
# 启动Gunicorn服务
sudo supervisorctl start gunicorn

# 检查服务状态
sudo supervisorctl status gunicorn

# 查看服务日志
sudo supervisorctl tail -f gunicorn
```

**如果手动启动：**

```bash
# 启动Gunicorn
gunicorn --bind 0.0.0.0:8000 --workers 4 --timeout 120 shuashijuan_backend.wsgi:application &

# 记录进程ID
echo $! > /tmp/gunicorn.pid

# 检查进程状态
ps aux | grep gunicorn
```

### 9.4 配置环境变量到systemd服务（如果使用systemd）

```bash
# 编辑Gunicorn服务配置文件
sudo nano /etc/systemd/system/gunicorn.service

# 在[Service]部分添加环境变量：
[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/backend_shuashijuan
Environment="PATH=/path/to/backend_shuashijuan/venv/bin"
Environment="DJANGO_SHUASHIJUAN_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3/js"
Environment="DJANGO_SETTINGS_MODULE=shuashijuan_backend.settings"
ExecStart=/path/to/backend_shuashijuan/venv/bin/gunicorn --workers 3 --bind unix:/path/to/backend_shuashijuan/gunicorn.sock shuashijuan_backend.wsgi:application

# 保存并退出（Ctrl+O, Enter, Ctrl+X）

# 重新加载systemd配置
sudo systemctl daemon-reload

# 重启服务
sudo systemctl restart gunicorn
```

---

## 🌐 第十步：重启Nginx（如果使用）

### 10.1 测试Nginx配置

```bash
# 测试Nginx配置文件
sudo nginx -t

# 应该显示：syntax is ok, test is successful
```

**如果Nginx配置测试失败：**

```bash
# 查看具体错误
# 根据错误提示修改配置文件

# 常见问题：
# 1. 静态文件路径配置错误
# 2. Gunicorn socket路径配置错误
# 3. 权限问题
```

### 10.2 重启Nginx

```bash
# 重新加载Nginx配置
sudo nginx -s reload

# 或者重启Nginx
sudo systemctl restart nginx

# 检查Nginx状态
sudo systemctl status nginx
```

### 10.3 检查Nginx访问日志

```bash
# 查看最近的访问日志
sudo tail -f /var/log/nginx/access.log

# 查看错误日志
sudo tail -f /var/log/nginx/error.log

# 按Ctrl+C退出日志查看
```

---

## ✅ 第十一步：验证部署成功

### 11.1 检查服务进程

```bash
# 检查Gunicorn进程
ps aux | grep gunicorn

# 应该看到gunicorn进程正在运行

# 检查Nginx进程
ps aux | grep nginx

# 应该看到nginx进程正在运行
```

### 11.2 测试API访问

```bash
# 测试根API
curl -I http://your_server_ip/

# 应该返回HTTP/1.1 200 OK或401 Unauthorized（因为需要认证）

# 测试登录接口
curl -X POST http://your_server_ip/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_user","password":"test_password"}'

# 应该返回access token
```

### 11.3 测试新功能

```bash
# 测试权限控制（需要先登录获取token）
# 1. 登录获取token
TOKEN=$(curl -X POST http://your_server_ip/api/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"test_student","password":"Test123456"}' \
  | grep -o '"access":"[^"]*"' | cut -d'"' -f4)

# 2. 测试查看提交记录（应该只能看自己的）
curl -H "Authorization: Bearer $TOKEN" \
  http://your_server_ip/api/submissions/

# 3. 测试修改别人的记录（应该被拒绝）
curl -X PUT -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  http://your_server_ip/api/submissions/1/ \
  -d '{"student_answers":{"q1":"test"}}'

# 应该返回403 Forbidden
```

### 11.4 检查日志文件

```bash
# 检查Gunicorn日志
sudo tail -f /var/log/gunicorn/error.log

# 或者查看应用日志
tail -f logs/app.log

# 查看是否有错误信息
```

---

## 📊 第十二步：数据迁移和清理

### 12.1 检查历史数据

```bash
# 检查现有的提交记录
python manage.py shell << EOF
from exams.models import Submission
print(f"总提交记录数: {Submission.objects.count()}")
print(f"有分数的记录数: {Submission.objects.exclude(score__isnull=True).count()}")
EOF
```

### 12.2 更新历史数据（如果有需要）

```bash
# 如果需要更新历史数据的统计信息
# 可以创建一个管理命令来处理

# 或者使用Django shell更新
python manage.py shell << EOF
from exams.models import Submission
import json

# 更新历史提交记录的统计信息
for submission in Submission.objects.all():
    if submission.score is not None:
        # 将分数信息转换为正确率信息
        # 这里需要根据具体业务逻辑调整
        submission.wrong_count = submission.total_scoreable - submission.correct_count
        submission.save()

print("历史数据更新完成")
EOF
```

### 12.3 清理临时文件

```bash
# 清理临时文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# 清理旧的备份文件（保留最近的3个）
cd backups
ls -t backup_*.sql | tail -n +4 | xargs -r rm
ls -t code_backup_*.tar.gz | tail -n +4 | xargs -r rm
```

---

## 🔍 第十三步：监控和日志

### 13.1 设置日志监控

```bash
# 创建日志监控脚本
cat > /tmp/monitor_logs.sh << 'EOF'
#!/bin/bash

# 监控关键日志文件
while true; do
    # 检查错误日志
    if grep -i "error" /var/log/gunicorn/error.log | tail -1; then
        echo "发现错误日志！" | mail -s "后端服务错误" admin@example.com
    fi

    # 检查500错误
    if grep "500" /var/log/nginx/error.log | tail -1; then
        echo "发现500错误！" | mail -s "服务器500错误" admin@example.com
    fi

    sleep 300  # 每5分钟检查一次
done
EOF

chmod +x /tmp/monitor_logs.sh

# 运行监控脚本
nohup /tmp/monitor_logs.sh > /dev/null 2>&1 &
```

### 13.2 配置日志轮转

```bash
# 创建日志轮转配置
sudo nano /etc/logrotate.d/gunicorn

# 添加以下内容：
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data www-data
    sharedscripts
    postrotate
        systemctl reload gunicorn > /dev/null 2>&1 || true
    endscript
}
```

---

## 📝 第十四步：文档和报告

### 14.1 生成部署报告

```bash
# 创建部署报告
cat > /tmp/deployment_report_$(date +%Y%m%d_%H%M%S).txt << EOF
=== 刷题系统后端更新部署报告 ===

部署时间: $(date)
操作人员: $(whoami)
服务器信息: $(hostname)

=== 更新内容 ===
- 分数系统改为正确率统计
- 添加用户权限控制
- 修复SECRET_KEY安全配置
- 数据库结构更新
- 新增权限管理模块

=== 部署步骤 ===
1. ✅ 备份数据库和代码
2. ✅ 拉取最新代码
3. ✅ 配置环境变量
4. ✅ 激活虚拟环境
5. ✅ 安装依赖包
6. ✅ 执行数据库迁移
7. ✅ 收集静态文件
8. ✅ 测试应用
9. ✅ 重启Gunicorn服务
10. ✅ 重启Nginx服务
11. ✅ 验证部署成功

=== 系统状态 ===
- Gunicorn进程数: $(ps aux | grep gunicorn | grep -v grep | wc -l)
- Nginx状态: $(systemctl is-active nginx)
- 数据库状态: $(systemctl is-active mysql)
- 当前Git版本: $(git log -1 --oneline)

=== 问题记录 ===
- 无重大问题

=== 后续监控 ===
- 需要监控用户登录情况
- 需要监控API响应时间
- 需要关注错误日志

=== 联系信息 ===
- 开发人员: your_email@example.com
- 运维负责人: your_name
EOF

# 查看报告
cat /tmp/deployment_report_*.txt
```

### 14.2 发送部署通知

```bash
# 发送部署完成通知（如果配置了邮件服务）
mail -s "刷题系统后端更新完成" admin@example.com << EOF
刷题系统后端更新已完成部署。

部署时间: $(date)
服务器: $(hostname)

所有服务运行正常，请登录系统验证功能。

如有问题请联系开发人员。
EOF
```

---

## 🎯 部署完成检查清单

### 系统服务
- [ ] Gunicorn服务运行正常
- [ ] Nginx服务运行正常
- [ ] MySQL数据库运行正常

### 功能验证
- [ ] 用户登录功能正常
- [ ] 试卷列表可以正常查看
- [ ] 提交答案功能正常
- [ ] 正确率统计显示正常
- [ ] 权限控制生效（学生不能看别人记录）

### 安全检查
- [ ] SECRET_KEY环境变量已设置
- [ ] 数据库连接正常
- [ ] 静态文件可以正常访问
- [ ] API认证正常工作

### 日志和监控
- [ ] 错误日志无异常
- [ ] 访问日志正常记录
- [ ] 系统监控正常

### 文档和备份
- [ ] 备份文件已保存
- [ ] 部署报告已生成
- [ ] 环境配置已记录

---

## 🚨 应急回滚方案

### 如果部署失败，按照以下步骤回滚：

#### 1. 立即停止服务
```bash
sudo systemctl stop gunicorn
sudo systemctl stop nginx
```

#### 2. 恢复数据库
```bash
# 恢复到备份的数据库
mysql -u django -p'DjangoPass123!' my_project_db < backup_20260521_163000.sql
```

#### 3. 恢复代码
```bash
# 恢复到备份的代码版本
cd /path/to/backend_shuashijuan
tar -xzf backups/code_backup_20260521_163000.tar.gz

# 或者使用git回滚
git reset --hard HEAD~1  # 回滚到上一个版本
```

#### 4. 重新启动服务
```bash
sudo systemctl start gunicorn
sudo systemctl start nginx
```

#### 5. 验证回滚成功
```bash
# 检查服务状态
sudo systemctl status gunicorn
sudo systemctl status nginx

# 测试基本功能
curl http://your_server_ip/
```

---

## 📞 联系信息

### 开发团队
- **主要开发人员**: your_name
- **联系方式**: your_email@example.com
- **紧急联系**: your_phone_number

### 运维团队
- **主要运维人员**: your_ops_name
- **联系方式**: your_ops_email@example.com

### 技术支持
- **服务器信息**: Ubuntu 22.04 LTS
- **项目路径**: /path/to/backend_shuashijuan
- **数据库**: MySQL/MariaDB
- **Web服务器**: Nginx + Gunicorn

---

## 📚 参考文档

- Django官方文档: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- SECRET_KEY配置说明: SECRET_KEY_SETUP.md
- 权限控制说明: exams/permissions.py
- 参考文档: Django官方文档: https://docs.djangoproject.com/
- Django REST Framework: https://www.django-rest-framework.org/
- SECRET_KEY配置说明: SECRET_KEY_SETUP.md

---

## 📋 运维行为规范

### 🔒 运维禁止的操作

#### ❌ 绝对禁止（会导致系统故障）
- **修改核心业务逻辑** - 如判分规则、权限检查、提交限制等
- **修改数据库结构** - 如模型字段、关系定义等
- **修改API接口设计** - 如接口路径、数据格式等
- **调整安全配置** - 如权限类、认证方式等
- **修改错误处理逻辑** - 如异常处理方式、错误信息格式等

#### ⚠️ 需要授权的操作
- **修改环境变量值** - 必须得到开发团队明确授权
- **调整Gunicorn配置** - 如worker数量、超时时间等
- **修改Nginx配置** - 如代理规则、负载均衡等
- **添加或删除Django应用** - 如新的中间件等
- **数据库性能调优** - 如索引优化、查询优化等

### ✅ 运维可以自主操作

#### 🛠️ 基础设施配置
- **服务器配置** - 防火墙规则、端口开放、资源监控
- **网络配置** - 域名解析、SSL证书、负载均衡
- **存储配置** - 磁盘扩容、备份策略、CDN配置

#### 🔧 应用配置调整
- **环境变量** - 根据环境设置不同的配置值
- **日志级别** - 根据需要调整日志详细程度
- **缓存配置** - Redis缓存、CDN缓存等配置
- **限流配置** - 根据业务需求调整API访问频率限制

#### 📊 监控和告警
- **应用监控** - CPU、内存、磁盘、网络使用情况
- **业务监控** - API访问量、错误率、响应时间
- **日志监控** - 错误日志、异常告警、性能分析
- **安全监控** - 异常登录、API攻击检测、权限异常

### 📝 报告和文档

#### 📋 日常运维报告
- **每日报告** - 系统运行状态、错误统计、性能指标
- **每周报告** - 趋势分析、资源使用情况、改进建议
- **每月报告** - 容量规划、技术债务、安全审计

#### 🚨 问题处理流程
1. **发现问题** - 通过监控、用户反馈、日志分析
2. **问题分类** - 紧急/高/中/低优先级
3. **制定方案** - 临时解决方案/根本解决方案/预防措施
4. **执行修复** - 按优先级和时间窗口执行
5. **效果验证** - 验证修复效果，避免引入新问题
6. **文档记录** - 记录问题原因、解决方案、预防措施

### 🎯 服务质量标准

#### 🔒 可用性要求
- **系统可用性** ≥ 99.5%（月度）
- **故障恢复时间** < 1小时
- **计划内维护** ≤ 4小时/月
- **备份成功率** 100%（按计划执行）

#### 🚀 性能要求
- **API响应时间** < 500ms（P95）
- **数据库查询时间** < 100ms（P95）
- **静态文件加载** < 200ms（P95）
- **页面加载时间** < 2秒（P95）

#### 🛡️ 安全要求
- **安全漏洞修复** = 0（已知高危漏洞）
- **安全配置合规** = 100%（按要求配置）
- **权限控制正确** = 100%（按业务规则）
- **异常监控覆盖** = 100%（所有关键操作）

---

## ✅ 部署完成

**恭喜！刷题系统后端更新已完成。**

请按照上述检查清单逐项验证，确保所有功能正常。

⚠️ **重要提醒：**
- 运维团队主要负责基础设施配置和日常运维
- 核心业务逻辑的任何修改都必须得到开发团队明确授权
- 如遇问题，请参考应急回滚方案或联系开发团队

**记住：每次部署后都要监控系统的运行状态，确保没有异常。**

---

*最后更新时间: 2026-05-21*
*文档版本: v2.0* 
*添加内容: 代码修改禁止警告、运维行为规范*
*操作人员: your_username*