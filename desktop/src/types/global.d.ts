// Electron API exposed via preload
interface ElectronAPI {
  openFile: () => Promise<string | null>;
  saveFile: (suggestedName: string) => Promise<string | null>;
  getApiUrl: () => Promise<string>;
  getAppVersion: () => Promise<string>;
  getAppPath: () => Promise<string>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};
