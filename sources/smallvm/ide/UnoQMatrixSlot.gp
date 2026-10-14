// SPDX-License-Identifier: MPL-2.0
// A 13x8 graphical input, based on MicroBlocks' MicroBitDisplaySlot.
// Original: Copyright 2019 John Maloney, Bernat Romagosa, and Jens Mönig.
// Its ordinary String value preserves the existing UNO Q matrix ABI.

defineClass UnoQMatrixSlot morph pixels paintValue inset stride ledSize lastPaintIndex

to newUnoQMatrixSlot pattern {
	return (initialize (new 'UnoQMatrixSlot') pattern)
}

method initialize UnoQMatrixSlot pattern {
	morph = (newMorph this)
	setHandler morph this
	setGrabRule morph 'defer'
	setTransparentTouch morph true
	pixels = (newArray 104 '0')
	inset = 3
	stride = 10
	ledSize = 8
	paintValue = '7'
	lastPaintIndex = nil
	setContents this pattern
	redraw this
	return this
}

method contents UnoQMatrixSlot { return (joinStringArray pixels) }

method setContents UnoQMatrixSlot pattern {
	if (or (isNil pattern) (pattern == '')) {
		pattern = (joinStringArray (newArray 104 '0'))
	}
	// Validate completely before replacing an existing image.
	if (not (isClass pattern 'String')) { return false }
	if ((count pattern) != 104) { return false }
	for i 104 {
		if ((containsSubString '01234567' (at pattern i)) == 0) { return false }
	}
	for i 104 { atPut pixels i (at pattern i) }
	redraw this
	raise morph 'inputChanged' this
	return true
}

method redraw UnoQMatrixSlot {
	scale = (blockScale)
	bm = (newBitmap (152 * scale) (86 * scale) (color 30 45 70))
	for y 8 {
		for x 13 {
			v = (toNumber (at pixels (((y - 1) * 13) + x)))
			c = (color 43 62 88)
			if (v > 0) { c = (color (30 + (v * 15)) (85 + (v * 20)) (115 + (v * 20))) }
			fillRect bm c ((inset + ((x - 1) * stride)) * scale) ((inset + ((y - 1) * stride)) * scale) (ledSize * scale) (ledSize * scale)
		}
	}
	pen = (newVectorPen bm)
	beginPath pen (138 * scale) (38 * scale)
	lineTo pen (148 * scale) (38 * scale)
	lineTo pen (143 * scale) (45 * scale)
	closePath pen
	fill pen (color 200 215 235)
	setCostume morph bm
}

method pixelIndexAt UnoQMatrixSlot localX localY {
	// Unscaled local coordinates; gaps and the dropdown never paint pixels.
	x = (localX - inset)
	y = (localY - inset)
	if (or (x < 0) (y < 0) (x >= (13 * stride)) (y >= (8 * stride))) { return nil }
	if (or ((x % stride) >= ledSize) ((y % stride) >= ledSize)) { return nil }
	return ((((truncate (y / stride)) * 13) + (truncate (x / stride))) + 1)
}

method pixelIndex UnoQMatrixSlot aHand {
	scale = (blockScale)
	return (pixelIndexAt this (((x aHand) - (left morph)) / scale)
		(((y aHand) - (top morph)) / scale))
}

method handEnter UnoQMatrixSlot aHand { setCursor 'crosshair' }
method handLeave UnoQMatrixSlot aHand { lastPaintIndex = nil; setCursor 'default' }

method handDownOn UnoQMatrixSlot aHand {
	if ((((x aHand) - (left morph)) / (blockScale)) >= 136) {
		showPresets this
		return true
	}
	index = (pixelIndex this aHand)
	if (isNil index) { return true }
	lastPaintIndex = nil
	paintValue = '7'
	if ((at pixels index) != '0') { paintValue = '0' }
	focusOn aHand this
	handMoveFocus this aHand
	return true
}

method handMoveFocus UnoQMatrixSlot aHand {
	index = (pixelIndex this aHand)
	if (notNil index) {
		paintStrokeTo this index
	} else {
		x = (((x aHand) - (left morph)) / (blockScale))
		y = (((y aHand) - (top morph)) / (blockScale))
		if (or (x < inset) (y < inset) (x >= (inset + 130)) (y >= (inset + 80))) {
			lastPaintIndex = nil
		}
	}
	return true
}

method paintStrokeTo UnoQMatrixSlot index {
	if (not (isClass index 'Integer')) { return false }
	if (or (index < 1) (index > 104)) { return false }
	if (or (isNil lastPaintIndex) (lastPaintIndex == index)) {
		lastPaintIndex = index
		return (paintPixelAt this index paintValue)
	}
	x0 = ((lastPaintIndex - 1) % 13)
	y0 = (truncate ((lastPaintIndex - 1) / 13))
	dx = (((index - 1) % 13) - x0)
	dy = ((truncate ((index - 1) / 13)) - y0)
	steps = (max (abs dx) (abs dy))
	for step (range 0 steps) {
		x = (round (x0 + ((dx * step) / steps)))
		y = (round (y0 + ((dy * step) / steps)))
		atPut pixels (((y * 13) + x) + 1) paintValue
	}
	lastPaintIndex = index
	redraw this
	raise morph 'inputChanged' this
	return true
}

method paintPixelAt UnoQMatrixSlot index value {
	if (not (isClass index 'Integer')) { return false }
	if (or (index < 1) (index > 104)) { return false }
	if (not (isClass value 'String')) { return false }
	if (or ((count value) != 1) ((containsSubString '01234567' value) == 0)) { return false }
	atPut pixels index value
	redraw this
	raise morph 'inputChanged' this
	return true
}

method showPresets UnoQMatrixSlot {
	m = (menu 'Matrix images')
	for name (array 'Heart' 'Smile' 'Checkerboard' 'Diagonal' 'All on' 'Clear') {
		addItem m name (action 'setContents' this (unoQMatrixPreset name))
	}
	popUpAtHand m (global 'page')
}

method rightClicked UnoQMatrixSlot aHand { showPresets this; return true }
method trigger UnoQMatrixSlot { showPresets this }

to unoQMatrixPreset name {
	if (name == 'Heart') {
		return '00077000770000077770777700077777777777007777777777700077777777700000777777700000007777700000000007000000'
	} (name == 'Checkerboard') {
		return '70707070707070707070707070707070707070707070707070707070707070707070707070707070707070707070707070707070'
	} (name == 'Diagonal') {
		return '70000000000000700000000000007000000000000070000000000000700000000000007000000000000070000000000000700000'
	} (name == 'Smile') {
		return (join '0000000000000' '0007000007000' '0007000007000' '0000000000000'
			'0070000000700' '0007000007000' '0000777770000' '0000000000000')
	} (name == 'All on') {
		return (joinStringArray (newArray 104 '7'))
	}
	return (joinStringArray (newArray 104 '0'))
}
