<template>
  <div class="container">
    <!-- 左侧菜单 -->
    <aside class="sidebar">
      <ul>
        <li v-for="record in records" :key="record.id">{{ record.name }}</li>
      </ul>
    </aside>

    <!-- 右侧内容区域 -->
    <main class="content">
      <!-- 显示用户输入的内容 -->
      <div v-if="userInputs.length > 0" class="user-input-area centered-content">
        <div v-for="(input, index) in userInputs" :key="index" class="user-input">
          <pre>{{ input }}</pre>
        </div>
      </div>

      <!-- 条件渲染：当 testCases 数组为空时显示介绍文字 -->
      <div v-if="testCases.length === 0 && userInputs.length === 0" class="centered-content">
        <h1>白盒</h1>
        <p>你的自动测试小助手</p>
        <p>输入测试代码，你将得到：程序流程图、基本路径集合、测试用例</p>
      </div>

      <!-- 测试结果显示在输入框上方 -->
      <div v-if="testCases.length > 0" class="output-area centered-content">
        <div v-for="(testCase, index) in testCases" :key="index" class="test-case">
          <p>测试用例 {{ index + 1 }}:</p>
          <p>&nbsp;&nbsp;输入: {{ formatInputs(testCase.inputs) }}</p>
          <p>&nbsp;&nbsp;条件: {{ testCase.conditions }}</p>
        </div>
      </div>

      <div class="input-area centered-content">
        <div class="input-row">
          <textarea
              v-model="code"
              placeholder="请输入你要进行测试的代码"
              class="code-input"
          ></textarea>
          <button @click="submitCode" class="submit-button">提交代码</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      records: [
        { id: 1, name: '记录1' },
        { id: 2, name: '记录2' },
        { id: 3, name: '记录3' }
      ],
      code: '',
      userInputs: [],  // 存储用户的输入内容
      testCases: [],  // 用于存储生成的测试用例
    };
  },
  methods: {
    async submitCode() {
      if (this.code.trim() === '') return;  // 防止提交空输入

      // 保存用户的输入
      this.userInputs.push(this.code);

      try {
        // 调用后端 API 处理用户输入的代码
        const response = await fetch('http://127.0.0.1:5001/api/process_code', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ code: this.code })
        });

        if (response.ok) {
          const result = await response.json();
          this.testCases = result.testCases;  // 假设后端返回的结果包含 testCases 字段
          this.code = '';  // 清空输入框
        } else {
          console.error('Error processing code');
        }
      } catch (error) {
        console.error('Error submitting code:', error);
      }
    },
    formatInputs(inputs) {
      // 将 inputs 对象格式化为类似 "{'age': -346, 'b': -886}" 的字符串
      return JSON.stringify(inputs).replace(/"/g, "'")
    }
  }
};
</script>

<style scoped>
.container {
  display: flex;
  height: 100vh;
  background-color: #f4f4f4;
  overflow-y: auto; /* 为整个页面添加一个垂直滚动条 */
}

.sidebar {
  width: 20%; /* 缩小左侧菜单栏的宽度 */
  background-color: #f9f9f9;
  padding: 20px;
  border-right: 1px solid #ddd;
  height: 100vh;
}

.sidebar ul {
  list-style: none;
  padding: 0;
}

.sidebar li {
  padding: 10px 0;
  cursor: pointer;
}

.sidebar li:hover {
  background-color: #e0e0e0;
}

.content {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center; /* 保持框居中 */
  padding: 20px;
}

.centered-content {
  width: 70%; /* 调整右侧内容的宽度，保持框居中 */
  max-width: 600px; /* 设置最大宽度 */
}

.user-input-area {
  margin-bottom: 20px;
  background-color: #ffffff;
  border: 1px solid #ccc;
  padding: 10px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  text-align: left;
}

.user-input {
  background-color: #e0e0e0;
  padding: 20px;
  border-radius: 5px;
  margin-bottom: 10px;
}

.user-input pre {
  white-space: pre-wrap; /* 保留换行符和空格 */
  font-family: monospace; /* 使用等宽字体 */
  margin: 0;
}

.input-area {
  margin-top: 20px; /* 可以根据需要调整 */
  width: 100%;
}

.input-row {
  display: flex; /* 将输入框和按钮排列在同一行 */
  align-items: center; /* 使按钮与输入框垂直居中对齐 */
}

.code-input {
  width: 100%;
  height: 50px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: none; /* 禁用 textarea 调整大小 */
  font-family: monospace; /* 使用等宽字体 */
  white-space: pre; /* 保留空白字符和换行 */
  margin-right: 10px; /* 为按钮留出一些空间 */
}

.submit-button {
  padding: 10px 20px;
  background-color: #535553;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  flex-shrink: 0;
}

.submit-button:hover {
  background-color: #888f88;
}

.output-area {
  margin-bottom: 20px; /* 调整结果和输入框之间的间距 */
  background-color: #ffffff;
  border: 1px solid #ccc;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  text-align: left; /* 确保内容是左对齐的 */
}

.test-case {
  background-color: #f4f4f4;
  padding: 10px;
  border-radius: 5px;
  margin-bottom: 10px;
}
</style>
