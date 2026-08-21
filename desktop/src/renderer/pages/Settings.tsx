import { useState } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { useLicense } from '../hooks/useLicense';
import { Crown, Globe, Palette, Save, Key } from 'lucide-react';

export default function Settings() {
  const { preferences, setPreferences } = useAnalysisStore();
  const { license, activate, isPro } = useLicense();
  const [licenseKey, setLicenseKey] = useState('');
  const [activating, setActivating] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = () => {
    // Will connect to API
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleActivate = async () => {
    setActivating(true);
    await activate(licenseKey);
    setActivating(false);
  };

  return (
    <div className="space-y-8 max-w-2xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-cascade-sage text-sm mt-1">Configure your FinSight Pro experience</p>
        </div>
        <button onClick={handleSave} className="btn-primary flex items-center gap-2">
          <Save size={16} /> {saved ? 'Saved!' : 'Save Changes'}
        </button>
      </div>

      {/* License */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-cascade-gold/10 flex items-center justify-center">
            <Crown size={20} className="text-cascade-gold" />
          </div>
          <div>
            <h2 className="font-semibold">License</h2>
            <p className="text-xs text-cascade-sage">Manage your subscription and activation</p>
          </div>
        </div>

        {isPro ? (
          <div className="bg-semantic-success/5 border border-semantic-success/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className={`status-good`}>Active</span>
              <span className="text-sm font-semibold">{license?.tier?.toUpperCase()}</span>
            </div>
            {license?.expiresAt && (
              <p className="text-xs text-cascade-sage">Expires: {license.expiresAt}</p>
            )}
          </div>
        ) : (
          <div className="space-y-3">
            <div className="flex gap-2">
              <input
                type="text"
                value={licenseKey}
                onChange={(e) => setLicenseKey(e.target.value)}
                placeholder="XXXX-XXXX-XXXX-XXXX"
                className="input-field flex-1 font-mono"
              />
              <button
                onClick={handleActivate}
                disabled={activating || !licenseKey}
                className="btn-primary flex items-center gap-2"
              >
                <Key size={16} /> {activating ? 'Activating...' : 'Activate'}
              </button>
            </div>
            <p className="text-xs text-cascade-sage">
              Don't have a key? <a href="https://finsightpro.com" className="text-cascade-gold hover:underline">Get one here</a>
            </p>
          </div>
        )}
      </div>

      {/* Appearance */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-semantic-info/10 flex items-center justify-center">
            <Palette size={20} className="text-semantic-info" />
          </div>
          <div>
            <h2 className="font-semibold">Appearance</h2>
            <p className="text-xs text-cascade-sage">Customize the look and feel</p>
          </div>
        </div>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Chart Theme</label>
            <select
              value={preferences.chartTheme}
              onChange={(e) => setPreferences({ chartTheme: e.target.value as 'light' | 'dark' })}
              className="input-field w-40"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Decimal Places</label>
            <select
              value={preferences.decimalPlaces}
              onChange={(e) => setPreferences({ decimalPlaces: parseInt(e.target.value) })}
              className="input-field w-40"
            >
              <option value={1}>1</option>
              <option value={2}>2</option>
              <option value={3}>3</option>
              <option value={4}>4</option>
            </select>
          </div>

          <div className="flex items-center justify-between">
            <label className="text-sm font-medium">Auto-save analyses</label>
            <button
              onClick={() => setPreferences({ autoSave: !preferences.autoSave })}
              className={`relative w-11 h-6 rounded-full transition-colors ${
                preferences.autoSave ? 'bg-cascade-gold' : 'bg-cascade-mist'
              }`}
            >
              <span className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                preferences.autoSave ? 'translate-x-5' : ''
              }`} />
            </button>
          </div>
        </div>
      </div>

      {/* Language */}
      <div className="card">
        <div className="flex items-center gap-3 mb-6">
          <div className="w-10 h-10 rounded-xl bg-semantic-warning/10 flex items-center justify-center">
            <Globe size={20} className="text-semantic-warning" />
          </div>
          <div>
            <h2 className="font-semibold">Language & Region</h2>
            <p className="text-xs text-cascade-sage">Set your preferred language</p>
          </div>
        </div>

        <div className="flex items-center justify-between">
          <label className="text-sm font-medium">Display Language</label>
          <select
            value={preferences.defaultLanguage}
            onChange={(e) => setPreferences({ defaultLanguage: e.target.value as 'en' | 'fa' | 'ar' })}
            className="input-field w-40"
          >
            <option value="en">English</option>
            <option value="fa">فارسی</option>
            <option value="ar">العربية</option>
          </select>
        </div>
      </div>
    </div>
  );
}