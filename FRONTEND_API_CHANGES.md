# 🎯 前端API适配指令

## 📋 操作步骤

### 第一步：查看API文档

**你需要在本地启动后端：**
```bash
cd e:\Pythonproject\shuashijuan_backend\shuashijuan_backend
python manage.py runserver
```

**然后访问以下URL：**
```
http://localhost:8000/api/docs/
```

---

## 🔍 需要重点检查的API接口

### 1. POST /api/submissions/ - 提交试卷接口

#### ❌ 旧版本响应格式：
```json
{
  "message": "交卷并阅卷成功！",
  "score": 85,           // 已删除！
  "submission_id": 123
}
```

#### ✅ 新版本响应格式：
```json
{
  "message": "交卷并阅卷成功！",
  "statistics": {
    "total_questions": 10,           // 试卷总题数
    "total_scoreable": 8,            // 可判分题数（除去空题）
    "correct_count": 6,               // 答对题数
    "wrong_count": 2,                 // 答错题数
    "empty_count": 2,                 // 未答题数
    "correct_rate": 0.75               // 正确率（0-1）
  },
  "submission_id": 123,
  "is_first_submit": true,             // 是否首次提交
  "can_retry": false,                 // 是否可以重新提交
  "retry_info": {
    "can_submit_now": false,          // 是否可以立即提交
    "reason": "同一天只能提交一次，明天可以重新提交",
    "next_submit_time": "2026-05-22 00:00:00"  // 下次可提交时间
  }
}
```

#### 🔍 关键变化：
- ❌ **删除**：`score` 字段
- ✅ **新增**：`statistics` 对象，包含正确的率统计
- ✅ **新增**：`is_first_submit` 布尔值
- ✅ **新增**：`can_retry` 布尔值
- ✅ **新增**：`retry_info` 对象，包含重新提交信息

---

## 🛠️ 需要修改的前端代码

### 修改1：更新提交表单的响应处理

**文件位置：** `src/components/ExamSubmission.tsx` 或相关提交组件

#### 1.1 更新接口调用代码

```typescript
// ❌ 旧版本代码
const handleSubmit = async (examId: number, answers: object) => {
  try {
    const response = await api.submitExam(examId, answers);
    const score = response.data.score;  // ❌ 这个字段已经不存在了！
    console.log(`得分：${score}分`);
    return response;
  } catch (error) {
    console.error('提交失败', error);
    throw error;
  }
};

// ✅ 新版本代码
const handleSubmit = async (examId: number, answers: object) => {
  try {
    const response = await api.submitExam(examId, answers);
    
    // 🎯 提取新的响应字段
    const { message, statistics, submission_id, is_first_submit, can_retry, retry_info } = response.data;
    
    // 📊 处理正确率统计
    const correctRate = (statistics.correct_rate * 100).toFixed(1);
    const { total_questions, correct_count, wrong_count, empty_count } = statistics;
    
    // 🔄 处理重新提交限制
    if (!can_retry && retry_info) {
      const { next_submit_time } = retry_info;
      const canSubmitNow = new Date() >= new Date(next_submit_time);
      
      if (!canSubmitNow) {
        const hoursUntilNext = calculateHoursUntilTime(next_submit_time);
        alert(`此试卷今天已提交，明天才能重新提交\n还需等待${hoursUntilNext}小时`);
        return false; // 阻止提交
      }
    }
    
    // ✅ 提交成功
    console.log(`${message}`);
    console.log(`答对：${correct_count}题，答错：${wrong_count}题，正确率：${correctRate}%`);
    
    return { success: true, message, statistics, submission_id, is_first_submit };
  } catch (error: any) {
    // 🔍 错误处理
    if (error.status === 400 && error.data.security_reason) {
      // 同一天重复提交错误
      const { message, can_submit_time } = error.data;
      alert(message);
      return false;
    } else if (error.status === 403) {
      // 权限错误
      alert('您没有权限执行此操作，请登录或联系教师');
      return false;
    } else {
      // 其他错误
      alert('提交失败，请检查网络或稍后重试');
      return false;
    }
  }
};
```

#### 1.2 添加辅助函数

```typescript
// 📊 计算距离下次提交时间的小时数
function calculateHoursUntilTime(targetTimeString: string): number {
  const targetTime = new Date(targetTimeString);
  const now = new Date();
  const diff = targetTime.getTime() - now.getTime();
  return Math.ceil(diff / (1000 * 60 * 60));
}

// 🎯 检查是否可以提交
function canSubmitExam(retryInfo: any): boolean {
  if (!retryInfo || retryInfo.can_submit_now) {
    return true;
  }
  
  const { next_submit_time } = retryInfo;
  const now = new Date();
  return now >= new Date(next_submit_time);
}
```

---

### 修改2：更新提交结果显示页面

**文件位置：** `src/components/ExamResult.tsx` 或相关结果展示组件

#### 2.1 更新显示逻辑

```typescript
// ❌ 旧版本显示
<div className="result">
  <h2>得分：{score}分</h2>
  <p>提交ID：{submission_id}</p>
</div>

// ✅ 新版本显示
const ExamResult = ({ result }) => {
  const { message, statistics, submission_id, is_first_submit, can_retry, retry_info } = result;
  const { total_questions, correct_count, wrong_count, empty_count, correct_rate } = statistics;
  
  return (
    <div className="result">
      <h2>{message}</h2>
      
      {/* 📊 正确率统计 */}
      <div className="statistics">
        <div className="stat-item">
          <span className="stat-label">答对：</span>
          <span className="stat-value">{correct_count}题</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">答错：</span>
          <span className="stat-value wrong">{wrong_count}题</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">未答：</span>
          <span className="stat-value empty">{empty_count}题</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">正确率：</span>
          <span className="stat-value correct">{(correct_rate * 100).toFixed(1)}%</span>
        </div>
      </div>
      
      {/* 🎯 提交信息 */}
      <div className="submit-info">
        <p>提交ID：{submission_id}</p>
        <p>{is_first_submit ? '首次提交' : '重新提交'}</p>
      </div>
      
      {/* ⏰ 重新提交信息 */}
      {!can_retry && retry_info && (
        <div className="retry-info">
          <p>{retry_info.reason}</p>
          <p>下次可提交时间：{retry_info.next_submit_time}</p>
        </div>
      )}
      
      {/* 🔘 操作按钮 */}
      <div className="actions">
        <button onClick={handleViewWrongQuestions}>查看错题本</button>
        {can_retry && <button onClick={handleRetryExam}>重新练习</button>}
      </div>
    </div>
  );
};
```

---

### 修改3：更新提交确认对话框

**文件位置：** `src/components/SubmitConfirmDialog.tsx` 或相关对话框组件

#### 3.1 更新对话框内容

```typescript
const SubmitConfirmDialog = ({ exam, answers, onConfirm, onCancel }) => {
  // 📊 计算预览统计（可选）
  const answeredCount = Object.keys(answers).length;
  const emptyCount = exam.question_count - answeredCount;
  
  return (
    <Dialog open={true} onClose={onCancel}>
      <DialogTitle>确认提交试卷</DialogTitle>
      
      <DialogContent>
        <Typography variant="body1">
          你即将提交试卷：<strong>{exam.title}</strong>
        </Typography>
        
        <Typography variant="body2" color="text.secondary">
          已答题数：{answeredCount}题，未答题数：{emptyCount}题
        </Typography>
        
        {/* ⚠️ 重要提示 */}
        <Alert severity="warning" sx={{ mt: 2 }}>
          <Typography variant="body2">
            <strong>重要提醒：</strong>
          </Typography>
          <Typography variant="body2">
            • 每天只能提交一次，提交后当天无法修改
          </Typography>
          <Typography variant="body2">
            • 提交后可以在错题本中查看标准答案
          </Typography>
          <Typography variant="body2">
            • 第二天可以重新提交订正答案
          </Typography>
        </Alert>
        
        <Typography variant="body2" sx={{ mt: 2 }}>
          确认要提交吗？
        </Typography>
      </DialogContent>
      
      <DialogActions>
        <Button onClick={onCancel}>取消</Button>
        <Button onClick={onConfirm} variant="contained" color="primary">
          确认提交
        </Button>
      </DialogActions>
    </Dialog>
  );
};
```

---

### 修改4：更新错误处理逻辑

**文件位置：** `src/utils/apiErrorHandler.ts` 或相关错误处理文件

#### 4.1 统一错误处理函数

```typescript
export const handleApiError = (error: any): { showMessage: string; canRetry: boolean } => {
  // 🔍 错误类型判断
  if (!error.response) {
    return {
      showMessage: '网络连接错误，请检查网络设置',
      canRetry: true
    };
  }

  const { status, data } = error.response;

  switch (status) {
    case 400:
      // 400 错误处理
      if (data.security_reason) {
        // 同一天重复提交限制
        return {
          showMessage: data.message || '此试卷今天已提交，明天才能重新提交',
          canRetry: false
        };
      } else if (data.error) {
        // 其他业务错误
        return {
          showMessage: data.message || '请求参数错误',
          canRetry: false
        };
      }
      break;

    case 401:
      // 401 未认证
      return {
        showMessage: '请先登录',
        canRetry: false
      };

    case 403:
      // 403 权限不足
      return {
        showMessage: data.message || '您没有权限执行此操作',
        canRetry: false
      };

    case 404:
      // 404 资源不存在
      return {
        showMessage: '请求的资源不存在',
        canRetry: false
      };

    case 429:
      // 429 限流错误
      return {
        showMessage: '请求过于频繁，请稍后重试',
        canRetry: true
      };

    case 500:
      // 500 服务器错误
      return {
        showMessage: '服务器错误，请稍后重试或联系支持',
        canRetry: true
      };

    default:
      return {
        showMessage: '未知错误，请稍后重试',
        canRetry: true
      };
  }

  return {
    showMessage: '请求失败，请稍后重试',
    canRetry: true
  };
};
```

---

### 修改5：更新类型定义

**文件位置：** `src/types/api.ts` 或相关类型定义文件

#### 5.1 生成新的类型定义

**在终端运行：**
```bash
# 1. 安装openapi-typescript工具
npm install -g openapi-typescript

# 2. 从后端API文档生成类型定义
openapi-typescript http://localhost:8000/api/schema/ > src/types/api.ts

# 3. 如果后端使用了JWT认证，可能需要添加认证头配置
openapi-typescript http://localhost:8000/api/schema/ --header "Authorization: Bearer YOUR_TOKEN_HERE" > src/types/api.ts
```

#### 5.2 手动添加类型定义（如果自动生成失败）

```typescript
// src/types/api.ts

// ✅ 新的提交响应接口
interface SubmissionResponse {
  message: string;
  statistics: {
    total_questions: number;
    total_scoreable: number;
    correct_count: number;
    wrong_count: number;
    empty_count: number;
    correct_rate: number;
  };
  submission_id: number;
  is_first_submit: boolean;
  can_retry: boolean;
  retry_info: {
    can_submit_now: boolean;
    reason: string;
    next_submit_time: string;
  };
}

// ✅ 错误响应接口
interface ErrorResponse {
  error: string;
  message: string;
  can_retry?: boolean;
  security_reason?: string;
  last_submit_time?: string;
  can_submit_time?: string;
  exam_id?: number;
}

// ✅ 试卷接口
interface Exam {
  id: number;
  exam_id: string;
  title: string;
  subject: 'math' | 'science';
  visible_date: string;
  questions: Question[];
}

// ✅ 问题接口
interface Question {
  id: number;
  q_id: string;
  q_type: string;
  stem: string;
  options: object;
  analysis: string;
  order: number;
  blank_configs: any[];
  // ❌ 注意：标准答案字段不在返回中
}

// ✅ 错题接口
interface WrongQuestion {
  id: number;
  student: number;
  question: Question;
  exam: Exam;
  exam_title: string;
  student_answer: object;
  question_details: {
    id: number;
    q_id: string;
    q_type: string;
    stem: string;
    options: object;
    answer_data: any;  // ✅ 错题本中包含标准答案
    analysis: string;
  };
  created_at: string;
}

// ✅ 提交记录接口
interface Submission {
  id: number;
  exam: number;
  student: number;
  student_answers: object;
  statistics: {
    total_questions: number;
    total_scoreable: number;
    correct_count: number;
    wrong_count: number;
    empty_count: number;
    correct_rate: number;
  };
  submit_time: string;
  updated_time: string;
}
```

---

## 🧪 测试验证步骤

### 测试1：首次提交（应该成功）
```typescript
// 测试步骤：
1. 打开任意试卷
2. 填写答案
3. 点击提交
4. 查看响应

// 预期结果：
✅ 提交成功
✅ 显示正确的正确率统计
✅ is_first_submit === true
✅ can_retry === false
✅ retry_info.next_submit_time 显示明天的日期
```

### 测试2：同一天重复提交（应该被拒绝）
```typescript
// 测试步骤：
1. 在同一天内，再次提交同一张试卷
2. 查看错误响应

// 预期结果：
✅ 返回400错误
✅ 显示"此试卷今天已提交，明天才能重新提交"
✅ 显示等待时间（比如"还需等待X小时"）
✅ 提交按钮被禁用或显示禁用状态
```

### 测试3：第二天重新提交（应该成功）
```typescript
// 测试步骤：
1. 等到第二天（或者修改系统时间测试）
2. 重新提交同一张试卷
3. 查看响应

// 预期结果：
✅ 提交成功
✅ is_first_submit === false
✅ 正确率统计正确更新
✅ 错题本正确更新
```

### 测试4：权限控制
```typescript
// 测试步骤：
1. 登录学生A账号
2. 尝试修改学生B的提交记录
3. 查看响应

// 预期结果：
✅ 返回403错误
✅ 显示权限错误提示
✅ 不能成功修改其他同学的记录
```

---

## 📋 修改检查清单

请按照以下清单检查你的修改：

### 核心功能
- [ ] 去除了所有`score`字段的引用
- [ ] 更新了提交响应处理逻辑
- [ ] 添加了正确率统计显示
- [ ] 添加了同一天重复提交限制处理
- [ ] 添加了`is_first_submit`状态显示

### 错误处理
- [ ] 400错误：显示同一天重复提交提示
- [ ] 401错误：引导用户登录
- [ ] 403错误：显示权限错误提示
- [ ] 404错误：显示资源不存在提示
- [ ] 500错误：显示重试按钮和联系支持

### 用户界面
- [ ] 提交确认对话框包含重要提醒
- [ ] 提交结果显示详细的正确率统计
- [ ] 错误提示清晰友好
- [ ] 按钮状态正确（禁用/启用）
- [ ] 显示"是否首次提交"标识

### 类型定义
- [ ] 更新了接口类型定义
- [ ] 移除了score字段类型
- [ ] 添加了statistics相关类型
- [ ] 添加了retry_info相关类型

---

## 🚨 常见问题和解决方案

### 问题1：找不到score字段
```
错误信息：Property 'score' does not exist on type 'SubmissionResponse'

解决方法：
- 使用 response.data.statistics.correct_rate 替代 response.data.score
- 更新所有显示分数的地方为显示正确率
```

### 问题2：TypeScript类型错误
```
错误信息：Type 'string' is not assignable to type 'number'

解决方法：
- 重新生成类型定义：openapi-typescript http://localhost:8000/api/schema/ > src/types/api.ts
- 检查API文档中字段的具体类型
- 确保使用了正确的类型转换
```

### 问题3：同一天重复提交仍然能提交
```
原因：前端没有正确处理can_retry字段

解决方法：
- 检查错误响应处理逻辑
- 确保400错误被正确捕获
- 显示错误提示并禁用提交按钮
```

### 问题4：错误提示不友好
```
原因：使用了默认的错误处理方式

解决方法：
- 使用统一的错误处理函数
- 根据错误类型显示不同的友好提示
- 添加重试按钮（针对网络错误）
```

---

## 📝 完成后请告诉我

修改完成后，请告诉我：

1. ✅ 哪些文件被修改了？
2. ✅ 是否遇到了TypeScript类型错误？
3. ✅ 同一天重复提交限制是否正常工作？
4. ✅ 是否有其他问题或疑问？

如果遇到任何问题，请详细描述：
- 问题的具体表现
- 错误信息
- 重现步骤
- 期望的结果

---

*这个文档会随着后端API的更新而更新，请保持关注*