# Buckshot 3

One app for modding Stormworks map tiles. It replaces the old chain:
`r2.py` / `r3.py` → `ref.png` + `export.json` → `run.py` → `line_editor.py` → lines JSON → `add_lines.py`.
No intermediate files: renders, generated lines, geometry and hand-drawn lines all live in one document,
and **Export .bin** goes straight to sw_ducky.

```powershell
py -m Buckshot3
```

Run it from the repo root. It needs PySide6, numpy and sw_ducky (your Python 3.14 install has all three).
You can also pass a file to open: `py -m Buckshot3 my_tile.bs3` or `py -m Buckshot3 tile.bin`.

## Workflow

1. **Import** (Ctrl+I, shown at startup)
   * **Render .mesh files**: add one or more meshes. Each has X / Height / Z offsets, a yaw rotation, and a
     *Contours* tick box. The hangar and runway placements from `grunk2.py` are under *Apply placement preset*,
     so the old `r3.py` setup is three rows. You also pick the render resolution and background colour, and
     which lines to generate:
     * Shoreline (sea level, channel)
     * Height contours (interval, levels, first channel, one channel per level or all in one)
     * Undersea contours (same options)

     Each line group can be **added as editable lines** and/or **painted onto the image**. Contours are
     welded into connected lines, simplified (tolerance setting) and clipped to the tile.
     Press **Render** to watch the tile draw (speed slider, or *Skip animation*). Then pick where it goes:
     the centre (it becomes the reference image, and its lines are added; Ctrl+Z undoes that) or a neighbour slot.
   * **Map tile (.bin)**: set the render resolution and a slot. The centre loads the tile (and its lines) for
     editing. Any other slot (N / S / E / W / diagonals) shows it read-only beside your tile.
   * **Reference image**: any picture, stretched over a tile slot.

2. **Edit**: one canvas with two modes (toolbar or `Tab`).
   * **Geometry**: `G` select/move (box select, Shift adds, drag moves), `V` add vertex,
     `T` triangle (click 3 vertices, or click empty space to create one; Shift-click the third to keep building a strip).
   * **Lines**: `V` draw lines **point to point**. Clicking an existing point connects to it, and clicking an
     existing line splits it to make a junction. Double-click, right-click or Enter ends the line.
     `G` select/move: drag a point onto another point to weld them; double-click a line to insert a point.
   * `1`–`0` picks the layer (geometry) or channel (lines). Del deletes, Esc cancels, `F` fits the tile, `Shift+F` fits the neighbours too.
   * Snapping: the grid (toolbar), plus existing points within a few pixels. These include vertices on other layers
     and the **border points of neighbour tiles** (yellow diamonds), so edges line up across tiles. Hold Alt to place freely.
   * `W` `A` `S` `D` pan (hold Shift for faster). Wheel zooms. Middle/right drag or Space+drag pans too.
   * Line points show as small white dots in both modes, so lines are easy to line up with triangle vertices
     (which have a black outline).
   * Undo/redo (Ctrl+Z / Ctrl+Y) is one history covering geometry and lines.

3. **Layer stack** panel, with two views (switch with the buttons at the top, or `R`):
   * **Layers**: an exploded view of all 11 layers in draw order, with the lines as the top sheet. Click a sheet to edit it.
   * **Render**: the finished tile, flat, exactly as it will export (it ignores the visibility ticks). Toggles add the
     lines, neighbour tiles, a 50% reference image overlay, and an outline of the editor's view. Hover to see the
     topmost layer under the cursor. Click or drag to move the editor there; scroll to zoom the editor.

   The lists below toggle visibility and show counts; double-click a channel to rename it.

4. **Export .bin** (Ctrl+E): triangles are re-wound counter-clockwise. Each channel's connected points are walked
   into continuous paths and passed to `MapGeometry.add_path`, so ducky mitre-joins every run. Paths are split at
   near-reversals (>135°), where a mitre would spike.

5. **Save project** (Ctrl+S, `.bs3`): keeps everything, including the line connectivity a .bin can't store,
   references, and the last render settings. Rendered images are saved as PNGs next to the project.

## Layout

```
core/   constants, model (Document + undo), meshfile (fast .mesh reader + placement),
        contours (iso-lines, welding, simplify, clip), bin_io (ducky I/O, path export),
        tile_render (rasterising), project_io (.bs3)
ui/     main_window, canvas, stack_view, render_view, panels, mesh_dialog, import_dialogs, state, paths
```
