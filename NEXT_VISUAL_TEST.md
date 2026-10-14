# Remaining physical observations

The owner has visually confirmed the matrix heart/checkerboard and red, green,
blue on each LED in turn. These observations are recorded as physical visual
PASS in TEST_RESULTS.md and evidence/visual-confirmations.json.

Exact matrix orientation remains unconfirmed. No firmware update is needed:
select LED matrix and Start, then compare the diagonal's physical direction
with the logical upper-left to lower-right framebuffer. Full/blank/diagonal
framebuffers were measured, but only heart/checkerboard were explicitly named
in the owner's visual reply. Optical grayscale linearity was not measured.

A fresh owner's board should separately verify the generic runtime's first
installation, restart registration, private LED backup and recovery procedure.
Do not replace this existing board's combined FPGA runtime merely for that test.
