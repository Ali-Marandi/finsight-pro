import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';

let mainWindow: BrowserWindow | null = null;
let apiProcess: ChildProcess | null = null;

const isDev = !app.isPackaged;
const API_PORT = 8000;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 800,
    minWidth: 1024,
    minHeight: 680,
    title: 'FinSight Pro',
    backgroundColor: '#f5f5f4',
    titleBarStyle: 'hiddenInset',
    trafficLightPosition: { x: 16, y: 16 },
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: true,
    },
  });

  if (isDev) {
    mainWindow.loadURL('http://localhost:5173');
    mainWindow.webContents.openDevTools({ mode: 'detach' });
  } else {
    mainWindow.loadFile(path.join(__dirname, '..', 'renderer', 'index.html'));
  }

  mainWindow.on('closed', () => {
    mainWindow = null;
  });
}

function startApiServer() {
  const apiPath = isDev
    ? path.join(__dirname, '..', '..', 'api')
    : path.join(process.resourcesPath, 'api');

  const pythonExe = isDev
    ? 'python'
    : path.join(process.resourcesPath, 'python', 'python.exe');

  apiProcess = spawn(pythonExe, ['-m', 'uvicorn', 'app.main:app', '--host', '127.0.0.1', '--port', String(API_PORT)], {
    cwd: apiPath,
    env: { ...process.env, FINSGHT_ENV: isDev ? 'development' : 'production' },
  });

  apiProcess.stdout?.on('data', (data: Buffer) => {
    console.log(`[API] ${data.toString()}`);
  });

  apiProcess.stderr?.on('data', (data: Buffer) => {
    console.error(`[API] ${data.toString()}`);
  });

  apiProcess.on('error', (err) => {
    console.error('Failed to start API server:', err);
  });
}

function stopApiServer() {
  if (apiProcess) {
    apiProcess.kill();
    apiProcess = null;
  }
}

// IPC Handlers

ipcMain.handle('open-file', async () => {
  const result = await dialog.showOpenDialog(mainWindow!, {
    properties: ['openFile'],
    filters: [
      { name: 'Financial Statements', extensions: ['csv', 'xlsx', 'xls'] },
      { name: 'All Files', extensions: ['*'] },
    ],
  });
  if (result.canceled) return null;
  return result.filePaths[0];
});

ipcMain.handle('save-file', async (_event, suggestedName: string) => {
  const result = await dialog.showSaveDialog(mainWindow!, {
    defaultPath: suggestedName,
    filters: [
      { name: 'PDF Report', extensions: ['pdf'] },
      { name: 'Excel Report', extensions: ['xlsx'] },
      { name: 'HTML Report', extensions: ['html'] },
    ],
  });
  if (result.canceled) return null;
  return result.filePath;
});

ipcMain.handle('get-api-url', () => {
  return `http://127.0.0.1:${API_PORT}/api/v1`;
});

ipcMain.handle('get-app-version', () => {
  return app.getVersion();
});

ipcMain.handle('get-app-path', () => {
  return app.getPath('userData');
});

// App Lifecycle

app.whenReady().then(() => {
  startApiServer();
  createWindow();

  app.on('activate', () => {
    if (BrowserWindow.getAllWindows().length === 0) {
      createWindow();
    }
  });
});

app.on('window-all-closed', () => {
  stopApiServer();
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('before-quit', () => {
  stopApiServer();
});
