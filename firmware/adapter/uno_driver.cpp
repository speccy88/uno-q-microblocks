// SPDX-License-Identifier: MPL-2.0
#include <Arduino.h>
#include <Arduino_LED_Matrix.h>
#include "uno_hardware.h"
static Arduino_LED_Matrix matrix;
static bool initialized;
static const pin_size_t channels[2][3]={{LED3_R,LED3_G,LED3_B},{LED4_R,LED4_G,LED4_B}};
extern "C" void unoHardwareInit(void){
 if(initialized)return;
 for(auto &led:channels)for(auto pin:led){pinMode(pin,OUTPUT);digitalWrite(pin,HIGH);}
 matrix.begin();matrix.setGrayscaleBits(3);matrix.clear();initialized=true;
}
extern "C" void unoLedWrite(unsigned led,unsigned r,unsigned g,unsigned b){
 if(led<3||led>4)return;
 unsigned values[]={r,g,b};for(unsigned i=0;i<3;++i)digitalWrite(channels[led-3][i],values[i]?LOW:HIGH);
}
extern "C" void unoMatrixWrite(const uint8_t *frame){if(initialized)matrix.draw((uint8_t*)frame);}

extern "C" unsigned unoGPIOState(uint8_t *out){for(unsigned l=0;l<2;++l)for(unsigned c=0;c<3;++c)out[l*3+c]=digitalRead(channels[l][c]);return 6;}
