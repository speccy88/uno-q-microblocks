// SPDX-License-Identifier: MIT
// Execute the real GP slot/model. Drawing is covered separately in the browser.
method redraw UnoQMatrixSlot { nop }
method redraw MicroBitDisplaySlot { nop }

to assert value {
	if (value != true) { error 'Matrix slot assertion failed' }
	setGlobal 'matrixSlotChecks' ((global 'matrixSlotChecks') + 1)
}

to startup {
	setGlobal 'scale' 1
	setGlobal 'blockScale' 1
	setGlobal 'matrixSlotChecks' 0
	s = (newUnoQMatrixSlot nil)
	assert ((contents s) == (unoQMatrixPreset 'Clear'))
	for name (array 'Heart' 'Smile' 'Checkerboard' 'Diagonal' 'All on' 'Clear') {
		p = (unoQMatrixPreset name)
		assert ((count p) == 104)
		assert (setContents s p)
		assert ((contents s) == p)
	}
	for y 8 {
		for x 13 {
			index = (((y - 1) * 13) + x)
			assert ((pixelIndexAt s (4 + ((x - 1) * 10)) (4 + ((y - 1) * 10))) == index)
			assert (isNil (pixelIndexAt s (11 + ((x - 1) * 10)) (4 + ((y - 1) * 10))))
		}
	}
	for p (array (array -1 5) (array 5 -1) (array 136 5) (array 5 83) (array 200 200)) {
		assert (isNil (pixelIndexAt s (at p 1) (at p 2)))
	}
	gray = (joinStringArray (newArray 13 '01234567'))
	assert (setContents s gray)
	assert ((contents s) == gray)
	for bad (array 42 'bad' (joinStringArray (newArray 104 '8')) (joinStringArray (newArray 104 'X'))) {
		assert (not (setContents s bad))
		assert ((contents s) == gray)
	}
	assert (setContents s (unoQMatrixPreset 'Clear'))
	assert (paintPixelAt s 1 '7')
	assert (paintPixelAt s 104 '7')
	assert ((at (contents s) 1) == '7')
	assert ((at (contents s) 104) == '7')
	assert (paintPixelAt s 1 '0')
	assert ((at (contents s) 1) == '0')
	for index (array 0 105 '1') { assert (not (paintPixelAt s index '7')) }
	assert (not (paintPixelAt s 2 '8'))
	assert (not (paintPixelAt s 2 '77'))
	assert (not (paintPixelAt s 2 7))
	// A fast pointer can jump multiple cells between events; fill the stroke.
	dragSlot = (newUnoQMatrixSlot nil)
	assert (paintStrokeTo dragSlot 1)
	assert (paintStrokeTo dragSlot 13)
	for i 13 { assert ((at (contents dragSlot) i) == '7') }
	setField dragSlot 'lastPaintIndex' nil
	setField dragSlot 'paintValue' '0'
	assert (paintStrokeTo dragSlot 13)
	assert (paintStrokeTo dragSlot 1)
	assert ((contents dragSlot) == (unoQMatrixPreset 'Clear'))
	setField dragSlot 'lastPaintIndex' nil
	setField dragSlot 'paintValue' '7'
	assert (paintStrokeTo dragSlot 1)
	assert (paintStrokeTo dragSlot 104)
	for y 8 {
		index = ((((y - 1) * 13) + (round (((y - 1) * 12) / 7))) + 1)
		assert ((at (contents dragSlot) index) == '7')
	}
	assert (not (paintStrokeTo dragSlot 0))
	assert (not (paintStrokeTo dragSlot 105))
	mb = (newMicroBitDisplaySlot 16777217)
	assert ((contents mb) == 16777217)
	setContents mb 0
	assert ((contents mb) == 0)
	// Exercise the real BlockSpec and Block event path, not a substitute model.
	spec = (blockSpecFromStrings '[unoq:matrixPattern]' ' ' 'image _' 'unoqMatrix' (array (unoQMatrixPreset 'Clear')))
	q = (inputSlot spec 1 (color 80 80 160))
	assert (isClass q 'UnoQMatrixSlot')
	block = (new 'Block')
	setField block 'morph' (newMorph block)
	setField block 'labelParts' (list (list q))
	setField block 'expression' (newCommand '[unoq:matrixPattern]' (contents q))
	addPart (morph block) (morph q)
	assert ((count (inputs block)) == 1)
	assert ((inputIndex block q) == 1)
	assert (paintPixelAt q 104 '7')
	assert ((first (argList (expression block))) == (contents q))
	// Standard .ubp serialization and the actual SmallVM compiler, without UI.
	for name (array 'matrix-drawing' 'matrix' 'combined' 'rgb') {
		p = (newMicroBlocksProject)
		loadFromString p (readFile (join '/external/examples/' name '.ubp')) false
		assert (saveLoadTest p)
	}
	hs = (new 'MicroBlocksScripter')
	setField hs 'mbProject' p
	rt = (initialize (new 'SmallRuntime') hs)
	setGlobal 'smallRuntime' rt
	assert (setContents s (unoQMatrixPreset 'Heart'))
	bytes = (compiledBytesFor rt (newCommand '[unoq:matrixPattern]' (contents s)))
	assert ((count bytes) > 104)
	print 'PATTERN_BYTECODE_JSON:' (jsonStringify bytes)
	f = (functionNamed p 'unoqShowImage')
	assert (notNil f)
	assert ((count (compiledBytesFor rt f)) > 0)
	print 'PASS: real GP matrix slot presets, 104 cells, gap/bounds rejection, editing and grayscale round-trip; checks:' (global 'matrixSlotChecks')
}
