import pytest
import json
import random
from api_calls import API


def character_template(name='dude', pop_key=None):
    template = {
        "education": "",
        "height": 0,
        "identity": "",
        "name": name,
        "other_aliases": "",
        "universe": "",
        "weight": 0
    }
    if pop_key:
        template.pop(pop_key)
    return template


@pytest.fixture(scope='session')
def api():
    a = API('http://rest.test.ivi.ru/', 'pashtet123@gmail.com', 'hgJH768Cv23')
    yield a
    a.reset_collection()


@pytest.fixture()
def bad_auth_api():
    return API('http://rest.test.ivi.ru/', 'pashtet123@gmail.com', '')


def test_wrong_auth(bad_auth_api):
    r = bad_auth_api.get_all_characters()
    assert r.status_code == 401


@pytest.mark.dependency()
def test_get_characters(api):
    request = api.get_all_characters()
    assert request.status_code == 200
    api.characters = json.loads(request.text)["result"]


@pytest.mark.dependency(depends=["test_get_characters"])
def test_bd_content(api, expected_length=1):
    assert len(api.characters) >= expected_length


@pytest.mark.dependency(depends=["test_bd_content"])
def test_get_user(api):
    character = random.choice(api.characters)
    get_character = api.get_character(character["name"])
    result = json.loads(get_character.text)["result"][0]
    assert result == character


# TODO: find out if there are any constraints for character names
@pytest.mark.parametrize('name', ['Good_Name', '11111', 'G', '10g'])
def test_insert_character(api, name):
    insert = api.insert_character(character_template(name))
    get_character = api.get_character(name)
    assert json.loads(insert.text)["result"] == json.loads(get_character.text)["result"][0]


@pytest.mark.parametrize('pop_key', character_template().keys())
def test_insert_broken_character(api, pop_key, name="failanyway"):
    insert = api.insert_character(character_template(name, pop_key))
    assert insert.status_code == 500  # TODO: ensure that 500 is correct here and request should fail
    get_character = api.get_character(name)
    assert json.loads(get_character.text) == {"result": "No such name"}


@pytest.mark.dependency(depends=["test_bd_content"])
@pytest.mark.parametrize('change_key', character_template(pop_key="name").keys())
def test_modify_character(api, change_key):
    data = random.choice(api.characters)
    name = data["name"]
    data[change_key] = "i am changed"
    modify_result = api.modify_character(name, data)
    assert modify_result.status_code == 200
    get_character = api.get_character(name)
    assert json.loads(get_character.text)["result"][0] == data


@pytest.mark.dependency(depends=["test_bd_content"])
@pytest.mark.parametrize('pop_key', character_template().keys())
def test_invalid_modify_character(api, pop_key):
    data = random.choice(api.characters)
    name = data["name"]
    data.pop(pop_key)
    modify_result = api.modify_character(name, data)
    assert modify_result.status_code == 500  # TODO: ensure that 500 is correct here and request should fail


@pytest.mark.dependency(depends=["test_bd_content"])
def test_delete_existing_character(api):
    api.deleted_character = random.choice(api.characters)
    name = api.deleted_character["name"]
    delete_result = api.delete_character(name)
    get_character = api.get_character(name)
    assert "is deleted" in delete_result.text and "No such name" in get_character.text


def test_delete_nonexistent_character(api):
    name = "i_do_not_exist"
    delete_result = api.delete_character(name)
    assert "No such name" in delete_result.text


@pytest.mark.dependency(depends=["test_delete_existing_character"])
def test_collection_reset(api):
    api.insert_character(character_template("to_be_deleted"))
    api.reset_collection()
    get_deleted = api.get_character(api.deleted_character["name"])
    get_added = api.get_character("to_be_deleted")
    assert json.loads(get_deleted.text)["result"][0] == api.deleted_character and "No such name" in get_added.text


@pytest.mark.dependency(depends=["test_bd_content"])
def test_db_limit(api, db_limit=500):
    characters_needed = db_limit - len(api.characters)
    for i in range(characters_needed):
        api.insert_character(character_template("dummy" + str(i)))
    r = api.insert_character(character_template("failing"))
    assert r.status_code == 400 and json.loads(r.text) == {"error": "Collection can't contain more than 500 items"}
