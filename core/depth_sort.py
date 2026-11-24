"""
Painter's-algorithm ordering for the top-down mesh render.

Sorting triangles by their average height goes wrong whenever a big triangle sits under or
over smaller ones: a long, sloping ground triangle can have a higher centroid than a building
roof that is really above it, so the ground gets drawn last and covers the roof.

For triangles that don't pass through each other, a correct order only has to respect one rule:
if two triangles overlap when seen from above, the lower one is drawn first. Within the overlap
the height gap between the two planes is linear and can't change sign (that would be an
intersection), so testing one point inside the overlap tells which is on top. Those
"A under B" pairs form a graph, and a topological sort of it is a valid drawing order
(the core of Newell's algorithm, without the polygon splitting).

  1. broad phase: triangles cut into grid columns, each piece boxed tightly (a long diagonal
     sliver's own bounding box is mostly empty), then a sweep along y within each column
  2. narrow phase: separating axis test on the two 2D triangles
  3. which is on top: average the height gap over corners of the overlap polygon (triangle
     corners inside the other triangle, and edge / edge crossings). The overlap is convex, so
     the average of its corners is a point inside it.
  4. Kahn's topological sort, taking the lowest (average height) free triangle each time, so
     unrelated triangles keep the old bottom-up order and the draw animation still builds upward

Real meshes aren't perfect: triangles that do intersect, or three that overlap in a cycle, can
leave the graph without a free triangle. Then the lowest remaining triangle is drawn next,
which is what the plain height sort would have done.
"""
import heapq

import numpy as np

CELL = 8.0              # tile units; broad phase column width
PAIR_CHUNK = 250_000    # pairs per numpy batch (bounds memory use)
OVERLAP_EPS = 1e-4      # tile units; triangles that only touch (shared edges) don't count as overlapping
HEIGHT_EPS = 1e-5       # height gaps smaller than this are treated as coplanar (no constraint)
PARALLEL = 1e-6         # sin of the smallest angle at which two edges are said to cross


def _column_strips(xy, cell):
    """
    Each triangle cut into the grid columns (cell wide) it spans, with the exact box of the
    piece inside each column: corners inside the column plus where the edges cross its sides.
    A long diagonal sliver's single bounding box covers a huge empty area (and so "overlaps"
    thousands of triangles it never touches); its strips don't.
    Returns (owner, col, x0, x1, y0, y1) per strip.
    """
    lo, hi = xy.min(axis=1), xy.max(axis=1)
    c0 = np.floor(lo[:, 0] / cell).astype(np.int64)
    k = np.floor(hi[:, 0] / cell).astype(np.int64) - c0 + 1
    owner = np.repeat(np.arange(len(xy)), k)
    col = c0[owner] + np.arange(len(owner)) - np.repeat(np.cumsum(k) - k, k)
    x0 = np.maximum(col * cell, lo[owner, 0])
    x1 = np.minimum((col + 1) * cell, hi[owner, 0])

    T = xy[owner]
    px, py = T[..., 0], T[..., 1]
    inside = (px >= x0[:, None]) & (px <= x1[:, None])
    y0 = np.where(inside, py, np.inf).min(1)
    y1 = np.where(inside, py, -np.inf).max(1)
    dx = np.roll(px, -1, axis=1) - px
    dy = np.roll(py, -1, axis=1) - py
    safe = np.where(dx != 0, dx, 1.0)
    for xs in (x0, x1):
        t = (xs[:, None] - px) / safe
        hit = (dx != 0) & (t >= 0) & (t <= 1)
        y = py + t * dy
        y0 = np.minimum(y0, np.where(hit, y, np.inf).min(1))
        y1 = np.maximum(y1, np.where(hit, y, -np.inf).max(1))
    bad = ~(y0 <= y1)            # can't happen bar rounding; fall back to the bounding box
    y0[bad], y1[bad] = lo[owner[bad], 1], hi[owner[bad], 1]
    return owner, col, x0, x1, y0, y1


def _candidate_pairs(xy, cell=CELL):
    """
    Sorted unique keys i * n + j (i < j) of triangles whose column strips overlap (by more than
    OVERLAP_EPS) somewhere. Sweep along y within each column: sorted by (column, y0), a
    strip's partners are the strips after it that start before its y1.
    """
    n = len(xy)
    if n < 2:
        return np.zeros(0, np.int64)
    owner, col, x0, x1, y0, y1 = _column_strips(xy, cell)
    # one sort key for (column, y): columns laid end to end, each `span` long
    ymin = y0.min()
    span = float(y1.max() - ymin) + 1.0
    base = (col - col.min()) * span - ymin
    srt = np.lexsort((y0, col))
    owner, x0, x1 = owner[srt], x0[srt], x1[srt]
    start_key = (base + y0)[srt]
    end_key = (base + y1)[srt]
    s = len(owner)
    cnt = np.maximum(np.searchsorted(start_key, end_key - OVERLAP_EPS, side='left')
                     - np.arange(s) - 1, 0)
    cum = np.cumsum(cnt)
    keys = []
    pos = 0
    while pos < s:
        done = cum[pos - 1] if pos else 0
        stop = max(pos + 1, int(np.searchsorted(cum, done + PAIR_CHUNK, side='right')))
        c = cnt[pos:stop]
        total = int(c.sum())
        if total:
            a = np.repeat(np.arange(pos, stop), c)
            b = a + 1 + np.arange(total) - np.repeat(np.cumsum(c) - c, c)
            ok = ((x0[b] < x1[a] - OVERLAP_EPS) & (x0[a] < x1[b] - OVERLAP_EPS)
                  & (owner[a] != owner[b]))
            a, b = owner[a[ok]], owner[b[ok]]
            keys.append(np.minimum(a, b) * n + np.maximum(a, b))
        pos = stop
    if not keys:
        return np.zeros(0, np.int64)
    keys = np.sort(np.concatenate(keys))
    return keys[np.r_[True, keys[1:] != keys[:-1]]]


def _edge_lines(xy):
    """
    (3,M,3): a, b, c per triangle edge, with a x + b y + c the signed distance from the edge,
    positive inside, whichever way the triangle winds. Zero-area triangles get all zeros, so
    they never count as overlapping anything.
    """
    p = xy
    e = np.roll(p, -1, axis=1) - p                                   # (M,3,2)
    area = e[:, 0, 0] * e[:, 1, 1] - e[:, 0, 1] * e[:, 1, 0]
    length = np.hypot(e[..., 0], e[..., 1])
    s = np.sign(area)[:, None] / np.where(length > 0, length, 1.0)  # (M,3)
    a = -e[..., 1] * s
    b = e[..., 0] * s
    c = -(a * p[..., 0] + b * p[..., 1])
    return np.stack([a, b, c])


def _sides(L, X, Y):
    """(P,3 edges,3 corners): signed distance of corners X, Y (P,3) from edge lines L (3,P,3)."""
    return L[0][:, :, None] * X[:, None] + L[1][:, :, None] * Y[:, None] + L[2][:, :, None]


def _planes(xy, h):
    """(M,2) height gradient (d/dx, d/dy) of each triangle; zero for zero-area ones."""
    e1, e2 = xy[:, 1] - xy[:, 0], xy[:, 2] - xy[:, 0]
    d1, d2 = h[:, 1] - h[:, 0], h[:, 2] - h[:, 0]
    area = e1[:, 0] * e2[:, 1] - e1[:, 1] * e2[:, 0]
    safe = np.where(area != 0, area, 1.0)
    gx = np.where(area != 0, (d1 * e2[:, 1] - d2 * e1[:, 1]) / safe, 0.0)
    gy = np.where(area != 0, (e1[:, 0] * d2 - e2[:, 0] * d1) / safe, 0.0)
    return np.stack([gx, gy], 1)


def _height_on(T, H, G, P):
    """Heights on the planes of triangles T (P,3,2) / corner heights H (P,3) / gradients G (P,2) at points P (P,k,2)."""
    return (H[:, 0:1] + G[:, 0:1] * (P[..., 0] - T[:, 0:1, 0])
            + G[:, 1:2] * (P[..., 1] - T[:, 0:1, 1]))


def _crossing_gap(sij, sji, Hi, Hj, Li, Lj):
    """
    (sum, count) of height(i) - height(j) where the edges of i cross the edges of j, worked
    out from the signed distances already known: sij (P,3,3) of j's corners from i's edge
    lines, sji of i's corners from j's. Edge a of i (corner a to a+1) crosses edge b of j
    where i's two corners are on opposite sides of j's edge line b, and vice versa; distance
    is linear along an edge, which gives how far along each edge the crossing is.
    Li, Lj (P,3) are the edge lengths: (near) parallel edges are skipped, as their distances
    are mostly rounding noise and the two "crossing" points needn't be the same point.
    """
    s0 = sji.transpose(0, 2, 1)                 # [p, a, b]: i's corner a from j's edge b
    s1 = np.roll(s0, -1, axis=1)                # i's corner a+1
    r0 = sij                                    # [p, a, b]: j's corner b from i's edge a
    r1 = np.roll(r0, -1, axis=2)                # j's corner b+1
    hit = ((s0 * s1 <= 0) & (r0 * r1 <= 0)
           & (np.abs(s0 - s1) > PARALLEL * Li[:, :, None])     # = edge length x sin(angle)
           & (np.abs(r0 - r1) > PARALLEL * Lj[:, None]))
    t = s0 / np.where(hit, s0 - s1, 1.0)        # along i's edge a
    u = r0 / np.where(hit, r0 - r1, 1.0)        # along j's edge b
    hi = Hi[:, :, None] + t * (np.roll(Hi, -1, axis=1) - Hi)[:, :, None]
    hj = Hj[:, None] + u * (np.roll(Hj, -1, axis=1) - Hj)[:, None]
    return np.where(hit, hi - hj, 0).sum((1, 2)), hit.sum((1, 2))


def below_pairs(xy, h):
    """
    (lower, upper) index arrays: every pair of triangles that overlap seen from above, lower one
    first. xy (M,3,2) top-down corner positions, h (M,3) corner heights.

    Which one is on top: the height gap averaged over the corners of the overlap polygon, i.e.
    triangle corners inside the other triangle, and where the edges cross. For triangles that
    intersect (no right answer) that is the gap at the middle of the overlap, which keeps
    cycles in the graph rare.
    """
    n = len(xy)
    keys = _candidate_pairs(xy)
    lines = _edge_lines(xy)
    X, Y = np.ascontiguousarray(xy[..., 0]), np.ascontiguousarray(xy[..., 1])
    grads = _planes(xy, h)
    lengths = np.hypot(*(np.roll(xy, -1, axis=1) - xy).transpose(2, 0, 1))   # (M,3)
    lowers, uppers = [], []
    for start in range(0, len(keys), PAIR_CHUNK):
        i, j = np.divmod(keys[start:start + PAIR_CHUNK], n)
        # separating axis test: overlapping unless all of one triangle is outside an edge of the other
        sij = _sides(lines[:, i], X[j], Y[j])              # i's edges x j's corners
        keep = ~(sij <= OVERLAP_EPS).all(-1).any(-1)
        i, j, sij = i[keep], j[keep], sij[keep]
        sji = _sides(lines[:, j], X[i], Y[i])
        keep = ~(sji <= OVERLAP_EPS).all(-1).any(-1)
        i, j, sij, sji = i[keep], j[keep], sij[keep], sji[keep]
        if not len(i):
            continue

        Ti, Tj, Hi, Hj = xy[i], xy[j], h[i], h[j]
        j_in_i = (sij >= -1e-9).all(1)                     # (P,3) per corner of j
        i_in_j = (sji >= -1e-9).all(1)
        total, count = _crossing_gap(sij, sji, Hi, Hj, lengths[i], lengths[j])
        total += (np.where(j_in_i, _height_on(Ti, Hi, grads[i], Tj) - Hj, 0).sum(1)
                  + np.where(i_in_j, Hi - _height_on(Tj, Hj, grads[j], Ti), 0).sum(1))
        count += j_in_i.sum(1) + i_in_j.sum(1)
        gap = np.where(count > 0, total / np.maximum(count, 1), 0.0)   # > 0: i is above j

        up = gap > HEIGHT_EPS
        down = gap < -HEIGHT_EPS
        lowers += [j[up], i[down]]
        uppers += [i[up], j[down]]
    if not lowers:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    return np.concatenate(lowers), np.concatenate(uppers)


def depth_order(xy, h):
    """
    Drawing order (indices, first drawn first) for triangles xy (M,3,2) with corner heights
    h (M,3), so that a triangle is drawn after every triangle under it.
    Returns (order, forced): forced counts the times a cycle had to be broken.
    """
    n = len(xy)
    if n == 0:
        return np.zeros(0, np.int64), 0
    xy = np.asarray(xy, np.float64)
    h = np.asarray(h, np.float64)

    # tie-break / fallback order: plain average height, stable
    by_height = np.argsort(h.mean(axis=1), kind='stable')
    rank = np.empty(n, np.int64)
    rank[by_height] = np.arange(n)

    lower, upper = below_pairs(xy, h)

    # adjacency lists (CSR), lower -> upper
    adj = upper[np.argsort(lower, kind='stable')].tolist()
    ptr = np.r_[0, np.cumsum(np.bincount(lower, minlength=n))].tolist()
    indeg = np.bincount(upper, minlength=n).tolist()
    rank_l = rank.tolist()
    by_height_l = by_height.tolist()

    heap = [rank_l[i] for i in range(n) if indeg[i] == 0]
    heapq.heapify(heap)
    drawn = bytearray(n)
    out = []
    forced = 0
    nxt = 0                       # by_height position: everything before it is drawn
    while len(out) < n:
        if not heap:
            # only cycles left: draw the lowest remaining triangle anyway
            while drawn[by_height_l[nxt]]:
                nxt += 1
            k = by_height_l[nxt]
            indeg[k] = 0
            heap.append(rank_l[k])
            forced += 1
        k = by_height_l[heapq.heappop(heap)]
        if drawn[k]:
            continue
        drawn[k] = 1
        out.append(k)
        for m in adj[ptr[k]:ptr[k + 1]]:
            indeg[m] -= 1
            if indeg[m] == 0:
                heapq.heappush(heap, rank_l[m])
    return np.asarray(out, np.int64), forced
