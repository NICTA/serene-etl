import StringIO
import tempfile
import io
import os
import pickle
import logging
import base64

log = logging.getLogger()

BUFSZ = 4*1024*1024


def monkeypatch_io(classnm):
    # Monkey patch to support io module...
    def ersr(self):
        return True

    def ersw(self):
        return False

    classnm.readable = ersr
    classnm.writable = ersw
    classnm.seekable = ersw
    classnm.read1 = classnm.read


def do_pickle(data):
    s = StringIO.StringIO()
    p = pickle.Pickler(s, protocol=-1)
    p.dump(data)

    # return s.getvalue()
    return base64.b64encode(s.getvalue().encode('zlib_codec'))


def do_unpickle(buf):
    buf = base64.b64decode(buf).decode('zlib_codec')
    s = StringIO.StringIO(buf)
    p = pickle.Unpickler(s)
    return p.load()


class BaseProcessor(object):
    @classmethod
    def mime_test(cls, f):
        raise NotImplementedError()


class BaseContainer(object):
    """
    Wrap around a file and provide a picklable class to access the file in the future
    """
    _container_registry = {}

    @staticmethod
    def add_container_type(container):
        BaseContainer._container_registry[container.__name__] = container

    @staticmethod
    def unpickle(p, job_args):
        args = do_unpickle(p)

        _type = args.pop('_type')
        log.debug('Unpickle {} with args {}'.format(_type, args))

        if _type not in BaseContainer._container_registry:
            log.warn("_type: {0} is NOT in _container_registry: {1}".format(_type, BaseContainer._container_registry))

        nested = {
            'job_args': job_args
        }
        nested_rem = []

        for k, v in args.iteritems():
            if k.startswith('_pickle_'):
                nested[k[8:]] = BaseContainer.unpickle(v, job_args=job_args)
                nested_rem.append(k)

        for r in nested_rem:
            del args[r]
        args.update(nested)

        return BaseContainer._container_registry[_type](**args)

    def get_pickle(self):
        assert self.__class__.__name__ in self._container_registry, "Container {} not registered".format(self.__class__.__name__)

        args = {
            '_type': self.__class__.__name__
        }

        for k, v in self.args.iteritems():
            if isinstance(v, BaseContainer):
                args['_pickle_' + k] = v.get_pickle()
            else:
                args[k] = v

        return do_pickle(args)

    def __repr__(self):
        return u'({}) {}'.format(self.__class__.__name__, self.relative_path())

    def instantiate_file(self):
        raise NotImplementedError(type(self))

    def open(self, args):
        raise NotImplementedError()

    def parent_path(self):
        raise NotImplementedError()

    def filename(self):
        raise NotImplementedError()

    def mktemp(self):
        t = tempfile.mktemp(dir=self.job_args.jobdir)
        assert self.job_args.jobdir.startswith('/tmp/')
        assert t.startswith(self.job_args.jobdir), t
        return t

    def parent(self):
        raise NotImplementedError()

    def relative_path(self):
        """
        relative path for this file (parent relative path + my filename)
        """
        return os.path.join(self.parent_path(), self.filename())

    def __init__(self, **kwargs):
        self.job_args = kwargs.pop('job_args')
        self.args = kwargs
        self.fds = []
        self._remove = set()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

    def cleanup(self):
        for fd in self.fds:
            fd.close()


class FileContainer(BaseContainer):
    """
    Container for files on the file system

    """

    @property
    def __name__(self):
        return "FileContainer"

    def filename(self):
        return self.args['file']

    def parent_path(self):
        return self.args['path']

    def instantiate_file(self):
        return os.path.join(self.job_args.base, self.parent_path(), self.filename())

    def open(self, *args):
        fp = self.instantiate_file()
        log.debug(u'Open {} from {}'.format(self, fp))
        fd = io.FileIO(fp, 'rb')
        self.fds.append(fd)
        return io.BufferedReader(fd)

BaseContainer.add_container_type(FileContainer)


class TempFileContainer(FileContainer):
    def parent(self):
        return self.args['input_fd']

    def parent_path(self):
        return self.parent().relative_path()

    def __enter__(self):
        fp = self.instantiate_file()
        self.job_args.cm.push(fp)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.job_args.cm.pop(self._uncompressed)

    def decompress(self, source, target):
        raise NotImplementedError()

    def __init__(self, **kwargs):
        super(TempFileContainer, self).__init__(**kwargs)
        try:
            parent = self.parent()
            if isinstance(parent, TempFileContainer):
                fp = parent.instantiate_file()
                self.job_args.cm.push(fp)
                log.debug('Added parent fp')
        except:
            pass

    def write_fd(self, fd, target):
        with io.BufferedWriter(io.FileIO(target, mode='wb')) as output:
            chunk = fd.read(BUFSZ)

            while chunk:
                output.write(chunk)
                chunk = fd.read(BUFSZ)

            output.flush()
            output.close()
            fd.close()

    def instantiate_file(self):
        try:
            fp = self._uncompressed
            assert os.path.exists(fp)
            return fp
        except AttributeError:
            pass

        uncompressed_file = self.mktemp()

        with self.parent() as parent:
            source = parent.instantiate_file()
            self.decompress(source, uncompressed_file)
            log.debug(u'UNPACK {} > {}'.format(self, uncompressed_file))
            self._uncompressed = uncompressed_file
            self.job_args.cm.push(uncompressed_file)

        return self._uncompressed

    def cleanup(self):
        log.debug(u'CLEAN  {}'.format(self))

        try:
            r = self._uncompressed
            inuse = self.job_args.cm.pop(r)
            if inuse == 0:
                super(TempFileContainer, self).cleanup()
                self.parent().cleanup()
                log.debug(u'REMOVE {}'.format(self))
                os.remove(r)
            else:
                log.debug(u'INUSE {}'.format(inuse, self))

        except AttributeError:
            return
