<template>
  <div class="logs-view">
    <div class="view-header">
      <h2>{{ $t('logs.title') }}</h2>
      <div class="header-actions">
        <el-button :icon="Refresh" @click="fetchLogs">
          {{ $t('common.refresh') }}
        </el-button>
        <el-button :icon="Delete" type="danger" @click="clearLogs" :disabled="selectedLogs.length === 0">
          {{ $t('logs.clearSelected') }}
        </el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-form :inline="true" :model="filter">
        <el-form-item :label="$t('logs.task')">
          <el-select
            v-model="filter.task_id"
            :placeholder="$t('logs.selectTask')"
            clearable
            filterable
            style="width: 200px;"
          >
            <el-option
              v-for="task in tasks"
              :key="task.id"
              :label="task.name"
              :value="task.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('logs.status')">
          <el-select
            v-model="filter.status"
            :placeholder="$t('logs.selectStatus')"
            clearable
            style="width: 150px;"
          >
            <el-option :label="$t('logs.statusPending')" :value="1" />
            <el-option :label="$t('logs.statusRunning')" :value="2" />
            <el-option :label="$t('logs.statusCompleted')" :value="3" />
            <el-option :label="$t('logs.statusFailed')" :value="4" />
            <el-option :label="$t('logs.statusTimeout')" :value="5" />
            <el-option :label="$t('logs.statusCancelled')" :value="6" />
          </el-select>
        </el-form-item>

        <el-form-item :label="$t('common.search')">
          <el-input
            v-model="filter.search"
            :placeholder="$t('logs.searchPlaceholder')"
            clearable
            style="width: 300px;"
          />
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="fetchLogs">
            {{ $t('common.filter') }}
          </el-button>
        </el-form-item>
      </el-form>
    </div>

    <el-table
      :data="logs"
      v-loading="loading"
      @selection-change="handleSelectionChange"
      style="width: 100%"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column :label="$t('logs.taskName')" min-width="150">
        <template #default="{ row }">
          <router-link
            v-if="row.task"
            :to="{ name: 'task-edit', params: { id: row.task.id } }"
            class="task-link"
          >
            {{ row.task.name }}
          </router-link>
          <span v-else>{{ row.task_id }}</span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('logs.command')" min-width="200">
        <template #default="{ row }">
          <code class="command">{{ row.command_executed }}</code>
        </template>
      </el-table-column>
      <el-table-column :label="$t('logs.status')" width="120">
        <template #default="{ row }">
          <el-tag :type="getStatusTagType(row.status)">
            {{ getStatusText(row.status) }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('logs.started')" width="180">
        <template #default="{ row }">
          {{ formatDate(row.started_at) }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('logs.duration')" width="100">
        <template #default="{ row }">
          {{ row.duration ? row.duration.toFixed(2) + 's' : '-' }}
        </template>
      </el-table-column>
      <el-table-column :label="$t('logs.exitCode')" width="100">
        <template #default="{ row }">
          <span :class="{ 'error-code': row.exit_code !== 0 }">
            {{ row.exit_code ?? '-' }}
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.actions')" width="120" fixed="right">
        <template #default="{ row }">
          <el-button
            size="small"
            :icon="View"
            @click="viewLogDetails(row)"
            :title="$t('logs.viewDetails')"
          ></el-button>
          <el-button
            size="small"
            :icon="Delete"
            type="danger"
            @click="deleteLog(row.id)"
            :title="$t('common.delete')"
          ></el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalLogs"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchLogs"
        @current-change="fetchLogs"
      />
    </div>

    <!-- Log Details Dialog -->
    <el-dialog
      v-model="showDetails"
      :title="$t('logs.details')"
      width="80%"
      top="5vh"
    >
      <div v-if="selectedLog" class="log-details">
        <div class="detail-section">
          <h3>{{ $t('logs.basicInfo') }}</h3>
          <el-descriptions :column="2" border>
            <el-descriptions-item :label="$t('logs.task')">
              {{ selectedLog.task?.name || selectedLog.task_id }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('logs.status')">
              <el-tag :type="getStatusTagType(selectedLog.status)">
                {{ getStatusText(selectedLog.status) }}
              </el-tag>
            </el-descriptions-item>
            <el-descriptions-item :label="$t('logs.started')">
              {{ formatDate(selectedLog.started_at) }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('logs.finished')">
              {{ selectedLog.finished_at ? formatDate(selectedLog.finished_at) : '-' }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('logs.duration')">
              {{ selectedLog.duration ? selectedLog.duration.toFixed(2) + 's' : '-' }}
            </el-descriptions-item>
            <el-descriptions-item :label="$t('logs.exitCode')">
              <span :class="{ 'error-code': selectedLog.exit_code !== 0 }">
                {{ selectedLog.exit_code ?? '-' }}
              </span>
            </el-descriptions-item>
          </el-descriptions>
        </div>

        <div class="detail-section">
          <h3>{{ $t('logs.command') }}</h3>
          <pre class="command-block">{{ selectedLog.command_executed }}</pre>
        </div>

        <div v-if="selectedLog.error_message" class="detail-section">
          <h3>{{ $t('logs.error') }}</h3>
          <pre class="error-block">{{ selectedLog.error_message }}</pre>
        </div>

        <div v-if="selectedLog.stdout" class="detail-section">
          <h3>{{ $t('logs.stdout') }}</h3>
          <pre class="output-block">{{ selectedLog.stdout }}</pre>
        </div>

        <div v-if="selectedLog.stderr" class="detail-section">
          <h3>{{ $t('logs.stderr') }}</h3>
          <pre class="error-block">{{ selectedLog.stderr }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="showDetails = false">
          {{ $t('common.close') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Refresh, Delete, View } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/taskStore'
import { useLogStore } from '@/stores/logStore'
import type { Task, TaskLog } from '@/types/task'

const taskStore = useTaskStore()
const logStore = useLogStore()

const loading = ref(false)
const showDetails = ref(false)
const logs = ref<TaskLog[]>([])
const tasks = ref<Task[]>([])
const selectedLogs = ref<TaskLog[]>([])
const selectedLog = ref<TaskLog | null>(null)

const filter = ref({
  task_id: undefined as number | undefined,
  status: undefined as number | undefined,
  search: ''
})

const currentPage = ref(1)
const pageSize = ref(20)
const totalLogs = ref(0)

const fetchTasks = async () => {
  try {
    const response = await taskStore.getTasks({ limit: 1000 })
    tasks.value = response.data
  } catch (error) {
    console.error('Failed to fetch tasks:', error)
  }
}

const fetchLogs = async () => {
  loading.value = true
  try {
    const response = await logStore.getLogs({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      task_id: filter.value.task_id,
      status: filter.value.status,
      search: filter.value.search || undefined
    })
    logs.value = response.data
    totalLogs.value = response.total
  } catch (error) {
    ElMessage.error('Failed to fetch logs')
  } finally {
    loading.value = false
  }
}

const getStatusTagType = (status: number) => {
  switch (status) {
    case 1: return 'info'    // PENDING
    case 2: return ''        // RUNNING
    case 3: return 'success' // COMPLETED
    case 4: return 'danger'  // FAILED
    case 5: return 'warning' // TIMEOUT
    case 6: return 'info'    // CANCELLED
    default: return 'info'
  }
}

const getStatusText = (status: number) => {
  switch (status) {
    case 1: return 'PENDING'
    case 2: return 'RUNNING'
    case 3: return 'COMPLETED'
    case 4: return 'FAILED'
    case 5: return 'TIMEOUT'
    case 6: return 'CANCELLED'
    default: return 'UNKNOWN'
  }
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  const seconds = String(date.getSeconds()).padStart(2, '0')
  return `${year}-${month}-${day} ${hours}:${minutes}:${seconds}`
}

const handleSelectionChange = (selection: TaskLog[]) => {
  selectedLogs.value = selection
}

const viewLogDetails = (log: TaskLog) => {
  selectedLog.value = log
  showDetails.value = true
}

const deleteLog = async (id: number) => {
  try {
    await ElMessageBox.confirm(
      $t('logs.confirmDeleteLog'),
      $t('common.confirm'),
      {
        confirmButtonText: $t('common.delete'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning'
      }
    )
    await logStore.deleteLog(id)
    ElMessage.success($t('logs.logDeleted'))
    fetchLogs()
  } catch (error) {
    // User cancelled
  }
}

const clearLogs = async () => {
  try {
    await ElMessageBox.confirm(
      $t('logs.confirmDeleteLogs', { count: selectedLogs.value.length }),
      $t('common.confirm'),
      {
        confirmButtonText: $t('common.delete'),
        cancelButtonText: $t('common.cancel'),
        type: 'warning'
      }
    )

    // Delete each selected log individually
    for (const log of selectedLogs.value) {
      try {
        await logStore.deleteLog(log.id)
      } catch (error) {
        console.error(`Failed to delete log ${log.id}:`, error)
        // Continue with other logs even if one fails
      }
    }

    ElMessage.success($t('logs.logsDeleted', { count: selectedLogs.value.length }))
    selectedLogs.value = []
    fetchLogs()
  } catch (error) {
    // User cancelled
  }
}

onMounted(() => {
  fetchTasks()
  fetchLogs()
})
</script>

<style lang="scss" scoped>
.logs-view {
  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
  }

  .filter-bar {
    background: var(--el-bg-color);
    padding: 20px;
    border-radius: 8px;
    margin-bottom: 20px;
  }

  .task-link {
    color: var(--el-color-primary);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  .command {
    font-family: monospace;
    font-size: 0.9em;
    word-break: break-all;
  }

  .error-code {
    color: var(--el-color-error);
    font-weight: bold;
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }

  .log-details {
    max-height: 70vh;
    overflow-y: auto;

    .detail-section {
      margin-bottom: 20px;

      h3 {
        margin-bottom: 10px;
        color: var(--el-text-color-primary);
      }
    }

    .command-block,
    .output-block,
    .error-block {
      background: var(--el-fill-color-light);
      padding: 10px;
      border-radius: 4px;
      font-family: monospace;
      white-space: pre-wrap;
      word-break: break-all;
      margin: 0;
    }

    .error-block {
      color: var(--el-color-error);
      background: var(--el-color-error-light-9);
    }
  }
}
</style>