<template>
  <div class="register-container">
    <div class="register-box">
      <h2>用户注册</h2>
      <el-form ref="registerForm" :model="registerForm" :rules="rules" label-width="0px">
        <el-form-item prop="username">
          <el-input class="el-input-user" v-model="registerForm.username" placeholder="请输入用户名">
            <template #prefix>
              <img class="icon" src="../assets/用户.png" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="password">
          <el-input class="el-input-pass" v-model="registerForm.password" type="password" placeholder="请输入密码">
            <template #prefix>
              <img class="icon" src="../assets/密码.png" />
            </template>
          </el-input>
        </el-form-item>

        <el-form-item prop="confirmPassword">
          <el-input class="el-input-word" v-model="registerForm.confirmPassword" type="password" placeholder="请确认密码">
            <template #prefix>
              <img class="icon" src="../assets/密码.png" />
            </template>
          </el-input>
        </el-form-item>

        <el-button class="el-button-zhu" type="primary" @click="submitForm">注册</el-button>
        <div class="login-link">
          已有账号？ <router-link to="/login">去登录</router-link>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      registerForm: {
        username: '',
        password: '',
        confirmPassword: '',
      },
      rules: {
        username: [
          { required: true, message: '请输入用户名', trigger: 'blur' },
          { min: 4, max: 10, message: '用户名长度为4-10个字符', trigger: 'blur' }
        ],
        password: [
          { required: true, message: '请输入密码', trigger: 'blur' },
          { min: 6, max: 15, message: '密码长度为6-15个字符', trigger: 'blur' }
        ],
        confirmPassword: [
          { required: true, message: '请确认密码', trigger: 'blur' },
          { validator: this.validatePassword, trigger: 'blur' }
        ]
      }
    };
  },
  methods: {
    validatePassword(rule, value, callback) {
      if (value !== this.registerForm.password) {
        callback(new Error('两次密码不一致，请重新输入密码'));
      } else {
        callback();
      }
    },
    submitForm() {
      this.$refs.registerForm.validate(async (valid) => {
        if (valid) {
          // 调用后端API检查用户名是否存在
          const response = await this.checkUsername(this.registerForm.username);
          if (response.exists) {
            this.$message.error('用户名已存在，请重新输入');
          } else {
            // 如果用户名不存在，则继续注册
            await this.registerUser(this.registerForm);
            this.$message.success('注册成功');
            this.$router.push('/login');
          }
        }
      });
    },

    async checkUsername(username) {
      try {
        const response = await fetch('http://localhost:28080/api/check-username', {
        // const response = await fetch('http://124.70.51.109:28080/api/check-username', {
          method: 'POST',
          body: JSON.stringify({ username }),
          headers: {
            'Content-Type': 'application/json'
          }
        });
        return await response.json();
      } catch (error) {
        console.error('Error fetching check-username API:', error);
        throw error;
      }
    },

    async registerUser(registerForm) {
      // 发送请求将用户名和密码保存到数据库
      const response = await fetch('http://localhost:28080/api/register', {
      // const response = await fetch('http://124.70.51.109:28080/api/register', {
        method: 'POST',
        body: JSON.stringify(registerForm),
        headers: {
          'Content-Type': 'application/json'
        }
      });
      return await response.json();
    }
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

.register-container {
  background-image: url('../assets/水墨背景蒙版.png');
  height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background-size: cover; /* 背景图像覆盖整个容器 */
}

.register-box {
  background-color: rgba(255, 255, 255, 0.8); /* 调整为半透明白色背景 */
  padding: 40px; /* 内边距稍微减少使得整体更紧凑 */
  border-radius: 12px; /* 圆角增加，更加柔和 */
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.2); /* 增强阴影效果 */
  width: 300px; /* 调整宽度，使其看起来更符合第二张图片的样式 */
  height: 350px;
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

.el-button-zhu {
  height: 45px; /* 调整按钮的高度 */
  font-size: 18px; /* 调整按钮文字的字体大小 */
  padding: 0 20px; /* 调整按钮内边距 */
  margin-top: 10px; /* 增加顶部间距 */
  background-color: #a64242; /* 调整按钮颜色为类似深红色 */
  border: none; /* 移除边框 */
}

.el-button-zhu:hover {
  background-color: #8c3737; /* 调整鼠标悬浮时的按钮颜色 */
}

.login-link {
  margin-top: 10px; /* 减少顶部的间距 */
  color: #555;
}

.login-link a {
  color: #a64242; /* 调整链接颜色，保持一致 */
  text-decoration: none; /* 移除下划线 */
}

.login-link a:hover {
  text-decoration: underline; /* 鼠标悬浮时显示下划线 */
}

.el-input-word {
  height: 40px; /* 增大输入框高度 */
  font-size: 18px; /* 增大输入框内字体的大小 */
}


</style>
