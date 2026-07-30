import React, { useState } from 'react';
import type { VerificationData } from '../types/api';
import { ShieldCheck, ShieldAlert, AlertOctagon, CheckCircle, XCircle, ChevronDown, ChevronUp } from 'lucide-react';

interface VerificationBadgeProps {
  verification: VerificationData | null;
  loading: boolean;
}

export const VerificationBadge: React.FC<VerificationBadgeProps> = ({ verification, loading }) => {
  const [isExpanded, setIsExpanded] = useState(true);

  if (loading) {
    return (
      <div className="glass-panel p-4 border border-blue-500/40 shadow-xl flex items-center gap-3 animate-pulse">
        <div className="w-10 h-10 rounded-full border-2 border-blue-500/40 border-t-blue-400 animate-spin"></div>
        <div>
          <p className="text-xs font-bold text-blue-400 font-mono">Gemma 4 Verifier Active</p>
          <p className="text-[10px] text-gray-400">Verifying LLM claims against telemetry...</p>
        </div>
      </div>
    );
  }

  if (!verification) return null;

  const trustPercent = Math.round(verification.trust_score * 100);
  const isLowTrust = verification.trust_score < 0.6;

  // Clean 2-color interpolation: Blue accent (#3b82f6) near 1.0 -> Red (#ef4444) near 0.0
  const ringColor = isLowTrust
    ? `rgb(${Math.round(239 + (59 - 239) * verification.trust_score)}, ${Math.round(68 + (130 - 68) * verification.trust_score)}, ${Math.round(68 + (246 - 68) * verification.trust_score)})`
    : '#3b82f6';

  return (
    <div className="glass-panel border border-white/10 shadow-xl transition-all overflow-hidden">
      {/* Compact Badge Ring Header */}
      <div
        onClick={() => setIsExpanded(!isExpanded)}
        className="p-3.5 flex items-center justify-between cursor-pointer hover:bg-white/5 transition-colors"
      >
        <div className="flex items-center gap-3">
          {/* SVG Circular Gauge with Glow Pulse when trust_score < 0.6 */}
          <div className={`relative w-12 h-12 flex items-center justify-center ${isLowTrust ? 'animate-pulse' : ''}`}>
            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
              <path
                className="text-slate-800"
                strokeWidth="3.5"
                stroke="currentColor"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
              <path
                strokeWidth="3.5"
                strokeDasharray={`${trustPercent}, 100`}
                stroke={isLowTrust ? '#ef4444' : ringColor}
                strokeLinecap="round"
                fill="none"
                d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"
              />
            </svg>
            <span className="absolute font-mono text-xs font-extrabold text-gray-100">{trustPercent}%</span>
          </div>

          <div>
            <div className="flex items-center gap-1.5">
              <h3 className="text-xs font-bold text-gray-100 flex items-center gap-1">
                {isLowTrust ? (
                  <ShieldAlert className="w-3.5 h-3.5 text-red-400" />
                ) : (
                  <ShieldCheck className="w-3.5 h-3.5 text-blue-400" />
                )}
                Gemma 4 Guardrail Verifier
              </h3>
            </div>
            <p className="text-[10px] text-gray-400 mt-0.5">
              {verification.claims_rejected > 0
                ? `${verification.claims_rejected} ungrounded claim stripped`
                : '100% telemetry grounded'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-1.5">
          {verification.claims_rejected > 0 && (
            <span className="tag-removed-unverifiable text-[9px] px-1.5 py-0.5">
              {verification.claims_rejected} REJECTED
            </span>
          )}
          {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-400" /> : <ChevronDown className="w-4 h-4 text-gray-400" />}
        </div>
      </div>

      {/* Expanded Claims & Rejection Details */}
      {isExpanded && (
        <div className="p-3.5 border-t border-white/10 space-y-3">
          {/* Claims Stats Grid */}
          <div className="grid grid-cols-3 gap-2 text-center text-xs font-mono">
            <div className="p-2 rounded bg-slate-900/80 border border-white/5">
              <span className="text-[9px] text-gray-400 block">Checked</span>
              <span className="font-bold text-gray-200">{verification.claims_checked}</span>
            </div>
            <div className="p-2 rounded bg-slate-900/80 border border-blue-500/20">
              <span className="text-[9px] text-blue-400 block">Grounded</span>
              <span className="font-bold text-blue-300">{verification.claims_grounded}</span>
            </div>
            <div className="p-2 rounded bg-red-950/40 border border-red-500/30">
              <span className="text-[9px] text-red-400 block">Rejected</span>
              <span className="font-bold text-red-300">{verification.claims_rejected}</span>
            </div>
          </div>

          {/* Rejected Claims Strikethrough List */}
          {verification.rejected_claims && verification.rejected_claims.length > 0 ? (
            <div className="space-y-2 pt-1">
              <span className="text-xs font-bold text-red-400 flex items-center gap-1">
                <AlertOctagon className="w-3.5 h-3.5" /> Stripped Unverifiable Claims:
              </span>
              {verification.rejected_claims.map((item) => (
                <div key={item.id} className="claim-rejected-item p-2.5">
                  <div className="flex items-center justify-between mb-1">
                    <span className="tag-removed-unverifiable text-[9px]">
                      <XCircle className="w-3 h-3" /> removed — unverifiable
                    </span>
                  </div>
                  <p className="claim-rejected-text text-xs">"{item.claim}"</p>
                  <p className="text-[10px] text-red-300/80 mt-1 font-mono">{item.reason}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-2.5 rounded bg-blue-950/30 border border-blue-500/20 text-xs text-blue-300 flex items-center gap-2">
              <CheckCircle className="w-4 h-4 text-blue-400 flex-shrink-0" />
              <span>All AI claims strictly grounded in satellite source indicators.</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
