from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from os.path import exists, join
import requests

from .state import StateBase

class HTTPError(Exception):
    def __init__(self, code, reason):
        self.code = code
        self.reason = reason

    def __str__(self):
        return "{}: {}".format(self.code, self.reason)

class BaseFetcher(StateBase):
    """
    Base class for interacting with source data.
    Primary use is fetching data files from source and standardizing names of files,
    which are then cached on S3 by their standardized name and used downstream to load
    results into data store.

    Intended to be subclassed in state-specific fetch.py modules.

    """

    def fetch(self, url, fname=None, overwrite=False):
        """Fetch and cache web page or data file

        Args:
            url: link to download
            fname:  file name for local storage in cache directory
            overwrite: if True, overwrite cached copy with fresh download

        """
        headers = None
        local_file_name = self._standardized_filename(url, fname)

        try:
            if overwrite:
                r = requests.get(url, verify=False)
                file = open(local_file_name, 'w')
                file.write(r.text)
            else:
                if exists(local_file_name):
                    print("File is cached: {}".format(local_file_name))
                else:
                    r = requests.get(url, verify=False)
                    file = open(local_file_name, 'w')
                    file.write(r.text)
                    print("Added to cache: {}".format(local_file_name))
        except HTTPError:
            print("Error downloading {}".format(url))
            assert not exists(local_file_name)

    def _standardized_filename(self, url, fname):
        """A standardized, fully qualified path name"""
        #TODO:apply filename standardization logic
        # non-result pages/files use default urllib name conventions
        # result files need standardization logic (TBD)
        if fname:
            filename = join(self.cache.abspath, fname)
        else:
            filename = self._filename_from_url(url)
        return filename

    def _filename_from_url(self, url):
        #TODO: this is quick and dirty
        # see urlretrieve code for more robust conversion of
        # url to local filepath
        result = urllib.parse.urlsplit(url)
        bits = [
            self.cache.abspath,
            result.netloc + '_' +
            result.path.strip('/'),
        ]
        name = join(*bits)
        return name

    def _remove_local_file(self, local_file_name):
        """
        Remove a downlaoded file.

        This is mostly useful for removing a file when the request results in
        an HTTP error.

        Args:
            local_file_name: Absolute path to the downloaded file.
        """
        # BOOKMARK
