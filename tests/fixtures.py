import pytest

from redact.data_structures import Hashset
from redact.data_structures import List
from redact.data_structures import Set
from redact.data_structures import SortedSet
from redact.db import get_redis_conn
from redact.model import BaseModel
from redact.model import KeyValueField
from redact.model import save
from redact.model import RemoteKeyValueField


class TestModel(BaseModel):
    def __init__(self, key, test_str_value_1=None, test_str_value_2=None, test_str_value_3=None):
        super(TestModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)
        self.test_str_2 = KeyValueField('t2', test_str_value_2)
        self.test_str_3 = KeyValueField('t3', test_str_value_3)
        self.test_remote_key_value = RemoteKeyValueField('tr', 'trkv:{}'.format(key))


class TestListModel(BaseModel):
    def __init__(self, key, l=[]):
        super(TestListModel, self).__init__(key)
        self.l = KeyValueField('l', l)


class TestMigratedModel(BaseModel):
    def __init__(self, key, test_str_value_1=None, test_str_value_2=None, test_str_value_3=None, test_extra_value_1=None, test_extra_value_2=None):
        super(TestMigratedModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)
        self.test_str_2 = KeyValueField('t2', test_str_value_2)
        self.test_str_3 = KeyValueField('t3', test_str_value_3)
        self.test_extra_value_1 = KeyValueField('e1', test_extra_value_1)
        self.test_extra_value_2 = KeyValueField('e2', test_extra_value_2)

    def get_migrations(self):
        def migration_1(base_model):
            base_model.test_extra_value_1 = "TEST_MIGRATION_VALUE_1"

        def migration_2(base_model):
            base_model.test_extra_value_2 = "TEST_MIGRATION_VALUE_2"
        return [migration_1, migration_2]


class TestRemoteModel(BaseModel):
    def __init__(self, key, test_str_value_1=None):
        super(TestRemoteModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)


### Test fixtures
@pytest.fixture
def model(request):
    model = TestModel('test_model_1', 'a', 'b', 'c')

    def fin():
        get_redis_conn().delete(model.key)
    request.addfinalizer(fin)
    return model


@pytest.fixture
def saved_model(request):
    model = TestModel('test_model_1', 'a', 'b', 'c')
    remote_model = TestRemoteModel(model.test_remote_key_value, 'd')
    save(model)
    save(remote_model)

    def fin():
        try:
            get_redis_conn().delete(model.key)
            get_redis_conn().delete(remote_model.key)
        except Exception:
            pass
    request.addfinalizer(fin)
    return model


@pytest.fixture
def saved_list_model(request):
    model = TestListModel('test_list_model_1', [])
    save(model)

    def fin():
        try:
            get_redis_conn().delete(model.key)
        except Exception:
            pass
    request.addfinalizer(fin)
    return model


@pytest.fixture
def sorted_set(request):
    model = SortedSet('test_sorted_set')

    def fin():
        get_redis_conn().delete('test_sorted_set')
    request.addfinalizer(fin)
    return model


@pytest.fixture
def list(request):
    model = List('test_list')

    def fin():
        get_redis_conn().delete('test_list')
    request.addfinalizer(fin)
    return model


@pytest.fixture
def hashset(request):
    model = Hashset('test_hashset')

    def fin():
        get_redis_conn().delete('test_hashset')
    request.addfinalizer(fin)
    return model


@pytest.fixture
def set(request):
    model = Set('test_set')

    def fin():
        get_redis_conn().delete('test_set')
    request.addfinalizer(fin)
    return model


@pytest.fixture
def set_2(request):
    model = Set('test_set_2')

    def fin():
        get_redis_conn().delete('test_set_2')
    request.addfinalizer(fin)
    return model
