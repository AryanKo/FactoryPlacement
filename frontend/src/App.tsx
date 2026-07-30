import React, { useState, useEffect, useCallback } from 'react';
import { fetchRiskData, fetchExplanation } from './api/client';
import type { RiskResponse, ExplainResponse } from './types/api';
import { PRESET_LOCATIONS } from './api/mockData';
import { GoogleMapView, PlacesAutocompleteInput } from './components/GoogleMapView';
import { RiskPanel } from './components/RiskPanel';
import { VerificationBadge } from './components/VerificationBadge';
import { RecommendationCard } from './components/RecommendationCard';
import { ComparePanel } from './components/ComparePanel';
import { ShieldCheck, Droplet, Code, Activity, AlertCircle, Navigation, MapPin, ArrowRight } from 'lucide-react';
import { APIProvider } from '@vis.gl/react-google-maps';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'verification' | 'compare' | 'contracts'>('verification');
  const [selectedLocation, setSelectedLocation] = useState<{ lat: number; lon: number }>({
    lat: PRESET_LOCATIONS[0].lat,
    lon: PRESET_LOCATIONS[0].lon
  });
  const [locationName, setLocationName] = useState<string>(PRESET_LOCATIONS[0].name);

  // Editable Lat / Lon state synchronized with map selection
  const [inputLat, setInputLat] = useState<string>(PRESET_LOCATIONS[0].lat.toFixed(4));
  const [inputLon, setInputLon] = useState<string>(PRESET_LOCATIONS[0].lon.toFixed(4));

  const [riskData, setRiskData] = useState<RiskResponse | null>(null);
  const [explainData, setExplainData] = useState<ExplainResponse | null>(null);
  const [loadingStep, setLoadingStep] = useState<'idle' | 'risk' | 'explain'>('idle');
  const [error, setError] = useState<string | null>(null);

  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';

  // Update input text fields whenever selectedLocation changes (via map click or preset)
  useEffect(() => {
    setInputLat(selectedLocation.lat.toFixed(4));
    setInputLon(selectedLocation.lon.toFixed(4));
  }, [selectedLocation]);

  // Sequenced execution pipeline: location select / map click / coordinate submit -> GET /api/risk -> POST /api/explain
  const runPipeline = useCallback(async (location: { lat: number; lon: number }, placeName?: string) => {
    setError(null);
    setLoadingStep('risk');
    if (placeName) setLocationName(placeName);

    try {
      // Step 1: GET /api/risk
      const riskResult = await fetchRiskData({ lat: location.lat, lon: location.lon });
      if (placeName) {
        riskResult.location.name = placeName;
      }
      setRiskData(riskResult);

      // Step 2: POST /api/explain
      setLoadingStep('explain');
      const explainResult = await fetchExplanation({
        indicators: riskResult.indicators,
        lat: location.lat,
        lon: location.lon,
      });
      setExplainData(explainResult);

    } catch (err: any) {
      console.error('AquaShield pipeline execution error:', err);
      setError(err.message || 'Pipeline execution failed.');
    } finally {
      setLoadingStep('idle');
    }
  }, []);

  // Initial load execution for default preset location
  useEffect(() => {
    runPipeline(selectedLocation, PRESET_LOCATIONS[0].name);
  }, []);

  const handleLocationSelect = (newLoc: { lat: number; lon: number }, placeName?: string) => {
    setSelectedLocation(newLoc);
    runPipeline(newLoc, placeName);
  };

  // Submit handler for manual Lat/Lon coordinate edits
  const handleCoordinateSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const lat = parseFloat(inputLat);
    const lon = parseFloat(inputLon);

    if (isNaN(lat) || isNaN(lon)) {
      setError('Please enter valid numeric latitude and longitude values.');
      return;
    }

    if (lat < -90 || lat > 90 || lon < -180 || lon > 180) {
      setError('Latitude must be between -90 and 90, Longitude between -180 and 180.');
      return;
    }

    const newLoc = { lat, lon };
    const name = `Custom Grid (${lat.toFixed(2)}, ${lon.toFixed(2)})`;
    setSelectedLocation(newLoc);
    runPipeline(newLoc, name);
  };

  return (
    <div className="relative w-screen h-screen overflow-hidden bg-[#090d16] text-gray-100 selection:bg-blue-500 selection:text-white">
      {/* 1. PERSISTENT TOP HEADER (Displayed at all times) */}
      <header className="fixed top-0 left-0 right-0 z-[3500] bg-slate-950/90 backdrop-blur-2xl border-b border-white/10 px-4 md:px-6 py-2.5 flex flex-col md:flex-row items-center justify-between gap-3 shadow-2xl">
        {/* Left Section: Brand Logo, Title & View Tabs */}
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2.5">
            <div className="p-1.5 rounded-xl bg-blue-500/20 border border-blue-400/40 text-blue-400 shadow-lg shadow-blue-950">
              <Droplet className="w-5 h-5 animate-pulse" />
            </div>
            <div>
              <div className="flex items-center gap-1.5">
                <h1 className="text-lg font-black tracking-tight text-white font-sans">
                  Aqua<span className="text-blue-400">Shield</span>
                </h1>
                <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/40 font-bold hidden sm:inline-block">
                  Gemma 4 Shield
                </span>
              </div>
              <p className="text-[10px] text-gray-400 font-mono">GDG VIT Chennai Hackathon</p>
            </div>
          </div>

          {/* View Mode Tabs */}
          <div className="glass-panel p-1 flex items-center gap-1 border border-white/10 text-xs">
            <button
              onClick={() => setActiveTab('verification')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all flex items-center gap-1 text-xs ${
                activeTab === 'verification'
                  ? 'bg-blue-600 text-white shadow-md font-semibold'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <ShieldCheck className="w-3.5 h-3.5" />
              Verifier View
            </button>
            <button
              onClick={() => setActiveTab('compare')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all flex items-center gap-1 text-xs ${
                activeTab === 'compare'
                  ? 'bg-blue-600 text-white shadow-md font-semibold'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Compare (P1)
            </button>
            <button
              onClick={() => setActiveTab('contracts')}
              className={`px-2.5 py-1 rounded-lg font-medium transition-all flex items-center gap-1 text-xs ${
                activeTab === 'contracts'
                  ? 'bg-blue-600 text-white shadow-md font-semibold'
                  : 'text-gray-400 hover:text-gray-200'
              }`}
            >
              <Code className="w-3.5 h-3.5" />
              Contracts
            </button>
          </div>

          {/* Preset Location Pills */}
          <div className="hidden lg:flex items-center gap-1 overflow-x-auto scrollbar-none">
            {PRESET_LOCATIONS.map((preset) => {
              const isSelected =
                Math.abs(selectedLocation.lat - preset.lat) < 0.05 &&
                Math.abs(selectedLocation.lon - preset.lon) < 0.05;

              return (
                <button
                  key={preset.id}
                  onClick={() => handleLocationSelect({ lat: preset.lat, lon: preset.lon }, preset.name)}
                  className={`text-[10px] px-2 py-0.5 rounded-full border whitespace-nowrap flex items-center gap-1 transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-400 shadow-md font-semibold'
                      : 'bg-slate-900/80 text-gray-300 border-white/10 hover:border-blue-400/50'
                  }`}
                >
                  <Navigation className="w-2.5 h-2.5 text-blue-400" />
                  {preset.name.split(' ')[0]}
                </button>
              );
            })}
          </div>
        </div>

        {/* TOP RIGHT CORNER: Places Search Bar & Below Editable Lat/Lon Inputs */}
        <div className="flex flex-col items-end gap-1.5 w-full md:w-80 lg:w-96 flex-shrink-0">
          {/* 1. Top Right Places Autocomplete Search Bar */}
          {apiKey ? (
            <APIProvider apiKey={apiKey} libraries={['places']}>
              <PlacesAutocompleteInput
                onPlaceSelect={(lat, lon, name) => handleLocationSelect({ lat, lon }, name)}
              />
            </APIProvider>
          ) : (
            <div className="w-full text-xs text-gray-400 font-mono bg-slate-900 px-3 py-1 rounded-xl border border-white/10 text-right">
              Set VITE_GOOGLE_MAPS_API_KEY for Places Search
            </div>
          )}

          {/* 2. Directly Below Search Bar: Editable Latitude and Longitude Control Form */}
          <form onSubmit={handleCoordinateSubmit} className="flex items-center gap-1.5 w-full bg-slate-900/90 p-1.5 rounded-xl border border-white/10 shadow-lg backdrop-blur-md">
            <div className="flex items-center gap-1 text-[10px] font-mono font-bold text-blue-400 pl-1 whitespace-nowrap">
              <MapPin className="w-3 h-3 text-blue-400" />
              <span>Grid:</span>
            </div>

            {/* Editable Latitude Input */}
            <div className="flex items-center gap-1 flex-1">
              <span className="text-[9px] font-mono text-gray-400 uppercase">Lat</span>
              <input
                type="text"
                value={inputLat}
                onChange={(e) => setInputLat(e.target.value)}
                placeholder="Lat"
                className="w-full bg-slate-950 text-gray-100 font-mono text-xs px-2 py-0.5 rounded border border-white/10 focus:outline-none focus:border-blue-400 text-center"
              />
            </div>

            {/* Editable Longitude Input */}
            <div className="flex items-center gap-1 flex-1">
              <span className="text-[9px] font-mono text-gray-400 uppercase">Lon</span>
              <input
                type="text"
                value={inputLon}
                onChange={(e) => setInputLon(e.target.value)}
                placeholder="Lon"
                className="w-full bg-slate-950 text-gray-100 font-mono text-xs px-2 py-0.5 rounded border border-white/10 focus:outline-none focus:border-blue-400 text-center"
              />
            </div>

            {/* Go Button to trigger camera pan and pipeline */}
            <button
              type="submit"
              className="bg-blue-600 hover:bg-blue-500 text-white px-2.5 py-1 rounded text-xs font-semibold flex items-center gap-1 transition-colors font-mono shadow-md"
              title="Pan marker to edited coordinates and run telemetry"
            >
              Go <ArrowRight className="w-3 h-3" />
            </button>
          </form>
        </div>
      </header>

      {/* Pipeline Error Banner */}
      {error && (
        <div className="fixed top-28 left-1/2 -translate-x-1/2 z-[4500] max-w-lg w-full glass-panel p-3 bg-red-950/90 border border-red-500/40 text-red-200 text-xs flex items-center gap-3 shadow-2xl">
          <AlertCircle className="w-4 h-4 text-red-400 flex-shrink-0" />
          <div className="flex-1">
            <p className="font-bold">Pipeline Error</p>
            <p className="text-[11px] text-red-300">{error}</p>
          </div>
          <button
            onClick={() => runPipeline(selectedLocation)}
            className="px-2.5 py-1 bg-red-800 hover:bg-red-700 text-white rounded text-[11px]"
          >
            Retry
          </button>
        </div>
      )}

      {/* 2. FULL-BLEED BACKGROUND INTERACTIVE GOOGLE MAP */}
      <div className="absolute inset-0 pt-20">
        <GoogleMapView
          selectedLocation={selectedLocation}
          onSelectLocation={handleLocationSelect}
          loadingStep={loadingStep}
        />
      </div>

      {/* 3. ALWAYS ACTIVE DEDICATED RIGHT SIDEBAR (DISPLAYING SELECTED LOCATION DATA) */}
      {activeTab === 'verification' && (
        <aside className="fixed top-24 right-0 bottom-0 w-full sm:w-96 md:w-[420px] z-[3000] bg-slate-950/90 backdrop-blur-2xl border-l border-white/10 p-4 overflow-y-auto space-y-4 shadow-2xl scrollbar-thin">
          {/* Active Location Info Card */}
          <div className="glass-panel p-3.5 border border-white/10 space-y-1 bg-gradient-to-r from-slate-900 to-blue-950/40">
            <div className="flex items-center justify-between">
              <span className="text-[10px] uppercase font-mono font-bold text-blue-400 flex items-center gap-1">
                <MapPin className="w-3.5 h-3.5 text-blue-400" /> Target Grid Telemetry
              </span>
              <span className="text-[10px] font-mono text-gray-400 bg-slate-900 px-2 py-0.5 rounded border border-white/10">
                {selectedLocation.lat.toFixed(4)}, {selectedLocation.lon.toFixed(4)}
              </span>
            </div>
            <h2 className="text-base font-bold text-white tracking-tight">{locationName}</h2>
          </div>

          {/* Section 1: Centerpiece Guardrail Verification Badge */}
          <VerificationBadge
            verification={explainData?.verification || null}
            loading={loadingStep !== 'idle'}
          />

          {/* Section 2: Satellite Risk Telemetry (GET /api/risk indicators) */}
          <RiskPanel
            data={riskData}
            loading={loadingStep === 'risk'}
          />

          {/* Section 3: Gemma 4 Verified Explanation & AWS Water Recommendation */}
          <RecommendationCard
            explanationData={explainData}
            loading={loadingStep !== 'idle'}
          />
        </aside>
      )}

      {/* Compare Panel Overlay (Tab 2) */}
      {activeTab === 'compare' && (
        <div className="fixed inset-0 z-[4000] bg-slate-950/80 backdrop-blur-md flex items-center justify-center p-6 pt-24">
          <div className="max-w-2xl w-full">
            <div className="flex justify-end mb-2">
              <button
                onClick={() => setActiveTab('verification')}
                className="text-xs text-gray-400 hover:text-white px-2 py-1 font-mono"
              >
                Close ✕
              </button>
            </div>
            <ComparePanel />
          </div>
        </div>
      )}

      {/* API Contracts Documentation Overlay (Tab 3) */}
      {activeTab === 'contracts' && (
        <div className="fixed inset-0 z-[4000] bg-slate-950/85 backdrop-blur-md flex items-center justify-center p-6 pt-24 overflow-y-auto">
          <div className="max-w-4xl w-full glass-panel p-6 space-y-4 my-8">
            <div className="flex items-center justify-between border-b border-white/10 pb-3">
              <div className="flex items-center gap-2">
                <Code className="w-5 h-5 text-blue-400" />
                <h2 className="text-base font-bold text-gray-100">API Contracts Specification</h2>
              </div>
              <button
                onClick={() => setActiveTab('verification')}
                className="text-xs text-gray-400 hover:text-white px-2 py-1 font-mono"
              >
                Close ✕
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="p-4 rounded-xl bg-slate-950 border border-white/10 space-y-2">
                <span className="text-xs font-mono font-bold text-emerald-400 px-2 py-0.5 rounded bg-emerald-950 border border-emerald-500/30">
                  GET /api/risk
                </span>
                <p className="text-xs text-gray-400">Request: <code className="text-gray-200">lat: float, lon: float</code></p>
                <pre className="text-[11px] font-mono bg-slate-900 p-3 rounded text-blue-300 overflow-x-auto">
{`{
  "location": { "lat": 12.9716, "lon": 80.2437 },
  "indicators": {
    "surface_water_trend": { "value": -12.4, "unit": "% change 10yr", "source": "GEE/JRC-GSW", "confidence": "measured" },
    "flood_exposure": { "value": "moderate", "source": "GEE/flood-layer", "confidence": "measured" },
    "rainfall_proxy": { "value": null, "source": null, "confidence": "no_data" }
  },
  "computed_at": "2026-07-30T13:30:00Z"
}`}
                </pre>
              </div>

              <div className="p-4 rounded-xl bg-slate-950 border border-white/10 space-y-2">
                <span className="text-xs font-mono font-bold text-blue-400 px-2 py-0.5 rounded bg-blue-950 border border-blue-500/30">
                  POST /api/explain
                </span>
                <p className="text-xs text-gray-400">Payload: <code className="text-gray-200">{'indicators: { ...from /api/risk... }'}</code></p>
                <pre className="text-[11px] font-mono bg-slate-900 p-3 rounded text-blue-300 overflow-x-auto">
{`{
  "explanation": "Plain English referencing given indicators",
  "recommendation": {
    "text": "Actionable site stewardship advice",
    "source_doc": "AWS Water Stewardship Standard",
    "source_excerpt": "Verbatim excerpt <300 chars",
    "section": "Section 1.3"
  },
  "verification": {
    "claims_checked": 5,
    "claims_grounded": 4,
    "claims_rejected": 1,
    "trust_score": 0.8,
    "rejected_claims": [
      { "id": "rej-1", "claim": "Aquifer recharged by +35%", "reason": "Unverifiable — groundwater metric missing" }
    ]
  }
}`}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
export default App;
