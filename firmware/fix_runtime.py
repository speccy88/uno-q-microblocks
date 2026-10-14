"""Apply narrow UNO Q runtime corrections to prepared canonical source."""
def replace_function(s,name,replacement):
 import re
 m=re.search(r'^(?:static )?(?:inline )?[\w*]+\s+'+name+r'\([^\n]*\)\s*\{',s,re.M)
 assert m,name
 a=m.start();p=s.index('{',m.start());depth=1;q=p+1
 while depth:
  depth+=(s[q]=='{')-(s[q]=='}');q+=1
 return s[:a]+replacement+s[q:]

def fix(s):
 import re
 s=s.replace('#define OUTBUF_SIZE 1024','#define OUTBUF_SIZE 2048')
 # Bulk replies own cursors, and advance one bounded record at a time.
 marker='static void sendData();'
 s=s.replace(marker,marker+'''\nstatic void bulkTick();
static int bulkKind, bulkIndex;
static int *bulkVar;
uint32 unoRxTimeouts, unoTxFaults;
int unoOutputFaulted;
void unoTransportFault(void);
void unoRuntimeResetTransport(void);
''',1)
 pos=s.index('static inline void queueByte')
 s=s[:pos]+'''static void outputFault(void) {
 if (!unoOutputFaulted) { unoOutputFaulted=1; ++unoTxFaults; }
 outBufStart=outBufEnd=0; bulkKind=0; bulkVar=NULL;
 unoTransportFault(); // drop the partial stream explicitly; client must open a new session
}
'''+s[pos:]
 s=s.replace('static inline void queueByte(uint8 aByte) {','static inline void queueByte(uint8 aByte) {\n if (unoOutputFaulted) return;',1)
 s=s.replace('static void sendMessage(int msgType, int chunkIndex, int dataSize, char *data) {','static void sendMessage(int msgType, int chunkIndex, int dataSize, char *data) {\n if (unoOutputFaulted) return;',1)
 s=s.replace('if (!hasOutputSpace(3)) return;','if (!hasOutputSpace(3)) { outputFault(); return; }',1)
 s=s.replace('if (!hasOutputSpace(totalBytes)) return;','if (!hasOutputSpace(totalBytes)) { outputFault(); return; }',1)
 s=s.replace('int hasOutputSpace(int byteCount) { return ((OUTBUF_MASK - OUTBUF_BYTES()) > byteCount); }','int hasOutputSpace(int byteCount) { return !unoOutputFaulted && ((OUTBUF_MASK - OUTBUF_BYTES()) > byteCount); }')
 s=replace_function(s,'waitForOutbufBytes', '''static int waitForOutbufBytes(int bytesNeeded) {
 if (unoOutputFaulted) return 0;
 sendData();
 if (bytesNeeded >= OUTBUF_SIZE || bytesNeeded > OUTBUF_MASK-OUTBUF_BYTES()) {
  outputFault(); return 0;
 }
 return 1;
}''')
 # Every synchronous producer returns rather than spinning or writing a partial reply.
 s=re.sub(r'(?m)^(\s*)waitForOutbufBytes\(([^;\n]+)\);',r'\1if (!waitForOutbufBytes(\2)) return;',s)
 s=s.replace('''\twhile (ideConnected() && (OUTBUF_BYTES() > 0)) {
\t\tsendData(); // should eventually create enough room for bytesNeeded
\t}''','\tsendData(); // nonblocking: subsequent VM slices drain the queue')
 s=replace_function(s,'sendAllCRCs','''void sendAllCRCs() {bulkKind=1;bulkIndex=0;}''')
 s=replace_function(s,'sendAllCode','''static void sendAllCode() {bulkKind=2;bulkIndex=0;}''')
 s=replace_function(s,'sendVarNames','''static void sendVarNames() {bulkKind=3;bulkVar=varsStart();}''')
 # bulkTick uses existing message encoders, no delay inside the VM thread.
 pos=s.index('// Startup gestures')
 s=s[:pos]+'''static void bulkTick() {
 if (unoOutputFaulted) {bulkKind=0;return;}
 if (bulkKind==1) {
  int count=0;for(int i=0;i<MAX_CHUNKS;i++)if(chunks[i].code)count++;
  if(!hasOutputSpace(5+count*5))return;
  queueByte(251);queueByte(allCRCsMsg);queueByte(0);queueByte((count*5)&255);queueByte((count*5)>>8);
  for(int i=0;i<MAX_CHUNKS;i++)if(chunks[i].code) {
   OBJ c=chunks[i].code;uint32 value=crc32((uint8*)(c+2),4*(*(c+1)));
   queueByte(i);for(int b=0;b<4;b++)queueByte(value>>(8*b));
  }
  bulkKind=0;
 } else if(bulkKind==2) {
  while(bulkIndex<MAX_CHUNKS && !chunks[bulkIndex].code)bulkIndex++;
  if(bulkIndex==MAX_CHUNKS){bulkKind=0;return;}
  OBJ c=chunks[bulkIndex].code;int n=4*(*(c+1));
  if(6+n>=OUTBUF_SIZE){outputFault();return;}
  if(!hasOutputSpace(6+n))return;
  sendCodeChunk(bulkIndex,chunks[bulkIndex].chunkType,n,(char*)(c+2));bulkIndex++;
 } else if(bulkKind==3) {
  while(bulkVar && ((*bulkVar>>16)&255)!=varName)bulkVar=recordAfter(bulkVar);
  if(!bulkVar){bulkKind=0;return;}
  int n=strlen((char*)(bulkVar+2));if(!hasOutputSpace(5+n))return;
  sendVarNameMessage((*bulkVar>>8)&255,bulkVar);bulkVar=recordAfter(bulkVar);
 }
 sendData();
}

'''+s[pos:]
 s=s.replace('uint32 lastRcvTime = 0;','uint32 lastRcvTime = 0;\nstatic uint32 lastByteTime;')
 s=replace_function(s,'receiveTimeout','''static int receiveTimeout() { return (uint32)(microsecs()-lastByteTime)>250000; }''')
 # Drop only a timed-out partial head, before accepting fresh bytes. Never discard complete queued frames.
 pos=s.index('void captureIncomingBytes()')
 s=s[:pos]+'''static void expirePartialHead(void) {
 if(!rcvByteCount || !receiveTimeout())return;
 int partial=0;
 if(rcvBuf[0]==250)partial=rcvByteCount<3;
 if(rcvBuf[0]==251)partial=rcvByteCount<5 || (rcvByteCount>=5 && rcvByteCount<5+((rcvBuf[4]<<8)|rcvBuf[3]));
 if(partial){rcvByteCount=0;++unoRxTimeouts;}
}
void unoRuntimeResetTransport(void) {
 outBufStart=outBufEnd=0;rcvByteCount=0;lastByteTime=lastRcvTime=0;
 bulkKind=bulkIndex=0;bulkVar=NULL;unoOutputFaulted=0;
}
'''+s[pos:]
 s=s.replace('int bytesRead = recvBytes(&rcvBuf[rcvByteCount], RCVBUF_SIZE - rcvByteCount);','expirePartialHead();\n\tint bytesRead = recvBytes(&rcvBuf[rcvByteCount], RCVBUF_SIZE - rcvByteCount);\n\tif(bytesRead>0)lastByteTime=lastRcvTime=microsecs();')
 s=s.replace('\tlastRcvTime = microsecs();\n\tint firstByte', '\tint firstByte')
 s=s.replace('\tsendData();\n\n\tint bytesRead', '\tsendData();\n\n\tint bytesRead') # retained for exact upstream layout
 s=s.replace('''\tsendData();

\texpirePartialHead();''','''\tsendData();
 if(unoOutputFaulted)return;
 if(bulkKind){bulkTick();return;}

\texpirePartialHead();''',1)
 # Avoid zero-length indexing and reject malformed short bodies before any operation.
 s=s.replace('if ((rcvByteCount >= 5) && (msgLength > MAX_MSG_SIZE))','if ((rcvByteCount >= 5) && (msgLength < 1 || msgLength > MAX_MSG_SIZE))')
 s=s.replace('''\tcase chunkCode16Msg: // code chunk from 16-bit IDE
''','''\tcase chunkCode16Msg: // code chunk from 16-bit IDE
  if(bodyBytes<3 || (bodyBytes&1)==0)break;
''')
 return s
