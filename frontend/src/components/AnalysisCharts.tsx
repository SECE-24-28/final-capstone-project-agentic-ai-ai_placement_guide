"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";

export function ATSDonutChart({ score, color }: { score: number; color: string }) {
  return (
    <ResponsiveContainer width="100%" height="100%">
      <PieChart>
        <Pie data={[{ value: score }, { value: 100 - score }]} cx="50%" cy="50%"
          innerRadius={38} outerRadius={52} startAngle={90} endAngle={-270} dataKey="value">
          <Cell fill={color} />
          <Cell fill="#f3f4f6" />
        </Pie>
      </PieChart>
    </ResponsiveContainer>
  );
}

export function SkillsPieChart({ data, colors }: { data: { name: string; value: any }[]; colors: string[] }) {
  return (
    <ResponsiveContainer width="100%" height={140}>
      <PieChart>
        <Pie data={data} cx="50%" cy="50%" outerRadius={55} dataKey="value"
          label={({ name, value }) => `${name} (${value})`} labelLine={false} fontSize={10}>
          {data.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}
        </Pie>
        <Tooltip contentStyle={{ borderRadius: "12px", fontSize: "12px" }} />
      </PieChart>
    </ResponsiveContainer>
  );
}
