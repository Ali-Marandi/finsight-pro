import { create } from 'zustand';
import type { AnalysisResult, AnalysisHistoryItem, LicenseInfo, UserPreferences } from '../../types';

interface AnalysisState {
  // Current analysis
  currentAnalysis: AnalysisResult | null;
  setCurrentAnalysis: (analysis: AnalysisResult | null) => void;

  // Analysis history
  analyses: AnalysisHistoryItem[];
  setAnalyses: (analyses: AnalysisHistoryItem[]) => void;
  addAnalysis: (analysis: AnalysisHistoryItem) => void;

  // UI state
  isLoading: boolean;
  setIsLoading: (loading: boolean) => void;
  sidebarOpen: boolean;
  toggleSidebar: () => void;

  // License
  license: LicenseInfo | null;
  setLicense: (license: LicenseInfo | null) => void;

  // Preferences
  preferences: UserPreferences;
  setPreferences: (prefs: Partial<UserPreferences>) => void;
}

const defaultPreferences: UserPreferences = {
  defaultLanguage: 'en',
  chartTheme: 'light',
  decimalPlaces: 2,
  autoSave: true,
};

export const useAnalysisStore = create<AnalysisState>((set) => ({
  currentAnalysis: null,
  setCurrentAnalysis: (analysis) => set({ currentAnalysis: analysis }),

  analyses: [],
  setAnalyses: (analyses) => set({ analyses }),
  addAnalysis: (analysis) =>
    set((state) => ({ analyses: [analysis, ...state.analyses] })),

  isLoading: false,
  setIsLoading: (isLoading) => set({ isLoading }),

  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),

  license: null,
  setLicense: (license) => set({ license }),

  preferences: defaultPreferences,
  setPreferences: (prefs) =>
    set((state) => ({
      preferences: { ...state.preferences, ...prefs },
    })),
}));
