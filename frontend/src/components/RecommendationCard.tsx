import React, { useState } from 'react';
import type { ExplainResponse } from '../types/api';
import { BookOpen, Sparkles, Compass, ChevronDown, ChevronUp } from 'lucide-react';

interface RecommendationCardProps {
  explanationData: ExplainResponse | null;
  loading: boolean;
}

export const RecommendationCard: React.FC<RecommendationCardProps> = ({ explanationData, loading }) => {
  const [isCollapsed, setIsCollapsed] = useState(false);

  if (loading) {
    return (
      <div className="glass-panel p-4 border border-white/10 animate-pulse space-y-2">
        <div className="h-4 bg-slate-800 rounded w-1/2 mb-2"></div>
        <div className="h-10 bg-slate-800/60 rounded"></div>
      </div>
    );
  }

  if (!explanationData) return null;

  const { explanation, recommendation } = explanationData;

  return (
    <div className="glass-panel p-4 space-y-3 border border-white/10 shadow-xl">
      {/* Panel Header */}
      <div className="flex items-center justify-between border-b border-white/10 pb-2">
        <div className="flex items-center gap-2 text-blue-400">
          <Sparkles className="w-4 h-4 text-blue-400" />
          <h3 className="text-xs font-bold uppercase tracking-wider font-mono text-gray-200">
            Gemma 4 Verified Explanation
          </h3>
        </div>

        <button
          onClick={() => setIsCollapsed(!isCollapsed)}
          className="p-1 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors"
          title={isCollapsed ? 'Expand explanation' : 'Collapse explanation'}
        >
          {isCollapsed ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
        </button>
      </div>

      {!isCollapsed && (
        <div className="space-y-3 text-xs">
          <p className="text-gray-200 leading-relaxed font-sans">
            {explanation}
          </p>

          {/* AWS Water Stewardship Recommendation */}
          <div className="p-3 rounded-xl bg-slate-900/80 border border-blue-500/20 space-y-2">
            <div className="flex items-center justify-between border-b border-white/5 pb-1">
              <span className="font-semibold text-blue-400 flex items-center gap-1">
                <Compass className="w-3.5 h-3.5" /> Stewardship Action
              </span>
              <span className="text-[9px] font-mono px-1.5 py-0.5 rounded bg-blue-500/20 text-blue-300">
                {recommendation.section}
              </span>
            </div>

            <p className="text-gray-100 font-medium">{recommendation.text}</p>

            <div className="pt-1 text-[10px] text-gray-400 space-y-1">
              <div className="flex items-center gap-1 font-mono text-gray-300">
                <BookOpen className="w-3 h-3 text-blue-400" />
                <span>{recommendation.source_doc}</span>
              </div>
              <blockquote className="italic text-gray-300 pl-2.5 border-l-2 border-blue-400/60 font-serif">
                "{recommendation.source_excerpt}"
              </blockquote>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
