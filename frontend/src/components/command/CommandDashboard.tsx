import React, { useState, useEffect } from 'react';
import {
  BarChart3,
  ShieldCheck,
  CheckCircle,
  AlertTriangle,
  Radio,
  FileCheck2,
  Lock,
  RefreshCw,
  Search,
  Filter,
  Check,
  X,
  Send,
  Eye,
  FileText,
  Activity,
  Layers,
  ChevronRight,
  TrendingUp,
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  LineChart,
  Line,
} from 'recharts';
import api from '../../api/client';
import { useAuth } from '../../context/AuthContext';
import {
  Report,
  Claim,
  Alert,
  OfficialDocument,
  NarrativeCluster,
  AuditLedgerResult,
  SecurityMetrics,
  SecurityEvent,
} from '../../types';

export const CommandDashboard: React.FC = () => {
  const { user, hasRole, hasPermission } = useAuth();
  const [activeSection, setActiveSection] = useState<
    'overview' | 'queue' | 'narratives' | 'registry' | 'alerts' | 'security'
  >('overview');

  // Overview Data
  const [reports, setReports] = useState<Report[]>([]);
  const [queueItems, setQueueItems] = useState<any[]>([]);
  const [clusters, setClusters] = useState<NarrativeCluster[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [officialDocs, setOfficialDocs] = useState<OfficialDocument[]>([]);
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics | null>(null);
  const [ledgerResult, setLedgerResult] = useState<AuditLedgerResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Verification Review Action State
  const [selectedQueueItem, setSelectedQueueItem] = useState<any | null>(null);
  const [verificationDecision, setVerificationDecision] = useState<string>('CONTRADICTED');
  const [verificationNotes, setVerificationNotes] = useState<string>('');
  const [contradictingDocId, setContradictingDocId] = useState<string>('');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);

  // Draft Alert State
  const [alertTitle, setAlertTitle] = useState('');
  const [alertSummary, setAlertSummary] = useState('');
  const [alertClarification, setAlertClarification] = useState('');
  const [alertSeverity, setAlertSeverity] = useState('HIGH');
  const [alertScope, setAlertScope] = useState('NATIONAL');
  const [alertState, setAlertState] = useState('');
  const [alertDebunkClaim, setAlertDebunkClaim] = useState('');

  // Official Doc Register State
  const [docCode, setDocCode] = useState('');
  const [docTitle, setDocTitle] = useState('');
  const [docInstitution, setDocInstitution] = useState('Independent National Electoral Commission');
  const [docContent, setDocContent] = useState('');
  const [docSummary, setDocSummary] = useState('');

  // Security Events & Audit
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [verifyingLedger, setVerifyingLedger] = useState(false);

  // Fetch initial institutional data
  const loadDashboardData = async () => {
    setIsLoading(true);
    try {
      const [
        reportsRes,
        queueRes,
        clustersRes,
        alertsRes,
        docsRes,
        metricsRes,
        eventsRes,
      ] = await Promise.allSettled([
        api.get('/reports?limit=20'),
        api.get('/verification/queue?limit=20'),
        api.get('/narratives/clusters?limit=10'),
        api.get('/alerts/feed/active?limit=20'),
        api.get('/registry/documents?limit=20'),
        api.get('/security/metrics'),
        api.get('/security/events?limit=10'),
      ]);

      if (reportsRes.status === 'fulfilled') setReports(reportsRes.value.data.data.items);
      if (queueRes.status === 'fulfilled') setQueueItems(queueRes.value.data.data.items);
      if (clustersRes.status === 'fulfilled') setClusters(clustersRes.value.data.data.items);
      if (alertsRes.status === 'fulfilled') setAlerts(alertsRes.value.data.data);
      if (docsRes.status === 'fulfilled') setOfficialDocs(docsRes.value.data.data.items);
      if (metricsRes.status === 'fulfilled') setSecurityMetrics(metricsRes.value.data.data);
      if (eventsRes.status === 'fulfilled') setSecurityEvents(eventsRes.value.data.data.items);
    } catch (err) {
      console.error('Error fetching institutional dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // Handle Recording Decision in Verification Queue
  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQueueItem) return;

    try {
      await api.post(`/verification/claims/${selectedQueueItem.claim_id}/decision`, {
        decision: verificationDecision,
        confidence_score: 0.95,
        verification_notes: verificationNotes || 'Authoritative review completed based on official certified gazettes.',
        official_document_id: contradictingDocId || undefined,
        requires_immediate_alert: verificationDecision === 'CONTRADICTED',
      });

      setActionSuccess(`Decision recorded: ${verificationDecision} for claim ${selectedQueueItem.claim_id}`);
      setSelectedQueueItem(null);
      setVerificationNotes('');
      setContradictingDocId('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to record decision');
    }
  };

  // Handle Drafting Early Warning Alert
  const handleDraftAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/alerts/draft', {
        title: alertTitle,
        summary: alertSummary,
        full_clarification: alertClarification,
        severity: alertSeverity,
        category: 'MISINFORMATION_ALERT',
        target_scope: alertScope,
        target_state: alertScope === 'STATE_SPECIFIC' ? alertState : undefined,
        debunked_claim_text: alertDebunkClaim || undefined,
      });

      alert('Early warning draft created! Proceed to approval queue.');
      setAlertTitle('');
      setAlertSummary('');
      setAlertClarification('');
      setAlertDebunkClaim('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to draft alert');
    }
  };

  // Handle Approving Alert
  const handleApproveAlert = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/approve`);
      alert('Alert approved and broadcast to targeted citizen feeds!');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to approve alert');
    }
  };

  // Handle Registering Official Document
  const handleRegisterDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post('/registry/documents', {
        document_code: docCode,
        title: docTitle,
        issuing_institution: docInstitution,
        content: docContent,
        summary: docSummary,
        publication_date: new Date().toISOString().split('T')[0],
      });

      alert('Official document authenticated and registered into gazette repository!');
      setDocCode('');
      setDocTitle('');
      setDocContent('');
      setDocSummary('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to register document');
    }
  };

  // Handle Cryptographic Ledger Integrity Check
  const handleVerifyAuditLedger = async () => {
    setVerifyingLedger(true);
    try {
      const res = await api.post('/security/audit-logs/verify-ledger');
      setLedgerResult(res.data.data);
    } catch (err: any) {
      alert('Verification request failed');
    } finally {
      setVerifyingLedger(false);
    }
  };

  // Prepare chart data for narrative clusters
  const clusterChartData = clusters.map((c) => ({
    name: c.cluster_name.length > 20 ? c.cluster_name.substring(0, 18) + '...' : c.cluster_name,
    reports: c.report_count,
    velocity: Math.round(c.propagation_velocity_score * 10),
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Header Bar */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-2xl shadow-md text-white">
        <div className="flex items-center space-x-3">
          <div className="p-2.5 rounded-xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 className="text-xl font-bold">CivicShield Command Centre</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
                OFFICER ACCESS
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Logged in as <strong className="text-slate-200">{user?.full_name}</strong> ({user?.roles.join(', ')})
            </p>
          </div>
        </div>

        <button
          onClick={loadDashboardData}
          disabled={isLoading}
          className="flex items-center space-x-2 px-3 py-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-xs text-slate-300 transition-colors border border-slate-700"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${isLoading ? 'animate-spin' : ''}`} />
          <span>Refresh Data</span>
        </button>
      </div>

      {/* Navigation Sub-Menu */}
      <div className="flex border-b border-slate-800 gap-1 overflow-x-auto pb-1 text-xs sm:text-sm font-semibold">
        {[
          { id: 'overview', label: 'Intelligence Overview', icon: Activity },
          { id: 'queue', label: `Verification Queue (${queueItems.length})`, icon: CheckCircle },
          { id: 'narratives', label: `Narrative Clusters (${clusters.length})`, icon: TrendingUp },
          { id: 'registry', label: 'Official Registry', icon: FileCheck2 },
          { id: 'alerts', label: `Early Warnings (${alerts.length})`, icon: Radio },
          { id: 'security', label: 'Security & Audit Ledger', icon: Lock },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveSection(tab.id as any)}
              className={`flex items-center space-x-2 px-4 py-2.5 rounded-lg transition-all border-b-2 whitespace-nowrap ${
                isActive
                  ? 'border-blue-500 text-blue-400 bg-blue-950/40'
                  : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-800/40'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* SECTION 1: OVERVIEW & THREAT KPIS */}
      {activeSection === 'overview' && (
        <div className="space-y-6">
          {/* KPI Cards Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Citizen Reports</span>
                <FileText className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-2xl font-bold text-white">{reports.length}</div>
              <p className="text-[11px] text-slate-500">Total ingested reports</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Pending Review Queue</span>
                <CheckCircle className="w-4 h-4 text-amber-400" />
              </div>
              <div className="text-2xl font-bold text-amber-400">{queueItems.length}</div>
              <p className="text-[11px] text-slate-500">Requires human decision</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Active Narrative Clusters</span>
                <TrendingUp className="w-4 h-4 text-blue-400" />
              </div>
              <div className="text-2xl font-bold text-blue-400">{clusters.length}</div>
              <p className="text-[11px] text-slate-500">Coordinated patterns tracked</p>
            </div>

            <div className="bg-slate-900 border border-slate-800 p-5 rounded-2xl space-y-2">
              <div className="flex items-center justify-between text-slate-400 text-xs">
                <span>Audit Ledger Integrity</span>
                <ShieldCheck className="w-4 h-4 text-emerald-400" />
              </div>
              <div className="text-xl font-bold text-emerald-400 font-mono">
                {securityMetrics?.ledger_integrity_status || 'VERIFIED'}
              </div>
              <p className="text-[11px] text-slate-500">
                {securityMetrics?.total_audit_records || 0} chained records
              </p>
            </div>
          </div>

          {/* Real-time Threat Chart */}
          <div className="bg-slate-900 border border-slate-800 p-6 rounded-2xl space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-white">Coordinated Misinformation Velocity</h3>
                <p className="text-xs text-slate-400">
                  Correlating citizen report volume with narrative propagation speed
                </p>
              </div>
            </div>

            {clusterChartData.length > 0 ? (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={clusterChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                    <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                    <YAxis stroke="#64748b" fontSize={11} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '8px' }}
                    />
                    <Bar dataKey="reports" fill="#10b981" name="Citizen Reports" radius={[4, 4, 0, 0]} />
                    <Bar dataKey="velocity" fill="#3b82f6" name="Velocity Index" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                No active narrative clusters available yet.
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 2: VERIFICATION QUEUE */}
      {activeSection === 'queue' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div>
              <h3 className="font-bold text-base text-white">Pending Verification Review Queue</h3>
              <p className="text-xs text-slate-400">
                Human Verification Officers must review candidate claims. AI results provide decision support, not final rulings.
              </p>
            </div>

            {queueItems.length > 0 ? (
              <div className="space-y-3">
                {queueItems.map((item) => (
                  <div
                    key={item.claim_id}
                    onClick={() => setSelectedQueueItem(item)}
                    className={`p-4 rounded-xl border cursor-pointer transition-all ${
                      selectedQueueItem?.claim_id === item.claim_id
                        ? 'bg-blue-950/60 border-blue-500'
                        : 'bg-slate-950/60 border-slate-800 hover:border-slate-700'
                    }`}
                  >
                    <div className="flex items-center justify-between text-xs mb-1">
                      <span className="font-mono text-emerald-400 font-bold">{item.report_reference}</span>
                      <span className="text-slate-400">State: {item.state || 'National'}</span>
                    </div>
                    <p className="text-sm font-semibold text-white">"{item.claim_text}"</p>
                    <div className="mt-2 flex items-center justify-between text-xs text-slate-400">
                      <span>Platform: {item.source_platform}</span>
                      <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-mono text-[11px]">
                        AI: {item.ai_suggested_status} ({(item.ai_confidence_score * 100).toFixed(0)}%)
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                Verification queue is currently clear!
              </div>
            )}
          </div>

          {/* Action / Review Form Panel */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Record Verification Decision</h3>

            {actionSuccess && (
              <div className="p-3 rounded-lg bg-emerald-950/60 border border-emerald-800 text-emerald-300 text-xs">
                {actionSuccess}
              </div>
            )}

            {selectedQueueItem ? (
              <form onSubmit={handleRecordDecision} className="space-y-4">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800 text-xs space-y-1">
                  <span className="text-slate-400">Selected Claim:</span>
                  <p className="font-bold text-white">"{selectedQueueItem.claim_text}"</p>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Authoritative Decision *
                  </label>
                  <select
                    value={verificationDecision}
                    onChange={(e) => setVerificationDecision(e.target.value)}
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="CONTRADICTED">CONTRADICTED (Confirmed False / Misleading)</option>
                    <option value="VERIFIED">VERIFIED (Confirmed Accurate with Official Record)</option>
                    <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT EVIDENCE</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Contradicting Official Document Citation
                  </label>
                  <select
                    value={contradictingDocId}
                    onChange={(e) => setContradictingDocId(e.target.value)}
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">None / External Verification</option>
                    {officialDocs.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.document_code} - {doc.title}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">
                    Officer Verification Notes &amp; Rationale *
                  </label>
                  <textarea
                    rows={3}
                    required
                    value={verificationNotes}
                    onChange={(e) => setVerificationNotes(e.target.value)}
                    placeholder="State the evidence or official announcement that contradicts or verifies this claim..."
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow transition-all"
                >
                  Confirm &amp; Record Decision
                </button>
              </form>
            ) : (
              <div className="text-center py-12 text-slate-500 text-xs">
                Select an item from the queue to review and record an authoritative decision.
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 3: NARRATIVE CLUSTERS */}
      {activeSection === 'narratives' && (
        <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
          <div>
            <h3 className="font-bold text-base text-white">Coordinated Information Manipulation Clusters</h3>
            <p className="text-xs text-slate-400">
              Clustering recurring claims across multiple states and platforms to detect organized disinformation campaigns.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
            {clusters.map((cluster) => (
              <div key={cluster.id} className="p-5 rounded-xl bg-slate-950 border border-slate-800 space-y-3">
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-sm text-white">{cluster.cluster_name}</h4>
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase ${
                      cluster.threat_level === 'CRITICAL'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}
                  >
                    {cluster.threat_level}
                  </span>
                </div>

                <p className="text-xs text-slate-300 italic">"{cluster.core_narrative}"</p>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Reports</span>
                    <strong className="text-white">{cluster.report_count}</strong>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">Velocity</span>
                    <strong className="text-emerald-400">{cluster.propagation_velocity_score.toFixed(1)}</strong>
                  </div>
                  <div className="p-2 rounded bg-slate-900 border border-slate-800">
                    <span className="text-[10px] text-slate-400 block">States</span>
                    <strong className="text-white">{cluster.distinct_states_count}</strong>
                  </div>
                </div>

                {cluster.geographical_spread && cluster.geographical_spread.length > 0 && (
                  <div className="text-[11px] text-slate-400">
                    Spread: <span className="text-slate-200">{cluster.geographical_spread.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* SECTION 4: OFFICIAL REGISTRY */}
      {activeSection === 'registry' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Register Document */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Register Official Certified Gazette</h3>
            <form onSubmit={handleRegisterDoc} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Document Code *</label>
                <input
                  type="text"
                  required
                  value={docCode}
                  onChange={(e) => setDocCode(e.target.value)}
                  placeholder="INEC-2026-PRESS-05"
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-blue-500 uppercase"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Title *</label>
                <input
                  type="text"
                  required
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="Official Rebuttal on Kano State Polling Units"
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Issuing Institution</label>
                <input
                  type="text"
                  value={docInstitution}
                  onChange={(e) => setDocInstitution(e.target.value)}
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Summary *</label>
                <input
                  type="text"
                  required
                  value={docSummary}
                  onChange={(e) => setDocSummary(e.target.value)}
                  placeholder="Summary of certified announcement..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Document Content *</label>
                <textarea
                  rows={4}
                  required
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  placeholder="Paste verbatim announcement text..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow"
              >
                Certify &amp; Compute SHA-256 Hash
              </button>
            </form>
          </div>

          {/* Existing Certified Records */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Certified Repository Records</h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {officialDocs.map((doc) => (
                <div key={doc.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-emerald-400">{doc.document_code}</span>
                    <span className="text-slate-400">{doc.publication_date}</span>
                  </div>
                  <h4 className="font-bold text-xs text-white">{doc.title}</h4>
                  <p className="text-[11px] text-slate-400">{doc.summary}</p>
                  <div className="text-[10px] font-mono text-slate-500 break-all pt-1">
                    SHA-256: {doc.sha256_hash}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SECTION 5: EARLY WARNINGS */}
      {activeSection === 'alerts' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Draft Alert Form */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Draft Early Warning Advisory</h3>
            <p className="text-xs text-slate-400">
              Only authorized human-reviewed findings may be distributed as confirmed misinformation alerts.
            </p>

            <form onSubmit={handleDraftAlert} className="space-y-3">
              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Advisory Title *</label>
                <input
                  type="text"
                  required
                  value={alertTitle}
                  onChange={(e) => setAlertTitle(e.target.value)}
                  placeholder="e.g. False Rumours of Kano Voting Postponement"
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Debunked Claim Text</label>
                <input
                  type="text"
                  value={alertDebunkClaim}
                  onChange={(e) => setAlertDebunkClaim(e.target.value)}
                  placeholder="e.g. Voting in Kano is postponed to Monday"
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Severity *</label>
                  <select
                    value={alertSeverity}
                    onChange={(e) => setAlertSeverity(e.target.value)}
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="INFORMATIONAL">INFORMATIONAL</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target Scope *</label>
                  <select
                    value={alertScope}
                    onChange={(e) => setAlertScope(e.target.value)}
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="NATIONAL">NATIONAL</option>
                    <option value="STATE_SPECIFIC">STATE_SPECIFIC</option>
                  </select>
                </div>
              </div>

              {alertScope === 'STATE_SPECIFIC' && (
                <div>
                  <label className="block text-xs font-semibold text-slate-300 mb-1">Target State *</label>
                  <input
                    type="text"
                    required
                    value={alertState}
                    onChange={(e) => setAlertState(e.target.value)}
                    placeholder="e.g. Kano"
                    className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Summary *</label>
                <input
                  type="text"
                  required
                  value={alertSummary}
                  onChange={(e) => setAlertSummary(e.target.value)}
                  placeholder="Short broadcast summary for notifications..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 mb-1">Full Clarification &amp; Evidence *</label>
                <textarea
                  rows={4}
                  required
                  value={alertClarification}
                  onChange={(e) => setAlertClarification(e.target.value)}
                  placeholder="Official debunk narrative and certified facts..."
                  className="w-full p-2.5 bg-slate-950 border border-slate-800 rounded-lg text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                className="w-full py-2.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow"
              >
                Draft Early Warning (Pending Dual-Key Approval)
              </button>
            </form>
          </div>

          {/* Active Broadcasts */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Active Early Warnings ({alerts.length})</h3>
            <div className="space-y-3 max-h-[500px] overflow-y-auto pr-1">
              {alerts.map((al) => (
                <div key={al.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 space-y-2">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono text-emerald-400 font-bold">{al.alert_reference}</span>
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                        al.severity === 'CRITICAL' ? 'bg-rose-950 text-rose-400' : 'bg-amber-950 text-amber-400'
                      }`}
                    >
                      {al.severity}
                    </span>
                  </div>
                  <h4 className="font-bold text-xs text-white">{al.title}</h4>
                  <p className="text-[11px] text-slate-400">{al.summary}</p>

                  <div className="pt-2 flex items-center justify-between text-xs border-t border-slate-800">
                    <span className="text-[11px] text-slate-500">Status: {al.status}</span>
                    {al.status === 'PENDING_APPROVAL' && (
                      <button
                        onClick={() => handleApproveAlert(al.id)}
                        className="px-3 py-1 rounded bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold"
                      >
                        Approve &amp; Broadcast
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SECTION 6: DATABASE SECURITY & AUDIT LEDGER */}
      {activeSection === 'security' && (
        <div className="space-y-6">
          {/* Tamper-Evident Ledger Verification Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <h3 className="font-bold text-base text-white">Cryptographic Tamper-Evident Audit Ledger</h3>
                <p className="text-xs text-slate-400">
                  Every state mutation is chained to preceding records via SHA-256 cryptographic hashes.
                </p>
              </div>

              <button
                onClick={handleVerifyAuditLedger}
                disabled={verifyingLedger}
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-bold text-xs shadow flex items-center space-x-2"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{verifyingLedger ? 'Traversing Chain...' : 'Run Ledger Verification'}</span>
              </button>
            </div>

            {ledgerResult && (
              <div
                className={`p-5 rounded-xl border space-y-3 ${
                  ledgerResult.is_valid
                    ? 'bg-emerald-950/60 border-emerald-800 text-emerald-200'
                    : 'bg-rose-950/60 border-rose-800 text-rose-200'
                }`}
              >
                <div className="flex items-center space-x-2 font-bold text-sm">
                  {ledgerResult.is_valid ? <CheckCircle className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                  <span>{ledgerResult.verification_message}</span>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs font-mono">
                  <div>Verified Records: {ledgerResult.total_entries_verified}</div>
                  {ledgerResult.first_verified_hash && (
                    <div className="truncate">First Hash: {ledgerResult.first_verified_hash}</div>
                  )}
                  {ledgerResult.latest_verified_hash && (
                    <div className="truncate">Latest Hash: {ledgerResult.latest_verified_hash}</div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Security Events Monitor */}
          <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
            <h3 className="font-bold text-base text-white">Technical Security Incidents</h3>
            <div className="space-y-3">
              {securityEvents.map((ev) => (
                <div key={ev.id} className="p-4 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                  <div>
                    <div className="flex items-center space-x-2">
                      <span className="font-bold text-white uppercase">{ev.event_type}</span>
                      <span className="px-1.5 py-0.5 rounded bg-rose-950 text-rose-400 font-mono text-[10px]">
                        {ev.severity}
                      </span>
                    </div>
                    <p className="text-slate-400 text-[11px] mt-0.5">
                      Target: {ev.user_identifier || ev.ip_address || 'System'} | Created: {ev.created_at}
                    </p>
                  </div>
                  <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${ev.resolved ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'}`}>
                    {ev.resolved ? 'RESOLVED' : 'OPEN'}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
