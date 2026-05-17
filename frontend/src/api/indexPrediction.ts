import { request } from './request'
import type {
  PredictionRequest, PredictionTask, PredictionResult,
  IndexMetadata, SectorInfo, TaskStatusResponse
} from '@/types/indexPrediction'

export function startPrediction(data: PredictionRequest) {
  return request.post<{ task_id: string; status: string }>('/api/index-prediction/analyze', data)
}

export function getTaskStatus(taskId: string) {
  return request.get<TaskStatusResponse>(`/api/index-prediction/tasks/${taskId}/status`)
}

export function getTaskResult(taskId: string) {
  return request.get<{ task_id: string; status: string; result?: PredictionResult }>(
    `/api/index-prediction/tasks/${taskId}/result`
  )
}

export function listTasks(params?: { status?: string; skip?: number; limit?: number }) {
  return request.get<{ tasks: PredictionTask[]; total: number }>('/api/index-prediction/tasks', { params })
}

export function cancelTask(taskId: string) {
  return request.post(`/api/index-prediction/tasks/${taskId}/cancel`)
}

export function deleteTask(taskId: string) {
  return request.delete(`/api/index-prediction/tasks/${taskId}`)
}

export function markTaskFailed(taskId: string) {
  return request.post(`/api/index-prediction/tasks/${taskId}/mark-failed`)
}

export function retryTask(taskId: string) {
  return request.post<{ task_id: string; status: string }>(`/api/index-prediction/tasks/${taskId}/retry`)
}

export function getPredictionHistory(params?: { skip?: number; limit?: number }) {
  return request.get<PredictionTask[]>('/api/index-prediction/history', { params })
}

export function getIndices() {
  return request.get<IndexMetadata[]>('/api/index-prediction/indices')
}

export function getSectors() {
  return request.get<SectorInfo[]>('/api/index-prediction/sectors')
}
