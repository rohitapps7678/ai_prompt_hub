import os
os.environ.setdefault("CLOUDINARY_URL", "cloudinary://863392175587377:VdAkiy1vlskR1P5a1wRENTrETqI@dno44x2cr")

import sys

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_prompt_hub.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed?"
        ) from exc
    execute_from_command_line(sys.argv)