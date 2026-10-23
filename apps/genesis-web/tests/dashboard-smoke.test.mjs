import assert from 'node:assert/strict';
import { spawn, spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const SERVER = fileURLToPath(new URL('../server.mjs', import.meta.url));

async function freePort() {
  const server = net.createServer();
  await new Promise((resolve, reject) => server.once('error', reject).listen(0, '127.0.0.1', resolve));
  const port = server.address().port;
  await new Promise(resolve => server.close(resolve));
  return port;
}

async function launchServer(trusts, port) {
  const child = spawn(process.execPath, [SERVER], {
    env: { ...process.env, AIFT_TRUSTS: trusts, PORT: String(port), HOST: '127.0.0.1' },
    stdio: ['ignore', 'pipe', 'pipe'],
  });
  let output = '';
  const ready = new Promise((resolve, reject) => {
    const timer = setTimeout(() => reject(new Error(`Dashboard did not start: ${output}`)), 4000);
    child.stdout.on('data', data => {
      output += data;
      if (output.includes('Dashboard running at')) {
        clearTimeout(timer);
        resolve();
      }
    });
    child.stderr.on('data', data => { output += data; });
    child.once('exit', code => {
      clearTimeout(timer);
      reject(new Error(`Dashboard exited ${code}: ${output}`));
    });
  });
  try {
    await ready;
    return child;
  } catch (error) {
    child.kill();
    throw error;
  }
}

test('documented Node entry point parses', () => {
  const result = spawnSync(process.execPath, ['--check', SERVER], { encoding: 'utf8' });
  assert.equal(result.status, 0, result.stderr);
});

test('documented local server starts and serves HTML plus trust listings', async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'genesis-web-smoke-'));
  const trusts = path.join(base, 'trusts');
  const trust = path.join(trusts, 'example');
  fs.mkdirSync(trust, { recursive: true });
  fs.writeFileSync(path.join(trust, 'LOCAL_MANIFEST.json'), JSON.stringify({ trust: { name: 'Example Trust' } }));
  const port = await freePort();
  let child;
  try {
    child = await launchServer(trusts, port);
    const homepage = await fetch(`http://127.0.0.1:${port}/`);
    assert.equal(homepage.status, 200);
    const html = await homepage.text();
    assert.match(html, /AIFT Genesis Dashboard/);
    const listing = await fetch(`http://127.0.0.1:${port}/api/trusts`);
    assert.equal(listing.status, 200);
    const data = await listing.json();
    assert.equal(data.trusts[0].name, 'Example Trust');
  } finally {
    child?.kill();
    fs.rmSync(base, { recursive: true, force: true });
  }
});

test('dashboard inline JavaScript parses and displays trust names as text', async () => {
  const source = fs.readFileSync(SERVER, 'utf8');
  const inline = source.split('<script>')[1]?.split('</script>')[0];
  assert.ok(inline, 'Dashboard inline script not found');
  new vm.Script(inline);
  const elements = [];
  function element(tag) {
    const el = {
      tag,
      style: {},
      children: [],
      textContent: '',
      append(...nodes) { this.children.push(...nodes); },
      replaceChildren(...nodes) { this.children = nodes; },
      addEventListener(event, handler) { this.handler = handler; },
      set innerHTML(_) { throw new Error('Untrusted data must not use innerHTML'); },
    };
    elements.push(el);
    return el;
  }
  const trusts = element('div');
  const output = element('pre');
  const document = {
    getElementById(id) { return id === 'trusts' ? trusts : output; },
    createElement: element,
  };
  const suspicious = '<b>Example</b>';
  const fetch = async () => ({ ok: true, json: async () => ({ trusts: [{ name: suspicious, slug: 'example' }] }) });
  vm.runInNewContext(inline, { document, fetch });
  await new Promise(resolve => setImmediate(resolve));
  assert.equal(trusts.children.length, 1);
  const button = elements.find(el => el.tag === 'button');
  assert.equal(button?.textContent, suspicious);
  assert.equal(typeof button?.handler, "function");
});

test('trust summary routes reject sibling-prefix and symlink escapes', async () => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'genesis-trust-boundary-'));
  const trusts = path.join(base, 'trusts');
  const outside = path.join(base, 'trusts-private');
  fs.mkdirSync(trusts);
  fs.mkdirSync(outside);
  fs.writeFileSync(path.join(outside, 'LOCAL_MANIFEST.json'),
    JSON.stringify({ trust: { name: 'Outside confidential trust' } }));
  fs.symlinkSync(outside, path.join(trusts, 'external-link'));

  const legitimate = path.join(trusts, 'legitimate');
  fs.mkdirSync(legitimate);
  fs.writeFileSync(path.join(legitimate, 'LOCAL_MANIFEST.json'),
    JSON.stringify({ trust: { name: 'Legitimate trust' } }));

  const port = await freePort();
  let child;
  try {
    child = await launchServer(trusts, port);
    for (const slug of ['../trusts-private', 'external-link']) {
      const response = await fetch(
        `http://127.0.0.1:${port}/api/trust/${encodeURIComponent(slug)}`
      );
      assert.notEqual(response.status, 200, `escaped trust ${slug} must not be served`);
      assert.doesNotMatch(await response.text(), /Outside confidential trust/);
    }
    const allowed = await fetch(`http://127.0.0.1:${port}/api/trust/legitimate`);
    assert.equal(allowed.status, 200);
    assert.equal((await allowed.json()).manifest.trust.name, 'Legitimate trust');
  } finally {
    child?.kill();
    fs.rmSync(base, { recursive: true, force: true });
  }
});
