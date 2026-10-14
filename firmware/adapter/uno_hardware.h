#pragma once
#include <stdint.h>
#ifdef __cplusplus
extern "C" {
#endif
void unoHardwareInit(void);
void unoHardwareOff(void);
void unoLedWrite(unsigned led, unsigned r, unsigned g, unsigned b);
void unoMatrixWrite(const uint8_t *frame);
unsigned unoHostPeek(uint8_t *out);
int unoHostAck(uint32_t sequence, int success);
int unoHardwareStat(int index);
unsigned unoHardwareState(uint8_t *out);
unsigned unoGPIOState(uint8_t *out);
unsigned unoMatrixState(uint8_t *out);
#ifdef __cplusplus
}
#endif
