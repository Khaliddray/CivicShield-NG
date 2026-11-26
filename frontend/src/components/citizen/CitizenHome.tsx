import React, { useState, useEffect } from 'react';
import {
  ShieldAlert,
  Search,
  FileCheck2,
  UploadCloud,
  MessageSquare,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  HelpCircle,
  ArrowRight,
  Sparkles,
  Lock,
  FileText,
  Clock,
  Layers,
  Mic,
  MicOff,
  Volume2,
  VolumeX,
  Copy,
  Check,
  ExternalLink,
  Info,
  Shield,
  FileSearch,
  Filter,
} from 'lucide-react';
import api from '../../api/client';
import { Report, OfficialDocument, HashVerificationResult, ClaimAnalysisResult } from '../../types';
import { useAccessibility } from '../../context/AccessibilityContext';

const NIGERIAN_STATES = [
  'All Nigeria (National)', 'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
  'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Federal Capital Territory',
  'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara',
  'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers',
  'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
];

export const CitizenHome: React.FC = () => {
  const {
    t,
    language,
    speak,
    stopSpeaking,
    isSpeaking,
    startListening,
    stopListening,
    isListening,
    recognitionSupported,
  } = useAccessibility();

  const [activeTab, setActiveTab] = useState<'report' | 'track' | 'registry' | 'assistant'>('report');

  // Low-Bandwidth / Offline Caching State
  const [isOnline, setIsOnline] = useState<boolean>(typeof navigator !== 'undefined' ? navigator.onLine : true);
  const [offlineCount, setOfflineCount] = useState<number>(() => {
    try {
      const q = localStorage.getItem('civicshield_offline_queue');
      return q ? JSON.parse(q).length : 0;
    } catch {
      return 0;
    }
  });

  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true);
      syncOfflineReports();
    };
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  const syncOfflineReports = async () => {
    try {
      const raw = localStorage.getItem('civicshield_offline_queue');
      if (!raw) return;
      const queue: any[] = JSON.parse(raw);
      if (queue.length === 0) return;

      const remaining: any[] = [];
      for (const item of queue) {
        try {
          const formData = new FormData();
          if (item.title) formData.append('title', item.title);
          formData.append('content_text', item.content_text);
          formData.append('source_platform', item.source_platform);
          if (item.nigerian_state) formData.append('nigerian_state', item.nigerian_state);
          await api.post('/reports/submit', formData);
        } catch {
          remaining.push(item);
        }
      }
      localStorage.setItem('civicshield_offline_queue', JSON.stringify(remaining));
      setOfflineCount(remaining.length);
    } catch (err) {
      console.error('Error syncing offline queue:', err);
    }
  };

  const loadDemoScenario = (scenario: 'kano_postpone' | 'bvas_failure' | 'inec_query') => {
    if (scenario === 'kano_postpone') {
      setActiveTab('report');
      setReportTitle('Viral audio claiming voting postponed across Kano State');
      setReportContent('BREAKING: An audio note forwarded on WhatsApp claims that all voting centers across Kano State will be shut down until next Monday due to logistics delay.');
      setSourcePlatform('WHATSAPP');
      setSelectedState('Kano');
    } else if (scenario === 'bvas_failure') {
      setActiveTab('report');
      setReportTitle('Disinformation circular: BVAS machines cancelled in Ward 7');
      setReportContent('Viral letter alleging that INEC has suspended the use of BVAS accreditation devices for all polling units in Ward 7 and manual voting will commence.');
      setSourcePlatform('TELEGRAM');
      setSelectedState('Kaduna');
    } else if (scenario === 'inec_query') {
      setActiveTab('assistant');
      setChatInput('Has INEC announced any postponement for Kano State polling units this weekend?');
    }
  };

  // Reporting Form State
  const [reportTitle, setReportTitle] = useState('');
  const [reportContent, setReportContent] = useState('');
  const [sourcePlatform, setSourcePlatform] = useState('WHATSAPP');
  const [sourceUrl, setSourceUrl] = useState('');
  const [selectedState, setSelectedState] = useState('Lagos');
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState<{ referenceNumber: string } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [copiedRef, setCopiedRef] = useState(false);

  // Tracking State
  const [trackRef, setTrackRef] = useState('');
  const [trackingReport, setTrackingReport] = useState<Report | null>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState<string | null>(null);

  // Registry Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [filterInstitution, setFilterInstitution] = useState('');
  const [registryResults, setRegistryResults] = useState<OfficialDocument[]>([]);
  const [registryLoading, setRegistryLoading] = useState(false);
  const [selectedDoc, setSelectedDoc] = useState<OfficialDocument | null>(null);

  // Cryptographic Hash Verifier State
  const [verifyMode, setVerifyMode] = useState<'text' | 'hash'>('text');
  const [verifyText, setVerifyText] = useState('');
  const [verifyHashInput, setVerifyHashInput] = useState('');
  const [verifyResult, setVerifyResult] = useState<HashVerificationResult | null>(null);
  const [verifying, setVerifying] = useState(false);

  // Conversational Assistant State
  const [chatMessages, setChatMessages] = useState<
    Array<{
      sender: 'user' | 'assistant';
      text: string;
      confidence?: number;
      decision?: string;
      sources?: Array<{ document_code?: string; title?: string; issuing_institution?: string }>;
      contradiction?: boolean;
    }>
  >([
    {
      sender: 'assistant',
      text: t(
        'ai_assistant_intro',
        'Greetings. I am CivicShield AI, your electoral information integrity assistant. You can ask me to verify circulating announcements, check official INEC schedules, or report suspicious election claims.'
      ),
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // File selection handling
  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const filesArray = Array.from(e.target.files);
      setSelectedFiles((prev) => [...prev, ...filesArray]);
    }
  };

  const removeFile = (idx: number) => {
    setSelectedFiles((prev) => prev.filter((_, i) => i !== idx));
  };

  // Voice recording for report content
  const handleVoiceInputReport = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening(
        (transcript) => {
          setReportContent((prev) => (prev ? `${prev} ${transcript}` : transcript));
        },
        (err) => {
          alert(`Voice error: ${err}`);
        }
      );
    }
  };

  // Voice recording for Chat
  const handleVoiceInputChat = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening(
        (transcript) => {
          setChatInput((prev) => (prev ? `${prev} ${transcript}` : transcript));
        },
        (err) => {
          alert(`Voice error: ${err}`);
        }
      );
    }
  };

  // Handle Report Submission
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      if (reportTitle) formData.append('title', reportTitle);
      formData.append('content_text', reportContent);
      formData.append('source_platform', sourcePlatform);
      if (sourceUrl) formData.append('source_url', sourceUrl);
      if (selectedState && selectedState !== 'All Nigeria (National)') {
        formData.append('nigerian_state', selectedState);
      }

      for (let i = 0; i < selectedFiles.length; i++) {
        formData.append('files', selectedFiles[i]);
      }

      const res = await api.post('/reports/submit', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const ref = res.data.data.reference_number;
      setSubmissionSuccess({ referenceNumber: ref });
      setReportTitle('');
      setReportContent('');
      setSourceUrl('');
      setSelectedFiles([]);
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || 'Failed to submit report. Please try again.';
      setSubmitError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyRefToClipboard = (ref: string) => {
    navigator.clipboard.writeText(ref);
    setCopiedRef(true);
    setTimeout(() => setCopiedRef(false), 2500);
  };

  // Handle Tracking
  const handleTrack = async (e: React.FormEvent, customRef?: string) => {
    if (e) e.preventDefault();
    const query = (customRef || trackRef).trim();
    if (!query) return;

    setTrackingLoading(true);
    setTrackingError(null);
    setTrackingReport(null);

    try {
      const res = await api.get(`/reports/track/${encodeURIComponent(query)}`);
      setTrackingReport(res.data.data);
    } catch (err: any) {
      setTrackingError(
        err.response?.data?.message || 'No record found for this reference number. Please check the code format (e.g. CS-YYYYMMDD-XXXXXX).'
      );
    } finally {
      setTrackingLoading(false);
    }
  };

  // Handle Registry Search
  const handleRegistrySearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setRegistryLoading(true);
    try {
      let url = `/registry/search?q=${encodeURIComponent(searchQuery)}`;
      if (filterInstitution) {
        url += `&institution=${encodeURIComponent(filterInstitution)}`;
      }
      const res = await api.get(url);
      setRegistryResults(res.data.data.items || []);
    } catch (err) {
      console.error('Error fetching registry search:', err);
    } finally {
      setRegistryLoading(false);
    }
  };

  // Handle Cryptographic Integrity Check
  const handleVerifyIntegrity = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    setVerifyResult(null);

    try {
      const payload: { content_text?: string; sha256_hash?: string } = {};
      if (verifyMode === 'text') {
        payload.content_text = verifyText;
      } else {
        payload.sha256_hash = verifyHashInput.trim();
      }

      const res = await api.post('/registry/verify', payload);
      setVerifyResult(res.data.data);
    } catch (err: any) {
      setVerifyResult({
        is_official_match: false,
        submitted_hash: 'N/A',
        verification_status: 'SERVICE_ERROR',
        analytical_note: err.response?.data?.message || 'Verification service error. Please try again.',
      });
    } finally {
      setVerifying(false);
    }
  };

  // Handle Chatbot Query
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userQuery = chatInput.trim();
    setChatMessages((prev) => [...prev, { sender: 'user', text: userQuery }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await api.post('/ai/analyze-claim', {
        claim_text: userQuery,
        context_state: selectedState !== 'All Nigeria (National)' ? selectedState : undefined,
      });

      const data: ClaimAnalysisResult = res.data.data;
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.analysis_summary,
          confidence: data.ai_confidence_score,
          decision: data.ai_suggested_status,
          sources: data.sources_consulted,
          contradiction: data.contradiction_suspected,
        },
      ]);
    } catch (err: any) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Unable to complete AI claim assessment right now. You can check the Official Gazettes tab directly or submit a report for human officer verification.',
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8" id="main-content">
      {/* Machine Translation Attribution Banner (Mandatory when Nigerian Pidgin is enabled) */}
      {language === 'pcm' && (
        <aside aria-label="Language translation notice" className="p-3 rounded-xl bg-emerald-950/70 border border-emerald-700/60 text-emerald-200 text-xs flex items-center justify-between shadow-sm">
          <div className="flex items-center space-x-2">
            <Info className="w-4 h-4 text-emerald-400 flex-shrink-0" />
            <span>
              <strong>Machine Translation (Nigerian Pidgin)</strong> — Official source is in English. Canonical legal documents preserve original English text.
            </span>
          </div>
          <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-900 border border-emerald-600">
            PIDGIN (PCM)
          </span>
        </aside>
      )}

      {/* Hero Section */}
      <section aria-labelledby="hero-title" className="relative rounded-3xl bg-gradient-to-br from-slate-950 via-emerald-950/80 to-slate-900 border border-emerald-900/50 p-8 sm:p-12 overflow-hidden shadow-2xl">
        <div className="absolute -right-10 -bottom-10 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-900/60 border border-emerald-700/60 text-emerald-300 text-xs font-bold">
            <Sparkles className="w-3.5 h-3.5 text-emerald-400" />
            <span>{t('hero_badge', 'AI-Powered Electoral Truth & Intelligence Infrastructure')}</span>
          </div>
          <h1 id="hero-title" className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
            {t('hero_title', 'Protecting Nigeria’s Electoral Information Environment')}
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            {t(
              'hero_subtitle',
              'Verify circulating election announcements against cryptographically certified institutional records. Report suspected misinformation, deepfakes, and coordinated propaganda in real-time.'
            )}
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => setActiveTab('report')}
              className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-sm shadow-lg shadow-emerald-950 transition-all flex items-center space-x-2 focus:ring-2 focus:ring-white"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>{t('btn_report_suspicious', 'Report Suspicious Information')}</span>
            </button>
            <button
              onClick={() => setActiveTab('registry')}
              className="px-5 py-3 rounded-xl bg-slate-900 hover:bg-slate-800 border border-slate-700 font-semibold text-slate-200 text-sm transition-all flex items-center space-x-2 focus:ring-2 focus:ring-white"
            >
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>{t('btn_verify_hash', 'Verify Official Document Hash')}</span>
            </button>
          </div>
        </div>
      </section>

      {/* Offline Alert & Demo Workflow Presets Toolbar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 rounded-2xl bg-slate-900 border border-slate-800 text-xs shadow-md">
        <div className="flex items-center space-x-2">
          <span className={`w-2.5 h-2.5 rounded-full ${isOnline ? 'bg-emerald-400' : 'bg-amber-400 animate-pulse'}`}></span>
          <span className="text-slate-300 font-semibold">
            {isOnline ? 'Network Operational' : `Offline Mode (${offlineCount} report${offlineCount === 1 ? '' : 's'} queued)`}
          </span>
          {!isOnline && (
            <span className="text-slate-500 text-[11px]">Submissions will auto-sync upon reconnection</span>
          )}
        </div>

        <div className="flex items-center space-x-2 flex-wrap gap-1">
          <span className="text-slate-400 font-mono text-[11px] hidden md:inline">Demo Presets:</span>
          <button
            type="button"
            onClick={() => loadDemoScenario('kano_postpone')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold border border-slate-700 transition-colors"
          >
            Kano Postponement Rumor
          </button>
          <button
            type="button"
            onClick={() => loadDemoScenario('bvas_failure')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold border border-slate-700 transition-colors"
          >
            Ward 7 BVAS Failure Notice
          </button>
          <button
            type="button"
            onClick={() => loadDemoScenario('inec_query')}
            className="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-[11px] font-semibold border border-slate-700 transition-colors"
          >
            AI Query Scenario
          </button>
        </div>
      </div>

      {/* Primary Feature Tabs */}
      <nav aria-label="Feature sections" className="flex w-full max-w-full border-b border-slate-800 gap-2 overflow-x-auto pb-1" role="tablist">
        <button
          role="tab"
          id="tab-btn-report"
          aria-selected={activeTab === 'report'}
          aria-controls="panel-report"
          onClick={() => setActiveTab('report')}
          className={`flex flex-shrink-0 items-center space-x-2 px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'report'
              ? 'border-emerald-500 text-emerald-400 bg-emerald-950/40 shadow-sm'
              : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>{t('tab_submit_report', 'Submit Report')}</span>
        </button>

        <button
          role="tab"
          id="tab-btn-track"
          aria-selected={activeTab === 'track'}
          aria-controls="panel-track"
          onClick={() => setActiveTab('track')}
          className={`flex flex-shrink-0 items-center space-x-2 px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'track'
              ? 'border-emerald-500 text-emerald-400 bg-emerald-950/40 shadow-sm'
              : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>{t('tab_track_status', 'Track Status')}</span>
        </button>

        <button
          role="tab"
          id="tab-btn-registry"
          aria-selected={activeTab === 'registry'}
          aria-controls="panel-registry"
          onClick={() => {
            setActiveTab('registry');
            if (registryResults.length === 0) handleRegistrySearch();
          }}
          className={`flex flex-shrink-0 items-center space-x-2 px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'registry'
              ? 'border-emerald-500 text-emerald-400 bg-emerald-950/40 shadow-sm'
              : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>{t('tab_official_registry', 'Official Gazettes')}</span>
        </button>

        <button
          role="tab"
          id="tab-btn-assistant"
          aria-selected={activeTab === 'assistant'}
          aria-controls="panel-assistant"
          onClick={() => setActiveTab('assistant')}
          className={`flex flex-shrink-0 items-center space-x-2 px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'assistant'
              ? 'border-emerald-500 text-emerald-400 bg-emerald-950/40 shadow-sm'
              : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>{t('tab_ai_assistant', 'CivicShield AI')}</span>
        </button>
      </nav>

      {/* TAB 1: CITIZEN REPORT SUBMISSION */}
      {activeTab === 'report' && (
        <section
          id="panel-report"
          role="tabpanel"
          aria-labelledby="tab-btn-report"
          className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-xl"
        >
          <div>
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-bold text-white">
                {language === 'pcm' ? 'Report Suspicious Election News / Announcement' : 'Submit Suspicious Election Announcement'}
              </h2>
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-950 text-emerald-400 border border-emerald-800">
                Salted Anonymity
              </span>
            </div>
            <p className="text-xs text-slate-400 mt-1">
              {t(
                'report_privacy_guarantee',
                'Zero Personally Identifiable Information (PII) is stored. Client IP is salted & cryptographically hashed with SHA-256.'
              )}
            </p>
          </div>

          {/* Success Card with Canonical Reference */}
          {submissionSuccess && (
            <div className="p-6 rounded-2xl bg-emerald-950/80 border border-emerald-700 text-white space-y-4 animate-fadeIn">
              <div className="flex items-center space-x-3">
                <CheckCircle2 className="w-7 h-7 text-emerald-400 flex-shrink-0" />
                <div>
                  <h3 className="font-bold text-base text-emerald-200">
                    {t('report_success_title', 'Report Ingested Successfully')}
                  </h3>
                  <p className="text-xs text-slate-300">
                    {t('report_reference_notice', 'Your canonical tracking reference code is:')}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between p-3.5 rounded-xl bg-black/50 border border-emerald-800/80">
                <span className="font-mono text-lg font-black text-emerald-400 tracking-wider">
                  {submissionSuccess.referenceNumber}
                </span>
                <button
                  onClick={() => copyRefToClipboard(submissionSuccess.referenceNumber)}
                  className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold transition-all flex items-center space-x-1"
                  aria-label="Copy reference code to clipboard"
                >
                  {copiedRef ? <Check className="w-3.5 h-3.5" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedRef ? 'Copied' : 'Copy'}</span>
                </button>
              </div>

              <div className="flex flex-wrap items-center justify-between gap-2 pt-2">
                <span className="text-xs text-slate-300">
                  Save this code to check verification progress without creating an account.
                </span>
                <button
                  onClick={() => {
                    setTrackRef(submissionSuccess.referenceNumber);
                    setActiveTab('track');
                    handleTrack(null as any, submissionSuccess.referenceNumber);
                  }}
                  className="px-4 py-2 rounded-xl bg-white text-slate-900 font-bold text-xs hover:bg-slate-200 transition-all flex items-center space-x-1"
                >
                  <span>Track Status Now</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}

          {submitError && (
            <div className="p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
              <span>{submitError}</span>
            </div>
          )}

          <form onSubmit={handleReportSubmit} className="space-y-5">
            {/* Short Title / Headline */}
            <div>
              <label htmlFor="report-title-input" className="block text-xs font-bold text-slate-300 mb-1">
                Headline / Short Summary (Optional)
              </label>
              <input
                id="report-title-input"
                type="text"
                value={reportTitle}
                onChange={(e) => setReportTitle(e.target.value)}
                placeholder="e.g. Rumor claiming Ward 4 polling units relocated"
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Content Text with Voice Dictation */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="report-content-textarea" className="text-xs font-bold text-slate-300">
                  {t('report_title_label', 'Suspicious Announcement / Incident Description *')}
                </label>
                {recognitionSupported && (
                  <button
                    type="button"
                    onClick={handleVoiceInputReport}
                    className={`flex items-center space-x-1 text-xs px-2.5 py-1 rounded-lg border transition-all ${
                      isListening
                        ? 'bg-rose-600 text-white border-rose-500 animate-pulse'
                        : 'bg-slate-950 text-emerald-400 border-slate-800 hover:border-emerald-600'
                    }`}
                    title="Speak using microphone"
                    aria-label={isListening ? 'Stop listening' : 'Start voice dictation'}
                  >
                    {isListening ? <MicOff className="w-3.5 h-3.5" /> : <Mic className="w-3.5 h-3.5" />}
                    <span>{isListening ? t('voice_stop', 'Stop Dictating') : t('voice_record', 'Voice Dictate')}</span>
                  </button>
                )}
              </div>
              <textarea
                id="report-content-textarea"
                required
                rows={5}
                value={reportContent}
                onChange={(e) => setReportContent(e.target.value)}
                placeholder={t(
                  'report_title_placeholder',
                  'Paste or describe the circulating claim, announcement, or rumor in detail...'
                )}
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 leading-relaxed"
              />
            </div>

            {/* Platform & State Selection */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label htmlFor="source-platform-select" className="block text-xs font-bold text-slate-300 mb-1">
                  {t('report_platform_label', 'Where did you encounter this? *')}
                </label>
                <select
                  id="source-platform-select"
                  value={sourcePlatform}
                  onChange={(e) => setSourcePlatform(e.target.value)}
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  <option value="WHATSAPP">WhatsApp Message / Voice Note</option>
                  <option value="TWITTER_X">X (Twitter)</option>
                  <option value="FACEBOOK">Facebook Post / Group</option>
                  <option value="TIKTOK">TikTok Video</option>
                  <option value="TELEGRAM">Telegram Channel</option>
                  <option value="RADIO_BROADCAST">Radio / FM Broadcast</option>
                  <option value="PHYSICAL_FLYER">Physical Flyer / Printout</option>
                  <option value="OTHER">Other / Word of Mouth</option>
                </select>
              </div>

              <div>
                <label htmlFor="nigerian-state-select" className="block text-xs font-bold text-slate-300 mb-1">
                  {t('report_state_label', 'State Affected (Location) *')}
                </label>
                <select
                  id="nigerian-state-select"
                  value={selectedState}
                  onChange={(e) => setSelectedState(e.target.value)}
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500"
                >
                  {NIGERIAN_STATES.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            {/* Source URL (Optional) */}
            <div>
              <label htmlFor="source-url-input" className="block text-xs font-bold text-slate-300 mb-1">
                Link to Post or Announcement (Optional)
              </label>
              <input
                id="source-url-input"
                type="url"
                value={sourceUrl}
                onChange={(e) => setSourceUrl(e.target.value)}
                placeholder="https://..."
                className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
              />
            </div>

            {/* Evidence Attachments */}
            <div>
              <label htmlFor="evidence-file-input" className="block text-xs font-bold text-slate-300 mb-1">
                {t('report_evidence_label', 'Attach Evidence (Image, Audio, Video, PDF)')}
              </label>
              <div className="border-2 border-dashed border-slate-800 hover:border-emerald-600 rounded-2xl p-5 text-center bg-slate-950/60 transition-colors">
                <input
                  id="evidence-file-input"
                  type="file"
                  multiple
                  onChange={handleFileChange}
                  className="hidden"
                />
                <label
                  htmlFor="evidence-file-input"
                  className="cursor-pointer flex flex-col items-center justify-center space-y-2"
                >
                  <UploadCloud className="w-8 h-8 text-emerald-400" />
                  <span className="text-xs text-slate-300 font-semibold">
                    Click to select evidence files (Max 25MB each)
                  </span>
                  <span className="text-[11px] text-slate-500">
                    PNG, JPG, MP3, WAV, OGG, MP4, PDF • SHA-256 fingerprinted
                  </span>
                </label>
              </div>

              {/* Selected Files List */}
              {selectedFiles.length > 0 && (
                <div className="mt-3 space-y-2">
                  {selectedFiles.map((f, idx) => (
                    <div
                      key={idx}
                      className="flex items-center justify-between p-2.5 rounded-xl bg-slate-950 border border-slate-800 text-xs"
                    >
                      <div className="flex items-center space-x-2 truncate">
                        <FileText className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                        <span className="text-slate-200 truncate">{f.name}</span>
                        <span className="text-[10px] text-slate-500">
                          ({(f.size / 1024).toFixed(1)} KB)
                        </span>
                      </div>
                      <button
                        type="button"
                        onClick={() => removeFile(idx)}
                        className="text-rose-400 hover:text-rose-300 text-xs p-1"
                        aria-label={`Remove file ${f.name}`}
                      >
                        <XCircle className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-sm shadow-xl shadow-emerald-950 transition-all flex items-center justify-center space-x-2"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>
                {isSubmitting
                  ? t('report_submitting', 'Securing Evidence & Hashing IP...')
                  : t('report_submit_btn', 'Submit Anonymously for Verification')}
              </span>
            </button>
          </form>
        </section>
      )}

      {/* TAB 2: REFERENCE TRACKING */}
      {activeTab === 'track' && (
        <section
          id="panel-track"
          role="tabpanel"
          aria-labelledby="tab-btn-track"
          className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-6 shadow-xl"
        >
          <div>
            <h2 className="text-xl font-bold text-white">
              {language === 'pcm' ? 'Check Status of Your Report' : 'Inspect Report Verification Status'}
            </h2>
            <p className="text-xs text-slate-400 mt-1">
              Look up any submitted report using its canonical reference code (<code className="font-mono text-emerald-400">CS-YYYYMMDD-XXXXXX</code>).
            </p>
          </div>

          <form onSubmit={handleTrack} className="flex flex-col sm:flex-row gap-3">
            <input
              type="text"
              required
              value={trackRef}
              onChange={(e) => setTrackRef(e.target.value.toUpperCase())}
              placeholder={t('track_input_placeholder', 'e.g. CS-20261125-A1B2C3')}
              className="flex-1 p-3.5 bg-slate-950 border border-slate-800 rounded-xl text-xs sm:text-sm font-mono text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 uppercase tracking-wider"
              aria-label="Report reference number"
            />
            <button
              type="submit"
              disabled={trackingLoading}
              className="px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs sm:text-sm transition-all flex items-center justify-center space-x-2"
            >
              <Search className="w-4 h-4" />
              <span>{trackingLoading ? t('track_loading', 'Checking...') : t('track_btn', 'Inspect Status')}</span>
            </button>
          </form>

          {trackingError && (
            <div className="p-4 rounded-xl bg-rose-950/80 border border-rose-800 text-rose-200 text-xs flex items-center space-x-2">
              <AlertTriangle className="w-4 h-4 flex-shrink-0 text-rose-400" />
              <span>{trackingError}</span>
            </div>
          )}

          {trackingReport && (
            <div className="p-6 rounded-2xl bg-slate-950 border border-slate-800 space-y-5 animate-fadeIn">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div>
                  <span className="text-[10px] uppercase font-mono text-slate-400 block">Report Reference</span>
                  <span className="text-lg font-mono font-black text-emerald-400">
                    {trackingReport.reference_number}
                  </span>
                </div>
                <div className="flex items-center space-x-2">
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold uppercase ${
                      trackingReport.status === 'VERIFIED'
                        ? 'bg-emerald-950 text-emerald-300 border border-emerald-700'
                        : trackingReport.status === 'CONTRADICTED'
                        ? 'bg-rose-950 text-rose-300 border border-rose-700'
                        : 'bg-amber-950 text-amber-300 border border-amber-700'
                    }`}
                  >
                    Status: {trackingReport.status}
                  </span>
                  <span className="px-2 py-1 rounded-lg bg-slate-900 text-slate-400 text-xs border border-slate-800">
                    State: {trackingReport.nigerian_state || 'National'}
                  </span>
                </div>
              </div>

              {/* Report Narrative Content */}
              <div>
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Submitted Narrative</h3>
                <p className="text-xs text-white leading-relaxed mt-1 p-3 rounded-xl bg-slate-900 border border-slate-800/80 italic">
                  "{trackingReport.content_text}"
                </p>
              </div>

              {/* Atomic Claims Evaluated */}
              {trackingReport.claims && trackingReport.claims.length > 0 && (
                <div className="space-y-3">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                    Extracted Claims &amp; Authoritative Review
                  </h3>
                  <div className="space-y-3">
                    {trackingReport.claims.map((claim) => (
                      <div
                        key={claim.id}
                        className="p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2"
                      >
                        <div className="flex items-center justify-between gap-2">
                          <span className="text-xs font-semibold text-white">{claim.claim_text}</span>
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase whitespace-nowrap ${
                              claim.ai_suggested_status === 'CONTRADICTED'
                                ? 'bg-rose-950 text-rose-400 border border-rose-800'
                                : claim.ai_suggested_status === 'VERIFIED'
                                ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                                : 'bg-slate-800 text-slate-300'
                            }`}
                          >
                            {claim.ai_suggested_status}
                          </span>
                        </div>

                        {claim.ai_analysis_summary && (
                          <p className="text-[11px] text-slate-300 leading-relaxed">
                            {claim.ai_analysis_summary}
                          </p>
                        )}

                        <div className="flex items-center space-x-3 text-[10px] text-slate-500 pt-1">
                          <span>Category: <strong className="text-slate-300">{claim.category}</strong></span>
                          <span>•</span>
                          <span>AI Confidence: <strong className="text-slate-300">{Math.round(claim.ai_confidence_score * 100)}%</strong></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Status Audit History Timeline */}
              {trackingReport.status_history && trackingReport.status_history.length > 0 && (
                <div className="space-y-2 pt-2 border-t border-slate-800">
                  <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wide">Audit Trail</h3>
                  <div className="space-y-1.5">
                    {trackingReport.status_history.map((h, i) => (
                      <div key={i} className="flex items-center space-x-2 text-[11px] text-slate-400 font-mono">
                        <span className="text-emerald-400">&bull;</span>
                        <span>{new Date(h.created_at).toLocaleString()}:</span>
                        <span className="text-slate-200">{h.previous_status} &rarr; {h.new_status}</span>
                        {h.notes && <span className="text-slate-500">({h.notes})</span>}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </section>
      )}

      {/* TAB 3: OFFICIAL GAZETTE REGISTRY & HASH VERIFIER */}
      {activeTab === 'registry' && (
        <section
          id="panel-registry"
          role="tabpanel"
          aria-labelledby="tab-btn-registry"
          className="space-y-6"
        >
          {/* Sub-Header: Search & Verifier Dual Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Search Authenticated Gazettes (2 Cols) */}
            <div className="lg:col-span-2 bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xl">
              <div>
                <h2 className="text-xl font-bold text-white">
                  {t('registry_search_label', 'Search Authenticated Electoral Documents')}
                </h2>
                <p className="text-xs text-slate-400 mt-1">
                  Query official gazettes, legal circulars, and INEC press statements with canonical SHA-256 checksums.
                </p>
              </div>

              <form onSubmit={handleRegistrySearch} className="flex flex-col sm:flex-row gap-3">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={t('registry_search_placeholder', 'Search by keyword, topic, or document code...')}
                  className="flex-1 p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-emerald-500"
                  aria-label="Search gazettes"
                />
                <button
                  type="submit"
                  disabled={registryLoading}
                  className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs transition-all flex items-center justify-center space-x-1.5"
                >
                  <Search className="w-4 h-4" />
                  <span>{registryLoading ? 'Searching...' : 'Search Registry'}</span>
                </button>
              </form>

              {/* Document Results List */}
              <div className="space-y-3 pt-2">
                {registryLoading ? (
                  <div className="text-center py-10 text-slate-500 text-xs">
                    Searching official gazette registry...
                  </div>
                ) : registryResults.length === 0 ? (
                  <div className="text-center py-10 text-slate-500 text-xs">
                    No authenticated documents matched your query. Try a different keyword or view recent publications.
                  </div>
                ) : (
                  registryResults.map((doc) => (
                    <div
                      key={doc.id}
                      className="p-5 rounded-2xl bg-slate-950 border border-slate-800 hover:border-slate-700 transition-all space-y-2 cursor-pointer"
                      onClick={() => setSelectedDoc(selectedDoc?.id === doc.id ? null : doc)}
                      role="button"
                      tabIndex={0}
                      aria-expanded={selectedDoc?.id === doc.id}
                    >
                      <div className="flex items-center justify-between gap-2 text-xs">
                        <span className="font-mono font-bold text-emerald-400 bg-emerald-950/80 px-2.5 py-0.5 rounded-full border border-emerald-800">
                          {doc.document_code}
                        </span>
                        <span className="text-slate-400 text-[11px] font-mono">
                          {doc.publication_date ? new Date(doc.publication_date).toLocaleDateString() : 'Active'}
                        </span>
                      </div>

                      <h3 className="font-bold text-sm text-white">{doc.title}</h3>
                      <p className="text-xs text-slate-300 leading-relaxed">{doc.summary}</p>

                      <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-[11px] text-slate-500 border-t border-slate-900">
                        <span>Institution: <strong className="text-slate-300">{doc.issuing_institution}</strong></span>
                        <span className="font-mono text-[10px] truncate max-w-xs">
                          SHA-256: {doc.sha256_hash?.slice(0, 20)}...
                        </span>
                      </div>

                      {/* Expanded Verbatim Content */}
                      {selectedDoc?.id === doc.id && (
                        <div className="mt-3 p-4 rounded-xl bg-slate-900 border border-slate-800 space-y-3 animate-fadeIn">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-bold text-emerald-300">Verbatim Official Document Text</span>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                speak(doc.content_text || doc.content || doc.summary);
                              }}
                              className="px-2 py-1 rounded bg-black/40 text-emerald-400 hover:text-emerald-300 text-[10px] flex items-center space-x-1"
                              aria-label="Read document aloud"
                            >
                              <Volume2 className="w-3 h-3" />
                              <span>Read Aloud</span>
                            </button>
                          </div>
                          <p className="text-xs text-white leading-relaxed font-mono whitespace-pre-wrap">
                            {doc.content_text || doc.content}
                          </p>
                          <div className="text-[10px] font-mono text-slate-400 break-all bg-black/40 p-2.5 rounded-lg border border-slate-800">
                            Canonical SHA-256 Checksum: <strong>{doc.sha256_hash}</strong>
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Cryptographic Hash Verifier Card (1 Col) */}
            <div className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl h-fit">
              <div className="flex items-center space-x-2">
                <FileCheck2 className="w-5 h-5 text-emerald-400" />
                <h2 className="text-base font-bold text-white">
                  {t('registry_verify_hash_title', 'Cryptographic Hash Verifier')}
                </h2>
              </div>
              <p className="text-xs text-slate-400">
                {t(
                  'registry_verify_hash_desc',
                  'Check if a digital announcement or PDF is authentic, untampered, and issued by verified electoral authorities.'
                )}
              </p>

              {/* Mode Toggle: Text vs Hash */}
              <div className="flex rounded-xl bg-slate-950 p-1 border border-slate-800 text-xs">
                <button
                  type="button"
                  onClick={() => setVerifyMode('text')}
                  className={`flex-1 py-1.5 rounded-lg font-bold transition-all ${
                    verifyMode === 'text' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Verify Text
                </button>
                <button
                  type="button"
                  onClick={() => setVerifyMode('hash')}
                  className={`flex-1 py-1.5 rounded-lg font-bold transition-all ${
                    verifyMode === 'hash' ? 'bg-emerald-600 text-white shadow' : 'text-slate-400 hover:text-white'
                  }`}
                >
                  Verify Hash
                </button>
              </div>

              <form onSubmit={handleVerifyIntegrity} className="space-y-3">
                {verifyMode === 'text' ? (
                  <div>
                    <label htmlFor="verify-text-area" className="block text-xs font-semibold text-slate-300 mb-1">
                      Paste Suspect Circular Text
                    </label>
                    <textarea
                      id="verify-text-area"
                      required
                      rows={5}
                      value={verifyText}
                      onChange={(e) => setVerifyText(e.target.value)}
                      placeholder="Paste verbatim announcement text to check against certified gazettes..."
                      className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                ) : (
                  <div>
                    <label htmlFor="verify-hash-input" className="block text-xs font-semibold text-slate-300 mb-1">
                      Enter SHA-256 Hex Hash (64 chars)
                    </label>
                    <input
                      id="verify-hash-input"
                      type="text"
                      required
                      minLength={64}
                      maxLength={64}
                      value={verifyHashInput}
                      onChange={(e) => setVerifyHashInput(e.target.value)}
                      placeholder="e.g. 5d41402abc4b2a76b9719d911017c592..."
                      className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                    />
                  </div>
                )}

                <button
                  type="submit"
                  disabled={verifying}
                  className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center space-x-1.5"
                >
                  <FileCheck2 className="w-4 h-4" />
                  <span>{verifying ? 'Verifying Hash...' : t('registry_verify_btn', 'Verify Integrity')}</span>
                </button>
              </form>

              {/* Verification Result Card */}
              {verifyResult && (
                <div
                  className={`p-4 rounded-2xl border space-y-2.5 text-xs animate-fadeIn ${
                    verifyResult.is_official_match
                      ? 'bg-emerald-950/70 border-emerald-700 text-emerald-200'
                      : verifyResult.verification_status === 'TAMPERED_SUSPECTED'
                      ? 'bg-rose-950/70 border-rose-700 text-rose-200'
                      : 'bg-amber-950/70 border-amber-700 text-amber-200'
                  }`}
                >
                  <div className="flex items-center space-x-2 font-bold">
                    {verifyResult.is_official_match ? (
                      <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-5 h-5 text-amber-400" />
                    )}
                    <span>
                      {verifyResult.is_official_match
                        ? 'AUTHENTIC CERTIFIED RECORD'
                        : verifyResult.verification_status}
                    </span>
                  </div>

                  <p className="leading-relaxed">{verifyResult.analytical_note}</p>

                  {verifyResult.matched_document_code && (
                    <div className="text-[11px] pt-1 border-t border-white/10">
                      Matched Code: <strong>{verifyResult.matched_document_code}</strong>
                    </div>
                  )}

                  <div className="text-[10px] font-mono break-all pt-1 opacity-70">
                    Hash: {verifyResult.submitted_hash}
                  </div>
                </div>
              )}
            </div>
          </div>
        </section>
      )}

      {/* TAB 4: CIVICSHIELD AI CONVERSATIONAL ASSISTANT */}
      {activeTab === 'assistant' && (
        <section
          id="panel-assistant"
          role="tabpanel"
          aria-labelledby="tab-btn-assistant"
          className="bg-slate-900/90 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xl max-w-4xl mx-auto"
        >
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
            <div>
              <div className="flex items-center space-x-2">
                <Sparkles className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-bold text-white">CivicShield Electoral AI Navigator</h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Grounded strictly in authenticated gazettes. When no official record exists, uncertainty is explicitly stated.
              </p>
            </div>
            <span className="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-950 text-emerald-300 border border-emerald-800 font-mono">
              Grounded Retrieval
            </span>
          </div>

          {/* Chat Messages Stream */}
          <div className="space-y-4 max-h-[500px] overflow-y-auto pr-1">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex flex-col space-y-1.5 ${
                  msg.sender === 'user' ? 'items-end' : 'items-start'
                }`}
              >
                <div
                  className={`p-4 rounded-2xl max-w-2xl text-xs sm:text-sm leading-relaxed shadow-md ${
                    msg.sender === 'user'
                      ? 'bg-emerald-600 text-white rounded-br-none'
                      : 'bg-slate-950 border border-slate-800 text-slate-100 rounded-bl-none space-y-3'
                  }`}
                >
                  <p className="whitespace-pre-wrap">{msg.text}</p>

                  {/* Assistant Evidence & Confidence Metadata */}
                  {msg.sender === 'assistant' && (msg.confidence !== undefined || (msg.sources && msg.sources.length > 0)) && (
                    <div className="pt-2 border-t border-slate-800/80 space-y-2 text-xs">
                      {msg.confidence !== undefined && (
                        <div className="flex items-center justify-between text-[11px] text-slate-400">
                          <span>
                            AI Assessment Confidence: <strong className="text-emerald-400">{Math.round(msg.confidence * 100)}%</strong>
                          </span>
                          {msg.decision && (
                            <span className="font-mono px-2 py-0.5 rounded bg-slate-900 border border-slate-800 text-[10px]">
                              Status: {msg.decision}
                            </span>
                          )}
                        </div>
                      )}

                      {/* Cited Sources */}
                      {msg.sources && msg.sources.length > 0 && (
                        <div className="space-y-1">
                          <span className="text-[11px] font-bold text-slate-400 block">Cited Certified Sources:</span>
                          {msg.sources.map((s, idx) => (
                            <div key={idx} className="p-2 rounded-lg bg-slate-900 text-[11px] border border-slate-800 flex items-center justify-between">
                              <span className="font-mono text-emerald-400 font-bold">{s.document_code}</span>
                              <span className="text-slate-300 truncate max-w-xs">{s.title}</span>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Read Aloud Button */}
                      <button
                        onClick={() => speak(msg.text)}
                        className="text-[11px] text-emerald-400 hover:text-emerald-300 flex items-center space-x-1 pt-1"
                        aria-label="Read this AI response aloud"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Read Aloud</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            {chatLoading && (
              <div className="flex items-center space-x-2 text-xs text-slate-400 p-3 rounded-2xl bg-slate-950 border border-slate-800 w-fit">
                <Sparkles className="w-4 h-4 text-emerald-400 animate-spin" />
                <span>Cross-referencing authenticated electoral registry...</span>
              </div>
            )}
          </div>

          {/* Mandatory Responsible AI Invariant Footer */}
          <aside aria-label="Responsible AI notice" className="p-3 rounded-xl bg-slate-950 border border-slate-800 text-[11px] text-slate-400 leading-normal flex items-start space-x-2">
            <Info className="w-4 h-4 text-amber-400 flex-shrink-0 mt-0.5" />
            <div>
              <strong>Responsible AI Directive:</strong> AI confidence scores are <em>never</em> presented as proof of truth or falsity. Authoritative decisions require human Verification Officer approval.
            </div>
          </aside>

          {/* Input Box */}
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <div className="relative flex-1">
              <input
                type="text"
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                placeholder={t('ai_input_placeholder', 'Ask about voting dates, polling centers, INEC circulars, or paste a circulating message...')}
                className="w-full p-3.5 pr-10 bg-slate-950 border border-slate-800 rounded-2xl text-xs sm:text-sm text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500"
                aria-label="Ask CivicShield AI a question"
              />
              {recognitionSupported && (
                <button
                  type="button"
                  onClick={handleVoiceInputChat}
                  className={`absolute right-2.5 top-1/2 -translate-y-1/2 p-1.5 rounded-lg transition-colors ${
                    isListening ? 'text-rose-400 animate-pulse' : 'text-slate-400 hover:text-emerald-400'
                  }`}
                  title="Speak your question"
                  aria-label={isListening ? 'Stop recording voice question' : 'Record voice question'}
                >
                  <Mic className="w-4 h-4" />
                </button>
              )}
            </div>

            <button
              type="submit"
              disabled={chatLoading || !chatInput.trim()}
              className="px-5 py-3.5 rounded-2xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs sm:text-sm shadow-md transition-all flex items-center justify-center space-x-1"
              aria-label="Send query to CivicShield AI"
            >
              <span>Ask</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </form>
        </section>
      )}
    </div>
  );
};
