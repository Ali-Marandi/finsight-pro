import { app, BrowserWindow, ipcMain, dialog, shell } from 'electron';
import path from 'path';
import { spawn, ChildProcess } from 'child_process';
import fs from 'fs';

let mainWindow: BrowserWindow | null = null;
let apiProcess: ChildProcess | null = null;

const isDev = !app.isPackaged;
const API_PORT = 8000;
const API_STARTUP_TIMEOUT = 30000;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 1024,
    minHeight: 680,
    title: 'FinSight Pro',
    backgroundColor: '#f5f5f4',
    frame: false,
    titleBarStyle: 'hidden',
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
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

  // Prevent external navigation
  mainWindow.webContents.on('will-navigate', (event, url) => {
    if (url !== 'http://localhost:5173' && !url.startsWith('file://')) {
      event.preventDefault();
      shell.openExternal(url);
    }
  });
}

function startApiServer(): Promise<void> {
  return new Promise((resolve, reject) => {
    const apiPath = isDev
      ? path.join(__dirname, '..', '..', 'api')
      : path.join(process.resourcesPath, 'api');

    // Check if api directory exists
    if (!fs.existsSync(apiPath)) {
      console.warn(`API directory not found at ${apiPath}, running without backend`);
      resolve();
      return;
    }

    const pythonExe = isDev
      ? 'python3'
      : path.join(process.resourcesPath, 'python', 'python.exe');

    const args = [
      '-m', 'uvicorn', 'app.main:app',
      '--host', '127.0.0.1',
      '--port', String(API_PORT),
      '--log-level', 'warning',
    ];

    apiProcess = spawn(pythonExe, args, {
      cwd: apiPath,
      env: { ...process.env, FINSIGHT_ENV: isDev ? 'development' : 'production' },
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    let started = false;
    const timeout = setTimeout(() => {
      if (!started) {
        console.warn('API server startup timed out, continuing without backend');
        resolve();
      }
    }, API_STARTUP_TIMEOUT);

    apiProcess.stdout?.on('data', (data: Buffer) => {
      const msg = data.toString();
      console.log(`[API] ${msg}`);
      if (!started && msg.includes('Uvicorn running')) {
        started = true;
        clearTimeout(timeout);
        console.log('API server is ready');
        resolve();
      }
    });

    apiProcess.stderr?.on('data', (data: Buffer) => {
      const msg = data.toString();
      console.error(`[API] ${msg}`);
      if (!started && msg.includes('Uvicorn running')) {
        started = true;
        clearTimeout(timeout);
        resolve();
      }
    });

    apiProcess.on('error', (err) => {
      console.error('Failed to start API server:', err);
      clearTimeout(timeout);
      resolve(); // Don't block the app
    });

    apiProcess.on('exit', (code, signal) => {
      console.log(`API process exited with code ${code}, signal ${signal}`);
      apiProcess = null;
    });
  });
}

function stopApiServer() {
  if (apiProcess) {
    try {
      apiProcess.kill('SIGTERM');
      // Force kill after 3 seconds
      const forceKill = setTimeout(() => {
        if (apiProcess) {
          apiProcess.kill('SIGKILL');
          apiProcess = null;
        }
      }, 3000);
      apiProcess.on('exit', () => clearTimeout(forceKill));
    } catch (e) {
      console.error('Error stopping API:', e);
    }
  }
}

// IPC Handlers

ipcMain.handle('open-file', async () => {
  if (!mainWindow) return null;
  const result = await dialog.showOpenDialog(mainWindow, {
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
  if (!mainWindow) return null;
  const result = await dialog.showSaveDialog(mainWindow, {
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

ipcMain.handle('read-file-buffer', async (_event, filePath: string) => {
  try {
    const buffer = fs.readFileSync(filePath);
    const ext = path.extname(filePath).toLowerCase();
    const mimeTypes: Record<string, string> = {
      '.csv': 'text/csv',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.xls': 'application/vnd.ms-excel',
    };
    return {
      buffer: buffer.toString('base64'),
      name: path.basename(filePath),
      mimeType: mimeTypes[ext] || 'application/octet-stream',
    };
  } catch (err: any) {
    throw new Error(`Failed to read file: ${err.message}`);
  }
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

// Window control IPC
ipcMain.handle('window-minimize', () => {
  mainWindow?.minimize();
});

ipcMain.handle('window-maximize', () => {
  if (mainWindow?.isMaximized()) {
    mainWindow.unmaximize();
  } else {
    mainWindow?.maximize();
  }
});

ipcMain.handle('window-close', () => {
  mainWindow?.close();
});

ipcMain.handle('window-is-maximized', () => {
  return mainWindow?.isMaximized() ?? false;
});

// App Lifecycle

app.whenReady().then(async () => {
  await startApiServer();
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
