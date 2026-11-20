"""Shared constants for Buckshot 3."""

TILE_HALF = 500.0
TILE_SIZE = 1000.0

# Order layers are drawn in (bottom first). Matches the Buckshot tile editor.
RENDER_ORDER = ['Sea-0', 'Sea-1', 'Sea-2', 'Sea-3', 'Land', 'Sand',
                'Gravel', 'Rock', 'Grass', 'Snow', 'Shallows']

LAYER_COLORS = {
    'Sea-0': (50, 121, 134),
    'Sea-1': (61, 142, 159),
    'Sea-2': (72, 163, 184),
    'Sea-3': (83, 185, 209),
    'Land': (208, 208, 198),
    'Sand': (227, 208, 141),
    'Gravel': (139, 110, 92),
    'Rock': (88, 62, 45),
    'Grass': (164, 184, 117),
    'Snow': (255, 255, 255),
    'Shallows': (83, 185, 209),
}

BASE_COLOR = (40, 100, 110)   # open ocean colour under every tile

NUM_CHANNELS = 10
CHANNEL_COLORS = ['#ff595e', '#ffca3a', '#8ac926', '#32d6ba', '#37b6ff',
                  '#a68aff', '#f776ce', '#ff9b54', '#d6e36c', '#ffffff']

# Grid snap sizes in metres. 0 = off.
SNAP_AMOUNTS = [0, 100, 50, 25, 10, 5, 1, 0.5, 0.1]
DEFAULT_SNAP = 1

# Neighbour slots: name -> tile offset in metres.
SLOT_OFFSETS = {
    'NW': (-1000, 1000), 'N': (0, 1000), 'NE': (1000, 1000),
    'W': (-1000, 0), 'C': (0, 0), 'E': (1000, 0),
    'SW': (-1000, -1000), 'S': (0, -1000), 'SE': (1000, -1000),
}
SLOT_GRID = [['NW', 'N', 'NE'], ['W', 'C', 'E'], ['SW', 'S', 'SE']]
SLOT_NAMES = {
    'NW': 'North-west', 'N': 'North (above)', 'NE': 'North-east',
    'W': 'West (left)', 'C': 'Centre (editable tile)', 'E': 'East (right)',
    'SW': 'South-west', 'S': 'South (below)', 'SE': 'South-east',
}

# Known placements for hangar / runway meshes (pivot x, y, z), yaw degrees.
# Copied from rendering/grunk2.py.
PRESETS = {
    'Hangar: island_15': ((-226.23999, 4.653687, -93.25), 0.0),
    'Hangar: mega_island_2_6': ((182.808823, 12.437572, 28.43618), -135.0),
    'Hangar: mega_island_12_6': ((-21.98167, 8.672104, 176.530518), 135.0),
    'Hangar: arid_island_7_5': ((148.887848, 175.920563, 29.660955), -135.0),
    'Hangar: arid_island_19_11': ((-49.699303, 19.074291, 226.026657), 135.0),
    'Hangar: arid_island_26_14': ((-387.543793, 8.631, -480.134338), 75.0),
    'Runway: mega_island_2_6': ((-59.726631, 12.477757, 67.26754), 45.0),
    'Runway: mega_island_12_6': ((-63.345463, 8.671816, -64.124214), -45.0),
    'Runway: arid_island_7_5': ((-88.678055, 175.920563, 66.114197), 45.0),
    'Runway: arid_island_19_11': ((-83.529327, 19.114193, -11.039524), -45.0),
    'Runway: island_43_multiplayer_base': ((60.71703, 13.856232, -54.833088), -135.0),
}
