import time
from sakura.common.tools import greenlet_env
from enum import Enum
from sakura.hub.access import ACCESS_SCOPES

class DatabaseMixin:
    @property
    def online(self):
        return self.datastore.online and self.datastore.daemon.connected
    @property
    def remote_instance(self):
        return self.datastore.remote_instance.databases[self.name]
    def pack(self):
        result = dict(
            tags = self.tags,
            contacts = tuple(u.login for u in self.contacts),
            database_id = self.id,
            datastore_id = self.datastore.id,
            name = self.name,
            creation_date = self.creation_date,
            access_scope = ACCESS_SCOPES(self.access_scope).name,
            owner = None if self.owner is None else self.owner.login,
            users_rw = tuple(u.login for u in self.users_rw),
            users_ro = tuple(u.login for u in self.users_ro),
            online = self.online
        )
        result.update(**self.metadata)
        return result
    def get_full_info(self, context):
        # start with general metadata
        result = self.pack()
        # if online, explore tables
        if self.online:
            self.update_tables(context)
            result['tables'] = tuple(t.pack() for t in self.tables)
        return result
    def update_tables(self, context):
        # ask daemon
        info_from_daemon = self.remote_instance.pack()
        # update tables (except foreign keys - a referenced table
        # may not be created yet otherwise)
        tables = set()
        for tbl_info in info_from_daemon['tables']:
            info = dict(tbl_info)
            del info['foreign_keys']
            tables.add(context.tables.restore_table(context, self, **info)
        )
        self.tables = tables
        context.db.commit() # make sure db id's are set
        # update foreign keys
        for tbl_info in info_from_daemon['tables']:
            table = context.tables.get(
                database = self,
                name = tbl_info['name']
            )
            table.update_foreign_keys(context, tbl_info['foreign_keys'])
    def update_attributes(self, context,
                users = None, contacts = None, creation_date = None,
                tags = None, access_scope = None, owner = None,
                **metadata):
        # update users
        if users is not None:
            self.users_rw = context.users.from_logins(
                        u for u, grants in users.items() if grants['WRITE'])
            self.users_ro = context.users.from_logins(
                        u for u, grants in users.items() if grants['READ'])
        # update contacts
        if contacts is not None:
            self.contacts = context.users.from_logins(contacts)
        # update creation date
        if creation_date is not None:
            self.creation_date = creation_date
        # update access scope
        if access_scope is not None:
            self.access_scope = getattr(ACCESS_SCOPES, access_scope).value
        # update metadata
        self.metadata.update(**metadata)
        # update owner
        if owner is not None:
            self.owner = context.users.get(login = owner)
        # update tags
        if tags is not None:
            self.tags = tags
    def create_on_datastore(self):
        self.datastore.remote_instance.create_db(
                self.name,
                self.owner.login)
    @classmethod
    def create_or_update(cls, context, datastore, name,
                         access_scope=None, owner=None, **kwargs):
        database = cls.get(datastore = datastore, name = name)
        if database is None:
            # unknown database detected on a daemon
            # if access_scope not specified, default to private
            if access_scope is None:
                access_scope = 'private'
            # if owner not specified, set it to datastore's admin
            if owner is None:
                owner = datastore.admin
            else:
                owner = context.users.get(login = owner)
            database = cls( datastore = datastore,
                            name = name,
                            access_scope = getattr(ACCESS_SCOPES, access_scope).value,
                            owner = owner)
        else:
            kwargs.update(access_scope = access_scope, owner = owner)
        database.update_attributes(context, **kwargs)
        return database
    @classmethod
    def restore_database(cls, context, datastore, **db):
        return cls.create_or_update(context, datastore, **db)
    @classmethod
    def create_db(cls, context, datastore, name, access_scope, creation_date = None, **kwargs):
        greenlet_env.user = 'etienne'    # TODO: handle this properly
        if creation_date is None:
            creation_date = time.time()
        # register in central db
        new_db = cls.create_or_update(context,
                        datastore = datastore,
                        name = name,
                        access_scope = access_scope,
                        owner = greenlet_env.user,
                        creation_date = creation_date,
                        **kwargs)
        # request daemon to create db on the remote datastore
        new_db.create_on_datastore()
        # return database_id
        context.db.commit()
        return new_db.id

