[app]

title = Baby Lights
package.name = baby_lights
package.domain = com.kivyschool
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,toml,txt
source.exclude_dirs = temp, bin, dist, .venv, __pycache__, .vscode, tests
source.exclude_patterns = app_copy.zip, buildozer.spec, poetry.lock, pyproject.toml, replace_kivy_reloader.py, get_context.py
version = 0.1.1
requirements = python3, kivy, kivy_reloader==0.7.0, android, toml, trio, attrs, outcome, sniffio, sortedcontainers, exceptiongroup
presplash.filename = baby_lights/assets/presplash.png
icon.filename = baby_lights/assets/icon.png
orientation = portrait

# Android specific
fullscreen = 0
android.permissions = INTERNET, REQUEST_LOCK_TASK
android.api = 35
android.minapi = 24
android.accept_sdk_license = True
android.archs = arm64-v8a
p4a.branch = develop


[buildozer]
log_level = 2
warn_on_root = 1
