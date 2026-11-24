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

PRESETS = {
    # Airfields
    'Hangar: arid_island_19_11': ((-49.699303, 19.074291, 226.026657), 135.0),
    'Hangar: arid_island_26_14': ((-387.543793, 8.631, -480.134338), 75.0),
    'Hangar: arid_island_7_5': ((148.887848, 175.920563, 29.660955), -135.0),
    'Hangar: island_15': ((-226.23999, 4.653687, -93.25), 0.0),
    'Hangar: mega_island_12_6': ((-21.98167, 8.672104, 176.530518), 135.0),
    'Hangar: mega_island_2_6': ((182.808823, 12.437572, 28.43618), -135.0),
    'Runway: arid_island_19_11': ((-83.529327, 19.114193, -11.039524), -45.0),
    'Runway: arid_island_7_5': ((-88.678055, 175.920563, 66.114197), 45.0),
    'Runway: island_43_multiplayer_base': ((60.71703, 13.856232, -54.833088), -135.0),
    'Runway: mega_island_12_6': ((-63.345463, 8.671816, -64.124214), -45.0),
    'Runway: mega_island_2_6': ((-59.726631, 12.477757, 67.26754), 45.0),
    'Airfield (island_33): island_33_multi_tile_01': ((710.776733, 7.465149, -768.43042), -140.205),
    'Airfield (island_33): island_33_tile_33': ((-55.141663, 7.51, 306.184418), -140.284),
    # Roadside / commercial
    'Gas Station: arid_island_11_6': ((243.28009, 50.046082, -23.482365), 30.0),
    'Gas Station: arid_island_18_7': ((-370.156403, 15.47, 141.563934), 85.0),
    'Gas Station: arid_island_27_10': ((-291.59021, 19.741283, 187.781921), -42.0),
    'Gas Station: arid_island_3_8': ((-167.782043, 15.863204, 361.468567), -84.0),
    'Gas Station: arid_island_8_10': ((-76.605164, 111.360069, -386.44162), 180.0),
    'Gas Station B: arid_island_11_6': ((243.28009, 50.046082, -23.482365), 30.0),
    'Gas Station B: arid_island_18_7': ((-370.156403, 15.471339, 141.563934), 85.0),
    'Gas Station B: arid_island_27_10': ((-291.59021, 19.741283, 187.781921), -42.0),
    'Gas Station B: arid_island_3_8': ((-167.782043, 15.863204, 361.468567), -84.0),
    'Gas Station B: arid_island_8_10': ((-76.605164, 111.360069, -386.44162), 180.0),
    'Car Garage: arid_island_12_10': ((254.126175, 30.78159, 271.372223), 50.0),
    'Car Garage: arid_island_18_7': ((-399.963074, 15.471399, 127.321732), -5.0),
    'Car Garage: arid_island_5_14': ((-444.648041, 10.899719, -370.758667), 45.0),
    'Car Garage: arid_island_8_10': ((-58.12767, 111.31781, -393.87085), 180.0),
    'Office Building: island_33_multi_tile_01': ((-101.96994, 5.713806, -855.689331), 35.342),
    'Office Building: island_33_tile_32': ((136.287506, 5.167488, 209.318787), 38.009),
    'Island 11 Building: arid_island_16_9': ((299.509125, 16.729549, -98.564453), 90.0),
    'Island 11 Building: arid_island_4_13': ((44.312565, 10.813236, 348.263275), 0.0),
    'Island 11 Building: island11': ((96.833221, 13.658722, 47.645325), 0.0),
    # Harbour / coastal
    'Boat Shed: arid_island_5_14': ((-302.806, 2.241965, -382.86969), -136.0),
    'Boat Shed: island12': ((-32.773224, 3.427032, 2.153931), 0.0),
    'Boat Shed Stairs: arid_island_5_14': ((-300.442749, 2.27445, -396.548737), -100.0),
    'Boat Shed Stairs: island12': ((-32.521301, 3.426195, 2.184786), 0.0),
    'Jetty: island_26_fishing': ((56.993164, 3.817962, -61.114655), -90.49),
    'Jetty: island_33_multi_tile_01': ((-307.885864, 6.936432, 905.752563), 83.564),
    'Jetty: island_33_tile_12': ((-72.827057, 2.211309, -19.722229), 67.609),
    'Jetty: mega_island_2_9': ((403.039246, 5.46692, -482.848267), -170.0),
    'Terminal Dock: arctic_island_playerbase': ((64.402916, 6.845056, 102.77475), 30.0),
    'Terminal Dock: island_33_tile_end': ((51.779152, 5.360572, 155.49324), -138.217),
    'Terminal Dock: mega_island_9_8': ((278.649994, 3.630022, 199.199997), 1.391),
    'Island 34 Dock: island_34_military': ((-112.795883, 7.618912, -127.271439), 31.645),
    'Island 34 Dock: mega_island_15_2': ((573.955444, 6.637036, -437.280731), -55.0),
    'Volcano Dock: arid_island_24_3': ((142.868164, -75.775421, 228.494843), 0.0),
    'Volcano Dock: mega_island_5_2': ((275.231934, -75.285004, 326.189941), 0.0),
    'Lighthouse (mainland): arid_island_3_14': ((479.952148, 68.727501, 477.873962), 0.0),
    'Lighthouse (mainland): mega_island_14_0': ((177.682159, 32.417896, -108.423706), 0.0),
    'Lighthouse Building (mainland): arid_island_3_14': ((479.952148, 68.727501, 477.873962), 0.0),
    'Lighthouse Building (mainland): mega_island_14_0': ((177.682159, 32.448532, -108.423706), 0.0),
    'Lighthouse (island_38): arid_island_29_4': ((273.548767, 89.470757, 28.982494), 0.0),
    'Lighthouse (island_38): island_38_lighthouse': ((0.0, 3.016907, 0.0), 0.0),
    'Lighthouse (arctic): arctic_tile_23': ((-134.12706, 24.313808, -190.65448), 90.0),
    'Lighthouse (arctic): mega_island_5_9': ((-48.122017, 16.299286, 78.491035), 10.0),
    'Bascule Bridge Base: arid_island_10_11 #1': ((287.119995, 14.951317, 102.679802), 90.0),
    'Bascule Bridge Base: arid_island_10_11 #2': ((377.957336, 14.951317, 102.673546), -90.0),
    'Bascule Bridge Base: arid_island_12_13 #1': ((-97.132217, 15.28913, -228.247269), -175.0),
    'Bascule Bridge Base: arid_island_12_13 #2': ((-105.047798, 15.28913, -318.722809), 5.0),
    'Bascule Bridge Base: arid_island_13_13 #1': ((-66.092308, 16.009987, 119.801987), 90.0),
    'Bascule Bridge Base: arid_island_13_13 #2': ((24.754707, 16.009987, 119.801987), -90.0),
    'Bascule Bridge Base: arid_island_14_11 #1': ((299.320679, 14.915922, -422.298706), 90.0),
    'Bascule Bridge Base: arid_island_14_11 #2': ((390.16626, 14.92, -422.298706), -90.0),
    'Bascule Bridge Base: arid_island_14_5 #1': ((123.361069, 15.570801, 250.60965), 130.0),
    'Bascule Bridge Base: arid_island_14_5 #2': ((192.885605, 15.570801, 192.271622), -50.0),
    'Bascule Bridge Base: arid_island_16_5 #1': ((123.166649, 14.902222, 189.228241), 90.0),
    'Bascule Bridge Base: arid_island_16_5 #2': ((213.952499, 14.902222, 189.228241), -90.0),
    'Bascule Bridge Base: arid_island_16_6 #1': ((-186.484375, 16.383701, -225.072845), 45.0),
    'Bascule Bridge Base: arid_island_16_6 #2': ((-122.252052, 16.383701, -160.84053), -135.0),
    'Bascule Bridge Base: arid_island_19_7 #1': ((-80.232803, 15.66893, -247.118958), 180.0),
    'Bascule Bridge Base: arid_island_19_7 #2': ((-80.232803, 15.66893, -337.950806), 0.0),
    'Bascule Bridge Base: arid_island_21_5 #1': ((333.509308, 15.232388, -412.885406), -65.0),
    'Bascule Bridge Base: arid_island_21_5 #2': ((251.176224, 15.232388, -374.492859), 115.0),
    'Bascule Bridge Base: arid_island_27_10 #1': ((162.045715, 14.883741, -63.993572), 115.0),
    'Bascule Bridge Base: arid_island_27_10 #2': ((244.290543, 14.883741, -102.344994), -65.0),
    'Bascule Bridge Base: arid_island_3_7 #1': ((239.415909, 14.957456, 247.559692), -40.0),
    'Bascule Bridge Base: arid_island_3_7 #2': ((181.022217, 14.957456, 317.150604), 140.0),
    'Bascule Bridge Base: arid_island_5_13 #1': ((340.082397, 15.106379, -178.992264), 145.0),
    'Bascule Bridge Base: arid_island_5_13 #2': ((392.191345, 15.106379, -253.41156), -35.0),
    'Bascule Bridge Base: arid_island_9_14 #1': ((286.369324, 14.741589, 159.524536), 80.0),
    'Bascule Bridge Base: arid_island_9_14 #2': ((375.769226, 14.741589, 175.288147), -100.0),
    'Bascule Bridge Base: arid_island_9_7 #1': ((-210.489365, 15.105131, -324.159424), 115.0),
    'Bascule Bridge Base: arid_island_9_7 #2': ((-128.146286, 15.105131, -362.556641), -65.0),
    'Bascule Bridge Base: mega_island_10_3 #1': ((363.130005, 15.47, 308.350006), 30.0),
    'Bascule Bridge Base: mega_island_10_3 #2': ((408.554382, 15.473963, 387.050629), -150.0),
    'Bascule Bridge Base: mega_island_3_5 #1': ((57.835785, 15.17997, 95.362808), -45.0),
    'Bascule Bridge Base: mega_island_3_5 #2': ((-6.428161, 15.17997, 159.626755), 135.0),
    'Bascule Bridge Base: mega_island_3_8 #1': ((377.114594, 15.316633, -37.120655), -90.0),
    'Bascule Bridge Base: mega_island_3_8 #2': ((286.25, 15.316633, -37.120655), 90.0),
    'Bascule Bridge Base: mega_island_6_2 #1': ((-357.640442, 14.916116, 225.458481), 0.0),
    'Bascule Bridge Base: mega_island_6_2 #2': ((-357.640442, 14.916116, 316.329987), 180.0),
    'Bascule Bridge Base: mega_island_7_1 #1': ((-242.108719, 14.99, 324.230835), 95.0),
    'Bascule Bridge Base: mega_island_7_1 #2': ((-151.588058, 14.987749, 316.311279), -85.0),
    'Bascule Bridge Base: mega_island_7_7 #1': ((342.59613, 15.517998, -20.482134), 30.0),
    'Bascule Bridge Base: mega_island_7_7 #2': ((388.02887, 15.517998, 58.209656), -150.0),
    # Housing / villages
    'Flatpack House: arid_island_11_14': ((65.093773, 29.628605, -63.8353), 150.0),
    'Flatpack House: arid_island_12_10': ((-202.471695, 47.674946, 258.438568), -85.0),
    'Flatpack House: arid_island_13_6': ((-395.617798, 29.908981, -215.083481), 148.0),
    'Flatpack House: arid_island_15_5': ((-321.842346, 30.074137, -143.159225), 3.0),
    'Flatpack House: arid_island_19_12': ((-262.920837, 19.088711, -101.109344), -135.0),
    'Flatpack House: arid_island_24_3': ((352.636841, 5.915098, 254.084198), 90.0),
    'Flatpack House: arid_island_26_14': ((-110.597191, 8.639879, 51.144958), -15.0),
    'Flatpack House: arid_island_5_14': ((-301.026306, 15.304531, -415.060883), 120.0),
    'Flatpack House: arid_island_6_7': ((130.272385, 67.665657, -438.936707), 25.0),
    'Flatpack House: arid_island_8_15': ((-23.319035, 8.363323, -238.578842), 0.0),
    'Cottages (island_26): island_26_fishing': ((36.011833, 3.928222, -33.1777), -90.801),
    'Cottages (island_26): island_33_multi_tile_01 #1': ((-256.097809, 8.478119, 841.678406), 110.251),
    'Cottages (island_26): island_33_multi_tile_01 #2': ((-352.564819, 12.007202, -744.681396), -68.911),
    'Cottages (island_26): island_33_tile_12': ((-16.743683, 8.495977, -87.724762), 109.241),
    'Cottages (island_26): island_33_tile_32': ((9.925659, 36.44175, 357.578796), -65.92),
    'Cottages (island_26): mega_island_15_2': ((-110.407433, 7.911799, 158.518692), -90.0),
    'Cottages (island_26): mega_island_2_9': ((360.820007, 5.086344, -430.272522), -165.0),
    'Cottages 02 (island_26): island_26_fishing': ((-11.412174, 3.937737, -53.839817), 70.695),
    'Cottages 02 (island_26): island_33_multi_tile_01': ((-265.377045, 8.38147, 841.678406), 0.0),
    'Cottages 02 (island_26): island_33_tile_12': ((-30.00885, 8.495977, -76.243988), -68.919),
    'Cottages 02 (island_26): mega_island_15_2': ((-108.313416, 8.013662, 148.838715), 105.0),
    'Cottages 02 (island_26): mega_island_2_9 #1': ((371.901062, 5.017859, -427.572052), 15.0),
    'Cottages 02 (island_26): mega_island_2_9 #2': ((378.381653, 5.125565, -406.113434), 25.0),
    'Church: island_26_fishing': ((-64.168953, 3.800964, -59.147034), -90.0),
    'Church: island_33_multi_tile_01': ((-107.230011, 8.547913, 923.686584), 0.0),
    'Church: island_33_tile_12': ((114.755524, 8.590094, -23.079712), 0.0),
    'Church: mega_island_2_9': ((308.667389, 5.79415, -311.112549), -125.0),
    'Church: mega_island_8_7': ((46.190331, 8.616663, 280.657074), -60.0),
    'Cottages (island_33): island_33_multi_tile_01': ((389.719025, 10.400574, -660.461121), 29.935),
    'Cottages (island_33): island_33_tile_33': ((-391.880127, 10.89, 389.213531), 10.014),
    'Village Cottages (mainland): mega_island_15_2 #1': ((43.901215, 6.427524, 221.938248), 110.0),
    'Village Cottages (mainland): mega_island_15_2 #2': ((130.928543, 6.462214, 185.144241), 115.0),
    'Village Cottages (mainland): mega_island_8_7': ((43.728561, 8.54055, 243.90007), -60.008),
    'Village Cottages (mainland): mega_island_8_8': ((57.465054, 12.737012, -424.941193), 90.0),
    'Village Cottages 02 (mainland): mega_island_15_2': ((31.129345, 6.438908, 225.96048), 110.0),
    'Village Cottages 02 (mainland): mega_island_8_7': ((139.1651, 8.530714, 184.674362), -54.831),
    'Village Cottages 02 (mainland): mega_island_8_8': ((50.492867, 12.745892, -423.291382), 90.0),
    'Village Centre (mainland): mega_island_15_2': ((68.633766, 6.529566, 289.938293), -70.0),
    'Village Centre (mainland): mega_island_8_7': ((-9.137402, 8.613266, 219.360687), -165.0),
    'Village Hall (mainland): mega_island_15_2': ((68.633766, 6.529566, 289.938293), -70.0),
    'Village Hall (mainland): mega_island_8_7': ((-9.137402, 8.613266, 219.360687), -165.0),
    'Arid House A: arid_island_11_5': ((-29.059458, 37.704594, 191.83757), 80.0),
    'Arid House A: arid_island_12_13': ((160.874985, 27.942886, 98.720276), 0.0),
    'Arid House A: arid_island_17_9': ((-76.384079, 16.142786, 64.189941), -55.0),
    'Arid House A: arid_island_4_12': ((167.906265, 15.558955, 278.397644), -140.0),
    'Arid House B: arid_island_12_13': ((129.0625, 28.433611, 86.775826), 0.0),
    'Arid House B: arid_island_17_9': ((-52.742348, 16.191483, 100.32061), 125.0),
    'Arid House B: arid_island_23_11': ((-156.556976, 19.972366, 249.580994), 0.0),
    'Arid House B: arid_island_5_4': ((219.967972, 105.625908, -344.465393), 90.0),
    'Arid House C: arid_island_23_11': ((-57.351303, 19.751171, 253.366425), 0.0),
    'Arid House C: arid_island_5_4 #1': ((177.80983, 105.504135, -343.115173), 0.0),
    'Arid House C: arid_island_5_4 #2': ((266.814484, 105.652435, -344.465393), 180.0),
    'Arid House C: arid_island_5_4 #3': ((197.611893, 105.432137, -303.227386), 0.0),
    'Arid House D: arid_island_12_13': ((180.034698, 27.461815, 93.095482), 0.0),
    'Arid House D: arid_island_17_9': ((-57.5494, 16.139864, 70.670517), -145.0),
    'Arid House D: arid_island_5_4': ((112.597549, 105.204323, -348.618896), 0.0),
    'Arid House E: arid_island_11_5': ((-42.181904, 37.865646, 190.344589), -10.0),
    'Arid House E: arid_island_17_9': ((-80.484192, 16.189396, 107.651443), 35.0),
    'Arid House E: arid_island_5_4': ((146.174072, 105.390411, -343.115173), 90.0),
    'Arid House G: arid_island_11_5': ((-33.792938, 37.865646, 212.198029), 80.0),
    'Arid House G: arid_island_12_13': ((148.592468, 28.433611, 82.075943), -90.0),
    'Arid House G: arid_island_23_11': ((-152.843842, 19.65205, 285.045715), 90.0),
    'Arid House G: arid_island_4_12': ((182.032837, 15.686121, 305.525482), 130.0),
    'Arid Village A: arid_island_23_11': ((-143.806641, 19.776443, 245.918945), 0.0),
    'Arid Village A: arid_island_5_4': ((107.840118, 105.719185, -336.340576), 0.0),
    'Arid Village A: arid_island_9_9': ((-407.835022, 52.856449, -44.727905), 0.0),
    'Arid Village B: arid_island_5_4': ((196.000122, 105.533401, -336.340576), 0.0),
    'Arid Village B: arid_island_9_9': ((-401.511261, 52.871887, 4.320937), 0.0),
    # Farms
    'Barn A: arid_island_11_12 #1': ((233.168777, 20.743816, -275.249939), 90.0),
    'Barn A: arid_island_11_12 #2': ((250.898239, 20.743816, -275.249939), 90.0),
    'Barn A: mega_island_10_7 #1': ((-158.169159, 7.468912, 181.060791), 90.0),
    'Barn A: mega_island_10_7 #2': ((-145.350769, 7.468912, 181.060791), 90.0),
    'Barn A: mega_island_10_7 #3': ((-132.529449, 7.468912, 181.060791), 90.0),
    'Barn B: arid_island_11_12 #1': ((363.883881, 20.737827, -235.784317), -90.0),
    'Barn B: arid_island_11_12 #2': ((382.064423, 20.737827, -235.784317), -90.0),
    'Barn B: mega_island_10_7': ((-73.677795, 7.423017, 250.078827), 90.0),
    'Grain Barn: arid_island_11_12': ((252.148743, 20.743816, -239.06398), -90.0),
    'Grain Barn: mega_island_10_7 #1': ((-93.772545, 7.468912, 181.060791), 90.0),
    'Grain Barn: mega_island_10_7 #2': ((-132.529449, 7.468912, 198.316818), 0.0),
    'Water Tower: arid_island_12_8': ((-260.408875, 33.372066, 159.144257), 0.0),
    'Water Tower: arid_island_7_7': ((-393.580048, 172.539078, -78.514099), 0.0),
    # Rail
    'Train Terminal Building: arctic_tile_12_oilrig': ((421.771484, 15.0, -386.196411), 0.0),
    'Train Terminal Building: arctic_tile_22': ((-40.800861, 15.894352, -384.172974), 180.0),
    'Train Terminal Building: island_33_tile_end': ((25.831154, 15.740822, 139.465927), -138.4),
    'Train Terminal Building: mega_island_12_7': ((-230.946579, 10.75, -445.954102), 0.0),
    'Train Terminal Building: mega_island_9_8': ((281.774353, 6.888823, 234.702896), 0.972),
    'Train Terminal (open): island_33_tile_end': ((25.990623, 15.98, 139.661758), -139.0),
    'Train Terminal (open): mega_island_9_8': ((281.602203, 6.925132, 234.075607), 0.8),
    'Train Shed: arctic_tile_12_oilrig': ((349.091614, 15.937923, -306.637787), 41.0),
    'Train Shed: arctic_tile_22': ((2.506878, 15.98, -349.587585), 91.0),
    'Train Shed: island_33_tile_32': ((-3.25174, 15.970907, 255.499817), -159.0),
    'Train Depot B: island_33_tile_end': ((25.831154, 15.740822, 139.465927), -138.4),
    'Train Depot B: mega_island_9_8': ((281.700897, 6.888823, 234.410889), 1.3),
    'Depot (island_37): island_37_container_depot': ((-11.74, 5.402466, -68.930153), 0.0),
    'Depot (island_37): mainland_container_depot': ((-11.74, 5.402466, -68.930153), 0.0),
    'Depot Railings (island_37): island_37_container_depot': ((-11.74, 5.402466, -68.930153), 0.0),
    'Depot Railings (island_37): mainland_container_depot': ((-11.74, 5.402466, -68.930153), 0.0),
    'Railway Stop: arid_island_14_13 #1': ((-291.408447, 18.912361, 86.492378), 0.0),
    'Railway Stop: arid_island_14_13 #2': ((-251.753006, 18.912361, 77.709068), 180.0),
    'Railway Stop: arid_island_17_7': ((-114.444511, 19.071995, 80.715912), 120.0),
    'Railway Stop: arid_island_23_11 #1': ((-89.918434, 19.048496, 345.237366), -179.0),
    'Railway Stop: arid_island_23_11 #2': ((-129.412292, 19.048496, 354.569061), 1.0),
    'Railway Stop: arid_island_28_8': ((-56.706242, 31.117805, 330.84967), 110.0),
    'Railway Stop: arid_island_8_14': ((-125.113762, 8.14, 216.160538), 0.0),
    'Signal Box (large): arid_island_17_12': ((-180.589035, 19.159437, 381.65152), -15.0),
    'Signal Box (large): arid_island_7_9': ((-312.949341, 76.394257, -478.269775), 20.0),
    'Signal Box (large): arid_island_8_7': ((74.189598, 29.219368, -223.681519), 0.0),
    'Signal Box (large): arid_island_9_11': ((403.81134, 39.265018, -303.102325), 145.0),
    'Signal Box (mid): arid_island_14_13 #1': ((-280.477936, 19.808844, 90.32814), 0.0),
    'Signal Box (mid): arid_island_14_13 #2': ((-278.967194, 19.808844, 90.32814), 0.0),
    'Signal Box (mid): arid_island_18_10': ((469.694611, 19.012386, 50.336311), 160.0),
    'Signal Box (mid): arid_island_23_11': ((-118.421677, 19.983335, 341.884949), 180.0),
    'Signal Box (mid): arid_island_28_8 #1': ((-47.719353, 15.941628, 352.970978), 15.0),
    'Signal Box (mid): arid_island_28_8 #2': ((-45.981499, 15.941628, 354.652557), -165.0),
    'Signal Box (mid): arid_island_3_8': ((-165.947922, 29.597425, 57.043129), 120.0),
    'Signal Box (mid): arid_island_5_6': ((-19.394337, 22.930937, 456.376495), 55.0),
    'Signal Box (mid): arid_island_8_14': ((-149.290848, 8.231449, 205.513367), 0.0),
    'Signal Box (mid): arid_island_9_11 #1': ((354.111237, 39.393463, -180.464828), -35.0),
    'Signal Box (mid): arid_island_9_11 #2': ((435.24762, 39.265018, -281.090424), 145.0),
    'Signal Box (mid): arid_island_9_11 #3': ((321.176727, 39.378685, -203.525818), -35.0),
    'Signal Box (small): arid_island_17_9': ((212.270065, 18.976212, -212.159576), 70.0),
    'Signal Box (small): arid_island_22_4': ((114.130287, 31.18026, 184.265884), 180.0),
    'Signal Box (small): arid_island_5_5': ((-191.832321, 35.174671, 245.763229), -140.0),
    'Signal Box (small): arid_island_9_11 #1': ((434.212036, 39.265018, -281.836426), 145.0),
    'Signal Box (small): arid_island_9_11 #2': ((352.958923, 39.378685, -181.271698), -35.0),
    'Signal Box (small): arid_island_9_11 #3': ((319.658691, 39.378685, -204.588745), -35.0),
    # Industry
    'Industrial Area: island_33_multi_tile_01': ((-101.96994, 5.713806, -858.200684), 32.555),
    'Industrial Area: island_33_tile_32': ((128.085266, 5.167488, 216.85202), 36.695),
    'Quarry: island_33_multi_tile_01': ((-153.443237, 67.020782, -290.818085), -159.321),
    'Quarry: island_33_tile_22': ((70.358589, 67.0439, -190.731476), -146.544),
    'Quarry: mega_island_7_6': ((145.765396, 30.938189, -38.812351), 0.0),
    'Coal Mine Building: arid_island_15_13 #1': ((348.309601, 19.091745, 154.841904), 0.0),
    'Coal Mine Building: arid_island_15_13 #2': ((348.309601, 19.091745, 145.790375), 0.0),
    'Coal Mine Building: arid_island_25_11 #1': ((-454.544739, 19.125969, -457.408203), 31.0),
    'Coal Mine Building: arid_island_25_11 #2': ((-459.213165, 19.125969, -465.15152), 31.0),
    'Coal Mine Machine: arid_island_16_14': ((310.639221, 121.37381, 40.255375), 120.0),
    'Coal Mine Machine: arid_island_17_14 #1': ((94.02758, 120.460907, 54.695862), 10.0),
    'Coal Mine Machine: arid_island_17_14 #2': ((-334.43396, 29.144775, 262.122253), -80.0),
    'Coal Mine Belt: arid_island_16_14': ((474.06488, 74.474747, 299.685699), 100.0),
    'Coal Mine Belt: arid_island_17_14': ((12.036065, 130.760956, -202.636032), 130.0),
    'Coal Mine Belt: arid_island_17_4': ((-184.578079, 159.566345, 250.553192), 0.0),
    'Coal Mine Belt: arid_island_23_10': ((-278.936157, 114.001968, -317.413635), 0.0),
    'Coal Mine Belt B: arid_island_16_14': ((354.981262, 120.267418, -33.909679), 60.0),
    'Coal Mine Belt B: arid_island_17_14': ((-334.43396, 27.901066, 237.053665), 0.0),
    'Oil Platform (arid): arid_island_23_14': ((-291.762238, 16.09, -361.867706), 0.0),
    'Oil Platform (arid): arid_island_24_4': ((-172.407883, 44.66, -84.083221), 0.0),
    'Oil Platform (arid): arid_island_3_12': ((412.251923, 18.27, 12.139788), 0.0),
    'Oil Platform (arid): arid_island_8_11': ((370.490082, 9.15, -0.511297), 0.0),
    'Wind Farm Building: island_28_windfarm': ((136.328171, 13.288757, -196.510391), 0.0),
    'Wind Farm Building: mega_island_11_4': ((-384.460541, 21.119886, 23.152624), 45.0),
    'Wind Turbine: island_28_windfarm #1': ((-72.385178, 48.798553, 13.297136), 0.0),
    'Wind Turbine: island_28_windfarm #2': ((-157.544479, 34.574066, -39.975388), 0.0),
    'Wind Turbine: island_28_windfarm #3': ((-125.947922, 39.011353, 99.939224), 0.0),
    'Wind Turbine: island_28_windfarm #4': ((-169.876328, 14.105072, -184.530197), 0.0),
    'Wind Turbine: island_28_windfarm #5': ((40.387619, 38.277008, 235.00206), 0.0),
    'Wind Turbine: island_28_windfarm #6': ((105.432266, 35.017456, 128.119705), 0.0),
    'Wind Turbine: island_28_windfarm #7': ((-80.265732, 14.200012, -141.896927), 0.0),
    'Wind Turbine: island_28_windfarm #8': ((-3.165359, 34.47998, -32.522049), 0.0),
    'Wind Turbine: island_28_windfarm #9': ((134.322952, 14.059174, -70.67067), 0.0),
    'Wind Turbine: island_28_windfarm #10': ((123.317215, 13.815582, -209.23085), 0.0),
    'Wind Turbine: mega_island_10_4 #1': ((319.684418, 42.464626, 186.611542), 0.0),
    'Wind Turbine: mega_island_10_4 #2': ((310.479462, 21.872055, 42.733734), 0.0),
    'Wind Turbine: mega_island_10_4 #3': ((353.298676, 46.82024, 324.789612), 0.0),
    'Wind Turbine: mega_island_10_4 #4': ((396.4375, 21.872055, 78.739532), 0.0),
    'Wind Turbine: mega_island_10_4 #5': ((406.583618, 56.54837, 237.918823), 0.0),
    'Wind Turbine: mega_island_10_4 #6': ((476.861755, 42.293381, 194.248367), 0.0),
    'Wind Turbine: mega_island_11_4 #1': ((-400.914673, 21.650532, 15.577141), 0.0),
    'Wind Turbine: mega_island_11_4 #2': ((-387.839417, 21.873096, 148.159531), 0.0),
    'Wind Turbine: mega_island_11_4 #3': ((-417.92215, 43.155205, 352.140808), 0.0),
    'Wind Turbine: mega_island_11_4 #4': ((-487.37616, 46.563637, 462.104614), 0.0),
    'Radio Dish: island_15': ((-223.570114, 14.305422, 103.996918), 0.0),
    'Radio Dish: oil_rig': ((-3.713301, 16.605446, 3.044933), 116.449),
    'Radio Dish: test_tile': ((-35.93425, 47.484741, 9.051788), -162.941),
    'Subsea System Core: oil_rig': ((1.38139, -90.507401, 11.076), 0.0),
    'Subsea System Core: oil_rig_medium': ((1.133554, -90.041168, 8.35338), 0.0),
    'Subsea System: oil_rig #1': ((-9.801044, -90.504166, 33.387096), -90.0),
    'Subsea System: oil_rig #2': ((12.517651, -90.506973, 33.387096), -90.0),
    'Subsea System: oil_rig #3': ((-15.71883, -90.503372, 7.010174), 180.0),
    'Subsea System: oil_rig #4': ((19.099377, -90.50679, 7.602184), 0.0),
    'Subsea System: oil_rig_medium #1': ((18.847939, -90.041168, 4.878405), 0.0),
    'Subsea System: oil_rig_medium #2': ((-15.961479, -90.041168, 4.290148), 180.0),
    'Subsea System: oil_rig_medium #3': ((-10.052208, -90.041168, 30.625687), -90.0),
    'Subsea System: oil_rig_medium #4': ((12.273354, -90.041168, 30.638779), -90.0),
    # Arctic
    'Arctic Playerbase Bridge: arctic_tile_21': ((362.031525, 15.122282, 230.863602), -30.0),
    'Arctic Playerbase Bridge: mega_island_3_1': ((489.213928, 12.775476, 460.67038), 90.0),
    # Single-tile buildings (model placed on one tile only), grouped by tile
    # arctic_island_oil_refinery
    'Arctic Oil Refinery: arctic_island_oil_refinery': ((156.245239, 7.67, -60.045685), -135.0),
    'Arctic Oil Refinery Platform: arctic_island_oil_refinery': ((156.245239, 7.67, -60.045685), -135.0),
    'Arctic Oil Refinery Pipes: arctic_island_oil_refinery': ((156.245239, 7.67, -60.045685), -135.0),
    # arctic_island_playerbase
    'Arctic Island Playerbase Runway: arctic_island_playerbase': ((-147.980988, 23.338436, 64.044479), -42.0),
    # arctic_island_shipbreaking
    'Arctic Shipbreaking Yard: arctic_island_shipbreaking': ((83.352524, 8.84146, -143.725922), -47.5),
    'Arctic Shipbreaking Yard Buildings: arctic_island_shipbreaking': ((83.352524, 8.84146, -143.725922), -47.5),
    # arctic_island_survey
    'Arctic Island Survey Modules: arctic_island_survey': ((-96.30983, 21.890718, 6.065075), 180.0),
    'Arctic Island Survey Modules Science End: arctic_island_survey': ((-96.309998, 21.890718, 6.06), 180.0),
    'Arctic Island Survey Module Main: arctic_island_survey': ((-96.309998, 21.890718, 6.065), 180.0),
    'Arctic Island Survey Modules Science: arctic_island_survey': ((-96.309998, 21.890718, 6.06), 180.0),
    'Arctic Island Survey Module Bunks: arctic_island_survey': ((-96.30983, 21.890718, 6.065075), 180.0),
    'Arctic Island Survey Modules Science End Top: arctic_island_survey': ((-96.309998, 21.890718, 6.06), 180.0),
    # arctic_tile_12_oilrig
    'Arctic Tile 12 Oil Rig Base: arctic_tile_12_oilrig': ((166.733154, 2.650543, -29.132385), 180.0),
    'Arctic Tile 12 Oil Rig Storage: arctic_tile_12_oilrig': ((166.733154, 2.650543, -29.132385), 180.0),
    'Arctic Tile 12 Oil Rig Drill: arctic_tile_12_oilrig': ((166.733154, 2.650543, -29.132385), 180.0),
    'Arctic Tile 12 Oil Rig Building 01: arctic_tile_12_oilrig': ((166.733154, 2.650543, -29.132385), 180.0),
    'Arctic Tile 12 Oil Rig Building 02: arctic_tile_12_oilrig': ((166.733154, 2.650543, -29.132385), 180.0),
    # arctic_tile_22
    'Arctic Tile 22 Research Base: arctic_tile_22': ((-367.279327, 29.383263, -270.156372), 0.0),
    # arctic_tile_23
    'Arctic Tile 23 Fishing: arctic_tile_23': ((-212.485703, 6.644732, -173.836121), 90.0),
    'Arctic Tile 23 Fishing Cabins: arctic_tile_23': ((-212.485703, 6.644732, -173.836121), 90.0),
    # arid_island_10_6
    'Gold Lab: arid_island_10_6': ((-325.011963, 29.543676, -328.968872), 45.0),
    # arid_island_11_12
    'Animal Run: arid_island_11_12': ((465.092346, 15.546829, 74.235748), -45.0),
    'Livestock Large Barn: arid_island_11_12 #1': ((290.047089, 20.743816, -250.359344), 90.0),
    'Livestock Large Barn: arid_island_11_12 #2': ((290.665497, 20.737827, -237.312881), 0.0),
    'Livestock Barn Base: arid_island_11_12 #1': ((382.064423, 20.737827, -235.784317), -90.0),
    'Livestock Barn Base: arid_island_11_12 #2': ((363.883881, 20.737827, -235.784317), -90.0),
    # arid_island_11_14
    'Arid Mainland Train Terminal: arid_island_11_14': ((61.089828, 29.541222, -113.030212), -30.0),
    'Arid Warehouse: arid_island_11_14': ((308.368378, 29.616001, -119.102013), -3.0),
    # arid_island_12_10
    'Arctic Tile 22 Train Depot: arid_island_12_10': ((-161.63269, 46.86924, 324.087616), 93.5),
    # arid_island_13_10
    'Satellite Dish: arid_island_13_10': ((-383.980774, 88.467651, -269.272278), 0.0),
    'Satellite Dish Tower A: arid_island_13_10 #1': ((-115.044212, 73.209999, -0.335634), 40.0),
    'Satellite Dish Tower A: arid_island_13_10 #2': ((-115.044212, 73.209999, -0.335634), -50.0),
    'Satellite Dish Tower A: arid_island_13_10 #3': ((-115.044212, 73.211227, -0.335634), 130.0),
    'Satellite Dish Tower A: arid_island_13_10 #4': ((-115.044212, 73.209999, -0.335634), -140.0),
    # arid_island_13_6
    'Shipping Yard Shelf: arid_island_13_6 #1': ((-458.352905, 29.795494, -196.748795), 58.0),
    'Shipping Yard Shelf: arid_island_13_6 #2': ((-437.327789, 29.795494, -230.396042), 58.0),
    'Shipping Yard Shelf: arid_island_13_6 #3': ((-420.636871, 29.795494, -219.9664), 58.0),
    'Shipping Yard Shelf: arid_island_13_6 #4': ((-441.560242, 29.795494, -186.255569), 58.0),
    'Shipping Yard Shelf: arid_island_13_6 #5': ((-425.601868, 29.795494, -176.283661), 58.0),
    'Storage Container Office: arid_island_13_6': ((-407.131226, 29.904993, -205.009933), 58.0),
    'Storage Extra: arid_island_13_6 #1': ((-437.327789, 29.795494, -230.396042), 58.0),
    'Storage Extra: arid_island_13_6 #2': ((-441.560242, 29.795494, -186.255569), -122.0),
    # arid_island_15_5
    'Arid Gold Refining Plant: arid_island_15_5': ((-299.236938, 28.98, -161.49704), 2.5),
    # arid_island_16_10
    'Separator: arid_island_16_10': ((263.675201, 17.066013, -245.685333), 150.0),
    # arid_island_16_14
    'Coal Mine Shaft: arid_island_16_14': ((-330.424377, 136.912476, -267.592621), 0.0),
    # arid_island_17_4
    'Old Coal Building: arid_island_17_4 #1': ((-195.669449, 166.999344, 161.952957), 75.0),
    'Old Coal Building: arid_island_17_4 #2': ((-184.345596, 166.761581, 121.049461), 75.0),
    # arid_island_19_5
    'Steelmill Furnace: arid_island_19_5': ((88.012741, 2.540588, -121.061913), 0.0),
    'Steelmill Building: arid_island_19_5': ((-108.446815, 2.540588, -122.448555), 0.0),
    'Steelmill Pipes: arid_island_19_5': ((-67.370407, 2.434968, 0.401737), 0.0),
    # arid_island_23_14
    # arid_island_26_14
    'Arid Mainland Drydock: arid_island_26_14': ((376.85788, 8.6347, -283.182861), 165.0),
    'Arid Mainland Drydock Rails: arid_island_26_14': ((376.85788, 8.634335, -283.182861), 165.0),
    'Arid Mainland Drydock Cover: arid_island_26_14': ((376.85788, 8.634335, -283.182861), 165.0),
    'Arid Mainland Drydock Cover Rails: arid_island_26_14 #1': ((323.447693, 8.188969, 64.904907), 165.0),
    'Arid Mainland Drydock Cover Rails: arid_island_26_14 #2': ((285.999451, 8.188969, -125.801506), -15.0),
    'Arid Mainland Drydock Rails B: arid_island_26_14': ((376.85788, 8.634335, -283.182861), 165.0),
    'Arid Runway: arid_island_26_14': ((-210.802505, 8.631, -632.515747), -105.0),
    # arid_island_4_12
    'Arid Buildings House F: arid_island_4_12': ((169.546722, 15.686121, 283.701569), 40.0),
    # arid_island_4_14
    'Ford Bridge: arid_island_4_14': ((-408.263611, -5.02967, -262.695282), -35.0),
    # arid_island_6_7
    'Arid Mainland Train Terminal Small: arid_island_6_7': ((41.994267, 67.392487, -442.533966), -152.0),
    'Arid Mainland Train Terminal Single: arid_island_6_7 #1': ((173.387589, 67.668991, -461.833588), -154.0),
    'Arid Mainland Train Terminal Single: arid_island_6_7 #2': ((164.715622, 67.668991, -479.61377), -154.0),
    # arid_island_7_7
    'Arid Buildings Deserted: arid_island_7_7': ((-421.269104, 173.012161, -96.400742), 0.0),
    # arid_island_8_13
    'Nuclear Storage Yard: arid_island_8_13': ((-400.689056, 71.485161, -340.878845), 0.0),
    'Nuclear Storage Yard B: arid_island_8_13': ((-400.689056, 71.485161, -340.878845), 0.0),
    'Nuclear Storage Yard Buildings: arid_island_8_13': ((-400.689056, 71.485161, -340.878845), 0.0),
    'Nuclear Storage Yard Buildings B: arid_island_8_13': ((-400.689056, 71.485161, -340.878845), 0.0),
    'Nuclear Storage Yard Buildings C: arid_island_8_13': ((-400.689056, 71.485161, -340.878845), 0.0),
    # arid_island_8_14
    'Nuclear Plant Buildings: arid_island_8_14': ((-129.546585, 3.369868, 296.498718), 0.0),
    'Nuclear Plant Reactor: arid_island_8_14': ((-5.464652, 7.729352, 338.738129), 0.0),
    'Nuclear Plant Turbine: arid_island_8_14': ((-8.375053, 1.575828, 309.645416), 0.0),
    'Nuclear Plant Reactor Room: arid_island_8_14': ((-9.126102, 44.775131, 355.022522), 0.0),
    'Nuclear Plant Reactor Room B: arid_island_8_14': ((-9.126102, 44.80809, 355.022522), 0.0),
    'Nuclear Plant Stairs: arid_island_8_14': ((-129.546585, 3.369868, 296.498718), 0.0),
    'Nuclear Plant Stairs B: arid_island_8_14': ((-129.546585, 3.369868, 296.498718), 0.0),
    'Nuclear Plant Entryways: arid_island_8_14': ((-129.546585, 3.369868, 296.498718), 0.0),
    'Nuclear Plant Coolingtower: arid_island_8_14 #1': ((-121.72657, 3.369868, -39.041382), 0.0),
    'Nuclear Plant Coolingtower: arid_island_8_14 #2': ((-383.568329, 3.369868, -39.041382), 0.0),
    'Nuclear Outsidearea: arid_island_8_14': ((-386.374969, 0.957879, 300.219635), 0.0),
    'Nuclear Substation: arid_island_8_14': ((-295.619293, 8.33379, 297.457855), 0.0),
    'Nuclear Substation B: arid_island_8_14': ((-295.619293, 8.33379, 297.457855), 0.0),
    'Nuclear Substation C: arid_island_8_14': ((-295.619293, 8.33379, 297.457855), 0.0),
    'Nuclear Plant Reactor Walkway: arid_island_8_14': ((-5.557814, 7.729352, 338.718018), 0.0),
    'Centrifuge: arid_island_8_14': ((330.101807, 8.061535, 247.867142), 0.0),
    # arid_island_8_15
    'Nuclear Dock: arid_island_8_15': ((-499.66568, -73.316208, -450.15155), 0.0),
    'Nuclear Outsidearea B: arid_island_8_15': ((-282.214355, 8.361946, -450.15155), 0.0),
    'Nuclear Dock Assets: arid_island_8_15': ((-499.66568, -73.316208, -450.15155), 0.0),
    # island12
    'Island 12 Cottage: island12': ((-32.083038, 3.445757, 1.97864), 0.0),
    # island_13
    'Island 13 Building: island_13': ((39.156616, 17.973877, -23.087402), 0.0),
    # island_15
    'Ultimate Base Buildings: island_15': ((-226.165894, 4.654706, -93.274261), 0.0),
    'Ultimate Base Control: island_15': ((-236.597916, 4.66, -96.204704), 0.0),
    # island_17
    'Island 17 Research Facility: island_17': ((65.825577, 19.100937, 27.075842), 179.645),
    # island_18
    'Island 18 Tower: island_18': ((-28.628555, 1.702324, -303.964264), 0.0),
    'Island 18 Dock: island_18': ((49.948166, 4.936394, 106.635429), -179.991),
    'Island 18 Lift: island_18': ((46.318359, 5.014287, 108.131622), 180.0),
    'Island 18 Dock Control: island_18': ((49.871826, 4.914306, 106.609772), 180.0),
    'Island 18 Buildings: island_18': ((45.799999, 0.621559, 114.875198), 180.0),
    'Island 18 Reactor: island_18': ((45.869999, 0.61, 114.889984), 180.0),
    'Island 18 Substation: island_18': ((130.879211, 1.014404, -87.37677), -90.0),
    'Island 18 Transformers: island_18': ((130.969635, 1.014404, -87.3703), -90.0),
    'Island 18 Turbine: island_18': ((45.84, 0.62, 114.889999), 180.0),
    # island_24
    'Island 24 Runway: island_24': ((-44.901726, 5.011811, -64.533058), 0.0),
    'Island 24 Control Tower: island_24': ((-44.905128, 5.01, -64.529999), 0.0),
    'Island 24 Control Tower Top: island_24': ((-44.905128, 5.01, -64.529999), 0.0),
    # island_25
    'Island 25 Boatyard: island_25': ((13.7789, 5.2435, -63.73), 0.0),
    'Island 25 Buildings: island_25': ((13.785385, 5.24, -63.73), 0.0),
    # island_27_airbase
    'Island 27 Runway: island_27_airbase': ((99.733597, 23.504456, -227.302948), 0.0),
    # island_3
    'Island 03 Hanger: island_3': ((-48.0, 9.419373, -167.0), 0.0),
    'Island 03 Runway: island_3': ((-48.0, 9.42, -167.0), 0.0),
    'Island 03 Tower: island_3': ((-48.0, 9.42, -167.0), 0.0),
    'Drop Off Tent: island_3': ((-94.001343, 11.06958, 86.95047), 0.0),
    # island_33_tile_05
    'Island 33 Hol Cottage: island_33_tile_05': ((-244.138885, 9.588725, 56.069023), -142.883),
    # island_33_tile_06
    'Island 33 06 Industrial: island_33_tile_06': ((-321.082245, 7.6623, 304.625946), 90.0),
    'Island 33 06 Industrial 02: island_33_tile_06': ((-321.082245, 7.6623, 304.625946), 90.0),
    # island_33_tile_07
    'Island 33 Lighthouse: island_33_tile_07': ((218.636307, 18.434042, 26.512835), -160.0),
    'Island 33 Lighthouse Cottage: island_33_tile_07': ((229.67366, 13.227865, 80.689468), 160.0),
    # island_34_military
    'Island 34 Runways: island_34_military': ((-113.010406, 22.111389, -143.182739), 31.585),
    'Island 34 Militaryhangar: island_34_military': ((85.664871, 22.111784, -28.670349), -58.0),
    'Island 34 Control Building: island_34_military': ((-173.057541, 21.968262, -82.549744), 117.116),
    'Island 34 Bunks: island_34_military #1': ((-58.283951, 21.93985, 56.898224), 30.929),
    'Island 34 Bunks: island_34_military #2': ((-68.768204, 21.93985, 39.400391), 30.929),
    'Island 34 Bunks: island_34_military #3': ((-29.497971, 21.93985, 75.428848), -149.07),
    'Island 34 Bunks: island_34_military #4': ((-47.1371, 21.93985, 75.501923), 30.929),
    'Island 34 Bunks: island_34_military #5': ((-40.534164, 21.939848, 56.900002), -149.07),
    'Island 34 Bunks: island_34_military #6': ((-51.140579, 21.939846, 39.400002), -149.07),
    'Island 34 Towers: island_34_military': ((-98.325714, 22.111511, 49.949677), 24.981),
    # island_35_seafort
    'Island 35 Seafort: island_35_seafort': ((-74.97821, 12.81885, -9.128805), 0.0),
    'Island 35 Seafort Tower: island_35_seafort': ((-74.97821, 12.81885, -9.128805), 0.0),
    # island_36_oil_refinery
    'Island 36 Dock: island_36_oil_refinery': ((-51.75666, 4.175196, -81.529831), 0.0),
    'Island 36 Refinery: island_36_oil_refinery': ((-43.357651, 20.685337, 23.029497), 138.155),
    'Island 36 Refinery Base: island_36_oil_refinery': ((-43.357651, 20.685337, 23.029497), 138.155),
    'Island 36 Refinery Towers: island_36_oil_refinery': ((-43.357651, 20.685337, 23.029497), 138.155),
    'Island 36 Refinery Floors: island_36_oil_refinery': ((-43.357651, 20.685337, 23.029497), 138.155),
    # island_39_observatory
    'Island 39 Observatory: island_39_observatory': ((37.540295, 7.849243, 37.123482), -123.902),
    # island_40_castle_tourism
    'Island 40 Castle: island_40_castle_tourism': ((19.848846, 15.046509, -3.773803), 56.728),
    # island_41_underwater_mining
    'Island 41 Underwater Mining Base: island_41_underwater_mining': ((-69.545425, 6.770912, -49.234333), 0.0),
    'Island 41 Underwater Mining Building: island_41_underwater_mining': ((-69.545425, 6.770912, -49.234333), 0.0),
    'Island 41 Underwater Mining Control: island_41_underwater_mining': ((-69.545425, 6.77, -49.234333), 0.0),
    'Island 41 Underwater Mining Machinery: island_41_underwater_mining': ((-69.545425, 6.770912, -49.234333), 0.0),
    'Uranium Refining 4: island_41_underwater_mining': ((-11.928102, 4.712827, -15.301921), 0.0),
    # island_43_multiplayer_base
    'Island 43 Multiplayer Dock: island_43_multiplayer_base': ((60.71703, 7.35, -54.833088), 45.0),
    'Island 43 Multiplayer Hangar: island_43_multiplayer_base': ((-130.965271, 13.856232, 41.040447), 45.0),
    'Island 43 Multiplayer Building: island_43_multiplayer_base': ((-130.965271, 13.856232, 41.040447), 45.0),
    # mega_island_10_7
    'Grain Silo: mega_island_10_7': ((-99.601997, 7.423017, 203.345642), 0.0),
    'Grain Storage: mega_island_10_7': ((-135.423965, 7.423017, 243.622223), 90.0),
    # mega_island_12_7
    'Mainland Train Terminal Small: mega_island_12_7': ((-231.140823, 2.996868, -439.395233), -90.0),
    # mega_island_5_2
    'Sawmill: mega_island_5_2': ((407.206329, 6.32924, 499.486389), 90.0),
    # mega_island_8_7
    'Mainland Quayside: mega_island_8_7': ((77.506142, 2.50695, 120.229919), 105.0),
    # oil_rig
    'Oil Rig: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Control Room: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Derrick: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Drill: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Flare: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Helipad: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Platform: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    'Oil Rig Stairs: oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),
    # oil_rig_medium
    'Oil Rig Medium Platform: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Derrick: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Accommodation: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Acc 02: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Acc Stairs: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Deck 01: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Deck 02: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Deck 02 Building: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    'Oil Rig Medium Derrick Platform: oil_rig_medium': ((2.139901, 1.611443, -7.843423), 0.0),
    # oil_rig_playerbase
    'Oil Rig Playerbase: oil_rig_playerbase': ((0.0, -10.480804, 0.0), 0.0),
    # seabed_shipwreck
    'Seabed Shipwreck: seabed_shipwreck': ((0.0, -82.667358, 0.0), 0.0),
    # seabed_shipwreck_02
    'Seabed Shipwreck 02: seabed_shipwreck_02': ((0.0, -83.115601, 0.0), 0.0),
    # volcanic_5_7
    'Planewreck: volcanic_5_7': ((-71.316017, -142.521713, 189.678513), 0.0),
    # volcanic_6_7
    'Ancient Greek Temple B: volcanic_6_7 #2': ((410.816223, -83.245895, 201.971848), 180.0),
    'Ancient Greek Parts C: volcanic_6_7': ((131.227036, -85.726822, 196.388168), 0.0),
    # volcanic_7_5
    'Shipwreck Mid: volcanic_7_5': ((-165.018707, -136.593796, 159.046494), 40.0),
    'Shipwreck Front: volcanic_7_5': ((-165.018707, -136.593796, 159.046494), 40.0),
    # wind_turbine
    'Wind Turbine: wind_turbine': ((-1.168854, 20.350372, 0.0), 0.0),
    'Wind Turbine Helipad: wind_turbine': ((-1.189514, 20.347076, 0.0), 0.0),
}


# Ground (terrain) mesh placement per tile. The tile's island/ground mesh and its ground physics
# mesh carry their own transform, and building pivots above are in tile space AFTER that offset.
# E.g. island12: island_12.mesh is drawn 6.485 m below 0. Draw the ground mesh with
#   rotate_point(p_mesh, *ground_offset(tile))
# Tiles not listed here place their ground mesh at the origin with no rotation.
# Multi-tile islands (arctic_tile_*, island_33_tile_*, island_42_volcano_tile_*) share one big
# mesh, shifted by whole kilometres into each tile's space.
GROUND = {
    'arctic_island_playerbase': ((2000.0, 0.0, -1000.0), 0.0),  # meshes/arctic_island_playerbase.mesh
    'arctic_island_survey': ((0.0, 2.514308, 0.0), 0.0),  # meshes/arctic_island_survey.mesh
    'arctic_tile_11': ((1000.0, 0.0, -1000.0), 0.0),  # meshes/arctic_tile_11.mesh
    'arctic_tile_12_oilrig': ((0.0, 0.0, -1000.0), 0.0),  # meshes/arctic_tile_12.mesh
    'arctic_tile_13': ((-1000.0, 0.0, -1000.0), 0.0),  # meshes/arctic_tile_13.mesh
    'arctic_tile_21': ((1000.0, 0.0, 0.0), 0.0),  # meshes/arctic_tile_21.mesh
    'arctic_tile_23': ((-1000.0, 0.0, 0.0), 0.0),  # meshes/arctic_tile_23.mesh
    'arctic_tile_31': ((1000.0, 0.0, 1000.0), 0.0),  # meshes/arctic_tile_31.mesh
    'arctic_tile_32': ((0.0, 0.0, 1000.0), 0.0),  # meshes/arctic_tile_32.mesh
    'arctic_tile_33': ((-1000.0, 0.0, 1000.0), 0.0),  # meshes/arctic_tile_33.mesh
    'arid_04': ((-8.875051, 5.141699, -3.448028), 0.0),  # meshes/arid_mainland_assets/arid_islands/arid_island_04.mesh
    'arid_13': ((0.0, 4.358292, 0.0), 0.0),  # meshes/arid_mainland_assets/arid_islands/arid_island_13.mesh
    'ice_shelf_01': ((15.911325, 1.196686, -14.13931), 0.0),  # meshes/arctic_ice_shelf_01.mesh
    'ice_shelf_01_rot_0': ((15.911325, 1.196686, -14.13931), 0.0),  # meshes/arctic_ice_shelf_01.mesh
    'ice_shelf_01_rot_1': ((-14.139311, 1.196686, -15.911324), 90.0),  # meshes/arctic_ice_shelf_01.mesh
    'ice_shelf_01_rot_2': ((-15.911324, 1.196686, 14.139311), 180.0),  # meshes/arctic_ice_shelf_01.mesh
    'ice_shelf_01_rot_3': ((14.13931, 1.196686, 15.911325), -90.0),  # meshes/arctic_ice_shelf_01.mesh
    'ice_shelf_02': ((-2.748169, -13.215759, 0.0), 0.0),  # meshes/arctic_ice_shelf_02.mesh
    'ice_shelf_02_rot_0': ((-2.748169, -13.215759, 0.0), 0.0),  # meshes/arctic_ice_shelf_02.mesh
    'ice_shelf_02_rot_1': ((0.0, -13.215759, 2.748169), 90.0),  # meshes/arctic_ice_shelf_02.mesh
    'ice_shelf_02_rot_2': ((2.748169, -13.215759, 0.0), 180.0),  # meshes/arctic_ice_shelf_02.mesh
    'ice_shelf_02_rot_3': ((0.0, -13.215759, -2.748169), -90.0),  # meshes/arctic_ice_shelf_02.mesh
    'ice_shelf_03': ((-42.583279, -7.157207, 0.736198), 0.0),  # meshes/arctic_ice_shelf_03.mesh
    'ice_shelf_03_rot_0': ((-42.583279, -7.157207, 0.736198), 0.0),  # meshes/arctic_ice_shelf_03.mesh
    'ice_shelf_03_rot_1': ((0.7362, -7.157207, 42.583279), 90.0),  # meshes/arctic_ice_shelf_03.mesh
    'ice_shelf_03_rot_2': ((42.583279, -7.157207, -0.736202), 180.0),  # meshes/arctic_ice_shelf_03.mesh
    'ice_shelf_03_rot_3': ((-0.736199, -7.157207, -42.583279), -90.0),  # meshes/arctic_ice_shelf_03.mesh
    'ice_shelf_04': ((73.958954, -1.373002, 23.819778), 0.0),  # meshes/arctic_ice_shelf_04.mesh
    'ice_shelf_04_rot_0': ((73.958954, -1.373002, 23.819778), 0.0),  # meshes/arctic_ice_shelf_04.mesh
    'ice_shelf_04_rot_1': ((23.819775, -1.373002, -73.958955), 90.0),  # meshes/arctic_ice_shelf_04.mesh
    'ice_shelf_04_rot_2': ((-73.958956, -1.373002, -23.819772), 180.0),  # meshes/arctic_ice_shelf_04.mesh
    'ice_shelf_04_rot_3': ((-23.819777, -1.373002, 73.958954), -90.0),  # meshes/arctic_ice_shelf_04.mesh
    'ice_shelf_05': ((-12.185305, -3.712941, -9.096939), 0.0),  # meshes/arctic_ice_shelf_05.mesh
    'ice_shelf_05_rot_0': ((-12.185305, -3.712941, -9.096939), 0.0),  # meshes/arctic_ice_shelf_05.mesh
    'ice_shelf_05_rot_1': ((-9.096938, -3.712941, 12.185305), 90.0),  # meshes/arctic_ice_shelf_05.mesh
    'ice_shelf_05_rot_2': ((12.185306, -3.712941, 9.096938), 180.0),  # meshes/arctic_ice_shelf_05.mesh
    'ice_shelf_05_rot_3': ((9.096939, -3.712941, -12.185305), -90.0),  # meshes/arctic_ice_shelf_05.mesh
    'ice_shelf_06': ((0.0, 98.502502, 0.0), 0.0),  # meshes/arctic_ice_shelf_06.mesh
    'ice_shelf_06_rot_0': ((0.0, 98.502502, 0.0), 0.0),  # meshes/arctic_ice_shelf_06.mesh
    'ice_shelf_06_rot_1': ((0.0, 98.502502, 0.0), 90.0),  # meshes/arctic_ice_shelf_06.mesh
    'ice_shelf_06_rot_2': ((0.0, 98.502502, 0.0), 180.0),  # meshes/arctic_ice_shelf_06.mesh
    'ice_shelf_06_rot_3': ((0.0, 98.502502, 0.0), -90.0),  # meshes/arctic_ice_shelf_06.mesh
    'ice_shelf_07': ((0.0, -9.76825, 0.0), 0.0),  # meshes/arctic_ice_shelf_07.mesh
    'ice_shelf_07_rot_0': ((0.0, -9.76825, 0.0), 0.0),  # meshes/arctic_ice_shelf_07.mesh
    'ice_shelf_07_rot_1': ((0.0, -9.76825, 0.0), 90.0),  # meshes/arctic_ice_shelf_07.mesh
    'ice_shelf_07_rot_2': ((0.0, -9.76825, 0.0), 180.0),  # meshes/arctic_ice_shelf_07.mesh
    'ice_shelf_07_rot_3': ((0.0, -9.76825, 0.0), -90.0),  # meshes/arctic_ice_shelf_07.mesh
    'ice_shelf_08': ((0.0, 42.578094, 0.0), 0.0),  # meshes/arctic_ice_shelf_08.mesh
    'ice_shelf_08_rot_0': ((0.0, 42.578094, 0.0), 0.0),  # meshes/arctic_ice_shelf_08.mesh
    'ice_shelf_08_rot_1': ((0.0, 42.578094, 0.0), 90.0),  # meshes/arctic_ice_shelf_08.mesh
    'ice_shelf_08_rot_2': ((0.0, 42.578094, 0.0), 180.0),  # meshes/arctic_ice_shelf_08.mesh
    'ice_shelf_08_rot_3': ((0.0, 42.578094, 0.0), -90.0),  # meshes/arctic_ice_shelf_08.mesh
    'ice_shelf_09': ((0.0, -3.654663, 0.0), 0.0),  # meshes/arctic_ice_shelf_09.mesh
    'ice_shelf_09_rot_0': ((0.0, -3.654663, 0.0), 0.0),  # meshes/arctic_ice_shelf_09.mesh
    'ice_shelf_09_rot_1': ((0.0, -3.654663, 0.0), 90.0),  # meshes/arctic_ice_shelf_09.mesh
    'ice_shelf_09_rot_2': ((0.0, -3.654663, 0.0), 180.0),  # meshes/arctic_ice_shelf_09.mesh
    'ice_shelf_09_rot_3': ((0.0, -3.654663, 0.0), -90.0),  # meshes/arctic_ice_shelf_09.mesh
    'ice_shelf_10': ((-43.083244, -2.272047, -43.206367), 0.0),  # meshes/arctic_ice_shelf_10.mesh
    'ice_shelf_10_rot_0': ((-43.083244, -2.272047, -43.206367), 0.0),  # meshes/arctic_ice_shelf_10.mesh
    'ice_shelf_10_rot_1': ((-43.206365, -2.272047, 43.083246), 90.0),  # meshes/arctic_ice_shelf_10.mesh
    'ice_shelf_10_rot_2': ((43.083248, -2.272047, 43.206363), 180.0),  # meshes/arctic_ice_shelf_10.mesh
    'ice_shelf_10_rot_3': ((43.206366, -2.272047, -43.083245), -90.0),  # meshes/arctic_ice_shelf_10.mesh
    'ice_shelf_11': ((0.0, 54.092712, 0.0), 0.0),  # meshes/arctic_ice_shelf_11.mesh
    'ice_shelf_11_rot_0': ((0.0, 54.092712, 0.0), 0.0),  # meshes/arctic_ice_shelf_11.mesh
    'ice_shelf_11_rot_1': ((0.0, 54.092712, 0.0), 90.0),  # meshes/arctic_ice_shelf_11.mesh
    'ice_shelf_11_rot_2': ((0.0, 54.092712, 0.0), 180.0),  # meshes/arctic_ice_shelf_11.mesh
    'ice_shelf_11_rot_3': ((0.0, 54.092712, 0.0), -90.0),  # meshes/arctic_ice_shelf_11.mesh
    'ice_shelf_12': ((0.0, 47.152893, 0.0), 0.0),  # meshes/arctic_ice_shelf_12.mesh
    'ice_shelf_12_rot_0': ((0.0, 47.152893, 0.0), 0.0),  # meshes/arctic_ice_shelf_12.mesh
    'ice_shelf_12_rot_1': ((0.0, 47.152893, 0.0), 90.0),  # meshes/arctic_ice_shelf_12.mesh
    'ice_shelf_12_rot_2': ((0.0, 47.152893, 0.0), 180.0),  # meshes/arctic_ice_shelf_12.mesh
    'ice_shelf_12_rot_3': ((0.0, 47.152893, 0.0), -90.0),  # meshes/arctic_ice_shelf_12.mesh
    'island11': ((0.0, -1.766724, 0.0), 0.0),  # meshes/island_11.mesh
    'island12': ((0.0, -6.485474, 0.0), 0.0),  # meshes/island_12.mesh
    'island_13': ((0.0, -5.716156, 0.0), 0.0),  # meshes/island_13.mesh
    'island_14': ((0.0, -4.292084, 0.0), 0.0),  # meshes/island_14.mesh
    'island_15': ((-228.539993, -5.2, -65.550003), 0.0),  # meshes/island_15.mesh
    'island_17': ((0.0, -2.13, 0.0), 0.0),  # meshes/island_17.mesh
    'island_18': ((0.0, -2.628662, 0.0), 0.0),  # meshes/island_18.mesh
    'island_2': ((0.0, -10.0, -30.0), 0.0),  # meshes/island_02.mesh
    'island_22': ((0.0, -1.285553, 0.0), 0.0),  # meshes/island_22.mesh
    'island_23': ((0.0, -0.717804, 0.0), 0.0),  # meshes/island_23.mesh
    'island_24': ((0.0, -3.149536, 0.0), 0.0),  # meshes/island_24.mesh
    'island_25': ((0.0, -7.765717, 0.0), 0.0),  # meshes/island_25.mesh
    'island_26_fishing': ((0.0, -1.90271, 0.0), 0.0),  # meshes/island_26_fishing.mesh
    'island_28_windfarm': ((-25.723804, 0.0, -17.995771), 0.0),  # meshes/island_28_windfarm.mesh
    'island_3': ((0.0, -11.0, 0.0), 0.0),  # meshes/island_03.mesh
    'island_33_tile_03': ((-1000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_03.mesh
    'island_33_tile_04': ((-2000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_04.mesh
    'island_33_tile_05': ((-3000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_05.mesh
    'island_33_tile_06': ((-4000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_06.mesh
    'island_33_tile_07': ((-5000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_07.mesh
    'island_33_tile_08': ((-6000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_08.mesh
    'island_33_tile_09': ((-7000.0, 0.0, -2000.0), 0.0),  # meshes/island_33_tile_09.mesh
    'island_33_tile_11': ((1000.0, 0.0, -1000.0), 0.0),  # meshes/island_33_tile_11.mesh
    'island_33_tile_12': ((0.0, 0.0, -1000.0), 0.0),  # meshes/island_33_tile_12.mesh
    'island_33_tile_13': ((-1000.0, 0.0, -1000.0), 0.0),  # meshes/island_33_tile_13.mesh
    'island_33_tile_21': ((1000.0, 0.0, 0.0), 0.0),  # meshes/island_33_tile_21.mesh
    'island_33_tile_23': ((-1000.0, 0.0, 0.0), 0.0),  # meshes/island_33_tile_23.mesh
    'island_33_tile_31': ((1000.0, 0.0, 1000.0), 0.0),  # meshes/island_33_tile_31.mesh
    'island_33_tile_32': ((0.0, 0.0, 1000.0), 0.0),  # meshes/island_33_tile_32.mesh
    'island_33_tile_33': ((-1000.0, 0.0, 1000.0), 0.0),  # meshes/island_33_tile_33.mesh
    'island_33_tile_end': ((-7000.0, 0.0, -1000.0), 0.0),  # meshes/island_33_tile_end.mesh
    'island_33_tile_end_1': ((-8000.0, 0.0, -1000.0), 0.0),  # meshes/island_33_tile_end_1.mesh
    'island_33_tile_end_2': ((-8000.0, 0.0, 0.0), 0.0),  # meshes/island_33_tile_end_2.mesh
    'island_34_military': ((-17.326813, 0.294007, -20.327866), 0.0),  # meshes/island_34_military.mesh
    'island_35_seafort': ((-34.094116, 0.240053, -8.562216), 0.0),  # meshes/island_35.mesh
    'island_36_oil_refinery': ((0.0, -1.638, 0.0), 0.0),  # meshes/island_36_oil_refinery.mesh
    'island_38_lighthouse': ((0.0, 3.016907, 0.0), 0.0),  # meshes/island_38_lighthouse.mesh
    'island_4': ((-21.725525, 8.608276, 93.378479), 0.0),  # meshes/island_04.mesh
    'island_41_underwater_mining': ((0.0, -2.511261, 0.0), 0.0),  # meshes/island_41_underwater_mining.mesh
    'island_42_volcano_tile_11': ((1000.0, 0.0, -1000.0), 0.0),  # meshes/island_42_volcano_tile_11.mesh
    'island_42_volcano_tile_12': ((0.0, 0.0, -1000.0), 0.0),  # meshes/island_42_volcano_tile_12.mesh
    'island_42_volcano_tile_13': ((-1000.0, 0.0, -1000.0), 0.0),  # meshes/island_42_volcano_tile_13.mesh
    'island_42_volcano_tile_21': ((1000.0, 0.0, 0.0), 0.0),  # meshes/island_42_volcano_tile_21.mesh
    'island_42_volcano_tile_23': ((-1000.0, 0.0, 0.0), 0.0),  # meshes/island_42_volcano_tile_23.mesh
    'island_42_volcano_tile_31': ((1000.0, 0.0, 1000.0), 0.0),  # meshes/island_42_volcano_tile_31.mesh
    'island_42_volcano_tile_32': ((0.0, 0.0, 1000.0), 0.0),  # meshes/island_42_volcano_tile_32.mesh
    'island_42_volcano_tile_33': ((-1000.0, 0.0, 1000.0), 0.0),  # meshes/island_42_volcano_tile_33.mesh
    'oil_rig': ((-0.477882, -1.221771, -0.79731), 0.0),  # meshes/oil_rig.mesh
    'oil_rig_medium': ((1.133554, -90.041168, 8.35338), 0.0),  # meshes/seabed_subsea_system_core.mesh
    'oil_rig_playerbase': ((0.0, -10.480804, 0.0), 0.0),  # meshes/oil_rig_playerbase.mesh
    'seabed_cave_system': ((0.0, -76.173004, 0.0), 0.0),  # meshes/seabed_cave_system.mesh
    'seabed_island': ((0.0, -82.800842, 0.0), 90.0),  # meshes/seabed_island.mesh
    'seabed_island_14': ((0.0, -88.412201, 0.0), 90.0),  # meshes/seabed_island_14.mesh
    'seabed_island_19': ((0.0, -80.855347, 0.0), -90.0),  # meshes/seabed_island_19.mesh
    'seabed_island_20': ((0.0, -84.076416, 0.0), 180.0),  # meshes/seabed_island_20.mesh
    'seabed_island_21': ((0.0, -76.510132, 0.0), 90.0),  # meshes/seabed_island_21.mesh
    'seabed_island_22': ((0.0, -84.959747, 0.0), 90.0),  # meshes/seabed_island_22.mesh
    'seabed_island_23': ((0.0, -85.705322, 0.0), 180.0),  # meshes/seabed_island_23.mesh
    'seabed_island_38': ((0.0, -74.647522, 0.0), -90.0),  # meshes/seabed_island_38.mesh
    'seabed_shipwreck': ((0.0, -82.667358, 0.0), 0.0),  # meshes/seabed_shipwreck.mesh
    'seabed_shipwreck_02': ((0.0, -83.115601, 0.0), 0.0),  # meshes/seabed_shipwreck_02.mesh
    'track_curve_left_diagonal_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_curve_left_diagonal.mesh
    'track_curve_left_diagonal_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_curve_left_diagonal.mesh
    'track_curve_left_diagonal_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_curve_left_diagonal.mesh
    'track_curve_right_diagonal_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_curve_right_diagonal.mesh
    'track_curve_right_diagonal_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_curve_right_diagonal.mesh
    'track_curve_right_diagonal_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_curve_right_diagonal.mesh
    'track_curve_right_diagonal_variant_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_curve_right_diagonal_variant.mesh
    'track_curve_right_diagonal_variant_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_curve_right_diagonal_variant.mesh
    'track_curve_right_diagonal_variant_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_curve_right_diagonal_variant.mesh
    'track_diagonal_left_fork_straight_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_diagonal_left_fork_straight.mesh
    'track_diagonal_left_fork_straight_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_diagonal_left_fork_straight.mesh
    'track_diagonal_left_fork_straight_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_diagonal_left_fork_straight.mesh
    'track_diagonal_right_fork_straight_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_diagonal_right_fork_straight.mesh
    'track_diagonal_right_fork_straight_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_diagonal_right_fork_straight.mesh
    'track_diagonal_right_fork_straight_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_diagonal_right_fork_straight.mesh
    'track_diagonal_variant_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_diagonal_variant.mesh
    'track_diagonal_variant_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_diagonal_variant.mesh
    'track_diagonal_variant_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_diagonal_variant.mesh
    'track_straight_fork_left_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_straight_fork_left.mesh
    'track_straight_fork_left_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_straight_fork_left.mesh
    'track_straight_fork_left_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_straight_fork_left.mesh
    'track_straight_fork_right_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_straight_fork_right.mesh
    'track_straight_fork_right_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_straight_fork_right.mesh
    'track_straight_fork_right_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_straight_fork_right.mesh
    'track_straight_variant_rot_1': ((0.0, 0.0, 0.0), 90.0),  # meshes/track_pieces/track_straight_variant.mesh
    'track_straight_variant_rot_2': ((0.0, 0.0, 0.0), 180.0),  # meshes/track_pieces/track_straight_variant.mesh
    'track_straight_variant_rot_3': ((0.0, 0.0, 0.0), -90.0),  # meshes/track_pieces/track_straight_variant.mesh
    'wind_turbine': ((-1.168854, 20.350372, 0.0), 0.0),  # meshes/wind_turbine.mesh
}