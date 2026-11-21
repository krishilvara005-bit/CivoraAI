import assert from 'node:assert/strict';
import fs from 'node:fs';
import http from 'node:http';
import os from 'node:os';
import path from 'node:path';
import { after, before, test } from 'node:test';
import { createApp } from '../src/app.js';

const listen = (server) => new Promise((r) => server.listen(0, '127.0.0.1', () => r(server.address().port)));
let fake, gw, base, dist;

before(async () => {
  fake = http.createServer((req, res) => {
    res.setHeader('Content-Type', 'application/json');
    res.end(JSON.stringify({ path: req.url, method: req.method }));
  });
  const fakePort = await listen(fake);
  dist = fs.mkdtempSync(path.join(os.tmpdir(), 'dist-'));
  fs.writeFileSync(path.join(dist, 'index.html'), '<!doctype html><title>spa</title>');
  gw = http.createServer(createApp({ backend: `http://127.0.0.1:${fakePort}`, dist, quiet: true }));
  base = `http://127.0.0.1:${await listen(gw)}`;
});
after(() => { fake.close(); gw.close(); });

test('proxies /api requests with the path unchanged', async () => {
  const r = await fetch(`${base}/api/projects?x=1`);
  assert.deepEqual(await r.json(), { path: '/api/projects?x=1', method: 'GET' });
});

test('sends security headers', async () => {
  const r = await fetch(`${base}/`);
  assert.ok(r.headers.get('content-security-policy'));
  assert.equal(r.headers.get('x-powered-by'), null);
});

test('serves the SPA for client-side routes', async () => {
  const r = await fetch(`${base}/projects/abc/cost`);
  assert.match(await r.text(), /<title>spa<\/title>/);
});

test('healthz reports the backend', async () => {
  const r = await fetch(`${base}/healthz`);
  assert.equal(r.status, 200);
  assert.deepEqual(await r.json(), { gateway: 'ok', backend: 'ok' });
});

test('returns 502 JSON when the backend is down', async () => {
  const down = http.createServer(createApp({ backend: 'http://127.0.0.1:1', dist, quiet: true }));
  const url = `http://127.0.0.1:${await listen(down)}`;
  const r = await fetch(`${url}/api/projects`);
  assert.equal(r.status, 502);
  assert.match((await r.json()).error, /unavailable/);
  down.close();
});

test('rate limits the assistant', async () => {
  let last;
  for (let i = 0; i < 22; i++) last = await fetch(`${base}/api/assistant`, { method: 'POST' });
  assert.equal(last.status, 429);
});
