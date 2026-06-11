import {
  Area,
  AreaChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  CartesianGrid,
  Legend,
} from "recharts";

export interface ChartPoint {
  t_hours: number;
  temp_c?: number;
  humidity_pct?: number;
  co2_ppm?: number;
  ethylene_ppm?: number;
  methane_ppm?: number;
  rsl_days?: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="glass p-3 rounded-lg border border-white/10 shadow-2xl">
        <p className="text-bss-muted text-xs font-mono mb-2">{`Time: ${Number(label).toFixed(1)}h`}</p>
        {payload.map((entry: any, index: number) => (
          <div key={index} className="flex items-center justify-between gap-4 text-xs font-medium mb-1">
            <span style={{ color: entry.color }} className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              {entry.name}
            </span>
            <span className="text-white font-mono">{Number(entry.value).toFixed(2)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function SensorChart({ data }: { data: ChartPoint[] }) {
  return (
    <div className="h-[350px] w-full">
      <ResponsiveContainer>
        <AreaChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorCo2" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#3B82F6" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorEth" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EAB308" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#EAB308" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorTemp" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#EF4444" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#EF4444" stopOpacity={0}/>
            </linearGradient>
            <linearGradient id="colorRsl" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#22C55E" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#22C55E" stopOpacity={0}/>
            </linearGradient>
          </defs>
          <CartesianGrid stroke="#1F2937" strokeDasharray="3 3" vertical={false} />
          <XAxis
            dataKey="t_hours"
            stroke="#9CA3AF"
            tick={{ fill: '#9CA3AF', fontSize: 10, fontFamily: 'monospace' }}
            tickLine={false}
            axisLine={{ stroke: '#1F2937' }}
            minTickGap={30}
          />
          <YAxis 
            yAxisId="left" 
            stroke="#9CA3AF" 
            tick={{ fill: '#9CA3AF', fontSize: 10, fontFamily: 'monospace' }} 
            tickLine={false}
            axisLine={false}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right" 
            stroke="#9CA3AF" 
            tick={{ fill: '#9CA3AF', fontSize: 10, fontFamily: 'monospace' }} 
            tickLine={false}
            axisLine={false}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ stroke: 'rgba(255,255,255,0.1)', strokeWidth: 2, strokeDasharray: '5 5' }} />
          <Legend 
            wrapperStyle={{ paddingTop: "20px" }}
            iconType="circle"
            formatter={(value) => <span className="text-bss-muted text-xs font-medium ml-1">{value}</span>}
          />
          <Area yAxisId="left" type="monotone" dataKey="co2_ppm" stroke="#3B82F6" strokeWidth={2} fillOpacity={1} fill="url(#colorCo2)" dot={false} name="CO2 (ppm)" activeDot={{ r: 4, strokeWidth: 0 }} />
          <Area yAxisId="left" type="monotone" dataKey="ethylene_ppm" stroke="#EAB308" strokeWidth={2} fillOpacity={1} fill="url(#colorEth)" dot={false} name="Ethylene (ppm)" activeDot={{ r: 4, strokeWidth: 0 }} />
          <Area yAxisId="right" type="monotone" dataKey="temp_c" stroke="#EF4444" strokeWidth={2} fillOpacity={1} fill="url(#colorTemp)" dot={false} name="Temp (°C)" activeDot={{ r: 4, strokeWidth: 0 }} />
          <Area yAxisId="right" type="monotone" dataKey="rsl_days" stroke="#22C55E" strokeWidth={2} fillOpacity={1} fill="url(#colorRsl)" dot={false} name="RSL (days)" activeDot={{ r: 4, strokeWidth: 0 }} />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
