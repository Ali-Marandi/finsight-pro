/* Electron type declarations */
interface ElectronAPI {
  openFile: () => Promise<string | null>;
  saveFile: (options: { defaultName: string; filters: Array<{ name: string; extensions: string[] }> }) => Promise<string | null>;
  getApiUrl: () => Promise<string>;
  getAppVersion: () => Promise<string>;
}

interface Window {
  electronAPI?: ElectronAPI;
}