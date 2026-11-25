"""Editor view state shared by the canvas and the side panels."""
from dataclasses import dataclass, field

import numpy as np
from PySide6 import QtCore, QtGui

from ..core.constants import RENDER_ORDER, NUM_CHANNELS, DEFAULT_SNAP, SLOT_OFFSETS, TILE_HALF


class ImageRef:
    """A reference picture covering one tile, with cached downscaled copies for fast drawing."""

    def __init__(self, image: QtGui.QImage, label: str, source_path: str | None = None):
        self.image = image.convertToFormat(QtGui.QImage.Format_RGB32)
        self.label = label
        self.source_path = source_path
        self._levels = {}

    def pixmap_for(self, screen_px: float) -> QtGui.QPixmap:
        """Smallest power-of-two downscale that still has >= 1 source px per screen px."""
        w = self.image.width()
        level = 0
        while w / (2 ** (level + 1)) >= max(64.0, screen_px):
            level += 1
        if level not in self._levels:
            if level == 0:
                img = self.image
            else:
                s = max(1, w // (2 ** level))
                img = self.image.scaled(s, s, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            self._levels[level] = QtGui.QPixmap.fromImage(img)
        return self._levels[level]


@dataclass
class Neighbour:
    slot: str
    kind: str                    # 'bin' | 'mesh' | 'image'
    image: ImageRef
    path: str | None = None
    resolution: int = 2048
    tiledata: object = None      # TileData for .bin neighbours (edge snap markers)
    settings: dict = field(default_factory=dict)
    edge_points: np.ndarray = None

    def compute_edge_points(self, tol=0.5):
        """Neighbour vertices / line points lying on the shared border, in centre-tile coords."""
        pts = []
        if self.tiledata is not None:
            for verts, _ in self.tiledata.layers.values():
                pts.extend(verts)
            for cpts, _ in self.tiledata.channels:
                pts.extend(cpts)
        if not pts:
            self.edge_points = np.zeros((0, 2))
            return
        ox, oy = SLOT_OFFSETS[self.slot]
        a = np.array(pts, np.float64) + (ox, oy)
        on_x = np.abs(np.abs(a[:, 0]) - TILE_HALF) < tol
        on_y = np.abs(np.abs(a[:, 1]) - TILE_HALF) < tol
        inside = (np.abs(a[:, 0]) <= TILE_HALF + tol) & (np.abs(a[:, 1]) <= TILE_HALF + tol)
        self.edge_points = np.unique(np.round(a[(on_x | on_y) & inside], 4), axis=0)


class EditorState(QtCore.QObject):

    changed = QtCore.Signal(str)   # what changed: 'mode', 'tool', 'active', 'visibility', 'refs', 'view'

    GEOMETRY_TOOLS = ['select', 'vertex', 'triangle']
    LINE_TOOLS = ['select', 'draw']

    def __init__(self):
        super().__init__()
        self.mode = 'geometry'
        self.tools = {'geometry': 'select', 'lines': 'draw'}
        self.active_layer = 'Land'
        self.active_channel = 0
        self.layer_visible = {n: True for n in RENDER_ORDER}
        self.channel_visible = [True] * NUM_CHANNELS
        self.snap = DEFAULT_SNAP
        self.fill_opacity = 0.55
        self.inactive_opacity = 0.35
        self.background_opacity = 0.6
        self.neighbour_opacity = 0.8
        self.show_grid = True
        self.show_lines_in_geometry = True
        self.show_geometry_in_lines = True
        self.background: ImageRef | None = None
        self.neighbours: dict[str, Neighbour] = {}
        self.last_dir = ''
        self.last_mesh_settings = None

    @property
    def tool(self):
        return self.tools[self.mode]

    def active_key(self):
        return ('layer', self.active_layer) if self.mode == 'geometry' else ('line', self.active_channel)

    def set_mode(self, mode):
        if mode != self.mode:
            self.mode = mode
            self.changed.emit('mode')

    def set_tool(self, tool):
        if self.tools[self.mode] != tool:
            self.tools[self.mode] = tool
            self.changed.emit('tool')

    def set_active_layer(self, name):
        self.active_layer = name
        self.changed.emit('active')
        self.set_mode('geometry')

    def set_active_channel(self, i):
        self.active_channel = i
        self.changed.emit('active')
        self.set_mode('lines')

    def notify(self, what):
        self.changed.emit(what)
