# Deed Plotter

Reads a land description ("metes and bounds": a starting monument, then a bearing and distance for each
side) and writes a `.kml` file that Google Earth opens, showing the parcel's outline.

## Run it

In a Command Prompt inside this folder:

```
python deed_plotter.py parcel_example.json
```

This prints the closure and area, and creates `parcel_example.kml`. Double-click the `.kml` to open it in Google Earth.
No extra libraries are needed.

## Use your own parcel

1. Copy `parcel_example.json` to a new name (for example `parcel.json`) and edit it.
2. `monument`: the starting monument's latitude and longitude, in decimal degrees.
3. `tie`: the bearing and distance from the monument to corner 1.
4. `legs`: one entry per side, in order, ending with the leg that returns to corner 1.
   Bearings are written like `N 74°09' W` (north or south, degrees, minutes, east or west).
5. `stated_area_sqm` is optional. If given, it is printed next to the computed area as a check.
6. Optional: slide the whole outline to line it up with the satellite image (useful if the monument's coordinates
   are on an older datum). Either give `"shift": {"azimuth_deg": 108.49, "distance_m": 105.61}` (a distance along an
   azimuth, measured clockwise from north) or `shift_east_m` and `shift_north_m`.

`parcel.json` and all `.kml` files are listed in `.gitignore`, so real deed data is not uploaded to GitHub.

## What it does not do

- It does not convert between map datums (for example the old Luzon 1911 datum to WGS84). It assumes the
  monument's coordinates are WGS84, which is what Google Earth uses.
- It assumes bearings are from true north.
- The outline is a plot of the deed's numbers, not a legal survey.

## Drawing neighbouring lots (optional)

Add a `"neighbors"` list to the data file to draw other lots in a different colour, for example the other lots of a
subdivision. Each has a `name` and `corners_m`, a list of `[east, north]` positions in metres measured from corner 1
of the main parcel. Neighbours move with the main parcel when you use a `shift`.
