import React, { useState } from 'react';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Navbar } from './components/common/Navbar';
import { AlertBanner } from './components/common/AlertBanner';
import { AuthModal } from './components/common/AuthModal';
import { CitizenHome } from './components/citizen/CitizenHome';
import { CommandDashboard } from './components/command/CommandDashboard';
import { Shield, Lock } from 'lucide-react';

const AppContent: React.FC = () => {
  const { user, isAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<'citizen' | 'command'>('citizen');
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  const isInstitutionalUser = user?.roles.some((r) =>
    ['ANALYST', 'VERIFICATION_OFFICER', 'SECURITY_OFFICER', 'ADMINISTRATOR'].includes(r)
  );

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col">
      {/* Top Navigation */}
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

      {/* Real-time Early Warning Alert Banner */}
      <AlertBanner />

      {/* Main Content Area */}
      <main className="flex-1">
        {currentView === 'citizen' && <CitizenHome />}

        {currentView === 'command' && (
          <>
            {isAuthenticated && isInstitutionalUser ? (
              <CommandDashboard />
            ) : (
              <div className="max-w-md mx-auto my-20 p-8 bg-slate-900 border border-slate-800 rounded-2xl text-center space-y-4">
                <div className="w-12 h-12 rounded-full bg-blue-600/20 text-blue-400 border border-blue-500/30 flex items-center justify-center mx-auto">
                  <Lock className="w-6 h-6" />
                </div>
                <h2 className="text-lg font-bold text-white">Institutional Access Required</h2>
                <p className="text-xs text-slate-400">
                  The CivicShield Command Centre is restricted to authorized Verification Officers, Analysts, and Security Administrators.
                </p>
                <button
                  onClick={() => setIsAuthModalOpen(true)}
                  className="px-5 py-2.5 rounded-xl bg-blue-600 hover:bg-blue-500 text-white font-bold text-xs shadow transition-all"
                >
                  Sign In with Officer Credentials
                </button>
              </div>
            )}
          </>
        )}
      </main>

      {/* Global Footer */}
      <footer className="border-t border-slate-900 bg-slate-950 py-8 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center space-x-2">
            <Shield className="w-4 h-4 text-emerald-500" />
            <span className="font-bold text-slate-300">CivicShield NG</span>
            <span>&mdash; Non-Partisan Electoral Truth &amp; Intelligence Infrastructure</span>
          </div>
          <div className="flex items-center space-x-4 text-[11px]">
            <span>Federal Republic of Nigeria</span>
            <span>&bull;</span>
            <span>Cryptographic SHA-256 Ledger</span>
            <span>&bull;</span>
            <span>Zero-PII Storage</span>
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
      <AppContent />
    </AuthProvider>
  );
}
