from .bitfont import bitfont_render
from .entities import GameMilestone, GameMode, GameView
from .reducer import compute_fingerprint, reduce_views, FakePdfRecorder
from .visit import build_initial_state


AN_EXPLORE_STATE = build_initial_state()._replace(mode=GameMode.EXPLORE)
A_FINAL_STATE = AN_EXPLORE_STATE._replace(milestone=GameMilestone.GAME_OVER)


def test_reduce_2_identical_views():
    game_views = [
        GameView(A_FINAL_STATE),
        GameView(A_FINAL_STATE._replace(hidden_triggers=('X',)))
    ]
    assert len(reduce_views(game_views, print_reduced_views=True)) == 1

    def render(pdf):
        bitfont_render(pdf, 'Online hall of fame', 80, 90, url='https://chezsoi.org/lucas/blog/')
    game_views = [
        GameView(renderer=render),
        GameView(renderer=render),
    ]
    assert len(reduce_views(game_views, print_reduced_views=True)) == 1


def test_reduce_2_identical_views_except_for_secret():
    game_views = [
        GameView(A_FINAL_STATE),
        GameView(A_FINAL_STATE._replace(secrets_found=('X',)))
    ]
    assert len(reduce_views(game_views, print_reduced_views=True)) == 2


def test_reduce_2_identical_views_except_for_page_id_link():
    def render1(pdf):
        bitfont_render(pdf, 'Back to start', 80, 90, page_id=1)
    def render2(pdf):
        bitfont_render(pdf, 'Back to start', 80, 90, page_id=2)
    game_views = [
        GameView(renderer=render1),
        GameView(renderer=render2),
    ]
    assert len(reduce_views(game_views, print_reduced_views=True)) == 2


def test_reduce_2_identical_views_except_for_url_link():
    def render1(pdf):
        bitfont_render(pdf, 'Online hall of fame', 80, 90, url='https://chezsoi.org/lucas/blog/')
    def render2(pdf):
        bitfont_render(pdf, 'Online hall of fame', 80, 90, url='https://chezsoi.org/lucas/blog')
    game_views = [
        GameView(renderer=render1),
        GameView(renderer=render2),
    ]
    assert len(reduce_views(game_views, print_reduced_views=True)) == 2


def test_reduce_5_views_to_3():
    leaf_view1 = GameView(A_FINAL_STATE)
    leaf_view2 = GameView(A_FINAL_STATE._replace(hidden_triggers=('X',)))
    middle_view1 = GameView(AN_EXPLORE_STATE._replace(y=2))
    middle_view1.actions['MOVE-BACKWARD'] = leaf_view1
    middle_view2 = GameView(AN_EXPLORE_STATE._replace(y=2))
    middle_view2.actions['MOVE-BACKWARD'] = leaf_view2
    root_view = GameView(AN_EXPLORE_STATE._replace(y=3))
    root_view.actions['MOVE-BACKWARD'] = middle_view1
    root_view.actions['MOVE-FORWARD'] = middle_view2
    game_views = [leaf_view1, leaf_view2, middle_view1, middle_view2, root_view]
    reduced = reduce_views(game_views, print_reduced_views=True)
    _print_reduced(reduced)
    assert len(reduced) == 3


def test_no_over_reduce():
    leaf_view1 = GameView(A_FINAL_STATE)
    leaf_view2 = GameView(A_FINAL_STATE._replace(x=2))
    middle_view1 = GameView(AN_EXPLORE_STATE._replace(y=2))
    middle_view1.actions['MOVE-BACKWARD'] = leaf_view1
    middle_view2 = GameView(AN_EXPLORE_STATE._replace(y=2))
    middle_view2.actions['MOVE-BACKWARD'] = leaf_view2
    root_view1 = GameView(AN_EXPLORE_STATE._replace(y=3))
    root_view1.actions['MOVE-BACKWARD'] = middle_view1
    root_view2 = GameView(AN_EXPLORE_STATE._replace(y=3))
    root_view2.actions['MOVE-BACKWARD'] = middle_view2
    game_views = [leaf_view1, leaf_view2, middle_view1, middle_view2, root_view1, root_view2]
    reduced = reduce_views(game_views, print_reduced_views=True)
    _print_reduced(reduced)
    assert len(reduced) == 6


def test_fingerprint_differ():
    fake_pdf = FakePdfRecorder()
    fp1 = compute_fingerprint(fake_pdf, GameView(A_FINAL_STATE))
    fp2 = compute_fingerprint(fake_pdf, GameView(A_FINAL_STATE._replace(x=2)))
    assert fp1 != fp2


def _print_reduced(reduced):
    for gv in reduced:
        gs = gv.state
        # pylint: disable=protected-access
        print(f'y={gs.y}, milestone={gs.milestone}, secrets_found={gs.secrets_found}), page_id={gv.page_id}, _page_id_from={bool(gv._page_id_from)}, actions={ {a: ngv.page_id for a, ngv in gv.actions.items()} }')
