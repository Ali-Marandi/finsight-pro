import { useState } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { useLicense } from '../hooks/useLicense';
import { Crown, Globe, Palette, Save, Key, RotateCcw, Monitor } from 'lucide-react';
import { updatePreferences } from '../lib/api';
import { useToast } from '../components/Toast';

export default function Settings() {
  const { preferences, setPreferences } = useAnalysisStore();
  const { license, activate, isPro } = useLicense();
  const { toast } = useToast();
  const [licenseKey, setLicenseKey] = useState('');
  const [activating, setActivating] = useState(false);
  const [saved, setSaved] = useState(false);

  const handleSave = async () => {
    try {
      await updatePreferences(preferences);
      setSaved(true);
      toast('success', 'Preferences saved');
      setTimeout(() => setSaved(false), 2000);
    } catch {
      toast('error', 'Failed to save preferences');
    }
  };

  const handleActivate = async () => {
    setActivating(true);
    try {
      const ok = await activate(licenseKey);
      if (ok) {
        toast('success', 'License activated successfully');
        setLicenseKey('');
      } else {
        toast('error', 'Invalid license key');
      }
    } catch {
      toast('error', 'Activation failed');
    }
    setActivating(false);
  };

  const handleReset = () => {
    setPreferences({ defaultLanguage: 'en', chartTheme: 'light', decimalPlaces: 2, autoSave: true });
    toast('info', 'Preferences reset to defaults');
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Settings</h1>
          <p className="text-cascade-sage text-sm mt-1">Configure your FinSight Pro experience</p>
        </div>
        <div className="flex gap-2">
          <button onClick={handleReset} className="btn-secondary flex items-center gap-2 text-xs">
            <RotateCcw size={14} /> Reset
          </button>
          <button onClick={handleSave} className="btn-primary flex items-center gap-2">
            <Save size={16} /> {saved ? 'Saved!' : 'Save'}
          </button>
        </div>
      </div>

      {/* License */}
      <SettingsCard icon={Crown} iconBg="bg-cascade-gold/10" iconColor="text-cascade-gold" title="License" desc="Manage your subscription and activation">
        {isPro ? (
          <div className="bg-semantic-success/5 border border-semantic-success/20 rounded-lg p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="status-good">Active</span>
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
                placeholder="FSP-PRO-XXXX-XXXX-XXXX"
                className="input-field flex-1 font-mono text-sm"
              />
              <button
                onClick={handleActivate}
                disabled={activating || !licenseKey}
                className="btn-primary flex items-center gap-2"
              >
                <Key size={16} /> {activating ? '...' : 'Activate'}
              </button>
            </div>
            <p className="text-xs text-cascade-sage">
              Don't have a key? <a href="https://finsightpro.com" className="text-cascade-gold hover:underline">Get one here</a>
            </p>
          </div>
        )}
      </SettingsCard>

      {/* Appearance */}
      <SettingsCard icon={Palette} iconBg="bg-semantic-info/10" iconColor="text-semantic-info" title="Appearance" desc="Customize the look and feel">
        <div className="space-y-4">
          <SettingRow label="Chart Theme">
            <select
              value={preferences.chartTheme}
              onChange={(e) => setPreferences({ chartTheme: e.target.value as 'light' | 'dark' })}
              className="input-field w-40"
            >
              <option value="light">Light</option>
              <option value="dark">Dark</option>
            </select>
          </SettingRow>

          <SettingRow label="Decimal Places">
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
          </SettingRow>

          <SettingRow label="Auto-save analyses">
            <Toggle checked={preferences.autoSave} onChange={(v) => setPreferences({ autoSave: v })} />
          </SettingRow>
        </div>
      </SettingsCard>

      {/* Language */}
      <SettingsCard icon={Globe} iconBg="bg-semantic-warning/10" iconColor="text-semantic-warning" title="Language & Region" desc="Set your preferred language">
        <SettingRow label="Display Language">
          <select
            value={preferences.defaultLanguage}
            onChange={(e) => setPreferences({ defaultLanguage: e.target.value as 'en' | 'fa' | 'ar' })}
            className="input-field w-40"
          >
            <option value="en">English</option>
            <option value="fa">\u0641\u0627\u0631\u0633\u06cc</option>
            <option value="ar">\u0627\u0644\u0639\u0631\u0628\u064a\u0629</option>
          </select>
        </SettingRow>
      </SettingsCard>

      {/* About */}
      <SettingsCard icon={Monitor} iconBg="bg-cascade-mist" iconColor="text-cascade-sage" title="About" desc="Application information">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-cascade-sage">Version</span><span className="font-medium">0.1.0-beta</span></div>
          <div className="flex justify-between"><span className="text-cascade-sage">Engine</span><span className="font-medium">17 Financial Ratios</span></div>
          <div className="flex justify-between"><span className="text-cascade-sage">License</span><span className="font-medium">{isPro ? (license?.tier?.toUpperCase() || 'PRO') : 'Free Tier'}</span></div>
          <div className="flex justify-between"><span className="text-cascade-sage">Data</span><span className="font-medium">Local Only</span></div>
        </div>
      </SettingsCard>
    </div>
  );
}

function SettingsCard({ icon: Icon, iconBg, iconColor, title, desc, children }: {
  icon: React.ElementType; iconBg: string; iconColor: string; title: string; desc: string; children: React.ReactNode;
}) {
  return (
    <div className="card">
      <div className="flex items-center gap-3 mb-5">
        <div className={`w-9 h-9 rounded-xl ${iconBg} flex items-center justify-center shrink-0`}>
          <Icon size={18} className={iconColor} />
        </div>
        <div>
          <h2 className="font-semibold text-sm">{title}</h2>
          <p className="text-xs text-cascade-sage">{desc}</p>
        </div>
      </div>
      {children}
    </div>
  );
}

function SettingRow({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <label className="text-sm font-medium">{label}</label>
      {children}
    </div>
  );
}

function Toggle({ checked, onChange }: { checked: boolean; onChange: (v: boolean) => void }) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={checked}
      onClick={() => onChange(!checked)}
      className={`relative w-10 h-[22px] rounded-full transition-colors ${
        checked ? 'bg-cascade-gold' : 'bg-cascade-mist'
      }`}
    >
      <span className={`absolute top-[3px] left-[3px] w-4 h-4 bg-white rounded-full shadow transition-transform ${
        checked ? 'translate-x-[18px]' : ''
      }`} />
    </button>
  );
}