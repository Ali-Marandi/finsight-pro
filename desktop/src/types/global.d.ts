interface ElectronAPI {
  openFile: () => Promise<string | null>;
  saveFile: (suggestedName: string) => Promise<string | null>;
  readFileBuffer: (filePath: string) => Promise<{ buffer: string; name: string; mimeType: string }>;
  getApiUrl: () => Promise<string>;
  getAppVersion: () => Promise<string>;
  getAppPath: () => Promise<string>;
  windowMinimize: () => Promise<void>;
  windowMaximize: () => Promise<void>;
  windowClose: () => Promise<void>;
  windowIsMaximized: () => Promise<boolean>;
}

declare global {
  interface Window {
    electronAPI?: ElectronAPI;
  }
}

export {};
