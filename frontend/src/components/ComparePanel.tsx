import React from 'react';
import { ArrowRightLeft, Sparkles, ShieldCheck } from 'lucide-react';
import { PRESET_LOCATIONS } from '../api/mockData';

export const ComparePanel: React.FC = () => {
  return (
    <div className="glass-panel p-6 space-y-5 border border-cyan-500/20">
      <div className="flex items-center justify-between border-b border-white/10 pb-3">
        <div className="flex items-center gap-2">
          <ArrowRightLeft className="w-5 h-5 text-cyan-400" />
          <h2 className="text-base font-semibold text-gray-100">Multi-Location Telemetry Compare</h2>
        </div>
        <span className="text-xs font-mono font-bold text-amber-400 px-2 py-0.5 rounded bg-amber-500/20 border border-amber-500/30">
          P1 Stub Feature
        </span>
      </div>

      <p className="text-sm text-gray-300">
        Compare water-risk telemetry indicators and Gemma 4 guardrail trust scores side-by-side across major agricultural and urban basins.
      </p>

      {/* Grid mockup preview */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 opacity-75">
        {PRESET_LOCATIONS.slice(0, 2).map((loc) => (
          <div key={loc.id} className="p-4 rounded-xl bg-gray-900/60 border border-white/10 space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-sm text-cyan-300">{loc.name}</span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-gray-800 text-gray-400">{loc.region}</span>
            </div>
            <p className="text-xs text-gray-400">{loc.description}</p>
            <div className="pt-2 flex items-center justify-between text-xs border-t border-white/5">
              <span className="text-gray-400 flex items-center gap-1">
                <ShieldCheck className="w-3 h-3 text-emerald-400" /> Verification Status
              </span>
              <span className="font-mono text-cyan-400">Ready for comparison</span>
            </div>
          </div>
        ))}
      </div>

      <div className="p-4 rounded-lg bg-cyan-950/30 border border-cyan-500/30 text-center space-y-2">
        <Sparkles className="w-5 h-5 text-cyan-400 mx-auto" />
        <p className="text-xs text-cyan-300 font-mono">
          Multi-basin comparison telemetry model queued for P1 Hackathon release.
        </p>
      </div>
    </div>
  );
};
