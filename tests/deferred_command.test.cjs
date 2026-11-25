const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../extension/source/userfunctions.js'), 'utf8');

// TerminalLine falsa: registerEvent(nombre, contexto, función) como en la API IPC de PT.
function fakeLine() {
  const handlers = {};
  return {
    entered: [],
    registerEvent(name, ctx, fn) { (handlers[name] = handlers[name] || []).push([ctx, fn]); },
    unregisterEvent(name, ctx, fn) {
      handlers[name] = (handlers[name] || []).filter(([c, f]) => !(c === ctx && f === fn));
    },
    emit(name, args) { for (const [c, f] of handlers[name] || []) f.call(c, this, args); },
    count(name) { return (handlers[name] || []).length; },
    enterCommand(cmd) { this.entered.push(cmd); },
  };
}

function load(devices) {
  const context = vm.createContext({ipc: {network: () => ({getDevice: (n) => devices[n] || null})}});
  vm.runInContext(source, context);
  return context;
}

test('PC: lanza el comando en el Command Prompt y acumula outputWritten', () => {
  const line = fakeLine();
  const ctx = load({PC10: {getCommandPrompt: () => line}});
  const start = ctx.startCommand('PC10', 'ping 192.168.10.1');
  assert.equal(start.success, true);
  assert.equal(start.terminal, 'pc');
  assert.deepEqual(line.entered, ['ping 192.168.10.1']);

  line.emit('outputWritten', {newOutput: 'Reply from 192.168.10.1: bytes=32\n'});
  line.emit('outputWritten', {newOutput: 'Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),\n'});
  line.emit('commandEnded', {status: 0});
  const read = ctx.readCommandOutput('PC10', true);
  assert.equal(read.success, true);
  assert.match(read.output, /Reply from[\s\S]*Lost = 0/);
  assert.equal(read.ended, true);
  assert.equal(read.events, 2);
  assert.equal(line.count('outputWritten'), 0, 'finish desuscribe los eventos');
});

function iosDevice(prompt) {
  const ipcLine = fakeLine();
  const consoleLine = fakeLine();
  consoleLine.prompt = prompt;
  consoleLine.getPrompt = function () { return this.prompt; };
  consoleLine.enterCommand = function (cmd) {
    this.entered.push(cmd);
    if (cmd === '') this.prompt = 'DS1>';
  };
  const device = {
    getIpcTerminalLine: () => ipcLine,
    getCommandLine: () => consoleLine,
    enterCommand: () => { throw new Error('el ping IOS no debe ir por device.enterCommand'); },
  };
  return {ipcLine, consoleLine, device};
}

test('IOS: teclea el comando en la consola y lee su salida', () => {
  const {ipcLine, consoleLine, device} = iosDevice('DS1#');
  const ctx = load({DS1: device});
  const start = ctx.startCommand('DS1', 'ping 192.168.30.10');
  assert.equal(start.success, true);
  assert.equal(start.terminal, 'ipc,console');
  assert.deepEqual(consoleLine.entered, ['ping 192.168.30.10']);
  consoleLine.emit('outputWritten', '!!!!!\nSuccess rate is 100 percent (5/5)\n');
  const read = ctx.readCommandOutput('DS1', true);
  assert.match(read.output, /Success rate is 100 percent/);
  assert.equal(read.terminal, 'console');
  assert.equal(read.eventsPerLine.console, 1);
  assert.equal(ipcLine.count('outputWritten') + consoleLine.count('outputWritten'), 0);
});

test('IOS: en modo configuración antepone do', () => {
  const {consoleLine, device} = iosDevice('DS1(config-if)#');
  const ctx = load({DS1: device});
  const start = ctx.startCommand('DS1', 'ping 1.1.1.1');
  assert.equal(start.typed, 'do ping 1.1.1.1');
  assert.deepEqual(consoleLine.entered, ['do ping 1.1.1.1']);
});

test('IOS: con la consola en «Press RETURN» manda primero un Enter', () => {
  const {consoleLine, device} = iosDevice('');
  const ctx = load({DS1: device});
  const start = ctx.startCommand('DS1', 'traceroute 1.1.1.1');
  assert.deepEqual(consoleLine.entered, ['', 'traceroute 1.1.1.1']);
  assert.equal(start.promptBefore, '');
  assert.equal(start.promptAfter, 'DS1>');
});

test('un comando nuevo en el mismo equipo descarta la captura anterior', () => {
  const line = fakeLine();
  const ctx = load({PC10: {getCommandPrompt: () => line}});
  ctx.startCommand('PC10', 'ipconfig');
  ctx.startCommand('PC10', 'arp -a');
  assert.equal(line.count('outputWritten'), 1);
  assert.equal(ctx.readCommandOutput('PC10', false).command, 'arp -a');
});

test('errores: equipo inexistente y lectura sin comando', () => {
  const ctx = load({});
  assert.equal(ctx.startCommand('X', 'ping 1.1.1.1').success, false);
  assert.equal(ctx.readCommandOutput('X', false).success, false);
});
