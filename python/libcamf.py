#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# libcamf.py: Common Alert Message Format (CAMF) tables and decoder
# A part of QZS L6 Tool, https://github.com/yoronneko/qzsl6tool
#
# Copyright (c) 2026 Satoshi Takahashi, all rights reserved.
#
# Released under BSD 2-clause license.
#
# References:
# [1] European Union, Emergency Warning Satellite Service Common Alert Message Format Specification, Issue 1.0, Jan. 2024.
#     Source: Common Alert Message Format Specification. (c) European Union/Japan Cabinet Office, 2023

from bitstring import BitStream

# ---- A1 message type, ref.[1] Annex C.1
MSG_TYPE: dict[int, str] = {0: 'Test', 1: 'Alert', 2: 'Update', 3: 'All Clear'}

# ---- A2 country/region name, ref.[1] Annex C.2 (ISO 3166 based)
COUNTRY: dict[int, str] = {
      0: 'Afghanistan', 1: 'Albania', 2: 'Antarctica', 3: 'Algeria', 4: 'American Samoa',
      5: 'Andorra', 6: 'Angola', 7: 'Antigua and Barbuda', 8: 'Azerbaijan', 9: 'Argentina',
     10: 'Australia', 11: 'Austria', 12: 'Bahamas', 13: 'Bahrain', 14: 'Bangladesh',
     15: 'Armenia', 16: 'Barbados', 17: 'Belgium', 18: 'Bermuda', 19: 'Bhutan',
     20: 'Bolivia', 21: 'Bosnia and Herzegovina', 22: 'Botswana', 23: 'Bouvet Island', 24: 'Brazil',
     25: 'Belize', 26: 'British Indian Ocean Territory', 27: 'Solomon Islands', 28: 'Virgin Islands (British)', 29: 'Brunei Darussalam',
     30: 'Bulgaria', 31: 'Myanmar', 32: 'Burundi', 33: 'Belarus', 34: 'Cambodia',
     35: 'Cameroon', 36: 'Canada', 37: 'Cabo Verde', 38: 'Cayman Islands', 39: 'Central African Republic',
     40: 'Sri Lanka', 41: 'Chad', 42: 'Chile', 43: 'China', 44: 'Taiwan',
     45: 'Christmas Island', 46: 'Cocos (Keeling) Islands', 47: 'Colombia', 48: 'Comoros', 49: 'Mayotte',
     50: 'Congo', 51: 'Congo (Democratic Republic)', 52: 'Cook Islands', 53: 'Costa Rica', 54: 'Croatia',
     55: 'Cuba', 56: 'Cyprus', 57: 'Czechia', 58: 'Benin', 59: 'Denmark',
     60: 'Dominica', 61: 'Dominican Republic', 62: 'Ecuador', 63: 'El Salvador', 64: 'Equatorial Guinea',
     65: 'Ethiopia', 66: 'Eritrea', 67: 'Estonia', 68: 'Faroe Islands', 69: 'Falkland Islands',
     70: 'South Georgia and the South Sandwich Islands', 71: 'Fiji', 72: 'Finland', 73: 'Aland Islands', 74: 'France',
     75: 'French Guiana', 76: 'French Polynesia', 77: 'French Southern Territories', 78: 'Djibouti', 79: 'Gabon',
     80: 'Georgia', 81: 'Gambia', 82: 'Palestine', 83: 'Germany', 84: 'Ghana',
     85: 'Gibraltar', 86: 'Kiribati', 87: 'Greece', 88: 'Greenland', 89: 'Grenada',
     90: 'Guadeloupe', 91: 'Guam', 92: 'Guatemala', 93: 'Guinea', 94: 'Guyana',
     95: 'Haiti', 96: 'Heard Island and McDonald Islands', 97: 'Holy See', 98: 'Honduras', 99: 'Hong Kong',
    100: 'Hungary', 101: 'Iceland', 102: 'India', 103: 'Indonesia', 104: 'Iran',
    105: 'Iraq', 106: 'Ireland', 107: 'Israel', 108: 'Italy', 109: "Cote d'Ivoire",
    110: 'Jamaica', 111: 'Japan', 112: 'Kazakhstan', 113: 'Jordan', 114: 'Kenya',
    115: "Korea (Democratic People's Republic)", 116: 'Korea (Republic)', 117: 'Kuwait', 118: 'Kyrgyzstan', 119: "Lao People's Democratic Republic",
    120: 'Lebanon', 121: 'Lesotho', 122: 'Latvia', 123: 'Liberia', 124: 'Libya',
    125: 'Liechtenstein', 126: 'Lithuania', 127: 'Luxembourg', 128: 'Macao', 129: 'Madagascar',
    130: 'Malawi', 131: 'Malaysia', 132: 'Maldives', 133: 'Mali', 134: 'Malta',
    135: 'Martinique', 136: 'Mauritania', 137: 'Mauritius', 138: 'Mexico', 139: 'Monaco',
    140: 'Mongolia', 141: 'Moldova', 142: 'Montenegro', 143: 'Montserrat', 144: 'Morocco',
    145: 'Mozambique', 146: 'Oman', 147: 'Namibia', 148: 'Nauru', 149: 'Nepal',
    150: 'Netherlands', 151: 'Curacao', 152: 'Aruba', 153: 'Sint Maarten', 154: 'Bonaire, Sint Eustatius and Saba',
    155: 'New Caledonia', 156: 'Vanuatu', 157: 'New Zealand', 158: 'Nicaragua', 159: 'Niger',
    160: 'Nigeria', 161: 'Niue', 162: 'Norfolk Island', 163: 'Norway', 164: 'Northern Mariana Islands',
    165: 'United States Minor Outlying Islands', 166: 'Micronesia', 167: 'Marshall Islands', 168: 'Palau', 169: 'Pakistan',
    170: 'Panama', 171: 'Papua New Guinea', 172: 'Paraguay', 173: 'Peru', 174: 'Philippines',
    175: 'Pitcairn', 176: 'Poland', 177: 'Portugal', 178: 'Guinea-Bissau', 179: 'Timor-Leste',
    180: 'Puerto Rico', 181: 'Qatar', 182: 'Reunion', 183: 'Romania', 184: 'Russian Federation',
    185: 'Rwanda', 186: 'Saint Barthelemy', 187: 'Saint Helena, Ascension and Tristan da Cunha', 188: 'Saint Kitts and Nevis', 189: 'Anguilla',
    190: 'Saint Lucia', 191: 'Saint Martin (French part)', 192: 'Saint Pierre and Miquelon', 193: 'Saint Vincent and the Grenadines', 194: 'San Marino',
    195: 'Sao Tome and Principe', 196: 'Saudi Arabia', 197: 'Senegal', 198: 'Serbia', 199: 'Seychelles',
    200: 'Sierra Leone', 201: 'Singapore', 202: 'Slovakia', 203: 'Viet Nam', 204: 'Slovenia',
    205: 'Somalia', 206: 'South Africa', 207: 'Zimbabwe', 208: 'Spain', 209: 'South Sudan',
    210: 'Sudan', 211: 'Western Sahara', 212: 'Suriname', 213: 'Svalbard and Jan Mayen', 214: 'Eswatini',
    215: 'Sweden', 216: 'Switzerland', 217: 'Syrian Arab Republic', 218: 'Tajikistan', 219: 'Thailand',
    220: 'Togo', 221: 'Tokelau', 222: 'Tonga', 223: 'Trinidad and Tobago', 224: 'United Arab Emirates',
    225: 'Tunisia', 226: 'Turkey', 227: 'Turkmenistan', 228: 'Turks and Caicos Islands', 229: 'Tuvalu',
    230: 'Uganda', 231: 'Ukraine', 232: 'North Macedonia', 233: 'Egypt', 234: 'United Kingdom',
    235: 'Guernsey', 236: 'Jersey', 237: 'Isle of Man', 238: 'Tanzania', 239: 'United States of America',
    240: 'Virgin Islands (U.S.)', 241: 'Burkina Faso', 242: 'Uruguay', 243: 'Uzbekistan', 244: 'Venezuela',
    245: 'Wallis and Futuna', 246: 'Samoa', 247: 'Yemen', 248: 'Zambia',
    500: 'EU Organisations', 501: 'UN Organisations', 502: 'International',
}

# ---- A4 hazard category and type, ref.[1] Annex C.4
HAZARD: dict[int, str] = {
      0: 'not used',
      1: 'CBRNE - Air strike', 2: 'CBRNE - Attack on IT systems', 3: 'CBRNE - Attack with nuclear weapons',
      4: 'CBRNE - Biological hazard', 5: 'CBRNE - Chemical hazard', 6: 'CBRNE - Explosive hazard',
      7: 'CBRNE - Meteorite impact', 8: 'CBRNE - Missile attack', 9: 'CBRNE - Nuclear hazard',
     10: 'CBRNE - Nuclear power station accident', 11: 'CBRNE - Radiological hazard',
     12: 'CBRNE - Satellite/space re-entry debris', 13: 'CBRNE - Siren test',
     14: 'ENVIRONMENT - Acid rain', 15: 'ENVIRONMENT - Air pollution', 16: 'ENVIRONMENT - Contaminated drinking water',
     17: 'ENVIRONMENT - Gas leak', 18: 'ENVIRONMENT - Marine pollution', 19: 'ENVIRONMENT - Noise pollution',
     20: 'ENVIRONMENT - Plague of insects', 21: 'ENVIRONMENT - River pollution', 22: 'ENVIRONMENT - Suspended dust',
     23: 'ENVIRONMENT - UV radiation',
     24: 'FIRE - Conflagration', 25: 'FIRE - Fire brigade deployment', 26: 'FIRE - Fire gases', 27: 'FIRE - Forest fire',
     28: 'FIRE - Fumes', 29: 'FIRE - Odour nuisance', 30: 'FIRE - Risk of fire', 31: 'FIRE - Structure fire / Industrial fire',
     32: 'GEO - Ash fall', 33: 'GEO - Avalanche risk', 34: 'GEO - Crack in the ground/sinkhole', 35: 'GEO - Debris flow',
     36: 'GEO - Earthquake', 37: 'GEO - Geomagnetic or solar storm', 38: 'GEO - Glacial ice avalanche', 39: 'GEO - Landslide',
     40: 'GEO - Lava flow', 41: 'GEO - Pyroclastic flow', 42: 'GEO - Snowdrifts', 43: 'GEO - Tidal wave', 44: 'GEO - Tsunami',
     45: 'GEO - Volcanic mud flow', 46: 'GEO - Volcano eruption', 47: 'GEO - Wind/wave/storm surge',
     48: 'HEALTH - Epizootic', 49: 'HEALTH - Food safety alert', 50: 'HEALTH - Health hazard', 51: 'HEALTH - Pandemic',
     52: 'HEALTH - Pest infestation', 53: 'HEALTH - Risk of infection',
     54: 'INFRASTRUCTURE - Building collapse', 55: 'INFRASTRUCTURE - Emergency number outage', 56: 'INFRASTRUCTURE - Gas supply outage',
     57: 'INFRASTRUCTURE - Outage of IT systems', 58: 'INFRASTRUCTURE - Power outage', 59: 'INFRASTRUCTURE - Raw sewage',
     60: 'INFRASTRUCTURE - Telephone line outage',
     61: 'MET - Black ice', 62: 'MET - Coastal flooding', 63: 'MET - Cold wave', 64: 'MET - Derecho', 65: 'MET - Drought',
     66: 'MET - Dust storm', 67: 'MET - Floating ice / icebergs', 68: 'MET - Flood', 69: 'MET - Fog', 70: 'MET - Hail',
     71: 'MET - Heat wave', 72: 'MET - Lightning', 73: 'MET - Pollens', 74: 'MET - Rainfall', 75: 'MET - Snow storm / blizzard',
     76: 'MET - Snowfall', 77: 'MET - Storm or thunderstorm', 78: 'MET - Thawing', 79: 'MET - Tornado',
     80: 'MET - Tropical cyclone (hurricane)', 81: 'MET - Wind chill/frost', 82: 'MET - Tropical cyclone (typhoon)',
     83: 'RESCUE - Dam failure or bursting of a dam', 84: 'RESCUE - Dike failure or bursting of a dike',
     85: 'RESCUE - Explosive ordnance disposal', 86: 'RESCUE - Factory accident', 87: 'RESCUE - Mine hazard',
     88: 'SAFETY - Bomb/ammunition discovery', 89: 'SAFETY - Demonstration', 90: 'SAFETY - Hazardous material accident',
     91: 'SAFETY - Life threatening situation', 92: 'SAFETY - Major event', 93: 'SAFETY - Missing person/abduction',
     94: 'SAFETY - Risk of explosion', 95: 'SAFETY - Safety warning', 96: 'SAFETY - Undefined flying object',
     97: 'SAFETY - Unidentified animal',
     98: 'SECURITY - Chemical attack', 99: 'SECURITY - Guerrilla attack', 100: 'SECURITY - Hijack',
    101: 'SECURITY - Shooting or danger due to weapons', 102: 'SECURITY - Special forces attack', 103: 'SECURITY - Terrorism',
    104: 'TRANSPORT - Aircraft crash', 105: 'TRANSPORT - Bridge collapse', 106: 'TRANSPORT - Dangerous goods accident',
    107: 'TRANSPORT - Inland waterway transport accident', 108: 'TRANSPORT - Nautical disaster/Maritime/Marine security',
    109: 'TRANSPORT - Oil spill', 110: 'TRANSPORT - Road traffic incident', 111: 'TRANSPORT - Train/rail accident',
    112: 'TRANSPORT - Tunnel accident',
    113: 'OTHER - Test alert',
}

# ---- A5 severity, A8 duration, A9 library, ref.[1] Annex C.5, C.8, C.9
SEVERITY: dict[int, str] = {0: 'Unknown', 1: 'Moderate', 2: 'Severe', 3: 'Extreme'}
DURATION: dict[int, str] = {0: 'Unknown', 1: '<6h', 2: '6-12h', 3: '12-24h'}
WEEKDAY: list[str] = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

# ---- A11 international guidance library, ref.[1] Annex C.11
LIST_A: dict[int, str] = {  # IC-A-01 to IC-A-32, general required action
     0: '',
     1: 'You are in the danger zone, leave the area immediately. Listen to radio or media for directions and information.',
     2: 'You are in the danger zone, leave the area immediately and reach the evacuation point indicated by the area plotted in yellow. Listen to radio or media for directions and information.',
     3: 'Seek shelter in a building immediately. Stay under cover and stay informed.',
     4: 'Seek out a cellar or interior rooms on lower floors.',
     5: 'If you are in an alpine terrain, start descending immediately and seek for shelter.',
     6: 'Quickly move into interior rooms. If you are in a vehicle: Stop driving immediately on the edge of the road. If a building is nearby, seek shelter in that building.',
     7: 'If you are in open terrain and you cannot find shelter, lie face-down on the ground and protect your head and neck with your hands, in a hollow where possible',
     8: 'Prepare for evacuation. Take only the essentials with you, especially ID cards, passport, credit cards and cash. Evacuate only after the instruction of the emergency authorities.',
     9: 'Prepare emergency food and relief material: Check and restock your equipment and supplies of water, food, medicine, cash and batteries.',
    10: 'Stay away from glass surfaces such as windows and glass doors. There is a risk of injury from glass splinters.',
    11: 'Reduce your power consumption to a minimum.',
    12: 'Reduce your water consumption to a minimum.',
    13: 'Boil water before drinking it or using it in the kitchen.',
    14: 'Keep at least one metre away from any conversation partners. Avoid physical contact with other people such as kissing and shaking hands. Wash your hands regularly and thoroughly.',
    15: 'Do not drink any tap water. Avoid any skin contact with tap water. Only drink mineral water from a bottle. Turn off the water supply to your house.',
    16: 'Watch out for escaping gas. This can be indicated by hissing noises or a typical gas odour. Do not use matches, lighters or the like: naked flames in combination with leaking gas can lead to explosions and fires.',
    17: 'Do not go outside and do not use your car.',
    18: 'Do not touch any objects that seem suspicious to you. Debris can cause additional hazards such as fires and explosions. Inform the emergency services about damage and debris.',
    19: 'Do not enter smoke-filled rooms. Deadly gases can form there.',
    20: 'Do not enter cellars or underground car parks.',
    21: 'Do not leave pets or livestock outside.',
    22: 'Do not touch any dead animals. Report any findings of dead wild animals to the authorities.',
    23: 'Avoid driving',
    24: 'Avoid all items with metal parts such as umbrellas and bicycles. Do not bathe or shower during a thunderstorm. Bathing and showering can be life-threatening.',
    25: 'Avoid rooms directly underneath the roof truss. Avoid very large rooms, such as halls, in which the ceiling is not supported by pillars.',
    26: 'Avoid going outdoors. Keep away from trees, towers and masts. Keep at least 20 m away from power lines. Watch out for flying objects and falling objects.',
    27: 'Avoid the danger area',
    28: 'Avoid going out when it is not necessary',
    29: 'This is only a test. You do not have to take any action or to adopt any particular sheltering behaviour',
    30: 'This replaces the warning previously in effect for this area.',
    31: 'Conditions have improved and are no longer expected to meet alert criteria.',
}
LIST_B: dict[int, str] = {  # IC-B-01 to IC-B-32, monitoring and required action
     0: '',
     1: 'Check with the weather services and local authorities for additional information',
     2: 'Find out the location of the information points set up by the authorities on official channels (radio, internet, TV, social networks...)',
     3: 'Sensitive or vulnerable people should not go out unless they must.',
     4: 'Rescue operation under process by security forces and emergency services. Avoid moving to facilitate security and emergency actions.',
     5: 'Protect the most vulnerable and hear from your loved ones. Be aware of their special needs and support, as required. If you notice distressed or vulnerable persons, call the emergency services. Provide first aid if necessary but do not put yourself in any danger.',
     6: 'Pay attention to announcements made by the police, fire brigade and by officials.',
     7: 'Stay aware, keep listening to official instructions broadcast on the radio, television, websites and social networks pages',
     8: 'If you need help leaving your home, call the emergency services.',
     9: 'Only make phone calls in serious emergencies to avoid overloading the mobile network.',
    10: 'Extreme intensity weather phenomena expected. The weather is very dangerous and implies high level of threat to health, even the life hazard. BE AWARE and keep up to date with the latest weather forecast.',
    11: 'Severe weather expected. BE PREPARED. Take precautions and keep up to date with the latest weather forecast. Severe damages to people and properties may occur, especially to those vulnerable or in exposed areas.',
    12: 'Moderate intensity weather phenomena expected. BE AWARE, keep up to date with the latest weather forecast. Moderate damages to people and properties may occur, especially to those vulnerable or in exposed areas',
    13: 'BE PREPARED to protect yourself and your property. Flooding of properties and transport networks is expected. Disruption to power, communications and water supplies are possible. Evacuation may be required. Dangerous driving conditions due to reduced visibility and aquaplaning',
    14: 'Do not go near or in flooded waters. Do not walk or drive on a submerged road. Flood waves may surprise you, the river bank may collapse or you could be sucked in a manhole or hit by a floating debris. Keep drains and shafts clear so that the water can drain away. Secure and/or move assets away from vulnerable area (car along the river, basements).',
    15: 'Take shelter in the most resistant part of a permanent building, a municipal shelter if possible, and keep away from windows. BE AWARE of the "eye of the storm", the calm area in its centre. It will be followed by an inversion and the strengthening of winds. Do not go outside and do not use your car. Wait until the alert is over.',
    16: 'TAKE PRECAUTIONS, High temperatures are expected. Protect yourself from the heat and avoid physical and sports activities. Wet your body several times a day. Drink plenty of water and eat light food.',
    17: 'Forest fire danger. Under these conditions fires may develop and spread rapidly resulting in damage to property and possible loss of human and/or animal life. Do not throw away any burning cigarettes or matches to the environment. Do not make a fire outdoors. Do not light any fireworks. Do not barbeque in open places. Vegetation is easily ignited and large areas may be affected. Follow the instructions from the local authorities.',
    18: 'Risks of fire. Use permanent fireplaces when barbecuing. Make sure your fire is completely extinguished before you leave. Only light fireworks with the permission of the municipality, keep a safe distance from the forest and have water to hand.',
    19: 'Keep as far away as possible from coastal areas, beaches and rivers. Get immediately to the highest ground possible and wait until the alert is over. If you are in danger of being overtaken by waves, climb onto a roof or up a solid tree, or cling on to a floating object carried along by the water.',
    20: "Do not go to sea and keep as far away as possible from the coast and wait until the alert is over. If you are at sea, don't return to port. Keep away from the coast. Waves are much less dangerous out at sea.",
    21: 'Leave the affected area immediately and seek higher ground or move to higher parts of the building. Listen to radio or media for directions and information',
    22: 'Indoors: during the quake, take shelter near a wall or a solid piece of furniture. Outside: during the quake, keep away from anything that might collapse. In a car: during the quake, stop as far away from buildings as you can. After, be prepared for aftershocks. If you are indoor, leave by the stairs.',
    23: 'Leave the impact site immediately and cover your mouth and nose with improvised respiratory protection (cloth, garment, surgical mask). This protects you from dust, but not from gaseous hazardous substances. Seek out a building. Move wherever possible at a right angle to the wind direction as this is the quickest way to leave the danger zone with a possible cloud of hazardous substances.',
    24: 'Switch off the ventilation and air conditioning systems. Close all windows, doors and shutters. Cover your mouth and nose and breathe through a facemask or an improvised respiratory protection (cloth, garment, surgical mask) if the air is filled with smoke and ashes',
    25: 'Have iodine tablets ready. DO NOT take the iodine tablets now. If this becomes necessary, we will inform you in good time.',
    26: 'Take the iodine tablets NOW according to the package insert.',
    27: 'Avoid watering your plants during the hottest hours, avoid using water for secondary uses such as washing your car.',
    28: 'Seek shelter if you cannot leave the area immediately.',
    29: 'reserved', 30: 'reserved',
    31: 'This replaces the warning previously in effect for this area.',
}
LIST_C: dict[int, str] = {  # IC-C-01 to IC-C-32, specific action for second ellipse, ref.[1] Annex C.18.3.4
     0: '',
     1: 'Prepare for evacuation. Take only the essentials with you, especially ID cards, passport, credit cards and cash. Evacuate only after the instruction of the emergency authorities.',
     2: 'Prepare emergency food and relief material: Check and restock your equipment and supplies of water, food, medicine, cash and batteries.',
     3: 'Be prepared to protect yourself and your property. Flooding of properties and transport networks is expected. Disruption to power, communications and water supplies are possible. Evacuation may be required. Dangerous driving conditions due to reduced visibility and aquaplaning.',
     4: 'Have iodine tablets ready. DO NOT take the iodine tablets now. If this becomes necessary, we will inform you in good time.',
     5: 'Keep your smartphone charged to be able to receive further instructions and information',
     6: 'Avoid using lifts.',
     7: 'Avoid the danger area.',
     8: 'Avoid driving.',
     9: 'Rescue operation under process by security forces and emergency services. Avoid moving to facilitate security and emergency actions.',
    10: 'Check with the weather services and local authorities for additional information.',
    11: 'Find out the location of the information points set up by the authorities on official channels (radio, internet, TV, social networks...).',
    12: 'Sensitive or vulnerable people should not go out unless they must.',
    13: 'Protect the most vulnerable and hear from your loved ones. Be aware of their special needs and support, as required. If you notice distressed or vulnerable persons, contact the emergency services. Provide first aid if necessary but do not put yourself in any danger.',
    14: 'Pay attention to announcements made by the police, fire brigade and by officials.',
    15: 'Stay aware, keep listening to official instructions broadcast on the radio, television, websites and social networks pages.',
    16: 'Only make phone calls in serious emergencies to avoid overloading the mobile network.',
    30: 'This is only a test. You do not have to take any action or to adopt any particular sheltering behaviour.',
    31: 'Conditions have improved and are no longer expected to meet alert criteria.',
}

# ---- A14/A15 ellipse axis length [km], ref.[1] Annex C.14
RADIUS_KM: list[float] = [
       0.216,    0.292,    0.395,    0.535,    0.723,    0.978,    1.322,    1.788,
       2.418,    3.269,    4.421,    5.979,    8.085,   10.933,   14.784,   19.992,
      27.035,   36.559,   49.439,   66.855,   90.407,  122.255,  165.324,  223.564,
     302.322,  408.824,  552.846,  747.603, 1010.970, 1367.116, 1848.727, 2500.000,
]

# ---- A17 main subject for specific settings, ref.[1] Annex C.17
SPECIFIC_SETTINGS: dict[int, str] = {
    0: 'B1 improved resolution of main ellipse', 1: 'B2 position of the centre of the hazard',
    2: 'B3 secondary ellipse definition', 3: 'B4 quantitative and detailed information',
}

# ---- B4 lower level fields, ref.[1] Annex C.18.4
# hazard code -> list of (D field name, bits); remaining bits are reserved
B4_LAYOUT: dict[int, list[tuple[str, int]]] = {
    36: [('D1', 4), ('D2', 3), ('D3', 4), ('D4', 4)],   # earthquake
    44: [('D5', 3)], 43: [('D5', 3)],                   # tsunami, tidal wave
    63: [('D6', 4)], 71: [('D6', 4)],                   # cold wave, heat wave
    80: [('D7', 3), ('D8', 4), ('D9', 3)],              # hurricane
    82: [('D36', 3), ('D8', 4), ('D9', 3)],             # typhoon
    79: [('D8', 4), ('D9', 3), ('D11', 3)],             # tornado
    77: [('D8', 4), ('D9', 3), ('D10', 3), ('D16', 3)], # storm or thunderstorm
    70: [('D12', 4)],                                   # hail
    74: [('D9', 3), ('D13', 4)],                        # rainfall
    76: [('D14', 5), ('D13', 4)],                       # snowfall
    68: [('D15', 2)],                                   # flood
    72: [('D16', 3)],                                   # lightning
    81: [('D8', 4), ('D6', 4)],                         # wind chill/frost
    64: [('D8', 4), ('D9', 3), ('D16', 3), ('D11', 3)], # derecho
    69: [('D17', 3), ('D13', 4)],                       # fog
    75: [('D13', 4), ('D8', 4)],                        # snow storm / blizzard
    65: [('D18', 2)],                                   # drought
    33: [('D19', 3)],                                   # avalanche risk
    32: [('D20', 3)],                                   # ash fall
    47: [('D8', 4), ('D5', 3)],                         # wind/wave/storm surge
    37: [('D21', 3)],                                   # geomagnetic or solar storm
    103: [('D22', 3)],                                  # terrorism
    27: [('D23', 3)], 30: [('D23', 3)],                 # forest fire, risk of fire
    16: [('D24', 3)], 18: [('D24', 3)], 21: [('D24', 3)],  # contaminated water, marine, river pollution
    23: [('D25', 4)],                                   # UV radiation
    53: [('D26', 5), ('D35', 6)], 51: [('D26', 5), ('D35', 6)],  # risk of infection, pandemic
    19: [('D27', 4)],                                   # noise pollution
    15: [('D28', 3)],                                   # air pollution
    56: [('D29', 5)], 57: [('D29', 5)], 58: [('D29', 5)], 55: [('D29', 5)], 60: [('D29', 5)],  # outages
    11: [('D30', 4)], 9: [('D30', 4)], 10: [('D30', 4)],  # radiological, nuclear hazard, nuclear power station
    5: [('D31', 4)],                                    # chemical hazard
    4: [('D32', 2), ('D33', 2)],                        # biological hazard
    6: [('D34', 2)],                                    # explosive hazard
}
D_NAME: dict[str, str] = {
    'D1': 'magnitude', 'D2': 'seismic coefficient', 'D3': 'azimuth to epicentre', 'D4': 'distance to epicentre',
    'D5': 'wave height', 'D6': 'temperature', 'D7': 'hurricane category', 'D8': 'wind', 'D9': 'rainfall',
    'D10': 'damage category', 'D11': 'tornado probability', 'D12': 'hail scale', 'D13': 'visibility',
    'D14': 'snow depth', 'D15': 'flood severity', 'D16': 'lightning', 'D17': 'fog level', 'D18': 'drought level',
    'D19': 'avalanche level', 'D20': 'ash fall', 'D21': 'geomagnetic scale', 'D22': 'terrorism threat',
    'D23': 'fire risk level', 'D24': 'water quality', 'D25': 'UV index', 'D26': 'cases per 100000',
    'D27': 'noise', 'D28': 'air quality index', 'D29': 'outage duration', 'D30': 'nuclear event scale',
    'D31': 'chemical hazard type', 'D32': 'biohazard level', 'D33': 'biohazard type', 'D34': 'explosive hazard type',
    'D35': 'infection type', 'D36': 'typhoon category',
}
D_VALUE: dict[str, dict[int, str]] = {  # code to short value, ref.[1] Annex C.18.4.35
    'D1': {0: 'M1.0-1.9', 1: 'M2.0-2.9', 2: 'M3.0-3.9', 3: 'M4.0-4.9', 4: 'M5.0-5.9', 5: 'M6.0-6.9', 6: 'M7.0-7.9', 7: 'M8.0-8.9', 8: 'M9.0+'},
    'D2': {0: '2', 1: '3', 2: '4', 3: '5 weak', 4: '5 strong', 5: '6 weak', 6: '6 strong', 7: '7'},
    'D3': {i: f'{i*22.5:.1f}[deg]' for i in range(16)},
    'D4': {0: 'x0.25', 1: 'x0.5', 2: 'x0.75', 3: 'x1', 4: 'x2', 5: 'x3', 6: 'x5', 7: 'x10', 8: 'x20', 9: 'x30', 10: 'x40', 11: 'x50', 12: 'x70', 13: 'x100', 14: 'x150', 15: 'x200'},
    'D5': {0: '<=0.5[m]', 1: '0.5-1[m]', 2: '1-1.5[m]', 3: '1.5-2[m]', 4: '2-3[m]', 5: '3-5[m]', 6: '5-10[m]', 7: '>10[m]'},
    'D6': {0: '<=-30[degC]', 1: '-30..-25[degC]', 2: '-25..-20[degC]', 3: '-20..-15[degC]', 4: '-15..-10[degC]', 5: '-10..-5[degC]', 6: '-5..0[degC]', 7: '0..5[degC]', 8: '5..10[degC]', 9: '10..15[degC]', 10: '15..20[degC]', 11: '20..25[degC]', 12: '25..30[degC]', 13: '30..35[degC]', 14: '35..45[degC]', 15: '>45[degC]'},
    'D7': {0: 'category 1', 1: 'category 2', 2: 'category 3', 3: 'category 4', 4: 'category 5'},
    'D8': {i: f'Beaufort {i}' for i in range(13)},
    'D9': {0: '<=2.5[mm/h]', 1: '2.5-7.5[mm/h]', 2: '7.5-10[mm/h]', 3: '10-20[mm/h]', 4: '20-30[mm/h]', 5: '30-50[mm/h]', 6: '50-80[mm/h]', 7: '>80[mm/h]'},
    'D10': {0: 'category 1', 1: 'category 2', 2: 'category 3', 3: 'category 4', 4: 'category 5', 5: 'category 5'},
    'D11': {0: 'non-threatening', 1: 'very low', 2: 'low', 3: 'moderate', 4: 'high', 5: 'extreme'},
    'D12': {i: f'H{i}' for i in range(11)},
    'D13': {0: '<20[m]', 1: '20-200[m]', 2: '200-500[m]', 3: '500-1000[m]', 4: '1-2[km]', 5: '2-4[km]', 6: '4-10[km]', 7: '10-20[km]', 8: '20-50[km]', 9: '>50[km]'},
    'D14': {**{i: f'{20*i}-{20*(i+1)}[cm]' for i in range(30)}, 30: '>600[cm]'},
    'D15': {0: 'minor', 1: 'moderate', 2: 'major', 3: 'record'},
    'D16': {i: f'LAL {i+1}' for i in range(6)},
    'D17': {i: f'level {i+1}/5' for i in range(5)},
    'D18': {0: 'D1 moderate', 1: 'D2 severe', 2: 'D3 extreme', 3: 'D4 exceptional'},
    'D19': {0: '1 low', 1: '2 moderate', 2: '3 considerable', 3: '4 high', 4: '5 very high'},
    'D20': {0: '<1[mm]', 1: '1-5[mm]', 2: '5-100[mm]', 3: '100-300[mm]', 4: '>300[mm]'},
    'D21': {0: 'G1 minor', 1: 'G2 moderate', 2: 'G3 strong', 3: 'G4 severe', 4: 'G5 extreme'},
    'D22': {0: 'very low', 1: 'low', 2: 'medium', 3: 'high', 4: 'critical'},
    'D23': {i: f'level {i+1}/5' for i in range(5)},
    'D24': {0: 'excellent', 1: 'good', 2: 'poor', 3: 'very poor', 4: 'suitable for drinking', 5: 'unsuitable for drinking'},
    'D25': {0: '0-2 low', 1: '3 moderate', 2: '4 moderate', 3: '5 high', 4: '6 high', 5: '7 high', 6: '8 very high', 7: '9 very high', 8: '10 extreme', 9: '11 extreme'},
    'D26': {0: '0-9', 1: '10-20', 2: '21-50', 3: '51-70', 4: '71-100', 5: '101-125', 6: '126-150', 7: '151-175', 8: '176-200', 9: '201-250', 10: '251-300', 11: '301-350', 12: '351-400', 13: '401-450', 14: '451-500', 15: '501-750', 16: '751-1000', 17: '>1000', 18: '>2000', 19: '>3000', 20: '>5000'},
    'D27': {0: '40-45[dB]', 1: '45-50[dB]', 2: '50-60[dB]', 3: '60-70[dB]', 4: '70-80[dB]', 5: '80-90[dB]', 6: '90-100[dB]', 7: '100-110[dB]', 8: '110-120[dB]', 9: '120-130[dB]', 10: '130-140[dB]', 11: '>140[dB]'},
    'D28': {0: '0-50 good', 1: '51-100 moderate', 2: '101-150 unhealthy for sensitive groups', 3: '151-200 unhealthy', 4: '201-300 very unhealthy', 5: '301-500 hazardous'},
    'D29': {0: '<30min', 1: '30-45min', 2: '45min-1h', 3: '1-1.5h', 4: '1.5-2h', 5: '2-3h', 6: '3-4h', 7: '4-5h', 8: '5-10h', 9: '10-24h', 10: '1-2days', 11: '2-7days', 12: '>=7days', 13: 'unknown'},
    'D30': {0: 'unknown', **{i: f'INES level {i-1}' for i in range(1, 9)}},
    'D31': {0: 'explosives', 1: 'flammable gases', 2: 'flammable aerosols', 3: 'oxidizing gases', 4: 'gases under pressure', 5: 'flammable liquids', 6: 'flammable solids', 7: 'self-reactive', 8: 'pyrophoric liquids', 9: 'pyrophoric solids', 10: 'self-heating', 11: 'water-reactive', 12: 'oxidising liquids', 13: 'oxidising solids', 14: 'organic peroxides', 15: 'corrosive to metals'},
    'D32': {i: f'level {i+1}/4' for i in range(4)},
    'D33': {0: 'biological agents', 1: 'biotoxins', 2: 'blood and blood products', 3: 'environmental specimens'},
    'D34': {0: 'PE1', 1: 'PE2', 2: 'PE3', 3: 'PE4'},
    'D35': {0: 'Anthrax', 1: 'Avian influenza', 2: 'Botulism', 3: 'Brucellosis', 4: 'Campylobacteriosis', 5: 'Chikungunya', 6: 'Chlamydia', 7: 'Cholera', 8: 'COVID-19', 9: 'vCJD', 10: 'Cryptosporidiosis', 11: 'Dengue', 12: 'Diphtheria', 13: 'Echinococcosis', 14: 'Giardiasis', 15: 'Gonorrhoea', 16: 'Hepatitis A', 17: 'Hepatitis B', 18: 'Hepatitis C', 19: 'HIV/AIDS', 20: 'Haemophilus influenza B', 21: 'Influenza', 22: 'Invasive meningococcal disease', 23: 'Invasive pneumococcal disease', 24: "Legionnaires' disease", 25: 'Leptospirosis', 26: 'Listeriosis', 27: 'Lyme neuroborreliosis', 28: 'Malaria', 29: 'Measles', 30: 'Meningococcal disease', 31: 'Mumps', 32: 'Pertussis', 33: 'Plague', 34: 'Pneumococcal invasive diseases', 35: 'Poliomyelitis', 36: 'Q fever', 37: 'Rabies', 38: 'Rubella', 39: 'Rubella, congenital', 40: 'Salmonellosis', 41: 'SARS', 42: 'STEC/VTEC', 43: 'Shigellosis', 44: 'Smallpox', 45: 'Syphilis', 46: 'Syphilis, congenital', 47: 'Tetanus', 48: 'Tick-borne encephalitis', 49: 'Toxoplasmosis, congenital', 50: 'Trichinellosis', 51: 'Tuberculosis', 52: 'Tularaemia', 53: 'Typhoid and paratyphoid fevers', 54: 'Viral haemorrhagic fevers', 55: 'West Nile virus', 56: 'Yellow fever', 57: 'Yersinosis', 58: 'Zika virus', 59: 'Zika virus, congenital', 60: 'Nosocomial infections', 61: 'Antimicrobial resistance', 62: 'unidentified infection'},
    'D36': {0: 'scale 1 intensity 1', 1: 'scale 1 intensity 2', 2: 'scale 1 intensity 3', 3: 'scale 2 intensity 1', 4: 'scale 2 intensity 2'},
}

def onset_str(week: int, tow: int) -> str:
    ''' A6/A7 hazard onset to string, tow in minutes from Monday 00:00 (1-origin), 0 = not used '''
    if tow == 0:
        return 'not used'
    wd, t = divmod(tow - 1, 1440)
    day = WEEKDAY[wd] if wd < 7 else '?'
    return f'{"next week" if week else "this week"} {day} {t//60:02d}:{t%60:02d} UTC'

def delta_deg(code: int) -> float:
    ''' C5/C6 delta latitude/longitude [deg] from 7-bit code, ref.[1] Annex C.18.2 '''
    return -10.0 + (code if code <= 63 else code + 1) * 20.0 / 128

def refined_axis_km(code: int, factor: int) -> float:
    ''' C3/C4 refined semi-axis length [km], ref.[1] sect.3.7.1.3 '''
    delta = RADIUS_KM[code] - RADIUS_KM[code - 1] if code > 0 else RADIUS_KM[0]
    return RADIUS_KM[code] - factor / 8 * delta

def decode_specific_settings(a17: int, a18: BitStream, a4: int,
                             lat: float, lon: float, major_code: int, minor_code: int, azimuth: float) -> list[str]:
    '''
    decodes A17/A18 specific settings, ref.[1] sect.3.7
    inputs  a17 main subject, a18 15-bit specific settings, a4 hazard code,
            main ellipse centre lat/lon [deg], axis codes, azimuth [deg]
    returns list of description lines
    '''
    a18.pos = 0
    lines: list[str] = []
    if a17 == 0:    # B1 improved resolution of main ellipse
        c1 = a18.read(3).u
        c2 = a18.read(3).u
        c3 = a18.read(3).u
        c4 = a18.read(3).u
        if c1 or c2 or c3 or c4:
            rlat = lat + c1 * 180 / (pow(2, 16) - 1) / 8
            rlon = lon + c2 * 360 / (pow(2, 17) - 1) / 8
            lines.append(f'refined ellipse: centre {rlat:.6f} {rlon:.6f}, semi-major {refined_axis_km(major_code, c3):.3f}[km], semi-minor {refined_axis_km(minor_code, c4):.3f}[km]')
    elif a17 == 1:  # B2 position of the centre of the hazard
        c5 = a18.read(7).u
        c6 = a18.read(7).u
        lines.append(f'hazard centre: {lat + delta_deg(c5):.3f} {lon + delta_deg(c6):.3f} (delta {delta_deg(c5):+.5f} {delta_deg(c6):+.5f}[deg])')
    elif a17 == 2:  # B3 secondary ellipse definition
        c7  = a18.read(2).u  # shift factor
        c8  = a18.read(3).u  # homothetic factor
        c9  = a18.read(5).u  # bearing angle
        c10 = a18.read(5).u  # guidance for second ellipse
        major = RADIUS_KM[major_code]
        lines.append(f'secondary ellipse: shift {c7}x{major:.3f}[km] along bearing {c9 * 360 / 32:.2f}[deg], '
                     f'size x{(c8 + 1) * 0.25:.2f}, instruction IC-C-{c10+1:02d}: "{LIST_C.get(c10, "reserved")}"')
    else:           # B4 quantitative and detailed information
        layout = B4_LAYOUT.get(a4)
        if layout is None:
            lines.append(f'detailed information: (not defined for this hazard) {a18.bin}')
        else:
            items = []
            for name, bits in layout:
                code = a18.read(bits).u
                items.append(f'{D_NAME[name]}={D_VALUE.get(name, {}).get(code, f"code {code}")}')
            lines.append('detailed information: ' + ', '.join(items))
    return lines

# EOF
