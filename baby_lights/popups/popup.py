"""
Popup components for Baby Lights app.
Clean Python classes that use KV files for layout.
"""

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivy.uix.popup import Popup
from kivy_reloader.utils import load_kv_path

# Load the KV file
load_kv_path(__file__)


class ConfirmationPopup(Popup):
    """A popup with title, message, and confirm/cancel buttons."""

    message_text = StringProperty('Are you sure?')
    confirm_text = StringProperty('Confirm')
    cancel_text = StringProperty('Cancel')

    def __init__(
        self,
        title='Confirmation',
        message='Are you sure?',
        *,
        confirm_text='Confirm',
        cancel_text='Cancel',
        on_confirm=None,
        on_cancel=None,
        **kwargs,
    ):
        # Set properties
        self.message_text = message
        self.confirm_text = confirm_text
        self.cancel_text = cancel_text

        # Store callbacks
        self.on_confirm_callback = on_confirm
        self.on_cancel_callback = on_cancel

        # Set title
        kwargs.setdefault('title', title)

        super().__init__(**kwargs)

    def on_confirm_press(self):
        """Handle confirm button press."""
        # Disable both buttons to prevent multiple clicks
        self._disable_buttons()

        if self.on_confirm_callback:
            self.on_confirm_callback()
        self.dismiss()

    def on_cancel_press(self):
        """Handle cancel button press."""
        # Disable both buttons to prevent multiple clicks
        self._disable_buttons()

        if self.on_cancel_callback:
            self.on_cancel_callback()
        self.dismiss()

    def _disable_buttons(self):
        """Temporarily disable both buttons to prevent multiple clicks."""
        confirm_btn = self.ids.get('confirm_button')
        cancel_btn = self.ids.get('cancel_button')

        if confirm_btn:
            confirm_btn.disabled = True
        if cancel_btn:
            cancel_btn.disabled = True

        # Re-enable after 1 second (in case popup doesn't dismiss immediately)
        Clock.schedule_once(self._enable_buttons, 1.0)

    def _enable_buttons(self, dt):
        """Re-enable buttons after delay."""
        confirm_btn = self.ids.get('confirm_button')
        cancel_btn = self.ids.get('cancel_button')

        if confirm_btn:
            confirm_btn.disabled = False
        if cancel_btn:
            cancel_btn.disabled = False


class InfoPopup(Popup):
    """A simple info popup with just an OK button."""

    message_text = StringProperty('Info')
    ok_text = StringProperty('OK')

    def __init__(
        self,
        title='Information',
        message='Info',
        *,
        ok_text='OK',
        on_ok=None,
        **kwargs,
    ):
        # Set properties
        self.message_text = message
        self.ok_text = ok_text

        # Store callback
        self.on_ok_callback = on_ok

        # Set title
        kwargs.setdefault('title', title)

        super().__init__(**kwargs)

    def on_ok_press(self):
        """Handle OK button press."""
        # Disable button to prevent multiple clicks
        self._disable_ok_button()

        if self.on_ok_callback:
            self.on_ok_callback()
        self.dismiss()

    def _disable_ok_button(self):
        """Temporarily disable OK button to prevent multiple clicks."""
        ok_btn = self.ids.get('ok_button')

        if ok_btn:
            ok_btn.disabled = True

        # Re-enable after 1 second (in case popup doesn't dismiss immediately)
        Clock.schedule_once(self._enable_ok_button, 1.0)

    def _enable_ok_button(self, dt):
        """Re-enable OK button after delay."""
        ok_btn = self.ids.get('ok_button')

        if ok_btn:
            ok_btn.disabled = False


def show_confirmation_popup(
    title='Confirmation',
    message='Are you sure?',
    *,
    confirm_text='Confirm',
    cancel_text='Cancel',
    on_confirm=None,
    on_cancel=None,
):
    """
    Show a confirmation popup with confirm and cancel buttons.

    Args:
        title (str): Popup title
        message (str): Message to display
        confirm_text (str): Text for confirm button
        cancel_text (str): Text for cancel button
        on_confirm (callable): Callback when confirm is pressed
        on_cancel (callable): Callback when cancel is pressed

    Returns:
        ConfirmationPopup: The created popup instance
    """
    popup = ConfirmationPopup(
        title=title,
        message=message,
        confirm_text=confirm_text,
        cancel_text=cancel_text,
        on_confirm=on_confirm,
        on_cancel=on_cancel,
    )
    popup.open()
    return popup


def show_info_popup(title='Information', message='Info', *, ok_text='OK', on_ok=None):
    """
    Show an information popup with just an OK button.

    Args:
        title (str): Popup title
        message (str): Message to display
        ok_text (str): Text for OK button
        on_ok (callable): Callback when OK is pressed

    Returns:
        InfoPopup: The created popup instance
    """
    popup = InfoPopup(title=title, message=message, ok_text=ok_text, on_ok=on_ok)
    popup.open()
    return popup


def show_exit_confirmation(*, on_confirm=None, on_cancel=None):
    """
    Show a specific exit confirmation popup for the Baby Lights app.

    Args:
        on_confirm (callable): Callback when exit is confirmed
        on_cancel (callable): Callback when exit is cancelled

    Returns:
        ConfirmationPopup: The created popup instance
    """
    return show_confirmation_popup(
        title='Exit Baby Lights',
        message='Are you sure you want to exit the app?',
        confirm_text='Exit',
        cancel_text='Stay',
        on_confirm=on_confirm,
        on_cancel=on_cancel,
    )
