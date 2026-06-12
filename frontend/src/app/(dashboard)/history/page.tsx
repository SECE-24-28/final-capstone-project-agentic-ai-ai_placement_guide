"use client";
import { useEffect, useState } from "react";
import { resumeApi } from "@/lib/api";
import { History, GitCompare, CheckCircle, XCircle, Minus, TrendingUp, TrendingDown, FileText } from "lucide-react";

export default function HistoryPage() {
  const [history, setHistory]   = useState<any>(null);
  const [compare, setCompare]   = useState<any>(null);
  const [loading, setLoading]   = useState(true);
  const [cmpLoading, setCmpLoading] = useState(false);
  const [error, setError]       = useState("");

  useEffect(() => {
    resumeApi.getHistory()
      .then((r) => setHistory(r.data))
      .catch((e) => setError(e.response?.data?.detail || "No resume history found"))
      .finally(() => setLoading(false));
  }, []);

  const runCompare = async () => {
    setCmpLoading(true);
    try {
      const r = await resumeApi.compare();
      setCompare(r.data);
    } catch (e: any) {
      setError(e.response?.data?.detail || "Compare failed");
    } finally {
      setCmpLoading(false);
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center py-24">
      <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin" />
    </div>
  );

  if (error && !history) return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <FileText className="h-12 w-12 text-gray-300 mb-4" />
      <p className="text-gray-500">{error}</p>
      <p className="text-sm text-gray-400 mt-1">Upload at least one resume to see history</p>
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Resume History</h1>
          <p className="text-gray-500 mt-1">All your uploaded resume versions</p>
        </div>
        {history?.total >= 2 && (
          <button onClick={runCompare} disabled={cmpLoading}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-700 text-white px-5 py-2.5 rounded-xl font-semibold text-sm shadow-lg shadow-blue-200 transition-all disabled:opacity-60">
            <GitCompare className="h-4 w-4" />
            {cmpLoading ? "Comparing..." : "Compare Last 2 Versions"}
          </button>
        )}
      </div>

      {/* History list */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm overflow-hidden">
        <div className="p-5 border-b border-gray-100 flex items-center gap-2">
          <History className="h-4 w-4 text-blue-600" />
          <span className="font-semibold text-gray-900">Upload History</span>
          <span className="ml-auto text-sm text-gray-400">{history?.total} version{history?.total !== 1 ? "s" : ""}</span>
        </div>
        <div className="divide-y divide-gray-50">
          {history?.history?.map((r: any, i: number) => (
            <div key={r.resume_id} className="flex items-center gap-4 p-4 hover:bg-gray-50 transition-colors">
              <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 font-bold text-sm ${
                r.is_active ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "bg-gray-100 text-gray-500"
              }`}>
                {r.is_active ? "✓" : `v${history.total - i}`}
              </div>
              <div className="flex-1 min-w-0">
                <p className="font-semibold text-gray-900 truncate">{r.file_name}</p>
                <p className="text-xs text-gray-400 mt-0.5">
                  {r.uploaded_at ? new Date(r.uploaded_at).toLocaleString("en-IN", { dateStyle: "medium", timeStyle: "short" }) : "—"}
                  {" · "}{r.skills_count} skills
                </p>
              </div>
              <div className="text-right flex-shrink-0">
                <p className="text-lg font-black" style={{ color: r.resume_score >= 70 ? "#10b981" : r.resume_score >= 50 ? "#f59e0b" : "#ef4444" }}>
                  {r.resume_score}
                </p>
                <p className="text-xs text-gray-400">ATS Score</p>
              </div>
              {r.is_active && (
                <span className="px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-semibold rounded-full">Active</span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Compare result */}
      {compare && (
        <div className="space-y-4">
          {/* ATS Score diff */}
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <h2 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              <GitCompare className="h-4 w-4 text-blue-600" /> ATS Score Comparison
            </h2>
            <div className="flex items-center gap-6">
              <div className="text-center">
                <p className="text-3xl font-black text-gray-400">{compare.ats_v1}</p>
                <p className="text-xs text-gray-400 mt-1">Previous Version</p>
              </div>
              <div className="flex-1 flex items-center justify-center">
                <div className={`flex items-center gap-2 px-4 py-2 rounded-xl font-bold text-lg ${
                  compare.ats_improvement > 0 ? "bg-emerald-50 text-emerald-600" :
                  compare.ats_improvement < 0 ? "bg-red-50 text-red-600" : "bg-gray-50 text-gray-500"
                }`}>
                  {compare.ats_improvement > 0 ? <TrendingUp className="h-5 w-5" /> : compare.ats_improvement < 0 ? <TrendingDown className="h-5 w-5" /> : <Minus className="h-5 w-5" />}
                  {compare.ats_improvement > 0 ? "+" : ""}{compare.ats_improvement} pts
                </div>
              </div>
              <div className="text-center">
                <p className="text-3xl font-black text-blue-600">{compare.ats_v2}</p>
                <p className="text-xs text-gray-400 mt-1">Latest Version</p>
              </div>
            </div>
            {compare.sections_changed?.length > 0 && (
              <div className="mt-4 flex flex-wrap gap-2">
                <span className="text-xs text-gray-500 font-medium">Sections changed:</span>
                {compare.sections_changed.map((s: string) => (
                  <span key={s} className="px-2 py-0.5 bg-amber-100 text-amber-700 text-xs font-semibold rounded-full">{s}</span>
                ))}
              </div>
            )}
          </div>

          {/* Added / Removed */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h3 className="font-bold text-emerald-700 mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" /> Added ({compare.added?.length})
              </h3>
              {compare.added?.length === 0 ? (
                <p className="text-sm text-gray-400">Nothing added</p>
              ) : (
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {compare.added?.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="px-1.5 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded font-medium">{item.section}</span>
                      <span className="text-gray-700 capitalize">{item.item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
              <h3 className="font-bold text-red-600 mb-3 flex items-center gap-2">
                <XCircle className="h-4 w-4" /> Removed ({compare.removed?.length})
              </h3>
              {compare.removed?.length === 0 ? (
                <p className="text-sm text-gray-400">Nothing removed</p>
              ) : (
                <div className="space-y-1.5 max-h-48 overflow-y-auto">
                  {compare.removed?.map((item: any, i: number) => (
                    <div key={i} className="flex items-center gap-2 text-sm">
                      <span className="px-1.5 py-0.5 bg-red-100 text-red-700 text-xs rounded font-medium">{item.section}</span>
                      <span className="text-gray-700 capitalize">{item.item}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
