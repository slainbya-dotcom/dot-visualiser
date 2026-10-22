# Building Dot Visualiser

The `.msi` has to be built on Windows and the `.dmg` on macOS. The steps are the same as for Dot Clock.

## build locally

### Windows (makes the .msi)

1. Install the tools once, from Terminal. Skip this if you've already built one of the other apps on this PC:

   ```powershell
   winget install OpenJS.NodeJS.LTS
   winget install Rustlang.Rustup
   winget install Microsoft.VisualStudio.2022.BuildTools --override "--wait --passive --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended"
   ```

2. Open a terminal in this folder. In File Explorer, type `powershell` in the address bar of the folder that contains `package.json`.
3. Run:

   ```powershell
   npm install
   npm run build:win
   ```

4. The installer is written to `src-tauri\target\release\bundle\msi\Dot Visualiser_1.0.0_x64_en-US.msi`.

### macOS (makes a universal .dmg)

```bash
rustup target add aarch64-apple-darwin x86_64-apple-darwin
npm install
npm run build:mac
```

The `.dmg` is written to `src-tauri/target/universal-apple-darwin/release/bundle/dmg/`.

For development, `npm run dev` runs the app with live reload. `npm test` runs the logic tests in Node, which cover decibels and sensitivity, the bars jumping and falling, silence, the scope's auto-gain, every style's size with and without the track line, scrolling, colours, margins at every width and settings repair.

## Project layout

```
src/                 UI (no build step)
  index.html         the widget window
  settings.html      the settings window
  js/viz.js          smoothing the sound, the five styles, simulated music for previews
  js/dotmatrix.js    5×7 font, Dot Clock's layout, the row + loading bar
  js/worldtime.js    reads Dot Clock's settings and measures its widget
  js/time.js         time-zone helpers (needed to measure Dot Clock's rows)
  js/store.js        settings model + bridge to the native shell
src-tauri/           native shell (Rust), config, icons, capabilities
  src/audio.rs       listens to the sound and splits it into 32 frequency bands
  src/media/         what's playing (shared with Dot Player), for the track line
  Info.plist         the messages macOS shows when asking for the microphone / Spotify / Music
tools/               icon generator, preview builder
tests/               Node tests
```

## Things to know

- **The link to Dot Clock is by identifier.** "Match Dot Clock" finds Dot Clock's settings using its app identifier, `app.worldtime.dotmatrix`. If you change that identifier in Dot Clock's `tauri.conf.json`, also change `WORLD_TIME_ID` at the top of `src-tauri/src/lib.rs` here.
- **Sound capture uses the `cpal` library; the frequencies come from `rustfft`.** On Windows, opening the speakers "for input" is how system audio (loopback) works, so no extra driver or permission is needed. On macOS it listens to an input device; macOS asks for microphone permission the first time.
- **macOS asks permission once per player** for the track line. If someone clicks **Don't Allow**, turn it back on in **System Settings › Privacy & Security › Automation › Dot Visualiser**.
- **The installers aren't code-signed.** As with Dot Clock, Windows will show a SmartScreen warning and macOS needs **Privacy & Security › Open Anyway**.
- **Replace the placeholder identifier** `app.worldtime.dotvisualiser` in `src-tauri/tauri.conf.json` if you like.
- **The Windows build uses the `windows` Rust library**, pinned to an exact version (`=0.58.0`) because its functions change between releases. If you update it, expect small edits in `src-tauri/src/media/win.rs`.
