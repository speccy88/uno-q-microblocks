# UNO Q hardware blocks

`examples/UNO_Q_Hardware.ubl` is a standard MicroBlocks library.
`UNO_Q_Hardware.ubp` is its editable project. They are embedded in the pinned
editor build and are automatically imported using the upstream library mechanism.

| Block | Semantics |
|---|---|
| set LED 1–4 red/green/blue | Integers 0..255; 0 off, every nonzero value ON. No proportional RGB PWM is claimed. |
| turn LED off / all RGB off | Same MCU primitives; Linux requests are asynchronous and bounded. |
| matrix clear | Clear framebuffer and immediately display blank. |
| matrix set pixel | x 0..12, y 0..7, brightness 0..7; modifies framebuffer only. |
| matrix fill | Set every framebuffer byte to brightness 0..7; call show. |
| matrix draw pattern | Exactly 104 characters, each `0` through `7`, row-major y*13+x; call show. |
| matrix show | Commit the complete framebuffer through Arduino_LED_Matrix.draw. |

Linux LED1/2 use existing user/gpiod permissions and device aliases, with modern
and legacy sysfs name discovery. All six installed channels had max_brightness=1.
The original trigger/brightness snapshot is restored on App stop; LED2 WLAN and
Bluetooth status triggers were physically checked after stopping the App.

LED3/4 use official LED3_R/G/B and LED4_R/G/B macros. HIGH is OFF, LOW is ON.
Physical digitalRead observations independently verified these six pin states.
The matrix initializes once and uses the installed core's exported begin,
3-bit grayscale and framebuffer APIs. Bounds/type checks happen before updates.
Pixel ordering is logical row-major. The owner visually recognized the heart
and checkerboard on the physical matrix; exact orientation was not confirmed.
Matrix brightness API compatibility is established, but optical grayscale
linearity was not measured.
