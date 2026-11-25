import React from 'react';
import {
  Shield,
  BarChart3,
  User,
  LogOut,
  SunMoon,
  Type,
  Globe,
  Radio,
  Sparkles,
} from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { useAccessibility, TextSize, AppLanguage } from '../../context/AccessibilityContext';

interface NavbarProps {
  currentView: 'citizen' | 'command';
  onViewChange: (view: 'citizen' | 'command') => void;
  onOpenAuthModal: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({ currentView, onViewChange, onOpenAuthModal }) => {
  const { user, isAuthenticated, logout } = useAuth();
  const {
    highContrast,
    toggleHighContrast,
    textSize,
    setTextSize,
    language,
    setLanguage,
    t,
  } = useAccessibility();

  const isInstitutionalUser = user?.roles?.some((r) =>
    ['ANALYST', 'VERIFICATION_OFFICER', 'SECURITY_OFFICER', 'ADMINISTRATOR'].includes(r)
  );

  const cycleTextSize = () => {
    const sizes: TextSize[] = ['sm', 'md', 'lg', 'xl'];
    const nextIdx = (sizes.indexOf(textSize) + 1) % sizes.length;
    setTextSize(sizes[nextIdx]);
  };

  const toggleLanguage = () => {
    const nextLang: AppLanguage = language === 'en' ? 'pcm' : 'en';
    setLanguage(nextLang);
  };

  return (
    <>
      {/* Skip to Main Content Link for Keyboard and Screen-Reader Traversal */}
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:absolute focus:top-2 focus:left-2 focus:z-50 focus:px-4 focus:py-2 focus:bg-emerald-600 focus:text-white focus:font-bold focus:rounded-md focus:shadow-lg"
      >
        {t('skip_to_content', 'Skip to main content')}
      </a>

      {/* Top Banner: Synthetic Data Disclaimer + Nonpartisan Notice */}
      <aside aria-label="Platform Notice" className="bg-slate-900 border-b border-slate-800 text-[11px] text-slate-400 py-1 px-4 sm:px-8">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-1">
          <div className="flex items-center space-x-2">
            <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-amber-950 text-amber-300 border border-amber-800">
              {t('simulated_data_watermark', 'SIMULATED / DEMONSTRATION DATA')}
            </span>
            <span className="hidden md:inline text-slate-500">•</span>
            <span className="hidden md:inline">
              {t('nonpartisan_disclaimer', 'Non-Partisan Electoral Truth & Intelligence Infrastructure • Federal Republic of Nigeria')}
            </span>
          </div>

          {/* Accessibility Quick Toggles */}
          <div className="flex items-center space-x-3 text-xs" role="region" aria-label="Accessibility quick controls">
            {/* Language Switcher */}
            <button
              onClick={toggleLanguage}
              className="flex items-center space-x-1 px-2 py-0.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors"
              title="Toggle language: English / Nigerian Pidgin"
              aria-label={`Current language is ${language === 'en' ? 'English' : 'Nigerian Pidgin'}. Press to switch.`}
            >
              <Globe className="w-3.5 h-3.5 text-emerald-400" />
              <span className="font-semibold">{language === 'en' ? 'English' : 'Naija Pidgin'}</span>
            </button>

            {/* High Contrast Mode */}
            <button
              onClick={toggleHighContrast}
              className={`flex items-center space-x-1 px-2 py-0.5 rounded transition-colors ${
                highContrast
                  ? 'bg-amber-400 text-black font-bold'
                  : 'hover:bg-slate-800 text-slate-300 hover:text-white'
              }`}
              title="Toggle High Contrast Mode"
              aria-pressed={highContrast}
              aria-label="High contrast mode toggle"
            >
              <SunMoon className="w-3.5 h-3.5" />
              <span className="hidden sm:inline">{t('high_contrast', 'Contrast')}</span>
            </button>

            {/* Text Resizer */}
            <button
              onClick={cycleTextSize}
              className="flex items-center space-x-1 px-2 py-0.5 rounded hover:bg-slate-800 text-slate-300 hover:text-white transition-colors font-mono"
              title={`Cycle text size (currently ${textSize.toUpperCase()})`}
              aria-label={`Text size is ${textSize}. Press to scale font.`}
            >
              <Type className="w-3.5 h-3.5" />
              <span>{textSize.toUpperCase()}</span>
            </button>
          </div>
        </div>
      </aside>

      {/* Main Header / Navigation */}
      <header className="sticky top-0 z-40 bg-slate-950/95 backdrop-blur border-b border-slate-800 text-white shadow-xl">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Platform Identity */}
            <div
              className="flex items-center space-x-3 cursor-pointer"
              onClick={() => onViewChange('citizen')}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && onViewChange('citizen')}
              aria-label="CivicShield NG Home"
            >
              <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-500 to-teal-700 flex items-center justify-center shadow-lg shadow-emerald-950/60 border border-emerald-400/30">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="font-black text-lg tracking-tight bg-gradient-to-r from-emerald-400 via-teal-200 to-white bg-clip-text text-transparent">
                    CIVICSHIELD NG
                  </span>
                  <span className="hidden sm:inline-block px-1.5 py-0.5 text-[9px] font-bold uppercase rounded bg-emerald-950 text-emerald-400 border border-emerald-800">
                    NG Integrity
                  </span>
                </div>
                <p className="text-[11px] text-slate-400 hidden md:block">
                  {t('tagline', 'Electoral Information Integrity & Threat Intelligence Platform')}
                </p>
              </div>
            </div>

            {/* Navigation Mode Switcher: Citizen Portal vs Command Centre */}
            <nav className="flex items-center bg-slate-900/90 p-1 rounded-xl border border-slate-800" aria-label="Experience switcher">
              <button
                onClick={() => onViewChange('citizen')}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  currentView === 'citizen'
                    ? 'bg-emerald-600 text-white shadow-md shadow-emerald-950'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
                aria-current={currentView === 'citizen' ? 'page' : undefined}
              >
                <Shield className="w-4 h-4" />
                <span>{t('citizen_portal', 'Citizen Portal')}</span>
              </button>

              <button
                onClick={() => {
                  if (!isAuthenticated) {
                    onOpenAuthModal();
                  } else {
                    onViewChange('command');
                  }
                }}
                className={`flex items-center space-x-2 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all ${
                  currentView === 'command'
                    ? 'bg-blue-600 text-white shadow-md shadow-blue-950'
                    : 'text-slate-300 hover:text-white hover:bg-slate-800/80'
                }`}
                aria-current={currentView === 'command' ? 'page' : undefined}
              >
                <BarChart3 className="w-4 h-4" />
                <span>{t('command_centre', 'Command Centre')}</span>
                {isInstitutionalUser && (
                  <span className="w-2 h-2 rounded-full bg-blue-400 animate-pulse" title="Active Officer Access"></span>
                )}
              </button>
            </nav>

            {/* Auth & Cryptographic Ledger Status */}
            <div className="flex items-center space-x-3">
              <div className="hidden lg:flex items-center space-x-2 text-xs text-slate-400 border-r border-slate-800 pr-3">
                <span className="flex h-2 w-2 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                </span>
                <span className="font-mono text-[11px]">{t('ledger_verified', 'Ledger Verified')}</span>
              </div>

              {isAuthenticated && user ? (
                <div className="flex items-center space-x-3">
                  <div className="text-right hidden sm:block">
                    <div className="text-xs font-semibold text-slate-200">{user.full_name}</div>
                    <div className="text-[10px] text-emerald-400 font-mono">
                      {user.roles?.join(', ')}
                    </div>
                  </div>
                  <button
                    onClick={logout}
                    title="Sign out"
                    aria-label="Sign out of account"
                    className="p-2 rounded-lg bg-slate-900 hover:bg-rose-950/70 hover:text-rose-400 border border-slate-800 text-slate-300 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <button
                  onClick={onOpenAuthModal}
                  className="flex items-center space-x-1.5 px-3.5 py-1.5 rounded-xl text-xs font-bold bg-emerald-600 hover:bg-emerald-500 text-white transition-all shadow-md shadow-emerald-950"
                  aria-label="Open authentication modal"
                >
                  <User className="w-4 h-4" />
                  <span>{t('officer_sign_in', 'Officer / Sign In')}</span>
                </button>
              )}
            </div>
          </div>
        </div>
      </header>
    </>
  );
};
