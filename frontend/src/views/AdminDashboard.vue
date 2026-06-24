<template>
  <div class="admin-dashboard-container">
    <header class="dashboard-header">
      <div>
        <p class="eyebrow">SelfFound Control Room</p>
        <h2>분실물 관리자 대시보드</h2>
      </div>
      <div class="live-indicator">
        <span class="live-dot"></span>
        실시간 모니터링
      </div>
    </header>

    <div v-if="alerts.length > 0" class="alert-list" role="alert">
      <div
        v-for="alert in alerts"
        :key="alert.id"
        :class="['alert-item', `alert-${alert.level}`]"
      >
        <span class="alert-icon">{{ alert.level === 'error' ? '⚠' : 'ℹ' }}</span>
        <div class="alert-body">
          <span class="alert-source">{{ alert.source || '시스템' }}</span>
          <span class="alert-message">{{ alert.message }}</span>
          <span class="alert-time">{{ formatDate(alert.created_at) }}</span>
        </div>
        <button type="button" class="alert-dismiss" @click="dismissAlert(alert.id)">✕</button>
      </div>
    </div>

    <main class="dashboard-grid">
      <section class="panel reports-panel">
        <div class="panel-header">
          <div>
            <h3>신고 내역</h3>
            <p>사용자가 등록한 분실 신고 목록</p>
          </div>
          <span class="count-pill">{{ reports.length }}건</span>
        </div>

        <div v-if="isLoading" class="status-message">데이터를 불러오는 중입니다...</div>
        <div v-else-if="errorMessage" class="status-message error">{{ errorMessage }}</div>

        <div v-else class="table-responsive report-scroll">
          <table class="report-table compact">
            <thead>
              <tr>
                <th>번호</th>
                <th>신고자</th>
                <th>카테고리</th>
                <th>분실 장소</th>
                <th>상태</th>
                <th>검토</th>
              </tr>
            </thead>
            <tbody>
              <tr
                v-for="report in reports"
                :key="report.id"
                :class="{ selected: selectedReport && selectedReport.id === report.id }"
              >
                <td><strong>#{{ report.id }}</strong></td>
                <td>
                  <div class="person-cell">
                    <strong>{{ report.user_name }}</strong>
                    <span>{{ report.user_email }}</span>
                  </div>
                </td>
                <td><span class="badge category">{{ getCategoryLabel(report.category) }}</span></td>
                <td class="text-left">{{ report.lost_location }}</td>
                <td>
                  <select
                    v-model="report.status"
                    @change="updateStatus(report.id, report.status)"
                    :class="['status-select', report.status]"
                  >
                    <option value="searching">찾는중</option>
                    <option value="review">검토중</option>
                    <option value="matched">매칭완료</option>
                    <option value="processing">이송중</option>
                    <option value="completed">수령완료</option>
                  </select>
                </td>
                <td>
                  <button
                    type="button"
                    class="review-open-button"
                    :disabled="report.status !== 'review'"
                    @click="openReview(report)"
                  >
                    확인
                  </button>
                </td>
              </tr>
              <tr v-if="reports.length === 0">
                <td colspan="6" class="empty-row">접수된 분실물 신고 내역이 없습니다.</td>
              </tr>
            </tbody>
          </table>
        </div>
      </section>

      <section class="right-column">
        <section class="panel items-panel">
          <div class="panel-header split">
            <div>
              <h3>분실물 접수 내역</h3>
              <p>습득되어 창고에 적재된 물품 목록</p>
            </div>
            <form class="date-filter" @submit.prevent="fetchItems">
              <input v-model="dateFilters.from" type="date" aria-label="검색 시작 날짜" />
              <span>~</span>
              <input v-model="dateFilters.to" type="date" aria-label="검색 종료 날짜" />
              <button type="submit">검색</button>
              <button type="button" class="ghost-button" @click="resetDateFilters">초기화</button>
            </form>
          </div>

          <div v-if="itemsLoading" class="status-message small">분실물 접수 내역을 불러오는 중입니다...</div>
          <div v-else class="item-list">
            <article v-for="item in items" :key="item.id" class="item-row">
              <div class="item-thumb">
                <img v-if="getImageSrc(item.image_b64)" :src="getImageSrc(item.image_b64)" alt="분실물 이미지" />
                <span v-else>이미지 없음</span>
              </div>
              <div class="item-main">
                <div class="item-title-line">
                  <strong>#{{ item.id }} {{ getCategoryLabel(item.category) }}</strong>
                  <span class="warehouse-chip">{{ item.warehouse_location || '미배정' }}</span>
                </div>
                <button
                  type="button"
                  :class="['item-description', { expanded: isItemDescriptionExpanded(item.id) }]"
                  @click="toggleItemDescription(item.id)"
                >
                  {{ item.description || '상세 묘사가 등록되지 않았습니다.' }}
                </button>
                <dl class="item-meta">
                  <div>
                    <dt>습득 날짜</dt>
                    <dd>{{ formatDate(item.found_at || item.created_at) }}</dd>
                  </div>
                  <div>
                    <dt>습득 장소</dt>
                    <dd>{{ item.found_info || '미입력' }}</dd>
                  </div>
                  <div>
                    <dt>경과 시간</dt>
                    <dd>{{ getElapsedTime(item.found_at || item.created_at) }}</dd>
                  </div>
                </dl>
              </div>
            </article>
            <div v-if="items.length === 0" class="empty-row standalone">조건에 맞는 분실물 접수 내역이 없습니다.</div>
          </div>
        </section>

        <section v-if="selectedReport" class="panel review-panel">
          <div class="panel-header">
            <div>
              <h3>매칭 보류 검토</h3>
              <p>#{{ selectedReport.id }} 신고와 후보 분실물을 직접 비교합니다.</p>
            </div>
            <button type="button" class="ghost-button panel-close-button" @click="closeReview">닫기</button>
          </div>

          <div class="review-body">
            <article class="review-report">
              <div>
                <span class="review-label">신고 내용</span>
                <h4>{{ getCategoryLabel(selectedReport.category) }} · {{ selectedReport.lost_location || '장소 미입력' }}</h4>
                <p>{{ selectedReport.lost_description }}</p>
              </div>
              <dl>
                <div>
                  <dt>신고자</dt>
                  <dd>{{ selectedReport.user_name }}</dd>
                </div>
                <div>
                  <dt>분실 시각</dt>
                  <dd>{{ formatDate(selectedReport.lost_at || selectedReport.created_at) }}</dd>
                </div>
              </dl>
            </article>

            <div v-if="reviewLoading" class="status-message small">매칭 후보를 불러오는 중입니다...</div>
            <div v-else-if="reviewError" class="status-message small error">{{ reviewError }}</div>
            <div v-else-if="reviewCandidates.length === 0" class="empty-row standalone">
              검토할 매칭 후보가 없습니다.
            </div>

            <article v-for="candidate in reviewCandidates" :key="candidate.id" class="candidate-card">
              <div class="candidate-image">
                <img v-if="getImageSrc(candidate.item.image_b64)" :src="getImageSrc(candidate.item.image_b64)" alt="후보 분실물 이미지" />
                <span v-else>이미지 없음</span>
              </div>
              <div class="candidate-info">
                <div class="candidate-title">
                  <strong>#{{ candidate.item.id }} {{ getCategoryLabel(candidate.item.category) }}</strong>
                  <span>{{ candidate.score_percent }}%</span>
                </div>
                <p>{{ candidate.item.description || '상세 묘사가 등록되지 않았습니다.' }}</p>
                <dl class="candidate-meta">
                  <div>
                    <dt>습득 장소</dt>
                    <dd>{{ candidate.item.found_info || '미입력' }}</dd>
                  </div>
                  <div>
                    <dt>습득 날짜</dt>
                    <dd>{{ formatDate(candidate.item.found_at || candidate.item.created_at) }}</dd>
                  </div>
                  <div>
                    <dt>창고</dt>
                    <dd>{{ candidate.item.warehouse_location || '미배정' }}</dd>
                  </div>
                </dl>
                <div class="reason-box">
                  {{ candidate.reasoning || '저장된 매칭 판단 사유가 없습니다.' }}
                </div>
                <div class="candidate-actions">
                  <button type="button" class="approve-button" @click="decideCandidate(candidate.id, 'approve')">맞음</button>
                  <button type="button" class="reject-button" @click="decideCandidate(candidate.id, 'reject')">아님</button>
                </div>
              </div>
            </article>
          </div>
        </section>

        <section class="panel map-panel">
          <div class="panel-header">
            <div>
              <h3>분실물 센터 맵</h3>
              <p>Dobot, TurtleBot, 컨베이어, 창고 적재 상태</p>
            </div>
            <span class="updated-at">최근 갱신 {{ lastUpdatedLabel }}</span>
          </div>

          <div class="center-map" aria-label="분실물 센터 실시간 모니터링 맵">
            <div class="entry entry-deposit">습득물 투입</div>
            <div class="entry entry-pickup">수령 대기</div>
            <div class="intake-slot deposit-slot"></div>
            <div class="intake-slot pickup-slot"></div>
            <div class="belt">컨베이어 벨트</div>
            <div class="camera">카메라</div>
            <div class="scanner"></div>

            <div :class="['robot dobot', { active: robotStatus.dobot.active }]">
              <strong>Dobot</strong>
              <span>{{ robotStatus.dobot.task }}</span>
            </div>

            <div :class="['robot turtlebot', { active: robotStatus.turtlebot.active }]">
              <strong>TurtleBot</strong>
              <span>{{ robotStatus.turtlebot.task }}</span>
            </div>

            <div class="warehouse">
              <h4>분실물 창고</h4>
              <div class="warehouse-grid">
                <div
                  v-for="slot in warehouseSlots"
                  :key="slot.id"
                  :class="['slot-cell', { occupied: slot.item }]"
                  :title="slot.item ? `${slot.id}: ${slot.item.description || getCategoryLabel(slot.item.category)}` : `${slot.id}: 비어 있음`"
                >
                  <span>{{ slot.id }}</span>
                  <strong>{{ slot.item ? getCategoryLabel(slot.item.category) : '-' }}</strong>
                </div>
              </div>
            </div>
          </div>
        </section>
      </section>
    </main>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref } from 'vue';
import axios from 'axios';

const reports = ref([]);
const items = ref([]);
const alerts = ref([]);
const isLoading = ref(true);
const itemsLoading = ref(true);
const errorMessage = ref('');
const dateFilters = ref({ from: '', to: '' });
const lastUpdatedAt = ref(null);
const selectedReport = ref(null);
const reviewCandidates = ref([]);
const reviewLoading = ref(false);
const reviewError = ref('');
const expandedItemDescriptions = ref(new Set());
let refreshTimer = null;

const fetchReports = async () => {
  try {
    isLoading.value = true;
    const response = await axios.get('/api/reports/manage/');

    if (response.data && response.data.status === 'ok') {
      reports.value = response.data.data;
    }
  } catch (error) {
    console.error('대시보드 데이터 로드 실패:', error);
    errorMessage.value = '신고 목록을 불러오는 중 오류가 발생했습니다.';
  } finally {
    isLoading.value = false;
  }
};

const fetchItems = async () => {
  try {
    itemsLoading.value = true;
    const params = {};
    if (dateFilters.value.from) params.found_from = dateFilters.value.from;
    if (dateFilters.value.to) params.found_to = dateFilters.value.to;

    const response = await axios.get('/api/items/', { params });
    if (response.data && response.data.status === 'ok') {
      items.value = response.data.data;
      lastUpdatedAt.value = new Date();
    }
  } catch (error) {
    console.error('분실물 접수 내역 로드 실패:', error);
  } finally {
    itemsLoading.value = false;
  }
};

const fetchAlerts = async () => {
  try {
    const response = await axios.get('/api/admin_panel/alerts/');
    if (response.data && response.data.status === 'ok') {
      alerts.value = response.data.data;
    }
  } catch (error) {
    console.error('알림 로드 실패:', error);
  }
};

const dismissAlert = async (id) => {
  try {
    await axios.patch(`/api/admin_panel/alerts/${id}/dismiss/`);
    alerts.value = alerts.value.filter((a) => a.id !== id);
  } catch (error) {
    console.error('알림 닫기 실패:', error);
  }
};

const refreshDashboard = () => {
  fetchReports();
  fetchItems();
  fetchAlerts();
};

const resetDateFilters = () => {
  dateFilters.value = { from: '', to: '' };
  fetchItems();
};

const isItemDescriptionExpanded = (itemId) => {
  return expandedItemDescriptions.value.has(itemId);
};

const toggleItemDescription = (itemId) => {
  const next = new Set(expandedItemDescriptions.value);
  if (next.has(itemId)) {
    next.delete(itemId);
  } else {
    next.add(itemId);
  }
  expandedItemDescriptions.value = next;
};

const openReview = async (report) => {
  selectedReport.value = report;
  reviewCandidates.value = [];
  reviewError.value = '';
  await fetchReviewCandidates(report.id);
};

const closeReview = () => {
  selectedReport.value = null;
  reviewCandidates.value = [];
  reviewError.value = '';
};

const fetchReviewCandidates = async (reportId) => {
  try {
    reviewLoading.value = true;
    const response = await axios.get(`/api/matching/review/${reportId}/`);
    if (response.data && response.data.status === 'ok') {
      selectedReport.value = response.data.report;
      reviewCandidates.value = response.data.data;
    }
  } catch (error) {
    console.error('매칭 후보 조회 실패:', error);
    reviewError.value = '매칭 후보를 불러오는 중 오류가 발생했습니다.';
  } finally {
    reviewLoading.value = false;
  }
};

const decideCandidate = async (candidateId, action) => {
  const message = action === 'approve'
    ? '이 후보를 실제 매칭으로 확정하시겠습니까?'
    : '이 후보를 매칭 후보에서 제외하시겠습니까?';

  if (!window.confirm(message)) return;

  try {
    await axios.post(`/api/matching/review/${candidateId}/decide/`, { action });

    if (action === 'approve') {
      alert('매칭을 확정했습니다.');
      closeReview();
      refreshDashboard();
      return;
    }

    alert('후보를 반려했습니다.');
    if (selectedReport.value) {
      await fetchReviewCandidates(selectedReport.value.id);
    }
    refreshDashboard();
  } catch (error) {
    console.error('매칭 후보 처리 실패:', error);
    alert('매칭 후보 처리 중 오류가 발생했습니다.');
  }
};

const updateStatus = async (reportId, newStatus) => {
  try {
    await axios.patch(`/api/reports/manage/${reportId}/`, {
      status: newStatus
    });
    alert(`#${reportId}번 신고 상태가 성공적으로 변경되었습니다.`);
  } catch (error) {
    console.error('상태 업데이트 실패:', error);
    alert('상태 변경 중 오류가 발생했습니다. 다시 시도해 주세요.');
    fetchReports();
  }
};

const getCategoryLabel = (category) => {
  const categories = {
    card: '카드',
    Card: '카드',
    glasses: '안경',
    Glasses: '안경',
    keys: '열쇠',
    Keys: '열쇠',
    wallet: '지갑',
    Wallet: '지갑',
    phone: '휴대폰',
    Phone: '휴대폰',
    sunglasses: '선글라스',
    Sunglasses: '선글라스',
    watch: '시계',
    Watch: '시계',
    etc: '기타',
    Etc: '기타'
  };
  return categories[category] || category || '기타';
};

const formatDate = (value) => {
  if (!value) return '미입력';
  return new Date(value).toLocaleString('ko-KR', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

const getElapsedTime = (value) => {
  if (!value) return '알 수 없음';
  const diffMinutes = Math.max(0, Math.floor((Date.now() - new Date(value).getTime()) / 60000));
  if (diffMinutes < 60) return `${diffMinutes}분 전`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}시간 전`;
  return `${Math.floor(diffHours / 24)}일 전`;
};

const getImageSrc = (imageB64) => {
  if (!imageB64) return '';
  if (imageB64.startsWith('data:image')) return imageB64;
  return `data:image/jpeg;base64,${imageB64}`;
};

const itemByWarehouse = computed(() => {
  return items.value.reduce((acc, item) => {
    if (item.warehouse_location) acc[item.warehouse_location] = item;
    return acc;
  }, {});
});

const warehouseSlots = computed(() => {
  const rows = ['A', 'B', 'C', 'D', 'E'];
  const cols = ['1', '2', '3', '4', '5'];
  return rows.flatMap((row) =>
    cols.map((col) => {
      const id = `${row}-${col}`;
      return { id, item: itemByWarehouse.value[id] };
    })
  );
});

const robotStatus = computed(() => {
  const latestItem = items.value[0];
  const activeDobot = latestItem && ['stored', 'matched'].includes(latestItem.status);
  const deliveryReport = reports.value.find((report) => ['matched', 'processing'].includes(report.status));

  return {
    dobot: {
      active: Boolean(activeDobot),
      task: activeDobot
        ? `${getCategoryLabel(latestItem.category)}를 ${latestItem.warehouse_location || '창고'}에 적재 중`
        : '대기 중'
    },
    turtlebot: {
      active: Boolean(deliveryReport),
      task: deliveryReport
        ? `#${deliveryReport.id} 신고 물품 이송 준비`
        : '대기 중'
    }
  };
});

const lastUpdatedLabel = computed(() => {
  if (!lastUpdatedAt.value) return '없음';
  return lastUpdatedAt.value.toLocaleTimeString('ko-KR', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  });
});

onMounted(() => {
  refreshDashboard();
  refreshTimer = window.setInterval(refreshDashboard, 10000);
});

onUnmounted(() => {
  if (refreshTimer) window.clearInterval(refreshTimer);
});
</script>

<style scoped>
.admin-dashboard-container {
  max-width: 1480px;
  margin: 0 auto;
  padding: 32px 20px;
  color: #1f2937;
  font-family: Arial, sans-serif;
}

.alert-list {
  display: grid;
  gap: 8px;
  margin-bottom: 16px;
}

.alert-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 6px;
  border: 1px solid;
  font-size: 13px;
}

.alert-error {
  border-color: #fca5a5;
  background: #fef2f2;
  color: #991b1b;
}

.alert-warning {
  border-color: #fcd34d;
  background: #fffbeb;
  color: #92400e;
}

.alert-info {
  border-color: #93c5fd;
  background: #eff6ff;
  color: #1e40af;
}

.alert-icon {
  flex: 0 0 auto;
  font-size: 16px;
  line-height: 1.3;
}

.alert-body {
  flex: 1;
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 0 10px;
}

.alert-source {
  font-weight: 700;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  opacity: 0.7;
}

.alert-message {
  font-weight: 500;
}

.alert-time {
  font-size: 11px;
  opacity: 0.6;
  white-space: nowrap;
}

.alert-dismiss {
  flex: 0 0 auto;
  border: none;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
  opacity: 0.5;
  padding: 0 2px;
  line-height: 1;
}

.alert-dismiss:hover {
  opacity: 1;
}

.dashboard-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 18px;
  margin-bottom: 22px;
  border-bottom: 1px solid #d7dde5;
  padding-bottom: 18px;
}

.eyebrow {
  margin: 0 0 6px;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0;
  text-transform: uppercase;
}

.dashboard-header h2 {
  font-size: 28px;
  color: #111827;
  margin: 0;
}

.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  min-height: 34px;
  padding: 0 12px;
  border: 1px solid #bbf7d0;
  border-radius: 4px;
  background: #f0fdf4;
  color: #166534;
  font-size: 13px;
  font-weight: 700;
}

.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 0 5px rgba(34, 197, 94, 0.14);
}

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(430px, 0.95fr) minmax(560px, 1.25fr);
  gap: 18px;
  align-items: stretch;
}

.right-column {
  display: grid;
  grid-template-rows: auto auto minmax(380px, 1fr);
  gap: 18px;
  min-width: 0;
}

.panel {
  min-width: 0;
  border: 1px solid #d7dde5;
  border-radius: 8px;
  background-color: #fff;
  box-shadow: 0 10px 24px rgba(15, 23, 42, 0.06);
}

.reports-panel,
.items-panel,
.review-panel,
.map-panel {
  display: flex;
  flex-direction: column;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid #edf0f4;
}

.panel-header.split {
  align-items: flex-start;
}

.panel-header h3 {
  margin: 0 0 4px;
  color: #111827;
  font-size: 18px;
}

.panel-header p {
  margin: 0;
  color: #64748b;
  font-size: 13px;
}

.count-pill,
.updated-at {
  flex: 0 0 auto;
  border-radius: 4px;
  background: #eef2f7;
  color: #475569;
  padding: 6px 9px;
  font-size: 12px;
  font-weight: 700;
}

.status-message {
  text-align: center;
  padding: 40px;
  font-size: 16px;
  color: #666;
}

.status-message.small {
  padding: 28px;
  font-size: 14px;
}

.status-message.error {
  color: #d9534f;
}

.table-responsive {
  width: 100%;
  overflow-x: auto;
}

.report-scroll {
  max-height: 720px;
  overflow: auto;
}

.report-table {
  width: 100%;
  border-collapse: collapse;
  background-color: #fff;
  text-align: center;
}

.report-table th,
.report-table td {
  padding: 13px 12px;
  border-bottom: 1px solid #eeeeee;
  font-size: 14px;
  vertical-align: middle;
}

.report-table.compact th,
.report-table.compact td {
  padding: 12px 10px;
}

.report-table th {
  position: sticky;
  top: 0;
  z-index: 1;
  background-color: #f8f9fa;
  color: #495057;
  font-weight: 700;
}

.report-table tr.selected td {
  background: #f0f7ff;
}

.person-cell {
  display: grid;
  gap: 2px;
  text-align: left;
}

.person-cell span {
  max-width: 150px;
  overflow: hidden;
  color: #64748b;
  font-size: 12px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.text-left {
  max-width: 180px;
  overflow: hidden;
  text-align: left;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.badge {
  display: inline-block;
  padding: 4px 8px;
  font-size: 12px;
  border-radius: 4px;
  font-weight: 700;
}

.badge.category {
  background-color: #e9ecef;
  color: #495057;
}

.status-select {
  max-width: 96px;
  padding: 6px 8px;
  border-radius: 4px;
  font-weight: 700;
  border: 1px solid #ced4da;
  cursor: pointer;
}

.status-select.searching,
.status-select.review {
  background-color: #fff7ed;
  color: #9a3412;
  border-color: #fed7aa;
}

.status-select.matched,
.status-select.processing {
  background-color: #eff6ff;
  color: #1d4ed8;
  border-color: #bfdbfe;
}

.status-select.completed {
  background-color: #ecfdf5;
  color: #047857;
  border-color: #a7f3d0;
}

.review-open-button {
  min-height: 32px;
  border: 1px solid #2563eb;
  border-radius: 4px;
  background: #2563eb;
  color: #fff;
  padding: 0 10px;
  font-size: 12px;
  font-weight: 800;
  cursor: pointer;
}

.review-open-button:disabled {
  border-color: #d6dde7;
  background: #f1f5f9;
  color: #94a3b8;
  cursor: not-allowed;
}

.empty-row {
  color: #999;
  padding: 36px !important;
}

.empty-row.standalone {
  text-align: center;
}

.date-filter {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  align-items: center;
  gap: 7px;
}

.date-filter input {
  width: 136px;
  min-height: 34px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  padding: 0 8px;
  color: #334155;
}

.date-filter button {
  min-height: 34px;
  border: 1px solid #2563eb;
  border-radius: 4px;
  background: #2563eb;
  color: #fff;
  padding: 0 10px;
  font-weight: 700;
  cursor: pointer;
}

.date-filter .ghost-button {
  border-color: #cbd5e1;
  background: #fff;
  color: #475569;
}

.panel-close-button {
  min-height: 34px;
  border: 1px solid #cbd5e1;
  border-radius: 4px;
  background: #fff;
  color: #475569;
  padding: 0 10px;
  font-weight: 700;
  cursor: pointer;
}

.item-list {
  display: grid;
  gap: 10px;
  max-height: 360px;
  overflow: auto;
  padding: 14px 18px 18px;
}

.item-row {
  display: grid;
  grid-template-columns: 82px minmax(0, 1fr);
  gap: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px;
  background: #fcfcfd;
}

.item-thumb {
  display: grid;
  place-items: center;
  width: 82px;
  height: 82px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f8fafc;
  color: #94a3b8;
  font-size: 11px;
  text-align: center;
}

.item-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.item-main {
  min-width: 0;
}

.item-title-line {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 5px;
}

.item-title-line strong,
.item-meta dd {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.warehouse-chip {
  flex: 0 0 auto;
  border-radius: 4px;
  background: #e0f2fe;
  color: #0369a1;
  padding: 4px 7px;
  font-size: 12px;
  font-weight: 800;
}

.item-description {
  display: -webkit-box;
  width: 100%;
  overflow: hidden;
  border: 0;
  background: transparent;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
  margin: 0 0 9px;
  padding: 0;
  color: #334155;
  cursor: pointer;
  font-size: 13px;
  line-height: 1.45;
  text-align: left;
  font-family: inherit;
}

.item-description.expanded {
  display: block;
  overflow: visible;
  -webkit-line-clamp: unset;
}

.item-meta {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
  margin: 0;
}

.item-meta div {
  min-width: 0;
}

.item-meta dt {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 700;
}

.item-meta dd {
  margin: 2px 0 0;
  color: #475569;
  font-size: 12px;
}

.review-body {
  display: grid;
  gap: 12px;
  max-height: 420px;
  overflow: auto;
  padding: 14px 18px 18px;
}

.review-report,
.candidate-card {
  border: 1px solid #dbe4ef;
  border-radius: 8px;
  background: #fcfdff;
}

.review-report {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 220px;
  gap: 14px;
  padding: 14px;
}

.review-label {
  display: inline-block;
  margin-bottom: 6px;
  border-radius: 4px;
  background: #eef2f7;
  color: #475569;
  padding: 4px 7px;
  font-size: 11px;
  font-weight: 800;
}

.review-report h4 {
  margin: 0 0 7px;
  color: #111827;
  font-size: 15px;
}

.review-report p {
  margin: 0;
  color: #334155;
  font-size: 13px;
  line-height: 1.45;
}

.review-report dl,
.candidate-meta {
  display: grid;
  gap: 7px;
  margin: 0;
}

.review-report dt,
.candidate-meta dt {
  color: #94a3b8;
  font-size: 11px;
  font-weight: 800;
}

.review-report dd,
.candidate-meta dd {
  margin: 2px 0 0;
  color: #475569;
  font-size: 12px;
}

.candidate-card {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr);
  gap: 12px;
  padding: 12px;
}

.candidate-image {
  display: grid;
  place-items: center;
  width: 96px;
  height: 96px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f8fafc;
  color: #94a3b8;
  font-size: 11px;
  text-align: center;
}

.candidate-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.candidate-info {
  min-width: 0;
}

.candidate-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.candidate-title strong {
  min-width: 0;
  overflow: hidden;
  color: #111827;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-title span {
  flex: 0 0 auto;
  border-radius: 4px;
  background: #dbeafe;
  color: #1d4ed8;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 900;
}

.candidate-info > p {
  margin: 0 0 9px;
  overflow: hidden;
  color: #334155;
  font-size: 13px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.candidate-meta {
  grid-template-columns: repeat(3, minmax(0, 1fr));
  margin-bottom: 10px;
}

.candidate-meta dd {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reason-box {
  border-left: 3px solid #93c5fd;
  background: #eff6ff;
  color: #334155;
  padding: 9px 10px;
  font-size: 12px;
  line-height: 1.45;
}

.candidate-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 10px;
}

.approve-button,
.reject-button {
  min-height: 34px;
  border-radius: 4px;
  padding: 0 14px;
  font-weight: 800;
  cursor: pointer;
}

.approve-button {
  border: 1px solid #16a34a;
  background: #16a34a;
  color: #fff;
}

.reject-button {
  border: 1px solid #dc2626;
  background: #fff;
  color: #dc2626;
}

.center-map {
  position: relative;
  min-height: 430px;
  margin: 18px;
  overflow: hidden;
  border: 3px solid #253041;
  border-radius: 22px;
  background:
    linear-gradient(90deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    linear-gradient(0deg, rgba(148, 163, 184, 0.12) 1px, transparent 1px),
    #fbfdff;
  background-size: 32px 32px;
}

.entry {
  position: absolute;
  left: 24px;
  width: 128px;
  z-index: 2;
  color: #475569;
  font-size: 13px;
  font-weight: 700;
}

.entry-deposit {
  top: 122px;
}

.entry-pickup {
  bottom: 108px;
}

.intake-slot {
  position: absolute;
  left: 210px;
  width: 34px;
  height: 76px;
  z-index: 2;
  border: 2px solid #334155;
  border-radius: 10px;
  background: #fff;
}

.deposit-slot {
  top: 94px;
}

.pickup-slot {
  bottom: 82px;
}

.belt {
  position: absolute;
  top: 121px;
  left: 290px;
  right: calc(7% + clamp(220px, 28%, 300px) + 150px);
  display: grid;
  place-items: center;
  min-width: 240px;
  height: 42px;
  z-index: 2;
  border: 2px solid #334155;
  border-radius: 8px;
  background: repeating-linear-gradient(90deg, #eef2f7 0 18px, #dbe4ef 18px 36px);
  color: #334155;
  font-weight: 800;
}

.camera {
  position: absolute;
  top: 54px;
  right: calc(7% + clamp(220px, 28%, 300px) + 62px);
  display: grid;
  place-items: center;
  width: 90px;
  height: 36px;
  z-index: 3;
  border: 2px solid #334155;
  border-radius: 8px;
  background: #fff;
  font-weight: 800;
}

.scanner {
  position: absolute;
  top: 112px;
  right: calc(7% + clamp(220px, 28%, 300px) + 78px);
  width: 48px;
  height: 52px;
  z-index: 2;
  border: 2px solid #334155;
  border-radius: 10px;
  background: #f8fafc;
}

.robot {
  position: absolute;
  display: grid;
  place-items: center;
  gap: 3px;
  z-index: 4;
  border: 3px solid #263244;
  background: #fff;
  color: #111827;
  text-align: center;
  box-shadow: 0 8px 18px rgba(15, 23, 42, 0.08);
}

.robot strong {
  font-size: 16px;
}

.robot span {
  max-width: 112px;
  color: #64748b;
  font-size: 11px;
  line-height: 1.25;
}

.robot.active {
  border-color: #2563eb;
  box-shadow: 0 0 0 7px rgba(37, 99, 235, 0.13);
}

.dobot {
  top: 111px;
  right: calc(7% + clamp(220px, 28%, 300px) + 28px);
  width: 116px;
  height: 86px;
  border-radius: 50%;
}

.turtlebot {
  bottom: 86px;
  left: 34%;
  width: 160px;
  height: 84px;
  border-radius: 16px;
}

.warehouse {
  position: absolute;
  top: 96px;
  right: 7%;
  width: clamp(220px, 28%, 300px);
  min-height: 218px;
  z-index: 3;
  border: 3px solid #263244;
  border-radius: 18px;
  background: #fff;
  padding: 14px;
}

.warehouse h4 {
  margin: 0 0 10px;
  text-align: center;
  font-size: 15px;
}

.warehouse-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 5px;
}

.slot-cell {
  display: grid;
  place-items: center;
  min-width: 0;
  height: 28px;
  border: 1px solid #d6dde7;
  border-radius: 4px;
  background: #f8fafc;
  color: #94a3b8;
}

.slot-cell span {
  font-size: 9px;
  line-height: 1;
}

.slot-cell strong {
  max-width: 100%;
  overflow: hidden;
  color: inherit;
  font-size: 9px;
  line-height: 1;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.slot-cell.occupied {
  border-color: #7dd3fc;
  background: #e0f2fe;
  color: #0369a1;
}

@media (max-width: 1180px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }

  .right-column {
    grid-template-rows: auto auto;
  }
}

@media (max-width: 760px) {
  .admin-dashboard-container {
    padding: 22px 12px;
  }

  .dashboard-header,
  .panel-header,
  .panel-header.split {
    align-items: flex-start;
    flex-direction: column;
  }

  .date-filter {
    justify-content: flex-start;
  }

  .item-row,
  .item-meta {
    grid-template-columns: 1fr;
  }

  .item-thumb {
    width: 100%;
  }

  .center-map {
    min-width: 720px;
  }

  .map-panel {
    overflow-x: auto;
  }
}
</style>
