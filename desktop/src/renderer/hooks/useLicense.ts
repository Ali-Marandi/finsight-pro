import { useEffect } from 'react';
import { useAnalysisStore } from './useAnalysisStore';
import { validateLicense } from '../lib/api';

export function useLicense() {
  const { license, setLicense } = useAnalysisStore();

  useEffect(() => {
    // Check for stored license on mount
    const stored = localStorage.getItem('finsight_license_key');
    if (stored) {
      validateLicense(stored).then((res) => {
        if (res.data) setLicense(res.data);
      });
    }
  }, [setLicense]);

  const activate = async (key: string) => {
    const res = await validateLicense(key);
    if (res.data?.valid) {
      localStorage.setItem('finsight_license_key', key);
      setLicense(res.data);
      return true;
    }
    return false;
  };

  const isPro = license?.tier === 'pro' || license?.tier === 'enterprise';
  const isEnterprise = license?.tier === 'enterprise';

  return { license, activate, isPro, isEnterprise };
}
