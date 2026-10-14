#include "vm/interp.h"
#include "vm/persist.h"
#include <stdio.h>
#include <assert.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include "uno_hardware.h"
static uint8_t observedRGB[6],observedFrame[104];
void unoHardwareInit(void){}
void unoLedWrite(unsigned led,unsigned r,unsigned g,unsigned b){assert(led>=3 && led<=4);unsigned i=(led-3)*3;observedRGB[i]=r>0;observedRGB[i+1]=g>0;observedRGB[i+2]=b>0;}
void unoMatrixWrite(const uint8_t *p){memcpy(observedFrame,p,104);}
static uint8 rx[2048],tx[16384];static int rn,tn,blocked;
uint32 microsecs(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return (uint32)((uint64)t.tv_sec*1000000+t.tv_nsec/1000);}
uint32 millisecs(void){return microsecs()/1000;}
uint64 totalMicrosecs(void){return microsecs();}
uint32 seconds(void){return millisecs()/1000;}
void handleMicosecondClockWrap(void){}
void unoDelay(unsigned long n){(void)n;}
void lightSleep(int n){(void)n;}
void deepSleep(int n){(void)n;}
int recvBytes(uint8*p,int n){int k=n<rn?n:rn;memcpy(p,rx,k);memmove(rx,rx+k,rn-k);rn-=k;return k;}
int sendBytes(uint8*p,int a,int b){if(blocked)return 0;assert(tn+b-a<=sizeof tx);memcpy(tx+tn,p+a,b-a);tn+=b-a;return b-a;}

static void inject(const uint8 *p,int n) {assert(rn+n<=sizeof rx);memcpy(rx+rn,p,n);rn+=n;}
static void pump(int n) {for(int i=0;i<n;i++)vmSlice(1);}
static void code(int id,const uint16 *ops,int words) {
 uint8 p[1024]={251,32,(uint8)id,0,0,1};int length=2+2*words;
 p[3]=length&255;p[4]=length>>8;memcpy(p+6,ops,2*words);p[6+2*words]=254;
 inject(p,7+2*words);pump(100);assert(chunks[id].code);tn=0;
}
static int pingSeen(int id) {for(int i=0;i+2<tn;i++)if(tx[i]==250&&tx[i+1]==26&&tx[i+2]==id)return 1;return 0;}
extern uint32 unoRxTimeouts,unoTxFaults;
extern int unoOutputFaulted;
void unoRuntimeResetTransport(void);
void unoTransportFault(void){rn=tn=0;}
int main(int argc,char **argv){memInit();primsInit();hardwareInit();restoreScripts();pump(100);tn=0;
 if(argc>1 && !strcmp(argv[1],"hardware")){
  OBJ args[]={int2obj(3),int2obj(255),zeroObj,zeroObj};
  doPrimitiveCall(IOPrims,"setRGB",4,args);assert(!failure() && observedRGB[0]==1 && observedRGB[1]==0);
  args[0]=int2obj(1);for(int i=0;i<8;++i){doPrimitiveCall(IOPrims,"setRGB",4,args);assert(!failure());}
  uint8_t record[8];assert(unoHostPeek(record)==8 && record[4]==1 && record[5]==255);
  uint32_t sequence=record[0]|record[1]<<8|record[2]<<16|record[3]<<24;
  assert(!unoHostAck(sequence+1,1));assert(!unoHostAck(sequence,2));assert(unoHardwareStat(0)==8);
  doPrimitiveCall(IOPrims,"setRGB",4,args);assert(failure());fail(0);
  assert(unoHostAck(sequence,1));assert(!unoHostAck(sequence,1));
  while(unoHostPeek(record)){sequence=record[0]|record[1]<<8|record[2]<<16|record[3]<<24;assert(unoHostAck(sequence,0));}
  assert(unoHardwareStat(1)==1 && unoHardwareStat(2)==7);
  args[0]=int2obj(5);doPrimitiveCall(IOPrims,"setRGB",4,args);assert(failure());fail(0);
  args[0]=int2obj(3);args[1]=int2obj(256);doPrimitiveCall(IOPrims,"setRGB",4,args);assert(failure());fail(0);
  OBJ coords[]={int2obj(12),int2obj(7),int2obj(7)};doPrimitiveCall(IOPrims,"matrixPixel",3,coords);assert(!failure() && observedFrame[103]==0);
  doPrimitiveCall(IOPrims,"matrixShow",0,NULL);assert(observedFrame[103]==7);
  coords[0]=int2obj(13);doPrimitiveCall(IOPrims,"matrixPixel",3,coords);assert(failure());fail(0);
  coords[0]=int2obj(12);coords[2]=int2obj(8);doPrimitiveCall(IOPrims,"matrixPixel",3,coords);assert(failure());fail(0);
  OBJ bad=newStringFromBytes("bad",3);doPrimitiveCall(IOPrims,"matrixPattern",1,&bad);assert(failure());fail(0);
  char pattern[104];memset(pattern,'7',104);OBJ good=newStringFromBytes(pattern,104);doPrimitiveCall(IOPrims,"matrixPattern",1,&good);assert(!failure());
  doPrimitiveCall(IOPrims,"matrixShow",0,NULL);for(int i=0;i<104;++i)assert(observedFrame[i]==7);
  unoHardwareOff();for(int i=0;i<104;++i)assert(!observedFrame[i]);assert(!unoHostPeek(record));
  puts("{\"result\":\"PASS\",\"scope\":\"real named primitives; simulated GPIO/matrix backend\"}");return 0;
 }
 if(argc>1 && !strcmp(argv[1],"ide-reset")){
  // Exact IDE 2.0.126-generated reporter bytes captured from the physical port.
  const uint8 reporter[]={251,32,0,22,0,2,9,0,2,11,2,15,50,2,35,0,127,0,240,0,0,0,0,0,0,0,254};
  for(int repeat=0;repeat<10;repeat++){
   const uint8 reset[]={250,14,1,250,15,0};inject(reset,sizeof reset);pump(100);
   assert(!failure());tn=0;inject(reporter,sizeof reporter);pump(100);
   const uint8 start[]={250,3,0};inject(start,sizeof start);pump(10000);
   const uint8 result[]={251,18,0,5,0,1,12,0,0,0};int found=0;
   for(int i=0;i+sizeof result<=tn;i++)if(!memcmp(tx+i,result,sizeof result))found=1;
   if(!found || failure()){fprintf(stderr,"reporter output: ");for(int j=0;j<tn;j++)fprintf(stderr,"%02x",tx[j]);fprintf(stderr," error=%d\n",failure());}
   assert(found && !failure());tn=0;
  }
  puts("{\"result\":\"PASS\",\"finding\":\"10 IDE reset/delete-all followed by exact captured reporter returns 12\"}");return 0;
 }
 if(argc>1 && !strcmp(argv[1],"truncation")){uint8 part[]={251,32,7,100,0,1};inject(part,6);pump(100);usleep(300000);uint8 ping[]={250,26,99};inject(ping,3);pump(1000);assert(pingSeen(99));assert(unoRxTimeouts==1);puts("{\"result\":\"PASS\",\"finding\":\"partial frame expires and next PING succeeds\"}");return 0;}
 if(argc>1 && !strcmp(argv[1],"backpressure")){blocked=1;char data[800]={0};uint32 t=microsecs();for(int i=0;i<20;i++)waitAndSendMessage(20,1,800,data);assert(unoOutputFaulted && unoTxFaults==1);assert(microsecs()-t<100000);blocked=0;unoRuntimeResetTransport();uint8 ping[]={250,26,99};inject(ping,3);pump(1000);assert(pingSeen(99));puts("{\"result\":\"PASS\",\"finding\":\"no consumer: bounded explicit session fault, reset and PING recovery\"}");return 0;}
 if(argc>1 && !strcmp(argv[1],"fragmented")){uint16 ops[506]={0};for(int i=0;i<500;i++)ops[i]=OP(21,0);ops[500]=OP(2,85);ops[501]=OP(7,2);uint8 packet[1019]={251,32,2,246,3,1};memcpy(packet+6,ops,1012);packet[1018]=254;
  for(int pos=0;pos<1019;pos+=192){int n=1019-pos;if(n>192)n=192;inject(packet+pos,n);pump(100);usleep(30000);}pump(100);assert(chunks[2].code && unoRxTimeouts==0);startTaskForChunk(2);pump(3);assert(obj2int(vars[2])==42);puts("{\"result\":\"PASS\",\"finding\":\"maximum message at 30 ms inter-RPC gaps executes exactly\"}");return 0;}
 if(argc>1 && !strcmp(argv[1],"bulk")){uint16 ops[400]={0};for(int i=0;i<398;i++)ops[i]=OP(21,0);for(int id=0;id<6;id++)code(id,ops,400);
  uint8 request[]={250,13,1};inject(request,3);blocked=1;pump(10000);assert(!unoOutputFaulted);blocked=0;tn=0;pump(20000);
  int count=0;for(int pos=0;pos<tn;){if(tx[pos]==250){pos+=3;continue;}assert(tx[pos]==251 && pos+5<=tn);int n=tx[pos+3]|(tx[pos+4]<<8);assert(pos+5+n<=tn);if(tx[pos+1]==32){assert(n==801);assert(!memcmp(tx+pos+6,ops,800));count++;}pos+=5+n;}
  assert(count==6);puts("{\"result\":\"PASS\",\"finding\":\"six code replies, stalled consumer then byte-exact resume\"}");return 0;}
 printf("{\"kind\":\"Actual SmallVM wasm32 interpreter on Mac, simulated services\",\"sizeof\":{\"OBJ\":%u,\"Task\":%u,\"tasks\":%u,\"chunks\":%u,\"vars\":%u},",(unsigned)sizeof(OBJ),(unsigned)sizeof(Task),(unsigned)sizeof(tasks),(unsigned)sizeof(chunks),(unsigned)sizeof(vars));
 uint8 p[]={250,26,73};inject(p,3);pump(100);assert(pingSeen(73));tn=0;
 const uint16 arithmetic[]={OP(2,11),OP(2,15),OP(50,2),OP(7,0),0};
 code(0,arithmetic,5);startTaskForChunk(0);pump(10);assert(obj2int(vars[0])==12);assert(!taskCount);tn=0;
 uint16 straight[506]={0};for(int i=0;i<500;i++)straight[i]=OP(21,0);straight[500]=OP(2,85);straight[501]=OP(7,2);straight[502]=0;straight[503]=0;
 code(2,straight,506);startTaskForChunk(2);pump(1);assert(taskCount==1);pump(2);assert(obj2int(vars[2])==42);tn=0;
 const uint16 timed[]={OP(2,21),OP(33,1),OP(2,19),OP(7,3),0};code(3,timed,5);startTaskForChunk(3);pump(1);assert(tasks[0].status==waiting_micros);usleep(15000);pump(2);assert(obj2int(vars[3])==9);tn=0;
 vars[1]=zeroObj;const uint16 busy[]={OP(2,3),OP(8,1),OP(22,-3),0};code(1,busy,4);startTaskForChunk(1);tn=0;
 uint32 maxSlice=0,maxPingLatency=0;int router=0,fpga=0,pings=0,maxQueue=0;uint32 began=microsecs();
 for(int i=0;i<300000;i++) {
  uint32 started=microsecs();vmSlice(1);uint32 elapsed=microsecs()-started;if(elapsed>maxSlice)maxSlice=elapsed;
  // Simulated loop hook services, no hardware accesses.
  router++;if(i%17==0)fpga++;
  if(i%997==0){p[2]=(uint8)i;uint32 t=microsecs();inject(p,3);if(rn>maxQueue)maxQueue=rn;int count=0;while(!pingSeen(p[2])&&count++<200)vmSlice(1);assert(pingSeen(p[2]));elapsed=microsecs()-t;if(elapsed>maxPingLatency)maxPingLatency=elapsed;pings++;tn=0;}
  if(i%10000==0){for(int j=0;j<8;j++){p[2]=j;inject(p,3);}if(rn>maxQueue)maxQueue=rn;pump(1000);for(int j=0;j<8;j++)assert(pingSeen(j));tn=0;}
 }
 assert(obj2int(vars[1])>300000);assert(!failure());
 printf("\"max_IDE_message_bytes\":1019,\"timing_wait_ms\":10,\"arithmetic_variable_result\":12,\"straight_line_budget\":\"PASS\",\"busy_counter\":%d,\"slices\":300000,\"simulated_router_callbacks\":%d,\"simulated_fpga_requests\":%d,\"actual_vm_ping_replies\":%d,\"burst_ping_replies\":240,\"max_input_queue_bytes\":%d,\"max_slice_us\":%u,\"max_ping_us\":%u,\"elapsed_us\":%u,\"result\":\"PASS\"}\n",obj2int(vars[1]),router,fpga,pings,maxQueue,maxSlice,maxPingLatency,microsecs()-began);return 0;}
