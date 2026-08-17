# Fixed six-frame contact-sheet replacement

Use chronological fixed batches: RF01-RF06, RF07-RF12, and so on. Only the last one may contain one to five frames. Never move a boundary for a shot, a scene, or a difficult interaction.

## Layout and output

- Use a 3-column by 2-row, zero-gutter source contact sheet for every full batch. Read left-to-right and then top-to-bottom.
- Use one horizontal, no-blank-cell row for a tail batch.
- Input the source sheet, existing product assets, product facts, user constraints, and per-frame plan. Save the result as `replacement-contact-sheet.png`.
- Keep accepted batch sheets as audit artifacts. Do not split or crop a sheet before batch review passes; after all batches pass, use only `assemble_storyboard_masters.py` to build the default final masters.

## Prompt and review

For every panel state its source composition anchor, expected product width/height and position relative to the panel, allowed replacement, prohibited changes, action, and transition. Preserve source camera, crop, exposure, blur, compression, full-sheet aspect ratio, and 9:16 cell geometry.

For filling, opening, cleaning, or hand-contact panels, state the proven product mechanism literally. For a bottom-hole feeder, show the side lattice and bottom hole as one coherent connected structure (the whole product need not be visible), with treats entering the bottom hole from above. Prohibit side-lattice filling, top openings, lids, smooth closed bottoms, and separable parts. For rinsing, keep the item whole and make water pass through the transparent lattice and naturally downward.

Review source and replacement sheets side by side for product identity, hard interaction facts, source order, recognizable composition, source visual texture, output sheet aspect, per-panel 9:16 geometry, and each approved product relative size. Fail geometry or scale drift that prevents deterministic master assembly; regenerate the same batch once only.
