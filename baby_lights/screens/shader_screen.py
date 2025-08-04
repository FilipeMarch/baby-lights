"""
Shader screen for Baby Lights app.
Full-screen shader canvas with exit gesture handling.
"""

import time
from typing import Optional

from kivy.app import App
from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy_reloader.utils import load_kv_path

from baby_lights.android_utils import (
    disable_immersive_mode,
    enable_immersive_mode,
    hide_status_bar_and_extend_content,
    is_lock_task_active,
    set_navigation_bar_black,
    set_status_bar_color,
    show_status_bar_and_constrain_content,
)
from baby_lights.logger import logger
from baby_lights.popups import show_exit_confirmation
from baby_lights.uix.shader import ShaderCanvas

load_kv_path(__file__)


class ShaderScreen(Screen):
    """
    Full-screen shader screen with exit gesture handling.

    This screen shows the baby lights shader canvas and handles
    the parental exit gesture (two corners held for 3 seconds).
    """

    # Exit gesture configuration
    MIN_TOUCHES_FOR_EXIT = 2
    EXIT_HOLD_SECONDS = 0.5

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Exit gesture state
        self._exit_start: Optional[float] = None
        self._exit_event = None
        self._exit_popup_open = False  # Flag to prevent multiple popups
        self.active_touches: dict = {}  # uid → touch

        # Create shader canvas
        self.shader_canvas = ShaderCanvas()
        self.add_widget(self.shader_canvas)

    def on_enter(self):
        """Called when screen is entered."""
        logger.info('Entered shader screen - baby lights active')

        # Bind to app lifecycle events to detect when immersive mode is broken
        app = App.get_running_app()
        app.bind(on_resume=self._on_app_resume)

        # Set status bar color to match app theme
        set_status_bar_color('#F5F7FF')  # Soft blue-white

        # Set black background and hide cursor for immersive experience
        Window.clearcolor = (0, 0, 0, 1)
        Window.show_cursor = False

        # Bind touch events for exit gesture
        self._setup_window_bindings()

    def on_leave(self):
        """Called when screen is left."""
        logger.info('Left shader screen')

        # Restore normal window state
        Window.show_cursor = True

        # Unbind touch events
        self._teardown_window_bindings()

        # Unbind app lifecycle events
        app = App.get_running_app()
        app.unbind(on_resume=self._on_app_resume)

        # Reset exit gesture state
        self._reset_exit_timer()
        self._exit_popup_open = False  # Reset popup flag when leaving screen

    def _setup_window_bindings(self):
        """Set up window event bindings for exit gesture detection."""
        Window.bind(
            on_touch_down=self._on_touch_down,
            on_touch_move=self._on_touch_move,
            on_touch_up=self._on_touch_up,
        )

    def _teardown_window_bindings(self):
        """Remove window event bindings."""
        Window.unbind(
            on_touch_down=self._on_touch_down,
            on_touch_move=self._on_touch_move,
            on_touch_up=self._on_touch_up,
        )

    def _on_app_resume(self, app):
        """Handle app resume to detect immersive mode breaks."""
        logger.debug('App resumed, checking immersive mode status')
        # Use Clock to delay the check to ensure system has settled
        Clock.schedule_once(lambda dt: self._check_immersive_mode_status(), 0.5)

    def _check_immersive_mode_status(self):
        """Check if lock task is active and navigate away if not."""
        if not is_lock_task_active():
            msg = (
                'Shader screen is active but lock task is broken - '
                'navigating to main screen'
            )
            logger.warning(msg)
            self._navigate_to_main_screen()

    def _navigate_to_main_screen(self):
        """Navigate back to main screen due to broken immersive mode."""
        try:
            # First restore main screen status bar theme
            logger.info('Restoring main screen status bar theme')
            set_status_bar_color('#F5F7FF')  # Soft blue-white with dark icons

            # Then disable immersive mode and restore normal UI
            logger.info('Disabling immersive mode due to broken lock task')
            disable_immersive_mode()

            # Navigate back to main screen
            if hasattr(self.manager, 'go_back'):
                self.manager.go_back()
            else:
                # Fallback to direct screen change
                self.manager.current = 'main_screen'
            logger.info('Navigated to main screen due to broken immersive mode')
        except Exception as e:
            logger.error(f'Failed to navigate to main screen: {e}')

    # ──────────────────────────────────────────────────────────
    # Exit Gesture Handling
    # ──────────────────────────────────────────────────────────

    def _on_touch_down(self, window, touch):
        """Handle touch down for exit gesture detection."""
        self.active_touches[touch.uid] = touch
        self._check_exit_gesture()
        # Don't consume the touch - let it pass through to shader canvas
        return False

    def _on_touch_move(self, window, touch):
        """Handle touch move for exit gesture detection."""
        if touch.uid in self.active_touches:
            self.active_touches[touch.uid] = touch
            self._check_exit_gesture()
        return False

    def _on_touch_up(self, window, touch):
        """Handle touch up for exit gesture detection."""
        self.active_touches.pop(touch.uid, None)
        self._check_exit_gesture()
        return False

    def _check_exit_gesture(self):
        """Check if the exit gesture is being performed."""
        w, h = Window.size
        top_left = []
        bottom_right = []

        # Check which corners have touches
        for touch in self.active_touches.values():
            x, y = touch.x, touch.y
            if x < w * 0.15 and y > h * 0.85:  # Top-left corner
                logger.info('Touch in top-left corner')
                top_left.append(touch)
            if x > w * 0.85 and y < h * 0.15:  # Bottom-right corner
                logger.info('Touch in bottom-right corner')
                bottom_right.append(touch)

        # Check if we have touches in both corners with minimum touch count
        if (
            top_left
            and bottom_right
            and len(self.active_touches) >= self.MIN_TOUCHES_FOR_EXIT
        ):
            # Start timer if not already started
            if self._exit_start is None:
                self._exit_start = time.time()
                logger.info('Exit gesture detected, starting timer')

                # Schedule periodic check
                if self._exit_event is None:
                    self._exit_event = Clock.schedule_interval(
                        self._check_exit_timer, 0.1
                    )
        else:
            # Reset if fingers leave corners
            self._reset_exit_timer()

    def _reset_exit_timer(self):
        """Reset the exit gesture timer."""
        if self._exit_start is not None:
            logger.debug('Exit gesture timer reset')

        self._exit_start = None
        if self._exit_event is not None:
            self._exit_event.cancel()
            self._exit_event = None

    def _check_exit_timer(self, dt):
        """Check if exit gesture has been held long enough."""
        if self._exit_start is None:
            return False

        now = time.time()
        held_time = now - self._exit_start

        if held_time >= self.EXIT_HOLD_SECONDS:
            logger.info(
                f'Exit gesture held for {held_time:.1f}s - showing exit confirmation'
            )
            self._reset_exit_timer()
            self._show_exit_confirmation()
            return False  # Stop the timer

        return True  # Continue the timer

    @mainthread
    def _show_exit_confirmation(self):
        """Show exit confirmation popup with proper system bar visibility."""

        # Prevent multiple popups from appearing
        if self._exit_popup_open:
            logger.debug('Exit popup already open, ignoring request')
            return

        self._exit_popup_open = True

        # Temporarily show system bars for better popup visibility
        logger.info('Temporarily showing system bars for exit popup')

        # Force Kivy to update its viewport
        Window.update_viewport()

        # Show status bar and constrain content
        show_status_bar_and_constrain_content()

        # Set bottom navigation bar to black
        set_navigation_bar_black()

        def on_confirm():
            """Exit baby lights mode."""
            logger.info('User confirmed exit from baby lights')
            self._exit_popup_open = False  # Reset flag
            self._exit_baby_lights()

        def on_cancel():
            """Cancel exit and restore immersive mode."""
            logger.info('User cancelled exit from baby lights')
            self._exit_popup_open = False  # Reset flag

            # Restore immersive mode since user wants to continue
            logger.info('Restoring immersive mode after cancelled exit')
            hide_status_bar_and_extend_content()
            enable_immersive_mode()

        # Delay popup creation to allow Android layout changes to take effect
        def show_delayed_popup(dt):
            show_exit_confirmation(on_confirm=on_confirm, on_cancel=on_cancel)

        Clock.schedule_once(show_delayed_popup, 0.2)

    def _exit_baby_lights(self):
        """Exit baby lights mode and return to main screen."""
        logger.info('Exiting baby lights mode...')

        # Restore main screen status bar theme before navigating
        set_status_bar_color('#F5F7FF')  # Soft blue-white with dark icons

        self.manager.go_back()  # Use navigator to go back intelligently

        # Disable immersive mode
        disable_immersive_mode()
