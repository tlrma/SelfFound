<template>
  <div class="admin-dashboard-container">
    <header class="dashboard-header">
      <h2>분실물 관리자 대시보드</h2>
      <p>접수된 분실물 신고 내역을 관리하고 처리 상태를 업데이트합니다.</p>
    </header>

    <main class="dashboard-content">
      <div v-if="isLoading" class="status-message">데이터를 불러오는 중입니다...</div>
      <div v-else-if="errorMessage" class="status-message error">{{ errorMessage }}</div>
      
      <div v-else class="table-responsive">
        <table class="report-table">
          <thead>
            <tr>
              <th>접수 번호</th>
              <th>신고자 이름</th>
              <th>이메일</th>
              <th>물품 카테고리</th>
              <th>분실 장소</th>
              <th>상세 특징</th>
              <th>상태</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="report in reports" :key="report.id">
              <td><strong>#{{ report.id }}</strong></td>
              <td>{{ report.user_name }}</td>
              <td>{{ report.user_email }}</td>
              <td><span class="badge category">{{ report.category }}</span></td>
              <td>{{ report.lost_location }}</td>
              <td class="text-left">{{ report.lost_description }}</td>
              <td>
                <select 
                  v-model="report.status" 
                  @change="updateStatus(report.id, report.status)"
                  :class="['status-select', report.status]"
                >
                  <option value="received">접수 완료</option>
                  <option value="matching">매칭 중</option>
                  <option value="completed">처리 완료</option>
                </select>
              </td>
            </tr>
            <tr v-if="reports.length === 0">
              <td colspan="7" class="empty-row">접수된 분실물 신고 내역이 없습니다.</td>
            </tr>
          </tbody>
        </table>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// 상태 관리를 위한 반응형 변수
const reports = ref([]);
const isLoading = ref(true);
const errorMessage = ref('');

// 1. 전체 분실물 신고 목록 가져오기 (API 연동)
const fetchReports = async () => {
  try {
    isLoading.value = true;
    const response = await axios.get('/api/reports/');
    
    // 백엔드 응답 규격이 { status: 'ok', data: [...] } 일 경우 분기 처리
    if (response.data && response.data.status === 'ok') {
      reports.value = response.data.data;
    } else {
      reports.value = response.data; // 일반 배열 형태일 경우
    }
  } catch (error) {
    console.error('대시보드 데이터 로드 실패:', error);
    errorMessage.value = '신고 목록을 불러오는 중 오류가 발생했습니다.';
  } finally {
    isLoading.value = false;
  }
};

// 2. 관리자가 직접 신고 상태 업데이트하기
const updateStatus = async (reportId, newStatus) => {
  try {
    const response = await axios.patch(`/api/reports/${reportId}/`, {
      status: newStatus
    });
    
    if (response.status === 200) {
      alert(`#${reportId}번 신고 상태가 성공적으로 변경되었습니다.`);
    }
  } catch (error) {
    console.error('상태 업데이트 실패:', error);
    alert('상태 변경 중 오류가 발생했습니다. 다시 시도해 주세요.');
    // 실패 시 화면을 원래 상태로 되돌리기 위해 새로고침
    fetchReports();
  }
};

onMounted(() => {
  fetchReports();
});
</script>

<style scoped>
.admin-dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  font-family: sans-serif;
}

.dashboard-header {
  margin-bottom: 30px;
  border-bottom: 2px solid #eaeaea;
  padding-bottom: 15px;
}

.dashboard-header h2 {
  font-size: 28px;
  color: #333;
  margin: 0 0 10px 0;
}

.dashboard-header p {
  color: #666;
  margin: 0;
}

.status-message {
  text-align: center;
  padding: 40px;
  font-size: 18px;
  color: #666;
}

.status-message.error {
  color: #d9534f;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
  border-radius: 8px;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fff;
  text-align: center;
}

.report-table th, .report-table td {
  padding: 14px 16px;
  border-bottom: 1px solid #eeeeee;
  font-size: 15px;
}

.report-table th {
  background-color: #f8f9fa;
  color: #495057;
  font-weight: 600;
}

.text-left {
  text-align: left;
  max-width: 300px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  font-weight: bold;
}

.badge.category {
  background-color: #e9ecef;
  color: #495057;
}

/* 상태별 셀렉트 박스 스타일 */
.status-select {
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: bold;
  border: 1px solid #ced4da;
  cursor: pointer;
}

.status-select.received {
  background-color: #fff3cd;
  color: #856404;
  border-color: #ffeeba;
}

.status-select.matching {
  background-color: #cce5ff;
  color: #004085;
  border-color: #b8daff;
}

.status-select.completed {
  background-color: #d4edda;
  color: #155724;
  border-color: #c3e6cb;
}

.empty-row {
  color: #999;
  padding: 40px !important;
}
</style>