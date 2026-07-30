import type { RiskResponse, ExplainResponse, PresetLocation } from '../types/api';

export const PRESET_LOCATIONS: PresetLocation[] = [
  {
    id: 'chennai',
    name: 'Chennai Coastline (GDG VIT)',
    region: 'Tamil Nadu, India',
    lat: 12.9716,
    lon: 80.2437,
    description: 'Rapid urban coastal development with seasonal monsoon variance and data gaps.',
    badge: 'Demo Default'
  },
  {
    id: 'central_valley',
    name: 'Central Valley Basin',
    region: 'California, USA',
    lat: 36.7783,
    lon: -119.4179,
    description: 'High agricultural water extraction; significant groundwater depletion claims flagged.',
    badge: 'High Risk'
  },
  {
    id: 'aral_sea',
    name: 'Aral Sea North Basin',
    region: 'Kazakhstan / Uzbekistan',
    lat: 45.0,
    lon: 59.0,
    description: 'Historic surface water loss (-68.2%); 100% grounded telemetry verification.',
    badge: 'High Trust'
  },
  {
    id: 'naivasha',
    name: 'Lake Naivasha Region',
    region: 'Rift Valley, Kenya',
    lat: -0.7167,
    lon: 36.4333,
    description: 'Horticultural pressure with qualitative flood risk and incomplete soil moisture telemetry.',
    badge: 'Data Gap'
  }
];

export const MOCK_RISK_FIXTURES: Record<string, RiskResponse> = {
  // Chennai (GDG VIT Chennai Hackathon demo default)
  chennai: {
    location: {
      lat: 12.9716,
      lon: 80.2437,
      name: 'Chennai Coastline',
      region: 'Tamil Nadu, India'
    },
    indicators: {
      surface_water_trend: {
        value: -12.4,
        unit: '% change 10yr',
        source: 'GEE/JRC-GSW',
        confidence: 'measured'
      },
      flood_exposure: {
        value: 'moderate',
        unit: null,
        source: 'GEE/flood-layer',
        confidence: 'measured'
      },
      rainfall_proxy: {
        value: null,
        unit: null,
        source: null,
        confidence: 'no_data'
      },
      groundwater_depletion: {
        value: -4.8,
        unit: 'm level drop',
        source: 'GEE/GRACE-FO',
        confidence: 'measured'
      }
    },
    computed_at: new Date().toISOString()
  },

  // Central Valley (California)
  central_valley: {
    location: {
      lat: 36.7783,
      lon: -119.4179,
      name: 'Central Valley Basin',
      region: 'California, USA'
    },
    indicators: {
      surface_water_trend: {
        value: -24.8,
        unit: '% change 10yr',
        source: 'GEE/JRC-GSW',
        confidence: 'measured'
      },
      flood_exposure: {
        value: 'severe',
        unit: null,
        source: 'GEE/flood-layer',
        confidence: 'measured'
      },
      rainfall_proxy: {
        value: 340,
        unit: 'mm/yr',
        source: 'CHIRPS-v2',
        confidence: 'measured'
      },
      groundwater_depletion: {
        value: -18.2,
        unit: 'm aquifer loss',
        source: 'GEE/GRACE-FO',
        confidence: 'measured'
      }
    },
    computed_at: new Date().toISOString()
  },

  // Aral Sea
  aral_sea: {
    location: {
      lat: 45.0,
      lon: 59.0,
      name: 'Aral Sea Basin',
      region: 'Kazakhstan'
    },
    indicators: {
      surface_water_trend: {
        value: -68.2,
        unit: '% change 10yr',
        source: 'GEE/JRC-GSW',
        confidence: 'measured'
      },
      flood_exposure: {
        value: 'low',
        unit: null,
        source: 'GEE/flood-layer',
        confidence: 'measured'
      },
      rainfall_proxy: {
        value: 110,
        unit: 'mm/yr',
        source: 'CHIRPS-v2',
        confidence: 'measured'
      }
    },
    computed_at: new Date().toISOString()
  },

  // Lake Naivasha
  naivasha: {
    location: {
      lat: -0.7167,
      lon: 36.4333,
      name: 'Lake Naivasha Basin',
      region: 'Rift Valley, Kenya'
    },
    indicators: {
      surface_water_trend: {
        value: -6.1,
        unit: '% change 10yr',
        source: 'GEE/JRC-GSW',
        confidence: 'measured'
      },
      flood_exposure: {
        value: 'moderate',
        unit: null,
        source: 'GEE/flood-layer',
        confidence: 'measured'
      },
      soil_moisture: {
        value: null,
        unit: null,
        source: null,
        confidence: 'no_data'
      },
      rainfall_proxy: {
        value: null,
        unit: null,
        source: null,
        confidence: 'no_data'
      }
    },
    computed_at: new Date().toISOString()
  }
};

export const MOCK_EXPLAIN_FIXTURES: Record<string, ExplainResponse> = {
  // Chennai: 80% Trust Score (4 grounded, 1 rejected, 1 no_data)
  chennai: {
    explanation:
      'Analysis of satellite observations around the Chennai coastline indicates a 10-year surface water trend of -12.4% measured via GEE JRC-GSW data. Flood exposure is evaluated as moderate. Atmospheric precipitation rainfall proxy data is currently unmeasured for this grid tile.',
    recommendation: {
      text: 'Implement site-level rainwater harvesting and conduct seasonal runoff monitoring to mitigate local water stress.',
      source_doc: 'AWS Water Stewardship Standard',
      source_excerpt: 'Catchment water governance requires facilities to assess local water availability and shared water challenges with local stakeholders.',
      section: 'Section 1.3 - Site Water Balance & Risk'
    },
    verification: {
      claims_checked: 5,
      claims_grounded: 4,
      claims_rejected: 1,
      trust_score: 0.8,
      rejected_claims: [
        {
          id: 'rej-1',
          claim: 'Sub-surface aquifer storage recharged by +35.5% over the past 3 years.',
          reason: 'Unverifiable — no groundwater telemetry or satellite GEE source for +35.5% recharge at target coordinates.',
          original_statement: 'Gemma 4 generated: "Sub-surface aquifer storage recharged by +35.5% over the past 3 years due to local conservation efforts."'
        }
      ],
      grounded_claims: [
        { id: 'g-1', claim: '10-year surface water trend is -12.4%', source_indicator: 'GEE/JRC-GSW' },
        { id: 'g-2', claim: 'Flood risk exposure is categorized as moderate', source_indicator: 'GEE/flood-layer' },
        { id: 'g-3', claim: 'Groundwater drop level measured at -4.8m', source_indicator: 'GEE/GRACE-FO' },
        { id: 'g-4', claim: 'Rainfall proxy telemetry flagged as missing/no_data', source_indicator: 'System Data Guard' }
      ]
    }
  },

  // Central Valley: 60% Trust Score (3 grounded, 2 rejected)
  central_valley: {
    explanation:
      'The Central Valley region demonstrates severe hydrologic stress with a -24.8% surface water decline and -18.2m deep aquifer loss measured via satellite altimetry. Flood risk exposure remains categorized as severe due to riverine overflow corridors.',
    recommendation: {
      text: 'Adopt precision drip irrigation and mandate groundwater extraction accounting under sustainable agricultural governance standards.',
      source_doc: 'AWS Water Stewardship Standard',
      source_excerpt: 'Facilities operating in high baseline water stress areas shall maintain a verifiable water balance register and minimize depletion of non-renewable aquifers.',
      section: 'Section 2.1 - Sustainable Water Balance'
    },
    verification: {
      claims_checked: 5,
      claims_grounded: 3,
      claims_rejected: 2,
      trust_score: 0.6,
      rejected_claims: [
        {
          id: 'rej-cv-1',
          claim: 'Regional water utility reserves will guarantee 100% supply through 2030.',
          reason: 'Unverifiable — utility reservoir reserves absent from GEE payload.',
          original_statement: 'Gemma 4 generated: "Regional water utility reserves will guarantee 100% supply through 2030 despite drought conditions."'
        },
        {
          id: 'rej-cv-2',
          claim: 'Desalination pipelines reduce baseline stress by 15%.',
          reason: 'Unverifiable — infrastructure capacity claim unsupported by satellite telemetry.',
          original_statement: 'Gemma 4 generated: "Desalination pipelines reduce baseline stress by 15% across agricultural zones."'
        }
      ],
      grounded_claims: [
        { id: 'g-cv-1', claim: 'Surface water change is -24.8% over 10 years', source_indicator: 'GEE/JRC-GSW' },
        { id: 'g-cv-2', claim: 'Flood exposure rating is severe', source_indicator: 'GEE/flood-layer' },
        { id: 'g-cv-3', claim: 'Annual rainfall proxy recorded at 340mm/yr', source_indicator: 'CHIRPS-v2' }
      ]
    }
  },

  // Aral Sea: 100% Trust Score (4 grounded, 0 rejected)
  aral_sea: {
    explanation:
      'Satellite telemetry confirms extreme environmental degradation with a 10-year surface water decline of -68.2%. Flood exposure remains low while annual precipitation proxy measures 110mm/yr.',
    recommendation: {
      text: 'Establish transboundary watershed protection agreements and strict ecological flow reserves.',
      source_doc: 'AWS Water Stewardship Standard',
      source_excerpt: 'Important Water-Related Areas (IWRAs) require immediate conservation actions when ecological thresholds are violated.',
      section: 'Section 3.4 - Protection of Important Water Areas'
    },
    verification: {
      claims_checked: 4,
      claims_grounded: 4,
      claims_rejected: 0,
      trust_score: 1.0,
      rejected_claims: [],
      grounded_claims: [
        { id: 'g-as-1', claim: 'Surface water reduction measured at -68.2%', source_indicator: 'GEE/JRC-GSW' },
        { id: 'g-as-2', claim: 'Flood exposure rating is low', source_indicator: 'GEE/flood-layer' },
        { id: 'g-as-3', claim: 'Precipitation proxy is 110mm/yr', source_indicator: 'CHIRPS-v2' },
        { id: 'g-as-4', claim: 'All claims grounded strictly in satellite telemetry', source_indicator: 'Gemma Guardrail Verifier' }
      ]
    }
  },

  // Naivasha: 75% Trust Score (3 grounded, 1 rejected, 2 no_data)
  naivasha: {
    explanation:
      'Lake Naivasha basin telemetry shows a slight surface water decrease of -6.1% with moderate flood risk. Both soil moisture and rainfall proxy datasets are currently uncomputed due to cloud cover data gaps.',
    recommendation: {
      text: 'Deploy ground telemetry sensors to bridge remote sensing data gaps and maintain community water governance.',
      source_doc: 'AWS Water Stewardship Standard',
      source_excerpt: 'Where remote sensing datasets are incomplete, site operators shall supplement with verified local monitoring.',
      section: 'Section 1.4 - Data Quality & Gaps'
    },
    verification: {
      claims_checked: 4,
      claims_grounded: 3,
      claims_rejected: 1,
      trust_score: 0.75,
      rejected_claims: [
        {
          id: 'rej-nv-1',
          claim: 'Local water table rose 2.1 meters after recent heavy downpours.',
          reason: 'Unverifiable — soil moisture & rainfall telemetry marked as no_data.',
          original_statement: 'Gemma 4 generated: "Local water table rose 2.1 meters after recent heavy downpours."'
        }
      ],
      grounded_claims: [
        { id: 'g-nv-1', claim: 'Surface water 10yr trend is -6.1%', source_indicator: 'GEE/JRC-GSW' },
        { id: 'g-nv-2', claim: 'Flood exposure is moderate', source_indicator: 'GEE/flood-layer' },
        { id: 'g-nv-3', claim: 'Soil moisture telemetry flagged as no_data', source_indicator: 'System Data Guard' }
      ]
    }
  }
};
