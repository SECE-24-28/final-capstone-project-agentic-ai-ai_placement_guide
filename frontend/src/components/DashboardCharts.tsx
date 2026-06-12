"use client";
import {
  RadialBarChart, RadialBar,
  PieChart, Pie, Cell, Tooltip,
} from "recharts";

export function ReadinessRadialChart({ value, color }: { value: number; color: string }) {
  return (
    <RadialBarChart width={160} height={160} cx={80} cy={80}
      innerRadius={50} outerRadius={72}
      data={[{ value, fill: color }]} startAngle={90} endAngle={-270}>
      <RadialBar dataKey="value" maxValue={100} cornerRadius={8}
        background={{ fill: "rgba(255,255,255,0.1)" }} />
    </RadialBarChart>
  );
}

export function SkillGapPieChart({ matched, missing }: { matched: number; missing: number }) {
  return (
    <PieChart width={96} height={96}>
      <Pie
        data={[{ name: "Matched", value: matched }, { name: "Missing", value: missing }]}
        cx={48} cy={48} innerRadius={28} outerRadius={44}
        dataKey="value" startAngle={90} endAngle={-270}>
        <Cell fill="#10b981" />
        <Cell fill="#fca5a5" />
      </Pie>
      <Tooltip formatter={(v: any, n: any) => [v, n]}
        contentStyle={{ fontSize: "11px", borderRadius: "8px" }} />
    </PieChart>
  );
}
