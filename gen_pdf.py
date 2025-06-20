#!/usr/bin/env python3

import argparse, json, logging, os, warnings
from contextlib import contextmanager

import fpdf

from pdf_game.visit import visit_game_views
from pdf_game.js import config
from pdf_game.logs import quiet_logging
from pdf_game.mapscript import mapscript_remove_all
from pdf_game.optional_deps import tqdm
from pdf_game.perfs import print_perf_stats, trace_time, PerfsMonitorWrapper
from pdf_game.render import render_page

from pdf_game.mod import campaign
from pdf_game.mod.metadata import METADATA, XMP_METADATA
from pdf_game.mod.pages import render_credit_pages, render_intro_pages, render_victory
# Note that there are other changes made from the "mod" package that are applied through patch* functions


def main():
    warnings.simplefilter('default', DeprecationWarning)
    args = parse_args()
    if args.list_checkpoints:
        for i, checkpoint in enumerate(campaign.CHECKPOINTS):
            print(f'{i + 1}: {checkpoint.description}')
        return
    logging.basicConfig(format="%(asctime)s %(filename)s [%(levelname)s] %(message)s",
                        datefmt="%H:%M:%S", level=logging.DEBUG)  # displays fpdf internal logs
    logging.getLogger('PIL').setLevel(logging.INFO)
    if not args.iter_logs:
        quiet_logging()
    if args.no_script:
        mapscript_remove_all()
    else:
        campaign.script_it()
    with trace_time() as trace:
        start_view, game_views = visit_game_views(args)
    print(f'States exploration took: {trace.time:.2f}s')
    if args.json:
        with trace_time() as trace, open('game_states.json', 'w', encoding='utf8') as json_file:
            json.dump({gv.page_id: gv.as_dict() for gv in game_views},
                      json_file, indent=4, sort_keys=True)
        print(f'JSON export took: {trace.time:.2f}s')
    if args.no_pdf:
        return
    print('Starting PDF pages rendering')
    pdf, links_to_credits = init_pdf(args, start_view.page_id)
    with trace_time() as trace:
        for game_view in tqdm(game_views, disable='NO_TQDM' in os.environ):
            render_page(pdf, game_view, lambda pdf, gs: render_victory(pdf, gs, links_to_credits))
    render_credit_pages(pdf, links_to_credits)
    print(f'Rendering of {len(pdf.pages)} pages took: {trace.time:.2f}s')
    assert not pdf._drawing_graphics_state_registry, "No /ExtGState are needed in Undying Dusk"  # pylint: disable=protected-access
    with trace_time() as trace:
        pdf.pdf_version = "1.3"  # Optimization: avoids 55bytes/page due to the transparency group
        pdf.output(f'{args.output_pdf}.pdf')
    print(f'Output generation took: {trace.time:.2f}s')
    print_perf_stats()
    pdf.print_perf_stats()


def parse_args():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--only-print-map", type=int, metavar="MAP_ID", help="Print a given map as ASCII and exit")
    parser.add_argument("--list-checkpoints", action="store_true", help="List checkpoints and exit")
    parser.add_argument("--inbetween-checkpoints", type=str, help="Only render the game inbetween the specified range of checkpoints. Example of valid values: 1-2 or 17-")
    parser.add_argument("--json", action="store_true", help="Dump all generated game states in a JSON file")
    parser.add_argument("--iter-logs", action="store_true", help=" ")
    parser.add_argument("--no-script", action="store_true", help=" ")
    parser.add_argument("--no-marked-content", action="store_true", help="Reduce PDF size by omitting links alternate descriptions")
    parser.add_argument("--no-reducer", action="store_true", help=" ")
    parser.add_argument("--no-pdf", action="store_true", help=" ")
    parser.add_argument("--detect-deadends", action="store_true", help="Sanity check")
    parser.add_argument("--print-reduced-views", action="store_true", help=" ")
    parser.add_argument("--output-pdf", "-o", type=str, default="undying-dusk", help="Name of the output PDF file (without the .pdf extension)")
    return parser.parse_args()


def init_pdf(args, start_page_id):
    if args.no_marked_content:  # currently adds ~66MB
        class PdfClass(fpdf.FPDF):
            @contextmanager
            def _marked_sequence(self, **kwargs):
                yield
            def _add_marked_content(self, *_, **__):
                pass
    else:
        PdfClass = fpdf.FPDF
    dimensions = [config().VIEW_WIDTH, config().VIEW_HEIGHT]
    pdf = PdfClass(format=dimensions, unit='pt')
    pdf.alias_nb_pages(None)  # disabling this feature for performance reasons
    pdf.set_auto_page_break(False)
    pdf.set_title(METADATA['dc:title'])
    pdf.set_subject(METADATA['dc:description'])
    pdf.set_author(METADATA['dc:creator'])
    pdf.set_keywords(METADATA['pdf:Keywords'])
    pdf.set_creator(METADATA['xmp:CreatorTool'])
    pdf.set_producer(METADATA['pdf:Producer'])
    pdf.set_xmp_metadata(XMP_METADATA)
    pdf = PerfsMonitorWrapper(pdf)
    links_to_credits = render_intro_pages(pdf, start_page_id)
    return pdf, links_to_credits


if __name__ == '__main__':
    main()
