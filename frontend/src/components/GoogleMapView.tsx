import React, { useState, useEffect, useRef, useCallback } from 'react';
import { APIProvider, Map, Marker, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import { DARK_WATER_MAP_STYLE } from '../utils/mapStyles';
import { PRESET_LOCATIONS } from '../api/mockData';
import { Search, AlertTriangle, Key, Compass } from 'lucide-react';

interface GoogleMapViewProps {
  selectedLocation: { lat: number; lon: number };
  onSelectLocation: (location: { lat: number; lon: number }, placeName?: string) => void;
  loadingStep: 'idle' | 'risk' | 'explain';
}

// Inner component for Places Autocomplete input
export const PlacesAutocompleteInput: React.FC<{
  onPlaceSelect: (lat: number, lon: number, name: string) => void;
}> = ({ onPlaceSelect }) => {
  const placesLib = useMapsLibrary('places');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!placesLib || !inputRef.current) return;

    const auto = new placesLib.Autocomplete(inputRef.current, {
      fields: ['geometry', 'formatted_address', 'name']
    });

    auto.addListener('place_changed', () => {
      const place = auto.getPlace();
      if (place.geometry?.location) {
        const lat = place.geometry.location.lat();
        const lon = place.geometry.location.lng();
        const name = place.name || place.formatted_address || 'Selected Location';
        onPlaceSelect(lat, lon, name);
      }
    });
  }, [placesLib, onPlaceSelect]);

  return (
    <div className="relative flex-1">
      <Search className="w-4 h-4 text-blue-400 absolute left-3 top-1/2 -translate-y-1/2" />
      <input
        ref={inputRef}
        type="text"
        placeholder="Search location or river basin (Places API)..."
        className="w-full bg-slate-900/90 text-gray-100 pl-9 pr-4 py-1.5 rounded-xl border border-white/10 text-xs font-sans focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500/50 shadow-md backdrop-blur-md"
      />
    </div>
  );
};

// Camera Controller component: smoothly pans to new location without locking camera gestures
const MapCameraController: React.FC<{ center: { lat: number; lng: number } }> = ({ center }) => {
  const map = useMap();

  useEffect(() => {
    if (map) {
      map.panTo(center);
    }
  }, [map, center.lat, center.lng]);

  return null;
};

// Map click event listener component
const MapClickListener: React.FC<{
  onMapClick: (lat: number, lon: number) => void;
}> = ({ onMapClick }) => {
  const map = useMap();

  useEffect(() => {
    if (!map) return;

    const listener = map.addListener('click', (e: google.maps.MapMouseEvent) => {
      if (e.latLng) {
        onMapClick(e.latLng.lat(), e.latLng.lng());
      }
    });

    return () => {
      google.maps.event.removeListener(listener);
    };
  }, [map, onMapClick]);

  return null;
};

// Main Map View Wrapper
export const GoogleMapView: React.FC<GoogleMapViewProps> = ({
  selectedLocation,
  onSelectLocation,
  loadingStep
}) => {
  // Read API Key from Vite env
  const apiKey = import.meta.env.VITE_GOOGLE_MAPS_API_KEY || '';
  const [manualKey, setManualKey] = useState('');
  const activeKey = manualKey || apiKey;

  // Handle map click
  const handleMapClick = useCallback(
    (lat: number, lon: number) => {
      onSelectLocation({ lat, lon });
    },
    [onSelectLocation]
  );

  return (
    <div className="relative w-full h-full min-h-screen">
      {/* Full-Bleed Google Maps Provider */}
      {activeKey ? (
        <APIProvider apiKey={activeKey} libraries={['places', 'geocoding']}>
          <Map
            style={{ width: '100vw', height: '100vh' }}
            defaultCenter={{ lat: selectedLocation.lat, lng: selectedLocation.lon }}
            defaultZoom={7}
            gestureHandling="greedy"
            styles={DARK_WATER_MAP_STYLE}
            disableDefaultUI={false}
            zoomControl={true}
            mapTypeControl={false}
            streetViewControl={false}
            fullscreenControl={false}
          >
            <MapCameraController center={{ lat: selectedLocation.lat, lng: selectedLocation.lon }} />
            <MapClickListener onMapClick={handleMapClick} />
            <Marker
              position={{ lat: selectedLocation.lat, lng: selectedLocation.lon }}
              title="Target Telemetry Grid"
            />
          </Map>
        </APIProvider>
      ) : (
        /* Graceful fallback if VITE_GOOGLE_MAPS_API_KEY is missing */
        <div className="absolute inset-0 bg-[#090d16] flex flex-col items-center justify-center p-6 text-center z-10">
          <div className="max-w-md w-full glass-panel p-6 space-y-4 border border-blue-500/30 text-left">
            <div className="flex items-center gap-3 text-amber-400">
              <AlertTriangle className="w-6 h-6 flex-shrink-0" />
              <div>
                <h3 className="font-bold text-gray-100">Google Maps API Key Required</h3>
                <p className="text-xs text-gray-400">VITE_GOOGLE_MAPS_API_KEY environment variable is not set.</p>
              </div>
            </div>

            <p className="text-xs text-gray-300 leading-relaxed">
              To view the live full-bleed Google Map, add your key to <code className="text-blue-400 font-mono">.env</code> as <code className="text-blue-400 font-mono">VITE_GOOGLE_MAPS_API_KEY</code> or input it below for immediate testing:
            </p>

            <div className="flex items-center gap-2">
              <Key className="w-4 h-4 text-blue-400" />
              <input
                type="text"
                placeholder="Paste AIzaSy... API key"
                value={manualKey}
                onChange={(e) => setManualKey(e.target.value)}
                className="flex-1 bg-slate-950 text-gray-100 px-3 py-1.5 rounded text-xs border border-white/10 font-mono focus:outline-none focus:border-blue-400"
              />
            </div>

            {/* Interactive Fallback Grid selector so mock demo functions seamlessly */}
            <div className="pt-2 border-t border-white/10 space-y-2">
              <p className="text-xs text-gray-400 font-semibold flex items-center gap-1">
                <Compass className="w-3.5 h-3.5 text-blue-400" /> Or select a telemetry preset location to run pipeline:
              </p>
              <div className="grid grid-cols-2 gap-2">
                {PRESET_LOCATIONS.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => onSelectLocation({ lat: preset.lat, lon: preset.lon }, preset.name)}
                    className="p-2 rounded bg-slate-900 hover:bg-slate-800 text-xs text-left border border-white/10 text-gray-200"
                  >
                    <div className="font-semibold text-blue-400">{preset.name}</div>
                    <div className="text-[10px] text-gray-500 font-mono">{preset.lat}, {preset.lon}</div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Loading Overlay when pipeline executes */}
      {loadingStep !== 'idle' && (
        <div className="fixed inset-0 z-[4000] bg-slate-950/70 backdrop-blur-sm flex flex-col items-center justify-center gap-3">
          <div className="w-12 h-12 rounded-full border-4 border-blue-500/20 border-t-blue-500 animate-spin"></div>
          <div className="text-center space-y-1">
            <p className="text-sm font-semibold text-blue-400 font-mono">
              {loadingStep === 'risk'
                ? 'Fetching Satellite Telemetry (GET /api/risk)...'
                : 'Executing Gemma 4 Guardrail Verifier (POST /api/explain)...'}
            </p>
            <p className="text-xs text-gray-400">Verifying AI claims against GEE source data</p>
          </div>
        </div>
      )}
    </div>
  );
};
