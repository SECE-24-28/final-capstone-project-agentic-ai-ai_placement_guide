"use client";
import { useAnalysisStore } from "@/lib/store";
import Link from "next/link";
import { Briefcase, TrendingUp, AlertCircle, Building2, ArrowRight } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const predictionConfig: any = {
  "Highly Likely": { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "Likely":        { bg: "bg-green-100",   text: "text-green-700",   border: "border-green-200",   dot: "bg-green-500" },
  "Possible":      { bg: "bg-yellow-100",  text: "text-yellow-700",  border: "border-yellow-200",  dot: "bg-yellow-500" },
  "Unlikely":      { bg: "bg-orange-100",  text: "text-orange-700",  border: "border-orange-200",  dot: "bg-orange-500" },
  "Not Ready":     { bg: "bg-red-100",     text: "text-red-700",     border: "border-red-200",     dot: "bg-red-500" },
};

const jobTypeConfig: any = {
  A: { label: "Skills Only",             bg: "bg-blue-50",   text: "text-blue-700",   border: "border-blue-200" },
  B: { label: "Skills + CGPA",           bg: "bg-purple-50", text: "text-purple-700", border: "border-purple-200" },
  C: { label: "Skills + Experience",     bg: "bg-orange-50", text: "text-orange-700", border: "border-orange-200" },
  D: { label: "Skills+CGPA+Batch+Certs", bg: "bg-rose-50",   text: "text-rose-700",   border: "border-rose-200" },
};

const scoreColor = (s: number) => s >= 70 ? "text-emerald-600" : s >= 50 ? "text-amber-600" : "text-red-500";
const scoreBg    = (s: number) => s >= 70 ? "bg-emerald-50 ring-emerald-200" : s >= 50 ? "bg-amber-50 ring-amber-200" : "bg-red-50 ring-red-200";
const barColors  = ["#3b82f6", "#10b981", "#f59e0b", "#8b5cf6", "#ef4444", "#14b8a6", "#f97316", "#ec4899"];

// Friendly label for each criterion
const criterionLabel: any = {
  skill_score:         "Skills",
  resume_score:        "Resume",
  cgpa_score:          "CGPA",
  experience_score:    "Experience",
  certification_score: "Certifications",
  batch_score:         "Batch Year",
};

export default function JobsPage() {
  const { jobMatches } = useAnalysisStore();

  if (!jobMatches) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <div className="w-20 h-20 bg-gray-100 rounded-2xl flex items-center justify-center mb-4">
          <Briefcase className="h-10 w-10 text-gray-300" />
        </div>
        <h2 className="text-xl font-bold text-gray-700 mb-2">No job matches yet</h2>
        <p className="text-gray-500 mb-6 max-w-sm">Upload your resume and run the full analysis to discover your best-matching companies</p>
        <Link href="/upload" className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-xl font-semibold shadow-lg shadow-blue-200 transition-all">
          Start Analysis <ArrowRight className="h-4 w-4" />
        </Link>
      </div>
    );
  }

  const chartData = jobMatches.company_rankings?.slice(0, 8).map((c: any) => ({
    name: c.company,
    score: Math.round(c.match_score),
  }));
  const pred = predictionConfig[jobMatches.placement_prediction] || predictionConfig["Possible"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Job Matches</h1>
        <p className="text-gray-500 mt-1">
          Analyzed <span className="font-semibold text-gray-700">{jobMatches.total_jobs_analyzed}</span> jobs using dynamic scoring
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl p-5 text-white">
          <p className="text-blue-200 text-xs font-semibold uppercase tracking-wider">Match Probability</p>
          <p className="text-5xl font-black mt-1">{jobMatches.match_probability}%</p>
          <div className="w-full bg-white/20 rounded-full h-1.5 mt-3">
            <div className="h-1.5 bg-white rounded-full" style={{ width: `${jobMatches.match_probability}%` }} />
          </div>
        </div>
        <div className="col-span-2 bg-white rounded-2xl p-5 border border-gray-100 shadow-sm flex items-center gap-5">
          <div className={`w-14 h-14 rounded-2xl flex items-center justify-center flex-shrink-0 ${pred.bg}`}>
            <TrendingUp className={`h-7 w-7 ${pred.text}`} />
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium uppercase tracking-wider">Placement Prediction</p>
            <p className={`text-2xl font-black mt-1 ${pred.text}`}>{jobMatches.placement_prediction}</p>
            <p className="text-gray-500 text-xs mt-1">Based on skills, resume score & job requirements</p>
          </div>
        </div>
      </div>

      {/* Dynamic Scoring Legend */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <p className="text-sm font-bold text-gray-900 mb-3">Dynamic Scoring — weights auto-adjust per job type</p>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          {Object.entries(jobTypeConfig).map(([type, cfg]: any) => (
            <div key={type} className={`rounded-xl px-3 py-2 border ${cfg.bg} ${cfg.border}`}>
              <span className={`text-xs font-bold ${cfg.text}`}>Type {type}</span>
              <p className={`text-xs mt-0.5 ${cfg.text} opacity-80`}>{cfg.label}</p>
            </div>
          ))}
        </div>
        <div className="mt-3 grid grid-cols-2 lg:grid-cols-4 gap-2 text-xs text-gray-500">
          <span>Type A → Skills 70% + Resume 30%</span>
          <span>Type B → Skills 50% + CGPA 30% + Resume 20%</span>
          <span>Type C → Skills 50% + Exp 30% + Resume 20%</span>
          <span>Type D → Skills 40% + CGPA+Batch+Certs 40% + Resume 20%</span>
        </div>
      </div>

      {/* Company Rankings Chart */}
      {chartData?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-600" /> Company Rankings
          </h3>
          <ResponsiveContainer width="100%" height={240}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 40 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#374151", fontWeight: 600 }} axisLine={false} tickLine={false} width={90} />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e5e7eb" }}
                formatter={(v: any) => [`${v}%`, "Match Score"]}
              />
              <Bar dataKey="score" radius={[0, 8, 8, 0]} maxBarSize={28}>
                {chartData.map((_: any, i: number) => <Cell key={i} fill={barColors[i % barColors.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Job Cards */}
      <div className="space-y-4">
        <h3 className="font-bold text-gray-900">All Matches ({jobMatches.job_matches?.length})</h3>
        {jobMatches.job_matches?.map((m: any, i: number) => {
          const p   = predictionConfig[m.placement_prediction] || predictionConfig["Possible"];
          const jt  = jobTypeConfig[m.job_type] || jobTypeConfig["A"];
          const criteria = (m.score_breakdown?.criteria_used || []).filter(
            (c: string) => c !== "criteria_used" && c !== "weights_used" && m.score_breakdown[c] !== undefined
          );
          const weights = m.score_breakdown?.weights_used || {};

          return (
            <div key={i} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:border-blue-200 hover:shadow-md transition-all">
              <div className="flex items-start gap-4">
                {/* Match Score */}
                <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center flex-shrink-0 ring-2 ${scoreBg(m.match_score)}`}>
                  <span className={`text-xl font-black ${scoreColor(m.match_score)}`}>{m.match_score}%</span>
                  <span className="text-[10px] text-gray-400 font-medium">match</span>
                </div>

                <div className="flex-1 min-w-0">
                  {/* Header row */}
                  <div className="flex items-start justify-between gap-2 flex-wrap">
                    <div>
                      <h3 className="font-bold text-gray-900 text-base">{m.company}</h3>
                      <p className="text-gray-500 text-sm">{m.role}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-wrap">
                      {/* Job Type badge */}
                      <span className={`text-xs font-semibold px-2.5 py-1 rounded-full border ${jt.bg} ${jt.text} ${jt.border}`}>
                        Type {m.job_type}: {jt.label}
                      </span>
                      {/* Prediction badge */}
                      <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${p.bg} ${p.text} ${p.border}`}>
                        <span className={`w-1.5 h-1.5 rounded-full ${p.dot}`} />
                        {m.placement_prediction}
                      </span>
                    </div>
                  </div>

                  {/* Score Breakdown with weights */}
                  {criteria.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-gray-400 font-medium mb-2">Score Breakdown (dynamic weights)</p>
                      <div className="flex flex-wrap gap-2">
                        {criteria.map((c: string) => {
                          const val    = m.score_breakdown[c];
                          const weight = weights[c];
                          const label  = criterionLabel[c] || c.replace(/_score$/, "").replace(/_/g, " ");
                          const color  =
                            val >= 80 ? "border-emerald-200 bg-emerald-50 text-emerald-700" :
                            val >= 50 ? "border-amber-200 bg-amber-50 text-amber-700" :
                                        "border-red-200 bg-red-50 text-red-700";
                          return (
                            <div key={c} className={`flex flex-col items-center px-3 py-1.5 rounded-xl border ${color}`}>
                              <span className="text-[10px] font-medium opacity-70 capitalize">{label}</span>
                              <span className="text-sm font-black">{val}%</span>
                              {weight !== undefined && (
                                <span className="text-[10px] opacity-60">wt: {weight}%</span>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    </div>
                  )}

                  {/* Missing skills */}
                  {m.missing_skills?.length > 0 && (
                    <div className="mt-3">
                      <p className="text-xs text-gray-500 flex items-center gap-1 mb-1.5">
                        <AlertCircle className="h-3 w-3 text-amber-500" /> Missing skills
                      </p>
                      <div className="flex flex-wrap gap-1.5">
                        {m.missing_skills.map((s: string, j: number) => (
                          <span key={j} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-0.5 rounded-full font-medium">{s}</span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
