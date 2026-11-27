---
title: HEIC photos without a decoder
tags: [image, heic, heif, ffmpeg, color-profile, contact-sheet]
---

# HEIC photos without a decoder

Use when a phone photo arrives as HEIC/HEIF, the sandbox has no HEIC decoder
(no `libheif`, no Pillow plugin) and package installs are blocked. Check first
that a decoder really is missing (`ffmpeg -i photo.heic`, `python -c "import
pillow_heif"`); if one works, use it and skip this.

A HEIC photo is a HEIF container holding HEVC-coded **tiles** (a grid), plus
properties for rotation, mirroring and the colour profile. Only ffmpeg's HEVC
decoder is needed.

1. **Parse the container.** Read the HEIF boxes (`meta`, `iloc`, `iinf`,
   `iprp`, `iref`): find the grid item, its tile item ids, each tile's byte
   offset and length, the grid's rows, columns and output size, and the
   transform properties (`irot` rotation, `imir` mirror, `colr` colour data).
2. **Extract the tiles.** Write each tile's bytes (with the HEVC parameter
   sets from `hvcC`) as a raw HEVC stream and decode each with ffmpeg to a
   lossless image.
3. **Stitch the grid** in row-major order and crop to the grid's declared size
   (the last tiles are padded).
4. **Apply the transforms in the container's order**: rotation, then mirror.
   A skipped `irot` is the usual reason the result is sideways.
5. **Convert colour.** If an ICC profile is embedded, convert to sRGB; with no
   profile assume sRGB. Skipping this makes skin tones look washed or
   oversaturated.
6. **Contact sheet before ranking.** Render all converted candidates on one
   sheet with their file names, check orientation and sharpness on it
   (`image-quality-gate.md`), and only then rank or choose.

Report which steps ran and that orientation was verified on the output. If the
container uses a layout this recipe does not cover (overlay items, a non-HEVC
codec), say so and ask the owner for a JPEG export instead of guessing.
