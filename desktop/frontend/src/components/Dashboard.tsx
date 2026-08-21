import React, { useEffect, useRef } from 'react';
import ReactECharts from 'echarts-for-react';

interface Props {
  periods: string[];
  ratios: Record<string, string | number | null>[];
  labels: Record<string, string>;
}

const RATIO_CATEGORIES = {
  'Profitability': ['gross_margin', 'operating_margin', 'net_margin', 'return_on_assets', 'return_on_equity'],
  'Liquidity': ['current_ratio', 'quick_ratio', 'cash_ratio'],
  'Leverage': ['debt_to_equity', 'debt_to_assets', 'interest_coverage'],
  'Efficiency': ['asset_turnover', 'inventory_turnover', 'receivables_turnover'],
};

const COLORS = ['#6c5ce7', '#00d2a0', '#fd79a8', '#fdcb6e', '#0984e3'];

function Dashboard({ periods, ratios, labels }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  const profitabilityOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['Gross Margin', 'Operating Margin', 'Net Margin'], textStyle: { color: '#8b8b9e' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category' as const, data: periods, axisLine: { lineStyle: { color: '#333' } }, axisLabel: { color: '#8b8b9e' } },
    yAxis: { type: 'value' as const, axisLabel: { color: '#8b8b9e', formatter: '{value}%' }, splitLine: { lineStyle: { color: '#222' } } },
    series: [
      { name: 'Gross Margin', type: 'line', data: ratios.map(r => r.gross_margin !== null ? +(r.gross_margin as number * 100).toFixed(2) : null), smooth: true, itemStyle: { color: COLORS[0] } },
      { name: 'Operating Margin', type: 'line', data: ratios.map(r => r.operating_margin !== null ? +(r.operating_margin as number * 100).toFixed(2) : null), smooth: true, itemStyle: { color: COLORS[1] } },
      { name: 'Net Margin', type: 'line', data: ratios.map(r => r.net_margin !== null ? +(r.net_margin as number * 100).toFixed(2) : null), smooth: true, itemStyle: { color: COLORS[2] } },
    ],
  };

  const liquidityOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'axis' as const },
    legend: { data: ['Current Ratio', 'Quick Ratio', 'Cash Ratio'], textStyle: { color: '#8b8b9e' } },
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
    xAxis: { type: 'category' as const, data: periods, axisLine: { lineStyle: { color: '#333' } }, axisLabel: { color: '#8b8b9e' } },
    yAxis: { type: 'value' as const, axisLabel: { color: '#8b8b9e' }, splitLine: { lineStyle: { color: '#222' } } },
    series: [
      { name: 'Current Ratio', type: 'line', data: ratios.map(r => r.current_ratio as number), smooth: true, itemStyle: { color: COLORS[0] } },
      { name: 'Quick Ratio', type: 'line', data: ratios.map(r => r.quick_ratio as number), smooth: true, itemStyle: { color: COLORS[1] } },
      { name: 'Cash Ratio', type: 'line', data: ratios.map(r => r.cash_ratio as number), smooth: true, itemStyle: { color: COLORS[3] } },
    ],
  };

  return (
    <div className="dashboard" ref={containerRef}>
      <div className="chart-card">
        <h3>Profitability Margins</h3>
        <ReactECharts option={profitabilityOption} style={{ height: 280 }} />
      </div>
      <div className="chart-card">
        <h3>Liquidity Ratios</h3>
        <ReactECharts option={liquidityOption} style={{ height: 280 }} />
      </div>
    </div>
  );
}

export default Dashboard;
