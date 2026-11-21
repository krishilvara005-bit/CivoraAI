import { execSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, '..');

console.log('=== [1/4] Installing Frontend Dependencies ===');
execSync('npm --prefix frontend install', { cwd: root, stdio: 'inherit' });

console.log('\n=== [2/4] Building Vite Frontend ===');
execSync('npm --prefix frontend run build', { cwd: root, stdio: 'inherit' });

console.log('\n=== [3/4] Installing Gateway Dependencies ===');
execSync('npm --prefix gateway install', { cwd: root, stdio: 'inherit' });

console.log('\n=== [4/4] Installing Python Backend Requirements (if python/pip available) ===');
try {
  const pyCmd = process.platform === 'win32' ? 'python' : 'python3';
  execSync(`${pyCmd} -m pip install -r backend/requirements.txt`, { cwd: root, stdio: 'inherit' });
  console.log('Backend requirements installed successfully.');
} catch (err) {
  console.log('Note: Python dependencies install skipped or failed. Continuing build.');
}

console.log('\n=== Civora AI Platform Build Complete ===');
