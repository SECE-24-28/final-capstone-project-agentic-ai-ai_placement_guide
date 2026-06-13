import axios from "axios";

const api = axios.create({ baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000" });

api.interceptors.request.use((config) => {
  const token = typeof window !== "undefined" ? localStorage.getItem("token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ─── Auth ─────────────────────────────────────────────────────────────────────
export const authApi = {
  register: (data: { email: string; password: string; full_name: string }) =>
    api.post("/api/v1/auth/register", data),
  login: (data: { email: string; password: string }) =>
    api.post("/api/v1/auth/login", data),
};

// ─── Student ─────────────────────────────────────────────────────────────────
export const studentApi = {
  getProfile: () => api.get("/api/v1/students/me"),
  updateProfile: (data: object) => api.patch("/api/v1/students/me", data),
};

// ─── Resume ──────────────────────────────────────────────────────────────────
export const resumeApi = {
  analyze: (file: File) => {
    const form = new FormData();
    form.append("resume", file);
    return api.post("/api/v1/resume/analyze", form);
  },
  getLatest:   () => api.get("/api/v1/resume/latest"),
  getHistory:  () => api.get("/api/v1/resume/history"),
  compare:     () => api.get("/api/v1/resume/compare"),
  compareById: (v1: string, v2: string) => api.get(`/api/v1/resume/compare/${v1}/${v2}`),
  getStrength: () => api.get("/api/v1/resume/strength"),
  tailor: (job_description: string) =>
    api.post("/api/v1/resume/tailor", { job_description }),
};

// ─── Skill Gap ────────────────────────────────────────────────────────────────
export const skillGapApi = {
  analyze: (skills: string[], target_role: string) =>
    api.post("/api/v1/skill-gap/analyze", { skills, target_role }),
};

// ─── Roadmap ─────────────────────────────────────────────────────────────────
export const roadmapApi = {
  generate: (data: { missing_skills: string[]; student_level: string; available_hours_per_day: number; target_role: string }) =>
    api.post("/api/v1/roadmap/generate", data),
  getLatest: () => api.get("/api/v1/roadmap/latest"),
};

// ─── Jobs ─────────────────────────────────────────────────────────────────────
export const jobsApi = {
  match:            (data: object) => api.post("/api/v1/jobs/match", data),
  getLive:          (role: string, location = "India") => api.get(`/api/v1/jobs/live?role=${encodeURIComponent(role)}&location=${encodeURIComponent(location)}`),
  getCompanyRankings: () => api.get("/api/v1/jobs/company-rankings"),
  getSkillTrends:   () => api.get("/api/v1/jobs/skill-trends"),
  explain:          (data: object) => api.post("/api/v1/jobs/explain", data),
};

// ─── Full Pipeline ────────────────────────────────────────────────────────────
export const pipelineApi = {
  fullAnalysis: (file: File, target_role: string, student_level: string, available_hours_per_day: number) => {
    const form = new FormData();
    form.append("resume", file);
    form.append("target_role", target_role);
    form.append("student_level", student_level);
    form.append("available_hours_per_day", String(available_hours_per_day));
    return api.post("/api/v1/analyze/full", form);
  },
};

export default api;
