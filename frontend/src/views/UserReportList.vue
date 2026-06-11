<template>
  <div class="history-container">
    <header class="history-header">
      <h2>내 분실물 신고 이력</h2>
      <!-- 💡 주소창 쿼리스트링(?name=...&email=...)에서 가져온 사용자 정보를 상단에 명시합니다 -->
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
            <!-- 💡 전체 데이터 중 로그인한 사용자의 것만 필터링된 myReports 배열을 반복 출력합니다 -->
            <tr v-for="report in myReports" :key="report.id">
              <td><strong>#{{ report.id }}</strong></td>
              <td><span class="badge">{{ report.category }}</span></td>
              <td>{{ report.lost_location }}</td>
              <td class="text-left">{{ report.lost_description }}</td>
              <td>
                <span :class="['status-text', report.status]">
                  {{ getStatusLabel(report.status) }}
                </span>
              </td>
            </tr>
            <!-- 💡 일치하는 데이터가 단 한 건도 없을 때 나타나는 행입니다 -->
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

const route = useRoute();

// 💡 서진 님이 구현하신 query 스펙(?name=값&email=값)을 그대로 정확하게 긁어옵니다.
const userName = ref(route.query.name || '');
const userEmail = ref(route.query.email || '');
const myReports = ref([]);

// 💡 시스템 전체 데이터베이스 역할을 하는 임시 Mock 데이터셋 (이순신의 데이터가 섞여 있는 상태)
const allMockData = [
  { id: 101, user_name: '홍길동', user_email: 'gildong@ssafy.com', category: 'wallet', lost_location: 'A동 3층 멀티캠퍼스 복도', lost_description: '갈색 가죽 가죽지갑', status: 'received' },
  { id: 102, user_name: '홍길동', user_email: 'gildong@ssafy.com', category: 'card', lost_location: '식당 입구 키오스크 주변', lost_description: '신한 체크카드', status: 'matching' },
  { id: 103, user_name: '이순신', user_email: 'sunshin@ssafy.com', category: 'phone', lost_location: 'B동 지하 1층 엘리베이터 앞', lost_description: '검은색 에어팟 프로 2세대', status: 'completed' }
];

const fetchMyReports = () => {
  // 💡 주소창 쿼리 파라미터의 '이름'과 '이메일'이 모두 완벽히 일치하는 데이터만 정밀 필터링합니다.
  myReports.value = allMockData.filter(
    report => report.user_name === userName.value && report.user_email === userEmail.value
  );
};

const getStatusLabel = (status) => {
  const labels = { received: '접수 완료', matching: '매칭 중', completed: '처리 완료' };
  return labels[status] || status;
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
.status-text.received { color: #f0ad4e; }
.status-text.matching { color: #0275d8; }
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