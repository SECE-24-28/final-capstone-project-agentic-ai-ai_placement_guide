"use client";
import { useEffect, useState } from "react";
import { RadialBarChart, RadialBar, ResponsiveContainer } from "recharts";
import { FileText, Target, Briefcase, Award, TrendingUp, ArrowRight, Zap } from "lucide-react";
import { studentApi } from "@/lib/api";
import { useAnalysisStore } from "@/lib/store";
import Link from "next/link";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

export default function DashboardPage() {
  const [profile, setProfile] = useState<any>(null);
  const { resumeAnalysis, skillGap, jobMatches } = useAnalysisStore();

  useEffect(() => {
    studentApi.getProfile().then((r) => setProfile(r.data)).catch(() => {});
  }, []);

  const resumeScore = resumeAnalysis?.resume_score ?? 0;
  const gapPct = skillGap?.skill_gap_percentage ?? 0;
  const matchProb = jobMatches?.match_probability ?? 0;
  const readiness = Math.round(resumeScore * 0.4 + (100 - gapPct) * 0.4 + matchProb * 0.2);

  const readinessColor = readiness >= 70 ? "#10b981" : readiness >= 50 ? "#f59e0b" : "#ef4444";
  const readinessLabel = readiness >= 80 ? "Highly Ready 🚀" : readiness >= 60 ? "Getting There 💪" : "Keep Preparing 📚";

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {profile?.full_name ? `Hey, ${profile.full_name.split(" ")[0]}! 👋` : "Dashboard 👋"}
          </h1>
          <p className="text-gray-500 mt-1">Here&apos;s your placement preparation overview</p>
        </div>
        {!resumeAnalysis && (
          <Link href="/upload"
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-blue-200 transition-all">
            <Zap className="h-4 w-4" /> Start Analysis
          </Link>
        )}
      </div>

      {/* Readiness Banner */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 rounded-2xl p-6 text-white overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-white/5 rounded-full translate-y-1/2" />
        <div className="relative z-10 flex items-center justify-between">
          <div className="space-y-2">
            <p className="text-blue-200 text-sm font-medium uppercase tracking-wider">Placement Readiness</p>
            <div className="flex items-end gap-3">
              <span className="text-7xl font-black">{readiness}</span>
              <span className="text-2xl text-blue-300 mb-2">/100</span>
            </div>
            <p className="text-blue-100 text-lg font-medium">{readinessLabel}</p>
            {profile?.target_role && (
              <span className="inline-block bg-white/10 backdrop-blur-sm border border-white/20 text-white text-xs px-3 py-1.5 rounded-full">
                🎯 Target: {profile.target_role}
              </span>
            )}
          </div>
          <ResponsiveContainer width={180} height={180}>
            <RadialBarChart cx="50%" cy="50%" innerRadius="55%" outerRadius="85%"
              data={[{ value: readiness, fill: readinessColor }]} startAngle={90} endAngle={-270}>
              <RadialBar dataKey="value" maxValue={100} cornerRadius={8} background={{ fill: "rgba(255,255,255,0.1)" }} />
            </RadialBarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "ATS Score", value: `${resumeScore}%`, sub: "Resume quality", icon: FileText, bg: "bg-blue-50", iconBg: "bg-blue-600", iconColor: "text-white", val: resumeScore, color: "text-blue-600" },
          { label: "Skill Gap", value: `${gapPct}%`, sub: `${skillGap?.missing_skills?.length ?? 0} missing`, icon: Target, bg: "bg-amber-50", iconBg: "bg-amber-500", iconColor: "text-white", val: gapPct, color: "text-amber-600" },
          { label: "Skills Found", value: resumeAnalysis?.skills?.length ?? 0, sub: "From resume", icon: Award, bg: "bg-emerald-50", iconBg: "bg-emerald-500", iconColor: "text-white", val: null, color: "text-emerald-600" },
          { label: "Job Matches", value: jobMatches?.job_matches?.length ?? 0, sub: "Top roles", icon: Briefcase, bg: "bg-violet-50", iconBg: "bg-violet-600", iconColor: "text-white", val: null, color: "text-violet-600" },
        ].map((s) => (
          <div key={s.label} className={`${s.bg} rounded-2xl p-5 border border-white`}>
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 ${s.iconBg} rounded-xl flex items-center justify-center shadow-sm`}>
                <s.icon className={`h-4 w-4 ${s.iconColor}`} />
              </div>
              {s.val !== null && (
                <div className="w-12 h-1.5 bg-white rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${s.iconBg}`} style={{ width: `${Math.min(s.val, 100)}%` }} />
                </div>
              )}
            </div>
            <p className={`text-3xl font-black ${s.color}`}>{s.value}</p>
            <p className="text-xs text-gray-500 mt-1 font-medium">{s.label}</p>
            <p className="text-xs text-gray-400">{s.sub}</p>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Skills */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Award className="h-4 w-4 text-blue-600" /> Extracted Skills
            </h3>
            {resumeAnalysis && (
              <Link href="/analysis" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          {resumeAnalysis?.skills?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {resumeAnalysis.skills.map((s: any, i: number) => (
                <span key={i} className="px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-sm"
                  style={{ backgroundColor: COLORS[i % COLORS.length] }}>
                  {s.name}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-center py-10">
              <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Award className="h-7 w-7 text-gray-300" />
              </div>
              <p className="text-gray-500 text-sm font-medium">No resume uploaded yet</p>
              <Link href="/upload" className="text-blue-600 text-sm font-semibold hover:underline mt-2 inline-flex items-center gap-1">
                Upload Resume <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>

        {/* Top Matches */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-emerald-600" /> Top Job Matches
            </h3>
            {jobMatches && (
              <Link href="/jobs" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          {jobMatches?.job_matches?.length > 0 ? (
            <div className="space-y-3">
              {jobMatches.job_matches.slice(0, 5).map((m: any, i: number) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                  <div className="w-8 h-8 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-xs font-bold text-gray-600 shadow-sm flex-shrink-0">
                    {i + 1}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-semibold text-gray-800 truncate">{m.company}</p>
                    <p className="text-xs text-gray-500 truncate">{m.role}</p>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div className="w-16 bg-gray-200 rounded-full h-1.5">
                      <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${m.match_score}%` }} />
                    </div>
                    <span className="text-sm font-bold text-gray-700 w-10 text-right">{m.match_score}%</span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-10">
              <div className="w-14 h-14 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Briefcase className="h-7 w-7 text-gray-300" />
              </div>
              <p className="text-gray-500 text-sm font-medium">No job matches yet</p>
              <Link href="/upload" className="text-blue-600 text-sm font-semibold hover:underline mt-2 inline-flex items-center gap-1">
                Start Analysis <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* CTA */}
      {!resumeAnalysis && (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-6 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-blue-900 text-lg">🚀 Ready to get started?</h3>
            <p className="text-blue-600 text-sm mt-1">Upload your resume and let our 4 AI agents analyze everything in one click</p>
          </div>
          <Link href="/upload"
            className="flex-shrink-0 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-lg shadow-blue-200 transition-all">
            Upload Resume <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      )}
    </div>
  );
}
