"use client";
import { useEffect, useState } from "react";
import { useAnalysisStore } from "@/lib/store";
import { resumeApi } from "@/lib/api";
import Link from "next/link";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import {
  FileText, Briefcase, GraduationCap, FolderOpen, Award, AlertCircle,
  ArrowRight, Zap, CheckCircle, XCircle, TrendingUp, TrendingDown,
  Minus, GitCompare, Upload, Equal
} from "lucide-react";

const COLORS = ["#3b82f6","#10b981","#f59e0b","#ef4444","#8b5cf6","#ec4899","#14b8a6","#f97316"];
const scoreColor = (s: number) => s >= 80 ? "#10b981" : s >= 60 ? "#f59e0b" : "#ef4444";
const scoreLabel = (s: number) => s >= 80 ? "Excellent" : s >= 60 ? "Good" : "Needs Work";
const scoreBg    = (s: number) => s >= 80 ? "from-emerald-500 to-green-600" : s >= 60 ? "from-amber-500 to-orange-500" : "from-red-500 to-rose-600";

const severityConfig: any = {
  error:   { bg: "bg-red-50",   text: "text-red-700",   border: "border-red-200",   badge: "bg-red-100 text-red-700" },
  warning: { bg: "bg-amber-50", text: "text-amber-700", border: "border-amber-200", badge: "bg-amber-100 text-amber-700" },
  info:    { bg: "bg-blue-50",  text: "text-blue-700",  border: "border-blue-200",  badge: "bg-blue-100 text-blue-700" },
};

const strengthColor = (s: number) => s >= 20 ? "#10b981" : s >= 10 ? "#f59e0b" : "#ef4444";
const strengthLabel: any = {
  skills:         "Skills",
  experience:     "Experience",
  summary:        "Summary / Objective",
  education:      "Education",
  certifications: "Certifications",
};

export default function AnalysisPage() {
  const { resumeAnalysis } = useAnalysisStore();
  const [strength, setStrength]   = useState<any>(null);
  const [compare, setCompare]     = useState<any>(null);
  const [firstUpload, setFirstUpload] = useState(false);

  useEffect(() => {
    resumeApi.getStrength().then((r) => setStrength(r.data)).catch(() => {});

    resumeApi.compare()
      .then((r) => setCompare(r.data))
      .catch((e) => {
        const msg = e.response?.data?.detail || "";
        // "Need at least 2" = first upload — show upload-another prompt
        if (msg.toLowerCase().includes("at least 2") || msg.toLowerCase().includes("need at least")) {
          setFirstUpload(true);
        }
      });
  }, []);

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

  // Compute % improvement
  const pctImprovement = compare
    ? compare.ats_v1 > 0
      ? Math.round(((compare.ats_v2 - compare.ats_v1) / compare.ats_v1) * 100)
      : compare.ats_v2 > 0 ? 100 : 0
    : 0;

  const noChanges = compare &&
    compare.added?.length === 0 &&
    compare.removed?.length === 0;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Resume Analysis</h1>
        <p className="text-gray-500 mt-1">AI-powered analysis of your resume</p>
      </div>

      {/* ── Header Card ─────────────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className={`h-2 bg-gradient-to-r ${scoreBg(score)}`} />
        <div className="p-6 flex items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <h2 className="text-2xl font-black text-gray-900">{resumeAnalysis.candidate_name || "Candidate"}</h2>
            <div className="flex flex-wrap gap-3 text-sm text-gray-600">
              {resumeAnalysis.email         && <span>📧 {resumeAnalysis.email}</span>}
              {resumeAnalysis.phone         && <span>📱 {resumeAnalysis.phone}</span>}
              {resumeAnalysis.cgpa          && <span>🎓 CGPA {resumeAnalysis.cgpa}</span>}
              {resumeAnalysis.graduation_year && <span>📅 Class of {resumeAnalysis.graduation_year}</span>}
            </div>
          </div>
          <div className="flex-shrink-0 text-center">
            <div className="relative w-28 h-28">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={[{ value: score }, { value: 100 - score }]} cx="50%" cy="50%"
                    innerRadius={38} outerRadius={52} startAngle={90} endAngle={-270} dataKey="value">
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

      {/* ── Strength Meter ──────────────────────────────────────────────── */}
      {strength && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Zap className="h-4 w-4 text-amber-500" /> Resume Strength Meter
            </h3>
            <span className={`text-sm font-bold px-3 py-1 rounded-full ${
              strength.overall >= 80 ? "bg-emerald-100 text-emerald-700" :
              strength.overall >= 60 ? "bg-amber-100 text-amber-700" : "bg-red-100 text-red-700"
            }`}>{strength.overall}/100 — {strength.grade}</span>
          </div>

          <div className="space-y-4">
            {Object.entries(strength.breakdown).map(([key, val]: any) => (
              <div key={key}>
                <div className="flex items-center justify-between mb-1.5">
                  <span className="text-sm text-gray-700 font-semibold">{strengthLabel[key] || key}</span>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-gray-400">{val}/20</span>
                    {val === 20
                      ? <CheckCircle className="h-4 w-4 text-emerald-500" />
                      : val === 0
                      ? <XCircle className="h-4 w-4 text-red-400" />
                      : <AlertCircle className="h-4 w-4 text-amber-400" />
                    }
                  </div>
                </div>
                <div className="w-full bg-gray-100 rounded-full h-3 overflow-hidden">
                  <div className="h-3 rounded-full transition-all duration-700"
                    style={{ width: `${(val / 20) * 100}%`, backgroundColor: strengthColor(val) }} />
                </div>
              </div>
            ))}
          </div>

          {strength.tips?.length > 0 && (
            <div className="mt-4 space-y-2">
              <p className="text-xs font-semibold text-gray-500 uppercase tracking-wider">💡 Suggestions to improve</p>
              {strength.tips.map((tip: string, i: number) => (
                <div key={i} className="flex items-start gap-2 text-sm text-amber-800 bg-amber-50 border border-amber-100 rounded-xl px-4 py-2.5">
                  <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0 text-amber-500" />
                  {tip}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ── Version Comparison ──────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <GitCompare className="h-4 w-4 text-blue-600" />
          <span className="font-bold text-gray-900">Resume Version Comparison</span>
        </div>

        {/* First upload — no previous version */}
        {firstUpload && !compare && (
          <div className="p-8 flex flex-col items-center text-center gap-3">
            <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center">
              <Upload className="h-7 w-7 text-blue-400" />
            </div>
            <p className="font-semibold text-gray-700">This is your first resume upload</p>
            <p className="text-sm text-gray-400 max-w-xs">
              Upload an updated resume again to automatically compare what changed, what improved, and your ATS score difference.
            </p>
            <Link href="/upload"
              className="mt-1 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all">
              <Upload className="h-4 w-4" /> Upload New Version
            </Link>
          </div>
        )}

        {/* No changes detected */}
        {compare && noChanges && (
          <div className="p-6">
            {/* ATS scores */}
            <div className="flex items-center gap-4 mb-5">
              <div className="flex-1 text-center p-4 bg-gray-50 rounded-2xl">
                <p className="text-xs text-gray-400 mb-1">Previous ATS Score</p>
                <p className="text-4xl font-black text-gray-400">{compare.ats_v1}</p>
              </div>
              <div className="flex flex-col items-center gap-1">
                <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-gray-100 text-gray-500 font-bold">
                  <Equal className="h-5 w-5" /> No change
                </div>
                <span className="text-xs text-gray-400">0 pts difference</span>
              </div>
              <div className="flex-1 text-center p-4 bg-blue-50 rounded-2xl">
                <p className="text-xs text-gray-400 mb-1">Latest ATS Score</p>
                <p className="text-4xl font-black text-blue-600">{compare.ats_v2}</p>
              </div>
            </div>
            <div className="text-center py-4 text-gray-400 text-sm">
              ✅ Both resume versions are identical — no sections were added or removed.
            </div>
          </div>
        )}

        {/* Changes detected */}
        {compare && !noChanges && (
          <div className="p-6 space-y-5">

            {/* ATS Score diff + % improvement */}
            <div className="flex items-stretch gap-4">
              <div className="flex-1 text-center p-4 bg-gray-50 rounded-2xl">
                <p className="text-xs text-gray-400 mb-1">Previous ATS Score</p>
                <p className="text-4xl font-black text-gray-400">{compare.ats_v1}</p>
              </div>

              <div className="flex flex-col items-center justify-center gap-1 px-2">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-base ${
                  compare.ats_improvement > 0 ? "bg-emerald-100 text-emerald-700" :
                  compare.ats_improvement < 0 ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-500"
                }`}>
                  {compare.ats_improvement > 0
                    ? <TrendingUp className="h-5 w-5" />
                    : compare.ats_improvement < 0
                    ? <TrendingDown className="h-5 w-5" />
                    : <Minus className="h-5 w-5" />}
                  {compare.ats_improvement > 0 ? "+" : ""}{compare.ats_improvement} pts
                </div>
                {pctImprovement !== 0 && (
                  <span className={`text-xs font-bold ${pctImprovement > 0 ? "text-emerald-600" : "text-red-500"}`}>
                    {pctImprovement > 0 ? "▲" : "▼"} {Math.abs(pctImprovement)}% {pctImprovement > 0 ? "improvement" : "decrease"}
                  </span>
                )}
              </div>

              <div className="flex-1 text-center p-4 bg-blue-50 rounded-2xl">
                <p className="text-xs text-gray-400 mb-1">Latest ATS Score</p>
                <p className="text-4xl font-black text-blue-600">{compare.ats_v2}</p>
              </div>
            </div>

            {/* Changed sections pills */}
            {compare.sections_changed?.length > 0 && (
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-semibold text-gray-500">Sections changed:</span>
                {compare.sections_changed.map((s: string) => (
                  <span key={s} className="px-3 py-1 bg-amber-100 text-amber-700 text-xs font-bold rounded-full">{s}</span>
                ))}
              </div>
            )}

            {/* Added / Removed / Unchanged counts summary */}
            <div className="grid grid-cols-3 gap-3 text-center">
              <div className="p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
                <p className="text-2xl font-black text-emerald-600">{compare.added?.length}</p>
                <p className="text-xs text-emerald-700 font-medium mt-0.5">✅ Added</p>
              </div>
              <div className="p-3 bg-red-50 border border-red-100 rounded-xl">
                <p className="text-2xl font-black text-red-500">{compare.removed?.length}</p>
                <p className="text-xs text-red-600 font-medium mt-0.5">❌ Removed</p>
              </div>
              <div className="p-3 bg-gray-50 border border-gray-100 rounded-xl">
                <p className="text-2xl font-black text-gray-500">{compare.unchanged?.length}</p>
                <p className="text-xs text-gray-500 font-medium mt-0.5">↔ Unchanged</p>
              </div>
            </div>

            {/* Added details */}
            {compare.added?.length > 0 && (
              <div>
                <p className="text-sm font-bold text-emerald-700 mb-2 flex items-center gap-1.5">
                  <CheckCircle className="h-4 w-4" /> What you added
                </p>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {compare.added.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 bg-emerald-50 border border-emerald-100 rounded-lg px-3 py-2">
                      <span className="px-2 py-0.5 bg-emerald-200 text-emerald-800 text-xs font-bold rounded">{item.section}</span>
                      <span className="text-sm text-gray-700 capitalize">{item.item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Removed details */}
            {compare.removed?.length > 0 && (
              <div>
                <p className="text-sm font-bold text-red-600 mb-2 flex items-center gap-1.5">
                  <XCircle className="h-4 w-4" /> What you removed
                </p>
                <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                  {compare.removed.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                      <span className="px-2 py-0.5 bg-red-200 text-red-800 text-xs font-bold rounded">{item.section}</span>
                      <span className="text-sm text-gray-700 capitalize">{item.item}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Overall verdict */}
            <div className={`rounded-xl p-4 border text-sm font-medium ${
              compare.ats_improvement > 5
                ? "bg-emerald-50 border-emerald-200 text-emerald-800"
                : compare.ats_improvement < 0
                ? "bg-red-50 border-red-200 text-red-800"
                : "bg-gray-50 border-gray-200 text-gray-700"
            }`}>
              {compare.ats_improvement > 5
                ? `🎉 Great improvement! Your resume got ${pctImprovement}% better. ${compare.added?.length} new items added across ${compare.sections_changed?.length} sections.`
                : compare.ats_improvement < 0
                ? `⚠️ Your ATS score dropped by ${Math.abs(compare.ats_improvement)} pts. ${compare.removed?.length} items were removed — consider adding them back.`
                : compare.ats_improvement === 0 && !noChanges
                ? `📋 Some sections changed but ATS score stayed the same. Focus on adding quantified achievements and keywords.`
                : `📈 Small improvement of ${compare.ats_improvement} pts. Keep adding relevant skills and experience details.`
              }
            </div>
          </div>
        )}
      </div>

      {/* ── Skills ──────────────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
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
                <p className="font-semibold text-gray-900">{e.degree}{e.field_of_study && ` — ${e.field_of_study}`}</p>
                <p className="text-sm text-gray-600 mt-0.5">{e.institution}</p>
                <p className="text-xs text-gray-400 mt-0.5">{e.start_year} – {e.end_year || "Present"}{e.cgpa ? ` • CGPA: ${e.cgpa}` : ""}</p>
              </div>
            ))}
          </div>
        </div>

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

        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-amber-100 rounded-lg flex items-center justify-center">
              <FolderOpen className="h-3.5 w-3.5 text-amber-600" />
            </div>
            Projects <span className="text-gray-400 text-sm font-normal">({resumeAnalysis.projects.length})</span>
          </h3>
          <div className="space-y-3">
            {resumeAnalysis.projects.map((p: any, i: number) => (
              <div key={i} className="p-3 bg-gray-50 rounded-xl border border-gray-100">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-semibold text-gray-900">{p.name}</p>
                  {p.url && <a href={p.url} target="_blank" rel="noopener noreferrer" className="text-xs text-blue-600 hover:underline flex-shrink-0">GitHub ↗</a>}
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

      {resumeAnalysis.certifications?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <div className="w-7 h-7 bg-blue-100 rounded-lg flex items-center justify-center">
              <Award className="h-3.5 w-3.5 text-blue-600" />
            </div>
            Certifications
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
