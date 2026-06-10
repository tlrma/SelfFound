<template>
  <div class="report-status-container">
    <div class="success-banner">
      <h3>🎉 분실물 신고 접수 완료</h3>
      <p>신고서가 시스템에 정상적으로 등록되었습니다.</p>
    </div>

    <div class="info-box" v-if="reportData">
      <h4>접수 정보</h4>
      <p><strong>접수 번호 (ID):</strong> {{ reportId }}</p>
      <p><strong>신고 물품:</strong> {{ reportData.item_name }}</p>
      <p><strong>상세 특징:</strong> {{ reportData.features }}</p>
      <p><strong>신고 일시:</strong> {{ formatDate(reportData.reported_at) }}</p>
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
const reportData = ref(null);

const fetchReportStatus = async () => {
  try {
    // 프로젝트 명세서의 GET /api/reports/{id}/ 호출 구현
    const response = await axios.get(`/api/reports/${reportId}/`);
    if (response.status === 200) {
      reportData.value = response.data.data || response.data;
    }
  } catch (error) {
    console.error('신고 정보 조회 실패:', error);
    alert('정보를 불러오는 중 에러가 발생했습니다.');
  }
};

const goHome = () => {
  router.push('/');
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString();
};

onMounted(() => {
  //fetchReportStatus();

  // 확인용 가짜 데이터
  // http://localhost:5173/status/1
  reportData.value = {
    item_name: '지갑',
    features: '검은 가죽 반지갑, 카드 슬롯 여러 개',
    reported_at: new Date().toISOString()
  };
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
</style>