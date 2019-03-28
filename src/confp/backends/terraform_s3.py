from __future__ import absolute_import

import json
import logging

from ..config import BASE_MODULE_SCHEMA
from ..exceptions import KeyNotFoundException
from . import BackendBase

LOG = logging.getLogger(__name__)

REQUIREMENTS = ("boto3",)

CONFIG_SCHEMA = BASE_MODULE_SCHEMA.copy()
CONFIG_SCHEMA.update(
    {
        "bucket": dict(type="string", required=True, empty=False),
        "key": dict(type="string", required=True, empty=False),
    }
)


class Backend(BackendBase):
    def connect(self):
        import boto3

        s3 = boto3.client("s3")
        LOG.debug(
            "Getting terraform state from s3://%s/%s",
            self.config["bucket"],
            self.config["key"],
        )
        resp = s3.get_object(Bucket=self.config["bucket"], Key=self.config["key"])
        self.state_raw = json.load(resp["Body"])
        self.state = {}
        # Flatten the state file so we just have keys and values. Any modules will be
        # nested under a '<module_name>.<var_name>' key.
        for module in self.state_raw["modules"]:
            key = module["path"][1:]
            for name, value in module["outputs"].items():
                self.state[".".join(key + [name])] = value["value"]

    def disconnect(self):
        pass

    def get_all(self):
        return self.state_raw

    def get_val(self, key):
        try:
            return self.state[key]
        except KeyError:
            raise KeyNotFoundException("Key %r was not found in Terraform state." % key)
