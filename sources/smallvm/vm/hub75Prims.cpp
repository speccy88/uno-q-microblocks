/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

// Copyright 2024 John Maloney, Bernat Romagosa, and Jens Mönig

// hub75Prims.cpp - MicroBlocks HUB75 LED Panels primitives
// José García, May 2025

#include <Arduino.h>
#include <stdio.h>
#include <stdlib.h>

#include "mem.h"
#include "interp.h"

#if defined(ESP32_S3_MATRIX_PORTAL)

#include <ESP32-HUB75-MatrixPanel-I2S-DMA.h>

#define PANEL_WIDTH 128
#define PANEL_HEIGHT 64
#define PANELS 1

static int h75initialized = false;
MatrixPanel_I2S_DMA *dma_display = nullptr;

#define UPDATE_DISPLAY() { taskSleep(-1); } // yield after potentially slow operations

static OBJ primh75Init(int argCount, OBJ *args) {

	if (!h75initialized) {
		HUB75_I2S_CFG mxconfig(PANEL_WIDTH, PANEL_HEIGHT, PANELS);

		mxconfig.gpio.r1 = 42;
		mxconfig.gpio.g1 = 41;
		mxconfig.gpio.b1 = 40;

		mxconfig.gpio.r2 = 38;
		mxconfig.gpio.g2 = 39;
		mxconfig.gpio.b2 = 37;

		mxconfig.gpio.a = 45;
		mxconfig.gpio.b = 36;
		mxconfig.gpio.c = 48;
		mxconfig.gpio.d = 35;
		mxconfig.gpio.e = 21;

		mxconfig.gpio.lat = 47;
		mxconfig.gpio.oe = 14;
		mxconfig.gpio.clk = 2;

		dma_display = new MatrixPanel_I2S_DMA(mxconfig);
		dma_display->begin();
		dma_display->setBrightness8(180); //0-255
		dma_display->clearScreen();

	};

	h75initialized = true;
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Clear(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	dma_display->clearScreen();
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75GetWidth(int argCount, OBJ *args) {
	if (h75initialized) {
		return int2obj(PANEL_WIDTH*PANELS);
	}
	return int2obj(0);
}

static OBJ primh75GetHeight(int argCount, OBJ *args) {
	if (h75initialized) {
		return int2obj(PANEL_HEIGHT);
	}
	return int2obj(0);
}

#define BUFFER_PIXELS_SIZE (PANEL_WIDTH * PANELS * 8)

uint16_t bufferPixelsH75[BUFFER_PIXELS_SIZE]; // used by primPixelRow and primDrawBuffer

static int color24to16b(int color24b) {
	// Convert 24-bit RGB888 format to the TFT's target pixel format.
	// Return RGB565 16-bit color.

	int r, g, b;

	r = (color24b >> 19) & 0x1F; // 5 bits
	g = (color24b >> 10) & 0x3F; // 6 bits
	b = (color24b >> 3) & 0x1F; // 5 bits

	return (r << 11) | (g << 5) | b; // color order: RGB
}

static OBJ primh75SetPixel(int argCount, OBJ *args) {
	if (h75initialized) {
		int x = obj2int(args[0]);
		int y = obj2int(args[1]);
		int color16b = color24to16b(obj2int(args[2]));

		dma_display->drawPixel(x, y, color16b);
		UPDATE_DISPLAY();
	}
	return falseObj;
}

static OBJ primh75PixelRow(int argCount, OBJ *args) {
	// Draw a single row of pixels (a list or byte array) at the given y.
	// If a byte array is provided the optional argument bytesPerPixel
	// determines the pixel size: 2, 3 or 4 bytes.
	// 2 means 16-bit RGB565 pixels; -2 means 16-bit RGB555 pixels.
	// 32 and 24 bit pixels are RGB(A) byte order. (Alpha of 32-bit pixels is ignored).
	// Used to accelerate BMP file display and other bitmap operations.

	if (!h75initialized) return falseObj;

	OBJ pixelDataObj = args[0];
	int x = obj2int(args[1]);
	if (x >= PANEL_WIDTH*PANELS) return falseObj;
	int y = obj2int(args[2]);
	if ((y < 0) || (y >= PANEL_HEIGHT)) return falseObj;
	int bytesPerPixel = ((argCount > 3) && isInt(args[3])) ? obj2int(args[3]) : 4;

	uint32 palette[256];
	if ((argCount > 4) && IS_TYPE(args[4], ListType)) {
		// paletteObj is a list of Integers representingRGB colors
		// palette is a C array of TFT display pixel values (e.g. 16-bit colors)
		OBJ paletteObj = args[4];
		int colorCount = obj2int(FIELD(paletteObj, 0)); // list size
		if (colorCount > 256) colorCount = 256;
		memset(palette, 0, sizeof(palette));
		for (int i = 0; i < colorCount; i++) {
			int rgb = obj2int(FIELD(paletteObj, i + 1));
			palette[i] = color24to16b(rgb & 0xFFFFFF);
		}
	}

	if (IS_TYPE(pixelDataObj, ListType)) {
		int pixelCount = obj2int(FIELD(pixelDataObj, 0));
		if (pixelCount > (PANEL_WIDTH*PANELS - x)) pixelCount = PANEL_WIDTH*PANELS - x;
		if (pixelCount > BUFFER_PIXELS_SIZE) pixelCount = BUFFER_PIXELS_SIZE;
		for (int i = 0; i < pixelCount; i++) {
			OBJ pixelObj = FIELD(pixelDataObj, (i + 1));
			bufferPixelsH75[i] = (isInt(pixelObj)) ? color24to16b(obj2int(pixelObj)) : 0;
		}
		dma_display->drawRGBBitmap(x, y, bufferPixelsH75, pixelCount, 1);
	} else if (IS_TYPE(pixelDataObj, ByteArrayType)) {
		int isRGB565 = true;
		if (bytesPerPixel < 0) {
			isRGB565 = false; // -2 means 16-bit RGB555 (vs. RGB565)
			bytesPerPixel = -bytesPerPixel;
		}
		if ((bytesPerPixel < 1) || (bytesPerPixel > 4)) return falseObj;

		int pixelCount = BYTES(pixelDataObj) / bytesPerPixel;
		if (pixelCount > (PANEL_WIDTH*PANELS - x)) pixelCount = PANEL_WIDTH*PANELS - x;
		if (pixelCount > BUFFER_PIXELS_SIZE) pixelCount = BUFFER_PIXELS_SIZE;
		uint8 *byte = (uint8 *) &FIELD(pixelDataObj, 0);
		if (1 == bytesPerPixel) {
			for (int i = 0; i < pixelCount; i++) {
				bufferPixelsH75[i] = palette[*byte++];
			}
		} else if (2 == bytesPerPixel) {
			for (int i = 0; i < pixelCount; i++) {
				int pixel = (byte[1] << 8) | byte[0];
				int r = isRGB565 ? ((pixel >> 8) & 248) : ((pixel >> 7) & 248);
				int g = isRGB565 ? ((pixel >> 3) & 252) : ((pixel >> 2) & 248);
				int b = (pixel << 3) & 248;
				bufferPixelsH75[i] = color24to16b((r << 16) | (g << 8) | b);
				byte += bytesPerPixel;
			}
		} else { // 24-bit or 32-bit pixels
			for (int i = 0; i < pixelCount; i++) {
				bufferPixelsH75[i] = color24to16b((byte[2] << 16) | (byte[1] << 8) | byte[0]);
				byte += bytesPerPixel;
			}
		}
		dma_display->drawRGBBitmap(x, y, bufferPixelsH75, pixelCount, 1);
	}
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Text(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	OBJ value = args[0];
	int x = obj2int(args[1]);
	int y = obj2int(args[2]);
	int color16b = color24to16b(obj2int(args[3]));
	int scale = (argCount > 4) ? obj2int(args[4]) : 2;
	int wrap = (argCount > 5) ? (trueObj == args[5]) : true;
	int bgColor = (argCount > 6) ? color24to16b(obj2int(args[6])) : -1;
	dma_display->setCursor(x, y);
	dma_display->setTextColor(color16b);
	dma_display->setTextSize(scale);
	dma_display->setTextWrap(wrap);

	int lineH = 8 * scale;
	int letterW = 6 * scale;
	if (IS_TYPE(value, StringType)) {
	char *str = obj2str(value);
	if (bgColor != -1) dma_display->fillRect(x, y, strlen(str) * letterW, lineH, bgColor);
		dma_display->print(obj2str(value));
	} else if (trueObj == value) {
		if (bgColor != -1) dma_display->fillRect(x, y, 4 * letterW, lineH, bgColor);
		dma_display->print("true");
	} else if (falseObj == value) {
		if (bgColor != -1) dma_display->fillRect(x, y, 5 * letterW, lineH, bgColor);
		dma_display->print("false");
	} else if (isInt(value)) {
		char s[50];
		sprintf(s, "%d", obj2int(value));
		if (bgColor != -1) dma_display->fillRect(x, y, strlen(s) * letterW, lineH, bgColor);
		dma_display->print(s);
	};
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Line(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	int x0 = obj2int(args[0]);
	int y0 = obj2int(args[1]);
	int x1 = obj2int(args[2]);
	int y1 = obj2int(args[3]);
	int color16b = color24to16b(obj2int(args[4]));
	dma_display->drawLine(x0, y0, x1, y1, color16b);
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Rect(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	int x = obj2int(args[0]);
	int y = obj2int(args[1]);
	int width = obj2int(args[2]);
	int height = obj2int(args[3]);
	int color16b = color24to16b(obj2int(args[4]));
	int fill = (argCount > 5) ? (trueObj == args[5]) : true;
	if (fill) {
		dma_display->fillRect(x, y, width, height, color16b);
	} else {
		dma_display->drawRect(x, y, width, height, color16b);
	}
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75RoundedRect(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	int x = obj2int(args[0]);
	int y = obj2int(args[1]);
	int width = obj2int(args[2]);
	int height = obj2int(args[3]);
	int radius = obj2int(args[4]);
	int color16b = color24to16b(obj2int(args[5]));
	int fill = (argCount > 6) ? (trueObj == args[6]) : true;
	if (fill) {
		dma_display->fillRoundRect(x, y, width, height, radius, color16b);
	} else {
		dma_display->drawRoundRect(x, y, width, height, radius, color16b);
	}
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Circle(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	int x = obj2int(args[0]);
	int y = obj2int(args[1]);
	int radius = obj2int(args[2]);
	int color16b = color24to16b(obj2int(args[3]));
	int fill = (argCount > 4) ? (trueObj == args[4]) : true;
	if (fill) {
		dma_display->fillCircle(x, y, radius, color16b);
	} else {
		dma_display->drawCircle(x, y, radius, color16b);
	}
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75Triangle(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	int x0 = obj2int(args[0]);
	int y0 = obj2int(args[1]);
	int x1 = obj2int(args[2]);
	int y1 = obj2int(args[3]);
	int x2 = obj2int(args[4]);
	int y2 = obj2int(args[5]);
	int color16b = color24to16b(obj2int(args[6]));
	int fill = (argCount > 7) ? (trueObj == args[7]) : true;
	if (fill) {
		dma_display->fillTriangle(x0, y0, x1, y1, x2, y2, color16b);
	} else {
		dma_display->drawTriangle(x0, y0, x1, y1, x2, y2, color16b);
	}
	UPDATE_DISPLAY();
	return falseObj;
}

static OBJ primh75DrawBuffer(int argCount, OBJ *args) {
	if (!h75initialized) return falseObj;

	OBJ buffer = args[0];
	OBJ palette = args[1]; // List, index-1 based
	int scale = max(min(obj2int(args[2]), 8), 1);

	int originX = 0;
	int originY = 0;
	int copyWidth = -1;
	int copyHeight = -1;

	if (argCount > 6) {
		originX = obj2int(args[3]);
		originY = obj2int(args[4]);
		copyWidth = obj2int(args[5]);
		copyHeight = obj2int(args[6]);
	}

	int bufferWidth = PANEL_WIDTH * PANELS / scale;
	int bufferHeight = PANEL_HEIGHT / scale;

	int originWidth = copyWidth >= 0 ? copyWidth : bufferWidth;
	int originHeight = copyHeight >= 0 ? copyHeight : bufferHeight;

	uint8 *bufferBytes = (uint8 *) &FIELD(buffer, 0);
	// Read the indices from the buffer and turn them into color values from the
	// palette, and paint them onto the TFT
	for (int y = 0; y < originHeight; y ++) {
		for (int x = 0; x < originWidth; x ++) {
			int colorIndex = bufferBytes[
				(y + originY) * bufferWidth + (x + originX)];
			int color = color24to16b(obj2int(FIELD(palette, colorIndex + 1)));
			for (int i = 0; i < scale; i ++) {
				for (int j = 0; j < scale; j ++) {
					bufferPixelsH75[(j * originWidth * scale) + x * scale + i] = color;
				}
			}
		}
		dma_display->drawRGBBitmap(
			originX * scale,
			(originY + y) * scale,
			bufferPixelsH75,
			originWidth * scale,
			scale
		);
	}

	UPDATE_DISPLAY();
	return falseObj;
}

// #else // stubs
//
// static OBJ primh75Init(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Clear(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75GetWidth(int argCount, OBJ *args) { return int2obj(0); }
// static OBJ primh75GetHeight(int argCount, OBJ *args) { return int2obj(0); }
// static OBJ primh75SetPixel(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75PixelRow(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Line(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Rect(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75RoundedRect(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Circle(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Triangle(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75Text(int argCount, OBJ *args) { return falseObj; }
// static OBJ primh75DrawBuffer(int argCount, OBJ *args) { return falseObj; }
//
// #endif

// Primitives

static PrimEntry entries[] = {
	{"init", primh75Init},
	{"clear", primh75Clear},
	{"getWidth", primh75GetWidth},
	{"getHeight", primh75GetHeight},
	{"setPixel", primh75SetPixel},
	{"pixelRow", primh75PixelRow},
	{"line", primh75Line},
	{"rect", primh75Rect},
	{"roundedRect", primh75RoundedRect},
	{"circle", primh75Circle},
	{"triangle", primh75Triangle},
	{"text", primh75Text},
	{"drawBuffer", primh75DrawBuffer},
};

void addH75Prims() {
	addPrimitiveSet(H75Prims,"h75", sizeof(entries) / sizeof(PrimEntry), entries);
}

#endif // ESP32_S3_MATRIX_PORTAL support
