#include <SPI.h>
#include <Arduino_RouterBridge.h>
#include <stm32u5xx_ll_rcc.h>
#if SPI_MIN_CLOCK_FREQUENCY != 100000
#error Supply compiler.cpp.extra_flags=-DSPI_MIN_CLOCK_FREQUENCY=100000
#endif
static_assert(DT_SAME_NODE(DT_PHANDLE_BY_IDX(DT_PATH(zephyr_user), spis, 0),
                          DT_NODELABEL(spi2)), "UNO Q SPI must use SPI2");
constexpr uint8_t CS_PIN=10;
constexpr uint32_t SPI_HZ=100000;
class CheckedSPI: public arduino::ZephyrSPI {
public:
 uint32_t errors=0;
 explicit CheckedSPI(const device* dev):arduino::ZephyrSPI(dev){}
 void beginTransaction(SPISettings settings) override {
  arduino::ZephyrSPI::beginTransaction(settings);
  // The installed core reports the boot APB1 rate. Match the temporary /16
  // clock scope used by the proven Phase 2 driver (physical divider /128).
  config.frequency*=16;config16.frequency*=16;
 }
 void transfer(void* data,size_t length) override {
  spi_buf tx={data,length},rx={data,length};
  spi_buf_set txSet={&tx,1},rxSet={&rx,1};
  if(spi_transceive(spi_dev,&config,&txSet,&rxSet))++errors;
 }
};
CheckedSPI FpgaSPI(DEVICE_DT_GET(DT_NODELABEL(spi2)));
class SpiClockScope {
 uint32_t saved=LL_RCC_GetAPB1Prescaler();
public:
 bool compatible()const{return saved==LL_RCC_APB1_DIV_1;}
 SpiClockScope(){if(compatible()){LL_RCC_SetAPB1Prescaler(LL_RCC_APB1_DIV_16);__DSB();}}
 ~SpiClockScope(){LL_RCC_SetAPB1Prescaler(saved);__DSB();}
};
uint8_t registerFrame(uint8_t operation,uint8_t address,uint8_t data=0){
 uint8_t frame[3]={operation,address,data};
 FpgaSPI.beginTransaction(SPISettings(SPI_HZ,MSBFIRST,SPI_MODE0));
 digitalWrite(CS_PIN,LOW);delayMicroseconds(10);
 FpgaSPI.transfer(frame,sizeof(frame));delayMicroseconds(10);
 digitalWrite(CS_PIN,HIGH);FpgaSPI.endTransaction();delayMicroseconds(10);
 return frame[2];
}
uint8_t rd(uint8_t address){return registerFrame(3,address);}
void wr(uint8_t address,uint8_t value){registerFrame(2,address,value);}
// One command commit, followed by independent response transactions.
// All semantic replies originate in PacoBlaze INPUT/OUTPUT instructions.
int32_t cpuRequest(uint8_t command,uint8_t argument){
 SpiClockScope clock;
 if(!clock.compatible())return -10;
 uint32_t initialErrors=FpgaSPI.errors;
 uint32_t start=millis();
 while(rd(0x13)&1){if(millis()-start>20)return -12;}
 uint8_t before=rd(0x16),tag=uint8_t(rd(0x12)+1);
 wr(0x10,command);wr(0x11,argument);wr(0x12,tag);
 start=millis();uint8_t status;
 do {status=rd(0x13);if(millis()-start>20)return -13;}while((status&3)!=2);
 if(status&4)return -16;
 if(rd(0x15)!=tag)return -14;
 uint8_t response=rd(0x14);
 if(rd(0x16)!=uint8_t(before+1))return -15;
 if(FpgaSPI.errors!=initialErrors)return -11;
 return response;
}
int32_t pb_echo(int32_t number){return number;}
int32_t pb_ping(){return cpuRequest(1,0);}
int32_t pb_set_led(int32_t mask){if(mask<0||mask>15)return -20;return cpuRequest(2,uint8_t(mask));}
int32_t pb_get_led(){return cpuRequest(3,0);}
int32_t pb_info(){SpiClockScope clock;if(!clock.compatible())return -10;return (int32_t(rd(0))<<16)|(int32_t(rd(1))<<8)|rd(0x18);}
int32_t pb_completed(){SpiClockScope clock;if(!clock.compatible())return -10;return rd(0x16);}
int32_t pb_led_register(){SpiClockScope clock;if(!clock.compatible())return -10;return rd(5);}
int32_t pb_errors(){return FpgaSPI.errors;}
int32_t pb_apb1(){return LL_RCC_GetAPB1Prescaler();}
// Phase 3: bounded programming operations, never arbitrary register access.
uint32_t uploadSessions=0;
int32_t pb_status(){SpiClockScope c;if(!c.compatible())return -10;return rd(0x25);}
int32_t pb_program_error(){SpiClockScope c;if(!c.compatible())return -10;return rd(0x26);}
int32_t pb_epoch(){SpiClockScope c;if(!c.compatible())return -10;return rd(0x2a);}
int32_t pb_sessions(){return uploadSessions;}
int32_t pb_uptime(){return millis()&0x7fffffff;}
int32_t pb_halt(){
 SpiClockScope c;if(!c.compatible())return -10;
 uint32_t before=FpgaSPI.errors;wr(0x20,1);
 if(FpgaSPI.errors!=before)return -11;
 if(rd(0x25)!=1)return -30;
 ++uploadSessions;return 1;
}
int32_t pb_write_instruction(int32_t address,int32_t word){
 if(address<0||address>=32)return -21;
 if(word<0||word>0x3ffff)return -22;
 SpiClockScope c;if(!c.compatible())return -10;
 uint32_t before=FpgaSPI.errors;
 if(!(rd(0x25)&1))return -30;
 if(rd(0x26)!=0)return -31;
 wr(0x21,uint8_t(address));wr(0x22,uint8_t(word));
 wr(0x23,uint8_t(word>>8));wr(0x24,uint8_t(word>>16));wr(0x20,3);
 if(FpgaSPI.errors!=before)return -11;
 return rd(0x26)==0 ? 0 : -31;
}
int32_t pb_read_instruction(int32_t address){
 if(address<0||address>=32)return -21;
 SpiClockScope c;if(!c.compatible())return -10;
 uint32_t before=FpgaSPI.errors;
 if(!(rd(0x25)&1))return -30;
 if(rd(0x26)!=0)return -31;
 wr(0x21,uint8_t(address));wr(0x20,4);
 uint32_t start=millis();uint8_t status;
 do {status=rd(0x25);if(millis()-start>20)return -32;}while(!(status&4));
 int32_t word=rd(0x27)|(int32_t(rd(0x28))<<8)|(int32_t(rd(0x29))<<16);
 if(FpgaSPI.errors!=before)return -11;
 if(rd(0x26)!=0)return -31;
 return word;
}
int32_t pb_run(){
 SpiClockScope c;if(!c.compatible())return -10;
 uint32_t before=FpgaSPI.errors;uint8_t status=rd(0x25);
 // Full writes + full readback are independently enforced in the FPGA too.
 if((status&0x1b)!=0x19)return -33;
 wr(0x20,2);
 if(FpgaSPI.errors!=before)return -11;
 return (rd(0x25)&3)==0 ? 0 : -34;
}
void setup(){
 FpgaSPI.begin();
 // SPI.begin() includes PB9 NSS pinctrl: restore D10 to GPIO afterward.
 pinMode(CS_PIN,OUTPUT);digitalWrite(CS_PIN,HIGH);
 Bridge.begin();Monitor.begin();
 Bridge.provide_safe("pb_halt",pb_halt);
 Bridge.provide_safe("pb_write_instruction",pb_write_instruction);
 Bridge.provide_safe("pb_read_instruction",pb_read_instruction);
 Bridge.provide_safe("pb_run",pb_run);
 Bridge.provide_safe("pb_status",pb_status);
 Bridge.provide_safe("pb_program_error",pb_program_error);
 Bridge.provide_safe("pb_epoch",pb_epoch);
 Bridge.provide_safe("pb_sessions",pb_sessions);
 Bridge.provide_safe("pb_uptime",pb_uptime);
 Bridge.provide_safe("pb_echo",pb_echo);
 Bridge.provide_safe("pb_ping",pb_ping);
 Bridge.provide_safe("pb_set_led",pb_set_led);
 Bridge.provide_safe("pb_get_led",pb_get_led);
 Bridge.provide_safe("pb_info",pb_info);
 Bridge.provide_safe("pb_completed",pb_completed);
 Bridge.provide_safe("pb_led_register",pb_led_register);
 Bridge.provide_safe("pb_errors",pb_errors);
 Bridge.provide_safe("pb_apb1",pb_apb1);
}
void loop(){delay(1);}
