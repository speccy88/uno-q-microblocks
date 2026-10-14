#include <Arduino.h>
#include <Arduino_RouterBridge.h>
#include "src/vm/interp.h"
#include "src/vm/persist.h"
#include <vector>
#include "src/uno_hardware.h"
int mbHardwareVersion(){return 1;}
int mbHostAck(int sequence,int success){return sequence>0?unoHostAck((uint32_t)sequence,success):0;}
std::vector<uint8_t> mbGPIO(){uint8_t b[6];unsigned n=unoGPIOState(b);return std::vector<uint8_t>(b,b+n);}
int mbUptime(){return millis();}
std::vector<uint8_t> mbHostPeek(){uint8_t b[8];unsigned n=unoHostPeek(b);return std::vector<uint8_t>(b,b+n);}
std::vector<uint8_t> mbHardwareState(){uint8_t b[12];unsigned n=unoHardwareState(b);return std::vector<uint8_t>(b,b+n);}
std::vector<uint8_t> mbMatrixState(){uint8_t b[104];unsigned n=unoMatrixState(b);return std::vector<uint8_t>(b,b+n);}
unsigned inputBytes(const uint8_t*,unsigned);
unsigned outputBytes(uint8_t*,unsigned);
// Native binary ingress/egress, bounded below RPClite's 256-byte request capacity.
extern "C" uint32 unoRxTimeouts,unoTxFaults;
extern "C" int unoOutputFaulted;
unsigned queuedRx(),queuedTx();void resetTransport();
int mbPush(std::vector<uint8_t> data){if(unoOutputFaulted)return -2;if(data.size()>192)return -1;return inputBytes(data.data(),data.size());}
std::vector<uint8_t> mbPull(){uint8_t b[192];auto n=outputBytes(b,192);return std::vector<uint8_t>(b,b+n);}
std::vector<uint8_t> mbEcho(std::vector<uint8_t> data){if(data.size()>192)return {};return data;}
int mbOpen(){resetTransport();return 1;}
uint32_t slices,maxSliceTime;
int mbStat(int index){switch(index){
 case 0:return slices;case 1:return maxSliceTime;case 2:return queuedRx();case 3:return queuedTx();
 case 4:return unoRxTimeouts;case 5:return unoTxFaults;case 6:return unoOutputFaulted;case 7:return taskCount;
 case 8:return -95; // installed INIT_STACKS is off; no exported check-link symbol
 case 9:return wordsFree()*4;
 default:return -1;}}
int mbVar(int index){if(index<0||index>=MAX_VARS)return -1;return isInt(vars[index])?obj2int(vars[index]):-2;}
volatile uint32_t mb_sizes[] = {sizeof(OBJ),sizeof(Task),sizeof(tasks),sizeof(chunks),sizeof(vars),sizeof(struct k_thread),sizeof(struct k_mutex),sizeof(RPCClient),sizeof(RPCServer),sizeof(RPCRequest<BRIDGE_RPC_BUFFER_SIZE>),sizeof(BridgeClass),sizeof(std::vector<uint8_t>)};
int mbSize(int i){return (i>=0 && i<12)?mb_sizes[i]:-1;}
void initTransport();
#ifdef MB_THREAD
K_THREAD_STACK_DEFINE(vm_stack,8192);
static struct k_thread vm_thread;
static void vmWorker(void*,void*,void*) {for(;;){vmSlice(1);k_msleep(1);}}
#endif
void setup(){initTransport();memInit();primsInit();hardwareInit();restoreScripts();Bridge.begin();Bridge.provide_safe("mb_push",mbPush);Bridge.provide_safe("mb_pull",mbPull);Bridge.provide_safe("mb_size",mbSize);Bridge.provide_safe("mb_open",mbOpen);Bridge.provide_safe("mb_echo",mbEcho);Bridge.provide_safe("mb_stat",mbStat);Bridge.provide_safe("mb_var",mbVar);Bridge.provide_safe("mb_hw_version",mbHardwareVersion);Bridge.provide_safe("mb_uptime",mbUptime);Bridge.provide_safe("mb_host_peek",mbHostPeek);Bridge.provide_safe("mb_host_ack",mbHostAck);Bridge.provide_safe("mb_hw_stat",unoHardwareStat);Bridge.provide_safe("mb_hw_state",mbHardwareState);Bridge.provide_safe("mb_matrix",mbMatrixState);Bridge.provide_safe("mb_gpio",mbGPIO);
#ifdef MB_THREAD
 k_thread_create(&vm_thread,vm_stack,K_THREAD_STACK_SIZEOF(vm_stack),vmWorker,nullptr,nullptr,nullptr,6,0,K_NO_WAIT);
#endif
}
void loop(){
#ifndef MB_THREAD
 uint32_t before=micros();processMessage();vmSlice(1);uint32_t used=micros()-before;if(used>maxSliceTime)maxSliceTime=used;++slices;
#endif
 delay(1);
}
