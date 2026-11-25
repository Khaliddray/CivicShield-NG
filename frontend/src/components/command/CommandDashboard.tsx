import React, { useState, useEffect, useRef } from 'react';
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
  Share2,
  Network,
  ShieldAlert,
  Info,
  Clock,
  Sparkles,
  ExternalLink,
  Ban,
  CheckSquare,
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
  PieChart,
  Pie,
  Cell,
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
  QueueItem,
  NarrativeGraph,
  GraphNode,
  GraphEdge,
} from '../../types';

const COLORS = ['#10b981', '#3b82f6', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export const CommandDashboard: React.FC = () => {
  const { user, hasPermission } = useAuth();
  const [activeSection, setActiveSection] = useState<
    'overview' | 'queue' | 'narratives' | 'registry' | 'alerts' | 'security'
  >('overview');

  // Overview Data
  const [reports, setReports] = useState<Report[]>([]);
  const [queueItems, setQueueItems] = useState<QueueItem[]>([]);
  const [clusters, setClusters] = useState<NarrativeCluster[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [officialDocs, setOfficialDocs] = useState<OfficialDocument[]>([]);
  const [securityMetrics, setSecurityMetrics] = useState<SecurityMetrics | null>(null);
  const [securityEvents, setSecurityEvents] = useState<SecurityEvent[]>([]);
  const [ledgerResult, setLedgerResult] = useState<AuditLedgerResult | null>(null);
  const [graphData, setGraphData] = useState<NarrativeGraph | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Live Auto-Polling Toggle (default: 10s)
  const [isLivePolling, setIsLivePolling] = useState(true);
  const [pollingCountdown, setPollingCountdown] = useState(10);

  // Verification Review Action State
  const [selectedQueueItem, setSelectedQueueItem] = useState<QueueItem | null>(null);
  const [verificationDecision, setVerificationDecision] = useState<
    'VERIFIED' | 'CONTRADICTED' | 'INSUFFICIENT_EVIDENCE'
  >('CONTRADICTED');
  const [verificationNotes, setVerificationNotes] = useState<string>('');
  const [publicClarification, setPublicClarification] = useState<string>('');
  const [contradictingDocId, setContradictingDocId] = useState<string>('');
  const [actionSuccess, setActionSuccess] = useState<string | null>(null);
  const [isSubmittingDecision, setIsSubmittingDecision] = useState(false);

  // Draft Alert State
  const [alertTitle, setAlertTitle] = useState('');
  const [alertSummary, setAlertSummary] = useState('');
  const [alertClarification, setAlertClarification] = useState('');
  const [alertSeverity, setAlertSeverity] = useState('HIGH');
  const [alertScope, setAlertScope] = useState('NATIONAL');
  const [alertTargetState, setAlertTargetState] = useState('');
  const [isDraftingAlert, setIsDraftingAlert] = useState(false);

  // Alert Withdrawal Modal
  const [withdrawingAlertId, setWithdrawingAlertId] = useState<string | null>(null);
  const [withdrawalReason, setWithdrawalReason] = useState('');

  // Official Doc Register State
  const [docCode, setDocCode] = useState('');
  const [docTitle, setDocTitle] = useState('');
  const [docInstitution, setDocInstitution] = useState('Independent National Electoral Commission');
  const [docContent, setDocContent] = useState('');
  const [docSummary, setDocSummary] = useState('');
  const [isRegisteringDoc, setIsRegisteringDoc] = useState(false);

  // Narrative Cluster Inspection & Graph Filter
  const [inspectingCluster, setInspectingCluster] = useState<NarrativeCluster | null>(null);
  const [scanningNarratives, setScanningNarratives] = useState(false);
  const [selectedGraphNode, setSelectedGraphNode] = useState<GraphNode | null>(null);

  // Security Events & Ledger Verification
  const [verifyingLedger, setVerifyingLedger] = useState(false);
  const [resolvingEventId, setResolvingEventId] = useState<string | null>(null);
  const [resolutionNotes, setResolutionNotes] = useState('');

  // Fetch all institutional dashboard data
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
        graphRes,
      ] = await Promise.allSettled([
        api.get('/reports?limit=20'),
        api.get('/verification/queue?limit=50'),
        api.get('/narratives/clusters?limit=20'),
        api.get('/alerts/active?limit=20'),
        api.get('/registry/search?page_size=50'),
        api.get('/security/metrics'),
        api.get('/security/events?limit=20'),
        api.get('/narratives/graph'),
      ]);

      if (reportsRes.status === 'fulfilled') {
        const d = reportsRes.value.data.data;
        setReports(d?.items || d || []);
      }
      if (queueRes.status === 'fulfilled') {
        setQueueItems(queueRes.value.data.data || []);
      }
      if (clustersRes.status === 'fulfilled') {
        setClusters(clustersRes.value.data.data || []);
      }
      if (alertsRes.status === 'fulfilled') {
        setAlerts(alertsRes.value.data.data || []);
      }
      if (docsRes.status === 'fulfilled') {
        const d = docsRes.value.data.data;
        setOfficialDocs(d?.items || d || []);
      }
      if (metricsRes.status === 'fulfilled') {
        setSecurityMetrics(metricsRes.value.data.data);
      }
      if (eventsRes.status === 'fulfilled') {
        const d = eventsRes.value.data.data;
        setSecurityEvents(d?.items || d || []);
      }
      if (graphRes.status === 'fulfilled') {
        setGraphData(graphRes.value.data.data);
      }
    } catch (err) {
      console.error('Error fetching institutional dashboard data:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, []);

  // 10-Second Auto-refresh interval
  useEffect(() => {
    if (!isLivePolling) return;
    const timer = setInterval(() => {
      setPollingCountdown((prev) => {
        if (prev <= 1) {
          loadDashboardData();
          return 10;
        }
        return prev - 1;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [isLivePolling]);

  // Handle Recording Authoritative Decision in Verification Review Queue
  const handleRecordDecision = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedQueueItem) return;
    setIsSubmittingDecision(true);
    setActionSuccess(null);

    try {
      await api.post('/verification/decisions', {
        claim_id: selectedQueueItem.claim_id,
        decision: verificationDecision,
        justification_notes:
          verificationNotes || 'Official verification review executed against certified electoral gazettes.',
        public_clarification:
          publicClarification ||
          `Official review: This claim has been recorded as ${verificationDecision} based on verified documentation.`,
        official_document_id: contradictingDocId || undefined,
        evidence_sources_consulted: contradictingDocId ? [contradictingDocId] : [],
      });

      setActionSuccess(`Authoritative decision '${verificationDecision}' recorded for claim ${selectedQueueItem.claim_id}.`);
      setSelectedQueueItem(null);
      setVerificationNotes('');
      setPublicClarification('');
      setContradictingDocId('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to record decision');
    } finally {
      setIsSubmittingDecision(false);
    }
  };

  // Handle Drafting Early Warning Alert
  const handleDraftAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsDraftingAlert(true);
    try {
      await api.post('/alerts', {
        title: alertTitle,
        summary: alertSummary,
        full_clarification: alertClarification,
        severity: alertSeverity,
        category: 'CONFIRMED_MISINFORMATION',
        target_scope: alertScope,
        target_states: alertScope === 'STATE_SPECIFIC' && alertTargetState ? [alertTargetState] : [],
      });

      alert('Early warning draft created successfully! It now requires approval by a Lead Officer.');
      setAlertTitle('');
      setAlertSummary('');
      setAlertClarification('');
      setAlertTargetState('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to draft alert');
    } finally {
      setIsDraftingAlert(false);
    }
  };

  // Handle Dual-Key Approving Alert (Lead Officers / Admins)
  const handleApproveAlert = async (alertId: string) => {
    try {
      await api.post(`/alerts/${alertId}/approve`);
      alert('Alert approved and broadcast across citizen feeds and channels!');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to approve alert');
    }
  };

  // Handle Alert Withdrawal with Recorded Justification
  const handleWithdrawAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!withdrawingAlertId) return;
    try {
      await api.post(`/alerts/${withdrawingAlertId}/withdraw`, {
        withdrawal_reason: withdrawalReason,
      });
      alert('Alert withdrawn and marked superseded with official audit justification.');
      setWithdrawingAlertId(null);
      setWithdrawalReason('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to withdraw alert');
    }
  };

  // Handle Registering Official Document
  const handleRegisterDoc = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsRegisteringDoc(true);
    try {
      await api.post('/registry/documents', {
        document_code: docCode.trim().toUpperCase(),
        title: docTitle.trim(),
        issuing_institution: docInstitution.trim(),
        summary: docSummary.trim(),
        content_text: docContent.trim(),
      });

      alert('Official document authenticated and registered with SHA-256 hash!');
      setDocCode('');
      setDocTitle('');
      setDocContent('');
      setDocSummary('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to register document');
    } finally {
      setIsRegisteringDoc(false);
    }
  };

  // Trigger Narrative Pulse Discovery Scan
  const handleTriggerNarrativeScan = async () => {
    setScanningNarratives(true);
    try {
      const res = await api.post('/narratives/scan');
      alert(`Narrative scan completed! Formed or updated ${res.data.data.clusters_formed} cluster(s).`);
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to execute narrative scan');
    } finally {
      setScanningNarratives(false);
    }
  };

  // Inspect Cluster Details
  const handleInspectCluster = async (clusterId: string) => {
    try {
      const res = await api.get(`/narratives/clusters/${clusterId}`);
      setInspectingCluster(res.data.data);
    } catch (err) {
      console.error(err);
    }
  };

  // Handle Cryptographic Ledger Integrity Check
  const handleVerifyAuditLedger = async () => {
    setVerifyingLedger(true);
    try {
      const res = await api.post('/security/verify-ledger');
      setLedgerResult(res.data.data);
    } catch (err: any) {
      alert(err.response?.data?.message || 'Verification request failed');
    } finally {
      setVerifyingLedger(false);
    }
  };

  // Resolve Security Threat Event
  const handleResolveEvent = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resolvingEventId) return;
    try {
      await api.post(`/security/events/${resolvingEventId}/resolve`, {
        resolution_notes: resolutionNotes || 'Investigated by Security Officer. Threat neutralized.',
      });
      alert('Security incident resolved.');
      setResolvingEventId(null);
      setResolutionNotes('');
      loadDashboardData();
    } catch (err: any) {
      alert(err.response?.data?.message || 'Failed to resolve event');
    }
  };

  // Chart data formatting
  const clusterChartData = clusters.map((c) => ({
    name: (c.cluster_title || c.cluster_name || 'Cluster').slice(0, 16) + '...',
    reports: c.reports_count || 1,
    velocity: Math.round((c.velocity_score || 1) * 10),
  }));

  const queueByCategory = queueItems.reduce((acc: Record<string, number>, item) => {
    acc[item.category] = (acc[item.category] || 0) + 1;
    return acc;
  }, {});

  const queuePieData = Object.entries(queueByCategory).map(([key, value]) => ({
    name: key.replace(/_/g, ' '),
    value,
  }));

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
      {/* Top Header Bar */}
      <section aria-labelledby="command-title" className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-5 rounded-3xl shadow-xl text-white">
        <div className="flex items-center space-x-3.5">
          <div className="p-3 rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30">
            <BarChart3 className="w-6 h-6" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h1 id="command-title" className="text-xl font-bold">CivicShield Command Centre</h1>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono font-bold bg-blue-950 text-blue-300 border border-blue-800">
                OFFICER ACCESS
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Institutional Threat Intelligence, Human Verification Review Queue, &amp; Early Warning Broadcasting
            </p>
          </div>
        </div>

        {/* Live Auto-Refresh Status & Manual Refresh */}
        <div className="flex items-center space-x-3 text-xs">
          <button
            onClick={() => setIsLivePolling(!isLivePolling)}
            className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-xl border transition-all ${
              isLivePolling
                ? 'bg-emerald-950 text-emerald-300 border-emerald-800'
                : 'bg-slate-950 text-slate-400 border-slate-800'
            }`}
            title="Toggle live 10-second polling"
          >
            <span className={`w-2 h-2 rounded-full ${isLivePolling ? 'bg-emerald-400 animate-ping' : 'bg-slate-500'}`}></span>
            <span>{isLivePolling ? `Live (${pollingCountdown}s)` : 'Polling Paused'}</span>
          </button>

          <button
            onClick={loadDashboardData}
            disabled={isLoading}
            className="p-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition-colors"
            title="Refresh dashboard metrics"
            aria-label="Refresh data"
          >
            <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>
      </section>

      {/* Navigation Sub-Tabs */}
      <nav aria-label="Command sections" className="flex border-b border-slate-800 gap-2 overflow-x-auto pb-1" role="tablist">
        {[
          { key: 'overview', label: 'Threat Overview', icon: BarChart3, count: null },
          { key: 'queue', label: 'Verification Queue', icon: CheckSquare, count: queueItems.length },
          { key: 'narratives', label: 'Narrative Pulse', icon: Network, count: clusters.length },
          { key: 'registry', label: 'Certified Gazettes', icon: FileCheck2, count: officialDocs.length },
          { key: 'alerts', label: 'Early Warnings', icon: Radio, count: alerts.length },
          { key: 'security', label: 'Ledger & Security', icon: ShieldCheck, count: null },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeSection === tab.key;
          return (
            <button
              key={tab.key}
              role="tab"
              aria-selected={isActive}
              onClick={() => setActiveSection(tab.key as any)}
              className={`flex items-center space-x-2 px-4 py-3 rounded-xl text-xs sm:text-sm font-bold transition-all border-b-2 whitespace-nowrap ${
                isActive
                  ? 'border-blue-500 text-blue-400 bg-blue-950/40 shadow-sm'
                  : 'border-transparent text-slate-400 hover:text-white hover:bg-slate-900'
              }`}
            >
              <Icon className="w-4 h-4" />
              <span>{tab.label}</span>
              {tab.count !== null && (
                <span className="px-1.5 py-0.2 rounded-full text-[10px] bg-slate-800 text-slate-300 font-mono">
                  {tab.count}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* SECTION 1: THREAT INTELLIGENCE OVERVIEW */}
      {activeSection === 'overview' && (
        <section aria-labelledby="threat-overview-title" className="space-y-6">
          <h2 id="threat-overview-title" className="sr-only">Threat Intelligence Overview</h2>
          {/* KPI Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Triage Queue</span>
              <div className="text-2xl font-black text-amber-400">{queueItems.length}</div>
              <span className="text-[10px] text-slate-500">Claims awaiting officer sign-off</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Active Clusters</span>
              <div className="text-2xl font-black text-blue-400">{clusters.length}</div>
              <span className="text-[10px] text-slate-500">Coordinated narrative groups</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Broadcast Alerts</span>
              <div className="text-2xl font-black text-emerald-400">{alerts.length}</div>
              <span className="text-[10px] text-slate-500">Live dual-key advisories</span>
            </div>

            <div className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-1">
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400">Ledger Health</span>
              <div className="text-2xl font-black text-teal-400">
                {securityMetrics?.ledger_integrity_status || 'VERIFIED'}
              </div>
              <span className="text-[10px] text-slate-500 font-mono">
                {securityMetrics?.total_audit_records || 0} hash chained blocks
              </span>
            </div>
          </div>

          {/* Charts Row */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Propagation Velocity by Narrative Cluster */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">Narrative Cluster Velocity &amp; Reports</h3>
                  <p className="text-[11px] text-slate-400">Real-time propagation velocity score vs submission volume</p>
                </div>
                <TrendingUp className="w-4 h-4 text-emerald-400" />
              </div>

              <div className="h-64 w-full">
                {clusterChartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={clusterChartData}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                      <XAxis dataKey="name" stroke="#64748b" fontSize={11} />
                      <YAxis stroke="#64748b" fontSize={11} />
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                      />
                      <Bar dataKey="velocity" name="Velocity Index" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                      <Bar dataKey="reports" name="Reports" fill="#10b981" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                    No active narrative clusters to graph. Run discovery scan.
                  </div>
                )}
              </div>
            </div>

            {/* Pending Claims by Electoral Category */}
            <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-sm text-white">Verification Queue Taxonomy</h3>
                  <p className="text-[11px] text-slate-400">Distribution of unverified claims across electoral domains</p>
                </div>
                <Activity className="w-4 h-4 text-blue-400" />
              </div>

              <div className="h-64 w-full flex items-center justify-center">
                {queuePieData.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie
                        data={queuePieData}
                        dataKey="value"
                        nameKey="name"
                        cx="50%"
                        cy="50%"
                        outerRadius={80}
                        label={(entry) => entry.name}
                        labelLine={false}
                      >
                        {queuePieData.map((_, index) => (
                          <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                        ))}
                      </Pie>
                      <Tooltip
                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', borderRadius: '12px' }}
                      />
                    </PieChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="text-slate-500 text-xs">Queue is clear! Zero claims pending triage.</div>
                )}
              </div>
            </div>
          </div>
        </section>
      )}

      {/* SECTION 2: HUMAN-IN-THE-LOOP VERIFICATION REVIEW QUEUE */}
      {activeSection === 'queue' && (
        <section aria-labelledby="verification-queue-title" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <h2 id="verification-queue-title" className="sr-only">Verification Queue Review</h2>
          {/* Left Column: Queue Items List (7 cols) */}
          <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-base text-white">Claims Awaiting Verification ({queueItems.length})</h3>
                <p className="text-xs text-slate-400">
                  Prioritized by report urgency, AI contradiction indicators, and affected Nigerian state.
                </p>
              </div>
            </div>

            <div className="space-y-3 max-h-[600px] overflow-y-auto pr-1">
              {queueItems.length === 0 ? (
                <div className="text-center py-16 text-slate-500 text-xs">
                  All ingested claims have received human verification review.
                </div>
              ) : (
                queueItems.map((item) => {
                  const isSelected = selectedQueueItem?.claim_id === item.claim_id;
                  return (
                    <div
                      key={item.claim_id}
                      onClick={() => setSelectedQueueItem(item)}
                      className={`p-4 rounded-2xl border transition-all cursor-pointer space-y-2.5 ${
                        isSelected
                          ? 'bg-blue-950/60 border-blue-500 shadow-md'
                          : 'bg-slate-950 border-slate-800 hover:border-slate-700'
                      }`}
                      role="button"
                      tabIndex={0}
                    >
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-mono font-bold text-emerald-400">{item.report_reference}</span>
                        <div className="flex items-center space-x-1.5">
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800 uppercase">
                            {item.report_priority}
                          </span>
                          <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-slate-900 text-slate-400 border border-slate-800">
                            {item.nigerian_state || 'National'}
                          </span>
                        </div>
                      </div>

                      <h4 className="text-xs font-bold text-white leading-relaxed">{item.claim_text}</h4>

                      {item.ai_analysis_summary && (
                        <p className="text-[11px] text-slate-300 italic bg-black/30 p-2 rounded-lg border border-slate-800/60">
                          AI Observation: {item.ai_analysis_summary}
                        </p>
                      )}

                      <div className="flex items-center justify-between text-[10px] text-slate-500 pt-1">
                        <span>Category: <strong className="text-slate-300">{item.category}</strong></span>
                        <span>AI Suggestion: <strong className="text-amber-400">{item.ai_suggested_status}</strong></span>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Right Column: Binding Decision Form (5 cols) */}
          <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl h-fit">
            <h3 className="font-bold text-base text-white">Record Authoritative Decision</h3>

            {actionSuccess && (
              <div className="p-3.5 rounded-xl bg-emerald-950 border border-emerald-700 text-emerald-200 text-xs flex items-center space-x-2">
                <Check className="w-4 h-4 text-emerald-400 flex-shrink-0" />
                <span>{actionSuccess}</span>
              </div>
            )}

            {selectedQueueItem ? (
              <form onSubmit={handleRecordDecision} className="space-y-4">
                <div className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1">
                  <span className="text-[10px] font-mono text-slate-400 uppercase block">Selected Claim</span>
                  <p className="text-xs text-white font-semibold">{selectedQueueItem.claim_text}</p>
                  <span className="text-[10px] text-slate-500 block font-mono">Ref: {selectedQueueItem.report_reference}</span>
                </div>

                {/* Binding Decision Selector */}
                <div>
                  <label htmlFor="binding-decision-select" className="block text-xs font-bold text-slate-300 mb-1">
                    Formal Binding Verdict *
                  </label>
                  <select
                    id="binding-decision-select"
                    value={verificationDecision}
                    onChange={(e) => setVerificationDecision(e.target.value as any)}
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500 font-bold"
                  >
                    <option value="CONTRADICTED">CONTRADICTED (Confirmed False / Fabricated)</option>
                    <option value="VERIFIED">VERIFIED (Confirmed True by Gazette)</option>
                    <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT_EVIDENCE (Cannot Prove/Disprove)</option>
                  </select>
                </div>

                {/* Gazette Citation Picker */}
                <div>
                  <label htmlFor="citation-doc-select" className="block text-xs font-bold text-slate-300 mb-1">
                    Cite Certified Official Gazette
                  </label>
                  <select
                    id="citation-doc-select"
                    value={contradictingDocId}
                    onChange={(e) => setContradictingDocId(e.target.value)}
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="">None / External Certified Investigation</option>
                    {officialDocs.map((doc) => (
                      <option key={doc.id} value={doc.id}>
                        {doc.document_code} - {doc.title.slice(0, 45)}...
                      </option>
                    ))}
                  </select>
                </div>

                {/* Institutional Officer Notes */}
                <div>
                  <label htmlFor="officer-notes-area" className="block text-xs font-bold text-slate-300 mb-1">
                    Officer Justification &amp; Evidence Rationale *
                  </label>
                  <textarea
                    id="officer-notes-area"
                    rows={3}
                    required
                    minLength={15}
                    value={verificationNotes}
                    onChange={(e) => setVerificationNotes(e.target.value)}
                    placeholder="Institutional reasoning citing verified gazettes, INEC press releases, or field liaison findings..."
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                {/* Public Clarification Note */}
                <div>
                  <label htmlFor="public-clarification-area" className="block text-xs font-bold text-slate-300 mb-1">
                    Public Clarification Note (For Citizen Portal) *
                  </label>
                  <textarea
                    id="public-clarification-area"
                    rows={2}
                    required
                    minLength={15}
                    value={publicClarification}
                    onChange={(e) => setPublicClarification(e.target.value)}
                    placeholder="Plain-language explanation published to citizens tracking this claim..."
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmittingDecision}
                  className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-lg transition-all flex items-center justify-center space-x-1.5"
                >
                  <CheckCircle className="w-4 h-4" />
                  <span>{isSubmittingDecision ? 'Recording Finding...' : 'Confirm Binding Decision'}</span>
                </button>
              </form>
            ) : (
              <div className="text-center py-16 text-slate-500 text-xs">
                Select an item from the queue to examine evidence and execute an authoritative decision.
              </div>
            )}
          </div>
        </section>
      )}

      {/* SECTION 3: FLAGSHIP NARRATIVE PULSE & NETWORK RELATIONSHIP GRAPH */}
      {activeSection === 'narratives' && (
        <section aria-labelledby="narrative-pulse-title" className="space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-900 border border-slate-800 p-6 rounded-3xl shadow-xl">
            <div>
              <div className="flex items-center space-x-2">
                <Network className="w-5 h-5 text-blue-400" />
                <h2 id="narrative-pulse-title" className="text-xl font-bold text-white">Narrative Pulse Intelligence</h2>
              </div>
              <p className="text-xs text-slate-400 mt-1">
                Real-time semantic clustering and propagation velocity tracking across the 36 Nigerian States + FCT.
              </p>
            </div>

            <button
              onClick={handleTriggerNarrativeScan}
              disabled={scanningNarratives}
              className="px-4 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow transition-all flex items-center space-x-2"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${scanningNarratives ? 'animate-spin' : ''}`} />
              <span>{scanningNarratives ? 'Scanning Stream...' : 'Run Discovery Scan'}</span>
            </button>
          </div>

          {/* Mandatory Ethical Invariant Banner */}
          <aside aria-label="Ethical invariant notice" className="p-4 rounded-2xl bg-slate-900/90 border border-slate-800 text-slate-400 text-xs flex items-start space-x-3">
            <Info className="w-5 h-5 text-amber-400 flex-shrink-0 mt-0.5" />
            <div className="leading-relaxed">
              <strong>Mandatory Ethical Principle (Section 7, Rule 5):</strong> Similar reports clustered in Narrative Pulse do <em>not</em> inherently prove coordinated disinformation, malicious intent, or common authorship. Clusters represent narrative recurrence, not criminal attribution.
            </div>
          </aside>

          {/* Network Relationship Graph Visualization Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-bold text-sm text-white">Narrative Relationship Graph</h3>
                <p className="text-xs text-slate-400">
                  Network edges indicate high text similarity or identical cryptographic media fingerprints across submissions.
                </p>
              </div>
              {graphData && (
                <div className="flex items-center space-x-3 text-xs font-mono text-slate-400">
                  <span>Nodes: <strong className="text-white">{graphData.nodes.length}</strong></span>
                  <span>Edges: <strong className="text-emerald-400">{graphData.edges.length}</strong></span>
                </div>
              )}
            </div>

            {/* Interactive SVG Network Graph Rendering */}
            <div className="relative w-full h-80 rounded-2xl bg-slate-950 border border-slate-800 overflow-hidden flex items-center justify-center p-4">
              {graphData && graphData.nodes.length > 0 ? (
                <svg className="w-full h-full" viewBox="0 0 800 300">
                  {/* Edges */}
                  {graphData.edges.map((edge, idx) => {
                    // Coordinate placement heuristics
                    const sourceIdx = graphData.nodes.findIndex((n) => n.id === edge.source);
                    const targetIdx = graphData.nodes.findIndex((n) => n.id === edge.target);
                    const x1 = 100 + ((sourceIdx * 120) % 650);
                    const y1 = 60 + ((sourceIdx * 70) % 200);
                    const x2 = 120 + ((targetIdx * 130) % 650);
                    const y2 = 80 + ((targetIdx * 80) % 200);

                    return (
                      <line
                        key={idx}
                        x1={x1}
                        y1={y1}
                        x2={x2}
                        y2={y2}
                        stroke="#334155"
                        strokeWidth={Math.max(1, edge.weight * 3)}
                        strokeDasharray="4 2"
                      />
                    );
                  })}

                  {/* Nodes */}
                  {graphData.nodes.map((node, idx) => {
                    const cx = 100 + ((idx * 120) % 650);
                    const cy = 60 + ((idx * 70) % 200);
                    const isCluster = node.type === 'CLUSTER';
                    const isSelected = selectedGraphNode?.id === node.id;

                    return (
                      <g
                        key={node.id}
                        onClick={() => setSelectedGraphNode(node)}
                        className="cursor-pointer transition-transform hover:scale-110"
                      >
                        <circle
                          cx={cx}
                          cy={cy}
                          r={isCluster ? 18 : 10}
                          fill={isCluster ? '#3b82f6' : '#10b981'}
                          stroke={isSelected ? '#facc15' : '#ffffff'}
                          strokeWidth={isSelected ? 3 : 1.5}
                        />
                        <text
                          x={cx}
                          y={cy + (isCluster ? 30 : 22)}
                          fontSize="10"
                          fill="#94a3b8"
                          textAnchor="middle"
                          className="font-mono"
                        >
                          {node.label.slice(0, 18)}
                        </text>
                      </g>
                    );
                  })}
                </svg>
              ) : (
                <div className="text-center text-slate-500 text-xs">
                  Network graph will render when at least two correlated reports are ingested and scanned.
                </div>
              )}
            </div>

            {selectedGraphNode && (
              <div className="p-3.5 rounded-xl bg-slate-950 border border-blue-500/50 text-xs flex items-center justify-between">
                <div>
                  <span className="font-bold text-white uppercase">{selectedGraphNode.type} Node: </span>
                  <span className="text-slate-300">{selectedGraphNode.label}</span>
                </div>
                <button
                  onClick={() => setSelectedGraphNode(null)}
                  className="text-slate-400 hover:text-white"
                  aria-label="Close details"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>

          {/* Active Narrative Clusters List */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {clusters.map((cluster) => (
              <div
                key={cluster.id}
                className="p-5 rounded-2xl bg-slate-900 border border-slate-800 space-y-3.5 hover:border-slate-700 transition-all cursor-pointer"
                onClick={() => handleInspectCluster(cluster.id)}
                role="button"
                tabIndex={0}
              >
                <div className="flex items-center justify-between gap-2">
                  <h4 className="font-bold text-sm text-white truncate">
                    {cluster.cluster_title || cluster.cluster_name}
                  </h4>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold bg-blue-950 text-blue-300 border border-blue-800 uppercase whitespace-nowrap">
                    {cluster.amplification_pattern}
                  </span>
                </div>

                <p className="text-xs text-slate-300 italic leading-relaxed">
                  "{cluster.summary || cluster.core_narrative}"
                </p>

                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 block">Reports</span>
                    <strong className="text-white text-sm">{cluster.reports_count || 1}</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 block">Velocity</span>
                    <strong className="text-emerald-400 text-sm">
                      {(cluster.velocity_score || 1).toFixed(1)}x
                    </strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-slate-950 border border-slate-800/80">
                    <span className="text-[10px] text-slate-400 block">States</span>
                    <strong className="text-white text-sm">
                      {cluster.geographic_scope?.length || 1}
                    </strong>
                  </div>
                </div>

                {cluster.geographic_scope && cluster.geographic_scope.length > 0 && (
                  <div className="text-[11px] text-slate-400">
                    Geographic Spread: <span className="text-slate-200">{cluster.geographic_scope.join(', ')}</span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {/* Cluster Detailed Inspection Modal / Drawer */}
          {inspectingCluster && (
            <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 max-w-2xl w-full max-h-[85vh] overflow-y-auto space-y-5 shadow-2xl">
                <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                  <h3 className="font-bold text-lg text-white">
                    {inspectingCluster.cluster_title || inspectingCluster.cluster_name}
                  </h3>
                  <button
                    onClick={() => setInspectingCluster(null)}
                    className="p-1 rounded-lg text-slate-400 hover:text-white"
                    aria-label="Close cluster inspection"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <p className="text-xs text-slate-300 leading-relaxed italic">
                  "{inspectingCluster.summary || inspectingCluster.core_narrative}"
                </p>

                {/* Technical Threat Indicators */}
                {inspectingCluster.threat_indicators && inspectingCluster.threat_indicators.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Technical Threat Indicators
                    </h4>
                    <div className="space-y-2">
                      {inspectingCluster.threat_indicators.map((ind) => (
                        <div key={ind.id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 space-y-1 text-xs">
                          <span className="font-bold text-rose-400 uppercase font-mono">{ind.indicator_type}</span>
                          <p className="text-slate-300 text-[11px]">{ind.evidence_detail}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Constituent Reports */}
                {inspectingCluster.cluster_reports && inspectingCluster.cluster_reports.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wide">
                      Constituent Citizen Reports
                    </h4>
                    <div className="space-y-2">
                      {inspectingCluster.cluster_reports.map((cr) => (
                        <div key={cr.report_id} className="p-3 rounded-xl bg-slate-950 border border-slate-800 flex items-center justify-between text-xs">
                          <div>
                            <span className="font-mono text-emerald-400 font-bold">{cr.reference_number}</span>
                            <p className="text-slate-300 mt-0.5">{cr.title}</p>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] bg-slate-900 border border-slate-800 text-slate-400">
                            State: {cr.nigerian_state || 'National'}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </section>
      )}

      {/* SECTION 4: OFFICIAL GAZETTES REGISTRATION */}
      {activeSection === 'registry' && (
        <section aria-labelledby="official-registry-title" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <h2 id="official-registry-title" className="sr-only">Official Gazettes Registration</h2>
          {/* Register Document Form (5 cols) */}
          <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl h-fit">
            <h3 className="font-bold text-base text-white">Certify Official Gazette</h3>
            <p className="text-xs text-slate-400">
              Only authorized officers may publish authenticated notices with canonical SHA-256 fingerprints.
            </p>

            <form onSubmit={handleRegisterDoc} className="space-y-3.5">
              <div>
                <label htmlFor="certify-doc-code" className="block text-xs font-bold text-slate-300 mb-1">Document Code *</label>
                <input
                  id="certify-doc-code"
                  type="text"
                  required
                  value={docCode}
                  onChange={(e) => setDocCode(e.target.value)}
                  placeholder="INEC-2026-PRESS-05"
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-blue-500 uppercase"
                />
              </div>

              <div>
                <label htmlFor="certify-doc-title" className="block text-xs font-bold text-slate-300 mb-1">Title *</label>
                <input
                  id="certify-doc-title"
                  type="text"
                  required
                  value={docTitle}
                  onChange={(e) => setDocTitle(e.target.value)}
                  placeholder="Official Rebuttal on Polling Center Relocations"
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="certify-doc-institution" className="block text-xs font-bold text-slate-300 mb-1">Issuing Authority</label>
                <input
                  id="certify-doc-institution"
                  type="text"
                  value={docInstitution}
                  onChange={(e) => setDocInstitution(e.target.value)}
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="certify-doc-summary" className="block text-xs font-bold text-slate-300 mb-1">Summary *</label>
                <input
                  id="certify-doc-summary"
                  type="text"
                  required
                  value={docSummary}
                  onChange={(e) => setDocSummary(e.target.value)}
                  placeholder="Executive summary of the official announcement..."
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="certify-doc-content" className="block text-xs font-bold text-slate-300 mb-1">Full Document Text *</label>
                <textarea
                  id="certify-doc-content"
                  rows={4}
                  required
                  value={docContent}
                  onChange={(e) => setDocContent(e.target.value)}
                  placeholder="Verbatim text of the announcement for SHA-256 fingerprinting..."
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs font-mono text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isRegisteringDoc}
                className="w-full py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center space-x-1.5"
              >
                <FileCheck2 className="w-4 h-4" />
                <span>{isRegisteringDoc ? 'Computing Hash...' : 'Certify & Register Document'}</span>
              </button>
            </form>
          </div>

          {/* Existing Certified Records (7 cols) */}
          <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
            <h3 className="font-bold text-base text-white">Certified Repository Records ({officialDocs.length})</h3>
            <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
              {officialDocs.map((doc) => (
                <div key={doc.id} className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-1.5">
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-mono font-bold text-emerald-400">{doc.document_code}</span>
                    <span className="text-slate-500 text-[10px] font-mono">
                      v{doc.current_version} • {doc.publication_date ? new Date(doc.publication_date).toLocaleDateString() : 'Active'}
                    </span>
                  </div>
                  <h4 className="font-bold text-xs text-white">{doc.title}</h4>
                  <p className="text-[11px] text-slate-400">{doc.summary}</p>
                  <div className="text-[10px] font-mono text-slate-500 break-all pt-1 border-t border-slate-900">
                    SHA-256: {doc.sha256_hash}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* SECTION 5: EARLY WARNING BROADCAST CENTRE (DUAL-KEY PROTOCOL) */}
      {activeSection === 'alerts' && (
        <section aria-labelledby="early-warnings-title" className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <h2 id="early-warnings-title" className="sr-only">Early Warning Broadcast Centre</h2>
          {/* Draft Alert Form (5 cols) */}
          <div className="lg:col-span-5 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl h-fit">
            <div className="flex items-center space-x-2">
              <Radio className="w-5 h-5 text-rose-400" />
              <h3 className="font-bold text-base text-white">Draft Early Warning Advisory</h3>
            </div>
            <p className="text-xs text-slate-400">
              Dual-Key Security Protocol: Analysts draft advisories; broadcast requires sign-off by a Lead Verification Officer.
            </p>

            <form onSubmit={handleDraftAlert} className="space-y-3.5">
              <div>
                <label htmlFor="advisory-title-input" className="block text-xs font-bold text-slate-300 mb-1">Advisory Headline *</label>
                <input
                  id="advisory-title-input"
                  type="text"
                  required
                  value={alertTitle}
                  onChange={(e) => setAlertTitle(e.target.value)}
                  placeholder="e.g. Debunk of False Postponement Circular in Kano"
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label htmlFor="advisory-severity-select" className="block text-xs font-bold text-slate-300 mb-1">Severity *</label>
                  <select
                    id="advisory-severity-select"
                    value={alertSeverity}
                    onChange={(e) => setAlertSeverity(e.target.value)}
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="CRITICAL">CRITICAL</option>
                    <option value="HIGH">HIGH</option>
                    <option value="MEDIUM">MEDIUM</option>
                    <option value="INFORMATIONAL">INFORMATIONAL</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="advisory-scope-select" className="block text-xs font-bold text-slate-300 mb-1">Target Scope *</label>
                  <select
                    id="advisory-scope-select"
                    value={alertScope}
                    onChange={(e) => setAlertScope(e.target.value)}
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  >
                    <option value="NATIONAL">NATIONAL</option>
                    <option value="STATE_SPECIFIC">STATE_SPECIFIC</option>
                  </select>
                </div>
              </div>

              {alertScope === 'STATE_SPECIFIC' && (
                <div>
                  <label htmlFor="advisory-state-input" className="block text-xs font-bold text-slate-300 mb-1">Target Nigerian State *</label>
                  <input
                    id="advisory-state-input"
                    type="text"
                    required
                    value={alertTargetState}
                    onChange={(e) => setAlertTargetState(e.target.value)}
                    placeholder="e.g. Kano"
                    className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                  />
                </div>
              )}

              <div>
                <label htmlFor="advisory-summary-input" className="block text-xs font-bold text-slate-300 mb-1">Short Broadcast Summary *</label>
                <input
                  id="advisory-summary-input"
                  type="text"
                  required
                  value={alertSummary}
                  onChange={(e) => setAlertSummary(e.target.value)}
                  placeholder="Brief summary displayed on mobile ticker and citizen alerts..."
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <div>
                <label htmlFor="advisory-clarification-area" className="block text-xs font-bold text-slate-300 mb-1">Full Clarification &amp; Evidence *</label>
                <textarea
                  id="advisory-clarification-area"
                  rows={4}
                  required
                  value={alertClarification}
                  onChange={(e) => setAlertClarification(e.target.value)}
                  placeholder="Official debunk narrative, gazette reference citations, and electoral instructions..."
                  className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                />
              </div>

              <button
                type="submit"
                disabled={isDraftingAlert}
                className="w-full py-3.5 rounded-xl bg-blue-600 hover:bg-blue-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-md transition-all flex items-center justify-center space-x-1.5"
              >
                <Send className="w-4 h-4" />
                <span>{isDraftingAlert ? 'Drafting Advisory...' : 'Draft Early Warning (Pending Dual-Key Sign-Off)'}</span>
              </button>
            </form>
          </div>

          {/* Active & Pending Early Warnings (7 cols) */}
          <div className="lg:col-span-7 bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
            <h3 className="font-bold text-base text-white">Advisories &amp; Active Broadcasts ({alerts.length})</h3>
            <div className="space-y-3 max-h-[580px] overflow-y-auto pr-1">
              {alerts.length === 0 ? (
                <div className="text-center py-16 text-slate-500 text-xs">
                  Zero active early warning alerts circulating.
                </div>
              ) : (
                alerts.map((al) => (
                  <div key={al.id} className="p-4 rounded-2xl bg-slate-950 border border-slate-800 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-mono text-emerald-400 font-bold">{al.alert_reference}</span>
                      <div className="flex items-center space-x-2">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-bold ${
                            al.severity === 'CRITICAL'
                              ? 'bg-rose-950 text-rose-300 border border-rose-800'
                              : 'bg-amber-950 text-amber-300 border border-amber-800'
                          }`}
                        >
                          {al.severity}
                        </span>
                        <span className="text-[10px] text-slate-400 font-mono">
                          {al.target_scope === 'STATE_SPECIFIC' ? (al.target_states?.join(', ') || al.target_state) : 'NATIONAL'}
                        </span>
                      </div>
                    </div>

                    <h4 className="font-bold text-xs text-white">{al.title}</h4>
                    <p className="text-[11px] text-slate-300 leading-relaxed">{al.summary}</p>

                    <div className="pt-2 flex flex-wrap items-center justify-between gap-2 text-xs border-t border-slate-800">
                      <span className="text-[10px] font-mono text-slate-400">Status: {al.status}</span>
                      <div className="flex items-center space-x-2">
                        {al.status === 'PENDING_APPROVAL' && (
                          <button
                            onClick={() => handleApproveAlert(al.id)}
                            className="px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold shadow"
                          >
                            Dual-Key Sign-Off &amp; Broadcast
                          </button>
                        )}
                        {al.status === 'PUBLISHED' && (
                          <button
                            onClick={() => setWithdrawingAlertId(al.id)}
                            className="px-2.5 py-1 rounded-lg bg-rose-950 hover:bg-rose-900 text-rose-300 border border-rose-800 text-[11px] font-semibold"
                          >
                            Withdraw Advisory
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Withdraw Alert Justification Modal */}
          {withdrawingAlertId && (
            <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 max-w-md w-full space-y-4 shadow-2xl">
                <h3 className="font-bold text-base text-white">Withdraw Active Advisory</h3>
                <p className="text-xs text-slate-400">
                  Mandatory justification rule: Provide the official rationale for superseding or retracting this early warning.
                </p>

                <form onSubmit={handleWithdrawAlert} className="space-y-4">
                  <div>
                    <label htmlFor="withdrawal-reason-area" className="block text-xs font-bold text-slate-300 mb-1">
                      Withdrawal Reason *
                    </label>
                    <textarea
                      id="withdrawal-reason-area"
                      rows={3}
                      required
                      minLength={10}
                      value={withdrawalReason}
                      onChange={(e) => setWithdrawalReason(e.target.value)}
                      placeholder="e.g. Rebuttal verified; situation de-escalated and polling centers opened on schedule..."
                      className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-rose-500"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setWithdrawingAlertId(null)}
                      className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 rounded-xl bg-rose-600 hover:bg-rose-500 text-white text-xs font-bold"
                    >
                      Confirm Withdrawal
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </section>
      )}

      {/* SECTION 6: CRYPTOGRAPHIC LEDGER AUDIT & THREAT INCIDENTS */}
      {activeSection === 'security' && (
        <section aria-labelledby="ledger-security-title" className="space-y-6">
          <h2 id="ledger-security-title" className="sr-only">Cryptographic Ledger &amp; Security Events</h2>
          {/* Tamper-Evident SHA-256 Ledger Card */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-5 shadow-xl">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div>
                <div className="flex items-center space-x-2">
                  <ShieldCheck className="w-5 h-5 text-teal-400" />
                  <h3 className="font-bold text-base text-white">Cryptographic SHA-256 Tamper-Evident Ledger</h3>
                </div>
                <p className="text-xs text-slate-400 mt-1">
                  Every state change (verification decisions, alert broadcasts, document registrations) appends an immutable hash block chained to genesis.
                </p>
              </div>

              <button
                onClick={handleVerifyAuditLedger}
                disabled={verifyingLedger}
                className="px-5 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 disabled:bg-slate-800 text-white font-bold text-xs shadow-md transition-all flex items-center space-x-2"
              >
                <ShieldCheck className="w-4 h-4" />
                <span>{verifyingLedger ? 'Traversing SHA-256 Chain...' : 'Verify Cryptographic Ledger'}</span>
              </button>
            </div>

            {ledgerResult && (
              <div
                className={`p-5 rounded-2xl border space-y-3 animate-fadeIn ${
                  ledgerResult.is_valid
                    ? 'bg-emerald-950/80 border-emerald-700 text-emerald-200'
                    : 'bg-rose-950/80 border-rose-700 text-rose-200'
                }`}
              >
                <div className="flex items-center space-x-2.5 font-bold text-sm">
                  {ledgerResult.is_valid ? (
                    <CheckCircle className="w-5 h-5 text-emerald-400" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-rose-400" />
                  )}
                  <span>{ledgerResult.verification_message}</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs font-mono pt-2 border-t border-white/10">
                  <div>
                    <span className="text-[10px] text-slate-400 block">Verified Chain Length</span>
                    <strong>{ledgerResult.total_entries_verified} Blocks</strong>
                  </div>
                  {ledgerResult.first_verified_hash && (
                    <div className="truncate">
                      <span className="text-[10px] text-slate-400 block">Genesis Hash</span>
                      <span className="truncate">{ledgerResult.first_verified_hash.slice(0, 20)}...</span>
                    </div>
                  )}
                  {ledgerResult.latest_verified_hash && (
                    <div className="truncate">
                      <span className="text-[10px] text-slate-400 block">Latest Block Hash</span>
                      <span className="truncate">{ledgerResult.latest_verified_hash.slice(0, 20)}...</span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Technical Security Threat Events */}
          <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 space-y-4 shadow-xl">
            <h3 className="font-bold text-base text-white">Technical Security Incidents ({securityEvents.length})</h3>
            <div className="space-y-3">
              {securityEvents.length === 0 ? (
                <div className="text-center py-10 text-slate-500 text-xs">
                  Zero active security incidents recorded. System perimeter secure.
                </div>
              ) : (
                securityEvents.map((ev) => (
                  <div
                    key={ev.id}
                    className="p-4 rounded-2xl bg-slate-950 border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
                  >
                    <div>
                      <div className="flex items-center space-x-2">
                        <span className="font-bold text-white uppercase">{ev.event_type}</span>
                        <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-rose-950 text-rose-300 border border-rose-800">
                          {ev.severity}
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            ev.resolved ? 'bg-emerald-950 text-emerald-400' : 'bg-amber-950 text-amber-400'
                          }`}
                        >
                          {ev.resolved ? 'RESOLVED' : 'OPEN'}
                        </span>
                      </div>
                      <p className="text-slate-400 text-[11px] mt-1">
                        Target: {ev.user_identifier || ev.ip_address || 'System Internal'} • Recorded: {new Date(ev.created_at).toLocaleString()}
                      </p>
                    </div>

                    {!ev.resolved && (
                      <button
                        onClick={() => setResolvingEventId(ev.id)}
                        className="px-3 py-1.5 rounded-lg bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs"
                      >
                        Resolve Incident
                      </button>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Resolve Incident Modal */}
          {resolvingEventId && (
            <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
              <div className="bg-slate-900 border border-slate-800 rounded-3xl p-6 sm:p-8 max-w-md w-full space-y-4 shadow-2xl">
                <h3 className="font-bold text-base text-white">Resolve Security Incident</h3>
                <form onSubmit={handleResolveEvent} className="space-y-4">
                  <div>
                    <label htmlFor="resolution-notes-area" className="block text-xs font-bold text-slate-300 mb-1">
                      Officer Resolution Notes *
                    </label>
                    <textarea
                      id="resolution-notes-area"
                      rows={3}
                      required
                      value={resolutionNotes}
                      onChange={(e) => setResolutionNotes(e.target.value)}
                      placeholder="Detail actions taken to investigate and neutralize the incident..."
                      className="w-full p-3 bg-slate-950 border border-slate-800 rounded-xl text-xs text-white focus:outline-none focus:border-blue-500"
                    />
                  </div>

                  <div className="flex justify-end space-x-2">
                    <button
                      type="button"
                      onClick={() => setResolvingEventId(null)}
                      className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 text-xs font-semibold"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="px-4 py-2 rounded-xl bg-blue-600 hover:bg-blue-500 text-white text-xs font-bold"
                    >
                      Record Resolution
                    </button>
                  </div>
                </form>
              </div>
            </div>
          )}
        </section>
      )}
    </div>
  );
};
