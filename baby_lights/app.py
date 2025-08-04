from kivy.clock import Clock, mainthread
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.utils import platform
from kivy_reloader.app import App

from baby_lights.logger import logger
from baby_lights.navigator import Navigator


class BabyLightsApp(App):
    """Main Kivy application."""

    def build(self):
        """Build the application with screen manager."""
        self.setup_window()
        self.setup_screen_manager()

        # Create the navigator with all possible screen destinations
        self.navigator = Navigator(
            destinations=['main_screen', 'shader_screen'],
            fallbacks={'shader_screen': 'main_screen'},  # Back from shader goes to main
            initial_destination='main_screen',
        )

        self.change_screen('Main Screen')  # Load main screen initially
        logger.info('Baby Lights app initialized')
        return self.screen_manager

    def setup_screen_manager(self):
        """Set up the screen manager with lazy loading support."""
        screen_manager = ScreenManager()

        # Add change_screen method to screen manager for easy access from screens
        screen_manager.change_screen = self.change_screen
        screen_manager.go_back = self.go_back

        self.screen_manager = screen_manager

    def setup_window(self):
        """Set up the main window properties."""
        if platform != 'android':
            # set the initial position
            Window._set_window_pos(50, 50)

    def change_screen(
        self, screen_name: str, mode: str = 'push', direction: str = 'right', **kwargs
    ) -> bool:
        """
        Change to a screen with lazy loading support.

        This method can be called from anywhere:
        - From app: app.change_screen("Shader Screen")
        - From screen: self.manager.change_screen("Shader Screen")

        Args:
            screen_name: Screen name (human readable like "Shader Screen")
            mode: Navigation mode ('push' or 'replace')
            direction: Transition direction ('right', 'left', 'up', 'down')
            **kwargs: Additional arguments for screen creation

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        # Convert human readable name to screen identifier
        screen_id = self._screen_name_to_id(screen_name)

        # Lazy load screen if it doesn't exist
        if screen_id not in self.screen_manager.screen_names:
            screen_object = self._create_screen_object(screen_name, **kwargs)
            if screen_object is None:
                logger.error(f'Failed to create screen: {screen_name}')
                return False

            screen_object.name = screen_id
            self.screen_manager.add_widget(screen_object)
            logger.info(f'Lazy loaded screen: {screen_name} ({screen_id})')

        # Set transition direction before navigating
        self.screen_manager.transition.direction = direction

        # Navigate using the navigator
        success = self.navigate_to(screen_id, mode)
        if success:
            logger.info(f'Screen transition: {direction}')
        return success

    @staticmethod
    def _screen_name_to_id(screen_name: str) -> str:
        """
        Convert human readable screen name to screen ID.

        Examples:
        - "Shader Screen" -> "shader_screen"
        - "Main Screen" -> "main_screen"
        - "Settings" -> "settings"
        """
        return '_'.join(word.lower() for word in screen_name.split())

    def _create_screen_object(self, screen_name: str, **kwargs):
        """
        Create a screen object from screen name with lazy import.

        Args:
            screen_name: Human readable screen name
            **kwargs: Additional arguments for screen creation

        Returns:
            Screen object or None if creation failed
        """
        try:
            # Convert screen name to module and class names
            screen_id = self._screen_name_to_id(screen_name)
            class_name = ''.join(word.capitalize() for word in screen_name.split())

            # Dynamic import
            module_path = f'baby_lights.screens.{screen_id}'
            module = __import__(module_path, fromlist=[class_name])
            screen_class = getattr(module, class_name)

            # Create instance
            return screen_class(**kwargs)

        except (ImportError, AttributeError) as e:
            logger.error(f'Failed to import screen {screen_name}: {e}')
            return None

    def navigate_to(self, destination: str, mode: str = 'push') -> bool:
        """
        Navigate to a destination using the Navigator component.

        Args:
            destination: Screen name to navigate to
            mode: Navigation mode ('push' or 'replace')

        Returns:
            bool: True if navigation was successful, False otherwise
        """
        try:
            # Update navigator state
            self.navigator.navigate(destination, mode)

            # Update screen manager to match navigator state
            current_destination = self.navigator.current()
            if current_destination in self.screen_manager.screen_names:
                # Don't set direction here - it should be set by the calling method
                self.screen_manager.current = current_destination
                logger.info(f'Navigated to {current_destination} (mode: {mode})')
                return True
            else:
                logger.error(
                    f'Screen {current_destination} not found in screen manager'
                )
                return False

        except ValueError as e:
            logger.error(f'Navigation failed: {e}')
            return False

    def go_back(self) -> bool:
        """
        Navigate back using the Navigator component.

        Returns:
            bool: True if back navigation was successful, False otherwise
        """
        if self.navigator.back():
            current_destination = self.navigator.current()
            if current_destination in self.screen_manager.screen_names:
                # Set transition direction to left for back navigation
                self.screen_manager.transition.direction = 'left'
                self.screen_manager.current = current_destination
                logger.info(
                    f'Navigated back to {current_destination} (direction: left)'
                )
                return True
            else:
                logger.error(
                    f'Screen {current_destination} not found in screen manager'
                )
                return False
        else:
            logger.info('No back navigation available')
            return False

    def get_current_screen(self) -> str:
        """Get the current screen name from navigator."""
        return self.navigator.current()

    def can_go_back(self) -> bool:
        """Check if back navigation is possible."""
        return self.navigator.can_go_back()

    def on_resume(self):
        Clock.schedule_once(self.restore_screen, 1)
        return True

    @mainthread
    def restore_screen(self, *args):
        logger.info('Restoring screen after resume')
        Window.update_viewport()

        # Reapply screen-specific styling based on current screen
        current_screen = self.screen_manager.current_screen
        if hasattr(current_screen, 'update_status_bar'):
            logger.info(f'Reapplying status bar styling for {current_screen.name}')
            current_screen.update_status_bar()
        else:
            logger.info(f'No update_status_bar method for {current_screen.name}')
