TVA BARKLEY DAM WELD INSPECTION SYSTEM
Portable Edition — Customer Instructions
========================================

WHAT IS THIS?
-------------
This folder contains the TVA Barkley Dam Weld Inspection System — a web-based
application for tracking, reviewing, and exporting weld inspection records and
photos for the Barkley Dam project. Everything needed to run the app is included
in this folder. No internet connection is required to run it (see note below).


SYSTEM REQUIREMENTS
-------------------
- Windows 10 or Windows 11 (64-bit)
- That's it! No Python, no databases, no other software to install.


GETTING STARTED
---------------

STEP 1 — Create your admin login (first time only)
  Double-click SETUP_USER.bat
  Follow the prompts to enter a username and password.
  You only need to do this once.

STEP 2 — Start the application
  Double-click START.bat
  A black command window will open and the app will start automatically.
  After a few seconds, your web browser will open to http://localhost:8000
  Log in with the username and password you created in Step 1.

STEP 3 — Use the app
  The app runs in your web browser just like a website.
  Keep the black START.bat window open while you use the app.


STOPPING THE APP
----------------
To stop the server:
  Option A: Close the black START.bat window.
  Option B: Double-click STOP.bat from another window.

The app will stop and the local server will shut down. Your data is saved
automatically in the database file (app\db.sqlite3).


IMPORTING WELD DATA
-------------------
To import weld data from an Excel spreadsheet:

  1. Start the app (run START.bat)
  2. Open a second command window (press Windows+R, type cmd, press Enter)
  3. Change to the app folder:
       cd /d "X:\TVA-Weld-Inspector\app"
     (replace X: with the actual drive letter of this folder)
  4. Run the import command:
       ..\python\python.exe manage.py import_welds "C:\path\to\your\data.xlsx"

To import weld photos:
       ..\python\python.exe manage.py import_photos "C:\path\to\photos\"


ACCESSING FROM OTHER COMPUTERS ON THE SAME NETWORK
---------------------------------------------------
If you want other computers on your local network to access the app
while it is running on your PC:

  1. Find your PC's local IP address:
     Open a command window and type: ipconfig
     Look for "IPv4 Address" — it will look like 192.168.1.x

  2. On the other computer, open a browser and go to:
     http://192.168.1.x:8000
     (replace 192.168.1.x with your actual IP address)

  3. Make sure Windows Firewall allows connections on port 8000.
     If asked, click "Allow access".

NOTE: This only works while the START.bat window is open on the host PC.


ABOUT INTERNET CONNECTIVITY
----------------------------
The app itself does NOT require an internet connection to run.

IMPORTANT NOTE about styling: The app's visual styling (Bootstrap CSS framework)
is loaded from the internet (cdnjs.cloudflare.com). This means:
- On a PC with internet access: the app looks fully styled with the dark navy theme.
- On a PC WITHOUT internet: the app works correctly but will appear plain/unstyled
  (no colors, basic layout). All data, filters, exports, and photos still work.

The weld data, database, and photos are all stored locally in this folder.
No weld data is ever sent to the internet.


TROUBLESHOOTING
---------------

Problem: "Port 8000 is already in use" error when starting
Solution: Run STOP.bat to stop any previous server instance, then try again.
          Or restart your computer and try START.bat again.

Problem: The browser doesn't open automatically
Solution: Open your browser manually and go to http://localhost:8000

Problem: "Access denied" or the browser shows an error page
Solution: Make sure START.bat is still open and the server is running.
          Wait a few extra seconds after starting before trying the browser.

Problem: Login page appears but username/password not accepted
Solution: Run SETUP_USER.bat again to create or reset the admin account.

Problem: App opens but looks unstyled (plain text, no colors)
Solution: Check your internet connection — Bootstrap is loaded from the web.

Problem: Photos are not showing
Solution: Make sure the media\ folder is present inside the app\ folder.
          If photos were stored separately, copy them to app\media\weld_photos\

Problem: "python.exe not found" error
Solution: The portable Python folder may be missing or damaged.
          Contact your system administrator to re-run the packaging script.


FOLDER STRUCTURE
----------------
TVA-Weld-Inspector\
  START.bat         — Double-click to start the app
  STOP.bat          — Double-click to stop the app
  SETUP_USER.bat    — Run once to create your admin login
  README.txt        — This file
  python\           — Portable Python (do not modify)
  app\
    manage.py       — Django management script
    db.sqlite3      — Your weld inspection database
    media\          — Uploaded weld photos
    staticfiles\    — App styling and assets
    weldmap\        — App configuration
    welds\          — Weld records module
    gallery\        — Photo gallery module


SUPPORT
-------
For technical support, contact the application developer.
App version: TVA Barkley Weld Map — Portable Edition
