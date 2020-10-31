import resource, tracemalloc

try:
    import psutil
except ImportError:
    psutil = False
try:
    from pympler import muppy, summary
except ImportError:
    muppy = False


def print_memory_stats():
    'This function has an impact on performances'
    memory_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f'resource.ru_maxrss memory peak: {memory_peak // 1000}MB')

    if psutil:
        memory_rss = psutil.Process().memory_info().rss
        print(f'psutil.memory_rss: {memory_rss // (1000*1000)}MB')

    if muppy:
        print('# muppy summary:')
        summary.print_(summary.summarize(muppy.get_objects()))

    print('# tracemalloc top 10:')
    if not tracemalloc.is_tracing():
        tracemalloc.start()
    for stat in tracemalloc.take_snapshot().statistics('lineno')[:10]:
        print(stat)
