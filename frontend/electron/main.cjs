const { app, BrowserWindow, Menu } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn, execSync } = require("child_process");

let exporterProcess = null;
let watcherProcess = null;

function getProjectRoot() {
  return path.resolve(__dirname, "../..");
}

function getPythonCommand(projectRoot) {
  const winPath = path.join(projectRoot, ".venv", "Scripts", "python.exe");
  const unixPath = path.join(projectRoot, ".venv", "bin", "python");
  if (fs.existsSync(winPath)) return winPath;
  if (fs.existsSync(unixPath)) return unixPath;
  return "python";
}

function getDesktopConfigPath() {
  return path.join(app.getPath("documents"), "My Games", "RLA", "desktop_config.json");
}

function ensureDesktopConfigFile() {
  const configPath = getDesktopConfigPath();
  const configDir = path.dirname(configPath);
  if (!fs.existsSync(configDir)) {
    fs.mkdirSync(configDir, { recursive: true });
  }
  if (!fs.existsSync(configPath)) {
    const defaults = {
      replayFolder: "",
      notes: "Set replayFolder to your Rocket League replay folder. Environment variable RLA_REPLAY_FOLDER overrides this file.",
    };
    fs.writeFileSync(configPath, JSON.stringify(defaults, null, 2), "utf-8");
  }
}

function readDesktopConfig() {
  try {
    ensureDesktopConfigFile();
    const raw = fs.readFileSync(getDesktopConfigPath(), "utf-8");
    return JSON.parse(raw);
  } catch (_) {
    return {};
  }
}

function getReplayFolder() {
  const envVal = process.env.RLA_REPLAY_FOLDER;
  if (envVal && envVal.trim() !== "") return envVal.trim();

  const config = readDesktopConfig();
  if (config.replayFolder && config.replayFolder.trim() !== "") {
    return config.replayFolder.trim();
  }
  return null;
}

function killProcess(child) {
  if (!child) return;
  try {
    if (process.platform === "win32") {
      execSync(`taskkill /PID ${child.pid} /T /F`, { stdio: "ignore" });
    } else {
      child.kill();
    }
  } catch (_) {}
}

function startLiveExporter() {
  if (exporterProcess) return;

  const projectRoot = getProjectRoot();
  const pythonCommand = getPythonCommand(projectRoot);
  const outputPath = path.resolve(__dirname, "../dist/dashboard_payload.json");

  exporterProcess = spawn(
    pythonCommand,
    ["-u", "-m", "rla_app.api.live_export_dashboard_payload_dev", "50", "5", "5", outputPath],
    {
      cwd: projectRoot,
      windowsHide: true,
      stdio: "pipe",
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    }
  );

  exporterProcess.stdout.on("data", (data) => process.stdout.write(`[RLA exporter] ${data}`));
  exporterProcess.stderr.on("data", (data) => process.stderr.write(`[RLA exporter error] ${data}`));
  exporterProcess.on("exit", () => { exporterProcess = null; });
}

function stopLiveExporter() {
  killProcess(exporterProcess);
  exporterProcess = null;
}

function startReplayWatcher() {
  if (watcherProcess) return;

  const configPath = getDesktopConfigPath();
  const replayFolder = getReplayFolder();

  if (!replayFolder) {
    console.log("[RLA watcher] Replay folder not configured. Watcher not started.");
    console.log(`[RLA watcher] Configure it at: ${configPath}`);
    return;
  }

  if (!fs.existsSync(replayFolder)) {
    console.error(`[RLA watcher error] Replay folder does not exist: ${replayFolder}`);
    return;
  }

  const projectRoot = getProjectRoot();
  const pythonCommand = getPythonCommand(projectRoot);

  watcherProcess = spawn(
    pythonCommand,
    ["-u", "-m", "rla_app.replay_intake.watch_folder_dev", replayFolder],
    {
      cwd: projectRoot,
      windowsHide: true,
      stdio: "pipe",
      env: { ...process.env, PYTHONUNBUFFERED: "1" },
    }
  );

  watcherProcess.stdout.on("data", (data) => process.stdout.write(`[RLA watcher] ${data}`));
  watcherProcess.stderr.on("data", (data) => process.stderr.write(`[RLA watcher error] ${data}`));
  watcherProcess.on("exit", () => { watcherProcess = null; });
}

function stopReplayWatcher() {
  killProcess(watcherProcess);
  watcherProcess = null;
}

function createWindow() {
  const win = new BrowserWindow({
    width: 1440,
    height: 900,
    minWidth: 1100,
    minHeight: 700,
    backgroundColor: "#0d0f18",
    title: "Rocket League Analyser",
    autoHideMenuBar: true,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      sandbox: true,
    },
  });

  win.loadFile(path.join(__dirname, "../dist/index.html"));
}

app.whenReady().then(() => {
  Menu.setApplicationMenu(null);
  startLiveExporter();
  startReplayWatcher();
  createWindow();

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
  });
});

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("before-quit", () => {
  stopLiveExporter();
  stopReplayWatcher();
});