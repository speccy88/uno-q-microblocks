// UNO Q SmallVM/SPI minimal platform. Hardware primitives intentionally disabled.
#include "vm/interp.h"
#include "vm/persist.h"
#include <string.h>
#include <stdlib.h>
#include "uno_hardware.h"
int useTFT, mbDisplayColor, resetDoubleTap, wifiActive, isCodingBox, isSpringbotGold;
int BLE_allowShutdown, BLE_connected_to_IDE, bleRunning;
char BLE_ThreeLetterID[4] = "---";
const char *boardType(void) { return "UNO Q SmallVM/SPI"; }
void hardwareInit(void) { initTasks(); unoHardwareInit(); }
void consolePrint(const char *s) {(void)s;}
void consoleReportNum(const char *s,int n) {(void)s;(void)n;}
void processFileMessage(int t,int n,char *p) {(void)t;(void)n;(void)p;}
void turnOffPins(void) { unoHardwareOff(); }
void stopPWM(void) {}
void stopServos(void) {}
void stopTone(void) {}
void resetRadio(void) {}
void turnOffInternalNeoPixels(void) {}
void tftClear(void) {}
void tftInit(void) {}
void updateMicrobitDisplay(void) {}
void restartSerial(void) {}
void BLE_start(void) {}
void BLE_stop(void) {}
void BLE_setEnabled(int n) {(void)n;}
int BLE_isEnabled(void) {return 0;}
int displayIsActive(void) {return 0;}
void getMACAddress(uint8 *p) {memset(p,0,6);}
OBJ primHexToInt(int n,OBJ *a) {return n ? int2obj(strtol(obj2str(a[0]),0,16)) : falseObj;}
#define DISABLED_A(name) OBJ name(OBJ *a) {(void)a;return fail(primitiveNotImplemented);}
#define DISABLED_N(name) OBJ name(int n,OBJ *a) {(void)n;(void)a;return fail(primitiveNotImplemented);}
#define DISABLED_V(name) void name(OBJ *a) {(void)a;fail(primitiveNotImplemented);}
DISABLED_A(primAnalogPins) DISABLED_A(primDigitalPins) DISABLED_A(primButtonA) DISABLED_A(primButtonB)
DISABLED_A(primI2cGet) DISABLED_A(primI2cSet) DISABLED_A(primSPISend) DISABLED_A(primSPIRecv)
DISABLED_N(primAnalogRead) DISABLED_N(primDigitalRead)
DISABLED_N(primMBDisplay) DISABLED_N(primMBEnableDisplay)
DISABLED_N(primMBPlot) DISABLED_N(primMBUnplot) DISABLED_N(primMBDrawShape) DISABLED_N(primMBShapeForLetter)
DISABLED_N(primMBTiltX) DISABLED_N(primMBTiltY) DISABLED_N(primMBTiltZ) DISABLED_N(primMBTemp)
DISABLED_V(primAnalogWrite) DISABLED_V(primDigitalWrite)
// IDE delete-all/soft-reset invokes these even when no display/VM LED exists.
// Cleanup must be harmless; requesting unsupported hardware remains an error.
OBJ primMBDisplayOff(int n,OBJ *a) {(void)n;(void)a;return falseObj;}
void primSetUserLED(OBJ *a) {if(a && a[0]!=falseObj)fail(primitiveNotImplemented);}
void primDigitalSet(int p,int f) {(void)p;(void)f;fail(primitiveNotImplemented);}
#define OMIT(name) void name(void) {}
OMIT(addDisplayPrims) OMIT(addFilePrims)  OMIT(addMiscPrims)
OMIT(addNetPrims) OMIT(addBLEPrims) OMIT(addRadioPrims) OMIT(addSensorPrims)
OMIT(addSerialPrims) OMIT(addTFTPrims) OMIT(addHIDPrims) OMIT(addOneWirePrims)
OMIT(addCameraPrims) OMIT(addEncoderPrims) OMIT(addSDCardPrims) OMIT(addElecfreaksPrims)
OMIT(addElecfreaksSensorPrims) OMIT(addSoundPrims)
