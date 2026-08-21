import { contextBridge, ipcRenderer } from 'electron';

export interface ElectronAPI {
  openFile: () => Promise<string | null>;
  saveFile: (suggestedName: string) => Promise<string | null>;
  getApiUrl: () => Promise<string>;
  getAppVersion: () => Promise<string>;
  getAppPath: () => Promise<string>;
}

const electronAPI: ElectronAPI = {
  openFile: () => ipcRenderer.invoke('open-file'),
  saveFile: (suggestedName: string) => ipcRenderer.invoke('save-file', suggestedName),
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),
  getAppPath: () => ipcRenderer.invoke('get-app-path'),
};

contextBridge.exposeInMainWorld('electronAPI', electronAPI);
