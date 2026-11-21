import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { createApp } from './app.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const port = Number(process.env.PORT || 8080);
const backend = process.env.BACKEND_URL || 'http://127.0.0.1:5000';
const dist = process.env.FRONTEND_DIST || path.resolve(here, '../../frontend/dist');

createApp({ backend, dist }).listen(port, () => {
  console.log(`CIVORA gateway on http://localhost:${port}  ->  ${backend}`);
});
