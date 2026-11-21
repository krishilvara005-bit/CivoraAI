import fs from 'node:fs';
import path from 'node:path';
import express from 'express';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import { createProxyMiddleware } from 'http-proxy-middleware';

export function createApp({ backend, dist, quiet = false }) {
  const app = express();
  app.disable('x-powered-by');
  if (process.env.TRUST_PROXY) app.set('trust proxy', 1);

  app.use(
    helmet({
      contentSecurityPolicy: {
        directives: {
          defaultSrc: ["'self'"],
          imgSrc: ["'self'", 'data:', 'blob:'],
          styleSrc: ["'self'", "'unsafe-inline'", 'https://fonts.googleapis.com'],
          fontSrc: ["'self'", 'https://fonts.gstatic.com'],
          objectSrc: ["'self'"],
          frameSrc: ["'self'"],
          connectSrc: ["'self'"],
        },
      },
    }),
  );
  if (!quiet) app.use(morgan('tiny'));

  const limiter = (windowMs, limit) =>
    rateLimit({ windowMs, limit, standardHeaders: true, legacyHeaders: false, message: { error: 'Too many requests. Try again shortly.' } });
  app.use('/api/assistant', limiter(5 * 60 * 1000, 20));
  app.use('/api', limiter(15 * 60 * 1000, 600));

  app.get('/healthz', async (_req, res) => {
    let backendStatus = 'down';
    try {
      const r = await fetch(`${backend}/api/health`, { signal: AbortSignal.timeout(2000) });
      if (r.ok) backendStatus = 'ok';
    } catch {
      /* backend unreachable */
    }
    res.status(backendStatus === 'ok' ? 200 : 503).json({ gateway: 'ok', backend: backendStatus });
  });

  // Mounted at the root with a path filter so the /api prefix reaches Flask unchanged.
  app.use(
    createProxyMiddleware({
      target: backend,
      changeOrigin: true,
      pathFilter: '/api',
      proxyTimeout: 60_000,
      on: {
        error: (_err, _req, res) => {
          if (typeof res.writeHead !== 'function') return;
          if (!res.headersSent) res.writeHead(502, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'The analysis service is unavailable.' }));
        },
      },
    }),
  );

  const index = dist && path.join(dist, 'index.html');
  if (index && fs.existsSync(index)) {
    app.use('/assets', express.static(path.join(dist, 'assets'), { immutable: true, maxAge: '1y' }));
    app.use(express.static(dist, { index: false, maxAge: '1h' }));
    app.use((req, res, next) => (req.method === 'GET' ? res.sendFile(index) : next()));
  } else {
    app.get('/', (_req, res) =>
      res.status(200).json({ message: 'Frontend not built. Run "npm run build" in frontend/, or use the Vite dev server on port 5173.' }),
    );
  }
  app.use((_req, res) => res.status(404).json({ error: 'Not found.' }));
  return app;
}
