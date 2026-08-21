const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  openFile: () => ipcRenderer.invoke('open-file'),
  saveFile: (options) => ipcRenderer.invoke('save-file', options),
  getApiUrl: () => ipcRenderer.invoke('get-api-url'),
  getAppVersion: () => ipcRenderer.invoke('get-app-version'),

  onFileDrop: (callback) => {
    const handler = (event, filePath) => callback(filePath);
    ipcRenderer.on('file-drop', handler);
    return () => ipcRenderer.removeListener('file-drop', handler);
  },
});
