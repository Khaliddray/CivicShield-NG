import React from 'react';
import { Shield, ShieldAlert, User, LogOut, CheckCircle, BarChart3, Radio } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';

interface NavbarProps {
  currentView: 'citizen' | 'command';
  onViewChange: (view: 'citizen' | 'command') => void;
  onOpenAuthModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onViewChange, onOpenAuthModal }) => {
  const { user, isAuthenticated, logout } = useAuth();

  const isInstitutionalUser = user?.roles.some((r) =>
    ['ANALYST', 'VERIFICATION_OFFICER', 'SECURITY_OFFICER', 'ADMINISTRATOR'].includes(r)
  );

  return (
    <header className="sticky top-0 z-50 bg-slate-900 border-b border-slate-800 text-white shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Identity */}
          <div className="flex items-center space-x-3 cursor-pointer" onClick={() => onViewChange('citizen')}>
            <div className="w-10 h-10 rounded-lg bg-emerald-600 flex items-center justify-center shadow-md shadow-emerald-900/40">
              <Shield className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-extrabold text-lg tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
                  CIVICSHIELD NG
                </span>
                <span className="px-1.5 py-0.5 text-[10px] font-bold uppercase rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                  Federal Republic of Nigeria
                </span>
              </div>
              <p className="text-xs text-slate-400 hidden sm:block">
                Electoral Information Integrity &amp; Threat Intelligence Platform
              </p>
            </div>
          </div>

          {/* Navigation Mode Switcher */}
          <div className="flex items-center bg-slate-800/80 p-1 rounded-xl border border-slate-700/60">
            <button
              onClick={() => onViewChange('citizen')}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentView === 'citizen'
                  ? 'bg-emerald-600 text-white shadow'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <Shield className="w-4 h-4" />
              <span>Citizen Portal</span>
            </button>

            <button
              onClick={() => {
                if (!isAuthenticated) {
                  onOpenAuthModal();
                } else {
                  onViewChange('command');
                }
              }}
              className={`flex items-center space-x-2 px-3 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                currentView === 'command'
                  ? 'bg-blue-600 text-white shadow'
                  : 'text-slate-300 hover:text-white hover:bg-slate-700/50'
              }`}
            >
              <BarChart3 className="w-4 h-4" />
              <span>Command Centre</span>
              {isInstitutionalUser && (
                <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse"></span>
              )}
            </button>
          </div>

          {/* Auth & Status Area */}
          <div className="flex items-center space-x-3">
            <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-400 border-r border-slate-800 pr-3">
              <span className="flex h-2 w-2 relative">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
              </span>
              <span>Ledger Verified</span>
            </div>

            {isAuthenticated && user ? (
              <div className="flex items-center space-x-3">
                <div className="text-right hidden sm:block">
                  <div className="text-xs font-medium text-slate-200">{user.full_name}</div>
                  <div className="text-[10px] text-emerald-400 font-mono">
                    {user.roles.join(', ')}
                  </div>
                </div>
                <button
                  onClick={logout}
                  title="Sign out"
                  className="p-2 rounded-lg bg-slate-800 hover:bg-rose-950/60 hover:text-rose-400 border border-slate-700 text-slate-300 transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={onOpenAuthModal}
                className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-sm"
              >
                <User className="w-4 h-4" />
                <span>Officer / Sign In</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
