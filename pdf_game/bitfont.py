'Replicates heroine-dusk/release/js/bitfont.js'

from contextlib import contextmanager

from .entities import Justify
from .js import bitfont, config, REL_RELEASE_DIR
from .render_utils import add_link


RED_RGB = (208, 70, 72)
WHITE_RGB = (222, 238, 214)

_RENDER_AS_TEXT = False # Use .otf/.ttf font files. Otherwise use original image-based text rendering.
                        # Note: enabling it reduced by ~7% the size of an output file that originally was ~160Mb.
                        # It would be required to make the PDF accessible.
                        # However the fonts are slightly less prettiers, and there is currently a bug with parens
_FONTS_LOADED = False
_ACTIVE_COLOR = WHITE_RGB


def bitfont_set_color_red(enable):
    global _ACTIVE_COLOR
    _ACTIVE_COLOR = RED_RGB if enable else WHITE_RGB


@contextmanager
def bitfont_color_red():
    bitfont_set_color_red(True)
    yield
    bitfont_set_color_red(False)


def bitfont_render(pdf, text, x, y, justify=Justify.LEFT, size=8, page_id=None, url=None, link=None):
    min_x, max_x = config().VIEW_WIDTH, 0
    lines = text.split('\n')
    for i, line in enumerate(lines):
        start_x, text_width = _bitfont_render(pdf, line, x, y + 10*i, justify, size)
        min_x = min(min_x, start_x)
        max_x = max(max_x, start_x + text_width)
    if url or page_id or link:
        return add_link(pdf, x=min_x, y=y, width=max_x - min_x, height=10*len(lines) - 4,
                        page_id=page_id, url=url, link=link)  # TODO: pass link_alt=
    return None


def _bitfont_render(pdf, text, x, y, justify=Justify.LEFT, size=8):
    text = text.upper()
    scale = size / 8
    text_width = scale * bitfont_calcwidth(text)
    if justify == Justify.RIGHT:
        x -= text_width
    if justify == Justify.CENTER:
        x -= text_width / 2
    start_x = x
    if _RENDER_AS_TEXT:
        _load_fonts(pdf)
        x -= 3
        y += size - 1
        pdf.set_text_color(0)
        pdf.set_font('BoxyBold', size=size)
        pdf.text(x, y, text)
        pdf.set_text_color(*_ACTIVE_COLOR)
        pdf.set_font('BoxyBoldLight', size=size)
        pdf.text(x, y, text)
    else:
        for char in text:
            x += bitfont_renderglyph(pdf, char, x, y, scale)
    return start_x, text_width


def _load_fonts(pdf):
    global _FONTS_LOADED
    if not _FONTS_LOADED and not pdf.__class__.__name__.startswith('Fake'):
        pdf.add_font('BoxyBold',      fname='fonts/Boxy-Bold.ttf',       uni=True)
        pdf.add_font('BoxyBoldLight', fname='fonts/Boxy-Bold-Light.otf', uni=True)
        _FONTS_LOADED = True


def bitfont_calcwidth(text):
    total_width = sum(_SPACE if char == " " else _GLYPH_W[char] + _KERNING for char in text)
    return total_width - _KERNING


def bitfont_renderglyph(pdf, char, x, y, scale=1):
    if char == " ":
        return _SPACE
    height = _HEIGHT * scale
    width = _GLYPH_W[char] * scale
    font_img_filepath = REL_RELEASE_DIR + (bitfont().imgred.src if _ACTIVE_COLOR == RED_RGB else bitfont().img.src)
    with pdf.rect_clip(x=x, y=y, w=width, h=height - scale):
        pdf.image(font_img_filepath,
                  x=x - _GLYPH_X[char]*scale, y=y,
                  w=_BITFONT_IMG_WIDTH*scale, h=height)
    return scale * (_GLYPH_W[char] + _KERNING)



# Those constants are defined for performance reasons,
# as "bitfont_render" is the most called function in the rendering step,
# to avoid costly calls to bitfont().* pyduktape.JSProxy instances
# (especially when they are Array, like .glyph_* attributes).
_GLYPHS = r"!\"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`{|}~"
_GLYPH_W = {char: bitfont().glyph_w[char] for char in _GLYPHS}
_GLYPH_X = {char: bitfont().glyph_x[char] for char in _GLYPHS}
_KERNING = bitfont().kerning
_HEIGHT = bitfont().height
_SPACE = bitfont().space
_BITFONT_IMG_WIDTH = 516
