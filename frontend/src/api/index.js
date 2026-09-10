import request from '../api/request'

export async function login(payload) {
  return request.post('/auth/login', payload)
}

export async function fetchContracts() {
  return request.get('/contracts')
}

export async function fetchContract(contractId) {
  return request.get(`/contracts/${contractId}`)
}

export async function uploadContract(formData) {
  return request.post('/contracts/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function reviewContract(contractId, reviewType = 'risk') {
  return request.post(`/review/${contractId}?review_type=${reviewType}`, {})
}

export async function fetchReviewProgress(taskId) {
  return request.get(`/review/progress/${taskId}`)
}

export async function fetchReports(contractId) {
  return request.get(`/review/reports/${contractId}`)
}

export async function generateContract(payload) {
  return request.post('/generation/contract', payload)
}

export async function compareTexts(textA, textB) {
  return request.post('/compare/text', { text_a: textA, text_b: textB })
}

export async function complianceCheck(contractId) {
  return request.post(`/compliance/${contractId}`, {})
}

export async function fetchClauses() {
  return request.get('/knowledge/clauses')
}

export async function fetchRegulations() {
  return request.get('/knowledge/regulations')
}

export async function rebuildIndex() {
  return request.post('/knowledge/rebuild-index', {})
}

export async function sendChat(message, sessionId) {
  return request.post('/chat', { message, session_id: sessionId })
}
