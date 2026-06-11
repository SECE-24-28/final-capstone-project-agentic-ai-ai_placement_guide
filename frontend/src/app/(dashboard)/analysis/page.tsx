"use client";
import { useAnalysisStore } from "@/lib/store";
import Link from "next/link";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { FileText, Briefcase, GraduationCap, FolderOpen, Award, AlertCircle, ArrowRight } from "lucide-react";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

const scoreColor = (s: number) => s >= 80 ? "#10b981" : s >= 60 ? "#f59e0b" : "#ef4444";
const scoreLabel = (s: number) => s >= 80 ? "Excellent" : s >= 60 ? "Good" : "Needs Work";
const scoreBg = (s: number) => s >= 80 ? "from-emerald-500 to-green-600" : s >= 60 ? "from-amber-500 to-orange-500" : "from-red-500 to-rose-600";

const severityConfig: any = {
  error: { bg: "bg-red-50", text: "text-red-700", border: "border-red-200", badge: "bg-red-100 text-red-700" },
  warning: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", badge: "bg-amber-100 text-amber-700" },
  info: { bg: "bg-blue-50", text: "text-blue-700", border: "border-blue-200", badge: "bg-blue-100 text-blue-700" },
};

export default function AnalysisPage() {
  const { resumeAnalysis } = useAnalysisStore();

  if (!resumeAnalysis) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
          <FileText className="h-10 w-10 text-gray-300" />
        </div>
        <h2 className="text-xl font-bold text-gray-700 mb-2">No analysis yet</h2>
        <p className="text-gray-500 mb-6 max-w-sm">Upload your resume to get a detailed AI-powered analysis</p>
        <Link href="/upload" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-blue-200 transition-all">
          Upload Resume <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  const score = resumeAnalysis.resume_score;
  const skillCategories = resumeAnalysis.skills.reduce((acc: any, s: any) => {
    const cat = s.category || "Other";
    acc[cat] = (acc[cat] || 0) + 1;
    return acc;
  }, {});
  const pieData = Object.entries(skillCategories).map(([name, value]) => ({ name, value }));

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Resume Analysis</h1>
        <p className="text-gray-500 mt-1">AI-powered analysis of your resume</p>
      </div>

      {/* Header Card */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className={`h-2 bg-gradient-to-r ${scoreBg(score)}`} />
        <div className="p-6 flex items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <h2 className="text-2xl font-black text-gray-900">{resumeAnalysis.candidate_name || "Candidate"}</h2>
            <div className="flex flex-wrap gap-3 text-sm text-gray-600">
              {resumeAnalysis.email && <span className="flex items-center gap-1.5">📧 {resumeAnalysis.email}</span>}
              {resumeAnalysis.phone && <span className="flex items-center gap-1.5">📱 {resumeAnalysis.phone}</span>}
              {resumeAnalysis.cgpa && <span className="flex items-center gap-1.5">🎓 CGPA {resumeAnalysis.cgpa}</span>}
              {resumeAnalysis.graduation_year && <span className="flex items-center gap-1.5">📅 Class of {resumeAnalysis.graduation_year}</span>}
            </div>
          </div>
          {/* Score */}
          <div className="flex-shrink-0 text-center">
            <div className="relative w-28 h-28">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={[{ value: score }, { value: 100 - score }]} cx="50%" cy="50%" innerRadius={38} outerRadius={52}
                    startAngle={90} endAngle={-270} dataKey="value">
                    <Cell fill={scoreColor(score)} />
                    <Cell fill="#f3f4f6" />
                  </Pie>
                </PieChart>
              </ResponsiveContainer>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-black" style={{ color: scoreColor(score) }}>{score}</span>
                <span className="text-xs text-gray-400">/100</span>
              </div>
            </div>
            <p className="text-xs font-bold mt-1" style={{ color: scoreColor(score) }}>{scoreLabel(score)}</p>
            <p className="text-xs text-gray-400">ATS Score</p>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
              <Award className="h-3.5 w-3.5 text-blue-600" />
            </div>
            Skills <span className="text-gray-400 text-sm font-normal">({resumeAnalysis.skills.length})</span>
          </h3>
          <div className="flex flex-wrap gap-2 mb-4">
            {resumeAnalysis.skills.map((s: any, i: number) => (
              <span key={i} className="px-3 py-1.5 rounded-full text-xs font-semibold text-white"
                style={{ backgroundColor: COLORS[i % COLORS.length] }}>
                {s.name}
              </span>
            ))}
          </div>
          {pieData.length > 0 && (
            <ResponsiveContainer width="100%" height={140}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={55} dataKey="value"
                  label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={10}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: "12px", fontSize: "12px" }} />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Education */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-emerald-100 rounded-lg flex items-center justify-center">
              <GraduationCap className="h-3.5 w-3.5 text-emerald-600" />
            </div>
            Education
          </h3>
          <div className="space-y-4">
            {resumeAnalysis.education.map((e: any, i: number) => (
              <div key={i} className="relative pl-4 border-l-2 border-emerald-300">
                <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-emerald-400" />
                <p className="font-semibold text-gray-900">{e.degree} {e.field_of_study && `— ${e.field_of_study}`}</p>
                <p className="text-sm text-gray-600 mt-0.5">{e.institution}</p>
                <p className="text-xs text-gray-400 mt-0.5">{e.start_year} – {e.end_year || "Present"}{e.cgpa ? ` • CGPA: ${e.cgpa}` : ""}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Experience */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-violet-100 rounded-lg flex items-center justify-center">
              <Briefcase className="h-3.5 w-3.5 text-violet-600" />
            </div>
            Experience
          </h3>
          {resumeAnalysis.experience.length > 0 ? (
            <div className="space-y-4">
              {resumeAnalysis.experience.map((ex: any, i: number) => (
                <div key={i} className="relative pl-4 border-l-2 border-violet-300">
                  <div className="absolute -left-1.5 top-1.5 w-3 h-3 rounded-full bg-violet-400" />
                  <p className="font-semibold text-gray-900">{ex.role}</p>
                  <p className="text-sm text-gray-600 mt-0.5">{ex.company}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{ex.start_date} – {ex.end_date}</p>
                  {ex.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ex.description}</p>}
                </div>
              ))}
            </div>
          ) : (
            <p className="text-gray-400 text-sm py-4 text-center">No experience found in resume</p>
          )}
        </div>

        {/* Projects */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
              <FolderOpen className="h-3.5 w-3.5 text-amber-600" />
            </div>
            Projects <span className="text-gray-400 text-sm font-normal">({resumeAnalysis.projects.length})</span>
          </h3>
          <div className="space-y-4">
            {resumeAnalysis.projects.map((p: any, i: number) => (
              <div key={i} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-gray-900">{p.name}</p>
                  {p.url && (
                    <a href={p.url} target="_blank" rel="noopener noreferrer"
                      className="text-xs text-blue-600 hover:underline flex-shrink-0">GitHub ↗</a>
                  )}
                </div>
                {p.description && <p className="text-xs text-gray-500 mt-1 line-clamp-2">{p.description}</p>}
                {p.tech_stack?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {p.tech_stack.map((t: string, j: number) => (
                      <span key={j} className="px-2 py-0.5 bg-white border border-gray-200 text-gray-600 rounded-md text-xs">{t}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Certifications */}
      {resumeAnalysis.certifications?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
              <Award className="h-3.5 w-3.5 text-blue-600" />
            </div>
            Certifications <span className="text-gray-400 text-sm font-normal">({resumeAnalysis.certifications.length})</span>
          </h3>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-3">
            {resumeAnalysis.certifications.map((c: any, i: number) => (
              <div key={i} className="flex items-center gap-3 p-3 bg-blue-50 border border-blue-100 rounded-xl">
                <div className="w-9 h-9 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
                  <Award className="h-4 w-4 text-white" />
                </div>
                <div>
                  <p className="text-sm font-semibold text-gray-900">{c.name}</p>
                  <p className="text-xs text-gray-500">{c.issuer}{c.year ? ` · ${c.year}` : ""}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Feedback */}
      {resumeAnalysis.feedback?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
              <AlertCircle className="h-3.5 w-3.5 text-amber-600" />
            </div>
            AI Feedback
          </h3>
          <div className="space-y-2">
            {resumeAnalysis.feedback.map((f: any, i: number) => {
              const c = severityConfig[f.severity] || severityConfig.info;
              return (
                <div key={i} className={`flex items-start gap-3 p-4 rounded-xl border ${c.bg} ${c.border}`}>
                  <span className={`flex-shrink-0 px-2 py-0.5 rounded-full text-xs font-bold ${c.badge}`}>{f.severity}</span>
                  <div>
                    <span className={`text-xs font-semibold uppercase tracking-wider ${c.text}`}>{f.category} · </span>
                    <span className={`text-sm ${c.text}`}>{f.message}</span>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
