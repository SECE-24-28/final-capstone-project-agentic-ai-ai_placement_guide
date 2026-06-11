"use client";
import { useAnalysisStore } from "@/lib/store";
import { useState } from "react";
import Link from "next/link";
import { Map, BookOpen, Calendar, Target, ExternalLink, Clock } from "lucide-react";

const Tab = ({ active, onClick, children }: any) => (
  <button onClick={onClick}
    className={`px-4 py-2 text-sm font-medium rounded-lg transition-colors ${active ? "bg-blue-600 text-white" : "text-gray-600 hover:bg-gray-100"}`}>
    {children}
  </button>
);

export default function RoadmapPage() {
  const { roadmap, skillGap } = useAnalysisStore();
  const [tab, setTab] = useState<"weekly" | "daily" | "resources" | "milestones" | "mock">("weekly");

  if (!roadmap) {
    return (
      <div className="text-center py-16">
        <Map className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-gray-600 mb-2">No roadmap yet</h2>
        <p className="text-gray-500 mb-6">Complete your resume analysis first to generate a personalized roadmap</p>
        <Link href="/upload" className="bg-blue-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-blue-700 transition-colors">Start Analysis</Link>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Learning Roadmap</h1>
        <p className="text-gray-500 mt-1">
          Personalized {roadmap.duration_weeks}-week plan for <span className="font-medium text-blue-600">{roadmap.target_role}</span>
        </p>
      </div>

      {/* Summary */}
      <div className="grid grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-blue-700">{roadmap.duration_weeks}</p>
          <p className="text-sm text-blue-600 mt-1">Weeks Duration</p>
        </div>
        <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-amber-700">{skillGap?.missing_skills?.length ?? 0}</p>
          <p className="text-sm text-amber-600 mt-1">Skills to Learn</p>
        </div>
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-4 text-center">
          <p className="text-3xl font-bold text-emerald-700">{roadmap.resources?.length ?? 0}</p>
          <p className="text-sm text-emerald-600 mt-1">Resources</p>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Tab active={tab === "weekly"} onClick={() => setTab("weekly")}>📅 Weekly Plan</Tab>
        <Tab active={tab === "daily"} onClick={() => setTab("daily")}>📆 Daily Plan</Tab>
        <Tab active={tab === "milestones"} onClick={() => setTab("milestones")}>🏆 Milestones</Tab>
        <Tab active={tab === "resources"} onClick={() => setTab("resources")}>📚 Resources</Tab>
        <Tab active={tab === "mock"} onClick={() => setTab("mock")}>🎯 Mock Interviews</Tab>
      </div>

      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        {tab === "weekly" && (
          <div className="space-y-4">
            {roadmap.weekly_plan?.map((w: any) => (
              <div key={w.week} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-gray-900">Week {w.week} — {w.focus}</h3>
                  <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded">{w.deliverable}</span>
                </div>
                <ul className="space-y-1">
                  {w.goals?.map((g: string, i: number) => (
                    <li key={i} className="text-sm text-gray-600 flex items-start gap-2">
                      <span className="text-blue-500 mt-0.5">•</span> {g}
                    </li>
                  ))}
                </ul>
                {w.skills_covered?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {w.skills_covered.map((s: string, i: number) => <span key={i} className="text-xs bg-gray-100 text-gray-600 px-2 py-0.5 rounded">{s}</span>)}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "daily" && (
          <div className="space-y-3">
            {roadmap.daily_plan?.map((d: any) => (
              <div key={d.day} className="flex gap-4 p-3 border border-gray-100 rounded-lg hover:bg-gray-50">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                  <span className="text-sm font-bold text-blue-700">D{d.day}</span>
                </div>
                <div className="flex-1">
                  <p className="font-medium text-gray-800">{d.topic}</p>
                  <ul className="mt-1 space-y-0.5">
                    {d.tasks?.map((t: string, i: number) => <li key={i} className="text-xs text-gray-500">→ {t}</li>)}
                  </ul>
                </div>
                <div className="flex items-center gap-1 text-xs text-gray-400">
                  <Clock className="h-3 w-3" /> {d.duration_hours}h
                </div>
              </div>
            ))}
          </div>
        )}

        {tab === "milestones" && (
          <div className="space-y-4">
            {roadmap.monthly_milestones?.map((m: any) => (
              <div key={m.month} className="border-l-4 border-emerald-500 pl-4">
                <h3 className="font-semibold text-gray-900">Month {m.month}: {m.milestone}</h3>
                <p className="text-sm text-gray-600 mt-1">Assessment: {m.assessment}</p>
                {m.skills_mastered?.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {m.skills_mastered.map((s: string, i: number) => (
                      <span key={i} className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded">✓ {s}</span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {tab === "resources" && (
          <div className="space-y-3">
            {roadmap.resources?.map((r: any, i: number) => (
              <div key={i} className="flex items-start justify-between p-3 border border-gray-100 rounded-lg hover:bg-gray-50 gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`text-xs px-2 py-0.5 rounded font-medium ${r.type === "Video" ? "bg-red-100 text-red-700" : r.type === "Course" ? "bg-blue-100 text-blue-700" : r.type === "Practice" ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-700"}`}>{r.type}</span>
                    <span className="text-xs text-gray-500">{r.skill}</span>
                    {r.duration && <span className="text-xs text-gray-400">• {r.duration}</span>}
                  </div>
                  <p className="text-sm font-medium text-gray-800">{r.title}</p>
                </div>
                <a href={r.url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-1 text-blue-600 hover:text-blue-800 text-xs font-medium">
                  Open <ExternalLink className="h-3 w-3" />
                </a>
              </div>
            ))}
          </div>
        )}

        {tab === "mock" && (
          <div className="space-y-3">
            {roadmap.mock_interview_schedule?.map((m: any, i: number) => (
              <div key={i} className="p-4 border border-purple-200 rounded-lg bg-purple-50">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold text-purple-900">Week {m.week}: {m.type}</h3>
                  <span className="text-xs text-purple-600">{m.duration_minutes} min • {m.platform}</span>
                </div>
                <div className="flex flex-wrap gap-1">
                  {m.topics?.map((t: string, j: number) => <span key={j} className="text-xs bg-white text-purple-700 border border-purple-200 px-2 py-0.5 rounded">{t}</span>)}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
