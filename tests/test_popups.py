"""
Test script to verify popup functionality.
Run this to test the new popup structure.
"""

import sys

sys.path.append('.')  # Adjust path to import from parent directory

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button

from baby_lights.popups import show_confirmation_popup, show_info_popup


class TestPopupApp(App):
    def build(self):
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        confirmation_btn = Button(text='Test Confirmation Popup')
        confirmation_btn.bind(on_press=self.show_confirmation)

        info_btn = Button(text='Test Info Popup')
        info_btn.bind(on_press=self.show_info)

        layout.add_widget(confirmation_btn)
        layout.add_widget(info_btn)

        return layout

    def show_confirmation(self, btn):
        def on_confirm():
            print('Confirmed!')

        def on_cancel():
            print('Cancelled!')

        show_confirmation_popup(
            title='Test Confirmation',
            message='This is a test confirmation popup\nwith multiple lines of text.',
            confirm_text='Yes',
            cancel_text='No',
            on_confirm=on_confirm,
            on_cancel=on_cancel,
        )

    def show_info(self, btn):
        def on_ok():
            print('OK pressed!')

        show_info_popup(
            title='Test Info',
            message='This is a test info popup.',
            ok_text='Got it',
            on_ok=on_ok,
        )


if __name__ == '__main__':
    TestPopupApp().run()
