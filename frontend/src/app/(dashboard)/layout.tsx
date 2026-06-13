"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { Brain, LayoutDashboard, Upload, Target, Map, Briefcase, User, LogOut, ChevronRight, History } from "lucide-react";
import { useAuthStore } from "@/lib/store";

const navItems = [
  { href: "/dashboard", label: "Dashboard",      icon: LayoutDashboard, color: "text-blue-600 bg-blue-50" },
  { href: "/upload",    label: "Resume Upload",   icon: Upload,          color: "text-violet-600 bg-violet-50" },
  { href: "/analysis", label: "Analysis",         icon: Target,          color: "text-emerald-600 bg-emerald-50" },
  { href: "/history",  label: "Resume History",   icon: History,         color: "text-cyan-600 bg-cyan-50" },
  { href: "/roadmap",  label: "Roadmap",           icon: Map,             color: "text-amber-600 bg-amber-50" },
  { href: "/jobs",     label: "Job Matches",       icon: Briefcase,       color: "text-rose-600 bg-rose-50" },
  { href: "/profile",  label: "Profile",           icon: User,            color: "text-gray-600 bg-gray-100" },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { logout, isAuthenticated } = useAuthStore();

  const [mounted, setMounted] = useState(false);
  useEffect(() => {
    useAuthStore.persist.rehydrate();
    setMounted(true);
  }, []);

  if (!mounted) return <div className="min-h-screen bg-gray-50" />;
  if (!isAuthenticated) { router.replace("/"); return <div className="min-h-screen bg-gray-50" />; }

  return (
    <div className="min-h-screen flex bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-100 flex flex-col fixed h-full shadow-sm z-10">
        {/* Logo — click navigates to dashboard */}
        <div className="p-5 border-b border-gray-100">
          <Link href="/dashboard" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
            <div className="w-9 h-9 bg-gradient-to-br from-blue-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-md shadow-blue-200">
              <Brain className="h-5 w-5 text-white" />
            </div>
            <div>
              <p className="font-bold text-gray-900 text-sm leading-tight">AI Placement</p>
              <p className="text-xs text-gray-400">Preparation Agent</p>
            </div>
          </Link>
        </div>

        {/* Nav */}
        <nav className="flex-1 p-3 space-y-0.5 overflow-y-auto">
          <p className="text-[10px] font-semibold text-gray-400 uppercase tracking-wider px-3 pt-3 pb-2">Navigation</p>
          {navItems.map(({ href, label, icon: Icon, color }) => {
            const active = pathname === href;
            return (
              <Link key={href} href={href}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all group ${
                  active ? "bg-blue-600 text-white shadow-md shadow-blue-200" : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
                }`}>
                <div className={`w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0 transition-all ${active ? "bg-white/20" : color}`}>
                  <Icon className={`h-3.5 w-3.5 ${active ? "text-white" : ""}`} />
                </div>
                <span className="flex-1">{label}</span>
                {active && <ChevronRight className="h-3.5 w-3.5 opacity-60" />}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-3 border-t border-gray-100">
          <button onClick={() => { logout(); router.push("/"); }}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium text-red-500 hover:bg-red-50 transition-all w-full group">
            <div className="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center group-hover:bg-red-100">
              <LogOut className="h-3.5 w-3.5 text-red-500" />
            </div>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main */}
      <main className="flex-1 ml-64 min-h-screen">
        <div className="max-w-6xl mx-auto p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
