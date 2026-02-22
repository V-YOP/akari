export interface Task {
  id: number
  name: string
  description?: string
  command: string
  args: string[]
  schedule_type: 1 | 2  // 1=cron, 2=interval
  cron_expression?: string
  interval_seconds?: number
  enabled: boolean
  timeout: number
  max_concurrent: number
  created_at: string
  updated_at: string
  log_count: number
  last_execution_success?: boolean
}

export interface TaskCreate {
  name: string
  description?: string
  command: string
  args?: string[]
  schedule_type: 1 | 2
  cron_expression?: string
  interval_seconds?: number
  enabled?: boolean
  timeout?: number
  max_concurrent?: number
}

export interface TaskUpdate {
  name?: string
  description?: string
  command?: string
  args?: string[]
  schedule_type?: 1 | 2
  cron_expression?: string
  interval_seconds?: number
  enabled?: boolean
  timeout?: number
  max_concurrent?: number
}

export interface TaskLog {
  id: number
  task_id: number
  status: number
  started_at: string
  finished_at?: string
  duration?: number
  command_executed: string
  stdout?: string
  stderr?: string
  exit_code?: number
  error_message?: string
  created_at: string
}

export interface PaginationParams {
  skip?: number
  limit?: number
  search?: string
  enabled?: boolean
}

export interface PaginatedResponse<T> {
  total: number
  skip: number
  limit: number
  data: T[]
}

export interface TestExecuteResult {
  exit_code: number
  stdout: string
  stderr: string
}