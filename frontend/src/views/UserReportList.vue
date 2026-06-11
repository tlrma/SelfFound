<template>
  <div class="history-container">
    <header class="history-header">
      <h2>내 분실물 신고 이력</h2>
      <p><strong>{{ userName }}</strong> ({{ userEmail }}) 님으로 접수된 신고 내역입니다.</p>
    </header>

    <main class="history-content">
      <div class="table-responsive">
        <table class="history-table">
          <thead>
            <tr>
              <th>접수 번호</th>
              <th>물품 카테고리</th>
              <th>분실 장소</th>
              <th>상세 특징</th>
              <th>처리 상태</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in myReports" :key="report.id">
              <td><strong>#{{ report.id }}</strong></td>
              <td><span class="badge">{{ getCategoryLabel(report.category) }}</span></td>
              <td>{{ report.lost_location }}</td>
              <td class="text-left">{{ report.lost_description }}</td>
              <td>
                <span :class="['status-text', report.status]">
                  {{ getStatusLabel(report.status) }}
                </span>
              </td>
            </tr>
            <tr v-if="myReports.length === 0">
              <td colspan="5" class="empty-row">해당 이름과 이메일로 접수된 이력이 없습니다.</td>
            </tr>
          </tbody>
        </table>
      </div>
      <button @click="$router.push('/')" class="btn-home">메인 화면으로</button>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

const route = useRoute();

const userName = ref(route.query.name || '');
const userEmail = ref(route.query.email || '');
const myReports = ref([]);

// 💡 백엔드 DB에서 실제 데이터를 가져오는 함수
const fetchMyReports = async () => {
  if (!userName.value || !userEmail.value) return;

  try {
    const response = await axios.get('/api/reports/manage/', {
      params: {
        name: userName.value,
        email: userEmail.value
      }
    });

    if (response.status === 200) {
      // 장고 백엔드의 { status: 'ok', data: [...] } 구조에서 데이터 배열 파싱
      if (response.data && response.data.status === 'ok') {
        myReports.value = response.data.data;
      } else {
        myReports.value = response.data;
      }
    }
  } catch (error) {
    console.error('신고 이력 조회 실패:', error);
    alert('이력을 불러오는 중 오류가 발생했습니다.');
  }
};

// 💡 백엔드 모델(STATUS_CHOICES) 기준에 맞춘 상태 라벨 변환
const getStatusLabel = (status) => {
  const labels = { searching: '찾는중', matched: '매칭완료', completed: '수령완료' };
  return labels[status] || status;
};

// 💡 백엔드 모델(CATEGORY_CHOICES) 기준에 맞춘 카테고리 라벨 변환
const getCategoryLabel = (category) => {
  const categories = {
    card: '카드',
    glasses: '안경',
    wallet: '지갑',
    phone: '휴대폰',
    keys: '열쇠',
    sunglasses: '선글라스',
    watch: '시계',
    etc: '기타'
  };
  return categories[category] || category;
};

onMounted(() => {
  fetchMyReports();
});
</script>

<style scoped>
.history-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: sans-serif;
}
.history-header {
  margin-bottom: 30px;
  border-bottom: 2px solid #eaeaea;
  padding-bottom: 15px;
}
.history-header h2 {
  font-size: 26px;
  color: #333;
  margin: 0 0 10px 0;
}
.history-header p {
  color: #666;
  margin: 0;
}
.table-responsive {
  width: 100%;
  overflow-x: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
  border-radius: 8px;
  margin-bottom: 25px;
}
.history-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fff;
  text-align: center;
}
.history-table th, .history-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #eeeeee;
  font-size: 15px;
}
.history-table th {
  background-color: #f8f9fa;
  color: #495057;
  font-weight: 600;
}
.text-left {
  text-align: left;
}
.badge {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  font-weight: bold;
  background-color: #e9ecef;
  color: #495057;
}
.status-text {
  font-weight: bold;
}
.status-text.searching { color: #f0ad4e; }
.status-text.matched { color: #0275d8; }
.status-text.completed { color: #5cb85c; }
.btn-home {
  padding: 12px 24px;
  background-color: #42b983;
  color: white;
  border: none;
  border-radius: 4px;
  font-size: 15px;
  font-weight: bold;
  cursor: pointer;
  transition: background-color 0.2s;
}
.btn-home:hover {
  background-color: #3aa876;
}
.empty-row {
  padding: 40px !important;
  color: #999;
}
</style>