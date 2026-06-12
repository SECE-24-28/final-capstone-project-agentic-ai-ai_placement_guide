"use client";
import { useEffect, useState } from "react";
import { useAnalysisStore } from "@/lib/store";
import { resumeApi } from "@/lib/api";
import Link from "next/link";
import dynamic from "next/dynamic";
import {
  FileText, Briefcase, GraduationCap, FolderOpen, Award, AlertCircle,
  ArrowRight, Zap, CheckCircle, XCircle, TrendingUp, TrendingDown,
  Minus, GitCompare, Upload, Equal, Lightbulb
} from "lucide-react";

// ssr:false — prevents Recharts hydration ID mismatch on page reload
const ATSDonutChart = dynamic(
  () => import("@/components/AnalysisCharts").then((m) => ({ default: m.ATSDonutChart })),
  { ssr: false, loading: () => <div className="w-full h-full" /> }
);
const SkillsPieChart = dynamic(
  () => import("@/components/AnalysisCharts").then((m) => ({ default: m.SkillsPieChart })),
  { ssr: false, loading: () => <div className="w-full h-[140px]" /> }
);

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
          <div className="flex-shrink-0">
            <div className="relative w-28 h-28">
              <ATSDonutChart score={score} color={scoreColor(score)} />
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

        {/* First upload */}
        {firstUpload && !compare && (
          <div className="p-8 flex flex-col items-center text-center gap-3">
            <div className="w-14 h-14 bg-blue-50 rounded-2xl flex items-center justify-center">
              <Upload className="h-7 w-7 text-blue-400" />
            </div>
            <p className="font-semibold text-gray-700">This is your first resume upload</p>
            <p className="text-sm text-gray-400 max-w-xs">Upload an updated resume to compare versions side by side.</p>
            <Link href="/upload" className="mt-1 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl text-sm font-semibold transition-all">
              <Upload className="h-4 w-4" /> Upload New Version
            </Link>
          </div>
        )}

        {compare && (
          <div className="p-6 space-y-5">

            {/* ATS Score Banner */}
            <div className="grid grid-cols-3 items-center gap-3">
              <div className="text-center p-4 bg-gray-50 border border-gray-200 rounded-2xl">
                <p className="text-xs text-gray-400 mb-1 font-medium">Previous Version</p>
                <p className="text-4xl font-black text-gray-400">{compare.ats_v1}</p>
                <p className="text-xs text-gray-400 mt-1">ATS Score</p>
              </div>

              <div className="flex flex-col items-center gap-2">
                <div className={`w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl font-bold text-sm ${
                  compare.ats_improvement > 0 ? "bg-emerald-100 text-emerald-700" :
                  compare.ats_improvement < 0 ? "bg-red-100 text-red-700" : "bg-gray-100 text-gray-500"
                }`}>
                  {compare.ats_improvement > 0 ? <TrendingUp className="h-4 w-4" /> :
                   compare.ats_improvement < 0 ? <TrendingDown className="h-4 w-4" /> :
                   <Equal className="h-4 w-4" />}
                  {compare.ats_improvement > 0 ? "+" : ""}{compare.ats_improvement} pts
                </div>
                {pctImprovement !== 0 && (
                  <span className={`text-xs font-bold ${pctImprovement > 0 ? "text-emerald-600" : "text-red-500"}`}>
                    {pctImprovement > 0 ? "▲" : "▼"} {Math.abs(pctImprovement)}%
                  </span>
                )}
              </div>

              <div className="text-center p-4 bg-blue-50 border border-blue-200 rounded-2xl">
                <p className="text-xs text-blue-500 mb-1 font-medium">Latest Version</p>
                <p className="text-4xl font-black text-blue-600">{compare.ats_v2}</p>
                <p className="text-xs text-blue-400 mt-1">ATS Score</p>
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

            {/* Side-by-side diff */}
            {(compare.added?.length > 0 || compare.removed?.length > 0) && (
              <div className="grid grid-cols-2 gap-3">
                {/* Removed — Previous */}
                <div className="rounded-xl border border-red-200 overflow-hidden">
                  <div className="bg-red-50 px-4 py-2.5 flex items-center gap-2 border-b border-red-200">
                    <XCircle className="h-4 w-4 text-red-500" />
                    <span className="text-sm font-bold text-red-700">Previous</span>
                    <span className="ml-auto text-xs font-bold bg-red-100 text-red-600 px-2 py-0.5 rounded-full">
                      {compare.removed?.length} removed
                    </span>
                  </div>
                  <div className="divide-y divide-red-100 max-h-60 overflow-y-auto">
                    {compare.removed?.length > 0 ? compare.removed.map((item: any, i: number) => (
                      <div key={i} className="flex items-start gap-2 px-4 py-2.5 bg-red-50/50">
                        <span className="text-red-400 font-bold text-sm mt-0.5">−</span>
                        <div>
                          <span className="text-xs font-bold text-red-600 uppercase tracking-wide">{item.section}</span>
                          <p className="text-sm text-gray-700 capitalize mt-0.5">{item.item}</p>
                        </div>
                      </div>
                    )) : (
                      <p className="text-xs text-gray-400 text-center py-6">Nothing removed</p>
                    )}
                  </div>
                </div>

                {/* Added — Latest */}
                <div className="rounded-xl border border-emerald-200 overflow-hidden">
                  <div className="bg-emerald-50 px-4 py-2.5 flex items-center gap-2 border-b border-emerald-200">
                    <CheckCircle className="h-4 w-4 text-emerald-500" />
                    <span className="text-sm font-bold text-emerald-700">Latest</span>
                    <span className="ml-auto text-xs font-bold bg-emerald-100 text-emerald-600 px-2 py-0.5 rounded-full">
                      {compare.added?.length} added
                    </span>
                  </div>
                  <div className="divide-y divide-emerald-100 max-h-60 overflow-y-auto">
                    {compare.added?.length > 0 ? compare.added.map((item: any, i: number) => (
                      <div key={i} className="flex items-start gap-2 px-4 py-2.5 bg-emerald-50/50">
                        <span className="text-emerald-500 font-bold text-sm mt-0.5">+</span>
                        <div>
                          <span className="text-xs font-bold text-emerald-700 uppercase tracking-wide">{item.section}</span>
                          <p className="text-sm text-gray-700 capitalize mt-0.5">{item.item}</p>
                        </div>
                      </div>
                    )) : (
                      <p className="text-xs text-gray-400 text-center py-6">Nothing added</p>
                    )}
                  </div>
                </div>
              </div>
            )}

            {/* Unchanged count */}
            {compare.unchanged?.length > 0 && (
              <div className="flex items-center gap-2 px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl">
                <Minus className="h-4 w-4 text-gray-400" />
                <span className="text-sm text-gray-500">
                  <span className="font-bold text-gray-700">{compare.unchanged.length}</span> items unchanged across all sections
                </span>
              </div>
            )}

            {/* No changes at all */}
            {noChanges && (
              <div className="text-center py-4 text-gray-400 text-sm">
                ✅ Both versions are identical — no sections were added or removed.
              </div>
            )}

            {/* Verdict */}
            <div className={`rounded-xl p-4 border text-sm font-medium ${
              compare.ats_improvement > 5 ? "bg-emerald-50 border-emerald-200 text-emerald-800" :
              compare.ats_improvement < 0 ? "bg-red-50 border-red-200 text-red-800" :
              "bg-gray-50 border-gray-200 text-gray-700"
            }`}>
              {compare.ats_improvement > 5
                ? `🎉 Great improvement! Your resume got ${pctImprovement}% better. ${compare.added?.length} new items added across ${compare.sections_changed?.length} sections.`
                : compare.ats_improvement < 0
                ? `⚠️ ATS score dropped by ${Math.abs(compare.ats_improvement)} pts. ${compare.removed?.length} items removed — consider adding them back.`
                : compare.ats_improvement === 0 && !noChanges
                ? `📋 Sections changed but ATS score stayed the same. Focus on adding quantified achievements and keywords.`
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
            <SkillsPieChart data={pieData} colors={COLORS} />
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
            ATS Signals
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

      {/* ── ATS Score Improvement Tips (ResumeWorded style) ─────────────────── */}
      {resumeAnalysis && (() => {
        const breakdown = resumeAnalysis.ats_breakdown;
        if (!breakdown) return null;

        // Build actionable fix items from ats_breakdown signals
        const tips: { title: string; desc: string; tag: string; tagColor: string; severity: "error" | "warning" | "ok"; points: number }[] = [];

        const kw = breakdown.keyword_match;
        if (kw?.score < 80) tips.push({
          title: "Improve keyword match",
          desc: kw.missing_keywords?.length
            ? `Add these missing keywords: ${kw.missing_keywords.slice(0, 5).join(", ")}`
            : "Add more role-specific keywords from the job description",
          tag: "KEYWORDS", tagColor: "bg-blue-100 text-blue-700",
          severity: kw.score < 40 ? "error" : "warning",
          points: Math.round((80 - kw.score) * 0.25),
        });

        const qa = breakdown.quantified_achievements;
        if (qa?.score < 80) tips.push({
          title: "Quantify your impact",
          desc: `Add numbers/metrics (%, $, counts) to your experience bullets. Currently ${qa.metrics_count ?? 0} metrics found — aim for 6+`,
          tag: "IMPACT", tagColor: "bg-orange-100 text-orange-700",
          severity: qa.score < 40 ? "error" : "warning",
          points: Math.round((80 - qa.score) * 0.20),
        });

        const av = breakdown.action_verbs;
        if (av?.score < 80) tips.push({
          title: "Use stronger action verbs",
          desc: `Start bullets with: Led, Built, Reduced, Increased, Deployed, Architected. Found ${av.verb_count ?? 0} strong verbs — aim for 8+`,
          tag: "STYLE", tagColor: "bg-violet-100 text-violet-700",
          severity: av.score < 40 ? "error" : "warning",
          points: Math.round((80 - av.score) * 0.10),
        });

        const sec = breakdown.section_detection;
        if (sec?.sections_missing?.length > 0) tips.push({
          title: "Add missing sections",
          desc: `Your resume is missing: ${sec.sections_missing.join(", ")}`,
          tag: "STRUCTURE", tagColor: "bg-emerald-100 text-emerald-700",
          severity: "warning",
          points: Math.round((sec.sections_missing.length / 6) * 15),
        });

        const fmt = breakdown.format_compliance;
        if (fmt?.format_issues?.length > 0) tips.push({
          title: "Fix formatting issues",
          desc: fmt.format_issues.join(". "),
          tag: "FORMAT", tagColor: "bg-gray-100 text-gray-700",
          severity: "warning",
          points: Math.round((100 - (fmt.score ?? 100)) * 0.05),
        });

        const rel = breakdown.relevance;
        if (rel?.cosine_similarity < 0.5) tips.push({
          title: "Improve role relevance",
          desc: `Your resume has low semantic relevance to the target role (${Math.round((rel.cosine_similarity ?? 0) * 100)}% match). Tailor your summary and skills section.`,
          tag: "RELEVANCE", tagColor: "bg-indigo-100 text-indigo-700",
          severity: rel.cosine_similarity < 0.3 ? "error" : "warning",
          points: Math.round((0.5 - rel.cosine_similarity) * 100 * 0.10),
        });

        if (tips.length === 0) return null;

        const totalPoints = tips.reduce((s, t) => s + t.points, 0);

        return (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
            {/* Header */}
            <div className="bg-gradient-to-r from-indigo-50 to-blue-50 px-6 py-5 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-bold text-gray-900 flex items-center gap-2 text-lg">
                    <Lightbulb className="h-5 w-5 text-indigo-500" />
                    Steps to increase your ATS score
                  </h3>
                  <p className="text-sm text-gray-500 mt-1">
                    Here are the checks bringing your score down. Fix them to gain up to
                    <span className="font-bold text-indigo-600 ml-1">+{totalPoints} points</span>.
                  </p>
                </div>
                <div className="text-right">
                  <div className="text-3xl font-black text-gray-700">{resumeAnalysis.resume_score}</div>
                  <div className="text-xs text-gray-400">Current Score</div>
                </div>
              </div>
            </div>

            {/* Tips list */}
            <div className="divide-y divide-gray-50">
              {tips.map((tip, i) => (
                <div key={i} className={`flex items-center gap-4 p-5 ${
                  tip.severity === "error" ? "border-l-4 border-red-400" : "border-l-4 border-amber-400"
                }`}>
                  {/* Icon */}
                  <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
                    tip.severity === "error" ? "bg-red-100" : "bg-amber-100"
                  }`}>
                    <XCircle className={`h-4 w-4 ${tip.severity === "error" ? "text-red-500" : "text-amber-500"}`} />
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-gray-900">{tip.title}</span>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${tip.tagColor}`}>{tip.tag}</span>
                    </div>
                    <p className="text-sm text-gray-500 mt-0.5">{tip.desc}</p>
                  </div>

                  {/* Points gain */}
                  <div className="flex-shrink-0 flex items-center gap-3">
                    {tip.points > 0 && (
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 border border-emerald-200 px-2 py-1 rounded-full">
                        +{tip.points} pts
                      </span>
                    )}
                    <Link href="/upload"
                      className="flex items-center gap-1.5 bg-indigo-600 hover:bg-indigo-700 text-white text-xs font-bold px-3 py-2 rounded-lg transition-all shadow-sm">
                      FIX <ArrowRight className="h-3 w-3" />
                    </Link>
                  </div>
                </div>
              ))}
            </div>

            {/* Completed signals */}
            {(() => {
              const done: string[] = [];
              if ((breakdown.keyword_match?.score ?? 0) >= 80) done.push("Keyword Match");
              if ((breakdown.quantified_achievements?.score ?? 0) >= 80) done.push("Quantified Achievements");
              if ((breakdown.action_verbs?.score ?? 0) >= 80) done.push("Action Verbs");
              if ((breakdown.section_detection?.sections_missing?.length ?? 1) === 0) done.push("All Sections Present");
              if ((breakdown.format_compliance?.score ?? 0) >= 80) done.push("Format Compliance");
              if (done.length === 0) return null;
              return (
                <div className="px-6 py-4 bg-emerald-50 border-t border-emerald-100">
                  <p className="text-xs font-semibold text-emerald-700 mb-2 flex items-center gap-1">
                    <CheckCircle className="h-3.5 w-3.5" /> Completed checks
                  </p>
                  <div className="flex flex-wrap gap-2">
                    {done.map((d) => (
                      <span key={d} className="flex items-center gap-1 text-xs bg-white border border-emerald-200 text-emerald-700 px-2.5 py-1 rounded-full font-medium">
                        <CheckCircle className="h-3 w-3" /> {d}
                      </span>
                    ))}
                  </div>
                </div>
              );
            })()}
          </div>
        );
      })()}

      {/* ── Smart Feedback (ResumeWorded style) ─────────────────────────── */}
      {resumeAnalysis.smart_feedback && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
          <div className="p-5 border-b border-gray-100">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Zap className="h-4 w-4 text-violet-500" /> Smart Resume Feedback
            </h3>
            {resumeAnalysis.smart_feedback.overall_verdict && (
              <p className="text-sm text-gray-500 mt-1">{resumeAnalysis.smart_feedback.overall_verdict}</p>
            )}
          </div>

          <div className="p-5 space-y-6">
            {/* Strengths */}
            {resumeAnalysis.smart_feedback.strengths?.length > 0 && (
              <div>
                <p className="text-sm font-bold text-emerald-700 mb-3 flex items-center gap-2">
                  <CheckCircle className="h-4 w-4" /> What's Working Well
                </p>
                <div className="space-y-2">
                  {resumeAnalysis.smart_feedback.strengths.map((s: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
                      <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-bold text-emerald-700 uppercase tracking-wide">{s.section}</span>
                        {s.item && <span className="text-xs text-emerald-600"> · {s.item}</span>}
                        <p className="text-sm text-gray-700 mt-0.5">{s.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Improvements */}
            {resumeAnalysis.smart_feedback.improvements?.length > 0 && (
              <div>
                <p className="text-sm font-bold text-red-600 mb-3 flex items-center gap-2">
                  <XCircle className="h-4 w-4" /> What Needs Fixing
                </p>
                <div className="space-y-3">
                  {resumeAnalysis.smart_feedback.improvements.map((imp: any, i: number) => (
                    <div key={i} className={`p-4 rounded-xl border ${
                      imp.priority === "high" ? "bg-red-50 border-red-200" :
                      imp.priority === "medium" ? "bg-amber-50 border-amber-200" :
                      "bg-gray-50 border-gray-200"
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          imp.priority === "high" ? "bg-red-100 text-red-700" :
                          imp.priority === "medium" ? "bg-amber-100 text-amber-700" :
                          "bg-gray-200 text-gray-600"
                        }`}>{imp.priority}</span>
                        <span className="text-xs font-semibold text-gray-500 uppercase tracking-wide">{imp.section}</span>
                        {imp.item && <span className="text-xs text-gray-400">· {imp.item}</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-800">{imp.issue}</p>
                      {imp.fix && (
                        <p className="text-xs text-gray-600 mt-1.5 bg-white/70 rounded-lg px-3 py-2 border border-gray-100">
                          💡 {imp.fix}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing */}
            {resumeAnalysis.smart_feedback.missing?.length > 0 && (
              <div>
                <p className="text-sm font-bold text-amber-700 mb-3 flex items-center gap-2">
                  <AlertCircle className="h-4 w-4" /> What's Missing
                </p>
                <div className="space-y-2">
                  {resumeAnalysis.smart_feedback.missing.map((m: any, i: number) => (
                    <div key={i} className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                      <p className="text-sm font-semibold text-gray-800">{m.what}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{m.why}</p>
                      {m.example && (
                        <p className="text-xs text-amber-700 mt-1.5 font-medium">Example: {m.example}</p>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
