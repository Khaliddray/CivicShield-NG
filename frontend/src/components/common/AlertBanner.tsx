import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  ChevronRight,
  X,
  Volume2,
  VolumeX,
  Radio,
  FileCheck2,
} from 'lucide-react';
import api from '../../api/client';
import { Alert } from '../../types';
import { useAccessibility } from '../../context/AccessibilityContext';

export const AlertBanner: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isExpanded, setIsExpanded] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const { speak, stopSpeaking, isSpeaking, t, language } = useAccessibility();

  useEffect(() => {
    const fetchActiveAlerts = async () => {
      try {
        const res = await api.get('/alerts/active?limit=5');
        if (res.data?.data && res.data.data.length > 0) {
          setAlerts(res.data.data);
        }
      } catch (err) {
        console.error('Failed to load active early warnings:', err);
      }
    };

    fetchActiveAlerts();
    const interval = setInterval(fetchActiveAlerts, 30000); // 30s auto-refresh
    return () => clearInterval(interval);
  }, []);

  if (dismissed || alerts.length === 0) {
    return null;
  }

  const current = alerts[currentIndex];
  const isCritical = current.severity === 'CRITICAL';

  const handleReadAloud = () => {
    if (isSpeaking) {
      stopSpeaking();
    } else {
      const speechText = `${current.severity} Early Warning: ${current.title}. Summary: ${current.summary}. Official clarification: ${current.full_clarification}`;
      speak(speechText);
    }
  };

  return (
    <div
      role="alert"
      aria-live="assertive"
      aria-label="Electoral early warning notice"
      className={`relative border-b transition-colors shadow-lg z-30 ${
        isCritical
          ? 'bg-rose-950/95 border-rose-800 text-rose-100'
          : 'bg-amber-950/95 border-amber-800 text-amber-100'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-2.5">
        <div className="flex items-center justify-between gap-3 text-xs sm:text-sm">
          {/* Severity Icon & Headline */}
          <div className="flex items-center space-x-2.5 min-w-0">
            <span
              className={`flex-shrink-0 p-1.5 rounded-lg shadow-sm ${
                isCritical ? 'bg-rose-600 text-white animate-pulse' : 'bg-amber-600 text-white'
              }`}
            >
              <AlertTriangle className="w-4 h-4" />
            </span>
            <div className="flex items-center space-x-2 min-w-0">
              <span className="font-bold tracking-wider uppercase text-[10px] px-2 py-0.5 rounded-full bg-black/50 border border-white/20 whitespace-nowrap">
                {current.severity} • {current.target_scope === 'STATE_SPECIFIC' ? (current.target_states?.join(', ') || current.target_state || 'STATE') : 'NATIONAL'}
              </span>
              <span className="font-bold truncate text-white">{current.title}</span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center space-x-2 flex-shrink-0">
            {/* Read Aloud Text-to-Speech Button */}
            <button
              onClick={handleReadAloud}
              className={`p-1.5 rounded-lg border transition-all flex items-center space-x-1 text-xs ${
                isSpeaking
                  ? 'bg-emerald-600 border-emerald-400 text-white animate-pulse'
                  : 'bg-black/40 border-white/20 hover:bg-black/60 text-white/90'
              }`}
              title={isSpeaking ? t('voice_stop_reading', 'Stop audio') : t('voice_read_aloud', 'Read aloud')}
              aria-label={isSpeaking ? 'Stop speaking alert' : 'Read alert aloud using text to speech'}
            >
              {isSpeaking ? <VolumeX className="w-3.5 h-3.5" /> : <Volume2 className="w-3.5 h-3.5" />}
              <span className="hidden md:inline text-[11px] font-semibold">
                {isSpeaking ? 'Stop' : 'Listen'}
              </span>
            </button>

            {/* Pagination if multiple alerts */}
            {alerts.length > 1 && (
              <span className="text-[11px] text-white/70 hidden sm:inline">
                {currentIndex + 1}/{alerts.length}
              </span>
            )}

            {/* Expand Clarification Details */}
            <button
              onClick={() => setIsExpanded(!isExpanded)}
              className="px-2.5 py-1 rounded-lg bg-black/40 hover:bg-black/60 border border-white/20 text-xs font-semibold transition-colors flex items-center space-x-1"
              aria-expanded={isExpanded}
            >
              <span>{isExpanded ? t('alerts_hide_details', 'Hide Details') : t('alerts_view_clarification', 'View Clarification')}</span>
              <ChevronRight
                className={`w-3.5 h-3.5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
              />
            </button>

            {/* Next Alert */}
            {alerts.length > 1 && (
              <button
                onClick={() => setCurrentIndex((prev) => (prev + 1) % alerts.length)}
                className="px-2 py-1 rounded-lg bg-black/40 hover:bg-black/60 border border-white/20 text-xs"
                title="Next alert"
                aria-label="View next alert"
              >
                &rarr;
              </button>
            )}

            {/* Dismiss Banner */}
            <button
              onClick={() => setDismissed(true)}
              className="p-1 rounded-lg hover:bg-white/10 text-white/70 hover:text-white transition-colors"
              title="Dismiss banner"
              aria-label="Dismiss alert banner"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Collapsible Clarification Panel */}
        {isExpanded && (
          <div className="mt-3 pt-3 border-t border-white/15 grid grid-cols-1 md:grid-cols-2 gap-4 text-xs animate-fadeIn">
            <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 space-y-1">
              <span className="font-bold text-rose-300 block">
                {language === 'pcm' ? 'Fake News / Claim Wey Dem Debunk:' : 'Debunked Misinformation Claim:'}
              </span>
              <p className="text-white/90 italic leading-relaxed">
                "{current.debunked_claim_text || current.summary}"
              </p>
              <div className="mt-2 text-[10px] font-mono text-white/60">
                Official Reference: <strong>{current.alert_reference}</strong>
              </div>
            </div>

            <div className="p-3.5 rounded-xl bg-black/40 border border-white/10 space-y-1">
              <div className="flex items-center space-x-1.5 text-emerald-300 font-bold">
                <FileCheck2 className="w-4 h-4" />
                <span>{language === 'pcm' ? 'Official Clarification & Evidence:' : 'Official Clarification & Certified Evidence:'}</span>
              </div>
              <p className="text-white/90 leading-relaxed whitespace-pre-line">
                {current.full_clarification}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
