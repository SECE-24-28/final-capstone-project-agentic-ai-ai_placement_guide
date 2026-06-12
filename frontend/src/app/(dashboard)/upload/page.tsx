"use client";
import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Upload, FileText, CheckCircle, Loader2, X, Sparkles, Brain, Target, Map, Briefcase, AlertCircle, XCircle, Zap, ArrowRight } from "lucide-react";
import { pipelineApi } from "@/lib/api";
import { useAnalysisStore } from "@/lib/store";

const ROLES = ["Software Engineer", "Full Stack Developer", "Backend Developer", "Frontend Developer", "Data Scientist", "ML Engineer", "AI Engineer", "DevOps Engineer", "Cloud Engineer", "Data Analyst", "Cyber Security Analyst", "Mobile Developer"];
const LEVELS = ["beginner", "intermediate", "advanced"];

const agents = [
  { icon: FileText, label: "Resume Analyzer", desc: "Parsing & ATS Scoring", color: "blue" },
  { icon: Target, label: "Skill Gap Analyzer", desc: "Role requirement matching", color: "amber" },
  { icon: Map, label: "Roadmap Generator", desc: "Creating learning plan", color: "emerald" },
  { icon: Briefcase, label: "Job Matcher", desc: "Finding best companies", color: "violet" },
];

const colorMap: any = {
  blue: { active: "bg-blue-600 text-white", done: "bg-blue-100 text-blue-600", pending: "bg-gray-100 text-gray-400", ring: "ring-blue-600", bar: "bg-blue-600" },
  amber: { active: "bg-amber-500 text-white", done: "bg-amber-100 text-amber-600", pending: "bg-gray-100 text-gray-400", ring: "ring-amber-500", bar: "bg-amber-500" },
  emerald: { active: "bg-emerald-500 text-white", done: "bg-emerald-100 text-emerald-600", pending: "bg-gray-100 text-gray-400", ring: "ring-emerald-500", bar: "bg-emerald-500" },
  violet: { active: "bg-violet-600 text-white", done: "bg-violet-100 text-violet-600", pending: "bg-gray-100 text-gray-400", ring: "ring-violet-600", bar: "bg-violet-600" },
};

export default function UploadPage() {
  const router = useRouter();
  const { setFullAnalysis, setLoading } = useAnalysisStore();
  const [file, setFile] = useState<File | null>(null);
  const [targetRole, setTargetRole] = useState("Software Engineer");
  const [level, setLevel] = useState("beginner");
  const [hours, setHours] = useState(2);
  const [statuses, setStatuses] = useState<("pending" | "running" | "done")[]>(["pending", "pending", "pending", "pending"]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<any>(null);

  const onDrop = useCallback((files: File[]) => { if (files[0]) setFile(files[0]); }, []);
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "application/pdf": [".pdf"], "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [".docx"] },
    maxFiles: 1,
    disabled: isAnalyzing,
  });

  const run = async () => {
    if (!file) return toast.error("Please upload a resume first");
    setIsAnalyzing(true);
    setLoading(true);
    const s: ("pending" | "running" | "done")[] = ["pending", "pending", "pending", "pending"];
    const upd = (i: number, v: "running" | "done") => { s[i] = v; setStatuses([...s]); };

    try {
      upd(0, "running"); await new Promise(r => setTimeout(r, 600));
      upd(0, "done"); upd(1, "running"); await new Promise(r => setTimeout(r, 600));
      upd(1, "done"); upd(2, "running"); await new Promise(r => setTimeout(r, 600));
      upd(2, "done"); upd(3, "running");

      const res = await pipelineApi.fullAnalysis(file, targetRole, level, hours);
      upd(3, "done");
      setFullAnalysis(res.data);
      setResult(res.data);
      toast.success("Analysis complete!");
    } catch (err: any) {
      const detail = err.response?.data?.detail || "Analysis failed.";
      const status = err.response?.status;
      if (status === 429) {
        toast.error(detail, { duration: 8000 });
      } else {
        toast.error(detail);
      }
      setStatuses(["pending", "pending", "pending", "pending"]);
    } finally {
      setIsAnalyzing(false);
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-2xl mx-auto">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Upload Resume</h1>
        <p className="text-gray-500 mt-1">Run all 4 AI agents with a single click</p>
      </div>

      {/* Drop Zone */}
      <div {...getRootProps()}
        className={`relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all ${
          isAnalyzing ? "opacity-50 cursor-not-allowed" :
          isDragActive ? "border-blue-500 bg-blue-50 scale-[1.01]" :
          file ? "border-emerald-400 bg-emerald-50" :
          "border-gray-200 hover:border-blue-400 hover:bg-blue-50/30 bg-white"
        }`}>
        <input {...getInputProps()} />
        {file ? (
          <div className="flex flex-col items-center gap-3">
            <div className="w-16 h-16 bg-emerald-100 rounded-2xl flex items-center justify-center">
              <FileText className="h-8 w-8 text-emerald-600" />
            </div>
            <div>
              <p className="font-semibold text-emerald-700 text-lg">{file.name}</p>
              <p className="text-emerald-600 text-sm mt-1">{(file.size / 1024).toFixed(1)} KB • Click to replace</p>
            </div>
            {!isAnalyzing && (
              <button onClick={(e) => { e.stopPropagation(); setFile(null); }}
                className="absolute top-4 right-4 w-8 h-8 bg-gray-100 hover:bg-red-100 rounded-full flex items-center justify-center transition-colors">
                <X className="h-4 w-4 text-gray-500 hover:text-red-500" />
              </button>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center gap-3">
            <div className={`w-16 h-16 rounded-2xl flex items-center justify-center transition-colors ${isDragActive ? "bg-blue-100" : "bg-gray-100"}`}>
              <Upload className={`h-8 w-8 ${isDragActive ? "text-blue-600" : "text-gray-400"}`} />
            </div>
            <div>
              <p className="font-semibold text-gray-700 text-lg">{isDragActive ? "Drop it here!" : "Drag & drop your resume"}</p>
              <p className="text-gray-400 text-sm mt-1">or click to browse • PDF, DOCX up to 10MB</p>
            </div>
          </div>
        )}
      </div>

      {/* Settings */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 space-y-5">
        <h3 className="font-bold text-gray-900 flex items-center gap-2">
          <Sparkles className="h-4 w-4 text-blue-600" /> Analysis Settings
        </h3>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Target Role</label>
          <select value={targetRole} onChange={e => setTargetRole(e.target.value)}
            className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all">
            {ROLES.map(r => <option key={r}>{r}</option>)}
          </select>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Skill Level</label>
            <select value={level} onChange={e => setLevel(e.target.value)}
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all">
              {LEVELS.map(l => <option key={l} value={l}>{l.charAt(0).toUpperCase() + l.slice(1)}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Hours/Day Available</label>
            <input type="number" min={0.5} max={12} step={0.5} value={hours} onChange={e => setHours(Number(e.target.value))}
              className="w-full border border-gray-200 rounded-xl px-4 py-3 text-sm bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all" />
          </div>
        </div>
      </div>

      {/* Agent Progress */}
      {isAnalyzing && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
          <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Brain className="h-4 w-4 text-blue-600 animate-pulse" /> AI Agents Running...
          </h3>
          <div className="space-y-3">
            {agents.map((agent, i) => {
              const status = statuses[i];
              const c = colorMap[agent.color];
              return (
                <div key={i} className={`flex items-center gap-4 p-4 rounded-xl border transition-all ${
                  status === "running" ? `ring-2 ${c.ring} ring-offset-1 bg-white` :
                  status === "done" ? "bg-gray-50 border-gray-100" : "bg-gray-50 border-gray-100 opacity-50"
                }`}>
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 transition-all ${
                    status === "running" ? c.active : status === "done" ? c.done : c.pending
                  }`}>
                    {status === "done" ? <CheckCircle className="h-5 w-5" /> :
                     status === "running" ? <Loader2 className="h-5 w-5 animate-spin" /> :
                     <agent.icon className="h-5 w-5" />}
                  </div>
                  <div className="flex-1">
                    <p className={`text-sm font-semibold ${status === "pending" ? "text-gray-400" : "text-gray-900"}`}>
                      Agent {i + 1}: {agent.label}
                    </p>
                    <p className="text-xs text-gray-500">{agent.desc}</p>
                  </div>
                  {status === "done" && <span className="text-xs text-emerald-600 font-semibold bg-emerald-50 px-2.5 py-1 rounded-full">Done ✓</span>}
                  {status === "running" && <span className="text-xs text-blue-600 font-semibold bg-blue-50 px-2.5 py-1 rounded-full">Running...</span>}
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Submit */}
      <button onClick={run} disabled={!file || isAnalyzing}
        className="w-full flex items-center justify-center gap-2.5 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-bold py-4 rounded-2xl transition-all shadow-xl shadow-blue-200 hover:shadow-blue-300 text-base">
        {isAnalyzing ? (
          <><Loader2 className="h-5 w-5 animate-spin" /> Analyzing with AI Agents...</>
        ) : (
          <><Sparkles className="h-5 w-5" /> Run Full AI Analysis</>
        )}
      </button>

      {/* ── Inline Smart Feedback after analysis ── */}
      {result?.resume_analysis?.smart_feedback && (() => {
        const sf = result.resume_analysis.smart_feedback;
        const score = result.resume_analysis.resume_score;
        return (
          <div className="space-y-4">
            {/* Score + verdict */}
            <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5 flex items-center gap-5">
              <div className="flex-shrink-0 text-center">
                <p className="text-5xl font-black" style={{ color: score >= 70 ? "#10b981" : score >= 50 ? "#f59e0b" : "#ef4444" }}>{score}</p>
                <p className="text-xs text-gray-400 mt-0.5">ATS Score</p>
              </div>
              <div>
                <p className="font-bold text-gray-900 text-lg">{result.resume_analysis.candidate_name}</p>
                {sf.overall_verdict && <p className="text-sm text-gray-500 mt-1">{sf.overall_verdict}</p>}
              </div>
            </div>

            {/* Strengths */}
            {sf.strengths?.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <p className="font-bold text-emerald-700 mb-3 flex items-center gap-2"><CheckCircle className="h-4 w-4" /> What's Working Well</p>
                <div className="space-y-2">
                  {sf.strengths.map((s: any, i: number) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-emerald-50 border border-emerald-100 rounded-xl">
                      <CheckCircle className="h-4 w-4 text-emerald-500 mt-0.5 flex-shrink-0" />
                      <div>
                        <span className="text-xs font-bold text-emerald-700 uppercase">{s.section}</span>
                        {s.item && <span className="text-xs text-emerald-600"> · {s.item}</span>}
                        <p className="text-sm text-gray-700 mt-0.5">{s.reason}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Improvements */}
            {sf.improvements?.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <p className="font-bold text-red-600 mb-3 flex items-center gap-2"><XCircle className="h-4 w-4" /> What Needs Fixing</p>
                <div className="space-y-3">
                  {sf.improvements.map((imp: any, i: number) => (
                    <div key={i} className={`p-4 rounded-xl border ${
                      imp.priority === "high" ? "bg-red-50 border-red-200" :
                      imp.priority === "medium" ? "bg-amber-50 border-amber-200" : "bg-gray-50 border-gray-200"
                    }`}>
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                          imp.priority === "high" ? "bg-red-100 text-red-700" :
                          imp.priority === "medium" ? "bg-amber-100 text-amber-700" : "bg-gray-200 text-gray-600"
                        }`}>{imp.priority}</span>
                        <span className="text-xs font-semibold text-gray-500 uppercase">{imp.section}</span>
                        {imp.item && <span className="text-xs text-gray-400">· {imp.item}</span>}
                      </div>
                      <p className="text-sm font-medium text-gray-800">{imp.issue}</p>
                      {imp.fix && <p className="text-xs text-gray-600 mt-1.5 bg-white/70 rounded-lg px-3 py-2 border border-gray-100">💡 {imp.fix}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Missing */}
            {sf.missing?.length > 0 && (
              <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-5">
                <p className="font-bold text-amber-700 mb-3 flex items-center gap-2"><AlertCircle className="h-4 w-4" /> What's Missing</p>
                <div className="space-y-2">
                  {sf.missing.map((m: any, i: number) => (
                    <div key={i} className="p-3 bg-amber-50 border border-amber-100 rounded-xl">
                      <p className="text-sm font-semibold text-gray-800">{m.what}</p>
                      <p className="text-xs text-gray-500 mt-0.5">{m.why}</p>
                      {m.example && <p className="text-xs text-amber-700 mt-1 font-medium">Example: {m.example}</p>}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Go to full dashboard */}
            <button onClick={() => router.push("/dashboard")}
              className="w-full flex items-center justify-center gap-2 bg-gray-900 hover:bg-gray-800 text-white font-bold py-4 rounded-2xl transition-all">
              View Full Dashboard <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        );
      })()}
    </div>
  );
}
