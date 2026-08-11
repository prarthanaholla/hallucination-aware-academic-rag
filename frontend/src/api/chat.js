import axios from 'axios'

const BASE = ''   // Vite proxy handles /ask → localhost:8000

export async function askQuestion(query, topK = 5) {
  const { data } = await axios.post('/ask', { query, top_k: topK })
  return data
}

export async function getHealth() {
  const { data } = await axios.get('/health')
  return data
}

export async function getStats() {
  const { data } = await axios.get('/stats')
  return data
}