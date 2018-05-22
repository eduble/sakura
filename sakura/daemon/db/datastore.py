from sakura.daemon.db import drivers
from sakura.daemon.db import adapters
from sakura.daemon.db.database import Database
from sakura.common.io import pack

class DataStoreProber:
    def __init__(self, datastore):
        self.datastore = datastore
        self.driver = datastore.driver
    def probe(self):
        print("DS probing start: %s" % self.datastore.host)
        admin_conn = self.datastore.admin_connect()
        self.users = []
        self.databases = {}
        self.driver.collect_users(admin_conn, self)
        self.driver.collect_dbs(admin_conn, self)
        self.driver.collect_db_grants(admin_conn, self)
        admin_conn.close()
        return self.users, self.databases.values()
    def register_user(self, db_user, createdb_grant):
        user = self.as_sakura_user(db_user)
        if user:
            self.users.append((user, createdb_grant))
    def register_db(self, db_name):
        print("DS probing: found database %s" % db_name)
        self.databases[db_name] = Database(self.datastore, db_name)
    def as_sakura_user(self, db_user):
        if db_user.startswith('sakura_'):
            return db_user[7:]
    def register_grant(self, db_user, db_name, privtype):
        user = self.as_sakura_user(db_user)
        if user:
            self.databases[db_name].grant(user, privtype)

class DataStore:
    def __init__(self, host, datastore_admin, sakura_admin,
                 driver_label, adapter_label, access_scope):
        self.host = host
        self.datastore_admin = datastore_admin
        self.sakura_admin = sakura_admin
        self.driver_label = driver_label
        self.driver = drivers.get(driver_label)
        self._users = None        # not probed yet
        self._databases = None    # not probed yet
        self._online = None       # not probed yet
        self.adapter = adapters.get(adapter_label)
        self.access_scope = access_scope
    def admin_connect(self, db_name = None):
        info = dict(
            host = self.host,
            **self.datastore_admin
        )
        if db_name is not None:
            info.update(dbname = db_name)
        return self.driver.connect(**info)
    @property
    def users(self):
        if self._users is None:
            self.refresh()
        return self._users
    @property
    def databases(self):
        if self._databases is None:
            self.refresh()
        return self._databases
    @property
    def online(self):
        if self._online is None:
            self.refresh()
        return self._online
    def has_user(self, user):
        return user in tuple(zip(*self.users))[0]
    def refresh(self):
        try:
            prober = DataStoreProber(self)
            self._users, databases = prober.probe()
            self._databases = { d.db_name: d for d in databases }
            self._online = True
        except BaseException as exc:
            print('WARNING: %s Data Store at %s is down: %s' % \
                    (self.driver_label, self.host, str(exc).strip()))
            self._online = False
    def pack(self):
        res = dict(
            host = self.host,
            driver_label = self.driver_label,
            admin = self.sakura_admin,
            online = self.online,
            access_scope = self.access_scope
        )
        if self.online:
            databases_overview = tuple(
                database.overview() for database in self.databases.values()
            )
            res.update(
                users = self.users,
                databases = databases_overview
            )
        return pack(res)
    def __getitem__(self, database_label):
        if not self.online:
            raise AttributeError('Sorry, datastore is down.')
        return self.databases[database_label]
    def create_db(self, db_name, owner):
        db_owner = 'sakura_' + owner
        admin_conn = self.admin_connect()
        if not self.has_user(owner):
            self.driver.create_user(admin_conn, db_owner)
        self.driver.create_db(admin_conn, db_name, db_owner)
        admin_conn.close()
        self.refresh()
