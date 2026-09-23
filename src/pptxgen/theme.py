import base64
import json
import re
from dataclasses import dataclass
from pathlib import Path
from PIL import Image

@dataclass(frozen=True)
class Logo:
    path: Path
    width: int
    height: int
    uri: str


def resolve_logo(root: Path, theme: str) -> Logo:
    if not re.fullmatch(r'[a-zA-Z0-9_-]+', theme):
        raise ValueError('Invalid theme name')
    candidate = root / 'themes' / theme / 'logo.png'
    path = candidate if candidate.exists() else root / 'assets' / 'logo.png'
    try:
        with Image.open(path) as img:
            if img.format != 'PNG':
                raise ValueError('Logo must be PNG')
            img.load()
            width, height = img.size
        return Logo(path, width, height, 'data:image/png;base64,' + base64.b64encode(path.read_bytes()).decode())
    except Exception as exc:
        raise ValueError(f'LOGO_LOAD_ERROR: {path}: {exc}') from exc


def load_theme(root: Path, name: str):
    logo = resolve_logo(root, name)
    path = root / 'themes' / name / 'theme.json'
    theme = json.loads(path.read_text()) if path.exists() else {}
    allowed = {'logo-top', 'logo-right', 'logo-height', 'logo-gap', 'margin-x', 'margin-y',
               'title-size', 'lead-size', 'body-size', 'minimum-font-size'}
    tokens = theme.get('tokens', {})
    for key, value in tokens.items():
        if key not in allowed or not isinstance(value, (float, int)) or isinstance(value, bool) or not 0 < value <= 1920:
            raise ValueError(f'Invalid theme token: {key}')
    if not isinstance(theme.get('footer', ''), str):
        raise ValueError('Theme footer must be a string')
    return logo, theme
