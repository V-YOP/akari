import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/utils/api'
import type { Task, TaskCreate, TaskUpdate, PaginationParams, PaginatedResponse, TaskLog, TestExecuteResult } from '@/types/task'

export const useTaskStore = defineStore('task', () => {
  const tasks = ref<Task[]>([])

  const getTasks = async (params?: PaginationParams): Promise<PaginatedResponse<Task>> => {
    const response = await api.get('/tasks', { params })
    return response.data
  }

  const getTask = async (id: number): Promise<Task> => {
    const response = await api.get(`/tasks/${id}`)
    return response.data
  }

  const createTask = async (taskData: TaskCreate): Promise<Task> => {
    const response = await api.post('/tasks', taskData)
    return response.data
  }

  const updateTask = async (id: number, taskData: TaskUpdate): Promise<Task> => {
    const response = await api.put(`/tasks/${id}`, taskData)
    return response.data
  }

  const deleteTask = async (id: number): Promise<void> => {
    await api.delete(`/tasks/${id}`)
  }

  const executeTask = async (id: number): Promise<void> => {
    await api.post(`/tasks/${id}/execute`)
  }

  const testExecute = async (command: string, args: string[], timeout: number): Promise<TestExecuteResult> => {
    const response = await api.post(`/tasks/test_execute`, {
      command,
      args,
      timeout
    })
    return response.data
  }

  const getTaskLogs = async (taskId: number, params?: PaginationParams): Promise<PaginatedResponse<TaskLog>> => {
    const response = await api.get(`/tasks/${taskId}/logs`, { params })
    return response.data
  }

  return {
    tasks,
    getTasks,
    getTask,
    createTask,
    updateTask,
    deleteTask,
    executeTask,
    testExecute,
    getTaskLogs
  }
})