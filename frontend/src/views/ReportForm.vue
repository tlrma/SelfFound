<template>
  <div class="navigation-header">
    <button type="button" @click="$router.push({ name: 'UserAuth' })" class="btn-history">
      📋 내 신고 기록 조회
    </button>
  </div>
  <div class="report-form-container">
    <h2>분실물 신고서 작성</h2>
    <form @submit.prevent="submitReport">
      <div class="form-group">
        <label for="name">이름</label>
        <input type="text" id="name" v-model="formData.name" required placeholder="이름을 입력하세요" />
      </div>

      <div class="form-group">
        <label for="email">이메일</label>
        <input type="email" id="email" v-model="formData.email" required placeholder="example@email.com" />
      </div>

      <div class="form-group">
        <label for="category">물품 카테고리</label>
        <select id="category" v-model="formData.category" required>
          <option value="" disabled>카테고리를 선택해주세요</option>
          <option value="Card">카드</option>
          <option value="Glasses">안경</option>
          <option value="Wallet">지갑</option>
          <option value="Phone">휴대폰</option>
          <option value="Etc">기타</option>
        </select>
      </div>

      <div class="form-group">
        <label for="found_location">분실 장소</label>
        <input type="text" id="found_location" v-model="formData.found_location" required placeholder="예: 서울역 1번 출구" />
      </div>

      <div class="form-group">
        <label for="found_at">분실 시간</label>
        <input type="datetime-local" id="found_at" v-model="formData.found_at" required />
      </div>

      <div class="form-group">
        <label for="features">상세 묘사 및 특징</label>
        <textarea id="features" v-model="formData.features" required rows="4" placeholder="물품의 색상, 브랜드, 특이사항 등을 상세히 적어주세요"></textarea>
      </div>

      <div class="checkbox-group">
        <label>
          <input type="checkbox" v-model="formData.agreeInfo" required />
          (필수) 개인정보 수집 및 처리 동의
        </label>
        <label>
          <input type="checkbox" v-model="formData.agreeVerify" required />
          (필수) 분실자 본인확인 절차 동의
        </label>
      </div>

      <button type="submit" class="submit-btn">신고서 제출</button>
    </form>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();

const formData = ref({
  name: '',
  email: '',
  category: '',
  found_location: '',
  found_at: '',
  features: '',
  agreeInfo: false,
  agreeVerify: false
});

const submitReport = async () => {
  try {
    // 프로젝트 규칙에 맞게 POST /api/reports/ 엔드포인트 호출
    const response = await axios.post('/api/reports/', {
      user_name: formData.value.name,
      user_email: formData.value.email,
      category: formData.value.category,          // 기존 소문자 옵션 값 그대로 전송
      lost_location: formData.value.found_location, // found_location -> lost_location 매핑
      lost_at: formData.value.found_at,             // found_at -> lost_at 매핑
      lost_description: formData.value.features
    });

    if (response.status === 200 || response.status === 201) {
      const reportId = response.data.report.id;
      const topMatch = response.data.top_match;
      const matched = topMatch ? 'true' : 'false';
      const reasoning = topMatch?.reasoning ?? '';
      router.push({ name: 'ReportStatus', params: { id: reportId }, query: { matched, reasoning } });
    }
  } catch (error) {
    console.error('신고 접수 실패:', error);
    alert('신고서 제출 중 오류가 발생했습니다.');
  }
};
</script>

<style scoped>
.navigation-header {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 20px;
}
.btn-history {
  background-color: #4a5568;
  color: white;
  padding: 10px 16px;
  border: none;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-history:hover {
  background-color: #2d3748;
}
.report-form-container {
  max-width: 600px;
  margin: 0 auto;
  padding: 20px;
  border: 1px solid #ccc;
  border-radius: 8px;
}
.form-group {
  margin-bottom: 15px;
  display: flex;
  flex-direction: column;
}
.form-group label {
  margin-bottom: 5px;
  font-weight: bold;
}
.form-group input, .form-group select, .form-group textarea {
  padding: 8px;
  border: 1px solid #ccc;
  border-radius: 4px;
}
.checkbox-group {
  margin: 20px 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.submit-btn {
  width: 100%;
  padding: 10px;
  background-color: #444;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 16px;
}
.submit-btn:hover {
  background-color: #222;
}
</style>