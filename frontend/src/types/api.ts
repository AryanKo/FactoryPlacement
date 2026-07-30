export type ConfidenceLevel = 'measured' | 'qualitative' | 'no_data' | string;

export interface Indicator {
  value: number | string | null;
  unit?: string | null;
  source: string | null;
  confidence: ConfidenceLevel;
}

export interface RiskRequest {
  lat: number;
  lon: number;
}

export interface RiskResponse {
  location: {
    lat: number;
    lon: number;
    name?: string;
    region?: string;
  };
  indicators: {
    surface_water_trend?: Indicator;
    flood_exposure?: Indicator;
    rainfall_proxy?: Indicator;
    groundwater_depletion?: Indicator;
    soil_moisture?: Indicator;
    [key: string]: Indicator | undefined;
  };
  computed_at: string;
}

export interface ExplainRequest {
  indicators: RiskResponse['indicators'];
  lat?: number;
  lon?: number;
}

export interface RejectedClaim {
  id: string;
  claim: string;
  reason: string;
  original_statement?: string;
  detected_at?: string;
}

export interface GroundedClaim {
  id: string;
  claim: string;
  source_indicator: string;
  verified_value?: string;
}

export interface VerificationData {
  claims_checked: number;
  claims_grounded: number;
  claims_rejected: number;
  trust_score: number; // e.g. 0.8 (80%)
  rejected_claims?: RejectedClaim[];
  grounded_claims?: GroundedClaim[];
}

export interface RecommendationData {
  text: string;
  source_doc: string;
  source_excerpt: string;
  section: string;
}

export interface ExplainResponse {
  explanation: string;
  recommendation: RecommendationData;
  verification: VerificationData;
}

export interface PresetLocation {
  id: string;
  name: string;
  region: string;
  lat: number;
  lon: number;
  description: string;
  badge?: string;
}
