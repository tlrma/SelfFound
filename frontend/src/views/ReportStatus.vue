<template>
  <div class="report-status-container">
    <div class="success-banner">
      <h3>🎉 분실물 신고 접수 완료</h3>
      <p>신고서가 시스템에 정상적으로 등록되었습니다.</p>
    </div>

    <div v-if="isMatching" class="match-banner loading-banner">
      <h3>🔍 매칭 분석 중...</h3>
      <p>유사한 분실물을 찾는 중입니다. 잠시만 기다려주세요.</p>
      <div class="spinner"></div>
    </div>

    <template v-else>
      <div v-if="matched === 'true'" class="match-banner match-success">
        <h3>✅ 매칭 성공</h3>
        <p>보관 중인 분실물 중 유사한 물건이 발견되었습니다.<br>담당자가 확인 후 연락드릴 예정입니다. 이메일을 확인해주세요!</p>
        <p v-if="reasoning" class="reasoning">💬 {{ reasoning }}</p>
      </div>
      <div v-else class="match-banner match-fail">
        <h3>❌ 매칭 실패</h3>
        <p>현재 보관 중인 분실물 중 일치하는 물건이 없습니다. 새로운 물건이 접수되면 자동으로 재매칭됩니다.</p>
        <p v-if="reasoning" class="reasoning error-text">{{ reasoning }}</p>
      </div>
    </template>

    <div class="info-box" v-if="reportData">
      <h2 style="text-align: center;">접수 정보</h2>
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

const reportData = ref(null);

// 매칭 관련 상태 변수 (URL 쿼리 대신 내부 상태로 관리)
const isMatching = ref(true); // 초기값을 true로 설정하여 화면 로딩 시 스피너 표시
const matched = ref('false');
const reasoning = ref('');

// 1. 신고 상세 정보 조회 (기존 로직 유지)
const fetchReportStatus = async () => {
  try {
    const response = await axios.get(`/api/reports/${reportId}/`);
    if (response.status === 200) {
      if (response.data && response.data.status === 'ok') {
        reportData.value = response.data.data;
      } else {
        reportData.value = response.data;
      }
    }
  } catch (error) {
    console.error('신고 정보 조회 실패:', error);
  }
};

// 2. ✅ 새로운 매칭 알고리즘 비동기 실행 API 호출
const runMatchingAlgorithm = async () => {
  try {
    const response = await axios.post(`/api/reports/${reportId}/match/`);
    
    if (response.status === 200) {
      const topMatch = response.data.top_match;
      
      if (topMatch) {
        matched.value = 'true';
        //reasoning.value = topMatch.reasoning || '유사한 항목이 발견되었습니다.';
      } else {
        matched.value = 'false';
      }
    }
  } catch (error) {
    console.error('매칭 알고리즘 오류:', error);
    matched.value = 'false';
    reasoning.value = '매칭 시스템 실행 중 오류가 발생했습니다.';
  } finally {
    isMatching.value = false; // 통신 완료(성공/실패 무관) 시 로딩 종료
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
  return categories[category.toLowerCase()] || category; // 안전한 맵핑을 위해 toLowerCase() 추가
};

const formatDate = (dateStr) => {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleString();
};

onMounted(() => {
  fetchReportStatus();      // 기존 정보 가져오기
  runMatchingAlgorithm();   // 화면 진입과 동시에 백그라운드에서 매칭 API 호출
});
</script>

<style scoped>
/* 기존 스타일 유지 및 로딩 스피너 디자인 추가 */
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
  display: flex;
  flex-direction: column;
  align-items: center;
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
.loading-banner {
  background-color: #f8fafc;
  color: #334155;
  border: 1px solid #cbd5e1;
}
.reasoning {
  margin-top: 8px;
  font-size: 0.9em;
  opacity: 0.85;
  font-style: italic;
}
.error-text {
  color: #d9534f;
}

/* 스피너 애니메이션 CSS */
.spinner {
  margin-top: 15px;
  width: 36px;
  height: 36px;
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-left-color: #0275d8;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>