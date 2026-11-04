import React, { useState, useEffect } from 'react';
import { AlertTriangle, ShieldAlert, ChevronRight, X, ExternalLink, Info } from 'lucide-react';
import api from '../../api/client';
import { Alert } from '../../types';

export const AlertBanner: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    const fetchActiveAlerts = async () => {
      try {
        const res = await api.get('/alerts/feed/active?limit=5');
        if (res.data?.data && res.data.data.length > 0) {
          setAlerts(res.data.data);
        }
      } catch (err) {
        console.error('Failed to load active early warnings:', err);
      }
    };

    fetchActiveAlerts();
    const interval = setInterval(fetchActiveAlerts, 60000); // 1-minute auto-refresh
    return () => clearInterval(interval);
  }, []);

  if (dismissed || alerts.length === 0) {
    return null;
  }

  const current = alerts[currentIndex];
  const isCritical = current.severity === 'CRITICAL';

  return (
    <div
      className={`relative border-b transition-colors ${
        isCritical
          ? 'bg-rose-950/90 border-rose-800 text-rose-100'
          : 'bg-amber-950/80 border-amber-800 text-amber-100'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5">
        <div className="flex items-center justify-between gap-3 text-xs sm:text-sm">
          {/* Severity Icon & Badge */}
          <div className="flex items-center space-x-2.5 min-w-0">
            <span
              className={`flex-shrink-0 p-1.5 rounded-md ${
                isCritical ? 'bg-rose-600 text-white animate-pulse' : 'bg-amber-600 text-white'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
            </span>
            <div className="flex items-center space-x-2 min-w-0">
              <span className="font-bold tracking-wide uppercase text-[11px] px-2 py-0.5 rounded bg-black/40 border border-white/10">
                {current.severity} ALERT ({current.target_scope === 'STATE_SPECIFIC' ? current.target_state : 'NATIONAL'})
              </span>
              <span className="font-semibold truncate">{current.title}</span>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            {alerts.length > 1 && (
              <span className="text-[11px] text-white/70">
                {currentIndex + 1} of {alerts.length}
              </span>
            )}

            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-2.5 py-1 rounded bg-white/10 hover:bg-white/20 text-xs font-medium transition-colors flex items-center space-x-1"
            >
              <span>{isExpanded ? 'Hide Details' : 'View Clarification'}</span>
              <ChevronRight
                className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              />
            </button>

            {alerts.length > 1 && (
              <button
                onClick={() => setCurrentIndex((prev) => (prev + 1) % alerts.length)}
                className="px-2 py-1 rounded bg-white/10 hover:bg-white/20 text-xs"
                title="Next alert"
              >
                &rarr;
              </button>
            )}

            <button
              onClick={() => setDismissed(true)}
              className="p-1 rounded hover:bg-white/10 text-white/70 hover:text-white"
              title="Dismiss for this session"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Collapsible Clarification Panel */}
        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-white/15 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3 rounded-lg bg-black/30 border border-white/10">
              <span className="font-bold text-rose-300 block mb-1">Debunked Misinformation Claim:</span>
              <p className="text-white/90 italic">"{current.debunked_claim_text || current.summary}"</p>
              <div className="mt-2 text-[10px] text-white/60">
                Reference ID: <span className="font-mono">{current.alert_reference}</span>
              </div>
            </div>

            <div className="p-3 rounded-lg bg-black/30 border border-white/10">
              <span className="font-bold text-emerald-300 block mb-1">Official Clarification &amp; Evidence:</span>
              <p className="text-white/90 whitespace-pre-line">{current.full_clarification}</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
