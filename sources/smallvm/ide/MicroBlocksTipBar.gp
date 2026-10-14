// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/.

// Copyright 2019 John Maloney, Bernat Romagosa, and Jens Mönig

// MicroBlocksTipBar.gp - A bar that displays useful information about the item under the mouse
// Bernat Romagosa, November 2021

defineClass MicroBlocksTipBar morph contentDict help lastContents

method initialize MicroBlocksTipBar {
	morph = (newMorph this)
	setFPS morph 5
	initContents this
	help = (initialize (new 'MicroBlocksHelp'))
	return this
}

method helpEntry MicroBlocksTipBar primName { return (entryForOp help primName) }

// stepping

method step MicroBlocksTipBar {
	hand = (hand (global 'page'))
	if (and (isClass (grabbedObject hand) 'Block') (isClass (objectAt hand) 'BlocksPalette')) {
		updateTip this (objectAt hand)
	} (isBusy hand) {
		setProperty (api (smallRuntime)) 'ide.tip' (array '' '')
	} else {
		updateTip this (objectAt hand)
	}
}

method updateTip MicroBlocksTipBar anElement {
	contents = (contentsFor this anElement)
	if (lastContents == contents) { return }
	lastContents = contents

	setProperty (api (smallRuntime)) 'ide.tip' contents
}

// tip Contents

method initContents MicroBlocksTipBar {
	contentDict = (dictionary)
	atPut contentDict 'BooleanSlot' (array 'Boolean Input' '[l] toggle value, or drop a reporter into it.')
	atPut contentDict 'ColorSlot' (array 'Color Input' '[l] change the color, or drop a reporter into it.')
	atPut contentDict 'InputSlot' (array 'Input' '[l] edit its value, or drop a reporter into it.')
	atPut contentDict 'BlockDrawer' (array 'Block Extension' '[l] right arrow to show optional inputs, left arrow to hide.')

	atPut contentDict 'Command' (array 'Command Block' '[l] to run, or drag to build scripts. [r] menu.')
	atPut contentDict 'Hat' (array 'Hat Block' '[l] to run, or drag to build scripts. [r] menu.')
	atPut contentDict 'Reporter' (array 'Reporter Block' '[l] to see value, or drop into an input slot. [r] menu.')
	atPut contentDict 'Script' (array 'Script' '[l] to run. [r] menu.')

	atPut contentDict 'PaneResizer' (array 'Pane Divider' 'Drag to change pane width.')
	atPut contentDict 'Library' (array 'Library' '[l] to show the blocks in this library. [r] menu.')
	atPut contentDict 'BlockCategory' (array 'Block Category' '[l] to show the blocks in this category.')
	atPut contentDict 'BlocksPalette' (array 'Palette' 'Drag blocks from here to build scripts. Drop scripts here to delete them.')

	atPut contentDict 'ScriptEditor' (array 'Scripts Pane' 'Drag blocks here to build scripts. [r] menu.')
}

method contentsFor MicroBlocksTipBar anElement {
	key = (className (classOf anElement))
	if ('Button' == key) {
		return (array 'Button' (hint anElement))
	}
	block = nil
	if ('Block' == key) { block = anElement }
	if ('Text' == key) {
		if (notNil (ownerThatIsA (morph anElement) 'InputSlot')) {
			key = 'InputSlot'
		} (notNil (ownerThatIsA (morph anElement) 'Block')) {
			block = (handler (ownerThatIsA (morph anElement) 'Block'))
		}
	}
	if ('Slider' == key) {
		paneM = (ownerThatIsA (morph anElement) 'ScrollFrame')
		if (notNil paneM) {
			key = (className (classOf (contents (handler paneM))))
		}
	}
	if (notNil block) {
		topBlock = (topBlock block)
		if (and ('hat' == (type block)) (isNil (next block))) {
			key = 'Hat'
		} ('reporter' == (type block)) {
			if (block == topBlock) { // stand-alone reporter
				key = 'Reporter'
			} else { // reporter in a script
				key = 'Script'
			}
		} else {
			if (and (block == topBlock) (isNil (next block))) { // stand-alone command
				key = 'Command'
			} else {
				key = 'Script'
			}
		}
	}
	if (isClass anElement 'CategorySelector') {
		category = (categoryUnderHand anElement)
		items = (collection anElement)
		if (and (notEmpty items) ('cat;Output' == (first items))) {
			key = 'BlockCategory'
		} else {
			key = 'Library'
		}
	}
	content = (at contentDict key)
	if (isNil content) { // no match
		devMode = false
		if devMode { return (array key '') } // show key in tip bar during development
		return (array '' '')
	}
	if (isOneOf key 'Reporter' 'Command' 'Hat') {
		helpEntry = (helpEntry this (primName (expression block)))
		if (notNil helpEntry) {
			if (devMode) {
				// just show the help string
				fullDescription = (at helpEntry 3)
			} else {
				// show help string and gesture hints
				fullDescription = (join (localized (at helpEntry 3)) '    ' (localized (at content 2)))
			}
			content = (copy content)
			atPut content 2 fullDescription
		}
	}
	return content
}
