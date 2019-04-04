#!/usr/bin/env python
import os
import requests
from boutiques import __file__ as bfile
from boutiques.logger import raise_error, print_info
from boutiques.localExec import extractFileName
from boutiques.zenodoHelper import ZenodoHelper, ZenodoError


class DataHandler(object):

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
                                          "execution-record.json")
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
    def publish(self, file, zenodo_token, author="Anonymous",
                individually=False, sandbox=False, no_int=False,
                verbose=False):
        self.filename = extractFileName(file)
        self.zenodo_access_token = zenodo_token
        self.author = author
        self.individual = individually
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.zenodo_helper = ZenodoHelper(sandbox, no_int, verbose)
        self.zenodo_endpoint = self.zenodo_helper.get_zenodo_endpoint()

        # Set Zenodo access token and save to configuration file
        if self.zenodo_access_token is None:
            self.zenodo_access_token = self.zenodo_helper\
                .get_zenodo_access_token()
        self.zenodo_helper.save_zenodo_access_token()

        # Verify publishing
        if not self.no_int:
            prompt = self._get_publishing_prompt()
            try:
                ret = raw_input(prompt)  # Python 2
            except NameError:
                ret = input(prompt)  # Python 3
            if ret.upper() != "Y":
                return
        self.zenodo_helper.zenodo_test_api()

        # Flag for data-set size
        self.bulk_publish = False
        # Single record publication
        if self.filename is not None:
            self._file_exists_in_cache(self.filename)
            self._zenodo_publish([self.filename])
        # All records published to individual data-sets
        elif individually:
            for file in self.cache_files:
                self._zenodo_publish([file])
        # All records published to one data-set
        else:
            self.bulk_publish = True
            self._zenodo_publish(self.cache_files)

    # Private method to publish all the records in file_list to a single
    # data-set on Zenodo
    def _zenodo_publish(self, files_list):
        # Create deposition
        deposition_id = self.zenodo_helper.zenodo_deposit(
            self._create_metadata(), self.zenodo_access_token)

        # Upload all files in files_list to deposition
        for file in files_list:
            self._zenodo_upload_dataset(deposition_id, file)

        # Publish deposition
        msg_obj = "Records" if self.bulk_publish \
            else "Record {}".format(files_list[0])
        self.zenodo_helper.zenodo_publish(self.zenodo_access_token,
                                          deposition_id, msg_obj)

    # Private function to set up  metadata
    def _create_metadata(self):
        data = {
            'metadata': {
                'upload_type': 'dataset',
                'description': "Boutiques execution data-set",
                'creators': [{'name': self.author}],
                'keywords': ['Boutiques'],
            }
        }
        data['metadata']['title'] = "Execution Records"
        keywords = data['metadata']['keywords']

    def _zenodo_upload_dataset(self, deposition_id, file):
        file_path = os.path.join(self.cache_dir, file)
        data = {'filename': file}
        files = {'file': open(file_path, 'rb')}
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/files'
                          % deposition_id,
                          params={'access_token': self.zenodo_access_token},
                          data=data,
                          files=files)

        if(r.status_code != 201):
            raise_error(ZenodoError, "Cannot upload descriptor", r)
        if(self.verbose):
            print_info("Descriptor uploaded to Zenodo", r)

    def _get_publishing_prompt(self):
        if self.filename is not None:
            return ("The dataset {} will be published to Zenodo, "
                    "this cannot be undone. Are you sure? (Y/n) "
                    .format(self.filename))
        if self.individual:
            return ("The records will be published to Zenodo each as "
                    "separate data-sets. This cannont be undone. Are you "
                    "sure? (Y/n ")
        return ("The records will be published to Zenodo as a data-set. This "
                "cannot be undone. Are you sure? (Y/n) ")


    # Function to remove file(s) from the cache
    # Option all will clear the data collection cache of all files
    # or passing in a file will remove only that file
    # Options are mutually exclusive and one is required
    def delete(self, file=None, all=False):
        self.all = all
        self.filename = extractFileName(file)
        # Check function is not called without any valid option
        if not self.all and self.filename is None:
            msg = "Must indicate a file to discard"
            raise_error(ValueError, msg)
        # Remove all files in the data cache
        if all:
            [os.remove(os.path.join(self.cache_dir, f))
             for f in self.cache_files]
            print_info("All files have been removed from the data cache")
        # Remove the file specified by the file option
        elif file is not None:
            # Check file exists in cache
            self._file_exists_in_cache(file)
            # Remove file from cache
            file_path = os.path.join(self.cache_dir, file)
            os.remove(file_path)
            print_info("File [] has been removed from the data cache"
                       .format(file))

    def _file_exists_in_cache(self, filename):
        file_path = os.path.join(self.cache_dir, filename)
        # Incorrect filename input
        if not os.path.isfile(file_path):
            msg = "File {} does not exist in the data cache".format(filename)
            raise_error(ValueError, msg)

