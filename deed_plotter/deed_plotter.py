# Deed Plotter
# Reads a land description ("metes and bounds") from a data file and draws the parcel's outline
# in a file that Google Earth can open.
#
# How to run (in a Command Prompt, inside this folder):
#     python deed_plotter.py parcel_example.json
# That creates parcel_example.kml. Double-click the .kml file to open it in Google Earth.

import json                                 # reads the data file
import re                                   # finds the pieces of a bearing like "N 74°09' W"
import sys                                  # lets us read the file name typed after the program name
from math import sin, cos, radians, sqrt, hypot


# --- Step 1: turn a bearing such as "N 74°09' W" into east/north distances ----------------------

def parse_bearing(text):
    """Turn a bearing like "N 74°09' W" into (north_or_south, degrees, minutes, east_or_west)."""
    # Pull out: a letter (N or S), the numbers, then a letter (E or W). Symbols like ° ' " are ignored.
    match = re.match(r"\s*([NS])\s*(\d+)\D+(\d+)?\D*([EW])\s*$", text.strip(), re.IGNORECASE)
    if not match:
        raise ValueError(f"Could not understand the bearing: {text!r}")
    ns, degrees, minutes, ew = match.groups()
    return ns.upper(), int(degrees), int(minutes or 0), ew.upper()


def step(bearing_text, distance):
    """Return (east, north) in metres for walking `distance` metres along a bearing.

    A bearing is measured from north or south toward east or west.
    Example: "N 74°09' W" means: face north, turn 74°09' toward west, and walk.
    """
    ns, degrees, minutes, ew = parse_bearing(bearing_text)
    angle = radians(degrees + minutes / 60)         # degrees and minutes -> one angle in radians
    north = distance * cos(angle) * (1 if ns == "N" else -1)   # cos gives the north-south part
    east = distance * sin(angle) * (1 if ew == "E" else -1)    # sin gives the east-west part
    return east, north


# --- Step 2: turn "metres east/north of the monument" into latitude and longitude ---------------

def metres_per_degree(latitude):
    """Return (metres per degree of latitude, metres per degree of longitude) at this latitude.

    Uses the shape of the Earth (the WGS84 ellipsoid, the same one GPS and Google Earth use),
    so the answer is accurate to well under a centimetre across a parcel.
    """
    a = 6378137.0                                   # Earth's equatorial radius, metres
    e2 = 0.00669437999014                           # how squashed the Earth is
    phi = radians(latitude)
    w = sqrt(1 - e2 * sin(phi) ** 2)
    per_degree_lat = radians(1) * a * (1 - e2) / w ** 3
    per_degree_lon = radians(1) * a * cos(phi) / w
    return per_degree_lat, per_degree_lon


def to_lat_lon(start_lat, start_lon, east, north):
    """Return the latitude and longitude of a spot `east` and `north` metres from the start."""
    per_lat, per_lon = metres_per_degree(start_lat)
    return start_lat + north / per_lat, start_lon + east / per_lon


# --- Step 3: walk the boundary -------------------------------------------------------------------

def walk(parcel):
    """Follow the deed from the monument around the parcel. Returns a list of corners.

    Each corner is (label, east, north), in metres from the monument.
    """
    east, north = 0.0, 0.0                          # we start standing on the monument
    # Optional nudge, for lining the outline up with what you see on the satellite image.
    # It can be given as metres east/north, or as a distance along an azimuth (degrees clockwise from north).
    east += parcel.get("shift_east_m", 0.0)
    north += parcel.get("shift_north_m", 0.0)
    shifts = parcel.get("shift", [])
    if isinstance(shifts, dict):                    # a single shift, or a list of shifts applied one after another
        shifts = [shifts]
    for one in shifts:
        azimuth = radians(one["azimuth_deg"])
        east += one["distance_m"] * sin(azimuth)
        north += one["distance_m"] * cos(azimuth)
    monument = (east, north)

    tie = parcel["tie"]                             # the line from the monument to corner 1
    de, dn = step(tie["bearing"], tie["distance_m"])
    east, north = east + de, north + dn
    corners = [("1", east, north)]

    for leg in parcel["legs"]:                      # then walk each side of the parcel in turn
        de, dn = step(leg["bearing"], leg["distance_m"])
        east, north = east + de, north + dn
        corners.append((leg["to"], east, north))
    return monument, corners


def area_and_closure(corners):
    """Return (misclosure in metres, area in square metres) for the walked outline."""
    start, end = corners[0], corners[-1]            # the walk should end where it began
    misclosure = hypot(end[1] - start[1], end[2] - start[2])
    outline = corners[:-1]                          # the last corner is a repeat of the first
    total = 0.0
    for i in range(len(outline)):                   # the "shoelace" formula for a polygon's area
        x1, y1 = outline[i][1], outline[i][2]
        x2, y2 = outline[(i + 1) % len(outline)][1], outline[(i + 1) % len(outline)][2]
        total += x1 * y2 - x2 * y1
    return misclosure, abs(total) / 2


# --- Step 4: write the Google Earth file ---------------------------------------------------------

def style_xml(style):
    """Inline KML style from a small dict: line_color, fill_color, width, fill (all optional). Colours are aabbggrr."""
    line = f"<LineStyle><color>{style.get('line_color', 'ffffffff')}</color><width>{style.get('width', 2)}</width></LineStyle>"
    if style.get("fill") is False:
        fill = "<PolyStyle><fill>0</fill></PolyStyle>"
    else:
        fill = f"<PolyStyle><color>{style.get('fill_color', '33ffffff')}</color></PolyStyle>"
    return f"<Style>{line}{fill}</Style>"


def write_kml(parcel, monument, corners, path):
    """Write a KML file (the format Google Earth opens) with the outline and labelled points."""
    lat0, lon0 = parcel["monument"]["lat"], parcel["monument"]["lon"]

    def coord(east, north):
        lat, lon = to_lat_lon(lat0, lon0, east, north)
        return f"{lon:.8f},{lat:.8f},0"             # KML wants longitude first, then latitude

    outline = corners[:-1]                          # drop the repeated last corner
    ring = " ".join(coord(e, n) for _, e, n in outline + outline[:1])   # repeat corner 1 to close it

    pins = [f"""    <Placemark><name>{parcel['monument'].get('name', 'Monument')}</name>
      <Point><coordinates>{coord(*monument)}</coordinates></Point></Placemark>"""]
    for label, e, n in outline:
        pins.append(f"""    <Placemark><name>Point {label}</name>
      <Point><coordinates>{coord(e, n)}</coordinates></Point></Placemark>""")

    # Optional neighbouring lots (for example the other lots on a subdivision plan). Their corners are given in
    # metres east/north of corner 1, so they move together with the main parcel.
    neighbours = []
    for lot in parcel.get("neighbors", []):
        base_e, base_n = corners[0][1], corners[0][2]
        pts = [(base_e + e, base_n + n) for e, n in lot["corners_m"]]
        lot_ring = " ".join(coord(e, n) for e, n in pts + pts[:1])
        neighbours.append(f"""    <Placemark><name>{lot['name']}</name><description>{lot.get('note', '')}</description>
      {style_xml(lot['style']) if 'style' in lot else '<styleUrl>#neighbour</styleUrl>'}
      <Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>
        <coordinates>{lot_ring}</coordinates>
      </LinearRing></outerBoundaryIs></Polygon></Placemark>""")

    # Optional extra lines (for example a road), given as points in metres east/north of corner 1.
    lines = []
    for ln in parcel.get("lines", []):
        base_e, base_n = corners[0][1], corners[0][2]
        pts = [(base_e + e, base_n + n) for e, n in ln["points_m"]]
        lines.append(f"""    <Placemark><name>{ln['name']}</name><description>{ln.get('note', '')}</description>
      {style_xml(ln['style']) if 'style' in ln else '<styleUrl>#outline</styleUrl>'}
      <LineString><tessellate>1</tessellate><coordinates>{' '.join(coord(e, n) for e, n in pts)}</coordinates></LineString></Placemark>""")

    # Optional text labels with no icon, given as points in metres east/north of corner 1.
    labels = []
    for lb in parcel.get("labels", []):
        base_e, base_n = corners[0][1], corners[0][2]
        e, n = base_e + lb["point_m"][0], base_n + lb["point_m"][1]
        labels.append(f"""    <Placemark><name>{lb['name']}</name>
      <Style><IconStyle><scale>0</scale></IconStyle><LabelStyle><color>{lb.get('color', 'ffffffff')}</color><scale>{lb.get('scale', 1.0)}</scale></LabelStyle></Style>
      <Point><coordinates>{coord(e, n)}</coordinates></Point></Placemark>""")

    # Optional point markers at absolute positions: [{"name", "lat", "lon", "color", "note"}].
    markers = []
    for mk in parcel.get("markers", []):
        markers.append(f"""    <Placemark><name>{mk['name']}</name><description>{mk.get('note', '')}</description>
      <Style><IconStyle><color>{mk.get('color', 'ffffffff')}</color><scale>{mk.get('scale', 1.2)}</scale>
        <Icon><href>http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png</href></Icon></IconStyle></Style>
      <Point><coordinates>{mk['lon']:.8f},{mk['lat']:.8f},0</coordinates></Point></Placemark>""")

    main_style = style_xml(parcel["style"]) if "style" in parcel else "<styleUrl>#outline</styleUrl>"
    tie_line = "" if parcel.get("clean") else f"""    <Placemark><name>Tie line</name><styleUrl>#outline</styleUrl>
      <LineString><tessellate>1</tessellate>
        <coordinates>{coord(*monument)} {coord(outline[0][1], outline[0][2])}</coordinates>
      </LineString></Placemark>"""
    if parcel.get("clean"):                         # "clean": true draws only the outlines, no pins or tie line
        pins = []

    kml = f"""<?xml version="1.0" encoding="UTF-8"?>
<kml xmlns="http://www.opengis.net/kml/2.2">
  <Document>
    <name>{parcel.get('name', 'Parcel')}</name><description>{parcel.get('description', '')}</description>
    <Style id="outline"><LineStyle><color>ff00ffff</color><width>3</width></LineStyle>
      <PolyStyle><color>3300ffff</color></PolyStyle></Style>
    <Style id="neighbour"><LineStyle><color>ffffaa00</color><width>2</width></LineStyle>
      <PolyStyle><color>33ffaa00</color></PolyStyle></Style>
    <Placemark><name>{parcel.get('label', str(parcel.get('name', 'Parcel')) + ' boundary')}</name>{main_style}
      <Polygon><tessellate>1</tessellate><outerBoundaryIs><LinearRing>
        <coordinates>{ring}</coordinates>
      </LinearRing></outerBoundaryIs></Polygon></Placemark>
{tie_line}
{chr(10).join(neighbours)}
{chr(10).join(lines)}
{chr(10).join(labels)}
{chr(10).join(markers)}
{chr(10).join(pins)}
  </Document>
</kml>
"""
    with open(path, "w", encoding="utf-8") as f:
        f.write(kml)


# --- The program starts here ---------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print("Usage: python deed_plotter.py <data file.json>")
        return
    data_file = sys.argv[1]
    with open(data_file, encoding="utf-8") as f:
        parcel = json.load(f)

    monument, corners = walk(parcel)
    misclosure, area = area_and_closure(corners)
    perimeter = sum(leg["distance_m"] for leg in parcel["legs"])

    output = data_file.rsplit(".", 1)[0] + ".kml"
    write_kml(parcel, monument, corners, output)

    print(f"Parcel: {parcel.get('name', '(unnamed)')}")
    if misclosure < 0.005:                          # under half a centimetre: call it exact
        print(f"Closure: the boundary closes exactly ({perimeter:.2f} m perimeter)")
    else:
        print(f"Misclosure: {misclosure:.2f} m over a {perimeter:.2f} m perimeter "
              f"(1 part in {perimeter / misclosure:,.0f})")
    print(f"Area from the walked outline: {area:,.0f} square metres")
    if "stated_area_sqm" in parcel:
        print(f"Area stated in the deed:      {parcel['stated_area_sqm']:,} square metres")
    for lot in parcel.get("neighbors", []):
        _, lot_area = area_and_closure([("", e, n) for e, n in lot["corners_m"]] + [("", *lot["corners_m"][0])])
        print(f"  {lot['name']}: {lot_area:,.0f} square metres")
    print(f"Wrote {output} -- double-click it to open in Google Earth.")


main()
