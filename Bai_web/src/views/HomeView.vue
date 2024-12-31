<template>
  <div class="container">
    <!-- 左侧菜单 -->

    <aside class="sidebar">
      <h2 class="sidebar-title">保存的记录</h2>
      <ul>
        <li v-for="record in savedRecords" :key="record.id" class="record-item">
          <div @click="loadRecord(record.id)" class="record-name">
            {{ record.name }}
          </div>
          <div class="record-actions">
            <button @click.stop="downloadRecord(record)" class="action-button download-button">下载</button>
            <button @click.stop="deleteRecord(record.id)" class="action-button delete-button">删除</button>
          </div>
        </li>
      </ul>
    </aside>
    <!-- 右侧内容区域 -->
    <main class="main-content">
      <!-- 选择方法的独立区域 -->
      <div class="selection-area">
        <div class="navbar">
          <div class="navbar-item" @click="logout">注销</div>
        </div>
        <el-select v-model="selectedOption" placeholder="请选择测试方法" class="method-select">
          <el-option
              v-for="item in options"
              :key="item.value"
              :label="item.label"
              :value="item.value">
          </el-option>
        </el-select>
      </div>

      <!-- 上半部分，包含用户输入显示和测试结果 -->
      <div class="upper-content">
        <transition-group name="fade" tag="div">
          <div v-for="(block, index) in responseBlocks" :key="index" class="response-block">
            <div v-if="block.flowchartPath" class="flowchart-container">
              <img :src="block.flowchartPath" alt="流程图" class="flowchart-image"/>
            </div>
            <div class="user-input">
              <h3>代码:</h3>
              <pre>{{ block.code }}</pre>
            </div>
            <div class="output-area">
              <div v-if="block.testCases && block.testCases.length && !block.hasLoop">
                <h3>测试用例:</h3>
                <div v-for="(testCase, i) in block.testCases" :key="i" class="test-case">
                  <p><strong>测试用例 {{ i + 1 }}:</strong></p>
                  <p>输入: {{ formatInputs(testCase.inputs) }}</p>
                  <p>条件:  {{ testCase.conditions }}</p>
                </div>
              </div>
              <div v-else-if="block.responseText">
                <h3>响应文本:</h3>
                <pre class="response-text">{{ block.responseText }}</pre>
              </div>
              <div v-if="block.selectedOption" class="method-info">
                <p><strong>测试方法:</strong> {{ getOptionLabel(block.selectedOption) }}</p>
              </div>
            </div>
          </div>
        </transition-group>
        <div v-if="responseBlocks.length === 0" class="intro-content">
          <h1>白盒测试通</h1>
          <p>你的自动测试小助手</p>
          <p>输入测试代码，你将得到：程序流程图、基本路径集合、测试用例</p>
        </div>
      </div>

      <!-- 下半部分，固定的输入框 -->
      <div class="input-area">
        <div class="input-row">
          <textarea
              v-model="code"
              placeholder="请输入你要进行测试的代码"
              class="code-input"
              @input="autoResize"
              ref="codeInput"
          ></textarea>
          <div class="button-group">
            <button @click="submitCode" class="submit-button">提交代码</button>
            <button @click="saveRecord" class="save-button">保存记录</button>
            <button @click="clearScreen" class="clear-button">清空屏幕</button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script>
export default {
  data() {
    return {
      code: '',
      responseBlocks: [],  // 当前显示的输出内容
      selectedOption: 'option1',
      options: [
        { value: 'option1', label: '基本路径测试' },
        { value: 'option2', label: '路径覆盖测试' },
        { value: 'option3', label: 'GPT测试' }
      ],
      savedRecords: [], // 存储保存的输出记录
      currentRecordId: null // 当前显示的记录ID
    };
  },
  methods: {
    // 注销功能
    logout() {
      this.$confirm('是否退出登录？', '提示', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      })
          .then(() => {
            this.$router.push('/login');
          })
          .catch(() => {
            this.$message.info('已取消退出');
          });
    },
    async submitCode() {
      if (this.code.trim() === '') return;
      const currentCode = this.code;

      // Improved loop detection for "for" or "while" using word boundaries
      const hasLoop = /\b(for|while)\b/.test(currentCode);

      try {
        const processResponse = await fetch('http://124.70.51.109:5002/api/process_code', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ code: this.code, option: this.selectedOption })
        });

        if (processResponse.ok) {
          const result = await processResponse.json();
          const newBlock = {
            code: currentCode,
            flowchartPath: `http://124.70.51.109:5002${result.flowchartPath}`,
            selectedOption: this.selectedOption,
            hasLoop: hasLoop  // Store if loop exists
          };

          // Only add test cases if no loop is detected
          if (!hasLoop && (this.selectedOption === 'option1' || this.selectedOption === 'option2')) {
            newBlock.testCases = result.testCases;
          } else if (this.selectedOption === 'option3') {
            newBlock.responseText = result.responseText;
          }

          this.responseBlocks.push(newBlock);
          this.code = '';
          this.resetTextareaHeight();
        } else {
          // If the backend responds with an error, show an alert message
          const error = await processResponse.json();
          console.error('Error processing code:', error.error);
          alert("错误: 请输入标准python代码");
        }
      } catch (error) {
        console.error('Error submitting code:', error);
        alert("错误: 请输入标准python代码");
      }
    },
    saveRecord() {
      if (this.responseBlocks.length === 0) return; // 如果没有输出，不保存
      const newRecord = {
        id: Date.now(), // 使用时间戳作为唯一ID
        name: `记录 ${this.savedRecords.length + 1}`,
        responseBlocks: [...this.responseBlocks] // 保存当前的输出内容
      };
      this.savedRecords.push(newRecord);
      this.currentRecordId = newRecord.id;
      alert('记录已保存');
    },
    loadRecord(recordId) {
      const record = this.savedRecords.find(r => r.id === recordId);
      if (record) {
        this.currentRecordId = record.id;
        this.responseBlocks = [...record.responseBlocks];
      }
    },
    deleteRecord(recordId) {
      const index = this.savedRecords.findIndex(r => r.id === recordId);
      if (index !== -1) {
        if (confirm('确定要删除此记录吗？')) {
          this.savedRecords.splice(index, 1);
          // 如果删除的是当前显示的记录，清空显示
          if (this.currentRecordId === recordId) {
            this.currentRecordId = null;
            this.responseBlocks = [];
          }
          alert('记录已删除');
        }
      }
    },
    async downloadRecord(record) {
      // 创建一个HTML字符串，包含图片和文本内容
      let htmlContent = `
        <html>
          <head>
            <meta charset="UTF-8">
            <title>${record.name}</title>
            <style>
              body { font-family: Arial, sans-serif; padding: 20px; }
              .section { margin-bottom: 20px; }
              .section img { max-width: 100%; height: auto; }
              .section pre { background-color: #f4f4f4; padding: 10px; border-radius: 4px; }
              .test-case { background-color: #f4f4f4; padding: 10px; border-radius: 4px; margin-bottom: 10px; }
              .test-case p { margin: 5px 0; }
              h1 { text-align: center; }
              h2 { color: #333; }
            </style>
          </head>
          <body>
            <h1>${record.name}</h1>
            <p><strong>测试方法:</strong> ${this.getOptionLabel(record.responseBlocks[0]?.selectedOption)}</p>
      `;
      for (const block of record.responseBlocks) {
        htmlContent += `<div class="section">`;
        // 添加流程图图片
        if (block.flowchartPath) {
          try {
            const imageBase64 = await this.convertImageToBase64(block.flowchartPath);
            htmlContent += `<h2>流程图:</h2>`;
            htmlContent += `<img src="data:image/png;base64,${imageBase64}" alt="流程图"/>`;
          } catch (error) {
            console.error('Error fetching image:', error);
            htmlContent += `<p>流程图无法加载。</p>`;
          }
        }
        // 添加代码
        htmlContent += `<h2>代码:</h2>`;
        htmlContent += `<pre style="text-align: left;">${this.escapeHtml(block.code)}</pre>`;
        // 添加测试用例或响应文本
        if (block.testCases && block.testCases.length) {
          htmlContent += `<h2>测试用例:</h2>`;
          for (const [i, testCase] of block.testCases.entries()) {
            htmlContent += `
              <div class="test-case">
                <p><strong>测试用例 ${i + 1}:</strong></p>
                <p>输入: ${this.formatInputs(testCase.inputs)}</p>
                <p>条件: ${testCase.conditions}</p>
              </div>
            `;
          }
        } else if (block.responseText) {
          htmlContent += `<h2>响应文本:</h2>`;
          htmlContent += `<pre style="text-align: left;">${this.escapeHtml(block.responseText)}</pre>`;
        }
        htmlContent += `</div>`;
      }
      htmlContent += `
          </body>
        </html>
      `;
      // 创建Blob并触发下载
      const blob = new Blob([htmlContent], { type: 'application/msword' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `${record.name}.doc`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    },
    // 将图片URL转换为Base64
    async convertImageToBase64(url) {
      const response = await fetch(url, { mode: 'cors' });
      const blob = await response.blob();
      return await this.blobToBase64(blob);
    },
    // 将Blob转换为Base64
    blobToBase64(blob) {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64data = reader.result.split(',')[1]; // 去掉前缀
          resolve(base64data);
        };
        reader.onerror = reject;
        reader.readAsDataURL(blob);
      });
    },
    clearScreen() {
      this.responseBlocks = []; // 清空当前显示的输出内容
    },
    resetTextareaHeight() {
      const element = this.$refs.codeInput;
      element.style.height = 'auto';
    },
    formatInputs(inputs) {
      return JSON.stringify(inputs, null, 2).replace(/"/g, "'");
    },
    // 转义HTML特殊字符
    escapeHtml(text) {
      const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
      };
      return text.replace(/[&<>"']/g, function(m) { return map[m]; });
    },
    // 获取选项的标签
    getOptionLabel(value) {
      const option = this.options.find(opt => opt.value === value);
      return option ? option.label : value;
    }
  }
};
</script>

<style scoped>
/* 基本布局 */
html, body {
  margin: 0;
  padding: 0;
  height: 100%;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  background-color: #f0f2f5;
  color: #333;
}

.navbar-item {
  position: absolute; /* 定位该元素 */
  top: 25px; /* 距离顶部 10px */
  right: 100px; /* 距离右边 10px */
  cursor: pointer; /* 鼠标悬停时显示为手形 */
  padding: 12px 25px; /* 添加按钮内边距 */
  background-color: #d3d3d3; /* 背景色，确保可见 */
  border-radius: 5px; /* 圆角 */
  font-family: '方正清刻本悦宋简体', sans-serif;
  font-size: 18px;
  transition: background-color 0.3s; /* 增加一个背景色变化效果 */
}

.navbar-item:hover {
  background-color: #ccc; /* 鼠标悬停时改变背景色 */
}

.container {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 20%;
  background-color: #f9f9f9; /* 浅灰色背景 */
  color: #333;
  padding: 0px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
}

.sidebar-title {
  font-size: 1.5em;
  margin-bottom: 0px;
  text-align: center;
  padding-bottom: 0px;
}

.sidebar ul {
  list-style: none;
  padding: 0;
  flex: 1;
  overflow-y: auto;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  background-color: #fff; /* 浅色记录框 */
  border: 1px solid #ddd;
  border-radius: 4px;
  margin-bottom: 10px;
  transition: background-color 0.3s, transform 0.2s;
  cursor: pointer;
}

.record-item:hover {
  background-color: #e6f7ff; /* 浅蓝色悬停 */
  transform: translateY(-2px);
}

.record-name {
  flex: 1;
  margin-right: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.record-actions {
  display: flex;
  gap: 5px;
}

.action-button {
  padding: 5px 10px;
  background-color: #ccc; /* 白灰色按钮背景 */
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s;
  font-size: 0.8em;
}

.download-button {
  background-color: #ddd; /* 浅灰色用于下载 */
}

.delete-button {
  background-color: #ccc; /* 浅灰色用于删除 */
}

.action-button:hover {
  background-color: #bbb; /* 更深的灰色悬停 */
  transform: scale(1.05);
}

/* 主要内容区域 */
.main-content {
  width: 80%;
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

/* 选择方法区域 */
.selection-area {
  padding: 20px;
  background-color: #fff;
  border-bottom: 1px solid #d9d9d9;
  display: flex;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.method-select {
  margin-right: 300px;
  width: 250px;
  font-size: 18px;
  transition: box-shadow 0.3s;
}

.method-select:hover {
  box-shadow: 0 0 5px rgba(24, 144, 255, 0.5);
}

/* 上半部分内容 */
.upper-content {
  flex: 1;
  overflow-y: auto;
  padding: 70px 150px;
  background-color: #f0f2f5;
  transition: background-color 0.3s;
}

.intro-content {
  text-align: center;
  width: 600px;
  height: 177px;
  padding: 40px 20px;
  background-color: #fff;
  border-radius: 8px;
  font-family: '微软雅黑', sans-serif;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 确保阴影一直存在 */
}

.intro-content:hover,
.intro-content:active,
.intro-content:focus {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1); /* 确保交互时阴影样式不变 */
}

.response-block {
  text-align: center;
  background-color: #fff;
  border-radius: 8px;
  padding: 20px;
  font-size: 18px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transition: transform 0.3s;
}

.response-block:hover {
  transform: translateY(-2px);
}

.flowchart-container {
  justify-content: center; /* 水平居中 */
  margin-bottom: 10px;
}

.flowchart-image {
  justify-content: center; /* 水平居中 */
  max-width: 100%;
  height: auto;
  border-radius: 4px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.user-input h3,
.output-area h3 {
  text-align: center;
  margin-top: 0;
  color: #333;
}

.user-input pre,
.output-area pre {
  background-color: #f5f5f5;
  padding: 10px;
  border-radius: 4px;
  overflow-x: auto;
  text-align: left; /* Ensures left alignment */
  white-space: pre; /* Maintains original formatting */
}

.test-case {
  text-align: center;
  background-color: #fafafa;
  padding: 10px;
  border-radius: 4px;
  margin-bottom: 10px;
  transition: background-color 0.3s;
}

.test-case:hover {
  background-color: #f0f0f0;
}

.method-info {
  text-align: center;
  margin-top: 10px;
  font-style: italic;
  color: #555;
}

.response-text {
  text-align: center;
  font-size: 18px;
  white-space: pre-wrap;  /* 保持换行 */
  word-wrap: break-word;  /* 长单词或 URL 也换行 */
  overflow-wrap: break-word;  /* 兼容性 */
}

/* 下半部分输入区域 */
.input-area {
  padding: 10px;
  height: 160px;
  background-color: #fff;
  border-top: 1px solid #d9d9d9;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
}

.input-row {
  display: flex;
  width: 100%;
  max-width: 1200px;
  gap: 10px;
  flex-wrap: nowrap;
  align-items: center; /* 使按钮组垂直居中 */
}

.code-input {
  flex: 1;
  width: 100%;
  height: 100px; /* Set a fixed height */
  max-height: 100px; /* Fixed max-height to prevent resizing */
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  resize: none;
  font-family: monospace;
  white-space: pre-wrap;
  overflow-y: auto; /* Enable vertical scrolling */
  line-height: 1.5;
  box-sizing: border-box;
  text-align: left;
  font-size: 18px;
}


.code-input:focus {
  border-color: #1890ff;
  box-shadow: 0 0 5px rgba(24, 144, 255, 0.5);
}

.button-group {
  display: flex;
  font-size: 18px;
  gap: 10px;
  flex-wrap: nowrap;
  flex-shrink: 0;
  align-items: center; /* 使按钮内部内容垂直居中 */
}

.submit-button,
.save-button,
.clear-button {
  width: 120px; /* 固定宽度 */
  height: 50px; /* 固定高度 */
  background-color: #ccc; /* 白灰色背景 */
  font-size: 18px;
  color: #333;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s, transform 0.2s;
  flex: 0 0 auto; /* 防止按钮缩放 */
}

.submit-button:hover,
.save-button:hover,
.clear-button:hover {
  background-color: #bbb; /* 更深的灰色悬停 */
  transform: scale(1.05);
}

/* 过渡效果 */
.fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to /* .fade-leave-active for below version 2.1.8 */ {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 1024px) {
  .sidebar {
    width: 25%;
  }
}

@media (max-width: 768px) {
  .container {
    flex-direction: column;
  }

  .sidebar {
    width: 100%;
    height: 200px;
    overflow-y: auto;
  }

  .main-content {
    width: 100%;
  }

  .input-row {
    flex-direction: column;
  }

  .button-group {
    justify-content: center;
  }

  /* Adjust button sizes for smaller screens if necessary */
  .submit-button,
  .save-button,
  .clear-button {
    min-width: 80px;
  }
}
</style>
