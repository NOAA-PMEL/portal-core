import logging
import sys

# A. Create a app_logger
app_logger = logging.getLogger('Data Submit')
app_logger.setLevel(logging.DEBUG)  # Capture everything from DEBUG up

# B. Create a handler to send messages to Standard Out
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

# C. Define a format (optional, but helpful)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)

# D. Add the handler to your app_logger
if not app_logger.handlers:
    app_logger.addHandler(handler)

# E. SILENCE THE NOISE
# Dash runs on Flask, which uses Werkzeug. Werkzeug prints every HTTP request
# to stdout at the INFO level. We set it to ERROR to mute standard traffic.
logging.getLogger('werkzeug').setLevel(logging.ERROR)
logging.getLogger('dash').setLevel(logging.ERROR)

# Debug prints for making sure logging configuration is correct
# print(f"Effective Level: {app_logger.getEffectiveLevel()}")
# print(f"Handlers: {app_logger.handlers}")
# print(f"Disabled: {app_logger.disabled}")

