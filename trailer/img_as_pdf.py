from contextlib import contextmanager

from PIL import Image


class ImageAsPdf:
    'Wrap a PIL.Image in an object with an API similar to FPDF'
    def __init__(self, fpdf, img):
        self.pdf = fpdf
        self.images = self.pdf.images
        self.img = img
        self._rect_clip = None

    def _parsepng(self, filename):
        # pylint: disable=protected-access
        return self.pdf._parsepng(filename)

    def add_page(self): pass
    def add_link(self): pass
    def set_link(self, link, page=-1): pass
    def link(self, x, y, w, h, link, alt_text=''): pass

    def image(self, img_filepath, x=None, y=None, w=0, h=0):
        is_bitfont = 'boxy_bold' in img_filepath
        with Image.open(img_filepath) as img_added:
            if self._rect_clip:
                rc_x, rc_y, rc_width, rc_height = self._rect_clip
                assert rc_width > 0 and rc_height > 0, f'{img_filepath}: rc_width={rc_width} rc_height={rc_height}'
                scale = w / 516 if is_bitfont and w else 1  # retrieving bitfont scale
                crop_x = (rc_x - x) / scale
                crop_y = (rc_y - y) / scale
                x, y = rc_x, rc_y
                if x < 0:  # PIL requires x & y to be positive:
                    if x < -rc_width: return  # out of screen, no need to render
                    assert scale == 1, 'Not implemented yet'
                    crop_x -= x
                    x = 0
                if y < 0:  # PIL requires x & y to be positive:
                    if y < -rc_height: return  # out of screen, no need to render
                    assert scale == 1, 'Not implemented yet'
                    crop_y -= y
                    y = 0
                rc_width, rc_height = map(int, (rc_width, rc_height))  # .resize box arg must be an int tuple
                img_added = img_added.crop((crop_x, crop_y, crop_x + rc_width / scale, crop_y + rc_height / scale))\
                                     .resize((rc_width, rc_height), resample=Image.NEAREST)
            else:
                assert not (w or h), 'Not implemented yet'
            x, y = map(int, (x, y))  # .paste box arg must be an int tuple
            if img_added.mode == 'P':
                img_added = img_added.convert('RGBA')
            self.img.alpha_composite(img_added, dest=(x, y))

    @contextmanager
    def rect_clip(self, x, y, w, h):
        self._rect_clip = (x, y, w, h)
        yield
        self._rect_clip = None