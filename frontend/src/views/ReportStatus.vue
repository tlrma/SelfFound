<template>
  <div class="report-status-container">
    <div class="success-banner">
      <h3>🎉 분실물 신고 접수 완료</h3>
      <p>신고서가 시스템에 정상적으로 등록되었습니다.</p>
    </div>

    <div v-if="matched === 'true'" class="match-banner match-success">
      <h3>✅ 매칭 성공</h3>
      <p>보관 중인 분실물 중 일치하는 물건이 발견되었습니다. 담당자가 확인 후 연락드릴 예정입니다.</p>
      <p v-if="reasoning" class="reasoning">💬 {{ reasoning }}</p>
    </div>
    <div v-else class="match-banner match-fail">
      <h3>❌ 매칭 실패</h3>
      <p>현재 보관 중인 분실물 중 일치하는 물건이 없습니다. 새로운 물건이 접수되면 자동으로 재매칭됩니다.</p>
    </div>

    <div class="info-box" v-if="reportData">
  <h4>접수 정보</h4>
  <p><strong>접수 번호 (ID):</strong> {{ reportId }}</p>
  <p><strong>신고 물품:</strong> {{ getCategoryLabel(reportData.category) }}</p>
  <p><strong>분실 장소:</strong> {{ reportData.lost_location }}</p>
  
  <p><strong>분실 시간:</strong> {{ formatDate(reportData.lost_at) }}</p>
  
  <p><strong>상세 특징:</strong> {{ reportData.lost_description }}</p>
  
  <p><strong>접수 일시:</strong> {{ formatDate(reportData.created_at) }}</p>
</div>
    
    <div v-else class="loading">
      신고 정보를 불러오는 중입니다...
    </div>

    <button @click="goHome" class="home-btn">홈으로 돌아가기</button>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const route = useRoute();
const router = useRouter();
const reportId = route.params.id;
const matched = route.query.matched;
const reasoning = route.query.reasoning;
const reportData = ref(null);

const fetchReportStatus = async () => {
  try {
    const response = await axios.get(`/api/reports/${reportId}/`);
    if (response.status === 200) {
      // 💡 백엔드가 보낸 { status: 'ok', data: { id: 6, ... } } 구조에서 data만 정확히 바인딩합니다.
      if (response.data && response.data.status === 'ok') {
        reportData.value = response.data.data;
      } else {
        reportData.value = response.data; // 예외 케이스 방어 코드
      }
    }
  } catch (error) {
    console.error('신고 정보 조회 실패:', error);
    alert('정보를 불러오는 중 에러가 발생했습니다.');
  }
};

const goHome = () => {
  router.push('/');
};

const getCategoryLabel = (category) => {
  const categories = {
    card: '카드',
    glasses: '안경',
    wallet: '지갑',
    phone: '휴대폰',
    etc: '기타'
  };
  return categories[category] || category;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString();
};

onMounted(() => {
  fetchReportStatus();
});
</script>

<style scoped>
.report-status-container {
  max-width: 600px;
  margin: 40px auto;
  padding: 20px;
  text-align: center;
  border: 1px solid #ddd;
  border-radius: 8px;
}
.success-banner {
  background-color: #f0fdf4;
  color: #166534;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}
.info-box {
  text-align: left;
  background-color: #f8fafc;
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
  border: 1px solid #e2e8f0;
}
.info-box p {
  margin: 8px 0;
}
.home-btn {
  padding: 10px 20px;
  background-color: #eee;
  border: 1px solid #ccc;
  border-radius: 4px;
  cursor: pointer;
}
.home-btn:hover {
  background-color: #ddd;
}
.loading {
  margin: 20px 0;
  color: #666;
}
.match-banner {
  padding: 15px;
  border-radius: 6px;
  margin-bottom: 20px;
}
.match-success {
  background-color: #f0fdf4;
  color: #166534;
  border: 1px solid #bbf7d0;
}
.match-fail {
  background-color: #fefce8;
  color: #854d0e;
  border: 1px solid #fde68a;
}
.reasoning {
  margin-top: 8px;
  font-size: 0.9em;
  opacity: 0.85;
  font-style: italic;
}
</style>