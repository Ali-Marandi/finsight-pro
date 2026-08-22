import { useState, useEffect } from 'react';
import { useAnalysisStore } from '../hooks/useAnalysisStore';
import { useLicense } from '../hooks/useLicense';
import { Crown, Globe, Palette, Save, Key, RotateCcw, Monitor, Sparkles, Eye, EyeOff, CheckCircle, XCircle } from 'lucide-react';
import { updatePreferences, getAIConfig, configureAI } from '../lib/api';
import { useToast } from '../components/Toast';

export default function Settings() {
  const { preferences, setPreferences } = useAnalysisStore();
  const { license, activate, isPro } = useLicense();
  const { toast } = useToast();
  const [licenseKey, setLicenseKey] = useState('');
  const [activating, setActivating] = useState(false);
  const [saved, setSaved] = useState(false);

  // AI Configuration state
  const [aiApiKey, setAiApiKey] = useState('');
  const [aiEndpoint, setAiEndpoint] = useState('https://api.openai.com/v1');
  const [aiModel, setAiModel] = useState('gpt-4o-mini');
  const [aiConfigured, setAiConfigured] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [savingAI, setSavingAI] = useState(false);

  useEffect(() => {
    getAIConfig().then((cfg) => {
      setAiConfigured(cfg.configured);
      if (cfg.model) setAiModel(cfg.model);
      if (cfg.endpoint) setAiEndpoint(cfg.endpoint);
    });
  }, []);

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

  const handleSaveAI = async () => {
    if (!aiApiKey.trim()) {
      toast('error', 'API key is required');
      return;
    }
    setSavingAI(true);
    try {
      await configureAI(aiApiKey.trim(), aiEndpoint.trim(), aiModel.trim());
      setAiConfigured(true);
      toast('success', 'AI configuration saved');
    } catch {
      toast('error', 'Failed to save AI configuration');
    }
    setSavingAI(false);
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

      {/* AI Copilot Configuration */}
      <SettingsCard icon={Sparkles} iconBg="bg-gradient-to-br from-cascade-gold/10 to-amber-100" iconColor="text-cascade-gold" title="AI Financial Copilot" desc="Connect your LLM for intelligent analysis">
        <div className="space-y-4">
          <div className="flex items-center gap-2 mb-2">
            {aiConfigured ? (
              <span className="flex items-center gap-1.5 text-xs font-medium text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full">
                <CheckCircle size={12} /> Connected
              </span>
            ) : (
              <span className="flex items-center gap-1.5 text-xs font-medium text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full">
                <XCircle size={12} /> Using built-in engine
              </span>
            )}
          </div>

          <SettingRow label="API Key">
            <div className="relative w-72">
              <input
                type={showApiKey ? 'text' : 'password'}
                value={aiApiKey}
                onChange={(e) => setAiApiKey(e.target.value)}
                placeholder="sk-..."
                className="input-field w-full pr-10 font-mono text-xs"
              />
              <button
                type="button"
                onClick={() => setShowApiKey(!showApiKey)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-cascade-sage hover:text-cascade-charcoal"
              >
                {showApiKey ? <EyeOff size={14} /> : <Eye size={14} />}
              </button>
            </div>
          </SettingRow>

          <SettingRow label="API Endpoint">
            <select
              value={aiEndpoint}
              onChange={(e) => setAiEndpoint(e.target.value)}
              className="input-field w-72 text-xs"
            >
              <option value="https://api.openai.com/v1">OpenAI</option>
              <option value="https://api.deepseek.com/v1">DeepSeek</option>
              <option value="https://openrouter.ai/api/v1">OpenRouter</option>
              <option value="http://localhost:11434/v1">Ollama (Local)</option>
              <option value="custom">Custom Endpoint...</option>
            </select>
          </SettingRow>

          {aiEndpoint === 'custom' && (
            <SettingRow label="Custom URL">
              <input
                type="url"
                value={aiEndpoint}
                onChange={(e) => setAiEndpoint(e.target.value)}
                placeholder="https://your-api.com/v1"
                className="input-field w-72 text-xs font-mono"
              />
            </SettingRow>
          )}

          <SettingRow label="Model">
            <input
              type="text"
              value={aiModel}
              onChange={(e) => setAiModel(e.target.value)}
              placeholder="gpt-4o-mini"
              className="input-field w-72 text-xs font-mono"
            />
          </SettingRow>

          <div className="flex justify-end pt-1">
            <button
              onClick={handleSaveAI}
              disabled={savingAI || !aiApiKey.trim()}
              className="btn-primary flex items-center gap-2 text-xs"
            >
              <Sparkles size={14} /> {savingAI ? 'Saving...' : 'Save AI Config'}
            </button>
          </div>

          <p className="text-[10px] text-cascade-sage leading-relaxed">
            Without an API key, the AI Copilot uses a built-in rule-based engine that provides analysis
            in English and Persian. Connect an LLM for deeper, more nuanced insights.
            Your API key is stored locally and never sent to our servers.
          </p>
        </div>
      </SettingsCard>

      {/* About */}
      <SettingsCard icon={Monitor} iconBg="bg-cascade-mist" iconColor="text-cascade-sage" title="About" desc="Application information">
        <div className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-cascade-sage">Version</span><span className="font-medium">0.3.0</span></div>
          <div className="flex justify-between"><span className="text-cascade-sage">Engine</span><span className="font-medium">17 Ratios + 5 Prediction Models + AI</span></div>
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