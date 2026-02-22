import { defineStore } from 'pinia'
import api from '@/utils/api'
import type { TaskLog, PaginationParams, PaginatedResponse } from '@/types/task'

export const useLogStore = defineStore('log', () => {
  const getLogs = async (params?: PaginationParams): Promise<PaginatedResponse<TaskLog>> => {
    const response = await api.get('/logs', { params })
    return response.data
  }

  const getLog = async (id: number): Promise<TaskLog> => {
    const response = await api.get(`/logs/${id}`)
    return response.data
  }

  const deleteLog = async (id: number): Promise<void> => {
    await api.delete(`/logs/${id}`)
  }

  const clearLogs = async (params?: { older_than_days?: number; task_id?: number }): Promise<void> => {
    await api.delete('/logs', { params })
  }

  return {
    getLogs,
    getLog,
    deleteLog,
    clearLogs
  }
})