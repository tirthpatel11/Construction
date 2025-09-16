import os

# Ensure settings are set for ASGI import on Vercel
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "sitesphere.settings")

from sitesphere.asgi import application as app  # ASGI callable expected by Vercel


