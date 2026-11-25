import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { AccessibilityProvider, useAccessibility } from './context/AccessibilityContext';
import { Navbar } from './components/common/Navbar';
import { AlertBanner } from './components/common/AlertBanner';
import { AuthModal } from './components/common/AuthModal';
import { CitizenHome } from './components/citizen/CitizenHome';
import { CommandDashboard } from './components/command/CommandDashboard';
import { Shield, Lock } from 'lucide-react';

const AppContent: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const { t } = useAccessibility();
  const [currentView, setCurrentView] = useState<'citizen' | 'command'>('citizen');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const isInstitutionalUser = user?.roles?.some((r) =>
    ['ANALYST', 'VERIFICATION_OFFICER', 'SECURITY_OFFICER', 'ADMINISTRATOR'].includes(r)
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col font-sans antialiased">
      {/* Top Navigation with Accessibility Controls */}
      <Navbar
        currentView={currentView}
        onViewChange={(view) => {
          if (view === 'command' && (!isAuthenticated || !isInstitutionalUser)) {
            setIsAuthModalOpen(true);
            return;
          }
          setCurrentView(view);
        }}
        onOpenAuthModal={() => setIsAuthModalOpen(true)}
      />

      {/* Real-time Early Warning Alert Banner with TTS */}
      <AlertBanner />

      {/* Main Content Area */}
      <main className="flex-1" id="main-content">
        {currentView === 'citizen' && <CitizenHome />}

        {currentView === 'command' && (
          <>
            {isAuthenticated && isInstitutionalUser ? (
              <CommandDashboard />
            ) : (
              <div className="max-w-md mx-auto my-20 p-8 bg-slate-900 border border-slate-800 rounded-3xl text-center space-y-4 shadow-2xl">
                <div className="w-12 h-12 rounded-2xl bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto">
                  <Lock className="w-6 h-6" />
                </div>
                <h2 className="text-lg font-bold text-white">Institutional Access Required</h2>
                <p className="text-xs text-slate-400 leading-relaxed">
                  The CivicShield Command Centre is restricted to authorized Verification Officers, Analysts, and Security Administrators.
                </p>
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  className="px-6 py-3 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow-lg transition-all"
                >
                  Sign In with Officer Credentials
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Global Civic Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-xs text-slate-500" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span className="font-bold text-slate-300">CivicShield NG</span>
            <span>&mdash; Non-Partisan Electoral Truth &amp; Intelligence Platform</span>
          </div>
          <div className="flex flex-wrap items-center space-x-3 text-[11px] text-slate-500">
            <span>Federal Republic of Nigeria</span>
            <span>&bull;</span>
            <span>Cryptographic SHA-256 Ledger</span>
            <span>&bull;</span>
            <span>Salted IP Privacy (Zero-PII)</span>
            <span>&bull;</span>
            <span className="text-amber-400/80">Demonstration Simulated Data</span>
          </div>
        </div>
      </footer>

      {/* Authentication Modal */}
      <AuthModal isOpen={isAuthModalOpen} onClose={() => setIsAuthModalOpen(false)} />
    </div>
  );
};

export default function App() {
  return (
    <AuthProvider>
      <AccessibilityProvider>
        <AppContent />
      </AccessibilityProvider>
    </AuthProvider>
  );
}
