import React, { useEffect, useRef } from 'react';
import { Map, useMap, useMapsLibrary } from '@vis.gl/react-google-maps';
import { PRESET_LOCATIONS } from '../api/mockData';
import { Search, AlertTriangle, Key, Compass } from 'lucide-react';

interface GoogleMapViewProps {
  selectedLocation: { lat: number; lon: number };
  onSelectLocation: (location: { lat: number; lon: number }, placeName?: string) => void;
  loadingStep: 'idle' | 'risk' | 'explain';
  hasApiKey: boolean;
  manualKey: string;
  setManualKey: (key: string) => void;
}

// Places Autocomplete input component
export const PlacesAutocompleteInput: React.FC<{
  onPlaceSelect: (lat: number, lon: number, name: string) => void;
}> = ({ onPlaceSelect }) => {
  const placesLib = useMapsLibrary('places');
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!placesLib || !inputRef.current) return;

    const auto = new placesLib.Autocomplete(inputRef.current, {
      fields: ['geometry', 'formatted_address', 'name'],
    });

    const listener = auto.addListener('place_changed', () => {
      const place = auto.getPlace();
      if (place.geometry?.location) {
        const lat = place.geometry.location.lat();
        const lon = place.geometry.location.lng();
        const name = place.name || place.formatted_address || 'Selected Location';
        onPlaceSelect(lat, lon, name);
      }
    });

    return () => {
      if (listener) google.maps.event.removeListener(listener);
    };
  }, [placesLib, onPlaceSelect]);

  return (
    <div className="relative flex-1">
      <Search className="w-4 h-4 text-sky-500 absolute left-3 top-1/2 -translate-y-1/2" />
      <input
        ref={inputRef}
        type="text"
        placeholder="Search location or river basin..."
        className="w-full bg-white/60 text-slate-900 pl-9 pr-4 py-2 rounded-xl border border-sky-200 text-sm font-sans focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 shadow-sm backdrop-blur-md transition-all placeholder:text-slate-400"
      />
    </div>
  );
};

// Smoothly pans camera to the selected location without locking gestures.
const MapCameraController: React.FC<{ center: { lat: number; lng: number } }> = ({ center }) => {
  const map = useMap();
  useEffect(() => {
    if (map) map.panTo(center);
  }, [map, center.lat, center.lng]);
  return null;
};

// AdvancedMarkerElement wrapper.
// mapId="aquashield-map" (set on <Map>) is required for AdvancedMarkerElement to work.
const AdvancedMarker: React.FC<{ position: { lat: number; lng: number }; title?: string }> = ({
  position,
  title,
}) => {
  const map = useMap();
  const markerRef = useRef<google.maps.marker.AdvancedMarkerElement | null>(null);

  useEffect(() => {
    if (!map) return;
    let cancelled = false;

    (async () => {
      const { AdvancedMarkerElement } = (await google.maps.importLibrary(
        'marker'
      )) as google.maps.MarkerLibrary;

      if (cancelled) return;

      if (!markerRef.current) {
        markerRef.current = new AdvancedMarkerElement({
          map,
          position,
          title: title ?? 'Target Telemetry Grid',
        });
      } else {
        markerRef.current.position = position;
      }
    })();

    return () => {
      cancelled = true;
      if (markerRef.current) {
        markerRef.current.map = null;
        markerRef.current = null;
      }
    };
  }, [map]);

  useEffect(() => {
    if (markerRef.current) {
      markerRef.current.position = position;
    }
  }, [position.lat, position.lng]);

  return null;
};

// Main Map View
export const GoogleMapView: React.FC<GoogleMapViewProps> = ({
  selectedLocation,
  onSelectLocation,
  loadingStep,
  hasApiKey,
  manualKey,
  setManualKey,
}) => {
  return (
    <div className="relative w-full h-full">
      {hasApiKey ? (
        <Map
          style={{ width: '100%', height: '100%' }}
          defaultCenter={{ lat: selectedLocation.lat, lng: selectedLocation.lon }}
          defaultZoom={7}
          gestureHandling="greedy"
          disableDefaultUI={false}
          zoomControl={true}
          mapTypeControl={false}
          streetViewControl={false}
          fullscreenControl={false}
          mapId="aquashield-map"
          zoomControlOptions={{ position: 6 }}
          onClick={(e) => {
            if (e.detail.latLng) {
              onSelectLocation({ lat: e.detail.latLng.lat, lon: e.detail.latLng.lng });
            }
          }}
        >
          <MapCameraController center={{ lat: selectedLocation.lat, lng: selectedLocation.lon }} />
          <AdvancedMarker
            position={{ lat: selectedLocation.lat, lng: selectedLocation.lon }}
            title="Target Telemetry Grid"
          />
        </Map>
      ) : (
        <div className="absolute inset-0 bg-sky-50 flex flex-col items-center justify-center p-6 text-center z-10">
          <div className="max-w-md w-full glass-panel p-8 space-y-5 text-left">
            <div className="flex items-center gap-3 text-sky-600">
              <AlertTriangle className="w-8 h-8 flex-shrink-0 text-sky-500" />
              <div>
                <h3 className="font-bold text-slate-900 text-lg">Maps API Key Required</h3>
                <p className="text-sm text-slate-500">Live map requires a Google Maps key.</p>
              </div>
            </div>

            <p className="text-sm text-slate-600 leading-relaxed">
              Add{' '}
              <code className="text-sky-600 font-mono bg-sky-100 px-1.5 py-0.5 rounded">
                VITE_GOOGLE_MAPS_API_KEY
              </code>{' '}
              to your{' '}
              <code className="text-sky-600 font-mono bg-sky-100 px-1.5 py-0.5 rounded">.env</code>{' '}
              or input it below:
            </p>

            <div className="flex items-center gap-2">
              <Key className="w-5 h-5 text-sky-400" />
              <input
                type="text"
                placeholder="Paste AIzaSy... API key"
                value={manualKey}
                onChange={(e) => setManualKey(e.target.value)}
                className="flex-1 bg-white text-slate-900 px-4 py-2.5 rounded-xl text-sm border border-sky-200 font-mono focus:outline-none focus:border-sky-500 focus:ring-2 focus:ring-sky-500/20 transition-all shadow-sm"
              />
            </div>

            <div className="pt-4 border-t border-sky-100 space-y-3">
              <p className="text-sm text-slate-600 font-semibold flex items-center gap-1.5">
                <Compass className="w-4 h-4 text-sky-500" /> Or select a test basin:
              </p>
              <div className="grid grid-cols-2 gap-3">
                {PRESET_LOCATIONS.map((preset) => (
                  <button
                    key={preset.id}
                    onClick={() => onSelectLocation({ lat: preset.lat, lon: preset.lon }, preset.name)}
                    className="p-3 rounded-xl bg-white hover:bg-sky-50 text-sm text-left border border-sky-200 hover:border-sky-400 transition-all shadow-sm hover:shadow text-slate-800"
                  >
                    <div className="font-semibold text-sky-600">{preset.name}</div>
                    <div className="text-xs text-slate-400 font-mono mt-0.5">
                      {preset.lat}, {preset.lon}
                    </div>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {loadingStep !== 'idle' && (
        <div className="absolute inset-0 z-[2000] bg-white/60 backdrop-blur-[2px] flex flex-col items-center justify-center gap-4">
          <div className="w-14 h-14 rounded-full border-4 border-sky-200 border-t-sky-500 animate-spin shadow-lg" />
          <div className="text-center space-y-1.5 bg-white/80 px-6 py-3 rounded-2xl shadow-sm border border-sky-100">
            <p className="text-sm font-bold text-sky-600 font-mono tracking-tight">
              {loadingStep === 'risk'
                ? 'Fetching Telemetry (GET /api/risk)...'
                : 'Running Gemma 4 + Guardrail Verifier...'}
            </p>
            <p className="text-xs text-slate-500 font-medium">Verifying claims against source data</p>
          </div>
        </div>
      )}
    </div>
  );
};
