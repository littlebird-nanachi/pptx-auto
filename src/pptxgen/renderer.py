from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

SOURCE = Path(__file__).parent
ROOT = SOURCE.parents[1]
ENV = Environment(loader=FileSystemLoader(SOURCE), autoescape=select_autoescape(['html']))


def render_html(slide, presentation, total, logo, theme, width=1920, height=1080):
    tokens = theme.get('tokens', {})
    css = '\n'.join((ROOT / 'styles' / name).read_text() for name in ('tokens.css', 'common.css'))
    overrides = ';'.join(f'--{key}:{value}px' for key, value in tokens.items())
    css += f'\n:root{{--slide-width:{width}px;--slide-height:{height}px;{overrides}}}'
    css += f'\n:root{{--logo-safe-area:calc(var(--logo-height) * {logo.width / logo.height} + var(--logo-gap));}}'
    # CSS grid keeps content beneath even a tall logo without per-layout logic.
    css += '\n.slide-heading{min-height:calc(var(--logo-top) + var(--logo-height) + var(--logo-gap) - var(--margin-y));}'
    return ENV.get_template('shell.html').render(slide=slide, total=total, logo=logo, css=css,
        footer=theme.get('footer', presentation['title']), layout_template=f"layouts/{slide['layout']}.html")
