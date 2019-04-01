#!/usr/bin/env python
import os
from boutiques import __file__ as bfile
from boutiques.logger import raise_error, print_info
from boutiques.localExec import extractFileName

class DataHandler(object):
    """
    This class represents
    """

    # Constructor
    def __init__(self):
        cache_dir = os.path.join(os.path.expanduser('~'), ".cache", "boutiques")
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        data_cache_dir = os.path.join(cache_dir, "data")
        if not os.path.exists(data_cache_dir):
            os.makedirs(data_cache_dir)
        self.cache_dir = data_cache_dir
        self.cache_files = os.listdir(cache_dir)

    # Function to display the contents of the cache
    # Option to display an example file which displays an pre-made example file
    # or the first file of the cache if it exists
    # Otherwise displays information about the cache and a list of files
    def inspect(self, example=False):
        self.example = example
        # Display an example json file
        if self.example:
            # Display the first file in cache
            if len(self.cache_files) > 0:
                filename = self.cache_files[0]
                file_path = os.path.join(self.cache_dir, filename)
                self._display_file(file_path)
            # Display the example file
            else:
                example_fn = os.path.join(bfile, "examples", "execution-data",
                                          "execution-data.json")
                self._display_file(example_fn)
        # Print information about files in cache
        else:
            # TODO remove descriptors from list or display seperately
            print("There are {} unpublished files in the cache"
                  .format(len(self.cache_files)))
            print(*self.cache_files, sep="\n")

    # Private function to print a file to console
    def _display_file(self, file_path):
        with open(file_path, 'r') as file_in:
            print(file_in.read())
            file_in.close()

    # Function to publish a data set to Zenodo
    # Options allow to only publish a single file, publish files individually as
    # data sets or bulk publish all files in the cache as one data set (default)
    # and allow author to be set
    def publish(self, single, author="Anonymous", individually=False):
        self.single = single
        self.author = author
        self.individual = individually

    # Function to remove file(s) from the cache
    # Option all will clear the data collection cache of all files
    # or passing in a file will remove only that file
    # Options are mutually exclusive and one is required
    def discard(self, file=None, all=False):
        self.all = all
        self.file = extractFileName(file)
        # Check function is not called without any valid option
        if not self.all and self.file is None:
            msg = "Must indicate a file to discard"
            raise_error(ValueError, msg)
        # Remove all files in the data cache
        if all:
            [os.remove(os.path.join(self.cache_dir, f))
             for f in self.cache_files]
            print_info("All files have been removed from the data cache")
        # Remove the file specified by the file option
        elif file is not None:
            file_path = os.path.join(self.cache_dir, file)
            # Incorrect filename input
            if not os.path.isfile(file_path):
                msg = "File {} does not exist in the data cache".format(file)
                raise_error(ValueError, msg)
            os.remove(file_path)
            print_info("File [] has been removed from the data cache"
                       .format(file))
