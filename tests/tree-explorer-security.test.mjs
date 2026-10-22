import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import vm from 'node:vm';
import { fileURLToPath } from 'node:url';
import test from 'node:test';

const ROOT = fileURLToPath(new URL('../', import.meta.url));
const HTML = path.join(ROOT, 'docs/generated/tree-of-emergence.html');

function explorerScript() {
  const html = fs.readFileSync(HTML, 'utf8');
  const script = html.match(/<script>\s*([\s\S]*?)<\/script>/)?.[1];
  assert.ok(script, 'Generated Tree explorer inline script is missing');
  return script;
}

test('generated Tree explorer JavaScript parses', () => {
  new vm.Script(explorerScript());
});

test('Tree details treat manifest labels, status, and sources as text, not markup', () => {
  const script = explorerScript();
  const start = script.includes('function escapeHtml(')
    ? script.indexOf('function escapeHtml(')
    : script.indexOf('function formatValue(');
  const end = script.indexOf('function updateTransform()', start);
  assert.ok(start >= 0 && end > start, 'Tree details functions are missing');

  const elements = new Map();
  const document = {
    getElementById(id) {
      if (!elements.has(id)) elements.set(id, { textContent: '', innerHTML: '' });
      return elements.get(id);
    },
    querySelectorAll() { return []; },
  };
  const node = {
    id: 'first', label: 'First', description: 'Safe description',
    domain: 'physical', epistemicClass: 'empirical',
    status: '<img src=x onerror=alert(1)>', sourceRefs: ['source-one'],
  };
  const other = {
    id: 'second', label: '<svg onload=alert(2)>', description: 'Other',
    domain: 'physical', epistemicClass: 'empirical', status: 'active', sourceRefs: [],
  };
  const context = vm.createContext({
    document,
    nodes: new Map([[node.id, node], [other.id, other]]),
    edges: [{ from: 'first', to: 'second', relation: 'emerges-from', role: 'cross-link' }],
    sources: {
      'source-one': {
        label: '<img src=x onerror=alert(3)>',
        uri: '<img src=x onerror=alert(4)>',
      },
    },
  });
  vm.runInContext(script.slice(start, end) + "\nrenderDetails('first');", context);

  const meta = elements.get('detail-meta').innerHTML;
  const relationships = elements.get('detail-relationships').innerHTML;
  const sources = elements.get('detail-sources').innerHTML;
  for (const value of [meta, relationships, sources]) {
    assert.doesNotMatch(value, /<(?:img|svg)\b/i, 'Untrusted markup entered innerHTML');
  }
  assert.match(meta, /&lt;img src=x onerror=alert\(1\)&gt;/);
  assert.match(relationships, /&lt;svg onload=alert\(2\)&gt;/);
  assert.match(sources, /&lt;img src=x onerror=alert\(3\)&gt;/);
  assert.match(sources, /&lt;img src=x onerror=alert\(4\)&gt;/);
  assert.equal(elements.get('detail-description').textContent, 'Safe description');
});
