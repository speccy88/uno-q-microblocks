#include <Arduino.h>
#include "vm/interp.h"
#include <zephyr/kernel.h>
// Queue ownership: loop and provide_safe callbacks run on the sketch thread.
static uint8_t rx[2048], tx[2048];
static unsigned rn,tn;
static struct k_mutex queues;
void initTransport(){k_mutex_init(&queues);}
struct Guard { Guard(){k_mutex_lock(&queues,K_FOREVER);} ~Guard(){k_mutex_unlock(&queues);} };
extern "C" uint32 microsecs(void) {return micros();}
extern "C" uint32 millisecs(void) {return millis();}
extern "C" uint64 totalMicrosecs(void) {return k_ticks_to_us_floor64(k_uptime_ticks());}
extern "C" uint32 seconds(void) {return millis()/1000;}
extern "C" void handleMicosecondClockWrap(void) {}
extern "C" void lightSleep(int n) {delay(n);}
extern "C" void deepSleep(int n) {(void)n;}
extern "C" int recvBytes(uint8 *p,int n) {Guard lock;unsigned k=min((unsigned)n,rn);memcpy(p,rx,k);memmove(rx,rx+k,rn-k);rn-=k;return k;}
extern "C" int sendBytes(uint8 *p,int a,int b) {Guard lock;unsigned k=min((unsigned)(b-a),2048-tn);memcpy(tx+tn,p+a,k);tn+=k;return k;}
unsigned inputBytes(const uint8_t *p,unsigned n) {Guard lock;if(n>2048-rn)return 0;memcpy(rx+rn,p,n);rn+=n;return n;}
unsigned outputBytes(uint8_t *p,unsigned n) {Guard lock;n=min(n,tn);memcpy(p,tx,n);memmove(tx,tx+n,tn-n);tn-=n;return n;}

extern "C" void unoDelay(unsigned long n) {::delay(n);}

extern "C" void unoRuntimeResetTransport(void);
unsigned queuedRx(){return rn;}
unsigned queuedTx(){return tn;}
void resetTransport(){Guard lock;rn=tn=0;unoRuntimeResetTransport();}
extern "C" void unoTransportFault(void){Guard lock;rn=tn=0;}
