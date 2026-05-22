# Django SECRET_KEY 安全配置指南

## 项目隔离说明

### 多项目部署的环境变量管理

由于服务器会部署多个Django项目，为了避免环境变量冲突，本项目使用项目特定的环境变量名称：

```bash
# 项目名称：shuashijuan_backend
# 环境变量：DJANGO_SHUASHIJUAN_SECRET_KEY

# 其他Django项目示例：
# 项目B → DJANGO_PROJECT_B_SECRET_KEY
# 项目C → DJANGO_PROJECT_C_SECRET_KEY
```

### 为什么需要项目隔离？

**问题：** 如果多个项目都使用 `DJANGO_SECRET_KEY`，后面设置的环境变量会覆盖前面的：

```bash
# 错误示例 ❌
export DJANGO_SECRET_KEY="project-a-key"    # 项目A设置
export DJANGO_SECRET_KEY="project-b-key"    # 项目B设置，覆盖了项目A

# 结果：项目A和项目B都使用了"project-b-key"
```

**正确做法：** 每个项目使用自己的环境变量名称

```bash
# 正确示例 ✅
export DJANGO_SHUASHIJUAN_SECRET_KEY="shuashijuan-key"    # 本项目
export DJANGO_PROJECT_B_SECRET_KEY="project-b-key"       # 项目B
export DJANGO_PROJECT_C_SECRET_KEY="project-c-key"       # 项目C
```
当前系统的SECRET_KEY直接硬编码在settings.py中，存在严重的安全隐患：
- 代码提交到GitHub后，任何人都可以看到SECRET_KEY
- 攻击者可以利用SECRET_KEY伪造用户会话、修改密码等
- 一旦SECRET_KEY泄露，系统的安全机制完全失效

## 解决方案
我们已经将SECRET_KEY改为从环境变量读取，开发环境使用默认值，生产环境必须设置环境变量。

## 已生成的SECRET_KEY

**推荐使用（Django官方格式）：**
```
0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js
```

## 运维配置步骤

### 1. 开发环境（本地开发）
不需要额外配置，使用settings.py中的默认值即可。

### 2. 生产环境（服务器部署）

#### Windows服务器配置：
```bash
# 临时生效（当前会话）
set DJANGO_SHUASHIJUAN_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js

# 永久生效（重启后有效）
setx DJANGO_SHUASHIJUAN_SECRET_KEY "0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js"
```

#### Linux服务器配置：
```bash
# 临时生效（当前会话）
export DJANGO_SHUASHIJUAN_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js'

# 永久生效（添加到~/.bashrc）
echo "export DJANGO_SHUASHIJUAN_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js'" >> ~/.bashrc
source ~/.bashrc
```

#### systemd服务配置：
在服务配置文件中添加：
```ini
[Service]
Environment="DJANGO_SHUASHIJUAN_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js"
```

#### Docker配置：
在docker-compose.yml或Dockerfile中：
```yaml
environment:
  - DJANGO_SHUASHIJUAN_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js
```

#### Linux服务器配置：
```bash
# 临时生效（当前会话）
export DJANGO_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js'

# 永久生效（添加到~/.bashrc）
echo "export DJANGO_SECRET_KEY='0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js'" >> ~/.bashrc
source ~/.bashrc
```

#### systemd服务配置：
在服务配置文件中添加：
```ini
[Service]
Environment="DJANGO_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js"
```

#### Docker配置：
在docker-compose.yml或Dockerfile中：
```yaml
environment:
  - DJANGO_SECRET_KEY=0e$5%m0$%jvt1hqrh@#(ey@k2u_ivb1)r(!t0@a82bh+wu3@js
```

### 1. 验证环境变量是否设置
```bash
# 检查环境变量
echo $DJANGO_SHUASHIJUAN_SECRET_KEY  # Linux
echo %DJANGO_SHUASHIJUAN_SECRET_KEY%  # Windows

# 或在Python中检查
python -c "import os; print(os.environ.get('DJANGO_SHUASHIJUAN_SECRET_KEY'))"
```

## 代码变更说明

### 修改文件：shuashijuan_backend/settings.py

**修改前：**
```python
SECRET_KEY = 'django-insecure-rb@)=*6lecf1rg+x^6*xuc+7j=lnrvy_9#m&oqhcko1$t8qik0'
```

**修改后：**
```python
import os
# 🔒 使用项目特定的环境变量名，避免多项目冲突
SECRET_KEY = os.environ.get('DJANGO_SHUASHIJUAN_SECRET_KEY', 'django-insecure-rb@)=*6lecf1rg+x^6*xuc+7j=lnrvy_9#m&oqhcko1$t8qik0')
```

### 工作原理
1. 优先从环境变量`DJANGO_SHUASHIJUAN_SECRET_KEY`读取
2. 如果环境变量不存在，使用默认值（开发环境）
3. 生产环境必须设置环境变量，否则使用默认值不安全
4. 每个项目使用不同的环境变量名称，避免多项目冲突

## 安全建议

### 1. 立即更换SECRET_KEY
- 使用上面生成的新的SECRET_KEY
- 旧的SECRET_KEY已经在GitHub上公开，不安全

### 2. 定期更换SECRET_KEY
- 建议每年更换一次
- 更换后需要清除所有用户会话

### 3. 保护SECRET_KEY的安全
- 不要将SECRET_KEY提交到版本控制系统
- 不要在日志、错误信息中输出SECRET_KEY
- 不要与不信任的人员分享SECRET_KEY

### 4. 清除旧的会话
更换SECRET_KEY后，所有现有的会话都会失效：
```bash
# 清除所有会话
python manage.py shell
>>> from django.contrib.sessions.models import Session
>>> Session.objects.all().delete()
```

## 测试验证

### 1. 验证环境变量生效
```bash
python manage.py shell
>>> from django.conf import settings
>>> print(settings.SECRET_KEY)
# 应该显示生产环境的SECRET_KEY
```

### 2. 验证应用正常运行
```bash
python manage.py runserver
# 访问 http://localhost:8000
# 确保应用正常运行
```

## 故障排除

### 问题1：环境变量不生效
**症状：** 使用的还是默认SECRET_KEY
**解决：**
- 检查环境变量是否正确设置
- 确认变量名称拼写正确：`DJANGO_SECRET_KEY`
- 重启应用或重新加载环境变量

### 问题2：应用启动失败
**症状：** 应用无法启动，报错SECRET_KEY相关
**解决：**
- 确认环境变量已正确设置
- 检查SECRET_KEY格式是否正确（应该是一个长字符串）
- 查看错误日志获取详细信息

## 紧急处理

如果发现SECRET_KEY已经泄露：

1. **立即更换SECRET_KEY**
2. **清除所有用户会话**
3. **让所有用户重新登录**
4. **检查是否有异常登录行为**
5. **审查安全日志**

## 联系支持

如有问题请联系开发团队或查看Django官方文档：
https://docs.djangoproject.com/en/stable/ref/settings/#secret-key