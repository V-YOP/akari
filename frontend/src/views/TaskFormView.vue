<template>
  <div class="task-form-view">
    <div class="view-header">
      <h2>{{ isEditMode ? $t('tasks.editTask') : $t('tasks.newTask') }}</h2>
      <el-button @click="goBack">
        {{ $t('common.back') }}
      </el-button>
    </div>

    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="150px"
      class="task-form"
      v-loading="loading"
    >
      <el-form-item :label="$t('tasks.name')" prop="name">
        <el-input v-model="form.name" :placeholder="$t('tasks.namePlaceholder')" />
      </el-form-item>

      <el-form-item :label="$t('tasks.description')" prop="description">
        <el-input
          v-model="form.description"
          type="textarea"
          :rows="3"
          :placeholder="$t('tasks.descriptionPlaceholder')"
        />
      </el-form-item>

      <el-form-item :label="$t('tasks.command')" prop="command">
        <el-input
          v-model="form.command"
          :placeholder="$t('tasks.commandPlaceholder')"
          style="width: 100%;"
        />
        <div class="form-hint">{{ $t('tasks.commandHint') }}</div>
      </el-form-item>

      <el-form-item :label="$t('tasks.arguments')" prop="args">
        <el-tag
          v-for="(arg, index) in form.args"
          :key="index"
          closable
          @close="removeArg(index)"
          style="margin-right: 5px; margin-bottom: 5px;"
        >
          {{ arg }}
        </el-tag>
        <div style="display: flex; margin-top: 10px;">
          <el-input
            v-model="newArg"
            :placeholder="$t('tasks.argPlaceholder')"
            style="margin-right: 10px;"
            @keyup.enter="addArg"
          />
          <el-button @click="addArg">{{ $t('common.add') }}</el-button>
        </div>
      </el-form-item>

      <el-form-item :label="$t('tasks.scheduleType')" prop="schedule_type">
        <el-radio-group v-model="form.schedule_type">
          <el-radio :label="1">Cron</el-radio>
          <el-radio :label="2">Interval</el-radio>
        </el-radio-group>
      </el-form-item>

      <el-form-item
        v-if="form.schedule_type === 1"
        :label="$t('tasks.cronExpression')"
        prop="cron_expression"
      >
        <el-input
          v-model="form.cron_expression"
          :placeholder="$t('tasks.cronPlaceholder')"
          style="width: 300px;"
        />
        <div class="form-hint">{{ $t('tasks.cronHint') }}</div>
      </el-form-item>

      <el-form-item
        v-if="form.schedule_type === 2"
        :label="$t('tasks.interval')"
        prop="interval_seconds"
      >
        <el-input-number
          v-model="form.interval_seconds"
          :min="1"
          :max="86400"
          :step="1"
          style="width: 300px;"
        />
        <span style="margin-left: 10px;">{{ $t('tasks.seconds') }}</span>
        <div class="form-hint">{{ $t('tasks.intervalHint') }}</div>
      </el-form-item>

      <el-form-item :label="$t('tasks.timeout')" prop="timeout">
        <el-input-number
          v-model="form.timeout"
          :min="1"
          :max="3600"
          :step="10"
          style="width: 300px;"
        />
        <span style="margin-left: 10px;">{{ $t('tasks.seconds') }}</span>
        <div class="form-hint">{{ $t('tasks.timeoutHint') }}</div>
      </el-form-item>

      <el-form-item :label="$t('tasks.maxConcurrent')" prop="max_concurrent">
        <el-input-number
          v-model="form.max_concurrent"
          :min="1"
          :max="10"
          :step="1"
          style="width: 300px;"
        />
        <div class="form-hint">{{ $t('tasks.concurrentHint') }}</div>
      </el-form-item>

      <el-form-item :label="$t('tasks.enabled')" prop="enabled">
        <el-switch v-model="form.enabled" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" @click="submitForm">
          {{ isEditMode ? $t('common.update') : $t('common.create') }}
        </el-button>
        <el-button @click="resetForm">{{ $t('common.reset') }}</el-button>
        <el-button @click="testTask" :loading="testing">
          {{ $t('tasks.test') }}
        </el-button>
      </el-form-item>
    </el-form>

    <!-- Test Execution Result Dialog -->
    <el-dialog
      v-model="showTestResult"
      :title="$t('tasks.testResult')"
      width="80%"
      top="5vh"
    >
      <div v-if="testResult" class="test-result">
        <div class="result-section">
          <h3>{{ $t('tasks.exitCode') }}</h3>
          <div :class="['exit-code', testResult.exit_code === 0 ? 'success' : 'error']">
            {{ testResult.exit_code }}
          </div>
        </div>

        <div v-if="testResult.stdout" class="result-section">
          <h3>{{ $t('tasks.stdout') }}</h3>
          <pre class="output-block">{{ testResult.stdout }}</pre>
        </div>

        <div v-if="testResult.stderr" class="result-section">
          <h3>{{ $t('tasks.stderr') }}</h3>
          <pre class="error-block">{{ testResult.stderr }}</pre>
        </div>
      </div>

      <template #footer>
        <el-button @click="showTestResult = false">
          {{ $t('common.close') }}
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { useTaskStore } from '@/stores/taskStore'
import type { TaskCreate, TaskUpdate, TestExecuteResult } from '@/types/task'

const route = useRoute()
const router = useRouter()
const taskStore = useTaskStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const testing = ref(false)
const newArg = ref('')
const showTestResult = ref(false)
const testResult = ref<TestExecuteResult | null>(null)

const isEditMode = computed(() => route.name === 'task-edit')

const form = ref<TaskCreate | TaskUpdate>({
  name: '',
  description: '',
  command: '',
  args: [],
  schedule_type: 1,
  cron_expression: '',
  interval_seconds: 60,
  enabled: true,
  timeout: 300,
  max_concurrent: 1
})

const rules: FormRules = {
  name: [
    { required: true, message: 'Please enter task name', trigger: 'blur' },
    { min: 1, max: 255, message: 'Length should be 1 to 255', trigger: 'blur' }
  ],
  command: [
    { required: true, message: 'Please enter command', trigger: 'blur' }
  ],
  cron_expression: [
    {
      required: true,
      message: 'Please enter cron expression',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (form.value.schedule_type === 1 && !value) {
          callback(new Error('Cron expression is required'))
        } else {
          callback()
        }
      }
    }
  ],
  interval_seconds: [
    {
      required: true,
      message: 'Please enter interval',
      trigger: 'blur',
      validator: (rule, value, callback) => {
        if (form.value.schedule_type === 2 && (!value || value < 1)) {
          callback(new Error('Interval must be at least 1 second'))
        } else {
          callback()
        }
      }
    }
  ]
}

const addArg = () => {
  if (newArg.value.trim()) {
    if (!form.value.args) form.value.args = []
    form.value.args.push(newArg.value.trim())
    newArg.value = ''
  }
}

const removeArg = (index: number) => {
  if (form.value.args) {
    form.value.args.splice(index, 1)
  }
}

const loadTask = async (id: string) => {
  loading.value = true
  try {
    const task = await taskStore.getTask(parseInt(id))
    form.value = {
      name: task.name,
      description: task.description,
      command: task.command,
      args: task.args,
      schedule_type: task.schedule_type,
      cron_expression: task.cron_expression,
      interval_seconds: task.interval_seconds,
      enabled: task.enabled,
      timeout: task.timeout,
      max_concurrent: task.max_concurrent
    }
  } catch (error) {
    ElMessage.error('Failed to load task')
    router.push({ name: 'tasks' })
  } finally {
    loading.value = false
  }
}

const submitForm = async () => {
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) return

    loading.value = true
    try {
      if (isEditMode.value) {
        const id = parseInt(route.params.id as string)
        await taskStore.updateTask(id, form.value as TaskUpdate)
        ElMessage.success('Task updated successfully')
      } else {
        await taskStore.createTask(form.value as TaskCreate)
        ElMessage.success('Task created successfully')
        router.push({ name: 'tasks' })
      }
    } catch (error) {
      ElMessage.error('Failed to save task')
    } finally {
      loading.value = false
    }
  })
}

const resetForm = () => {
  if (isEditMode.value) {
    loadTask(route.params.id as string)
  } else {
    formRef.value?.resetFields()
    form.value.args = []
  }
}

const testTask = async () => {
  // 验证表单
  if (!formRef.value) return

  await formRef.value.validate(async (valid) => {
    if (!valid) {
      ElMessage.error('Please fix form errors before testing')
      return
    }

    testing.value = true
    try {
      // 从表单中获取命令、参数和超时时间
      const command = form.value.command
      const args = form.value.args || []
      const timeout = form.value.timeout || 300

      const result = await taskStore.testExecute(command, args, timeout)
      testResult.value = result
      showTestResult.value = true
    } catch (error) {
      ElMessage.error('Failed to execute test')
    } finally {
      testing.value = false
    }
  })
}

const goBack = () => {
  router.push({ name: 'tasks' })
}

onMounted(() => {
  if (isEditMode.value) {
    loadTask(route.params.id as string)
  }
})
</script>

<style lang="scss" scoped>
.task-form-view {
  .view-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 30px;
  }

  .task-form {
    max-width: 800px;
    background: var(--el-bg-color);
    padding: 30px;
    border-radius: 8px;
    box-shadow: var(--el-box-shadow-light);
  }

  .form-hint {
    font-size: 0.9em;
    color: var(--el-text-color-secondary);
    margin-top: 5px;
  }

  .test-result {
    max-height: 70vh;
    overflow-y: auto;

    .result-section {
      margin-bottom: 20px;

      h3 {
        margin-bottom: 10px;
        color: var(--el-text-color-primary);
      }
    }

    .exit-code {
      display: inline-block;
      padding: 4px 12px;
      border-radius: 4px;
      font-weight: bold;
      font-family: monospace;
      font-size: 1.1em;

      &.success {
        background-color: var(--el-color-success-light-9);
        color: var(--el-color-success);
      }

      &.error {
        background-color: var(--el-color-error-light-9);
        color: var(--el-color-error);
      }
    }

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