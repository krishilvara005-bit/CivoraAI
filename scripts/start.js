import { spawn } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');
const port = process.env.PORT || 8080;

console.log('=== Starting Civora AI Platform Multi-Service Workstation ===');

// 1. Launch Python Flask backend
let backendProcess = null;
const pyCmd = process.platform === 'win32' ? 'python' : 'python3';

try {
  console.log(`[Backend] Launching Flask API with ${pyCmd} on port 5000...`);
  backendProcess = spawn(pyCmd, ['-m', 'flask', '--app', 'wsgi', 'run', '--port', '5000'], {
    cwd: path.join(root, 'backend'),
    stdio: 'inherit',
    env: { ...process.env, FLASK_APP: 'wsgi' }
  });

  backendProcess.on('error', (err) => {
    console.error('[Backend Warning] Could not launch Flask via spawn:', err.message);
  });
} catch (e) {
  console.error('[Backend Error]:', e.message);
}

// 2. Launch Node.js Edge Gateway
console.log(`[Gateway] Launching Gateway on port ${port}...`);
const gatewayProcess = spawn('node', ['src/index.js'], {
  cwd: path.join(root, 'gateway'),
  stdio: 'inherit',
  env: {
    ...process.env,
    PORT: String(port),
    BACKEND_URL: process.env.BACKEND_URL || 'http://127.0.0.1:5000'
  }
});

gatewayProcess.on('error', (err) => {
  console.error('[Gateway Error]:', err.message);
});

// 3. Graceful shutdown handler
const cleanExit = () => {
  console.log('\n[Civora] Stopping all background microservices...');
  if (backendProcess) {
    try { backendProcess.kill('SIGTERM'); } catch {}
  }
  if (gatewayProcess) {
    try { gatewayProcess.kill('SIGTERM'); } catch {}
  }
  process.exit(0);
};

process.on('SIGINT', cleanExit);
process.on('SIGTERM', cleanExit);
