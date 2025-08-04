import time

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics import Rectangle, RenderContext
from kivy.properties import NumericProperty
from kivy.uix.widget import Widget

# ────────────────────────────
# OpenGL shader (GLSL ES 3.0‑compatible)
# Touch‑centric radial glow with smooth fall‑off.
# ‑ uniform touch.xy ∈ [0,1] (normalised) or (−1,−1) when inactive.
# ‑ uniform time      – for subtle animation.
# ────────────────────────────
_FRAG_SHADER = """
#ifdef GL_ES
precision mediump float;
#endif

uniform vec2 resolution;   // Window size in px
uniform float time;        // Seconds
uniform vec2 touch;        // Normalised [0,1] of last touch (-1 when none)
uniform float fade;        // Opacity fade value (0..1)

void main() {
    vec2 uv = gl_FragCoord.xy / resolution;

    float d = distance(uv, touch);
    float glow = smoothstep(0.25, 0.0, d);      // inner-outer radius

    // animated hue shift for subtle variation
    float hue = mod(time*0.07 + d*3.0, 1.0);
    vec3 col = vec3(
        abs(hue*6.0-3.0)-1.0,
        2.0-abs(hue*6.0-2.0),
        2.0-abs(hue*6.0-4.0)
    );
    col = clamp(col, 0.0, 1.0);

    // Opacity fades linearly to 0 after 5 seconds since last touch
    gl_FragColor = vec4(col * glow, glow * fade);
}
"""


class ShaderCanvas(Widget):
    """Full-screen GLSL canvas reacting to touches."""

    MAX_GLOWS = 10  # Limit number of simultaneous glows

    _t0 = NumericProperty(time.time())  # start time for animation

    def __init__(self, **kw):
        super().__init__(**kw)
        self._contexts = []  # Store active touches: {"ctx", "t0", "pos", "rect"}
        self._ctx = RenderContext(use_parent_projection=True, fs=_FRAG_SHADER)
        self.canvas = self._ctx

        Clock.schedule_interval(self._update_shader, 0)  # every frame
        Window.bind(on_touch_down=self._on_touch, on_touch_move=self._on_touch)

    def _on_touch(self, _window, touch):
        pos = (touch.x / float(self.width), touch.y / float(self.height))
        # Remove oldest if over limit
        if len(self._contexts) >= self.MAX_GLOWS:
            oldest = self._contexts.pop(0)
            self.canvas.remove(oldest['ctx'])
        ctx = RenderContext(use_parent_projection=True, fs=_FRAG_SHADER)
        rect = Rectangle(size=self.size, pos=self.pos)
        ctx.add(rect)
        self.canvas.add(ctx)
        self._contexts.append({
            'ctx': ctx,
            't0': time.time(),
            'pos': pos,
            'rect': rect,
        })

    def _update_shader(self, _dt):
        elapsed = time.time() - self._t0
        for c in self._contexts[:]:
            ctx = c['ctx']
            since_touch = time.time() - c['t0']
            fade = max(0.0, 1.0 - since_touch / 5.0)
            if fade <= 0:
                self.canvas.remove(ctx)
                self._contexts.remove(c)
                continue
            ctx['time'] = elapsed
            ctx['resolution'] = list(map(float, self.size))
            ctx['touch'] = list(c['pos'])
            ctx['fade'] = fade
            c['rect'].size = self.size
            c['rect'].pos = self.pos
            c['rect'].pos = self.pos
