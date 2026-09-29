# World Clock tray app
# Shows the current date and time in three places from an icon in the Windows taskbar tray.
#   - Hover over the icon to see all three times.
#   - Right-click the icon for a menu with the times and a Quit option.

# "import" loads code that someone else already wrote, so we can use it.
import threading                            # lets us run a timer alongside the tray icon
from datetime import datetime, timedelta, timezone   # dates, times, and time differences
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError # the official time zone rules, if available

import pystray                              # puts an icon in the Windows tray
from PIL import Image, ImageDraw            # draws the little clock picture for the icon


# The places to show. Each line has:
#   the display name, the official time zone name,
#   the hours ahead of (+) or behind (-) UTC in winter, and whether the place uses daylight saving time.
# The last two are a backup, used only if the official time zone rules aren't installed.
PLACES = [
    ("Pangasinan, PH", "Asia/Manila",      +8, False),
    ("Crestview, FL",  "America/Chicago",  -6, True),   # Florida panhandle uses Central Time
    ("Medway, ME",     "America/New_York", -5, True),
]

UPDATE_EVERY_SECONDS = 20                   # how often the times refresh


def us_daylight_saving_on(utc_now, winter_offset):
    """Return True if US daylight saving time is in effect right now.

    US rule: it starts at 2 AM on the 2nd Sunday in March
    and ends at 2 AM on the 1st Sunday in November (local time).
    """
    year = utc_now.year
    march_1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    november_1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    # weekday() counts Monday as 0 and Sunday as 6, so this finds how many days until Sunday.
    second_sunday_march = march_1 + timedelta(days=(6 - march_1.weekday()) % 7 + 7)
    first_sunday_november = november_1 + timedelta(days=(6 - november_1.weekday()) % 7)
    # Convert "2 AM local" into UTC. In March the clocks still show winter time; in November, summer time.
    starts = second_sunday_march + timedelta(hours=2 - winter_offset)
    ends = first_sunday_november + timedelta(hours=2 - (winter_offset + 1))
    return starts <= utc_now < ends


def time_in(zone_name, winter_offset, uses_dst):
    """Return the current date and time in one place, as text like 'Tue Sep 29, 10:42 PM'.

    The date matters because the Philippines is usually a day ahead of the US.
    """
    try:
        # First choice: the official time zone rules (from the "tzdata" library).
        now = datetime.now(ZoneInfo(zone_name))
    except ZoneInfoNotFoundError:
        # Backup: work it out ourselves from the UTC time plus the offset.
        utc_now = datetime.now(timezone.utc)
        offset = winter_offset
        if uses_dst and us_daylight_saving_on(utc_now, winter_offset):
            offset = winter_offset + 1          # clocks "spring forward" one hour in summer
        now = utc_now + timedelta(hours=offset)
    # %a = day name, %b = month, %d = day of month, %I = hour, %M = minutes, %p = AM/PM
    # The replace() removes leading zeros, so "Sep 09, 09:05" becomes "Sep 9, 9:05".
    return now.strftime("%a %b %d, %I:%M %p").replace(" 0", " ")


def all_times():
    """Return one line of text per place, like 'Medway, ME: Tue Sep 29, 9:42 AM'."""
    lines = []
    for name, zone, winter_offset, uses_dst in PLACES:
        lines.append(f"{name}: {time_in(zone, winter_offset, uses_dst)}")
    return lines


def draw_icon():
    """Draw a simple 64x64 clock face to use as the tray icon."""
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))            # transparent square
    pen = ImageDraw.Draw(image)
    pen.ellipse((4, 4, 60, 60), fill="white", outline="navy", width=5)   # clock face
    pen.line((32, 32, 32, 14), fill="navy", width=5)             # hour hand
    pen.line((32, 32, 46, 32), fill="navy", width=4)             # minute hand
    return image


def build_menu():
    """Build the right-click menu: one line per place, a divider, then Quit."""
    items = []
    for line in all_times():
        items.append(pystray.MenuItem(line, None, enabled=False))   # enabled=False: shown, but not clickable
    items.append(pystray.Menu.SEPARATOR)
    items.append(pystray.MenuItem("Quit", quit_app))
    return pystray.Menu(*items)


def refresh(icon):
    """Update the hover text and the menu with the latest times."""
    icon.title = "\n".join(all_times())      # "\n" puts each place on its own line
    icon.menu = build_menu()


def keep_refreshing(icon, stop_signal):
    """Runs in the background: refresh, wait a bit, repeat until told to stop."""
    icon.visible = True
    while not stop_signal.is_set():
        refresh(icon)
        stop_signal.wait(UPDATE_EVERY_SECONDS)   # sleeps, but wakes up early if Quit is chosen


def quit_app(icon, item):
    """Called when you click Quit in the menu."""
    stop_signal.set()                        # tell the background loop to finish
    icon.stop()                              # remove the icon from the tray


# This is where the program actually starts running.
stop_signal = threading.Event()
icon = pystray.Icon("world_clock", draw_icon(), "World Clock")
icon.run(setup=lambda icon: keep_refreshing(icon, stop_signal))
