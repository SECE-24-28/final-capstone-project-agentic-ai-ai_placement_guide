import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  token: string | null;
  userId: number | null;
  role: string | null;
  isAuthenticated: boolean;
  setAuth: (token: string, userId: number, role: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      userId: null,
      role: null,
      isAuthenticated: false,
      setAuth: (token, userId, role) => {
        localStorage.setItem("token", token);
        set({ token, userId, role, isAuthenticated: true });
      },
      logout: () => {
        localStorage.removeItem("token");
        set({ token: null, userId: null, role: null, isAuthenticated: false });
      },
    }),
    { name: "auth-store", skipHydration: true }
  )
);


interface AnalysisState {
  resumeAnalysis: any | null;
  skillGap: any | null;
  roadmap: any | null;
  jobMatches: any | null;
  isLoading: boolean;
  setResumeAnalysis: (data: any) => void;
  setSkillGap: (data: any) => void;
  setRoadmap: (data: any) => void;
  setJobMatches: (data: any) => void;
  setLoading: (v: boolean) => void;
  setFullAnalysis: (data: any) => void;
}

// ─── Todo / Checklist Store (persisted) ─────────────────────────────────────

interface TodoState {
  checked: Record<string, boolean>; // key = "daily-{day}-{taskIdx}" | "weekly-{week}-{goalIdx}"
  toggle: (key: string) => void;
  resetTodos: () => void;
}

export const useTodoStore = create<TodoState>()(
  persist(
    (set) => ({
      checked: {},
      toggle: (key) => set((s) => ({ checked: { ...s.checked, [key]: !s.checked[key] } })),
      resetTodos: () => set({ checked: {} }),
    }),
    { name: "roadmap-todos" }
  )
);

export const useAnalysisStore = create<AnalysisState>()((set) => ({
  resumeAnalysis: null,
  skillGap: null,
  roadmap: null,
  jobMatches: null,
  isLoading: false,
  setResumeAnalysis: (data) => set({ resumeAnalysis: data }),
  setSkillGap: (data) => set({ skillGap: data }),
  setRoadmap: (data) => set({ roadmap: data }),
  setJobMatches: (data) => set({ jobMatches: data }),
  setLoading: (v) => set({ isLoading: v }),
  setFullAnalysis: (data) => set({
    resumeAnalysis: data.resume_analysis,
    skillGap: data.skill_gap,
    roadmap: data.roadmap,
    jobMatches: data.job_matches,
  }),
}));
