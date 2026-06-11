"use client";
import { useAnalysisStore } from "@/lib/store";
import Link from "next/link";
import { Briefcase, TrendingUp, AlertCircle, Building2, ChevronRight, ArrowRight } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from "recharts";

const predictionConfig: any = {
  "Highly Likely": { bg: "bg-emerald-100", text: "text-emerald-700", border: "border-emerald-200", dot: "bg-emerald-500" },
  "Likely": { bg: "bg-green-100", text: "text-green-700", border: "border-green-200", dot: "bg-green-500" },
  "Possible": { bg: "bg-yellow-100", text: "text-yellow-700", border: "border-yellow-200", dot: "bg-yellow-500" },
  "Unlikely": { bg: "bg-orange-100", text: "text-orange-700", border: "border-orange-200", dot: "bg-orange-500" },
  "Not Ready": { bg: "bg-red-100", text: "text-red-700", border: "border-red-200", dot: "bg-red-500" },
};

const scoreColor = (s: number) => s >= 70 ? "text-emerald-600" : s >= 50 ? "text-amber-600" : "text-red-500";
const scoreBg = (s: number) => s >= 70 ? "bg-emerald-50 ring-emerald-200" : s >= 50 ? "bg-amber-50 ring-amber-200" : "bg-red-50 ring-red-200";
const barColor = (_: any, i: number) => i === 0 ? "#3b82f6" : i === 1 ? "#10b981" : i === 2 ? "#f59e0b" : "#94a3b8";

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

  const chartData = jobMatches.company_rankings?.slice(0, 8).map((c: any) => ({ name: c.company, score: Math.round(c.match_score) }));
  const pred = predictionConfig[jobMatches.placement_prediction] || predictionConfig["Possible"];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Job Matches</h1>
        <p className="text-gray-500 mt-1">
          Analyzed <span className="font-semibold text-gray-700">{jobMatches.total_jobs_analyzed}</span> jobs
        </p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-gradient-to-br from-blue-600 to-indigo-600 rounded-2xl p-5 text-white col-span-1">
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

      {/* Chart */}
      {chartData?.length > 0 && (
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-5 flex items-center gap-2">
            <Building2 className="h-4 w-4 text-blue-600" /> Company Rankings
          </h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
              <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11, fill: "#94a3b8" }} axisLine={false} tickLine={false} />
              <YAxis type="category" dataKey="name" tick={{ fontSize: 12, fill: "#374151", fontWeight: 600 }} axisLine={false} tickLine={false} width={90} />
              <Tooltip
                contentStyle={{ borderRadius: "12px", border: "1px solid #e5e7eb", boxShadow: "0 4px 20px rgba(0,0,0,0.08)" }}
                formatter={(v: any) => [`${v}%`, "Match Score"]} />
              <Bar dataKey="score" radius={[0, 8, 8, 0]} maxBarSize={32}>
                {chartData.map((_: any, i: number) => <Cell key={i} fill={barColor(_, i)} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Job Cards */}
      <div className="space-y-4">
        <h3 className="font-bold text-gray-900">All Matches ({jobMatches.job_matches?.length})</h3>
        {jobMatches.job_matches?.map((m: any, i: number) => {
          const p = predictionConfig[m.placement_prediction] || predictionConfig["Possible"];
          return (
            <div key={i} className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm hover:border-blue-200 hover:shadow-md transition-all">
              <div className="flex items-start gap-4">
                {/* Score */}
                <div className={`w-16 h-16 rounded-2xl flex flex-col items-center justify-center flex-shrink-0 ring-2 ${scoreBg(m.match_score)}`}>
                  <span className={`text-xl font-black ${scoreColor(m.match_score)}`}>{m.match_score}%</span>
                  <span className="text-[10px] text-gray-400 font-medium">match</span>
                </div>

                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div>
                      <h3 className="font-bold text-gray-900 text-base">{m.company}</h3>
                      <p className="text-gray-500 text-sm">{m.role}</p>
                    </div>
                    <span className={`flex-shrink-0 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold border ${p.bg} ${p.text} ${p.border}`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${p.dot}`} />
                      {m.placement_prediction}
                    </span>
                  </div>

                  {/* Score breakdown */}
                  {m.score_breakdown?.criteria_used?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {m.score_breakdown.criteria_used.map((c: string) => {
                        const val = m.score_breakdown[c];
                        if (val === undefined || c === "criteria_used") return null;
                        const label = c.replace(/_score$/, "").replace(/_/g, " ");
                        return (
                          <div key={c} className="flex items-center gap-1.5 bg-gray-50 border border-gray-200 rounded-lg px-2.5 py-1">
                            <span className="text-xs text-gray-500 capitalize">{label}</span>
                            <span className="text-xs font-bold text-gray-800">{val}%</span>
                          </div>
                        );
                      })}
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
