import { request } from './request'
import type { Expectation, ExpectationCreate, ExpectationUpdate } from '@/types/expectation'

export function createExpectation(data: ExpectationCreate) {
  return request.post<Expectation>('/api/expectations', data)
}

export function getExpectations(params?: { skip?: number; limit?: number }) {
  return request.get<Expectation[]>('/api/expectations', { params })
}

export function getActiveExpectation() {
  return request.get<Expectation>('/api/expectations/active')
}

export function getExpectationById(id: string) {
  return request.get<Expectation>(`/api/expectations/${id}`)
}

export function updateExpectation(id: string, data: ExpectationUpdate) {
  return request.put<Expectation>(`/api/expectations/${id}`, data)
}

export function deleteExpectation(id: string) {
  return request.delete(`/api/expectations/${id}`)
}

export function activateExpectation(id: string) {
  return request.post(`/api/expectations/${id}/activate`)
}

export function copyExpectation(id: string) {
  return request.post<Expectation>(`/api/expectations/${id}/copy`)
}
