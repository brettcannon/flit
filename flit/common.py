import hashlib
from importlib.machinery import SourceFileLoader
from pathlib import Path

class Module(object):
    """This represents the module/package that we are going to distribute
    """
    def __init__(self, name, directory='.'):
        self.name = name

        # It must exist either as a .py file or a directory, but not both
        pkg_dir = Path(directory, name)
        py_file = Path(directory, name+'.py')
        if pkg_dir.is_dir() and py_file.is_file():
            raise ValueError("Both {} and {} exist".format(pkg_dir, py_file))
        elif pkg_dir.is_dir():
            self.path = pkg_dir
            self.is_package = True
        elif py_file.is_file():
            self.path = py_file
            self.is_package = False
        else:
            raise ValueError("No file/folder found for module {}".format(name))

    @property
    def file(self):
        if self.is_package:
            return self.path / '__init__.py'
        else:
            return self.path


def get_info_from_module(target):
    """Load the module/package, get its docstring and __version__
    """
    sl = SourceFileLoader(target.name, str(target.file))
    m = sl.load_module()
    docstring_lines = m.__doc__.splitlines()
    return {'summary': docstring_lines[0],
            'version': m.__version__}

script_template = """\
#!{interpreter}
from {module} import {func}
if __name__ == '__main__':
    {func}()
"""

def parse_entry_point(ep: str):
    """Check and parse a 'package.module:func' style entry point specification.

    Returns (modulename, funcname)
    """
    if ':' not in ep:
        raise ValueError("Invalid entry point (no ':'): %r" % ep)
    mod, func = ep.split(':')

    if not func.isidentifier():
        raise ValueError("Invalid entry point: %r is not an identifier" % func)
    for piece in mod.split('.'):
        if not piece.isidentifier():
            raise ValueError("Invalid entry point: %r is not a module path" % piece)

    return mod, func

def hash_file(path, algorithm='sha256'):
    with Path(path).open('rb') as f:
        h = hashlib.new(algorithm, f.read())
    return h.hexdigest()

class Metadata:

    home_page = None
    author = None
    maintainer = None
    maintainer_email = None
    license = None
    description = None
    keywords = None
    download_url = None
    requires_python = None

    platform = ()
    supported_platform = ()
    classifiers = ()
    provides = ()
    requires = ()
    obsoletes = ()
    project_urls = ()
    provides_dist = ()
    requires_dist = ()
    obsoletes_dist = ()
    requires_external = ()

    metadata_version="1.2"

    def __init__(self, data):
        self.name = data.pop('name')
        self.version = data.pop('version')
        self.author_email = data.pop('author_email')
        self.summary = data.pop('summary')
        for k, v in data.items():
            assert hasattr(self, k)
            setattr(self, k, v)

    def _normalise_name(self, n):
        return n.lower().replace('-', '_')

    def write_metadata_file(self, fp):
        """Write out metadata in the 1.x format (email like)"""
        fields = [
            'Metadata-Version',
            'Name',
            'Version',
            'Summary',
            'Home-page',
            'License',
        ]
        optional_fields = [
            'Keywords',
            'Author',
            'Author-email',
            'Maintainer',
            'Maintainer-email',
            'Requires-Python',
        ]

        for field in fields:
            value = getattr(self, self._normalise_name(field))
            fp.write("{}: {}\n".format(field, value or 'UNKNOWN'))

        for field in optional_fields:
            value = getattr(self, self._normalise_name(field))
            if value is not None:
                fp.write("{}: {}\n".format(field, value))

        for clsfr in self.classifiers:
            fp.write('Classifier: {}\n'.format(clsfr))

        for req in self.requires_dist:
            fp.write('Requires-Dist: {}\n'.format(req))

        if self.description is not None:
            fp.write('\n' + self.description + '\n')

def make_metadata(module, ini_info):
    md_dict = {'name': module.name, 'provides': [module.name]}
    md_dict.update(get_info_from_module(module))
    md_dict.update(ini_info['metadata'])
    return Metadata(md_dict)
