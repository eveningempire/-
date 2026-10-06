<template><div class="login"><div class="card"><h1>重复使用运载器发射场健康管理平台</h1><el-form :model="form" @submit.prevent="submit"><el-form-item><el-input v-model="form.username" placeholder="用户名"/></el-form-item><el-form-item><el-input v-model="form.password" type="password" placeholder="密码"/></el-form-item><el-button type="primary" native-type="submit" :loading="loading">登录系统</el-button></el-form><small>用户账号由管理员创建</small></div></div></template>
<script setup>
import { reactive, ref } from 'vue'; import { useRouter, useRoute } from 'vue-router'; import { ElMessage } from 'element-plus';
const router=useRouter(), route=useRoute(), form=reactive({username:'',password:''}), loading=ref(false);
async function submit(){loading.value=true;try{const r=await fetch('/api/v1/auth/login/',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(form)});const d=await r.json();if(!r.ok)throw Error(d.detail||'登录失败');sessionStorage.setItem('user',JSON.stringify(d));router.replace(route.query.redirect||'/')}catch(e){ElMessage.error(e.message)}finally{loading.value=false}}
</script>
<style scoped>.login{min-height:100vh;display:grid;place-items:center;background:#0b1d35}.card{width:390px;padding:40px;background:#fff;border-radius:16px;text-align:center}.card h1{margin:0 0 24px}.el-button{width:100%}small{display:block;margin-top:20px;color:#9aa6b5}</style>
