from kivy.app import App
from kivy.clock import mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import Screen
from kivy_reloader.utils import load_kv_path

from baby_lights.android_utils import (
    enable_immersive_mode,
    hide_status_bar_and_extend_content,
    set_navigation_bar_black,
    set_status_bar_color,
    show_status_bar_and_constrain_content,
)
from baby_lights.logger import logger
from baby_lights.popups import show_confirmation_popup, show_info_popup

load_kv_path(__file__)


class MainScreen(Screen):
    """Main screen of the Baby Lights app."""

    def on_pre_enter(self):
        """Called when entering this screen."""
        self.update_status_bar()

    @mainthread
    @staticmethod
    def update_status_bar(*args):
        try:
            logger.info('Updating status bar for main screen')

            # Force Kivy to update its viewport
            Window.update_viewport()

            # Show status bar and constrain content
            show_status_bar_and_constrain_content()

            # Set status bar color to soft blue-white
            set_status_bar_color('#F5F7FF')

            # Set bottom navigation bar to black
            set_navigation_bar_black()

        except Exception as e:
            logger.error(f'Failed to update status bar: {e}')

    def show_start_confirmation(self):
        """Show confirmation popup before starting immersive mode."""

        def on_confirm():
            """Start immersive mode when confirmed."""
            self.start_immersive_mode()

        def on_cancel():
            """Do nothing when cancelled."""
            logger.info('User cancelled starting immersive mode')

        show_confirmation_popup(
            title='Start Baby Lights',
            message='This will start immersive mode and pin the app.\n\n'
            'To exit later, press and hold both corners\n'
            '(top-left and bottom-right) for 0.5 seconds.',
            confirm_text='Start',
            cancel_text='Cancel',
            on_confirm=on_confirm,
            on_cancel=on_cancel,
        )

    def show_about_popup(self):
        """Show an info popup about the app."""
        show_info_popup(
            title='About Baby Lights',
            message='Baby Lights is designed to provide a distraction-free, '
            'non-addictive visual for babies who briefly handle a '
            "parent's phone, preventing accidental actions.\n\n"
            'No data is collected. No sounds, ads, or tracking.',
            ok_text='Got it',
        )

    def start_immersive_mode(self):
        """
        Start the immersive baby lights mode.

        This will enable immersive sticky mode and pin the app
        to prevent accidental exits.
        """
        logger.info('Starting Baby Lights immersive mode...')

        # Enable Android immersive mode
        success = enable_immersive_mode()

        if success:
            logger.info('Immersive mode started successfully')
            # TODO: Switch to baby lights screen or start shader canvas
            # Hide status bar and extend content to fill the space
            hide_status_bar_and_extend_content()
            self._start_baby_lights_canvas()
        else:
            logger.warning('Failed to enable immersive mode, continuing anyway')
            # Still start the baby lights even if immersive mode failed
            self._start_baby_lights_canvas()

    def _start_baby_lights_canvas(self):
        """Start the actual baby lights shader canvas."""
        logger.info('Starting baby lights canvas...')

        # Use the new change_screen method to lazy load the shader screen
        if hasattr(self.manager, 'change_screen'):
            success = self.manager.change_screen('Shader Screen', mode='push')
            if not success:
                logger.error('Failed to navigate to shader screen')
                print('Navigation to shader screen failed!')
        else:
            # Fallback to app method
            app = App.get_running_app()
            if hasattr(app, 'change_screen'):
                success = app.change_screen('Shader Screen', mode='push')
                if not success:
                    logger.error('Failed to navigate to shader screen')
                    print('Navigation to shader screen failed!')
            else:
                logger.error('No change_screen method available')
                print('Change screen method not available!')
