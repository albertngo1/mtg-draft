// Safe bridge: the sandboxed renderer only sees these three hooks.
import { contextBridge, ipcRenderer } from 'electron';

const api: OverlayAPI = {
  onPack: (cb) => ipcRenderer.on('pack', (_e, pack: Pack) => cb(pack)),
  onState: (cb) => ipcRenderer.on('state', (_e, state: OverlayState) => cb(state)),
  // let a hovered interactive element grab the mouse while the window is passive
  setIgnore: (ignore) => ipcRenderer.send('set-ignore', ignore),
};

contextBridge.exposeInMainWorld('overlay', api);
