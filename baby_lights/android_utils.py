"""
Android system integration utilities.
Handles immersive mode and screen pinning functionality.
"""

from kivy.utils import platform

try:
    from android.runnable import run_on_ui_thread
except ImportError:
    # Fallback decorator if not available
    def run_on_ui_thread(func):
        return func


# Conditional import for Android-specific modules
if platform == 'android':
    try:
        from jnius import PythonJavaClass, autoclass, cast, java_method
    except ImportError:
        pass

from baby_lights.logger import logger


def hide_status_bar_and_extend_content():
    if platform != 'android':
        return False
    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        VERSION = autoclass('android.os.Build$VERSION')
        View = autoclass('android.view.View')
        Color = autoclass('android.graphics.Color')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')

        activity = cast('android.app.Activity', PythonActivity.mActivity)

        @run_on_ui_thread
        def setup_ui():
            window = activity.getWindow()
            decor = window.getDecorView()

            # 1) Remove legacy/fullscreen flags that block edge-to-edge
            window.clearFlags(
                LayoutParams.FLAG_FULLSCREEN
                | LayoutParams.FLAG_LAYOUT_NO_LIMITS
                | LayoutParams.FLAG_TRANSLUCENT_STATUS
                | LayoutParams.FLAG_TRANSLUCENT_NAVIGATION
            )

            # 2) Allow the app to draw behind system bars
            if VERSION.SDK_INT >= 30:
                window.setDecorFitsSystemWindows(False)

                # Make bars transparent so content actually occupies that area
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
                window.setStatusBarColor(Color.TRANSPARENT)
                window.setNavigationBarColor(Color.TRANSPARENT)

                # Opt into display cutout area (notches)
                if VERSION.SDK_INT >= 28:
                    window.getAttributes().layoutInDisplayCutoutMode = (
                        LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES
                    )
                    window.setAttributes(window.getAttributes())

                # Hide bars using WindowInsetsController
                WindowInsets = autoclass('android.view.WindowInsets$Type')
                WindowInsetsController = autoclass(
                    'android.view.WindowInsetsController'
                )
                controller = window.getInsetsController()
                if controller:
                    controller.hide(
                        WindowInsets.statusBars() | WindowInsets.navigationBars()
                    )
                    controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE
                    )
            else:
                # Legacy best-effort for < API 30
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)
                window.setStatusBarColor(Color.TRANSPARENT)
                window.setNavigationBarColor(Color.TRANSPARENT)

                flags = (
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                )
                decor.setSystemUiVisibility(flags)

            logger.info('Edge-to-edge enabled; status bar area now usable.')

        setup_ui()
        return True
    except Exception as e:
        logger.error(f'Failed to enable edge-to-edge: {e}')
        return False


def show_status_bar_and_constrain_content():
    """
    Show the status bar and constrain content to the safe area.

    This does the opposite of hide_status_bar_and_extend_content():
    - Shows status bar and navigation bar
    - Constrains content to fit between system bars (normal windowed mode)
    - Restores standard Android app behavior
    """
    if platform != 'android':
        return False

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        VERSION = autoclass('android.os.Build$VERSION')
        View = autoclass('android.view.View')
        LayoutParams = autoclass('android.view.WindowManager$LayoutParams')

        activity = cast('android.app.Activity', PythonActivity.mActivity)

        @run_on_ui_thread
        def setup_ui():
            window = activity.getWindow()
            decor = window.getDecorView()

            # Get current flags
            current_flags = decor.getSystemUiVisibility()

            # Remove the layout flags that extend content behind system bars
            new_flags = current_flags & ~(
                View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
            )

            # Apply the new flags
            decor.setSystemUiVisibility(new_flags)

            # 1) Clear any fullscreen/edge-to-edge flags
            window.clearFlags(
                LayoutParams.FLAG_FULLSCREEN
                | LayoutParams.FLAG_LAYOUT_NO_LIMITS
                | LayoutParams.FLAG_TRANSLUCENT_STATUS
                | LayoutParams.FLAG_TRANSLUCENT_NAVIGATION
            )

            # 2) Restore normal windowed behavior
            if VERSION.SDK_INT >= 30:
                # Modern API: Tell system to fit content within system bars
                window.setDecorFitsSystemWindows(True)

                # Restore system bar backgrounds (not transparent)
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                # Force non-transparent bars to create proper boundaries
                Color = autoclass('android.graphics.Color')
                # Use a solid color instead of leaving it default
                window.setStatusBarColor(Color.parseColor('#000000'))
                window.setNavigationBarColor(Color.parseColor('#000000'))

                # Show bars using WindowInsetsController
                WindowInsets = autoclass('android.view.WindowInsets$Type')
                WindowInsetsController = autoclass(
                    'android.view.WindowInsetsController'
                )
                controller = window.getInsetsController()
                if controller:
                    controller.show(
                        WindowInsets.statusBars() | WindowInsets.navigationBars()
                    )
                    # Reset behavior to default
                    controller.setSystemBarsBehavior(
                        WindowInsetsController.BEHAVIOR_DEFAULT
                    )

                # Force window to re-layout by toggling a flag
                window.clearFlags(LayoutParams.FLAG_LAYOUT_IN_SCREEN)
                window.addFlags(LayoutParams.FLAG_LAYOUT_IN_SCREEN)

            else:
                # Legacy approach: clear all immersive/fullscreen flags
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                # Clear all system UI flags (back to normal windowed mode)
                decor.setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE)

            logger.info('Status bar shown and content constrained to safe area.')

        setup_ui()
        return True
    except Exception as e:
        logger.error(f'Failed to show status bar and constrain content: {e}')
        return False


def enable_immersive_mode():
    """
    Enable immersive sticky mode and screen pinning on Android.

    This will:
    - Hide navigation and status bars
    - Enable sticky immersive mode
    - Pin the app (prevent task switching)
    """
    logger.info('Enabling immersive sticky mode on Android')

    if platform != 'android':
        logger.info('Not on Android platform, skipping immersive mode')
        return False

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        View = autoclass('android.view.View')

        activity = cast('android.app.Activity', PythonActivity.mActivity)

        @run_on_ui_thread
        def setup_ui():
            """Setup immersive UI on the main thread."""
            try:
                decor = activity.getWindow().getDecorView()
                flags = (
                    View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                )
                decor.setSystemUiVisibility(flags)
                logger.info('Immersive mode enabled successfully')

                # Try to enable screen pinning
                activity.startLockTask()
                logger.info('Screen pinning enabled successfully')

            except Exception as e:
                logger.warning(f'Could not start lock task: {e}')

        # Run on UI thread using decorator
        setup_ui()

        return True

    except ImportError as e:
        logger.error(f'Failed to import Android modules: {e}')
        return False
    except Exception as e:
        logger.error(f'Failed to enable immersive mode: {e}')
        return False


def disable_immersive_mode():
    """
    Disable immersive mode and restore normal navigation.

    This will:
    - Restore navigation and status bars
    - Stop screen pinning
    """
    logger.info('Disabling immersive mode on Android')

    if platform != 'android':
        logger.info('Not on Android platform, skipping')
        return False

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        View = autoclass('android.view.View')

        activity = cast('android.app.Activity', PythonActivity.mActivity)

        @run_on_ui_thread
        def restore_ui():
            """Restore normal UI on the main thread."""
            try:
                decor = activity.getWindow().getDecorView()
                decor.setSystemUiVisibility(View.SYSTEM_UI_FLAG_VISIBLE)
                logger.info('Normal UI mode restored')

                activity.stopLockTask()
                logger.info('Screen pinning disabled')

            except Exception as e:
                logger.warning(f'Could not stop lock task: {e}')

        # Run on UI thread using decorator
        restore_ui()

        return True

    except ImportError as e:
        logger.error(f'Failed to import Android modules: {e}')
        return False
    except Exception as e:
        logger.error(f'Failed to disable immersive mode: {e}')
        return False


def set_status_bar_color(color_hex='#F5F7FF'):
    """
    Set Android status bar color.

    Args:
        color_hex (str): Hex color code (e.g., '#F5F7FF' for soft blue-white)
    """
    if platform == 'android':
        try:
            # Get the Android activity
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = cast('android.app.Activity', PythonActivity.mActivity)

            @run_on_ui_thread
            def setup_status_bar():
                """Setup status bar color on the main thread."""
                try:
                    # Get window and set status bar color
                    window = activity.getWindow()

                    # Get Android constants - access nested class properly
                    LayoutParams = autoclass('android.view.WindowManager$LayoutParams')

                    # Clear the translucent status bar flag and add
                    # system bar backgrounds
                    window.clearFlags(LayoutParams.FLAG_TRANSLUCENT_STATUS)
                    window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                    # Convert hex to Android color int
                    Color = autoclass('android.graphics.Color')
                    color_int = Color.parseColor(color_hex)

                    # Set the status bar color
                    window.setStatusBarColor(color_int)

                    logger.info(f'Status bar color set to {color_hex}')

                except Exception as e:
                    logger.error(f'Failed to set status bar color: {e}')

            # Run on UI thread using decorator
            setup_status_bar()

            # Set icons to dark for light background (call separately)
            set_status_bar_icons_dark(True)

        except Exception as e:
            logger.error(f'Failed to set status bar color: {e}')


def set_status_bar_icons_dark(dark=True):
    """
    Set status bar icons to dark or light.

    Args:
        dark (bool): True for dark icons (light status bar),
                    False for light icons (dark status bar)
    """
    if platform == 'android':
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            activity = cast('android.app.Activity', PythonActivity.mActivity)

            @run_on_ui_thread
            def setup_status_bar_icons():
                """Setup status bar icons on the main thread."""
                try:
                    # Get Android View class for constants
                    View = autoclass('android.view.View')

                    window = activity.getWindow()
                    view = window.getDecorView()

                    # Get current system UI flags
                    current_flags = view.getSystemUiVisibility()
                    logger.info(f'Current UI flags: {current_flags}')

                    if dark:
                        # Add light status bar flag (dark icons)
                        new_flags = current_flags | View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                        logger.info(
                            f'Setting LIGHT_STATUS_BAR flag: {View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR}'
                        )
                    else:
                        # Remove light status bar flag (light icons)
                        new_flags = (
                            current_flags & ~View.SYSTEM_UI_FLAG_LIGHT_STATUS_BAR
                        )
                        logger.info('Removing LIGHT_STATUS_BAR flag')

                    view.setSystemUiVisibility(new_flags)
                    logger.info(f'New UI flags set to: {new_flags}')

                    icon_type = 'dark' if dark else 'light'
                    logger.info(f'Status bar icons set to {icon_type}')

                except Exception as e:
                    logger.error(f'Failed to set status bar icons: {e}')

            # Run on UI thread using decorator
            setup_status_bar_icons()

        except Exception as e:
            logger.error(f'Failed to set status bar icons: {e}')


def set_navigation_bar_black():
    """
    Set the navigation bar (bottom bar) color to black.

    This function specifically changes the bottom navigation bar color
    to black, which can be useful for creating a consistent dark theme
    or matching specific design requirements.
    """
    if platform != 'android':
        return False

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        activity = cast('android.app.Activity', PythonActivity.mActivity)

        @run_on_ui_thread
        def setup_navigation_bar():
            """Set navigation bar color to black on the main thread."""
            try:
                window = activity.getWindow()

                # Get Android constants and Color class
                LayoutParams = autoclass('android.view.WindowManager$LayoutParams')
                Color = autoclass('android.graphics.Color')

                # Enable system bar backgrounds to allow color changes
                window.addFlags(LayoutParams.FLAG_DRAWS_SYSTEM_BAR_BACKGROUNDS)

                # Set navigation bar color to black
                window.setNavigationBarColor(Color.BLACK)

                logger.info('Navigation bar color set to black')

            except Exception as e:
                logger.error(f'Failed to set navigation bar color: {e}')

        # Run on UI thread using decorator
        setup_navigation_bar()
        return True

    except Exception as e:
        logger.error(f'Failed to set navigation bar black: {e}')
        return False


def is_lock_task_active():
    """
    Simple check if screen pinning (lock task) is active.

    Returns:
        bool: True if lock task is active
    """
    if platform != 'android':
        return False

    try:
        PythonActivity = autoclass('org.kivy.android.PythonActivity')
        ActivityManager = autoclass('android.app.ActivityManager')

        activity = cast('android.app.Activity', PythonActivity.mActivity)
        activity_manager = activity.getSystemService('activity')
        lock_task_state = activity_manager.getLockTaskModeState()
        lock_task_active = lock_task_state != ActivityManager.LOCK_TASK_MODE_NONE

        logger.debug(
            f'Lock task check: state={lock_task_state}, active={lock_task_active}'
        )

        return lock_task_active

    except Exception as e:
        logger.error(f'Failed to check lock task state: {e}')
        return False
