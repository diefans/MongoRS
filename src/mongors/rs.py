import functools
from itertools import imap
import pymongo


class reify(object):
    """Cache a property.
    Taken from pyramid."""

    def __init__(self, wrapped):
        self.wrapped = wrapped
        functools.update_wrapper(self, wrapped)

    def __get__(self, inst, objtype=None):
        if inst is None:
            return self
        val = self.wrapped(inst)
        setattr(inst, self.wrapped.__name__, val)
        return val


class ReplicaSetException(Exception):
    pass

class ReplicaSetAlreadyInitialized(ReplicaSetException):
    pass


class ReplicaSetInvalid(ReplicaSetException):
    pass


class ReplicaSet(object):

    def __init__(self, name, *instances, **kwargs):
        self.name = name
        self.instances = instances

        self.read_preference = kwargs.get("read_preference", "secondaryPreferred")

    def uri(self, *instances, **kwargs):
        db = kwargs.get("db")

        uri = "mongodb://{netloc}".format(
            netloc=",".join(':'.join(imap(str, instance)) for instance in instances)
        )

        if db:
            uri = "/".join((uri, db))

        return uri

    @reify
    def client(self):
        client = pymongo.MongoClient(
            self.uri(*self.instances),
            replicaSet=self.name,
            readPreference=self.read_preference,
        )

        return client

    @reify
    def admin_client(self):
        client = pymongo.MongoClient(
            self.uri(self.instances[0], db="admin"),
        )

        return client

    @property
    def config(self):
        config = {
            '_id': self.name,
            'members': [
                {
                    '_id': i,
                    'host': ":".join(imap(str, instance))
                } for i, instance in enumerate(self.instances)
            ],
            'version': 1
        }

        return config

    @property
    def status(self):
        try:
            status = self.admin_client.admin.command("replSetGetStatus")
            return status

        except pymongo.errors.OperationFailure as e:
            if e.details['code'] == 93:
                raise ReplicaSetInvalid(e.details)

    @property
    def is_healthy(self):
        return self.status

    def initiate(self):
        client = self.admin_client

        try:
            result = client.admin.command("replSetInitiate", self.config)

        except pymongo.errors.OperationFailure as e:
            if e.details['code'] == 23:
                # already initialized
                raise ReplicaSetAlreadyInitialized(e.details)
            else:
                # I don't know what else could happen
                raise

    def reconfig(self, force=False):
        return self.admin_client.admin.command("replSetReconfig", self.config, force=force)

    def ensure(self, reconfig=False):
        """Check if there is an active and healthy replica set."""

        try:
            # we have to try to initiate, since if we want to test the set
            # and it is not initiated, we get a long timeout
            # and mongo complaining about the missing Primary()
            self.initiate()

        except ReplicaSetAlreadyInitialized:
            # do further checks with replica set client
            try:
                return self.status

            except ReplicaSetInvalid:
                if reconfig:
                    # try to reconfigure
                    result = self.reconfig(True)

                else:
                    raise

        # should work now, otherwise it sucks
        return self.status
