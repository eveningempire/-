

<template>
  <!-- <h1>You did it!222</h1> -->
   <div>

  
 
  <div class="auth-container"> 
    <div style="color: black;font-size: 32px; font-family: Arial, sans-serif;font-weight: bold; margin-bottom: 50px ;">健康管理平台</div>
    <el-form  ref="loginRef" :model="form" :rules="loginrules" label-position="top" class="auth-form">
      <el-form-item label="用户名" prop="username">
        <el-input v-model="form.username" placeholder="请输入用户名" class="input-field">
          <template #prepend>
            <el-icon><UserFilled /></el-icon> 
          </template>
        </el-input>
      </el-form-item>
      <el-form-item label="密码" prop="password">
        <el-input
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          placeholder="请输入密码"
          class="input-field"
        >
          <template #prepend>
            <el-icon><Lock /></el-icon> <!-- 在密码输入框前插入图标 -->
          </template>
          <template #append>
            <el-icon @click="togglePasswordVisibility">
              <component :is="showPassword ? 'Hide' : 'View'" />
            </el-icon> <!-- 在密码输入框后插入可切换的图标 -->
          </template>
        </el-input>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" @click.prevent="logintohome" class="confirm-button">登录</el-button>
      </el-form-item>
    </el-form>
  </div>

  </div>
</template>

<script>
import { UserFilled, Lock, View, Hide } from '@element-plus/icons-vue';
import { ref } from 'vue';

import axios from 'axios';
export default{
  components: {
    UserFilled,
    Lock,
    View,
    Hide,
  },
  data(){
    return{
 form: ref({
        username: '',
        password: '',
      }),
      loginRef: ref(null),
      showPassword: false, // 控制密码显示
      showConfirmPassword: false, // 控制确认密码显示
      loginrules: {
        username:[{required:true,trigger:"blur",message:"请输入您的账号"}],
        password:[{required:true,trigger:"blur",message:"请输入您的密码"}],
      },
      
    };
  },
  methods:{

    async logintohome(){
      try {
          const res = await axios.post(`http://localhost:8000/algorithm/loginuser/`, {
           username:this.form.username,password:this.form.password
          });
          console.log("返回数据:", res.data.success);
          if(res.data.success){
           this.$router.push('/home');
           this.$message.success("登录成功!");
          }else{
            this.$message.error("用户名或密码错误!");
          }

                

          // 这里你可以调用 echart 绘图
          //this.initChart();
        } catch (error) {
          console.error("返回数据失败:", error);
        }
 

      // 跳转到 /home


      },

       togglePasswordVisibility() {
      this.showPassword = !this.showPassword;},


  },
}

</script>

<style scoped>
.auth-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100vh;
  background-image: url('@/assets/login.png');
  background-size: cover;
  background-position: center;
}
.auth-toggle {
  display: flex;
  justify-content: space-between;
  width: 300px;
  margin-bottom: 20px;
}

.toggle-button {
  background-color: blue;
  color: white;
}

.auth-form {
  max-width: 400px;
  width: 100%;
  padding: 20px;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  background-color: rgba(255, 255, 255, 0.8);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.input-field {
  background-color: black;
  color: white;
}

.input-field::placeholder {
  color: gray;
}

.icon {
  background-color: black;
  color: gray;
}

.submit-button {
  display: flex;
  justify-content: center;
}

.confirm-button {
  background-color: blue;
  color: white;
  justify-content: center;
}
</style>
