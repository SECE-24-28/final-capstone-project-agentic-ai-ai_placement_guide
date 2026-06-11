"use client";
import { useEffect, useState } from "react";
import { RadialBarChart, RadialBar, PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from "recharts";
import { FileText, Target, Briefcase, Award, TrendingUp, ArrowRight, Zap, BookOpen, CheckCircle, XCircle, Clock, Info, ChevronDown, ChevronUp } from "lucide-react";
import { studentApi } from "@/lib/api";
import { useAnalysisStore } from "@/lib/store";
import Link from "next/link";

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#14b8a6", "#f97316"];

export default function DashboardPage() {
  const [profile, setProfile] = useState<any>(null);
  const [showScoreInfo, setShowScoreInfo] = useState(false);
  const { resumeAnalysis, skillGap, jobMatches, roadmap } = useAnalysisStore();

  useEffect(() => {
    studentApi.getProfile().then((r) => setProfile(r.data)).catch(() => {});
  }, []);

  const resumeScore   = resumeAnalysis?.resume_score ?? 0;
  const gapPct        = skillGap?.skill_gap_percentage ?? 0;
  const matchProb     = jobMatches?.match_probability ?? 0;
  const matchedCount  = skillGap?.matched_skills?.length ?? 0;
  const missingCount  = skillGap?.missing_skills?.length ?? 0;
  const totalRequired = matchedCount + missingCount;
  const skillCoverage = totalRequired > 0 ? Math.round((matchedCount / totalRequired) * 100) : 0;

  // Readiness = ATS Score(40%) + Skill Coverage(40%) + Job Match(20%)
  const readiness      = Math.round(resumeScore * 0.4 + skillCoverage * 0.4 + matchProb * 0.2);
  const readinessColor = readiness >= 70 ? "#10b981" : readiness >= 50 ? "#f59e0b" : "#ef4444";
  const readinessLabel = readiness >= 80 ? "Highly Ready 🚀" : readiness >= 60 ? "Getting There 💪" : "Keep Preparing 📚";

  const breakdownData = resumeAnalysis ? [
    { name: "ATS Score",      value: resumeScore,    weight: "40%", color: "#3b82f6", icon: FileText,   href: "/analysis" },
    { name: "Skill Coverage", value: skillCoverage,  weight: "40%", color: "#10b981", icon: Target,     href: "/analysis" },
    { name: "Job Match",      value: Math.round(matchProb), weight: "20%", color: "#8b5cf6", icon: Briefcase, href: "/jobs" },
  ] : [];

  const topJob = jobMatches?.job_matches?.[0];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {profile?.full_name ? `Hey, ${profile.full_name.split(" ")[0]}! 👋` : "Dashboard 👋"}
          </h1>
          <p className="text-gray-500 mt-1">Your placement preparation overview</p>
        </div>
        <Link href="/upload"
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-lg shadow-blue-200 transition-all">
          <Zap className="h-4 w-4" /> {resumeAnalysis ? "Re-Analyze" : "Start Analysis"}
        </Link>
      </div>

      {/* Readiness Banner */}
      <div className="bg-gradient-to-r from-blue-600 via-blue-700 to-indigo-700 rounded-2xl p-6 text-white overflow-hidden relative">
        <div className="absolute top-0 right-0 w-64 h-64 bg-white/5 rounded-full -translate-y-1/2 translate-x-1/4" />
        <div className="absolute bottom-0 left-1/3 w-48 h-48 bg-white/5 rounded-full translate-y-1/2" />
        <div className="relative z-10 flex items-center justify-between gap-6">
          <div className="space-y-2 flex-1">
            <p className="text-blue-200 text-xs font-semibold uppercase tracking-wider">Placement Readiness Score</p>
            <div className="flex items-end gap-3">
              <span className="text-7xl font-black">{readiness}</span>
              <span className="text-2xl text-blue-300 mb-2">/100</span>
            </div>
            <p className="text-blue-100 text-lg font-medium">{readinessLabel}</p>
            <div className="flex flex-wrap gap-2 pt-1">
              {profile?.target_role && (
                <span className="bg-white/10 border border-white/20 text-white text-xs px-3 py-1.5 rounded-full">
                  🎯 {profile.target_role}
                </span>
              )}
              {profile?.student_level && (
                <span className="bg-white/10 border border-white/20 text-white text-xs px-3 py-1.5 rounded-full capitalize">
                  📊 {profile.student_level}
                </span>
              )}
              {roadmap && (
                <span className="bg-white/10 border border-white/20 text-white text-xs px-3 py-1.5 rounded-full">
                  🗓 {roadmap.duration_weeks}‑week roadmap
                </span>
              )}
            </div>
            {/* Formula breakdown */}
            {resumeAnalysis && (
              <div className="flex gap-3 pt-2 flex-wrap">
                <span className="text-xs text-blue-200">ATS {resumeScore}×0.4 = {Math.round(resumeScore*0.4)}</span>
                <span className="text-blue-400">+</span>
                <span className="text-xs text-blue-200">Skills {skillCoverage}×0.4 = {Math.round(skillCoverage*0.4)}</span>
                <span className="text-blue-400">+</span>
                <span className="text-xs text-blue-200">Match {Math.round(matchProb)}×0.2 = {Math.round(matchProb*0.2)}</span>
              </div>
            )}
          </div>
          <div className="flex-shrink-0 w-[160px] h-[160px]">
            <RadialBarChart width={160} height={160} cx={80} cy={80} innerRadius={50} outerRadius={72}
              data={[{ value: readiness, fill: readinessColor }]} startAngle={90} endAngle={-270}>
              <RadialBar dataKey="value" maxValue={100} cornerRadius={8} background={{ fill: "rgba(255,255,255,0.1)" }} />
            </RadialBarChart>
          </div>
        </div>
      </div>

      {/* 4 Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: "ATS Score",     value: `${resumeScore}`,   unit: "/100", sub: "Resume quality",                icon: FileText,  bg: "bg-blue-50",   iconBg: "bg-blue-600",   color: "text-blue-700",   href: "/analysis", bar: resumeScore },
          { label: "Skill Gap",     value: `${gapPct}`,        unit: "%",   sub: `${missingCount} skills missing`, icon: Target,    bg: "bg-amber-50",  iconBg: "bg-amber-500",  color: "text-amber-700",  href: "/analysis", bar: 100 - gapPct },
          { label: "Skills Found",  value: `${resumeAnalysis?.skills?.length ?? 0}`, unit: "", sub: `${matchedCount} role-matched`, icon: Award, bg: "bg-emerald-50", iconBg: "bg-emerald-500", color: "text-emerald-700", href: "/analysis", bar: null },
          { label: "Job Matches",   value: `${jobMatches?.job_matches?.length ?? 0}`, unit: "", sub: topJob ? `Best: ${topJob.company}` : "Run analysis", icon: Briefcase, bg: "bg-violet-50", iconBg: "bg-violet-600", color: "text-violet-700", href: "/jobs", bar: null },
        ].map((s) => (
          <Link key={s.label} href={s.href} className={`${s.bg} rounded-2xl p-5 border border-white hover:shadow-md transition-all`}>
            <div className="flex items-center justify-between mb-3">
              <div className={`w-9 h-9 ${s.iconBg} rounded-xl flex items-center justify-center shadow-sm`}>
                <s.icon className="h-4 w-4 text-white" />
              </div>
              {s.bar !== null && (
                <div className="w-12 h-1.5 bg-white rounded-full overflow-hidden">
                  <div className={`h-full rounded-full ${s.iconBg}`} style={{ width: `${Math.min(Math.max(s.bar ?? 0, 0), 100)}%` }} />
                </div>
              )}
            </div>
            <div className="flex items-end gap-1">
              <p className={`text-3xl font-black ${s.color}`}>{s.value}</p>
              {s.unit && <p className={`text-sm mb-1 ${s.color} opacity-60`}>{s.unit}</p>}
            </div>
            <p className="text-xs text-gray-500 mt-1 font-medium">{s.label}</p>
            <p className="text-xs text-gray-400">{s.sub}</p>
          </Link>
        ))}
      </div>

      {/* Readiness Breakdown + Skill Gap side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

        {/* Readiness Formula Breakdown */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <TrendingUp className="h-4 w-4 text-blue-600" /> Readiness Breakdown
          </h3>
          {resumeAnalysis ? (
            <div className="space-y-4">
              {breakdownData.map((item) => (
                <Link href={item.href} key={item.name} className="block group">
                  <div className="flex items-center justify-between mb-1">
                    <div className="flex items-center gap-2">
                      <item.icon className="h-3.5 w-3.5 text-gray-400" />
                      <span className="text-sm font-medium text-gray-700">{item.name}</span>
                      <span className="text-xs text-gray-400">({item.weight} weight)</span>
                    </div>
                    <span className="text-sm font-bold" style={{ color: item.color }}>{item.value}%</span>
                  </div>
                  <div className="w-full bg-gray-100 rounded-full h-2">
                    <div className="h-2 rounded-full transition-all" style={{ width: `${item.value}%`, backgroundColor: item.color }} />
                  </div>
                </Link>
              ))}
              <div className="pt-3 border-t border-gray-100 flex items-center justify-between">
                <span className="text-sm text-gray-500">Total Readiness Score</span>
                <span className="text-xl font-black" style={{ color: readinessColor }}>{readiness}/100</span>
              </div>
            </div>
          ) : (
            <div className="text-center py-8">
              <FileText className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">Upload resume to see breakdown</p>
              <Link href="/upload" className="mt-3 inline-flex items-center gap-1 text-blue-600 text-sm font-semibold hover:underline">
                Upload <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>

        {/* Skill Gap Summary */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Target className="h-4 w-4 text-amber-500" /> Skill Gap Summary
            </h3>
            {skillGap && (
              <Link href="/analysis" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                Full Analysis <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          {skillGap ? (
            <div className="space-y-4">
              {/* Donut chart */}
              <div className="flex items-center gap-4">
                <div className="w-24 h-24 flex-shrink-0">
                  <PieChart width={96} height={96}>
                    <Pie data={[
                      { name: "Matched", value: matchedCount },
                      { name: "Missing", value: missingCount },
                    ]} cx={48} cy={48} innerRadius={28} outerRadius={44} dataKey="value" startAngle={90} endAngle={-270}>
                      <Cell fill="#10b981" />
                      <Cell fill="#fca5a5" />
                    </Pie>
                    <Tooltip formatter={(v: any, n: any) => [v, n]} contentStyle={{ fontSize: "11px", borderRadius: "8px" }} />
                  </PieChart>
                </div>
                <div className="flex-1 space-y-2">
                  <div className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-emerald-500 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{matchedCount} skills matched</span>
                    <span className="ml-auto text-sm font-bold text-emerald-600">{skillCoverage}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <XCircle className="h-4 w-4 text-red-400 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{missingCount} skills missing</span>
                    <span className="ml-auto text-sm font-bold text-red-500">{gapPct}%</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="h-4 w-4 text-blue-400 flex-shrink-0" />
                    <span className="text-sm text-gray-600">{roadmap?.duration_weeks ?? "?"} weeks to close gap</span>
                  </div>
                </div>
              </div>
              {/* Top priority skills */}
              {skillGap.priority_skills?.length > 0 && (
                <div>
                  <p className="text-xs text-gray-400 font-medium mb-2">Top priority skills to learn</p>
                  <div className="flex flex-wrap gap-1.5">
                    {skillGap.priority_skills.slice(0, 6).map((s: string, i: number) => (
                      <span key={i} className="text-xs bg-amber-50 text-amber-700 border border-amber-200 px-2.5 py-1 rounded-full font-medium">{s}</span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <Target className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">No skill gap analysis yet</p>
              <Link href="/upload" className="mt-3 inline-flex items-center gap-1 text-blue-600 text-sm font-semibold hover:underline">
                Run Analysis <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Skills + Top Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Extracted Skills */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Award className="h-4 w-4 text-blue-600" /> Extracted Skills
              {resumeAnalysis?.skills?.length > 0 && (
                <span className="text-xs bg-blue-100 text-blue-600 px-2 py-0.5 rounded-full font-semibold">{resumeAnalysis.skills.length}</span>
              )}
            </h3>
            {resumeAnalysis && (
              <Link href="/analysis" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                Full Report <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          {resumeAnalysis?.skills?.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {resumeAnalysis.skills.map((s: any, i: number) => (
                <span key={i} className="px-3 py-1.5 rounded-full text-xs font-semibold text-white shadow-sm"
                  style={{ backgroundColor: COLORS[i % COLORS.length] }}>
                  {s.name}
                  {s.proficiency && <span className="ml-1 opacity-75 text-[10px]">· {s.proficiency}</span>}
                </span>
              ))}
            </div>
          ) : (
            <div className="text-center py-10">
              <Award className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">Upload resume to extract skills</p>
              <Link href="/upload" className="mt-2 inline-flex items-center gap-1 text-blue-600 text-sm font-semibold hover:underline">
                Upload Resume <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>

        {/* Top Job Matches */}
        <div className="bg-white rounded-2xl p-6 border border-gray-100 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-bold text-gray-900 flex items-center gap-2">
              <Briefcase className="h-4 w-4 text-violet-600" /> Top Job Matches
            </h3>
            {jobMatches && (
              <Link href="/jobs" className="text-xs text-blue-600 hover:underline flex items-center gap-1">
                View all <ArrowRight className="h-3 w-3" />
              </Link>
            )}
          </div>
          {jobMatches?.job_matches?.length > 0 ? (
            <div className="space-y-2.5">
              {jobMatches.job_matches.slice(0, 5).map((m: any, i: number) => {
                const scoreColor = m.match_score >= 70 ? "text-emerald-600 bg-emerald-50" : m.match_score >= 50 ? "text-amber-600 bg-amber-50" : "text-red-500 bg-red-50";
                return (
                  <div key={i} className="flex items-center gap-3 p-3 rounded-xl bg-gray-50 hover:bg-gray-100 transition-colors">
                    <div className="w-7 h-7 rounded-lg bg-white border border-gray-200 flex items-center justify-center text-xs font-bold text-gray-500 flex-shrink-0 shadow-sm">
                      {i + 1}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-gray-800 truncate">{m.company}</p>
                      <p className="text-xs text-gray-500 truncate">{m.role}</p>
                    </div>
                    <div className="flex items-center gap-2 flex-shrink-0">
                      <div className="w-14 bg-gray-200 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-blue-500" style={{ width: `${m.match_score}%` }} />
                      </div>
                      <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${scoreColor}`}>{m.match_score}%</span>
                    </div>
                  </div>
                );
              })}
            </div>
          ) : (
            <div className="text-center py-10">
              <Briefcase className="h-10 w-10 text-gray-200 mx-auto mb-3" />
              <p className="text-gray-400 text-sm">No job matches yet</p>
              <Link href="/upload" className="mt-2 inline-flex items-center gap-1 text-blue-600 text-sm font-semibold hover:underline">
                Start Analysis <ArrowRight className="h-3 w-3" />
              </Link>
            </div>
          )}
        </div>
      </div>

      {/* Roadmap Teaser */}
      {roadmap ? (
        <div className="bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200 rounded-2xl p-5 flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center">
              <BookOpen className="h-6 w-6 text-emerald-600" />
            </div>
            <div>
              <p className="font-bold text-emerald-900">Your {roadmap.duration_weeks}-Week Learning Roadmap is Ready!</p>
              <p className="text-emerald-700 text-sm mt-0.5">
                {missingCount} skills to learn · {roadmap.resources?.length ?? 0} resources · {roadmap.mock_interview_schedule?.length ?? 0} mock interviews
              </p>
            </div>
          </div>
          <Link href="/roadmap"
            className="flex-shrink-0 flex items-center gap-2 bg-emerald-600 hover:bg-emerald-700 text-white px-4 py-2.5 rounded-xl text-sm font-semibold shadow-md transition-all">
            View Roadmap <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      ) : !resumeAnalysis ? (
        <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-2xl p-6 flex items-center justify-between">
          <div>
            <h3 className="font-bold text-blue-900 text-lg">🚀 Ready to get started?</h3>
            <p className="text-blue-600 text-sm mt-1">Upload your resume → 4 AI agents analyze everything in seconds</p>
          </div>
          <Link href="/upload"
            className="flex-shrink-0 flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-3 rounded-xl text-sm font-semibold shadow-lg shadow-blue-200 transition-all">
            Upload Resume <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      ) : null}

      {/* How Scores Are Calculated */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <button
          onClick={() => setShowScoreInfo((v) => !v)}
          className="w-full flex items-center justify-between px-6 py-4 text-left hover:bg-gray-50 transition-colors">
          <span className="font-bold text-gray-900 flex items-center gap-2">
            <Info className="h-4 w-4 text-blue-500" /> How are scores calculated?
          </span>
          {showScoreInfo
            ? <ChevronUp className="h-4 w-4 text-gray-400" />
            : <ChevronDown className="h-4 w-4 text-gray-400" />}
        </button>
        {showScoreInfo && (
          <div className="px-6 pb-6 space-y-5 border-t border-gray-50">
            {/* ATS Score */}
            <div className="pt-4">
              <p className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <FileText className="h-4 w-4 text-blue-600" /> ATS Score (0–100)
              </p>
              <p className="text-sm text-gray-500 mb-3">Groq AI analyzes your resume text and scores it on 7 criteria:</p>
              <div className="space-y-2">
                {[
                  { label: "Contact Info",              pts: 10, desc: "Name, email, phone present" },
                  { label: "Skills Section",            pts: 25, desc: "Quantity, relevance, technical depth" },
                  { label: "Education",                 pts: 15, desc: "Degree, institution, CGPA" },
                  { label: "Work Experience",           pts: 20, desc: "Internships, roles, descriptions" },
                  { label: "Projects",                  pts: 15, desc: "Quality, tech stack, impact" },
                  { label: "Certifications",            pts: 10, desc: "Relevant certifications" },
                  { label: "Formatting & Keywords",     pts: 5,  desc: "ATS compatibility, keywords" },
                ].map((c) => (
                  <div key={c.label} className="flex items-center gap-3">
                    <div className="w-8 h-8 bg-blue-50 rounded-lg flex items-center justify-center flex-shrink-0">
                      <span className="text-xs font-black text-blue-600">{c.pts}</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-800">{c.label}</span>
                        <span className="text-xs text-gray-400">{c.pts} pts</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1 mt-1">
                        <div className="h-1 rounded-full bg-blue-400" style={{ width: `${c.pts}%` }} />
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{c.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Readiness Score */}
            <div className="pt-2 border-t border-gray-100">
              <p className="font-semibold text-gray-900 mb-2 flex items-center gap-2">
                <TrendingUp className="h-4 w-4 text-emerald-600" /> Placement Readiness Score
              </p>
              <p className="text-sm text-gray-500 mb-3">Weighted combination of 3 signals:</p>
              <div className="space-y-3">
                {[
                  { label: "ATS Score",      weight: 40, color: "bg-blue-500",   desc: "How strong your resume is" },
                  { label: "Skill Coverage", weight: 40, color: "bg-emerald-500", desc: "matched skills ÷ total required skills × 100" },
                  { label: "Job Match",      weight: 20, color: "bg-violet-500",  desc: "Top job match score from Agent 4" },
                ].map((s) => (
                  <div key={s.label} className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ backgroundColor: s.color.replace("bg-", "").includes("blue") ? "#eff6ff" : s.color.includes("emerald") ? "#ecfdf5" : "#f5f3ff" }}>
                      <span className="text-xs font-black text-gray-700">{s.weight}%</span>
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span className="text-sm font-medium text-gray-800">{s.label}</span>
                        <span className="text-xs font-bold text-gray-600">× {s.weight / 100}</span>
                      </div>
                      <div className="w-full bg-gray-100 rounded-full h-1.5 mt-1">
                        <div className={`h-1.5 rounded-full ${s.color}`} style={{ width: `${s.weight}%` }} />
                      </div>
                      <p className="text-xs text-gray-400 mt-0.5">{s.desc}</p>
                    </div>
                  </div>
                ))}
              </div>
              <div className="mt-3 p-3 bg-gray-50 rounded-xl border border-gray-100">
                <p className="text-xs font-mono text-gray-600">
                  Readiness = (ATS × 0.4) + (SkillCoverage × 0.4) + (JobMatch × 0.2)
                </p>
                {resumeAnalysis && (
                  <p className="text-xs font-mono text-blue-600 mt-1">
                    = ({resumeScore} × 0.4) + ({skillCoverage} × 0.4) + ({Math.round(matchProb)} × 0.2) = <strong>{readiness}</strong>
                  </p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
