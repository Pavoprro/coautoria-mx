import os
from subprocess import Popen

port = os.environ.get('PORT', 7860)

command = [
    "mercury",
    f"--ip=0.0.0.0",
    f"--port={port}",
    "--no-browser",
    "--allow-root"
]

worker = Popen(command)
worker.wait()
