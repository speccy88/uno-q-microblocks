/* SPDX-License-Identifier: MPL-2.0
 * UNO Q transport extension to the pinned official GP IDE. No editor substitute.
 */
(()=>{
 const state={ws:null,rx:[],rxBytes:0,tx:[],txBytes:0,error:null}; const LIMIT=65536;
 const update=()=>{if(typeof GP!=='undefined')GP.apiCall('ide.updateConnection');};
 const notice=text=>{const e=document.getElementById('unoq-status');if(e)e.textContent=text;};
 const disconnect=()=>{if(state.ws)state.ws.close(1000,'Client disconnect');state.ws=null;state.rx=[];state.rxBytes=0;state.tx=[];state.txBytes=0;update();};
 const connect=()=>{
  if(state.ws)return;
  state.error=null;notice('Connecting to Arduino UNO Q…');
  const socket=new WebSocket((location.protocol==='https:'?'wss://':'ws://')+location.host+'/ws/vm');socket.binaryType='arraybuffer';state.ws=socket;
  socket.onopen=()=>{for(const bytes of state.tx)socket.send(bytes);state.tx=[];state.txBytes=0;state.rx=[];state.rxBytes=0;notice('Arduino UNO Q (SmallVM)');update();};
  socket.onmessage=e=>{
   if(!(e.data instanceof ArrayBuffer)){state.error='Invalid binary response';socket.close(1003,state.error);return;}
   const bytes=new Uint8Array(e.data);
   if(state.rxBytes+bytes.length>LIMIT){state.error='Browser input queue full';socket.close(1009,state.error);return;}
   state.rx.push(bytes);state.rxBytes+=bytes.length;
  };
  socket.onclose=e=>{if(state.ws===socket)state.ws=null;state.rx=[];state.rxBytes=0;state.tx=[];state.txBytes=0;notice(e.reason||state.error||'Disconnected — use Connect to resume');update();};
  socket.onerror=()=>notice('Connection unavailable. Check the App and resident runtime.');
 };
 window.hasWebSerial=()=>true;window.webSerialIsConnected=()=>!!state.ws&&[WebSocket.CONNECTING,WebSocket.OPEN].includes(state.ws.readyState);
 window.webSerialConnect=connect;window.webSerialDisconnect=disconnect;
 window.GP_openSerialPort=()=>{connect();return 1;};
 window.GP_isOpenSerialPort=window.webSerialIsConnected;
 window.GP_closeSerialPort=disconnect;
 window.GP_getSerialPorts=()=>{GP_serialPortNames=[toUTF8Array('Arduino UNO Q (SmallVM)')];};
 window.GP_readSerialPort=max=>{
  const count=Math.min(max,state.rxBytes);const out=new Uint8Array(count);let pos=0;
  while(pos<count){const first=state.rx[0];const n=Math.min(first.length,count-pos);out.set(first.subarray(0,n),pos);pos+=n;
   if(n===first.length)state.rx.shift();else state.rx[0]=first.subarray(n);
  }
  state.rxBytes-=count;return out;
 };
 window.GP_writeSerialPort=data=>{
  const socket=state.ws;
  if(!socket)return 0;
  if(socket.readyState===WebSocket.CONNECTING){
   if(state.txBytes+data.byteLength>LIMIT){state.error='Connection pending queue full';disconnect();return 0;}
   state.tx.push(data.slice());state.txBytes+=data.byteLength;return data.byteLength;
  }
  if(socket.readyState!==WebSocket.OPEN)return 0;
  if(socket.bufferedAmount+data.byteLength>LIMIT){state.error='Browser output queue full';socket.close(1009,state.error);return 0;}
  socket.send(data.slice());return data.byteLength;
 };
 window.GP_setSerialPortDTR=()=>{};window.GP_setSerialPortRTS=()=>{};window.GP_setSerialPortDTRandRTS=()=>{};
 const original=GP.apiCall.bind(GP);
 GP.apiCall=(endpoint,params,callback)=>{
  if(endpoint.startsWith('board.installVM')||endpoint==='board.toggleBLE'){
   notice('Runtime installation is a separate guarded operation.');if(callback)callback(0);return;
  }
  return original(endpoint,params,callback);
 };
 document.addEventListener('ready',()=>{
  Menus.settings.items=Menus.settings.items.filter(x=>!/(firmware|ESP firmware|new versions)/i.test(x.label||''));
  Menus.connection.items=[
   {label:'Arduino UNO Q (SmallVM)',action:()=>GP.apiCall('board.connect',['connect (USB)']),hidden:()=>IDE.board.connected},
   {label:'Disconnect UNO Q',action:()=>{disconnect();GP.apiCall('board.disconnect');},hidden:()=>!IDE.board.connected}
  ];
  // Local integration controls use the real GP import/compiler path.
  const bar=document.querySelector('[data-ide="controls"]');
  const status=document.createElement('span');status.id='unoq-status';status.setAttribute('role','status');bar.prepend(status);
  const menu=document.createElement('select');menu.setAttribute('aria-label','UNO Q examples');
  [['','UNO Q examples'],['arithmetic','Arithmetic'],['output','500 outputs'],['rgb','RGB LEDs'],['matrix','LED matrix'],['combined','Combined hardware']].forEach(([value,text])=>{const option=document.createElement('option');option.value=value;option.textContent=text;menu.append(option);});
  menu.onchange=()=>{if(menu.value)GP.apiCall('unoq.openExample',[menu.value]);menu.value='';};bar.prepend(menu);
  const load=document.createElement('button');load.textContent='UNO Q Hardware';load.onclick=()=>GP.apiCall('unoq.loadLibrary');bar.prepend(load);
  GP.apiCall('unoq.loadLibrary');
  GP.apiCall('board.connect',['connect (USB)']);
 });
 window.UNOQTransportStatus=()=>({connected:webSerialIsConnected(),rxBytes:state.rxBytes,error:state.error});
})();
