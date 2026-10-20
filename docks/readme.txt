Heathcote for Windows

Heathcote is an interactive audio adventure told through sound, first made by Fabulae Obscurae for the iPhone and iPad.
You follow a presenter exploring an abandoned asylum, Heathcote, while he is on the phone to his producer, and you choose what he does next.
The original was played by swiping on the screen.
This is a port of it for Windows, played with the keyboard and your screen reader.

What works so far

The port is still being built, and the story cannot be played yet.
This version has the game's window, its speech through your screen reader, its menus, the key bindings and the volumes.
The original's sounds, its story and its own menus come in later versions.
Every recording ships with the game, so nothing needs downloading.

Headphones

Headphones are strongly recommended.
The original says so itself: "Heathcote is a responsive story told through sound. Headphones are strongly recommended."

Speech

The game speaks through NVDA if it is running.
Otherwise it speaks through another screen reader, such as JAWS or Narrator, and with no screen reader running, through a Windows voice.
It notices a screen reader started or closed while it runs.
Moving in a menu cuts off what was being said, so you never wait for a line to finish.
The window also shows what is said, for anyone helping you who can see the screen.

Starting the game

For now the game opens on a small main menu, with Settings and Quit.
Quit closes the game, as does closing its window.

In every menu, Up and Down move, as do Left and Right, Home and End go to the first and last row, Enter chooses, and Escape goes back.
Moving past either end of a menu wraps round to the other.
Back is always the first row of a menu that has one, and the menu opens on it.
Rows are read without their place in the menu.

Settings

Settings has Back and Key bindings.
Your settings are saved as you change them.

Volumes

The game has four volumes.
Each press of a volume key moves a volume by 10 percent and says where it is now, and holding the key keeps moving it.
Shift with Home and Shift with End turn the master volume up and down, from anywhere in the game.
The master volume sets how loud everything is together.
Page Up and Page Down turn the title volume up and down, wherever the title music plays, such as the main menu.
During the story, Page Up and Page Down turn the background volume up and down instead: the music, the ambience and the sounds that loop while you choose.
During the story, Shift with Page Up and Shift with Page Down turn the interface volume up and down: the game's own sounds and its recorded choices.
The game remembers every volume.
This version plays no sound yet, so the volumes only say their levels for now.

Key bindings

Press F1 at any time, or choose Key bindings in Settings, to change the game's keys.
Every action can be rebound, the menu keys included.
The screen opens on Back, and the actions follow it, each read with its keys.
The actions' names say where they work: Menus, Story, or Title music, and the master volume works everywhere.
Up and Down move through them, as do Left and Right, and Home and End go to the first and last.
Enter rebinds the action you are on: press the key you want, with Shift, Control or Alt if you like.
A adds another key for it instead of replacing the one it has.
Delete unbinds it.
R, then R again, resets every binding to the default; any other key after the first R keeps your bindings.
Escape, F1, or Enter on Back goes back.
The same key can do one thing in a menu and another during the story, such as Up and Escape.
If you give an action a key another action needs in the same place, the game takes it from that action and tells you which.
F1 and Escape can never be rebound, and the key bindings screen always uses its own keys, so you can always put your keys right.

Your files

Your settings and key bindings are kept in the Heathcote folder in your AppData folder, never in the game's own folder, so an update keeps them.
Every run writes a log there, in the logs folder.
If an error stops the game, it says so aloud and writes what happened to crash.txt in that logs folder.

Credits

Heathcote is Fabulae Obscurae's game, and its writers, voice actors, composer and team made everything you hear.
Story: Christian Francis and Ben Meares.
David Scott, Fausto Kaufer and Joe Banks: Hunter Davis.
Martin Fellows: Robert Dunne.
Announcer: Mark Hamilton.
Music: Jason Martin Castillo.
Design and Engineering: Mike Dean.
Producing and Directing: Lisa Wong.
Audio Consultant: Alex Ruger.
Special thanks to Nowell Valeri.
The original uses many sounds from freesound, listed at fabulaeobscurae.com/heathcote.
tsatria03 makes the Windows port.
FMOD Studio by Firelight Technologies Pty Ltd.

Licenses

The Windows port's own code uses the MIT License.
FMOD, which plays the game's sound, is Firelight Technologies Pty Ltd.'s, used under its own licence, which ships with the game.
The NVDA controller client, which speaks through NVDA, uses the GNU Lesser General Public License version 2.1, at https://github.com/nvaccess/nvda/blob/master/extras/controllerClient/license.txt
Prism, which speaks through other screen readers, uses the Mozilla Public License version 2.0, at https://github.com/ethindp/prism
CFFI, which Prism uses to reach its library, uses the MIT License, at https://github.com/python-cffi/cffi/blob/main/LICENSE
Pygame, which runs the window and the keyboard, uses the GNU Lesser General Public License version 2.1, at https://github.com/pygame/pygame/blob/main/docs/LGPL.txt
Pyfmodex, which connects the game to FMOD, uses the MIT License, at https://github.com/tyrylu/pyfmodex
The game's recordings and story are Fabulae Obscurae's, and are not covered by those licenses.
