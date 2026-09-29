# World Clock (Windows tray app)

Shows the current date and time in Pangasinan (Philippines), Crestview (Florida), and Medway (Maine)
from an icon in the Windows 11 taskbar tray.

- **Hover** over the clock icon to see all three times.
- **Right-click** it for a menu with the times and **Quit**.

## One-time setup

1. Install Python from https://www.python.org/downloads/ (or from the Microsoft Store).
   Newer installers set everything up automatically. Older installers show an
   **"Add python.exe to PATH"** checkbox on the first screen; tick it if you see it.
2. Download this `world_clock` folder to your computer.
3. Open the folder in File Explorer, click the address bar, type `cmd`, and press Enter.
   A black Command Prompt window opens in that folder.
4. Check that Python is working. Type this and press Enter:

   ```
   python --version
   ```

   You should see something like `Python 3.14.0`. If you get "not recognized", try `py --version` instead.
   If that works, use `py` in place of `python` in the next step.
5. Type this and press Enter (it downloads the three helper libraries the app needs):

   ```
   python -m pip install -r requirements.txt
   ```

## Running it

Double-click `world_clock.pyw`. The clock icon appears in the tray.
If you don't see it, click the small **^** arrow next to the tray icons.
You can drag the icon out of that pop-up onto the taskbar to keep it visible.

## Starting it automatically when Windows starts

1. Press **Windows key + R**, type `shell:startup`, and press Enter. The Startup folder opens.
2. Right-click an empty spot in that folder → **New** → **Shortcut**.
3. For the location, enter the full path to `pythonw.exe` followed by the full path to `world_clock.pyw`,
   each in quotes, with a space between. For example:

   ```
   "C:\Users\YourName\AppData\Local\Programs\Python\Python312\pythonw.exe" "C:\path\to\world_clock\world_clock.pyw"
   ```

   `pythonw.exe` runs the app without a Command Prompt window. Naming it directly also avoids
   Windows opening the file in a text editor instead of running it.
4. Click **Next**, name it `World Clock`, and click **Finish**.

If you later move or delete the `world_clock` folder, update or delete this shortcut too.
