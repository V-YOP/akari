<template>
  <div class="task-list-view">
    <div class="view-header">
      <h2>{{ $t('tasks.title') }}</h2>
      <div class="header-actions">
        <el-button type="primary" :icon="Plus" @click="goToNewTask">
          {{ $t('tasks.newTask') }}
        </el-button>
        <el-input
          v-model="searchQuery"
          :placeholder="$t('common.search')"
          style="width: 300px; margin-left: 10px;"
          clearable
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <el-table
      :data="filteredTasks"
      v-loading="loading"
      style="width: 100%"
      :row-class-name="tableRowClassName"
    >
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column :label="$t('tasks.name')" prop="name" min-width="180">
        <template #default="{ row }">
          <router-link :to="{ name: 'task-edit', params: { id: row.id } }" class="task-link">
            {{ row.name }}
          </router-link>
          <el-tag v-if="!row.enabled" size="small" type="info" style="margin-left: 5px;">
            {{ $t('tasks.disabled') }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tasks.description')" prop="description" min-width="250" />
      <el-table-column :label="$t('tasks.schedule')" min-width="150">
        <template #default="{ row }">
          <div v-if="row.schedule_type === 1">
            <el-tag type="primary">Cron</el-tag>
            <div class="schedule-detail">{{ row.cron_expression }}</div>
          </div>
          <div v-else>
            <el-tag type="success">Interval</el-tag>
            <div class="schedule-detail">{{ row.interval_seconds }}s</div>
          </div>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tasks.logCount')" width="120">
        <template #default="{ row }">
          <el-tag :type="row.log_count > 0 ? 'info' : ''">
            {{ row.log_count }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tasks.lastExecution')" width="140">
        <template #default="{ row }">
          <el-tag
            v-if="row.last_execution_success === true"
            type="success"
          >
            {{ $t('tasks.lastExecutionSuccess') }}
          </el-tag>
          <el-tag
            v-else-if="row.last_execution_success === false"
            type="danger"
          >
            {{ $t('tasks.lastExecutionFailed') }}
          </el-tag>
          <span v-else class="text-muted">
            {{ $t('tasks.lastExecutionUnknown') }}
          </span>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tasks.command')" prop="command" min-width="250">
        <template #default="{ row }">
          <code>{{ row.command }} {{ row.args.join(' ') }}</code>
        </template>
      </el-table-column>
      <el-table-column :label="$t('tasks.status')" width="100">
        <template #default="{ row }">
          <el-switch
            v-model="row.enabled"
            @change="toggleTaskStatus(row)"
          ></el-switch>
        </template>
      </el-table-column>
      <el-table-column :label="$t('common.actions')" width="180" fixed="right">
        <template #default="{ row }">
          <el-button-group>
            <el-button
              size="small"
              :icon="VideoPlay"
              @click="executeTask(row.id)"
              :title="$t('tasks.execute')"
            ></el-button>
            <el-button
              size="small"
              :icon="Notebook"
              @click="viewTaskLogs(row.id)"
              :title="$t('logs.title')"
            ></el-button>
            <el-button
              size="small"
              :icon="Edit"
              @click="editTask(row.id)"
              :title="$t('common.edit')"
            ></el-button>
            <el-button
              size="small"
              :icon="Delete"
              type="danger"
              @click="deleteTask(row)"
              :title="$t('common.delete')"
            ></el-button>
          </el-button-group>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-wrapper">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="totalTasks"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="fetchTasks"
        @current-change="fetchTasks"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, Edit, Delete, VideoPlay, Notebook } from '@element-plus/icons-vue'
import { useTaskStore } from '@/stores/taskStore'
import type { Task } from '@/types/task'

const router = useRouter()
const taskStore = useTaskStore()

const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(20)
const totalTasks = ref(0)

const tasks = ref<Task[]>([])

const filteredTasks = computed(() => {
  if (!searchQuery.value) return tasks.value
  const query = searchQuery.value.toLowerCase()
  return tasks.value.filter(task =>
    task.name.toLowerCase().includes(query) ||
    task.description?.toLowerCase().includes(query) ||
    task.command.toLowerCase().includes(query)
  )
})

const fetchTasks = async () => {
  loading.value = true
  try {
    const response = await taskStore.getTasks({
      skip: (currentPage.value - 1) * pageSize.value,
      limit: pageSize.value,
      search: searchQuery.value || undefined
    })
    tasks.value = response.data
    totalTasks.value = response.total
  } catch (error) {
    ElMessage.error('Failed to fetch tasks')
  } finally {
    loading.value = false
  }
}

const goToNewTask = () => {
  router.push({ name: 'task-new' })
}


const viewTaskLogs = (id: number) => {
  router.push({ name: 'logs', params: { id } })
}

const editTask = (id: number) => {
  router.push({ name: 'task-edit', params: { id } })
}

const executeTask = async (id: number) => {
  try {
    await taskStore.executeTask(id)
    ElMessage.success('Task execution started')
  } catch (error) {
    ElMessage.error('Failed to execute task')
  }
}

const toggleTaskStatus = async (task: Task) => {
  try {
    await taskStore.updateTask(task.id, { enabled: task.enabled })
    ElMessage.success(`Task ${task.enabled ? 'enabled' : 'disabled'}`)
  } catch (error) {
    task.enabled = !task.enabled // Revert on error
    ElMessage.error('Failed to update task status')
  }
}

const deleteTask = async (task: Task) => {
  try {
    await ElMessageBox.confirm(
      `Are you sure you want to delete task "${task.name}"?`,
      'Confirm Delete',
      {
        confirmButtonText: 'Delete',
        cancelButtonText: 'Cancel',
        type: 'warning'
      }
    )
    await taskStore.deleteTask(task.id)
    ElMessage.success('Task deleted')
    fetchTasks()
  } catch (error) {
    // User cancelled or error
  }
}

const tableRowClassName = ({ row }: { row: Task }) => {
  return row.enabled ? '' : 'disabled-row'
}

onMounted(() => {
  fetchTasks()
})
</script>

<style lang="scss" scoped>
.task-list-view {
  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;

    .header-actions {
      display: flex;
      align-items: center;
    }
  }

  .task-link {
    color: var(--el-color-primary);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  .schedule-detail {
    margin-top: 4px;
    font-size: 0.9em;
    color: var(--el-text-color-secondary);
  }

  .pagination-wrapper {
    margin-top: 20px;
    display: flex;
    justify-content: center;
  }

  :deep(.disabled-row) {
    opacity: 0.6;
  }

  .text-muted {
    color: var(--el-text-color-secondary);
    font-size: 0.9em;
  }

  :deep(.el-table) {
    min-width: 100%;
  }

  :deep(.el-table__body-wrapper) {
    overflow-x: auto;
  }
}
</style>