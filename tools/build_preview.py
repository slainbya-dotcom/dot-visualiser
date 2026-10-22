"""Inlines CSS/JS into single-file HTML previews (with a fake Tauri bridge and
sample settings) so the UI can be checked in any browser without building.

  python3 tools/build_preview.py [out_dir] [path/to/dot-clock]

If the Dot Clock project is given, also writes visualiser-side-by-side.html showing all five styles under Dot Clock
widgets together, with Dot Visualiser matching Dot Clock's look."""
import html, json, os, re, sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "preview")
WT_ROOT = sys.argv[2] if len(sys.argv) > 2 else None
os.makedirs(OUT, exist_ok=True)

WORLD_TIME_SAMPLE = {
    "clocks": [
        {"id": "h", "label": "London, UK", "tz": "Europe/London", "lat": 51.51, "lng": -0.13, "home": True},
        {"id": "a", "label": "New York, USA", "tz": "America/New_York", "lat": 40.71, "lng": -74.01},
        {"id": "b", "label": "Tokyo, Japan", "tz": "Asia/Tokyo", "lat": 35.68, "lng": 139.69},
    ],
    "use24h": True, "dotColor": "#ffb000", "dotSize": 3, "bgColor": "#101010", "bgOpacity": 0.85,
}

TIMER_SAMPLE_JS = """({ matchWorldTime: %(match)s, style: '%(style)s', track: { bars: false, mirror: false, scope: false, vu: false, falls: true } })"""


def shim(match=True, style="bars"):
    state_js = TIMER_SAMPLE_JS % {"match": "true" if match else "false", "style": style}
    return """<script>
var __state = JSON.stringify(%s);
window.__TAURI__ = {
  core: { invoke: async (cmd, args) => {
    if (cmd === 'load_state') return __state;
    if (!window.__sim) { window.__sim = WT.viz.simulator(); window.__t0 = Date.now(); }
    if (cmd === 'audio_frame') return Object.assign(window.__sim((Date.now() - window.__t0) / 1000), { device: 'Speakers (preview)' });
    if (cmd === 'audio_sources') return ['system', 'Microphone Array'];
    if (cmd === 'set_audio_source') return;
    if (cmd === 'read_player') return { available: true, source: 'Preview', title: 'Neon Harbour', artist: 'The Low Satellites', playing: true, position: 0, duration: 0 };
    if (cmd === 'read_world_time') return %s;
    if (cmd === 'save_state') { __state = args.json; return; }
  } },
  event: { listen: async () => () => {} },
  window: { getCurrentWindow: () => ({ setSize: async () => {}, setAlwaysOnTop: async () => {}, startDragging: async () => {} }) },
  dpi: { LogicalSize: function (w, h) { this.width = w; this.height = h; } },
};
</script>""" % (state_js, json.dumps(json.dumps(WORLD_TIME_SAMPLE)))


def inline(root, name, head=""):
    src = open(os.path.join(root, "src", name), encoding="utf-8").read()
    src = re.sub(r'<link rel="stylesheet" href="([^"]+)">',
                 lambda m: "<style>" + open(os.path.join(root, "src", m.group(1)), encoding="utf-8").read() + "</style>", src)
    src = re.sub(r'<script src="([^"]+)"></script>',
                 lambda m: "<script>" + open(os.path.join(root, "src", m.group(1)), encoding="utf-8").read()
                 .replace("</script", "<\\/script") + "</script>", src)
    return src.replace("</head>", head + "</head>", 1)


DESK = "<style>body{min-height:100vh;padding:24px;background:linear-gradient(135deg,#3a6186,#89253e)!important}</style>"
open(os.path.join(OUT, "visualiser-widget-preview.html"), "w", encoding="utf-8").write(inline(ROOT, "index.html", DESK + shim()))
open(os.path.join(OUT, "visualiser-settings-preview.html"), "w", encoding="utf-8").write(inline(ROOT, "settings.html", shim()))

if WT_ROOT:
    wt_shim = """<script>window.__TAURI__ = { core: { invoke: async (c) => c === 'load_state' ? %s : undefined },
      event: { listen: async () => () => {} },
      window: { getCurrentWindow: () => ({ setSize: async () => {}, setAlwaysOnTop: async () => {}, startDragging: async () => {} }) },
      dpi: { LogicalSize: function () {} } };</script>""" % json.dumps(json.dumps(WORLD_TIME_SAMPLE))
    wt_doc = inline(WT_ROOT, "index.html", wt_shim)
    styles = [("bars", "A · Spectrum columns", 85), ("mirror", "B · Mirror", 88), ("scope", "C · Oscilloscope", 82),
              ("vu", "D · VU meters", 76), ("falls", "E · Waterfall, with what's playing ticked", 96)]
    frames = "".join('<div class="cap">%s</div><iframe style="height:%dpx" srcdoc="%s"></iframe>\n'
                     % (t, h, html.escape(inline(ROOT, "index.html", shim(True, sid)), quote=True)) for sid, t, h in styles)
    page = """<!doctype html><html><head><meta charset="utf-8"><title>Side by side</title>
<style>body{margin:0;min-height:100vh;padding:24px;box-sizing:border-box;background:linear-gradient(135deg,#3a6186,#89253e);
font:12px system-ui;color:#fff}iframe{border:0;display:block;background:transparent;width:100%%;}
.cap{opacity:.75;margin:12px 0 4px}</style></head><body>
<div class="cap">Dot Clock</div><iframe id="a" style="height:100px" srcdoc="%s"></iframe>
%s
<div class="cap">Dot Visualiser (matching Dot Clock). Simulated music in this preview.</div>
</body></html>""" % (html.escape(wt_doc, quote=True), frames)
    open(os.path.join(OUT, "visualiser-side-by-side.html"), "w", encoding="utf-8").write(page)

print("previews written to", os.path.abspath(OUT))
