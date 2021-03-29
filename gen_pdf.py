#!/usr/bin/env python3.8

import argparse, json, logging, os

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
        with trace_time() as trace, open('game_states.json', 'w') as json_file:
            json.dump({gv.page_id: gv.as_dict() for gv in game_views},
                      json_file, indent=4, sort_keys=True)
        print(f'JSON export took: {trace.time:.2f}s')
    if args.no_pdf:
        return
    print('Starting PDF pages rendering')
    pdf, links_to_credits = init_pdf(start_view.page_id)
    with trace_time() as trace:
        for game_view in tqdm(game_views, disable='NO_TQDM' in os.environ):
            render_page(pdf, game_view, lambda pdf, gs: render_victory(pdf, gs, links_to_credits))
    render_credit_pages(pdf, links_to_credits)
    print(f'Rendering of {len(pdf.pages)} pages took: {trace.time:.2f}s')
    if args.no_marked_content:
        # pylint: disable=protected-access
        pdf._marked_contents = None
    with trace_time() as trace:
        pdf.output('undying-dusk.pdf', 'F')
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
    parser.add_argument("--no-marked-content", action="store_true", help="Reduce PDF size by omiting links alternate descriptions")
    parser.add_argument("--no-reducer", action="store_true", help=" ")
    parser.add_argument("--no-pdf", action="store_true", help=" ")
    parser.add_argument("--detect-deadends", action="store_true", help="Sanity check")
    parser.add_argument("--print-reduced-views", action="store_true", help=" ")
    return parser.parse_args()


def init_pdf(start_page_id):
    dimensions = [config().VIEW_WIDTH, config().VIEW_HEIGHT]
    pdf = fpdf.FPDF(format=dimensions, unit='pt')
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
