# World Clock (Windows tray app)

Shows the current date and time in Pangasinan (Philippines), Crestview (Florida), and Medway (Maine)
from an icon in the Windows 11 taskbar tray.

- **Hover** over the clock icon to see all three times.
- **Right-click** it for a menu with the times and **Quit**.

## One-time setup

1. Install Python from https://www.python.org/downloads/.
   On the first installer screen, tick **"Add python.exe to PATH"**.
2. Download this `world_clock` folder to your computer.
3. Open the folder in File Explorer, click the address bar, type `cmd`, and press Enter.
   A black Command Prompt window opens in that folder.
4. Type this and press Enter (it downloads the three helper libraries the app needs):

   ```
   pip install -r requirements.txt
   ```

## Running it

Double-click `world_clock.pyw`. The clock icon appears in the tray.
If you don't see it, click the small **^** arrow next to the tray icons.
You can drag the icon out of that pop-up onto the taskbar to keep it visible.

## Starting it automatically when Windows starts

1. Right-click `world_clock.pyw` → **Show more options** → **Create shortcut**.
2. Press **Windows key + R**, type `shell:startup`, and press Enter.
3. Move the shortcut into the folder that opens.
