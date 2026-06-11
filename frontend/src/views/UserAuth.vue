<template>
  <div class="auth-container">
    <div class="auth-box">
      <h2>내 신고 기록 조회</h2>
      <p class="auth-desc">신고서 접수 시 입력했던 이름과 이메일 주소를 입력해 주세요.</p>
      
      <form @submit.prevent="handleAuth">
        <div class="input-group">
          <label for="userName">이름</label>
          <input 
            type="text" 
            id="userName" 
            v-model="authData.user_name" 
            placeholder="이름을 입력하세요" 
            required
          />
        </div>

        <div class="input-group">
          <label for="userEmail">이메일</label>
          <input 
            type="email" 
            id="userEmail" 
            v-model="authData.user_email" 
            placeholder="example@ssafy.com" 
            required
          />
        </div>

        <button type="submit" class="btn-submit">확인</button>
        <button type="button" @click="$router.push('/')" class="btn-cancel">이전으로</button>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const authData = ref({
  user_name: '',
  user_email: ''
});

const handleAuth = () => {
  // 이름과 이메일 정보를 Query Parameter로 실어서 결과 조회 페이지로 스위칭합니다.
  router.push({
    name: 'UserReportList',
    query: {
      name: authData.value.user_name,
      email: authData.value.user_email
    }
  });
};
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 70vh;
  padding: 20px;
}
.auth-box {
  background: white;
  padding: 40px;
  border-radius: 8px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  width: 100%;
  max-width: 400px;
}
.auth-box h2 {
  margin-bottom: 10px;
  text-align: center;
  color: #333;
}
.auth-desc {
  font-size: 14px;
  color: #666;
  text-align: center;
  margin-bottom: 30px;
}
.input-group {
  display: flex;
  flex-direction: column;
  margin-bottom: 20px;
}
.input-group label {
  font-weight: bold;
  margin-bottom: 8px;
  color: #495057;
}
.input-group input {
  padding: 12px;
  border: 1px solid #ced4da;
  border-radius: 4px;
  font-size: 15px;
}
.btn-submit {
  width: 100%;
  padding: 12px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
  margin-bottom: 10px;
}
.btn-cancel {
  width: 100%;
  padding: 12px;
  background-color: #e9ecef;
  color: #495057;
  border: none;
  border-radius: 4px;
  font-size: 16px;
  font-weight: bold;
  cursor: pointer;
}
</style>