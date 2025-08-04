"""
Baby Lights Button Component

A custom Kivy button widget following shadcn/ui conventions with baby-specific variants.
Includes baby-themed styling with soft shadows, rounded corners, and smooth animations.

Visual styling is defined in baby_button.kv following Kivy best practices.
"""

from kivy.animation import Animation
from kivy.properties import ListProperty, StringProperty
from kivy.uix.button import Button
from kivy_reloader.utils import load_kv_path

# Load the KV file for styling
load_kv_path(__file__)


class BabyButton(Button):
    """
    Custom button following shadcn/ui conventions with baby-specific variants.

    Theme variants (semantic color schemes):
        - default: Primary brand color
        - secondary: Secondary actions (gray)
        - destructive: Dangerous actions (red)
        - outline: Border-only style
        - baby: Special baby-themed pastels

    Size variants (relative sizing):
        - sm: Small/compact
        - default: Standard size
        - lg: Large/prominent
        - baby: Extra large for little fingers
    """

    # Kivy properties for KV binding
    bg_color = ListProperty([0.3, 0.4, 0.8, 1])  # Default primary blue
    theme = StringProperty('default')
    button_size = StringProperty('default')

    # Color schemes following shadcn/ui conventions
    COLORS = {
        'default': {
            'bg': [0.3, 0.4, 0.8, 1],  # Primary blue
            'fg': [1, 1, 1, 1],  # White text
            'hover': [0.35, 0.45, 0.85, 1],  # Lighter blue
            'active': [0.25, 0.35, 0.75, 1],  # Darker blue
        },
        'secondary': {
            'bg': [0.9, 0.9, 0.9, 1],  # Light gray
            'fg': [0.2, 0.2, 0.2, 1],  # Dark gray text
            'hover': [0.85, 0.85, 0.85, 1],  # Darker gray
            'active': [0.8, 0.8, 0.8, 1],  # Even darker gray
        },
        'destructive': {
            'bg': [0.9, 0.3, 0.3, 1],  # Red
            'fg': [1, 1, 1, 1],  # White text
            'hover': [0.85, 0.35, 0.35, 1],  # Lighter red
            'active': [0.8, 0.25, 0.25, 1],  # Darker red
        },
        'outline': {
            'bg': [0, 0, 0, 0],  # Transparent
            'fg': [0.3, 0.4, 0.8, 1],  # Primary blue text
            'hover': [0.95, 0.97, 1, 1],  # Very light blue bg
            'active': [0.9, 0.94, 1, 1],  # Slightly darker bg
        },
        'baby': {
            'bg': [1, 0.8, 0.9, 1],  # Soft pink
            'fg': [0.4, 0.2, 0.4, 1],  # Dark purple text
            'hover': [1, 0.85, 0.92, 1],  # Lighter pink
            'active': [0.95, 0.75, 0.85, 1],  # Darker pink
        },
    }

    def __init__(self, **kwargs):
        # Extract custom properties before calling super
        self.theme = kwargs.pop('theme', 'default')
        self.button_size = kwargs.pop('button_size', 'default')

        super().__init__(**kwargs)

        # Internal state
        self._is_pressed = False

        # Set initial colors based on theme
        self._update_colors()

        # Bind theme changes to color updates
        self.bind(theme=self._on_theme_change)

    def _on_theme_change(self, instance, theme):
        """Called when theme property changes."""
        self._update_colors()

    def _update_colors(self):
        """Update colors based on current state and theme."""
        color_scheme = self.COLORS.get(self.theme, self.COLORS['default'])

        # Set text color
        self.color = color_scheme['fg']

        # Set background color based on state
        if self._is_pressed:
            target_color = color_scheme['active']
        else:
            target_color = color_scheme['bg']

        # Animate background color change
        if hasattr(self, 'bg_color'):
            anim = Animation(
                bg_color=target_color, duration=0.2, transition='out_cubic'
            )
            anim.start(self)
        else:
            self.bg_color = target_color

    def on_touch_down(self, touch):
        """Handle touch down with press animation."""
        if self.collide_point(*touch.pos):
            self._is_pressed = True
            self._update_colors()

            # Scale down animation for press feedback
            anim = Animation(
                size=(self.width * 0.95, self.height * 0.95),
                duration=0.1,
                transition='out_cubic',
            )
            anim.start(self)

        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        """Handle touch up with release animation."""
        if self._is_pressed:
            self._is_pressed = False
            self._update_colors()

            # Scale back to normal
            anim = Animation(
                size=(self.width / 0.95, self.height / 0.95),
                duration=0.1,
                transition='out_cubic',
            )
            anim.start(self)

        return super().on_touch_up(touch)

    def set_theme(self, theme):
        """Change button theme dynamically."""
        if theme in self.COLORS:
            self.theme = theme

    def set_button_size(self, size):
        """Change button size dynamically."""
        self.button_size = size
