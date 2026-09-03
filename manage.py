import os
import sys

# CLOUDINARY_URL (and every other secret) must come from the environment
# or a .env file — never hardcode credentials in source control.
# Example .env entry:
#   CLOUDINARY_URL=cloudinary://<key>:<secret>@<cloud_name>
try:
    from decouple import config
    os.environ.setdefault("CLOUDINARY_URL", config("CLOUDINARY_URL", default=""))
except ImportError:
    pass

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_prompt_hub.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)