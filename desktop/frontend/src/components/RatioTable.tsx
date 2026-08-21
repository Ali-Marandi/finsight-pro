import React, { useState } from 'react';

interface Props {
  periods: string[];
  ratios: Record<string, string | number | null>[];
  labels: Record<string, string>;
}

const RATIO_GROUPS = [
  {
    name: 'Profitability & Returns',
    keys: ['gross_margin', 'operating_margin', 'net_margin', 'return_on_assets', 'return_on_equity'],
    format: (v: number) => `${(v * 100).toFixed(2)}%`,
  },
  {
    name: 'Liquidity',
    keys: ['current_ratio', 'quick_ratio', 'cash_ratio'],
    format: (v: number) => v.toFixed(2),
  },
  {
    name: 'Leverage & Coverage',
    keys: ['debt_to_equity', 'debt_to_assets', 'interest_coverage'],
    format: (v: number) => v.toFixed(2),
  },
  {
    name: 'Efficiency',
    keys: ['asset_turnover', 'inventory_turnover', 'receivables_turnover'],
    format: (v: number) => v.toFixed(2),
  },
];

function RatioTable({ periods, ratios, labels }: Props) {
  const [activeGroup, setActiveGroup] = useState(0);
  const group = RATIO_GROUPS[activeGroup];

  const formatValue = (key: string, value: string | number | null): string => {
    if (value === null || value === undefined) return 'N/A';
    const num = typeof value === 'string' ? parseFloat(value) : value;
    if (isNaN(num)) return 'N/A';
    if (['gross_margin', 'operating_margin', 'net_margin', 'debt_to_assets', 'return_on_assets', 'return_on_equity', 'cash_flow_margin'].includes(key)) {
      return `${(num * 100).toFixed(2)}%`;
    }
    return num.toFixed(2);
  };

  return (
    <div className="ratio-table-container">
      <div className="table-tabs">
        {RATIO_GROUPS.map((g, i) => (
          <button
            key={g.name}
            className={`tab ${i === activeGroup ? 'active' : ''}`}
            onClick={() => setActiveGroup(i)}
          >
            {g.name}
          </button>
        ))}
      </div>
      <div className="table-wrapper">
        <table className="ratio-table">
          <thead>
            <tr>
              <th>Ratio</th>
              {periods.map(p => <th key={p}>{p}</th>)}
            </tr>
          </thead>
          <tbody>
            {group.keys.map(key => (
              <tr key={key}>
                <td className="ratio-name">{labels[key] || key}</td>
                {ratios.map((row, i) => (
                  <td key={i}>{formatValue(key, row[key])}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default RatioTable;