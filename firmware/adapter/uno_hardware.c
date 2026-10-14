// SPDX-License-Identifier: MPL-2.0
// Uses SmallVM's existing named-primitive extension mechanism. No VM changes.
#include "vm/interp.h"
#include "uno_hardware.h"
#include <string.h>
static uint8_t framebuffer[104], rgb[12];
static struct { uint32_t sequence; uint8_t led,r,g,b; } actions[8];
static unsigned head, count;
static uint32_t nextSequence, acknowledgements, failedActions, rgbWrites, matrixShows;
static int range(OBJ o,int low,int high) {return isInt(o) && obj2int(o)>=low && obj2int(o)<=high;}
static int enqueue(unsigned led,unsigned r,unsigned g,unsigned b) {
 if(count==8)return 0;
 unsigned i=(head+count)%8;
 if(nextSequence==0x7fffffff)nextSequence=0;actions[i].sequence=++nextSequence;actions[i].led=led;actions[i].r=r;actions[i].g=g;actions[i].b=b;
 ++count;return 1;
}
unsigned unoHostPeek(uint8_t *out) {
 if(!count)return 0;
 uint32_t s=actions[head].sequence;
 for(unsigned i=0;i<4;++i)out[i]=(uint8_t)(s>>(8*i));
 out[4]=actions[head].led;out[5]=actions[head].r;out[6]=actions[head].g;out[7]=actions[head].b;return 8;
}
int unoHostAck(uint32_t s,int success) {
 if(!count || actions[head].sequence!=s || (success!=0 && success!=1))return 0;
 if(success)++acknowledgements;else ++failedActions;
 head=(head+1)%8;--count;return 1;
}
int unoHardwareStat(int index) {
 switch(index){case 0:return count;case 1:return acknowledgements;case 2:return failedActions;case 3:return rgbWrites;case 4:return matrixShows;case 5:return sizeof(actions)+sizeof(framebuffer)+sizeof(rgb);default:return -1;}
}
unsigned unoHardwareState(uint8_t *out){memcpy(out,rgb,12);return 12;}
unsigned unoMatrixState(uint8_t *out){memcpy(out,framebuffer,104);return 104;}
void unoHardwareOff(void){
 for(unsigned led=3;led<=4;++led){unoLedWrite(led,0,0,0);memset(rgb+(led-1)*3,0,3);}
 memset(framebuffer,0,sizeof(framebuffer));unoMatrixWrite(framebuffer);
}
static OBJ setRGB(int n,OBJ *a) {
 if(n!=4)return fail(notEnoughArguments);
 for(int i=0;i<4;++i)if(!isInt(a[i]))return fail(needsIntegerError);
 if(!range(a[0],1,4)||!range(a[1],0,255)||!range(a[2],0,255)||!range(a[3],0,255))return fail(indexOutOfRangeError);
 unsigned led=obj2int(a[0]),r=obj2int(a[1]),g=obj2int(a[2]),b=obj2int(a[3]);
 if(led<3){if(!enqueue(led,r,g,b))return fail(insufficientMemoryError);}
 else unoLedWrite(led,r,g,b);
 rgb[(led-1)*3]=r;rgb[(led-1)*3+1]=g;rgb[(led-1)*3+2]=b;++rgbWrites;return falseObj;
}
static OBJ clearMatrix(int n,OBJ *a){(void)n;(void)a;memset(framebuffer,0,104);unoMatrixWrite(framebuffer);++matrixShows;return falseObj;}
static OBJ showMatrix(int n,OBJ *a){(void)n;(void)a;unoMatrixWrite(framebuffer);++matrixShows;return falseObj;}
static OBJ fillMatrix(int n,OBJ *a){
 if(n!=1)return fail(notEnoughArguments);
 if(!isInt(a[0]))return fail(needsIntegerError);
 if(!range(a[0],0,7))return fail(indexOutOfRangeError);
 memset(framebuffer,obj2int(a[0]),104);return falseObj;
}
static OBJ pixel(int n,OBJ *a){
 if(n!=3)return fail(notEnoughArguments);
 for(int i=0;i<3;++i)if(!isInt(a[i]))return fail(needsIntegerError);
 if(!range(a[0],0,12)||!range(a[1],0,7)||!range(a[2],0,7))return fail(indexOutOfRangeError);
 framebuffer[obj2int(a[1])*13+obj2int(a[0])]=obj2int(a[2]);return falseObj;
}
static OBJ pattern(int n,OBJ *a){
 if(n!=1)return fail(notEnoughArguments);
 if(!IS_TYPE(a[0],StringType))return fail(needsStringError);
 const char *p=obj2str(a[0]);
 if(strlen(p)!=104)return fail(indexOutOfRangeError);
 for(unsigned i=0;i<104;++i)if(p[i]<'0'||p[i]>'7')return fail(indexOutOfRangeError);
 for(unsigned i=0;i<104;++i)framebuffer[i]=p[i]-'0';return falseObj;
}
static PrimEntry entries[]={
 {"setRGB",setRGB},{"matrixClear",clearMatrix},{"matrixPixel",pixel},
 {"matrixShow",showMatrix},{"matrixFill",fillMatrix},{"matrixPattern",pattern}
};
// IOPrims was deliberately empty in the existing minimal port. Enum/ABI retained.
void addIOPrims(void){addPrimitiveSet(IOPrims,"unoq",sizeof(entries)/sizeof(entries[0]),entries);}
