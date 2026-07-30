import type { RiskRequest, RiskResponse, ExplainRequest, ExplainResponse } from '../types/api';
import { MOCK_RISK_FIXTURES, MOCK_EXPLAIN_FIXTURES, PRESET_LOCATIONS } from './mockData';

// Configurable flag for dev mode. Defaults to true for standalone laptop demoing.
export const USE_MOCK_API = true;
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api';

/**
 * Finds the closest mock key based on coordinates or defaults to 'chennai'
 */
function findClosestPresetKey(lat: number, lon: number): string {
  let closestKey = 'chennai';
  let minDistance = Infinity;

  PRESET_LOCATIONS.forEach((preset) => {
    const dist = Math.hypot(preset.lat - lat, preset.lon - lon);
    if (dist < minDistance) {
      minDistance = dist;
      closestKey = preset.id;
    }
  });

  return closestKey;
}

/**
 * GET /api/risk
 * Request: { lat: float, lon: float }
 */
export async function fetchRiskData(params: RiskRequest): Promise<RiskResponse> {
  if (USE_MOCK_API) {
    // Simulate network latency (350ms)
    await new Promise((resolve) => setTimeout(resolve, 350));
    
    const key = findClosestPresetKey(params.lat, params.lon);
    const template = MOCK_RISK_FIXTURES[key] || MOCK_RISK_FIXTURES.chennai;
    
    // Return mock response with dynamic exact lat/lon requested
    return {
      ...template,
      location: {
        ...template.location,
        lat: Number(params.lat.toFixed(4)),
        lon: Number(params.lon.toFixed(4))
      },
      computed_at: new Date().toISOString()
    };
  }

  const response = await fetch(`${API_BASE_URL}/risk?lat=${params.lat}&lon=${params.lon}`);
  if (!response.ok) {
    throw new Error(`GET /api/risk failed with status ${response.status}`);
  }
  return response.json();
}

/**
 * POST /api/explain
 * Request: { indicators: { ...from /api/risk... } }
 */
export async function fetchExplanation(payload: ExplainRequest): Promise<ExplainResponse> {
  if (USE_MOCK_API) {
    // Simulate Gemma 4 LLM + Guardrail Verifier reasoning pipeline delay (600ms)
    await new Promise((resolve) => setTimeout(resolve, 600));

    // Match fixture key based on indicator counts or surface water trend value
    const surfaceTrend = payload.indicators.surface_water_trend?.value;
    
    let key = 'chennai';
    if (typeof surfaceTrend === 'number') {
      if (surfaceTrend < -50) key = 'aral_sea';
      else if (surfaceTrend < -20) key = 'central_valley';
      else if (surfaceTrend > -10) key = 'naivasha';
    }

    return MOCK_EXPLAIN_FIXTURES[key] || MOCK_EXPLAIN_FIXTURES.chennai;
  }

  const response = await fetch(`${API_BASE_URL}/explain`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error(`POST /api/explain failed with status ${response.status}`);
  }

  return response.json();
}
