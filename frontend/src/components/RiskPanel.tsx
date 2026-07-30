import React from 'react';
import type { RiskResponse, Indicator } from '../types/api';
import { Database, CheckCircle2, Info } from 'lucide-react';

interface RiskPanelProps {
  data: RiskResponse | null;
  loading: boolean;
}

export const RiskPanel: React.FC<RiskPanelProps> = ({ data, loading }) => {
  if (loading) {
    return (
      <div className="glass-panel p-4 border border-white/10 animate-pulse space-y-2">
        <div className="flex items-center gap-2 mb-2">
          <Database className="w-4 h-4 text-blue-400" />
          <span className="text-xs font-semibold text-gray-200">GET /api/risk Telemetry</span>
        </div>
        <div className="h-10 bg-slate-800/60 rounded-xl"></div>
        <div className="h-10 bg-slate-800/60 rounded-xl"></div>
      </div>
    );
  }

  if (!data) return null;

  const indicators = data.indicators;
  const indicatorKeys = Object.keys(indicators);

  const formatIndicatorTitle = (key: string) => {
    return key
      .replace(/_/g, ' ')
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const renderIndicatorState = (key: string, indicator?: Indicator) => {
    if (!indicator || indicator.confidence === 'no_data' || indicator.value === null) {
      return (
        <div
          key={key}
          className="p-3 rounded-xl border border-dashed border-gray-600/60 bg-slate-950/40 text-gray-500 flex items-center justify-between transition-all"
        >
          <div>
            <div className="flex items-center gap-1.5">
              <span className="text-xs font-semibold text-gray-400">{formatIndicatorTitle(key)}</span>
              <span className="text-[9px] font-mono font-bold px-1.5 py-0.5 rounded bg-gray-800 text-gray-400 border border-gray-700">
                no_data
              </span>
            </div>
            <p className="text-[10px] text-gray-500 mt-0.5">Telemetry uncomputable for coordinate</p>
          </div>
          <span className="font-mono text-xs font-bold text-gray-500">NULL</span>
        </div>
      );
    }

    const isNumerical = typeof indicator.value === 'number';

    return (
      <div
        key={key}
        className="p-3 rounded-xl bg-slate-900/60 border border-white/10 flex items-center justify-between hover:border-blue-500/40 transition-all"
      >
        <div>
          <div className="flex items-center gap-1.5">
            <span className="text-xs font-semibold text-gray-200">{formatIndicatorTitle(key)}</span>
            <span className="text-[9px] font-mono font-semibold px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300 border border-blue-500/30 flex items-center gap-1">
              <CheckCircle2 className="w-2.5 h-2.5 text-blue-400" />
              {isNumerical ? 'measured' : 'qualitative'}
            </span>
          </div>
          <p className="text-[10px] text-gray-400 mt-0.5 flex items-center gap-1">
            <Info className="w-2.5 h-2.5 text-blue-400" />
            Source: <span className="font-mono text-gray-300">{indicator.source || 'GEE Telemetry'}</span>
          </p>
        </div>

        <div className="text-right">
          <span className="font-mono text-sm font-bold text-blue-400">
            {indicator.value}{' '}
            {indicator.unit ? <span className="text-[9px] font-normal text-gray-400">{indicator.unit}</span> : ''}
          </span>
        </div>
      </div>
    );
  };

  return (
    <div className="glass-panel p-4 space-y-3 border border-white/10 shadow-xl">
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-2">
          <Database className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-bold text-gray-100 uppercase tracking-wider font-mono">
            Satellite Risk Telemetry
          </h3>
        </div>
        <span className="text-[10px] font-mono text-gray-400">GET /api/risk</span>
      </div>

      <div className="text-[10px] text-gray-400 font-mono flex items-center justify-between px-1">
        <span>Target: {data.location.name || `${data.location.lat}, ${data.location.lon}`}</span>
        <span>{new Date(data.computed_at).toLocaleTimeString()}</span>
      </div>

      <div className="space-y-2">
        {indicatorKeys.map((key) => renderIndicatorState(key, indicators[key]))}
      </div>
    </div>
  );
};
