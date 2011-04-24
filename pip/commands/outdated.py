import sys
import pkg_resources
import pip.download
from pip.basecommand import Command
from pip.commands.search import compare_versions, highest_version, \
    transform_hits
from pip.util import get_installed_distributions, get_terminal_size
from pip.log import logger
from pip.backwardcompat import xmlrpclib


class OutdatedCommand(Command):
    name = 'outdated'
    usage = '%prog'
    summary = 'List outdated PyPI packages'

    def __init__(self):
        super(OutdatedCommand, self).__init__()
        self.parser.add_option(
            '--index',
            dest='index',
            metavar='URL',
            default='http://pypi.python.org/pypi',
            help='Base URL of Python Package Index (default %default)')
        self.parser.add_option(
            '-l', '--local',
            dest='local',
            action='store_true',
            default=False,
            help='Only report local packages if inside a virtualenv')
        self.parser.add_option(
            '-p', '--pipe-only',
            dest='pipe',
            action='store_true',
            default=False,
            help='Output list in format suitable to be piped (i.e. to xargs)')

    def run(self, options, args):

        if args:
            logger.warn('ERROR: No arguments are required for this command.')
            return

        index_url = options.index
        local_only = options.local
        pipe_only = options.pipe

        if not pipe_only:
            logger.notify('Searching for outdated packages, please wait...')
        outdated = get_outdated_distributions(index_url, local_only, pipe_only)

        if pipe_only:
            sys.stdout.write(' '.join([entry['name'] for entry in outdated]))
        elif not outdated:
            logger.notify('All packages are up to date.')


def get_outdated_distributions(index_url, local_only=True, pipe_only=False):
    """Get the list of installed packages that have updates available."""
    dists = get_installed_distributions(local_only)
    installed_packages = sorted([d.project_name for d in dists])
    outdated_packages = []

    pypi = xmlrpclib.ServerProxy(index_url, pip.download.xmlrpclib_transport)

    for pkg in installed_packages:
        # Could run all the searches first, and then compare versions, but
        # this way allows for output to be presented to user faster.
        hits = transform_hits(pypi.search({'name': pkg}))
        for hit in hits:
            name = hit['name']
            summary = hit['summary'] or ''
            try:
                if name in installed_packages:
                    dist = pkg_resources.get_distribution(name)
                    latest_pypi = highest_version(hit['versions'])
                    if compare_versions(dist.version, latest_pypi) == -1:
                        outdated_packages.append(hit)
                        if not pipe_only:
                            logger.notify('%s %s (%s)' % (name, dist.version,
                                latest_pypi))
            except UnicodeEncodeError:
                pass

    return outdated_packages

OutdatedCommand()
