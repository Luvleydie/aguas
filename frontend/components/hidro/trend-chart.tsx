"use client"

import {
  CartesianGrid,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

export function TrendChart({
  data,
  height = 320,
  simple = false,
  references = [],
}: {
  data: { semana: string; nivel: number }[]
  height?: number
  simple?: boolean
  references?: { y: number; label: string }[]
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={data} margin={{ top: 16, right: 24, left: 0, bottom: 8 }}>
        {!simple && <CartesianGrid strokeDasharray="4 4" stroke="var(--border)" vertical={false} />}
        <XAxis
          dataKey="semana"
          stroke="var(--muted-foreground)"
          tick={{ fontSize: 14, fill: "var(--muted-foreground)" }}
          tickLine={false}
          axisLine={{ stroke: "var(--border)" }}
        />
        <YAxis
          domain={[0, 100]}
          unit="%"
          stroke="var(--muted-foreground)"
          tick={{ fontSize: 14, fill: "var(--muted-foreground)" }}
          tickLine={false}
          axisLine={false}
          width={48}
        />
        <Tooltip
          contentStyle={{
            borderRadius: 12,
            border: "1px solid var(--border)",
            backgroundColor: "var(--card)",
            fontSize: 14,
            color: "var(--foreground)",
          }}
          formatter={(v: number) => [`${v}%`, "Almacenamiento"]}
        />
        {references.map((r) => (
          <ReferenceLine
            key={r.label}
            y={r.y}
            stroke="var(--nivel-naranja)"
            strokeDasharray="6 4"
            label={{ value: r.label, position: "insideTopRight", fill: "var(--nivel-naranja)", fontSize: 12 }}
          />
        ))}
        <Line
          type="monotone"
          dataKey="nivel"
          stroke="var(--accent)"
          strokeWidth={3.5}
          dot={{ r: simple ? 0 : 4, fill: "var(--accent)", strokeWidth: 0 }}
          activeDot={{ r: 6 }}
        />
      </LineChart>
    </ResponsiveContainer>
  )
}
