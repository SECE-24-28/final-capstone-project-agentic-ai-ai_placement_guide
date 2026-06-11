"use client";
import { useAnalysisStore, useTodoStore } from "@/lib/store";
import { useState } from "react";
import Link from "next/link";
import {
  Map, ExternalLink, Clock, CheckCircle2, Circle,
  Trophy, BookOpen, CalendarDays, Mic, RotateCcw, ChevronDown, ChevronUp
} from "lucide-react";

const Tab = ({ active, onClick, children }: any) => (
  <button onClick={onClick}
    className={`px-4 py-2 text-sm font-semibold rounded-xl transition-all ${
      active ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "text-gray-500 hover:bg-gray-100 hover:text-gray-800"
    }`}>
    {children}
  </button>
);

const typeColor: any = {
  Video:    "bg-red-100 text-red-700",
  Course:   "bg-blue-100 text-blue-700",
  Practice: "bg-green-100 text-green-700",
  Article:  "bg-gray-100 text-gray-700",
};

export default function RoadmapPage() {
  const { roadmap, skillGap } = useAnalysisStore();
  const { checked, toggle, resetTodos } = useTodoStore();
  const [tab, setTab] = useState<"daily" | "weekly" | "milestones" | "resources" | "mock">("daily");
  const [expandedWeeks, setExpandedWeeks] = useState<Record<number, boolean>>({ 1: true });

  if (!roadmap) {
    return (
      <div className="flex flex-col items-center justify-center py-24 text-center">
        <Map className="h-16 w-16 text-gray-200 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-700 mb-2">No roadmap yet</h2>
        <p className="text-gray-500 mb-6">Complete your resume analysis first to generate a personalized roadmap</p>
        <Link href="/upload" className="bg-blue-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors shadow-lg shadow-blue-200">
          Start Analysis
        </Link>
      </div>
    );
  }

  // ── Progress calculation ─────────────────────────────────────────────────
  const allDailyKeys  = (roadmap.daily_plan  ?? []).flatMap((d: any) =>
    (d.tasks ?? []).map((_: any, i: number) => `daily-${d.day}-${i}`)
  );
  const allWeeklyKeys = (roadmap.weekly_plan ?? []).flatMap((w: any) =>
    (w.goals ?? []).map((_: any, i: number) => `weekly-${w.week}-${i}`)
  );
  const allKeys       = [...allDailyKeys, ...allWeeklyKeys];
  const doneCount     = allKeys.filter((k) => checked[k]).length;
  const totalCount    = allKeys.length;
  const progressPct   = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;

  const dailyDone  = allDailyKeys.filter((k) => checked[k]).length;
  const weeklyDone = allWeeklyKeys.filter((k) => checked[k]).length;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Learning Roadmap</h1>
          <p className="text-gray-500 mt-1">
            {roadmap.duration_weeks}-week plan for{" "}
            <span className="font-semibold text-blue-600">{roadmap.target_role}</span>
          </p>
        </div>
        <button onClick={resetTodos}
          className="flex items-center gap-1.5 text-xs text-gray-400 hover:text-red-500 border border-gray-200 hover:border-red-200 px-3 py-2 rounded-xl transition-all">
          <RotateCcw className="h-3.5 w-3.5" /> Reset Progress
        </button>
      </div>

      {/* Overall Progress Bar */}
      <div className="bg-white rounded-2xl p-5 border border-gray-100 shadow-sm">
        <div className="flex items-center justify-between mb-3">
          <div>
            <p className="font-bold text-gray-900">Overall Progress</p>
            <p className="text-xs text-gray-500 mt-0.5">
              {doneCount} of {totalCount} tasks completed
            </p>
          </div>
          <div className="text-right">
            <span className="text-3xl font-black text-blue-600">{progressPct}%</span>
            <p className="text-xs text-gray-400">complete</p>
          </div>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-3">
          <div
            className="h-3 rounded-full transition-all duration-500"
            style={{
              width: `${progressPct}%`,
              background: progressPct >= 80 ? "#10b981" : progressPct >= 40 ? "#3b82f6" : "#f59e0b",
            }}
          />
        </div>
        {/* Mini stats */}
        <div className="flex gap-4 mt-4 flex-wrap">
          {[
            { label: "Weeks",       value: roadmap.duration_weeks,              color: "text-blue-600",   bg: "bg-blue-50" },
            { label: "Skills",      value: skillGap?.missing_skills?.length ?? 0, color: "text-amber-600",  bg: "bg-amber-50" },
            { label: "Resources",   value: roadmap.resources?.length ?? 0,      color: "text-emerald-600", bg: "bg-emerald-50" },
            { label: "Daily tasks", value: `${dailyDone}/${allDailyKeys.length}`,  color: "text-violet-600",  bg: "bg-violet-50" },
            { label: "Weekly goals",value: `${weeklyDone}/${allWeeklyKeys.length}`, color: "text-rose-600", bg: "bg-rose-50" },
          ].map((s) => (
            <div key={s.label} className={`flex-1 min-w-[80px] ${s.bg} rounded-xl px-3 py-2 text-center`}>
              <p className={`font-black text-lg ${s.color}`}>{s.value}</p>
              <p className="text-xs text-gray-500">{s.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 flex-wrap">
        <Tab active={tab === "daily"}      onClick={() => setTab("daily")}>
          <span className="flex items-center gap-1.5"><CalendarDays className="h-3.5 w-3.5" /> Daily Tasks</span>
        </Tab>
        <Tab active={tab === "weekly"}     onClick={() => setTab("weekly")}>
          <span className="flex items-center gap-1.5"><CheckCircle2 className="h-3.5 w-3.5" /> Weekly Goals</span>
        </Tab>
        <Tab active={tab === "milestones"} onClick={() => setTab("milestones")}>
          <span className="flex items-center gap-1.5"><Trophy className="h-3.5 w-3.5" /> Milestones</span>
        </Tab>
        <Tab active={tab === "resources"}  onClick={() => setTab("resources")}>
          <span className="flex items-center gap-1.5"><BookOpen className="h-3.5 w-3.5" /> Resources</span>
        </Tab>
        <Tab active={tab === "mock"}       onClick={() => setTab("mock")}>
          <span className="flex items-center gap-1.5"><Mic className="h-3.5 w-3.5" /> Mock Interviews</span>
        </Tab>
      </div>

      {/* ── DAILY TASKS (todo list) ─────────────────────────────────────── */}
      {tab === "daily" && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500 px-1">
            Check off tasks as you complete them — progress is saved automatically.
          </p>
          {roadmap.daily_plan?.map((d: any) => {
            const dayKeys  = (d.tasks ?? []).map((_: any, i: number) => `daily-${d.day}-${i}`);
            const dayDone  = dayKeys.filter((k: string) => checked[k]).length;
            const dayTotal = dayKeys.length;
            const allDone  = dayDone === dayTotal && dayTotal > 0;

            return (
              <div key={d.day}
                className={`bg-white rounded-2xl border shadow-sm transition-all ${
                  allDone ? "border-emerald-200 bg-emerald-50/30" : "border-gray-100"
                }`}>
                <div className="flex items-center gap-4 p-4">
                  {/* Day badge */}
                  <div className={`w-12 h-12 rounded-xl flex flex-col items-center justify-center flex-shrink-0 font-bold text-sm transition-all ${
                    allDone ? "bg-emerald-500 text-white" : "bg-blue-100 text-blue-700"
                  }`}>
                    {allDone
                      ? <CheckCircle2 className="h-5 w-5" />
                      : <><span className="text-[10px] font-medium opacity-70">DAY</span><span>{d.day}</span></>
                    }
                  </div>

                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <p className={`font-semibold text-sm ${allDone ? "text-emerald-700 line-through" : "text-gray-900"}`}>
                        {d.topic}
                      </p>
                      <div className="flex items-center gap-2 flex-shrink-0">
                        <span className="text-xs text-gray-400 flex items-center gap-1">
                          <Clock className="h-3 w-3" />{d.duration_hours}h
                        </span>
                        <span className="text-xs font-semibold text-gray-500">
                          {dayDone}/{dayTotal}
                        </span>
                      </div>
                    </div>
                    {/* Task progress mini bar */}
                    {dayTotal > 0 && (
                      <div className="w-full bg-gray-100 rounded-full h-1 mt-1.5">
                        <div
                          className="h-1 rounded-full bg-blue-500 transition-all"
                          style={{ width: `${(dayDone / dayTotal) * 100}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>

                {/* Tasks */}
                <div className="px-4 pb-4 space-y-2">
                  {d.tasks?.map((task: string, i: number) => {
                    const key  = `daily-${d.day}-${i}`;
                    const done = !!checked[key];
                    return (
                      <button key={i} onClick={() => toggle(key)}
                        className={`w-full flex items-start gap-3 p-3 rounded-xl border text-left transition-all group ${
                          done
                            ? "bg-emerald-50 border-emerald-200"
                            : "bg-gray-50 border-gray-100 hover:border-blue-200 hover:bg-blue-50/30"
                        }`}>
                        {done
                          ? <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                          : <Circle className="h-4 w-4 text-gray-300 flex-shrink-0 mt-0.5 group-hover:text-blue-400" />
                        }
                        <span className={`text-sm leading-relaxed ${done ? "line-through text-gray-400" : "text-gray-700"}`}>
                          {task}
                        </span>
                      </button>
                    );
                  })}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── WEEKLY GOALS (todo list, collapsible) ──────────────────────── */}
      {tab === "weekly" && (
        <div className="space-y-3">
          <p className="text-sm text-gray-500 px-1">
            Click a week to expand. Check off goals as you achieve them.
          </p>
          {roadmap.weekly_plan?.map((w: any) => {
            const wKeys   = (w.goals ?? []).map((_: any, i: number) => `weekly-${w.week}-${i}`);
            const wDone   = wKeys.filter((k: string) => checked[k]).length;
            const wTotal  = wKeys.length;
            const allDone = wDone === wTotal && wTotal > 0;
            const open    = !!expandedWeeks[w.week];

            return (
              <div key={w.week}
                className={`bg-white rounded-2xl border shadow-sm transition-all ${
                  allDone ? "border-emerald-200" : "border-gray-100"
                }`}>
                {/* Week header — click to collapse */}
                <button
                  className="w-full flex items-center gap-4 p-4 text-left"
                  onClick={() => setExpandedWeeks((p) => ({ ...p, [w.week]: !p[w.week] }))}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-sm ${
                    allDone ? "bg-emerald-500 text-white" : "bg-blue-600 text-white"
                  }`}>
                    {allDone ? <CheckCircle2 className="h-5 w-5" /> : `W${w.week}`}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <p className="font-semibold text-gray-900 text-sm">Week {w.week} — {w.focus}</p>
                      {allDone && <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-semibold">Done ✓</span>}
                    </div>
                    <div className="flex items-center gap-3 mt-1">
                      <div className="flex-1 bg-gray-100 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-blue-500 transition-all"
                          style={{ width: wTotal > 0 ? `${(wDone / wTotal) * 100}%` : "0%" }} />
                      </div>
                      <span className="text-xs text-gray-400 flex-shrink-0">{wDone}/{wTotal}</span>
                    </div>
                  </div>
                  <span className="text-xs bg-blue-50 text-blue-600 px-2.5 py-1 rounded-lg font-medium flex-shrink-0 hidden sm:block">
                    {w.deliverable}
                  </span>
                  {open ? <ChevronUp className="h-4 w-4 text-gray-400 flex-shrink-0" /> : <ChevronDown className="h-4 w-4 text-gray-400 flex-shrink-0" />}
                </button>

                {open && (
                  <div className="px-4 pb-4 space-y-2 border-t border-gray-50 pt-3">
                    {w.goals?.map((goal: string, i: number) => {
                      const key  = `weekly-${w.week}-${i}`;
                      const done = !!checked[key];
                      return (
                        <button key={i} onClick={() => toggle(key)}
                          className={`w-full flex items-start gap-3 p-3 rounded-xl border text-left transition-all group ${
                            done
                              ? "bg-emerald-50 border-emerald-200"
                              : "bg-gray-50 border-gray-100 hover:border-blue-200 hover:bg-blue-50/30"
                          }`}>
                          {done
                            ? <CheckCircle2 className="h-4 w-4 text-emerald-500 flex-shrink-0 mt-0.5" />
                            : <Circle className="h-4 w-4 text-gray-300 flex-shrink-0 mt-0.5 group-hover:text-blue-400" />
                          }
                          <span className={`text-sm ${done ? "line-through text-gray-400" : "text-gray-700"}`}>
                            {goal}
                          </span>
                        </button>
                      );
                    })}
                    {/* Skills covered */}
                    {w.skills_covered?.length > 0 && (
                      <div className="flex flex-wrap gap-1.5 pt-2">
                        {w.skills_covered.map((s: string, i: number) => (
                          <span key={i} className="text-xs bg-blue-50 text-blue-600 border border-blue-100 px-2.5 py-0.5 rounded-full">{s}</span>
                        ))}
                      </div>
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* ── MILESTONES ─────────────────────────────────────────────────── */}
      {tab === "milestones" && (
        <div className="space-y-4">
          {roadmap.monthly_milestones?.map((m: any, idx: number) => (
            <div key={m.month} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-start gap-4">
                <div className="w-10 h-10 bg-emerald-600 text-white rounded-xl flex items-center justify-center font-bold flex-shrink-0">
                  M{m.month}
                </div>
                <div className="flex-1">
                  <p className="font-bold text-gray-900">{m.milestone}</p>
                  <p className="text-sm text-gray-500 mt-1">
                    <span className="font-medium text-gray-700">Assessment: </span>{m.assessment}
                  </p>
                  {m.skills_mastered?.length > 0 && (
                    <div className="flex flex-wrap gap-1.5 mt-3">
                      {m.skills_mastered.map((s: string, i: number) => (
                        <span key={i} className="text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-0.5 rounded-full font-medium">
                          ✓ {s}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── RESOURCES ──────────────────────────────────────────────────── */}
      {tab === "resources" && (
        <div className="space-y-3">
          {roadmap.resources?.map((r: any, i: number) => (
            <div key={i} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 flex items-start justify-between gap-4 hover:border-blue-200 transition-all">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                  <span className={`text-xs px-2.5 py-0.5 rounded-full font-semibold ${typeColor[r.type] ?? typeColor.Article}`}>
                    {r.type}
                  </span>
                  {r.skill && (
                    <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded-full">{r.skill}</span>
                  )}
                  {r.duration && (
                    <span className="text-xs text-gray-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />{r.duration}
                    </span>
                  )}
                </div>
                <p className="text-sm font-semibold text-gray-800">{r.title}</p>
                <p className="text-xs text-gray-400 truncate mt-0.5">{r.url}</p>
              </div>
              <a href={r.url} target="_blank" rel="noopener noreferrer"
                className="flex-shrink-0 flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white text-xs font-semibold px-3 py-2 rounded-xl transition-all">
                Open <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          ))}
        </div>
      )}

      {/* ── MOCK INTERVIEWS ────────────────────────────────────────────── */}
      {tab === "mock" && (
        <div className="space-y-3">
          {roadmap.mock_interview_schedule?.map((m: any, i: number) => (
            <div key={i} className="bg-white rounded-2xl border border-purple-200 shadow-sm p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 bg-purple-600 text-white rounded-xl flex items-center justify-center flex-shrink-0">
                    <Mic className="h-4 w-4" />
                  </div>
                  <div>
                    <p className="font-bold text-gray-900">Week {m.week}: {m.type}</p>
                    <p className="text-xs text-gray-500 mt-0.5">{m.platform} · {m.duration_minutes} min</p>
                  </div>
                </div>
                <span className="text-xs bg-purple-100 text-purple-700 px-2.5 py-1 rounded-full font-semibold flex-shrink-0">
                  Week {m.week}
                </span>
              </div>
              <div className="flex flex-wrap gap-1.5 mt-3">
                {m.topics?.map((t: string, j: number) => (
                  <span key={j} className="text-xs bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-1 rounded-full">{t}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
