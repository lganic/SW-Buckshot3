"""
Fast Stormworks .mesh reader (same layout as rendering/mesh.py, but numpy based).

Layout: 8 byte header, uint16 vertex count, 4 unknown bytes, vertices
(pos f32x3, rgba u8x4, normal f32x3 = 28 bytes each), uint32 index count,
uint16 indices. Anything after the first index block is ignored.
"""
import math
import os
import struct
from dataclasses import dataclass, field

import numpy as np

from .constants import TILE_HALF
from .depth_sort import depth_order

VERT_DTYPE = np.dtype([('pos', '<f4', 3), ('col', 'u1', 4), ('nrm', '<f4', 3)])


@dataclass
class MeshData:
    path: str
    positions: np.ndarray   # (N, 3) float64, x / y (height) / z
    colors: np.ndarray      # (N, 4) uint8
    tris: np.ndarray        # (M, 3) int64


def load_mesh(path: str) -> MeshData:
    if not os.path.exists(path):
        raise FileNotFoundError(f'Mesh file not found: {path}')

    with open(path, 'rb') as f:
        data = f.read()

    off = 8
    (num_verts,) = struct.unpack_from('<H', data, off)
    off += 2 + 4
    verts = np.frombuffer(data, VERT_DTYPE, num_verts, off)
    off += num_verts * VERT_DTYPE.itemsize
    (num_idx,) = struct.unpack_from('<I', data, off)
    off += 4
    num_idx -= num_idx % 3
    idx = np.frombuffer(data, '<u2', num_idx, off).astype(np.int64).reshape(-1, 3)

    idx = idx[(idx < num_verts).all(axis=1)]
    return MeshData(path, verts['pos'].astype(np.float64), verts['col'].copy(), idx)


@dataclass
class MeshPlacement:
    """One mesh put into the scene: rotated by yaw about +Y, then moved to the pivot."""
    path: str
    x: float = 0.0
    y: float = 0.0          # height offset (affects contours)
    z: float = 0.0
    yaw: float = 0.0
    contours: bool = True   # does this mesh contribute to shore / height lines?

    def to_dict(self):
        return dict(path=self.path, x=self.x, y=self.y, z=self.z, yaw=self.yaw, contours=self.contours)

    @staticmethod
    def from_dict(d):
        return MeshPlacement(d['path'], d.get('x', 0), d.get('y', 0), d.get('z', 0),
                             d.get('yaw', 0), d.get('contours', True))


def transform_positions(pos: np.ndarray, p: MeshPlacement) -> np.ndarray:
    """Same maths as grunk2.rotate_point: yaw about +Y, then translate."""
    a = math.radians(p.yaw)
    c, s = math.cos(a), math.sin(a)
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    return np.stack([p.x + x * c + z * s, p.y + y, p.z - x * s + z * c], axis=1)


@dataclass
class SceneTris:
    """
    Up-facing triangles on the tile, in drawing order (each one after everything under it,
    see depth_sort). Tile coords (+Y up = mesh Z).
    """
    pts: np.ndarray       # (M, 3, 2) float64 tile x/y
    colors: np.ndarray    # (M, 3) uint8
    contour_meshes: list = field(default_factory=list)  # [(positions(N,3), tris(M,3))]


def build_scene(placements, cache=None) -> SceneTris:
    cache = {} if cache is None else cache
    all_pts, all_cols, all_h = [], [], []
    contour_meshes = []

    for p in placements:
        mesh = cache.get(p.path)
        if mesh is None:
            mesh = cache[p.path] = load_mesh(p.path)
        pos = transform_positions(mesh.positions, p)
        if p.contours:
            contour_meshes.append((pos, mesh.tris))

        tri_pos = pos[mesh.tris]                       # (M, 3, 3)
        xz = tri_pos[:, :, [0, 2]]
        (x1, z1), (x2, z2), (x3, z3) = xz[:, 0].T, xz[:, 1].T, xz[:, 2].T
        faces_up = ((z2 - z1) * (x3 - x1) - (x2 - x1) * (z3 - z1)) < 0   # back-face cull, see grunk2

        cols = mesh.colors[mesh.tris][:, :, :3].astype(np.float64).mean(axis=1)
        all_pts.append(xz[faces_up])
        all_cols.append(np.clip(np.round(cols[faces_up]), 0, 255).astype(np.uint8))
        all_h.append(tri_pos[faces_up][:, :, 1])

    if not all_pts:
        return SceneTris(np.zeros((0, 3, 2)), np.zeros((0, 3), np.uint8), contour_meshes)

    pts = np.concatenate(all_pts)
    cols = np.concatenate(all_cols)
    hts = np.concatenate(all_h)
    # nothing off the tile is ever seen, and sorting it would only cost time
    on_tile = (pts.min(axis=1) < TILE_HALF).all(axis=1) & (pts.max(axis=1) > -TILE_HALF).all(axis=1)
    pts, cols, hts = pts[on_tile], cols[on_tile], hts[on_tile]
    order, _ = depth_order(pts, hts)
    return SceneTris(pts[order], cols[order], contour_meshes)
