const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../extension/source/userfunctions.js'), 'utf8');

test('invokes native realtime fastForwardTime exactly once without arguments', () => {
  const calls = [];
  const context = vm.createContext({ipc: {appWindow: () => ({
    getRealtimeToolbar: () => ({fastForwardTime: (...args) => calls.push(args)})
  })}});
  vm.runInContext(source, context);
  const result = context.fastForwardTime();
  assert.equal(result.success, true);
  assert.deepEqual(calls, [[]]);
  assert.equal(result.converged, undefined);
  assert.match(result.message, /requested/i);
});

test('reports native fast forward failures', () => {
  const context = vm.createContext({ipc: {appWindow: () => ({
    getRealtimeToolbar: () => ({fastForwardTime: () => {throw new Error('native failure');}})
  })}});
  vm.runInContext(source, context);
  const result = context.fastForwardTime();
  assert.equal(result.success, false);
  assert.match(result.error, /native failure/);
});
