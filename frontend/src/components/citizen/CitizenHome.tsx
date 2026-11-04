import React, { useState } from 'react';
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
} from 'lucide-react';
import api from '../../api/client';
import { Report, OfficialDocument } from '../../types';

const NIGERIAN_STATES = [
  'All Nigeria (National)', 'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno',
  'Cross River', 'Delta', 'Ebonyi', 'Edo', 'Ekiti', 'Enugu', 'Federal Capital Territory',
  'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi', 'Kwara',
  'Lagos', 'Nasarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers',
  'Sokoto', 'Taraba', 'Yobe', 'Zamfara'
];

export const CitizenHome: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'report' | 'track' | 'registry' | 'assistant'>('report');

  // Reporting Form State
  const [reportContent, setReportContent] = useState('');
  const [sourcePlatform, setSourcePlatform] = useState('WHATSAPP');
  const [sourceUrl, setSourceUrl] = useState('');
  const [selectedState, setSelectedState] = useState('Lagos');
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submissionSuccess, setSubmissionSuccess] = useState<{ referenceNumber: string } | null>(null);
  const [submitError, setSubmitError] = useState<string | null>(null);

  // Tracking State
  const [trackRef, setTrackRef] = useState('');
  const [trackingReport, setTrackingReport] = useState<Report | null>(null);
  const [trackingLoading, setTrackingLoading] = useState(false);
  const [trackingError, setTrackingError] = useState<string | null>(null);

  // Registry Search State
  const [searchQuery, setSearchQuery] = useState('');
  const [registryResults, setRegistryResults] = useState<OfficialDocument[]>([]);
  const [registryLoading, setRegistryLoading] = useState(false);
  const [verifyText, setVerifyText] = useState('');
  const [verifyCode, setVerifyCode] = useState('');
  const [verifyResult, setVerifyResult] = useState<any | null>(null);
  const [verifying, setVerifying] = useState(false);

  // Conversational Assistant State
  const [chatMessages, setChatMessages] = useState<
    Array<{ sender: 'user' | 'assistant'; text: string; confidence?: number; decision?: string }>
  >([
    {
      sender: 'assistant',
      text: 'Greetings. I am CivicShield AI, your electoral information integrity assistant. You can ask me to verify circulating announcements, check official INEC schedules, or report suspicious election claims.',
    },
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);

  // Handle Report Submission
  const handleReportSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setIsSubmitting(true);

    try {
      const formData = new FormData();
      formData.append('content_text', reportContent);
      formData.append('source_platform', sourcePlatform);
      if (sourceUrl) formData.append('source_url', sourceUrl);
      if (selectedState && selectedState !== 'All Nigeria (National)') {
        formData.append('nigerian_state', selectedState);
      }

      if (selectedFiles) {
        for (let i = 0; i < selectedFiles.length; i++) {
          formData.append('files', selectedFiles[i]);
        }
      }

      const res = await api.post('/reports/submit', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      setSubmissionSuccess({ referenceNumber: res.data.data.reference_number });
      setReportContent('');
      setSourceUrl('');
      setSelectedFiles(null);
    } catch (err: any) {
      const msg = err.response?.data?.message || err.response?.data?.detail || 'Failed to submit report. Please try again.';
      setSubmitError(typeof msg === 'string' ? msg : JSON.stringify(msg));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handle Tracking
  const handleTrack = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!trackRef.trim()) return;
    setTrackingLoading(true);
    setTrackingError(null);
    setTrackingReport(null);

    try {
      const res = await api.get(`/reports/track/${trackRef.trim()}`);
      setTrackingReport(res.data.data);
    } catch (err: any) {
      setTrackingError('No record found for this reference number. Please check the code.');
    } finally {
      setTrackingLoading(false);
    }
  };

  // Handle Registry Search
  const handleRegistrySearch = async () => {
    setRegistryLoading(true);
    try {
      const res = await api.get(`/registry/documents?query=${encodeURIComponent(searchQuery)}&limit=10`);
      setRegistryResults(res.data.data.items);
    } catch (err) {
      console.error(err);
    } finally {
      setRegistryLoading(false);
    }
  };

  // Handle Cryptographic Integrity Check
  const handleVerifyIntegrity = async (e: React.FormEvent) => {
    e.preventDefault();
    setVerifying(true);
    try {
      const res = await api.post('/registry/verify-hash', {
        content: verifyText,
        document_code: verifyCode || undefined,
      });
      setVerifyResult(res.data.data);
    } catch (err: any) {
      setVerifyResult({ match_status: 'ERROR', message: 'Verification service error' });
    } finally {
      setVerifying(false);
    }
  };

  // Handle Chatbot Query
  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;

    const userQuery = chatInput;
    setChatMessages((prev) => [...prev, { sender: 'user', text: userQuery }]);
    setChatInput('');
    setChatLoading(true);

    try {
      const res = await api.post('/ai/analyze-claim', { text: userQuery });
      const data = res.data.data;
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: data.analysis_summary,
          confidence: data.confidence_score,
          decision: data.suggested_status,
        },
      ]);
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: 'Unable to reach the analysis pipeline at this moment. You can search the certified official registry tab directly.',
        },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
      {/* Hero Section */}
      <div className="relative rounded-3xl bg-gradient-to-br from-slate-950 via-emerald-950/70 to-slate-900 border border-emerald-900/40 p-8 sm:p-12 overflow-hidden shadow-2xl">
        <div className="absolute -right-10 -bottom-10 w-96 h-96 bg-emerald-600/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="relative z-10 max-w-3xl space-y-4">
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-emerald-900/60 border border-emerald-700/60 text-emerald-300 text-xs font-semibold">
            <Sparkles className="w-3.5 h-3.5" />
            <span>AI-Powered Electoral Truth &amp; Intelligence Infrastructure</span>
          </div>
          <h1 className="text-3xl sm:text-5xl font-black text-white tracking-tight leading-tight">
            Protecting Nigeria’s Electoral Information Environment
          </h1>
          <p className="text-slate-300 text-sm sm:text-base leading-relaxed">
            Verify circulating election announcements against cryptographically certified institutional records.
            Report suspected misinformation, deepfakes, and coordinated propaganda in real-time.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <button
              onClick={() => setActiveTab('report')}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-sm shadow-lg shadow-emerald-900/40 transition-all flex items-center space-x-2"
            >
              <ShieldAlert className="w-4 h-4" />
              <span>Report Suspicious Information</span>
            </button>
            <button
              onClick={() => setActiveTab('registry')}
              className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700 font-semibold text-slate-200 text-sm transition-all flex items-center space-x-2"
            >
              <FileCheck2 className="w-4 h-4 text-emerald-400" />
              <span>Verify Official Document Hash</span>
            </button>
          </div>
        </div>
      </div>

      {/* Primary Feature Tabs */}
      <div className="flex border-b border-slate-200 dark:border-slate-800 gap-2 overflow-x-auto pb-1">
        <button
          onClick={() => setActiveTab('report')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'report'
              ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <ShieldAlert className="w-4 h-4" />
          <span>Submit Report</span>
        </button>

        <button
          onClick={() => setActiveTab('track')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'track'
              ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <Clock className="w-4 h-4" />
          <span>Track Status</span>
        </button>

        <button
          onClick={() => setActiveTab('registry')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'registry'
              ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <FileCheck2 className="w-4 h-4" />
          <span>Official Registry &amp; Hash Check</span>
        </button>

        <button
          onClick={() => setActiveTab('assistant')}
          className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
            activeTab === 'assistant'
              ? 'border-emerald-600 text-emerald-700 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-950/40'
              : 'border-transparent text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white'
          }`}
        >
          <MessageSquare className="w-4 h-4" />
          <span>CivicShield AI Assistant</span>
        </button>
      </div>

      {/* TAB 1: SUBMIT REPORT */}
      {activeTab === 'report' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Submit Suspicious Electoral Information</h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Found a suspicious press release, video, audio note, or social media post claiming to be from INEC or an official source?
              </p>
            </div>

            {submissionSuccess ? (
              <div className="p-6 rounded-2xl bg-emerald-50 dark:bg-emerald-950/50 border border-emerald-200 dark:border-emerald-800 space-y-4">
                <div className="flex items-center space-x-3 text-emerald-700 dark:text-emerald-300">
                  <CheckCircle2 className="w-8 h-8 flex-shrink-0" />
                  <div>
                    <h3 className="font-bold text-lg">Report Successfully Submitted</h3>
                    <p className="text-xs">Your submission has entered the automated triage and verification queue.</p>
                  </div>
                </div>

                <div className="p-4 bg-white dark:bg-slate-900 rounded-xl border border-emerald-300 dark:border-emerald-800 text-center">
                  <span className="text-xs uppercase font-medium text-slate-500">Your Unique Tracking Reference</span>
                  <div className="text-2xl font-mono font-extrabold text-emerald-600 dark:text-emerald-400 mt-1 select-all">
                    {submissionSuccess.referenceNumber}
                  </div>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Save this reference code to track the investigation progress anytime.
                  </p>
                </div>

                <div className="flex justify-end space-x-3">
                  <button
                    onClick={() => {
                      setTrackRef(submissionSuccess.referenceNumber);
                      setActiveTab('track');
                    }}
                    className="px-4 py-2 rounded-lg bg-emerald-600 text-white font-medium text-xs hover:bg-emerald-500"
                  >
                    Track Progress Now
                  </button>
                  <button
                    onClick={() => setSubmissionSuccess(null)}
                    className="px-4 py-2 rounded-lg bg-slate-200 dark:bg-slate-800 text-slate-700 dark:text-slate-300 font-medium text-xs"
                  >
                    Submit Another Report
                  </button>
                </div>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4">
                {submitError && (
                  <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/50 border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs">
                    {submitError}
                  </div>
                )}

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Description or Content of Suspicious Claim *
                  </label>
                  <textarea
                    required
                    rows={4}
                    value={reportContent}
                    onChange={(e) => setReportContent(e.target.value)}
                    placeholder="Paste the suspicious message, transcript of voice note, or describe the claim being circulated..."
                    className="w-full p-3 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Encounter Platform *
                    </label>
                    <select
                      value={sourcePlatform}
                      onChange={(e) => setSourcePlatform(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                    >
                      <option value="WHATSAPP">WhatsApp Message / Group</option>
                      <option value="TELEGRAM">Telegram Channel</option>
                      <option value="TWITTER_X">X (Twitter)</option>
                      <option value="FACEBOOK">Facebook Post</option>
                      <option value="TIKTOK">TikTok Video</option>
                      <option value="YOUTUBE">YouTube</option>
                      <option value="RADIO_BROADCAST">Radio / Television Broadcast</option>
                      <option value="OTHER">Other / Word of Mouth</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                      Nigerian State (if applicable)
                    </label>
                    <select
                      value={selectedState}
                      onChange={(e) => setSelectedState(e.target.value)}
                      className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                    >
                      {NIGERIAN_STATES.map((st) => (
                        <option key={st} value={st}>
                          {st}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Source Link / URL (Optional)
                  </label>
                  <input
                    type="url"
                    value={sourceUrl}
                    onChange={(e) => setSourceUrl(e.target.value)}
                    placeholder="https://..."
                    className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm text-slate-900 dark:text-white focus:outline-none focus:border-emerald-500"
                  />
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                    Upload Supporting Media (Screenshots, PDF, Audio, Video - Max 25MB)
                  </label>
                  <div className="border-2 border-dashed border-slate-300 dark:border-slate-700 rounded-xl p-4 text-center hover:border-emerald-500 transition-colors">
                    <input
                      type="file"
                      multiple
                      accept="image/*,audio/*,video/*,application/pdf"
                      onChange={(e) => setSelectedFiles(e.target.files)}
                      className="hidden"
                      id="evidence-file-input"
                    />
                    <label htmlFor="evidence-file-input" className="cursor-pointer space-y-1 block">
                      <UploadCloud className="w-8 h-8 mx-auto text-slate-400" />
                      <div className="text-xs text-slate-600 dark:text-slate-400">
                        {selectedFiles && selectedFiles.length > 0 ? (
                          <span className="font-bold text-emerald-600 dark:text-emerald-400">
                            {selectedFiles.length} file(s) attached
                          </span>
                        ) : (
                          <span>Click to browse evidence files or drag &amp; drop</span>
                        )}
                      </div>
                      <p className="text-[10px] text-slate-400">PNG, JPG, MP3, WAV, MP4, PDF (max 25MB)</p>
                    </label>
                  </div>
                </div>

                <div className="pt-2">
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-sm shadow-md transition-all flex items-center justify-center space-x-2"
                  >
                    {isSubmitting ? (
                      <span>Analyzing &amp; Ingesting...</span>
                    ) : (
                      <>
                        <ShieldAlert className="w-4 h-4" />
                        <span>Submit for Verification</span>
                      </>
                    )}
                  </button>
                </div>
              </form>
            )}
          </div>

          {/* Privacy & Trust Safeguards Column */}
          <div className="space-y-6">
            <div className="p-6 rounded-2xl bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 space-y-4">
              <div className="flex items-center space-x-2 text-emerald-600 dark:text-emerald-400">
                <Lock className="w-5 h-5" />
                <h3 className="font-bold text-sm text-slate-900 dark:text-white">Citizen Privacy Guarantees</h3>
              </div>
              <ul className="text-xs text-slate-600 dark:text-slate-400 space-y-2.5">
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-500 font-bold">&#10003;</span>
                  <span><strong>Zero Submitter IP Storage:</strong> Client IP addresses are immediately salted and hashed with SHA-256 for abuse mitigation only.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-500 font-bold">&#10003;</span>
                  <span><strong>Sanitized Evidence:</strong> Uploaded media is scanned, sanitized, and stored with unique cryptographic hashes.</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-emerald-500 font-bold">&#10003;</span>
                  <span><strong>Neutral Institutional Oversight:</strong> Verified by accredited non-partisan fact-checkers and official election registrars.</span>
                </li>
              </ul>
            </div>

            <div className="p-6 rounded-2xl bg-slate-100 dark:bg-slate-800/50 border border-slate-200 dark:border-slate-700/50 space-y-3">
              <h4 className="font-bold text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">
                Report Lifecycle
              </h4>
              <div className="space-y-3 text-xs text-slate-600 dark:text-slate-300">
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-slate-300 dark:bg-slate-700 flex items-center justify-center text-[10px] font-bold">1</span>
                  <span>Automated claim extraction &amp; registry comparison</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-slate-300 dark:bg-slate-700 flex items-center justify-center text-[10px] font-bold">2</span>
                  <span>Cross-check with certified official gazettes</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-slate-300 dark:bg-slate-700 flex items-center justify-center text-[10px] font-bold">3</span>
                  <span>Human Verification Officer authoritative decision</span>
                </div>
                <div className="flex items-center space-x-2">
                  <span className="w-5 h-5 rounded-full bg-emerald-600 text-white flex items-center justify-center text-[10px] font-bold">4</span>
                  <span>Early Warning Advisory broadcast to citizens if critical</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* TAB 2: TRACK STATUS */}
      {activeTab === 'track' && (
        <div className="max-w-3xl mx-auto space-y-6">
          <div className="bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <h2 className="text-xl font-bold text-slate-900 dark:text-white">Track Submitted Report</h2>
            <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
              Enter your reference number (e.g. <span className="font-mono">CS-20261104-XXXXXX</span>) to check investigation progress.
            </p>

            <form onSubmit={handleTrack} className="flex gap-2">
              <input
                type="text"
                required
                value={trackRef}
                onChange={(e) => setTrackRef(e.target.value)}
                placeholder="CS-20261104-XXXXXX"
                className="flex-1 p-3 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm font-mono focus:outline-none focus:border-emerald-500 uppercase"
              />
              <button
                type="submit"
                disabled={trackingLoading}
                className="px-6 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 font-bold text-white text-sm shadow transition-all"
              >
                {trackingLoading ? 'Checking...' : 'Track'}
              </button>
            </form>

            {trackingError && (
              <div className="p-3 rounded-lg bg-rose-50 dark:bg-rose-950/50 border border-rose-300 dark:border-rose-800 text-rose-700 dark:text-rose-300 text-xs">
                {trackingError}
              </div>
            )}
          </div>

          {trackingReport && (
            <div className="bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-200 dark:border-slate-800 pb-4">
                <div>
                  <span className="text-[11px] font-mono text-slate-400">Reference: {trackingReport.reference_number}</span>
                  <h3 className="text-lg font-bold text-slate-900 dark:text-white">
                    Investigation Status:
                    <span
                      className={`ml-2 px-2.5 py-1 rounded-md text-xs font-extrabold uppercase ${
                        trackingReport.status === 'CONTRADICTED'
                          ? 'bg-rose-100 dark:bg-rose-950 text-rose-700 dark:text-rose-400 border border-rose-300 dark:border-rose-800'
                          : trackingReport.status === 'VERIFIED'
                          ? 'bg-emerald-100 dark:bg-emerald-950 text-emerald-700 dark:text-emerald-400 border border-emerald-300 dark:border-emerald-800'
                          : 'bg-amber-100 dark:bg-amber-950 text-amber-700 dark:text-amber-400 border border-amber-300 dark:border-amber-800'
                      }`}
                    >
                      {trackingReport.status}
                    </span>
                  </h3>
                </div>
                <div className="text-xs text-slate-500">
                  State: <strong className="text-slate-800 dark:text-slate-200">{trackingReport.nigerian_state || 'National'}</strong>
                </div>
              </div>

              {/* Claims Breakdown */}
              <div className="space-y-4">
                <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">Extracted Claims &amp; Analysis</h4>
                {trackingReport.claims?.map((claim) => (
                  <div key={claim.id} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-bold text-slate-700 dark:text-slate-300">{claim.category}</span>
                      <span className="text-[11px] font-mono text-slate-400">
                        AI Confidence: {(claim.ai_confidence_score * 100).toFixed(0)}%
                      </span>
                    </div>
                    <p className="text-sm font-semibold text-slate-900 dark:text-white">"{claim.extracted_claim}"</p>
                    <p className="text-xs text-slate-600 dark:text-slate-400">{claim.ai_analysis_summary}</p>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* TAB 3: REGISTRY & HASH VERIFIER */}
      {activeTab === 'registry' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Document Search */}
          <div className="bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Certified Electoral Gazette Repository</h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Search authenticated press releases, directives, and gazettes published by INEC and state electoral commissions.
              </p>
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search by keywords (e.g., 'Kano postponement', 'INEC timetable')..."
                className="flex-1 p-3 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm focus:outline-none focus:border-emerald-500"
              />
              <button
                onClick={handleRegistrySearch}
                className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow"
              >
                Search
              </button>
            </div>

            <div className="space-y-3 pt-2">
              {registryLoading ? (
                <div className="text-xs text-center text-slate-400 py-4">Searching certified registry...</div>
              ) : registryResults.length > 0 ? (
                registryResults.map((doc) => (
                  <div key={doc.id} className="p-4 rounded-xl bg-slate-50 dark:bg-slate-950 border border-slate-200 dark:border-slate-800 space-y-1.5">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-mono font-bold text-emerald-600 dark:text-emerald-400">
                        {doc.document_code}
                      </span>
                      <span className="text-[10px] text-slate-400">{doc.publication_date}</span>
                    </div>
                    <h4 className="font-bold text-sm text-slate-900 dark:text-white">{doc.title}</h4>
                    <p className="text-xs text-slate-600 dark:text-slate-400 line-clamp-2">{doc.summary}</p>
                    <div className="pt-1 text-[10px] font-mono text-slate-400 truncate">
                      SHA-256: {doc.sha256_hash}
                    </div>
                  </div>
                ))
              ) : (
                <div className="text-xs text-slate-400 text-center py-6">
                  Enter a keyword above to browse certified documents.
                </div>
              )}
            </div>
          </div>

          {/* Cryptographic SHA-256 Integrity Verifier */}
          <div className="bg-white dark:bg-slate-900 p-6 sm:p-8 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm space-y-4">
            <div>
              <h2 className="text-xl font-bold text-slate-900 dark:text-white">Cryptographic Document Integrity Verifier</h2>
              <p className="text-xs sm:text-sm text-slate-500 dark:text-slate-400">
                Paste the text of an announcement to compute its SHA-256 hash and verify if it has been tampered with or matches the certified official record.
              </p>
            </div>

            <form onSubmit={handleVerifyIntegrity} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Document Code (Optional)
                </label>
                <input
                  type="text"
                  value={verifyCode}
                  onChange={(e) => setVerifyCode(e.target.value)}
                  placeholder="e.g. INEC-2026-PRESS-04"
                  className="w-full p-2.5 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-sm font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 dark:text-slate-300 mb-1">
                  Exact Announcement Text *
                </label>
                <textarea
                  required
                  rows={4}
                  value={verifyText}
                  onChange={(e) => setVerifyText(e.target.value)}
                  placeholder="Paste the circulating text word-for-word..."
                  className="w-full p-3 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-xl text-xs font-mono focus:outline-none focus:border-emerald-500"
                />
              </div>

              <button
                type="submit"
                disabled={verifying}
                className="w-full py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-sm shadow transition-all"
              >
                {verifying ? 'Computing Canonical Hash...' : 'Verify Cryptographic Hash'}
              </button>
            </form>

            {verifyResult && (
              <div
                className={`p-4 rounded-xl border space-y-2 ${
                  verifyResult.match_status === 'AUTHENTIC_MATCH'
                    ? 'bg-emerald-50 dark:bg-emerald-950/60 border-emerald-300 dark:border-emerald-800'
                    : verifyResult.match_status === 'TAMPERED_SUSPECTED'
                    ? 'bg-rose-50 dark:bg-rose-950/60 border-rose-300 dark:border-rose-800'
                    : 'bg-slate-100 dark:bg-slate-800 border-slate-300 dark:border-slate-700'
                }`}
              >
                <div className="flex items-center space-x-2">
                  {verifyResult.match_status === 'AUTHENTIC_MATCH' ? (
                    <CheckCircle2 className="w-5 h-5 text-emerald-600 dark:text-emerald-400" />
                  ) : verifyResult.match_status === 'TAMPERED_SUSPECTED' ? (
                    <AlertTriangle className="w-5 h-5 text-rose-600 dark:text-rose-400" />
                  ) : (
                    <HelpCircle className="w-5 h-5 text-slate-500" />
                  )}
                  <span className="font-bold text-xs uppercase tracking-wide">
                    {verifyResult.match_status}
                  </span>
                </div>
                <p className="text-xs text-slate-700 dark:text-slate-300">{verifyResult.verification_message}</p>
                <div className="text-[10px] font-mono text-slate-500 break-all">
                  SHA-256: {verifyResult.submitted_hash}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* TAB 4: CIVICSHIELD AI ASSISTANT */}
      {activeTab === 'assistant' && (
        <div className="max-w-3xl mx-auto bg-white dark:bg-slate-900 rounded-2xl border border-slate-200 dark:border-slate-800 shadow-sm flex flex-col h-[600px] overflow-hidden">
          {/* Header */}
          <div className="p-4 border-b border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex items-center space-x-3">
            <div className="p-2 rounded-lg bg-emerald-600 text-white">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <h3 className="font-bold text-sm text-slate-900 dark:text-white">CivicShield AI Intelligence Assistant</h3>
              <p className="text-xs text-slate-400">Grounded in Nigerian certified gazettes &amp; election law</p>
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 p-4 overflow-y-auto space-y-4">
            {chatMessages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-2xl p-4 text-xs sm:text-sm leading-relaxed space-y-2 ${
                    msg.sender === 'user'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100'
                  }`}
                >
                  <p>{msg.text}</p>
                  {msg.decision && (
                    <div className="pt-2 border-t border-slate-200 dark:border-slate-700/60 flex items-center justify-between text-[11px]">
                      <span className="font-bold uppercase text-emerald-400">Status: {msg.decision}</span>
                      {msg.confidence !== undefined && (
                        <span className="opacity-80">Confidence: {(msg.confidence * 100).toFixed(0)}%</span>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-slate-100 dark:bg-slate-800 rounded-2xl p-3 text-xs text-slate-400 animate-pulse">
                  CivicShield AI is analyzing official registry &amp; cross-verifying...
                </div>
              </div>
            )}
          </div>

          {/* Input */}
          <form onSubmit={handleSendMessage} className="p-3 border-t border-slate-200 dark:border-slate-800 bg-slate-50 dark:bg-slate-950 flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              placeholder="Ask anything about Nigerian election announcements or claim authenticity..."
              className="flex-1 px-4 py-2.5 bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded-xl text-sm focus:outline-none focus:border-emerald-500"
            />
            <button
              type="submit"
              disabled={chatLoading}
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs"
            >
              Ask
            </button>
          </form>
        </div>
      )}
    </div>
  );
};
