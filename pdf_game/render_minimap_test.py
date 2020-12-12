from .render_minimap import parse_gpl_file


def test_parse_gpl_file():
    palette = parse_gpl_file('DawnBringer.gpl')
    assert palette.name == "DawnBringer's Palette"
    assert palette.columns == 8
    assert len(palette.colors) == 16
