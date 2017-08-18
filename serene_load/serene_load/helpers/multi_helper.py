import signal
import inspect
import importlib
import os
import multiprocessing
import sys
import traceback
import time
import logging
import datetime
import collections
from multiprocessing import Queue, Process, Value, managers
from serene_load.helpers.file_helpers import si_size
from Queue import Empty

log = logging.getLogger()


def pretty_exception():
    """
    format an exception suitable for printing in a single line log file
    """
    etype, value, tb = sys.exc_info()

    path = []
    for filename, lno, funcname, text in traceback.extract_tb(tb):
        if filename.startswith('/'):
            filename = '/'.join(filename.split('/')[-3:])

        path.append(
            '{} in {}:{}'.format(text, filename, lno)
        )

    path.reverse()
    return '{}: "{}". traceback: {}'.format(etype.__name__, value, ' -> '.join(path))

class ErrorCounter(object):
    def __init__(self):
        self.value = collections.defaultdict(int)

    def add(self, error):
        self.value[error] += 1

    def __call__(self, *args):
        """helper for add"""
        assert len(args) == 1
        self.value[args[0]] += 1

class WorkerState(object):
    def __init__(self, workers=None):
        assert workers
        self.worker_count = workers
        self.states = [Value('b', lock=False) for _ in range(workers)]

        for _ in self.states:
            _.value = False

    def pass_worker_object(self, worker):
        return self.states[worker]

    def count(self):
        return sum(_.value for _ in self.states)

    def working(self):
        return any(_.value for _ in self.states)

    def __repr__(self):
        return '{}/{}'.format(sum(_.value for _ in self.states), len(self.states))


def get_functions(modulename):
    module = importlib.import_module('serene_load.helpers.{}'.format(modulename))

    funcs = {}

    for n, m in inspect.getmembers(module, lambda _: inspect.isclass(_)):
        name = getattr(m, 'name', None)
        if name:
            #Todo - this is a HACK!!! We should be subclassing all relevant classes from a common base and testing
            #for membership that way.... this WILL break in the future so you should fix it if you're reading this
            f = getattr(m, 'func', None)
            if f:
                assert inspect.isfunction(f), f
                funcs[name] = f

    return funcs


def get_iowait(pid):
    try:
        with open('/proc/{}/stat'.format(pid), 'r') as iostats:
            stats = iostats.readlines()[0].split()
        return float(stats[41])
    except IOError:
        return 0.0


def get_pid_children(pid):
    for dirpath, dirnames, filenames in os.walk('/proc/{}/task'.format(pid)):
        if not dirpath.endswith('task'):
            continue
        for dirname in dirnames:
            try:
                with open('/proc/{}/task/{}/children'.format(pid, dirname), 'r') as fc:

                    for child in fc.read().split():
                        yield child
            except IOError:
                pass


def calc_all_iowait(pid=None):
    if pid is None:
        pid = os.getpid()

    total = get_iowait(pid)
    for cpid in get_pid_children(pid):
        total += calc_all_iowait(cpid)

    return total


class WorkerFilter(logging.Filter):
    def filter(self, record):
        """
        Determine if the specified record is to be logged.

        Is the specified record to be logged? Returns 0 for no, nonzero for
        yes. If deemed appropriate, the record may be modified in-place.
        """
        name = multiprocessing.current_process().name
        try:
            process, worker = name.split('-')
            name = '{}-{:>02}'.format(process, worker)
        except ValueError:
            pass

        record.__dict__.update({
            'msg': '{} {}'.format(name, record.msg)
        })
        return True


class MyManager(managers.BaseManager):
    pass


class ContainerManager(object):
    def __init__(self):
        self.files = []

    def push(self, filename):
        self.files.append(filename)

    def pop(self, filename):
        self.files.remove(filename)
        return self.files.count(filename)

    def count(self):
        return self.files.__len__()

MyManager.register('ContainerManager', ContainerManager)


class MultiJob(object):
    """
    Helper to run tasks that can be parallellised
    """
    def setup_multi(self, args, available_functions, load, daemon=True):
        log.addFilter(WorkerFilter())
        self.WORKERS = WORKERS = int(multiprocessing.cpu_count()*load)

        manager = MyManager()
        manager.start()
        self.cm = manager.ContainerManager()
        setattr(args, 'cm', self.cm)

        self.error_counter = ErrorCounter()
        setattr(args, 'error_counter', self.error_counter)

        self.queued_items = collections.defaultdict(list)
        self.work_q = Queue()
        self.intermediate_q = Queue()
        self.result_q = Queue()
        self.workers = []
        self.worker_state = WorkerState(WORKERS)
        self.available_functions = available_functions

        for i in range(WORKERS):
            worker = Process(
                target=self.multi_worker,
                name='worker-{}'.format(i),
                args=(
                    args,
                    self.work_q,
                    self.intermediate_q,
                    self.result_q,
                    self.worker_state.pass_worker_object(i),
                    self.available_functions
                )
            )
            worker.daemon = daemon
            worker.start()
            self.workers.append(worker)

        log.debug('{} workers started'.format(WORKERS))

        self._tasks_in = 0
        self._tasks_complete = 0
        self.bytes_processed = 0

        self.results = []
        self.progress = []
        self.last_progress = datetime.datetime.now()


    def print_error_log(self):
        self.log.info('- Printing Counters -')
        for k, v in sorted(self.error_counter.value.iteritems(), key=lambda sk: sk[0]):
            self.log.info(u'{:,}\t{}'.format(v, k).encode('utf-8'))

    def result(self, result):
        """
        Output results that have been processed
        """
        raise NotImplementedError()

    def run(self):
        """
        Queue initial tasks
        """
        raise NotImplementedError()

    def success(self):
        """
        finalize results before exit SUCCESS
        """
        raise NotImplementedError()

    def failure(self):
        """
        Cleanup after a failed run
        """
        raise NotImplementedError()

    @staticmethod
    def multi_worker(args, work_q, intermediate_q, result_q, mystate, funcs_from):
        # Ignore SIGINT signals
        signal.signal(signal.SIGINT, signal.SIG_IGN)
        available_functions = get_functions(funcs_from)

        while True:
            mystate.value = 0
            f = work_q.get(block=True)
            mystate.value = 1

            func = available_functions[f['next_func']]

            try:
                for _ in func(args, f):
                    _['priority'] = f['priority']
                    intermediate_q.put_nowait(_)
            except Exception as e:
                log.error(u'While working on >>{}<< - >>{}<<'.format(unicode(f), pretty_exception()))

                if 'cleanup' in f:
                    cleanup_name = f.pop('cleanup')
                    f[cleanup_name].cleanup()

            result_q.put_nowait(None)

    def queue_work(self, work_item):
        self._tasks_in += 1
        self.queued_items[work_item['priority']].append(work_item)

    def add_work(self):
        desired = (self.WORKERS*4) - self.work_q.qsize()

        if desired <= 0:
            return

        priorities = sorted(self.queued_items.keys(), reverse=True)

        if not priorities:
            return

        # Start with the highest priority list
        p = priorities.pop(0)

        while desired > 0:
            while not self.queued_items[p]:
                if not priorities:
                    # no more priority lists
                    return
                p = priorities.pop(0)

            item = self.queued_items[p].pop(0)
            self.work_q.put_nowait(item)
            desired -= 1

    def manage_work(self):
        while True:
            self.add_work()

            more = result = None
            try:
                more = self.intermediate_q.get(block=False)
                if more and 'next_func' in more:
                    more['priority'] += 1
                    self.queue_work(more)
                else:
                    result = more
                    more = None
            except Empty:
                try:
                    result = self.result_q.get(block=False)
                    self._tasks_complete += 1
                except Empty:
                    return

            for _ in [more, result]:
                if _ and 'proc_bytes' in _:
                    b = _.pop('proc_bytes')
                    self.progress.append(b)
                    self.bytes_processed += b

            if result and 'priority' in result:
                result.pop('priority')
            if result:
                self.result(result)

    def print_progress(self):
        since_last_printed = (datetime.datetime.now() - self.last_progress).total_seconds()

        if since_last_printed < 10:
            return

        if len(self.progress) == 0:
            if since_last_printed > 500:
                log.info('Worker status: {}'.format(self.worker_state))
                self.last_progress = datetime.datetime.now()
            return

        elapsed = (datetime.datetime.now() - self.last_progress).total_seconds()
        self.last_progress = datetime.datetime.now()
        total_bytes = sum(self.progress)
        self.progress = []

        log.info('Tasks: {:,} completed, {} running, {:,} queued. Data: {:.1S} processed (inst. rate: {:.1S}/s). Worker utilisation {}. Average IO wait {:.02f} per MB '.format(
            self._tasks_complete,
            self.worker_state.count(),
            self.waiting_tasks() - self.worker_state.count(),
            si_size(self.bytes_processed),
            si_size(float(total_bytes)/elapsed),
            self.worker_state,
            calc_all_iowait()/(self.bytes_processed/1024.0/1024)
        ))

        self.sync()

    def sync(self):
        pass

    def kill_workers(self):
        for worker in self.workers:
            worker.terminate()
            worker.join()
        self.work_q.close()
        self.intermediate_q.close()
        self.result_q.close()

    def waiting_tasks(self):
        return self._tasks_in - self._tasks_complete

    def go(self, PROFILE=False):
        nowork = 0
        success = False

        if PROFILE:
            log.info('Profiling performance')
            import cProfile, pstats, StringIO
            pr = cProfile.Profile()
            pr.enable()

        try:
            self.run()
            while True:
                time.sleep(0.1)
                self.manage_work()
                self.print_progress()

                if self.worker_state.working() is False and self.waiting_tasks() == 0:
                    nowork += 1
                else:
                    nowork = 0
                if nowork > 30 and self.waiting_tasks() == 0:
                    log.info('END: {} tasks run'.format(self._tasks_complete))
                    success = True
                    break

        except KeyboardInterrupt:
            print 'KeyboardInterrupt'

        if success:
            self.success()
        else:
            self.failure()

        self.kill_workers()

        if PROFILE:
            pr.disable()
            s = StringIO.StringIO()
            sortby = 'tottime'
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.print_stats()
            log.info('\n'.join(s.getvalue().split('\n')[:15]))

        if success:
            exit()
        else:
            exit(1)
