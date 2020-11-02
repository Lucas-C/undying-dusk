import resource, tracemalloc
from collections import defaultdict
from contextlib import contextmanager
from time import perf_counter
from types import SimpleNamespace

try:
    import psutil
except ImportError:
    psutil = False
try:
    from pympler import muppy, summary
except ImportError:
    muppy = False


EXEC_TIMES_MS = defaultdict(list)


@contextmanager
def trace_time(global_key=None, timings_in_ms=None):
    trace = SimpleNamespace() if (timings_in_ms is None and not global_key) else None  # do not create object if not needed
    start = perf_counter()
    yield trace
    duration = perf_counter() - start
    if global_key:
        EXEC_TIMES_MS[global_key].append(duration * 1000)
    elif timings_in_ms is None:
        trace.time = duration
    else:
        timings_in_ms.append(duration * 1000)


# pylint: disable=dangerous-default-value
def print_perf_stats(header='Stage', timings_in_ms_per_stage=EXEC_TIMES_MS):
    print(f'{header:<25} | Total exec time (ms) | #execs')
    print('--------------------------|----------------------|-------')
    for stage, timings_in_ms in sorted(timings_in_ms_per_stage.items()):
        count, total = len(timings_in_ms), sum(timings_in_ms)
        print(f'{stage:>25} | {total:>20.2f} | {count}')


class PerfsMonitorWrapper:
    'Measure execution times of all method calls performed on a given class instance'
    def __init__(self, instance, class_name=''):
        self.instance = instance
        self.class_name = class_name
        self.timings_in_ms_per_method = defaultdict(list)

    def __getattr__(self, name):
        with trace_time(timings_in_ms=self.timings_in_ms_per_method[name]):
            return getattr(self.instance, name)

    def print_perf_stats(self):
        print(f'Perf stats of all calls made to {self.class_name} methods:')
        print_perf_stats('Method name', self.timings_in_ms_per_method)


def print_memory_stats(detailed=False):
    'This function has an impact on performances'
    memory_peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    print(f'resource.ru_maxrss memory peak: {memory_peak // 1000}MB')

    if psutil:
        memory_rss = psutil.Process().memory_info().rss
        print(f'psutil.memory_rss: {memory_rss // (1000*1000)}MB')

    if not detailed: return

    if muppy:
        print('# muppy summary:')
        summary.print_(summary.summarize(muppy.get_objects()))

    if tracemalloc.is_tracing():
        snapshot = tracemalloc.take_snapshot()
        print('# tracemalloc top 10:')
        for stat in snapshot.statistics('lineno')[:10]:
            print(stat)
        print('Biggest memory block traceback:')
        stat = snapshot.statistics('traceback')[0]
        print("%s memory blocks: %.1f MiB" % (stat.count, stat.size / 1024 / 1024))
        for line in stat.traceback.format():
            print(line)
    else:
        tracemalloc.start()
