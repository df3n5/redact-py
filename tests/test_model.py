import json
import pytest

from redact.model import BaseModel
from redact.model import model_dump
from redact.model import model_load
from redact.model import model_save
from redact.model import KeyValueField
from redact.db import get_redis_conn


class TestModel(BaseModel):
    def __init__(self, key, test_str_value_1=None, test_str_value_2=None, test_str_value_3=None):
        super(TestModel, self).__init__(key)
        self.test_str_1 = KeyValueField('t1', test_str_value_1)
        self.test_str_2 = KeyValueField('t2', test_str_value_2)
        self.test_str_3 = KeyValueField('t3', test_str_value_3)


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
            base_model.test_extra_value_1.value = "TEST_MIGRATION_VALUE_1"

        def migration_2(base_model):
            base_model.test_extra_value_2.value = "TEST_MIGRATION_VALUE_2"
        return [migration_1, migration_2]


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
    model_save(model)

    def fin():
        get_redis_conn().delete(model.key)
    request.addfinalizer(fin)
    return model


### Tests
def test_model_load(saved_model):
    assert len(get_redis_conn().keys(saved_model.key)) == 1
    loaded_model = TestModel('test_model_1')
    model_load(loaded_model)
    assert loaded_model.test_str_1.value == saved_model.test_str_1.value
    assert loaded_model.test_str_2.value == saved_model.test_str_2.value
    assert loaded_model.test_str_3.value == saved_model.test_str_3.value


def test_model_save(model):
    assert len(get_redis_conn().keys(model.key)) == 0
    model_save(model)
    assert len(get_redis_conn().keys(model.key)) == 1
    db_model = get_redis_conn().hgetall(model.key)
    assert db_model is not None
    assert model.test_str_1.value == json.loads(db_model['t1'])
    assert model.test_str_2.value == json.loads(db_model['t2'])
    assert model.test_str_3.value == json.loads(db_model['t3'])


def test_model_dump(model):
    json_model = model_dump(model)
    reloaded_json = json.loads(json_model)
    assert model.test_str_1.value == reloaded_json['test_str_1']
    assert model.test_str_2.value == reloaded_json['test_str_2']
    assert model.test_str_3.value == reloaded_json['test_str_3']


def test_model_migration(saved_model):
    assert saved_model.version.value == 0
    loaded_model = TestMigratedModel('test_model_1')
    model_load(loaded_model)
    assert loaded_model.test_str_1.value == saved_model.test_str_1.value
    assert loaded_model.test_str_2.value == saved_model.test_str_2.value
    assert loaded_model.test_str_3.value == saved_model.test_str_3.value
    assert loaded_model.test_extra_value_1.value == "TEST_MIGRATION_VALUE_1"
    assert loaded_model.test_extra_value_2.value == "TEST_MIGRATION_VALUE_2"
    assert loaded_model.version.value == 2

    # Verify migration doesn't happen next time
    loaded_model.test_extra_value_1.value = 'different value 1'
    loaded_model.test_extra_value_2.value = 'different value 2'
    model_save(loaded_model)
    new_loaded_model = TestMigratedModel('test_model_1')
    model_load(new_loaded_model)
    assert new_loaded_model.test_extra_value_1.value != "TEST_MIGRATION_VALUE_1"
    assert new_loaded_model.test_extra_value_2.value != "TEST_MIGRATION_VALUE_2"
    assert new_loaded_model.test_extra_value_1.value == loaded_model.test_extra_value_1.value
    assert new_loaded_model.test_extra_value_2.value == loaded_model.test_extra_value_2.value
    assert new_loaded_model.version.value == 2
