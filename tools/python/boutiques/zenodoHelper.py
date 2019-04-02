#!/usr/bin/env python
import os
import json
import requests
from boutiques.logger import raise_error, print_info

class ZenodoError(Exception):
    pass



class ZenodoHelper(object):

    # Constructor
    def __init__(self, sandbox=False, no_int=False, verbose=False):
        self.sandbox = sandbox
        self.no_int = no_int
        self.verbose = verbose
        self.config_file = os.path.join(os.path.expanduser('~'), ".boutiques")
        self.zenodo_endpoint = self.get_zenodo_endpoint()


    def get_zenodo_access_token(self):
        json_creds = self.read_credentials()
        if json_creds.get(self.config_token_property_name()):
            return json_creds.get(self.config_token_property_name())
        if (self.no_int):
            raise_error(ZenodoError, "Cannot find Zenodo credentials.")
        prompt = ("Please enter your Zenodo access token (it will be "
                  "saved in {0} for future use): ".format(self.config_file))
        try:
            return raw_input(prompt)  # Python 2
        except NameError:
            return input(prompt)  # Python 3

    def save_zenodo_access_token(self, access_token):
        json_creds = self.read_credentials()
        json_creds[self.config_token_property_name()] = access_token
        with open(self.config_file, 'w') as f:
            f.write(json.dumps(json_creds, indent=4, sort_keys=True))
        if (self.verbose):
            print_info("Zenodo access token saved in {0}".
                       format(self.config_file))

    def get_zenodo_endpoint(self):
        endpoint = "https://sandbox.zenodo.org" if self.sandbox \
            else "https://zenodo.org"
        if (self.verbose):
            print_info("Using Zenodo endpoint {0}"
                       .format(endpoint))
        return endpoint

    def config_token_property_name(self):
        if self.sandbox:
            return "zenodo-access-token-test"
        return "zenodo-access-token"

    def read_credentials(self):
        try:
            with open(self.config_file, "r") as f:
                json_creds = json.load(f)
        except IOError:
            json_creds = {}
        except ValueError:
            json_creds = {}
        return json_creds

    def zenodo_test_api(self):
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions')
        if(r.status_code != 401):
            raise_error(ZenodoError, "Cannot access Zenodo", r)
        if(self.verbose):
            print_info("Zenodo is accessible", r)
        r = requests.get(self.zenodo_endpoint+'/api/deposit/depositions',
                         params={'access_token': self.zenodo_access_token})
        message = "Cannot authenticate to Zenodo API, check your access token"
        if(r.status_code != 200):
            raise_error(ZenodoError, message, r)
        if(self.verbose):
            print_info("Authentication to Zenodo successful", r)

    def zenodo_deposit(self, metadata, access_token):
        headers = {"Content-Type": "application/json"}
        data = metadata

        r = requests.post(self.zenodo_endpoint+'/api/deposit/depositions',
                          params={'access_token': access_token},
                          json={},
                          data=json.dumps(data),
                          headers=headers)
        if(r.status_code != 201):
            raise_error(ZenodoError, "Deposition failed", r)
        zid = r.json()['id']
        if(self.verbose):
            print_info("Deposition succeeded, id is {0}".
                       format(zid), r)
        return zid

    def zenodo_deposit_updated_version(self, update_metadata, delete_files,
                                       access_token, deposition_id):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/newversion'
                          % deposition_id,
                          params={'access_token': access_token})
        if(r.status_code != 201):
            raise_error(ZenodoError, "Deposition of new version failed. Check "
                                     "that the Zenodo ID is correct (if one "
                                     "was provided).", r)
        if(self.verbose):
            print_info("Deposition of new version succeeded", r)
        new_url = r.json()['links']['latest_draft']
        new_zid = new_url.split("/")[-1]
        update_metadata(new_zid, r.json()['doi'])
        delete_files(new_zid, r.json()["files"])
        return new_zid

    def zenodo_publish(self, access_token, deposition_id, msg_obj):
        r = requests.post(self.zenodo_endpoint +
                          '/api/deposit/depositions/%s/actions/publish'
                          % deposition_id,
                          params={'access_token': access_token})
        if(r.status_code != 202):
            raise_error(ZenodoError, "Cannot publish {}".format(msg_obj), r)
        if(self.verbose):
            print_info("{0} published to Zenodo, doi is {1}".
                       format(msg_obj, r.json()['doi']), r)
        return r.json()['doi']