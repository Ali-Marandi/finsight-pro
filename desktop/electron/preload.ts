import { contextBridge, ipcRenderer } from 'electron';

export interface ElectronAPI {
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

const electronAPI: ElectronAPI = {
  openFile: () => ipcRenderer.invoke('open-file'),
  saveFile: (suggestedName: string) => ipcRenderer.invoke('save-file', suggestedName),
  readFileBuffer: (filePath: string) => ipcRenderer.invoke('read-file-buffer', filePath),
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
  windowMinimize: () => ipcRenderer.invoke('window-minimize'),
  windowMaximize: () => ipcRenderer.invoke('window-maximize'),
  windowClose: () => ipcRenderer.invoke('window-close'),
  windowIsMaximized: () => ipcRenderer.invoke('window-is-maximized'),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
