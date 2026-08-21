import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, RadarChart, Radar, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Cell } from 'recharts';
import type { RatioResult } from '../../types';
import { useState } from 'react';

interface RatioChartProps {
  ratios: RatioResult[];
  title?: string;
}

type ChartType = 'bar' | 'radar';

export default function RatioChart({ ratios, title }: RatioChartProps) {
  const [chartType, setChartType] = useState<ChartType>('bar');

  const barData = ratios.map((r) => ({
    name: r.ratioName.replace(/_/g, ' '),
    value: r.unit === '%' ? r.value * 100 : r.value,
    fill: r.status === 'good' ? '#16a34a' : r.status === 'warning' ? '#d97706' : '#dc2626',
  }));

  const radarData = ratios.reduce<Record<string, { subject: string; value: number; fullMark: number }[]>>(
    (acc, r) => {
      const cat = r.category.charAt(0).toUpperCase() + r.category.slice(1);
      if (!acc[cat]) acc[cat] = [];
      acc[cat].push({
        subject: r.ratioName.replace(/_/g, ' '),
        value: r.unit === '%' ? r.value * 100 : r.value,
        fullMark: 100,
      });
      return acc;
    },
    {},
  );

  const radarItems = Object.values(radarData).flat();

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-6">
        <h3 className="font-semibold text-base">{title || 'Analysis Charts'}</h3>
        <div className="flex gap-1 bg-cascade-stone rounded-lg p-1">
          <button
            onClick={() => setChartType('bar')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              chartType === 'bar' ? 'bg-white shadow-sm text-cascade-charcoal' : 'text-cascade-sage'
            }`}
          >
            Bar
          </button>
          <button
            onClick={() => setChartType('radar')}
            className={`px-3 py-1.5 text-xs font-medium rounded-md transition-colors ${
              chartType === 'radar' ? 'bg-white shadow-sm text-cascade-charcoal' : 'text-cascade-sage'
            }`}
          >
            Radar
          </button>
        </div>
      </div>

      <div className="h-72">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === 'bar' ? (
            <BarChart data={barData} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e7e5e4" />
              <XAxis dataKey="name" tick={{ fontSize: 11, fill: '#78716c' }} angle={-25} textAnchor="end" height={60} />
              <YAxis tick={{ fontSize: 11, fill: '#78716c' }} />
              <Tooltip
                contentStyle={{
                  background: '#1a1a19',
                  border: 'none',
                  borderRadius: '8px',
                  color: '#fff',
                  fontSize: '12px',
                }}
              />
              <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                {barData.map((entry, index) => (
                  <Cell key={index} fill={entry.fill} />
                ))}
              </Bar>
            </BarChart>
          ) : (
            <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarItems}>
              <PolarGrid stroke="#e7e5e4" />
              <PolarAngleAxis dataKey="subject" tick={{ fontSize: 10, fill: '#78716c' }} />
              <PolarRadiusAxis tick={{ fontSize: 10, fill: '#78716c' }} />
              <Radar
                name="Ratios"
                dataKey="value"
                stroke="#92761f"
                fill="#92761f"
                fillOpacity={0.2}
              />
            </RadarChart>
          )}
        </ResponsiveContainer>
      </div>
    </div>
  );
}