"""
Buckshot 3 project files (.bs3, JSON). Keeps the editable tile with lines as
connected points (which a .bin cannot store), plus every reference: images
generated in-app are saved as PNGs beside the project.
"""
import json
import os

from PySide6 import QtGui

from .constants import RENDER_ORDER, NUM_CHANNELS

FORMAT = 'buckshot3'
VERSION = 1


def _sidecar(project_path, tag):
    base, _ = os.path.splitext(project_path)
    return f'{base}.{tag}.png'


def _rel(path, project_path):
    try:
        return os.path.relpath(path, os.path.dirname(project_path))
    except ValueError:
        return path


def _abs(path, project_path):
    if path is None or os.path.isabs(path):
        return path
    return os.path.normpath(os.path.join(os.path.dirname(project_path), path))


def save_project(path, doc, state):
    data = {'format': FORMAT, 'version': VERSION, 'layers': {}, 'channels': [],
            'channel_names': list(doc.channel_names), 'references': [],
            'mesh_settings': state.last_mesh_settings,
            'view': {'snap': state.snap, 'layer_visible': state.layer_visible,
                     'channel_visible': state.channel_visible}}
    for name in RENDER_ORDER:
        verts, tris = doc.layers[name].compact()
        data['layers'][name] = {'verts': verts, 'tris': tris}
    for ch in range(NUM_CHANNELS):
        pts, edges = doc.channels[ch].compact()
        data['channels'].append({'points': pts, 'edges': edges})

    def image_entry(slot, ref, kind, extra):
        if ref.source_path is None or kind == 'mesh':
            target = _sidecar(path, 'ref' if slot == 'C' else slot)
            ref.image.save(target)
            if kind != 'mesh':
                ref.source_path = target
            img_path = target
        else:
            img_path = ref.source_path
        e = {'slot': slot, 'kind': kind, 'label': ref.label, 'image': _rel(img_path, path)}
        e.update(extra)
        return e

    if state.background is not None:
        data['references'].append(image_entry('C', state.background, 'image', {}))
    for slot, nb in state.neighbours.items():
        if nb.kind == 'bin':
            data['references'].append({'slot': slot, 'kind': 'bin', 'label': nb.image.label,
                                       'path': _rel(nb.path, path), 'resolution': nb.resolution})
        else:
            data['references'].append(image_entry(slot, nb.image, nb.kind, {'settings': nb.settings}))

    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as f:
        json.dump(data, f)
    os.replace(tmp, path)


def load_project(path):
    """Returns (layers, channels, names, references, extras). References hold absolute paths."""
    with open(path, encoding='utf-8') as f:
        data = json.load(f)
    if data.get('format') != FORMAT:
        raise ValueError('Not a Buckshot 3 project file')
    layers = {name: (d['verts'], [tuple(t) for t in d['tris']])
              for name, d in data.get('layers', {}).items() if name in RENDER_ORDER}
    channels = [(c['points'], [tuple(e) for e in c['edges']]) for c in data.get('channels', [])][:NUM_CHANNELS]
    refs = []
    for r in data.get('references', []):
        r = dict(r)
        for k in ('image', 'path'):
            if k in r:
                r[k] = _abs(r[k], path)
        refs.append(r)
    return layers, channels, data.get('channel_names'), refs, data


def load_image(path) -> QtGui.QImage:
    img = QtGui.QImage(path)
    if img.isNull():
        raise ValueError(f'Could not read image: {path}')
    return img
