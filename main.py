import trio

from baby_lights import BabyLightsApp

app = BabyLightsApp()

trio.run(app.async_run, 'trio')
