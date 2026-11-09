const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../extension/source/userfunctions.js'), 'utf8');

function fixture({count = 0, result = 0, loaded = 'C:/lab.pkt', throws = false, initial = 'C:/previous.pkt'} = {}) {
  let current = initial;
  let calls = 0;
  const app = {
    getActiveFile: () => ({getSavedFilename: () => current}),
    fileOpen: () => { calls++; if (throws) throw new Error('native failure'); current = loaded; return result; }
  };
  const ctx = vm.createContext({ipc: {appWindow: () => app}});
  vm.runInContext(source, ctx);
  ctx.getNetwork = () => ({success: true, result: {deviceCount: count, connectionCount: 0, notes: []}});
  return {open: (...args) => ctx.openFile(...args), calls: () => calls};
}

test('verifies the actual opened filename and returns native code', () => {
  const f = fixture(); const r = f.open('C:/lab.pkt');
  assert.equal(r.success, true); assert.equal(r.path, 'C:/lab.pkt'); assert.equal(r.returnCode, 0);
});
test('reports failed or cancelled native opens with actual return code', () => {
  const r = fixture({loaded: 'C:/previous.pkt', result: 8}).open('C:/lab.pkt');
  assert.equal(r.success, false); assert.equal(r.returnCode, 8);
});
test('reports native exception as failure', () => {
  assert.equal(fixture({throws: true}).open('C:/lab.pkt').success, false);
});
test('an already active target is reported without reloading unsaved work', () => {
  const f = fixture({initial: 'C:/lab.pkt'}); const r = f.open('C:/lab.pkt');
  assert.equal(r.alreadyOpen, true); assert.equal(f.calls(), 0);
});
test('verifies UNC paths independent of case, separators and dot segments', () => {
  const r = fixture({loaded: '\\\\Server\\Share\\LAB.pkt'}).open('//server/share/sub/.././lab.pkt');
  assert.equal(r.success, true);
});
