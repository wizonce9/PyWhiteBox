<template>
  <div class="login-container">
    <div class="login-box">
      <h2>用户登录</h2>
      <el-form ref="loginForm" :model="loginForm" :rules="rules" label-width="0px">
        <!-- 用户名 -->
        <el-form-item prop="username">
          <el-input class="el-input-user" v-model="loginForm.username" placeholder="请输入用户名">
            <template #prefix>
              <img class="icon" src="../assets/用户.png" />
            </template>
          </el-input>
        </el-form-item>

        <!-- 密码 -->
        <el-form-item prop="password">
          <el-input class="el-input-pass" v-model="loginForm.password" type="password" placeholder="请输入密码">
            <template #prefix>
              <img class="icon" src="../assets/密码.png" />
            </template>
          </el-input>
        </el-form-item>

        <!-- 记住我复选框 -->
        <el-form-item>
          <div class="remember-me">
            <el-checkbox v-model="rememberMe">记住我</el-checkbox>
          </div>
        </el-form-item>

        <!-- 登录按钮 -->
        <el-button class="el-button-login" type="primary" @click="submitForm">登录</el-button>
        <div class="register-link">
          没有账号？ <router-link to="/register">去注册</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      loginForm: {
        username: '',
        password: '',
      },
      rememberMe: false, // 是否记住用户
      rules: {
        username: [{required: true, message: '请输入用户名', trigger: 'blur'}],
        password: [{required: true, message: '请输入密码', trigger: 'blur'}],
      },
    };
  },
  mounted() {
    // 页面加载时检查本地存储，自动填充用户名和密码
    const savedUsername = localStorage.getItem('username');
    const savedPassword = localStorage.getItem('password'); // 注意安全性
    if (savedUsername) {
      this.loginForm.username = savedUsername;
      this.loginForm.password = savedPassword;
      this.rememberMe = true; // 如果有存储信息，则默认勾选“记住我”
    }
  },
  methods: {
    async submitForm() {
      this.$refs.loginForm.validate(async (valid) => {
        if (valid) {
          try {
            // 发送登录请求
            // const response = await fetch('http://localhost:28080/api/login', {
            const response = await fetch('http://124.70.51.109:28080/api/login', {
              method: 'POST',
              body: JSON.stringify(this.loginForm),
              headers: {
                'Content-Type': 'application/json'
              },
            });
            const result = await response.json();

            if (result.status === 'success') {
              // 登录成功后的处理
              localStorage.setItem('token', result.token); // 存储 Token

              if (this.rememberMe) {
                // 如果选择了“记住我”，存储用户名和密码
                localStorage.setItem('username', this.loginForm.username);
                localStorage.setItem('password', this.loginForm.password); // 注意：生产环境建议加密存储
              } else {
                // 如果未选择“记住我”，清除存储
                localStorage.removeItem('username');
                localStorage.removeItem('password');
              }
              this.$message.success('登录成功');
              this.$router.push('/home'); // 跳转到首页或其他页面
            } else {
              // 登录失败提示
              this.$message.error(result.message || '登录失败');
            }
          } catch (error) {
            console.error('登录请求出错:', error);
            this.$message.error('服务器错误，请稍后再试');
          }
        }
      });
    },
  }
};
</script>

<style scoped>
h2 {
  font-family: '方正清刻本悦宋简体', sans-serif; /* 使用微软雅黑字体，您可以更换为其他字体 */
  color: #333333; /* 颜色设置为深灰色，可以根据需要调整 */
  font-size: 30px; /* 字体大小调整为24像素 */
  font-weight: normal; /* 字体加粗 */
  margin-bottom: 15px; /* 增加下方的间距 */
}

.login-container {
  background-image: url('../assets/水墨背景蒙版.png');
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-size: cover; /* 背景图像覆盖整个容器 */
}

.login-box {
  background-color: rgba(255, 255, 255, 0.8); /* 调整为半透明白色背景 */
  padding: 40px; /* 内边距稍微减少使得整体更紧凑 */
  border-radius: 12px; /* 圆角增加，更加柔和 */
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2); /* 增强阴影效果 */
  width: 300px; /* 调整宽度，使其看起来更符合第二张图片的样式 */
  height: 310px;
  text-align: center;
  font-size: 18px; /* 保持字体大小一致 */
}

.icon {
  width: 24px;
  height: 24px;
  position: relative; /* 使其可以相对于默认位置进行偏移 */
  top: 5px; /* 向下偏移 2 像素 */
  left: 0px; /* 向左偏移 4 像素 */
}

.el-input-user {
  height: 45px; /* 输入框稍微缩小高度 */
  font-size: 16px; /* 调整字体大小 */
}

.el-input-pass {
  height: 45px; /* 输入框稍微缩小高度 */
  font-size: 16px; /* 调整字体大小 */
}

.el-button-login {
  height: 45px; /* 调整按钮的高度 */
  font-size: 18px; /* 调整按钮文字的字体大小 */
  padding: 0 20px; /* 调整按钮内边距 */
  margin-top: -20px; /* 增加顶部间距 */
  background-color: #a64242; /* 调整按钮颜色为类似深红色 */
  border: none; /* 移除边框 */
}

.el-button-login:hover {
  background-color: #8c3737; /* 调整鼠标悬浮时的按钮颜色 */
}

.remember-me {
  display: flex;
  align-items: center;
  margin-top: -10px;
  font-size: 14px;
  color: #555;
}

.remember-me .el-checkbox {
  margin-right: 8px; /* 复选框与文字的间距 */
}

.remember-me .checkbox .el-checkbox__input.is-checked + .el-checkbox__label {
  color: #8c3737; /* 当复选框被选中时，文字变红 */
}

.register-link {
  margin-top: 10px; /* 减少顶部的间距 */
  color: #555;
}

.register-link a {
  color: #a64242; /* 调整链接颜色，保持一致 */
  text-decoration: none; /* 移除下划线 */
}

.register-link a:hover {
  text-decoration: underline; /* 鼠标悬浮时显示下划线 */
}
</style>
