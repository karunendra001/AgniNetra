import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 8000,
});

/**
 * Fetch all current detections from the ML backend.
 * Expected response shape (agree this with your ML teammate):
 * [
 *   {
 *     id: number,
 *     location: string,
 *     lat: number,
 *     lng: number,
 *     classification: "Vegetation Fire" | "Industrial Heat Source" | "Persistent Thermal Anomaly" | "Unclassified",
 *     confidence: number,      // 0-100
 *     brightness: number,      // Kelvin
 *     frp: number,             // Fire Radiative Power (MW)
 *     satellite: string,       // e.g. "VIIRS-NOAA20"
 *     time: string             // e.g. "5m ago" or ISO timestamp
 *   },
 *   ...
 * ]
 */
export async function fetchDetections() {
  const response = await api.get('/api/detections');
  return response.data;
}

/**
 * Fetch summary stats for the KPI cards.
 * Expected response shape:
 * {
 *   fire: number,
 *   industrial: number,
 *   persistent: number,
 *   highConfidence: number
 * }
 */
export async function fetchStats() {
  const response = await api.get('/api/stats');
  return response.data;
}

export default api;