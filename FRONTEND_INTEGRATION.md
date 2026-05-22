# 前后端同步说明

## 🔄 DRF-Spectacular 集成说明

### 🎯 作用
DRF-Spectacular会自动生成API文档，让前端实时了解后端API的变化，实现前后端完美同步。

### 📋 前端如何使用

#### 1. 访问OpenAPI文档
```bash
# 开发环境
http://localhost:8000/api/docs/

# 生产环境
http://116.62.144.210:8000/api/docs/

# 或者访问JSON Schema格式
http://localhost:8000/api/schema/
```

#### 2. 使用TypeScript类型定义
前端可以从文档生成TypeScript类型定义：

```bash
# 安装openapi-typescript
npm install -g openapi-typescript

# 从API文档生成类型定义
openapi-typescript http://localhost:8000/api/schema/ > src/types/api.ts
```

#### 3. 前端集成代码示例

```typescript
// 使用生成的API类型
import { ExamsApi } from './types/api';

const api = new ExamsApi({
  basePath: 'http://localhost:8000',
  baseOptions: {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  }
});

// 获取试卷列表
async function getExams() {
  const response = await api.apiExamsList();
  return response.data;
}

// 提交试卷答案
async function submitExam(examId: number, answers: object) {
  try {
    const response = await api.apiSubmissionsCreate({
      exam: examId,
      student_answers: answers
    });
    return response.data;
  } catch (error) {
    console.error('提交失败:', error);
    throw error;
  }
}
```

### 🔄 重要更新的API说明

#### 1. 试卷提交接口更新（重要！）
**接口路径：** `POST /api/submissions/`

**更新内容：**
- ❌ 旧版：返回 `{score: 85, submission_id: 123}`
- ✅ 新版：返回正确的率统计

**新接口响应格式：**
```json
{
  "message": "交卷并阅卷成功！",
  "statistics": {
    "total_questions": 10,
    "total_scoreable": 8,
    "correct_count": 6,
    "wrong_count": 2,
    "empty_count": 2,
    "correct_rate": 0.75
  },
  "submission_id": 123,
  "is_first_submit": true,
  "can_retry": false,
  "retry_info": {
    "can_submit_now": false,
    "reason": "同一天只能提交一次，明天可以重新提交",
    "next_submit_time": "2026-05-22 00:00:00"
  }
}
```

**前端需要修改：**
- ❌ 删除：`const score = response.data.score;`
- ✅ 添加：`const statistics = response.data.statistics;`
- ✅ 添加：`const canRetry = response.data.can_retry;`
- ✅ 添加：`const retryInfo = response.data.retry_info;`

#### 2. 同一天重复提交限制
**接口路径：** `POST /api/submissions/`

**错误响应格式：**
```json
{
  "error": "此试卷今天已提交，明天才能重新提交",
  "message": "请等待14小时后（明天）重新提交",
  "can_submit_time": "2026-05-22 00:00:00",
  "can_retry": false,
  "security_reason": "防止查看错题本答案后当天作弊",
  "last_submit_time": "2026-05-21 10:30:00"
}
```

**前端处理建议：**
- 显示友好的错误提示，而不是技术错误
- 显示可以提交的时间倒计时
- 如果`can_retry === false`，禁用提交按钮

#### 3. 权限错误处理
**错误响应格式：**
```json
{
  "error": "权限不足",
  "message": "您无权限修改其他同学的提交记录",
  "status_code": 403
}
```

**前端处理建议：**
- 显示403权限错误页面
- 提示用户登录或联系教师
- 记录权限错误供调试

### 📊 界面更新建议

#### 1. 试卷提交页面更新
- ✅ 显示正确率统计（答对/答错/未答/正确率）
- ✅ 显示是否首次提交
- ✅ 显示是否可以重新提交
- ✅ 显示下次可提交时间
- ❌ 移除分数显示

#### 2. 提交确认对话框
- ✅ 显示提交的统计信息
- ✅ 确认学生要提交
- ✅ 提醒每天只能提交一次

#### 3. 错误提示优化
- ✅ 同一天重复提交：显示倒计时和原因
- ✅ 权限错误：友好的提示和登录引导
- ✅ 网络错误：显示重试按钮和联系支持

### 🎯 完整的前端集成示例

#### React Hooks示例

```typescript
// API配置
const API_CONFIG = {
  BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api',
  DOCS_URL: `${process.env.REACT_APP_API_URL || 'http://localhost:8000'}/docs`,
};

// 自定义Hook：处理同一天重复提交限制
const useSubmitWithDailyLimit = () => {
  const response = await submitExam(examId, answers);
  
  // 检查是否可以重新提交
  if (!response.data.can_retry && response.data.retry_info) {
    const { next_submit_time } = response.data.retry_info;
    const now = new Date();
    const canSubmit = now >= new Date(next_submit_time);
    
    if (!canSubmit) {
      const hoursUntilMidnight = calculateHoursUntilMidnight(now);
      showToast(`请等待${hoursUntilMidnight}小时后重新提交`);
      return false;
    }
  }
  
  return true;
};

// 提交确认对话框
const showSubmitConfirmDialog = (statistics: any) => {
  const { correct_count, wrong_count, correct_rate } = statistics;
  
  const message = `确认提交？\n\n` +
    `📊 本次统计：\n` +
    `✅ 答对：${correct_count}题\n` +
    `❌ 答错：${wrong_count}题\n` +
    `🎯 正确率：${(correct_rate * 100).toFixed(1)}%\n\n` +
    `⚠️ 注意：每天只能提交一次，提交后不能再修改`;
  
  return confirm(message);
};
```

### 🔧 环境变量配置

**.env 文件示例（前端）：**
```bash
REACT_APP_API_URL=http://116.62.144.210:8000/api
REACT_APP_API_DOCS=http://116.62.144.210:8000/api/docs
```

**开发环境：**
```bash
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_API_DOCS=http://localhost:8000/api/docs
```

### 📝 测试建议

#### 1. 测试同一天重复提交
- 第一次提交：应该成功
- 第二次提交（同一天）：应该被拒绝，显示错误信息
- 第三天提交：应该成功

#### 2. 测试权限控制
- 尝试修改其他同学的记录：应该返回403错误
- 教师修改学生记录：应该成功

#### 3. 测试正确率计算
- 提交已知答案：正确率应该是100%
- 提交部分正确答案：正确率应该按实际计算
- 未答题：不计入可判分题数

### 🚨 前端需要注意的陷阱

#### 1. 不要硬编码分数
- ❌ 错误做法：`score = response.data.score`
- ✅ 正确做法：`const statistics = response.data.statistics`

#### 2. 处理所有错误状态
- 不要只处理200成功状态
- 要处理400、403、404、500等错误状态
- 使用统一的错误提示机制

#### 3. 注意权限控制
- 学生A可以看自己的提交记录
- 学生A不能修改学生B的提交记录
- 前端需要根据用户角色显示不同的界面

### 📚 相关资源

- Django REST Framework官方文档
- DRF-Spectacular文档
- 前端集成示例代码

---

*最后更新时间: 2026-05-21*
*文档版本: v1.0*
*维护人员: your_name*