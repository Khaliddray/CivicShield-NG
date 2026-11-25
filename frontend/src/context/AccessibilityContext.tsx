import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';

export type TextSize = 'sm' | 'md' | 'lg' | 'xl';
export type AppLanguage = 'en' | 'pcm';

interface AccessibilityContextType {
  highContrast: boolean;
  toggleHighContrast: () => void;
  textSize: TextSize;
  setTextSize: (size: TextSize) => void;
  language: AppLanguage;
  setLanguage: (lang: AppLanguage) => void;
  t: (key: string, fallback?: string) => string;
  speak: (text: string) => void;
  stopSpeaking: () => void;
  isSpeaking: boolean;
  announce: (message: string) => void;
  announcement: string;
  isListening: boolean;
  startListening: (onResult: (text: string) => void, onError?: (err: string) => void) => void;
  stopListening: () => void;
  speechSupported: boolean;
  recognitionSupported: boolean;
}

const TRANSLATIONS: Record<AppLanguage, Record<string, string>> = {
  en: {
    // Navigation & Common
    platform_name: 'CIVICSHIELD NG',
    tagline: 'Electoral Information Integrity & Threat Intelligence Platform',
    citizen_portal: 'Citizen Portal',
    command_centre: 'Command Centre',
    officer_sign_in: 'Officer / Sign In',
    ledger_verified: 'Ledger Verified',
    high_contrast: 'High Contrast',
    text_size: 'Text Size',
    language_toggle: 'Language',
    a11y_controls: 'Accessibility Settings',
    skip_to_content: 'Skip to main content',
    simulated_data_watermark: 'SIMULATED / DEMONSTRATION DATA',
    nonpartisan_disclaimer: 'Non-Partisan Electoral Truth & Intelligence Infrastructure • Federal Republic of Nigeria',
    
    // Citizen Home Hero
    hero_badge: 'AI-Powered Electoral Truth & Intelligence Infrastructure',
    hero_title: 'Protecting Nigeria’s Electoral Information Environment',
    hero_subtitle: 'Verify circulating election announcements against cryptographically certified institutional records. Report suspected misinformation, deepfakes, and coordinated propaganda in real-time.',
    btn_report_suspicious: 'Report Suspicious Information',
    btn_verify_hash: 'Verify Official Document Hash',

    // Citizen Tabs
    tab_submit_report: 'Submit Report',
    tab_track_status: 'Track Status',
    tab_official_registry: 'Official Gazettes',
    tab_ai_assistant: 'CivicShield AI',

    // Reporting Form
    report_title_label: 'Suspicious Announcement / Incident Description',
    report_title_placeholder: 'Paste or describe the circulating claim, announcement, or rumor...',
    report_platform_label: 'Where did you encounter this?',
    report_state_label: 'State Affected (Location)',
    report_evidence_label: 'Attach Evidence (Image, Audio, Video, PDF)',
    report_submit_btn: 'Submit Anonymously for Verification',
    report_submitting: 'Securing Evidence & Hashing IP...',
    report_success_title: 'Report Ingested Successfully',
    report_reference_notice: 'Your canonical tracking reference code is:',
    report_privacy_guarantee: 'Zero Personally Identifiable Information (PII) is stored. Client IP is salted & cryptographically hashed with SHA-256.',
    
    // Voice
    voice_record: 'Dictate by Voice',
    voice_listening: 'Listening... Speak clearly',
    voice_stop: 'Stop Recording',
    voice_read_aloud: 'Read aloud',
    voice_stop_reading: 'Stop audio',

    // Tracking
    track_input_label: 'Enter Canonical Reference Code',
    track_input_placeholder: 'e.g. CS-20261125-A1B2C3',
    track_btn: 'Inspect Verification Status',
    track_loading: 'Traversing Audit Ledger...',

    // Registry & Verification
    registry_search_label: 'Search Authenticated Electoral Documents',
    registry_search_placeholder: 'Search by keyword, topic, or document code (e.g. INEC-2026)...',
    registry_verify_hash_title: 'Cryptographic SHA-256 Hash Verifier',
    registry_verify_hash_desc: 'Check if a digital announcement or PDF is authentic, untampered, and issued by verified electoral authorities.',
    registry_verify_btn: 'Verify Cryptographic Integrity',

    // AI Assistant
    ai_assistant_intro: 'Greetings. I am CivicShield AI, your electoral information integrity assistant. You can ask me to verify circulating announcements, check official INEC schedules, or report suspicious election claims.',
    ai_input_placeholder: 'Ask about voting dates, polling centers, INEC circulars, or paste a circulating message...',
    ai_invariant_note: 'Invariant: AI confidence scores are never presented as proof of truth or falsity. Authoritative decisions require human Verification Officer approval.',
    ai_disclaimer: 'Answers are grounded strictly in certified gazettes and official documents. When evidence is insufficient, uncertainty is explicitly stated.',

    // Alerts
    alerts_banner_title: 'Active Early Warnings & Debunks',
    alerts_view_clarification: 'View Clarification',
    alerts_hide_details: 'Hide Details',
  },
  pcm: {
    // Navigation & Common
    platform_name: 'CIVICSHIELD NG',
    tagline: 'Platform Wey Dey Protect We Election Information and Security',
    citizen_portal: 'Citizens Corner',
    command_centre: 'Official Command Centre',
    officer_sign_in: 'Officer / Log In',
    ledger_verified: 'Ledger Clean & Checked',
    high_contrast: 'Bright Screen Mode',
    text_size: 'Font Size',
    language_toggle: 'Language',
    a11y_controls: 'Easy Access Settings',
    skip_to_content: 'Jump go main content',
    simulated_data_watermark: 'DEMO SAMPLE DATA (SIMULATION)',
    nonpartisan_disclaimer: 'CivicShield No Dey Support Any Political Party • Federal Republic of Nigeria',

    // Citizen Home Hero
    hero_badge: 'AI Engine Wey Dey Protect Election Truth & Security',
    hero_title: 'Dey Protect Nigeria Election Against Fake News & Lies',
    hero_subtitle: 'Confirm circulating election news against genuine government & INEC documents. Report fake announcements, manipulated audio, or propaganda sharp-sharp.',
    btn_report_suspicious: 'Report Wahala / Fake News',
    btn_verify_hash: 'Check Genuine Document Hash',

    // Citizen Tabs
    tab_submit_report: 'Send Report',
    tab_track_status: 'Check Status',
    tab_official_registry: 'Official INEC Papers',
    tab_ai_assistant: 'CivicShield AI Assistant',

    // Reporting Form
    report_title_label: 'Wetin You Hear / Suspicious Announcement',
    report_title_placeholder: 'Write or paste wetin people dey share for WhatsApp, X, or street...',
    report_platform_label: 'Which place you see am?',
    report_state_label: 'Which State e happen?',
    report_evidence_label: 'Attach Proof (Picture, Voice Note, Video, Document)',
    report_submit_btn: 'Send Am Secretly Make Dem Check Am',
    report_submitting: 'We dey secure your evidence and hide your identity...',
    report_success_title: 'Report Don Enter Hand Successfully',
    report_reference_notice: 'Your special tracking number na:',
    report_privacy_guarantee: 'We no dey save your name or phone number. We dey hash your IP address with SHA-256 for privacy.',

    // Voice
    voice_record: 'Talk With Your Mouth (Voice)',
    voice_listening: 'I dey listen... Talk clearly now',
    voice_stop: 'Stop Recording',
    voice_read_aloud: 'Read am out for me',
    voice_stop_reading: 'Stop voice',

    // Tracking
    track_input_label: 'Put Your Special Reference Number',
    track_input_placeholder: 'e.g. CS-20261125-A1B2C3',
    track_btn: 'Check Wetin Dey Happen',
    track_loading: 'We dey check the official ledger...',

    // Registry & Verification
    registry_search_label: 'Find Certified Official Papers',
    registry_search_placeholder: 'Search by keyword, topic, or document code (e.g. INEC-2026)...',
    registry_verify_hash_title: 'Cryptographic SHA-256 Hash Verifier',
    registry_verify_hash_desc: 'Check if document or text from government/INEC na original or fake clone.',
    registry_verify_btn: 'Check If Na Original Document',

    // AI Assistant
    ai_assistant_intro: 'Kedu! Ndewo! Salama! Welldone. Na me be CivicShield AI. Ask me about election dates, polling units, or send me any news make I check am for INEC record.',
    ai_input_placeholder: 'Ask question about election date, BVAS, or paste circulating claim...',
    ai_invariant_note: 'Strict Rule: AI confidence score no be final proof. Human verification officer must confirm any decision before e become official.',
    ai_disclaimer: 'All answers dey come direct from certified official gazettes. If document no dey, the system go talk true say evidence no reach.',

    // Alerts
    alerts_banner_title: 'Current Early Warning Alerts & Official Debunks',
    alerts_view_clarification: 'See Details & Proof',
    alerts_hide_details: 'Close Details',
  },
};

const AccessibilityContext = createContext<AccessibilityContextType | undefined>(undefined);

export const AccessibilityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [highContrast, setHighContrast] = useState<boolean>(() => {
    return localStorage.getItem('civicshield_contrast') === 'high';
  });

  const [textSize, setTextSizeState] = useState<TextSize>(() => {
    return (localStorage.getItem('civicshield_text_size') as TextSize) || 'md';
  });

  const [language, setLanguageState] = useState<AppLanguage>(() => {
    return (localStorage.getItem('civicshield_lang') as AppLanguage) || 'en';
  });

  const [announcement, setAnnouncement] = useState<string>('');
  const [isSpeaking, setIsSpeaking] = useState<boolean>(false);
  const [isListening, setIsListening] = useState<boolean>(false);

  const speechSupported = typeof window !== 'undefined' && 'speechSynthesis' in window;
  const recognitionSupported =
    typeof window !== 'undefined' &&
    ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

  // Sync high contrast to document element
  useEffect(() => {
    const root = document.documentElement;
    if (highContrast) {
      root.classList.add('high-contrast');
      localStorage.setItem('civicshield_contrast', 'high');
    } else {
      root.classList.remove('high-contrast');
      localStorage.setItem('civicshield_contrast', 'normal');
    }
  }, [highContrast]);

  // Sync text size to document element
  useEffect(() => {
    const root = document.documentElement;
    root.classList.remove('text-size-sm', 'text-size-md', 'text-size-lg', 'text-size-xl');
    root.classList.add(`text-size-${textSize}`);
    localStorage.setItem('civicshield_text_size', textSize);
  }, [textSize]);

  const toggleHighContrast = useCallback(() => {
    setHighContrast((prev) => !prev);
  }, []);

  const setTextSize = useCallback((size: TextSize) => {
    setTextSizeState(size);
  }, []);

  const setLanguage = useCallback((lang: AppLanguage) => {
    setLanguageState(lang);
    localStorage.setItem('civicshield_lang', lang);
  }, []);

  const t = useCallback(
    (key: string, fallback?: string): string => {
      const dict = TRANSLATIONS[language] || TRANSLATIONS.en;
      return dict[key] || TRANSLATIONS.en[key] || fallback || key;
    },
    [language]
  );

  const announce = useCallback((message: string) => {
    setAnnouncement(message);
    const timer = setTimeout(() => setAnnouncement(''), 4000);
    return () => clearTimeout(timer);
  }, []);

  const speak = useCallback(
    (text: string) => {
      if (!speechSupported) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.95;
      utterance.lang = language === 'pcm' ? 'en-NG' : 'en-US';
      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);
      window.speechSynthesis.speak(utterance);
    },
    [speechSupported, language]
  );

  const stopSpeaking = useCallback(() => {
    if (!speechSupported) return;
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
  }, [speechSupported]);

  const startListening = useCallback(
    (onResult: (text: string) => void, onError?: (err: string) => void) => {
      if (!recognitionSupported) {
        if (onError) onError('Speech recognition is not supported in this browser.');
        return;
      }

      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = language === 'pcm' ? 'en-NG' : 'en-US';

      recognition.onstart = () => setIsListening(true);
      recognition.onresult = (event: any) => {
        const transcript = event.results[0][0].transcript;
        setIsListening(false);
        onResult(transcript);
      };
      recognition.onerror = (event: any) => {
        setIsListening(false);
        if (onError) onError(event.error || 'Failed to capture voice.');
      };
      recognition.onend = () => setIsListening(false);

      recognition.start();
    },
    [recognitionSupported, language]
  );

  const stopListening = useCallback(() => {
    setIsListening(false);
  }, []);

  return (
    <AccessibilityContext.Provider
      value={{
        highContrast,
        toggleHighContrast,
        textSize,
        setTextSize,
        language,
        setLanguage,
        t,
        speak,
        stopSpeaking,
        isSpeaking,
        announce,
        announcement,
        isListening,
        startListening,
        stopListening,
        speechSupported,
        recognitionSupported,
      }}
    >
      {/* Live Region for Screen Readers */}
      <div
        role="status"
        aria-live="polite"
        aria-atomic="true"
        className="sr-only"
        id="a11y-live-announcer"
      >
        {announcement}
      </div>
      {children}
    </AccessibilityContext.Provider>
  );
};

export const useAccessibility = () => {
  const context = useContext(AccessibilityContext);
  if (!context) {
    throw new Error('useAccessibility must be used within an AccessibilityProvider');
  }
  return context;
};
