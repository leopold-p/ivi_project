import pytest
import json
import random
from api_calls import API

unicode_basic = "!\"#$%&'()*+,-.0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~"


def character_template(name=None, value="", pop_key=None):
    template = {
        "education": value,
        "height": value,
        "identity": value,
        "name": name,
        "other_aliases": value,
        "universe": value,
        "weight": value
    }
    if pop_key:
        template.pop(pop_key)
    return template


@pytest.fixture(scope='session')
def api():
    a = API('http://rest.test.ivi.ru/', 'pashtet123@gmail.com', 'hgJH768Cv23')
    yield a
    a.reset_collection()


@pytest.fixture(scope='class')
def character(api):
    r = api.insert_character(character_template("test_character"))
    yield r
    api.delete_character("test_character")


@pytest.fixture(params=[('pashtet123@gmail.com', ''),
                        ('pashtet123', 'hgJH768Cv23'),
                        ('v', 'hgJH768Cv23'),
                        ('', 'hgJH768Cv23'),
                        ('', '1'),
                        ('v', '1'),
                        ('', '')])
def bad_auth_api(request):
    login, password = request.param
    return API('http://rest.test.ivi.ru/', login, password)


def test_wrong_auth(bad_auth_api):
    """
    Некорректная попытка авторизации:
    запрашиваем characters с различными некорректными данными из фикстуры bad_auth_api
    """
    r = bad_auth_api.get_all_characters()
    assert r.status_code == 401
    assert json.loads(r.text) == {"error": "You have to login with proper credentials"}


@pytest.mark.dependency()
def test_get_characters(api, expected_length=1):
    """
    Получение коллекции:
    запрашиваем characters с корректными username:password
    ожидаем код 200 и не пустой список персонажей
    api.characters и api.unique_names нужны для дальнейших тестов
    """
    request = api.get_all_characters()
    characters = json.loads(request.text)["result"]
    assert request.status_code == 200 and len(characters) >= expected_length
    api.characters = characters
    api.unique_names = set(x["name"] for x in api.characters)


@pytest.mark.dependency(depends=["test_get_characters"])
class TestCollectionContent:

    def test_mangled_characters(self, api):
        """
        Валидация коллекции:
        проверяем, что у каждого персонажа имеются все поля, указанные в документации
        """
        expected_keys = sorted(character_template().keys())
        for character in api.characters:
            assert expected_keys == sorted(character.keys())

    def test_duplicate_characters(self, api):
        """
        Валидация коллекции:
        проверяем отсутствие дубликатов в коллекции
        """
        assert len(api.characters) == len(api.unique_names)


@pytest.mark.dependency(depends=["test_get_characters"])
def test_get_character(api):
    """
    Получение одного персонажа:
    запрашиваем случайно выбранного персонажа из сохраненной коллекции
    получаем данные, совпадающие с имеющимися данными
    """
    existing_character = random.choice(api.characters)
    character = api.get_character(existing_character["name"])
    result = json.loads(character.text)["result"][0]
    assert result == existing_character


@pytest.mark.dependency(depends=["test_get_characters"])
@pytest.mark.parametrize('name', [x+"name" for x in unicode_basic])
def test_get_nonexistent_character(api, name):
    """
    Получение несуществующего персонажа:
    запрашиваем персонажа, проверив, что его имени нет в списке имен персонажей в коллекции
    получаем данные, совпадающие с имеющимися данными
    """
    assert name not in api.unique_names
    character = api.get_character(name)
    assert character.status_code == 200
    assert json.loads(character.text) == {"result": "No such name"}


# TODO: find out if there are any constraints for character names
# TODO: возможно не стоит проходить все символы из unicode_basic, если важно время выполнения теста (+~10 секунд)
@pytest.mark.parametrize('value', [unicode_basic, 9999, 99.99, None, {'a': 'b'}, ['a', 'b']])
@pytest.mark.parametrize('name', [9999, 99.99, "test/name"] + [x+"name" for x in unicode_basic])
def test_insert_character(api, name, value):
    """
    Добавление нового песонажа:
    добавляем нового персонажа
    получаем его данные
    проверяем что полученные данные совпадают с отправленными
    удаляем персонажа
    """
    insertion = api.insert_character(character_template(name, value))
    character = api.get_character(name)
    assert json.loads(insertion.text)["result"] == json.loads(character.text)["result"][0]
    api.delete_character(name)


def test_insert_duplicate_character(api, character):
    """
    Добавление дубликата персонажа:
    добавляем персонажа с существующим в коллекции именем
    получаем ответ, что имя занято
    проверяем что персонаж действительно не добавился
    """
    characters_before = api.get_all_characters()
    name = json.loads(character.text)["result"]["name"]
    insertion = api.insert_character(character_template(name))
    assert "{} is already exists".format(name) in insertion.text
    characters_after = api.get_all_characters()
    assert len(json.loads(characters_before.text)["result"]) == len(json.loads(characters_after.text)["result"])


@pytest.mark.parametrize('pop_key', character_template().keys())
def test_insert_broken_character(api, pop_key, name="failanyway"):
    """
    Добавление персонажа с некорректно составленными данными:
    последовательно пробуем отправить json без каждого поля
    каждый раз получаем ожидаемый ответ 400
    """
    insertion = api.insert_character(character_template(name, pop_key))
    assert insertion.status_code == 400
    character = api.get_character(name)
    assert json.loads(character.text) == {"result": "No such name"}


class TestModifyCharacter:

    @pytest.mark.parametrize('value', [unicode_basic, 9999, 99.99, None, {'a': 'b'}, ['a', 'b']])
    @pytest.mark.parametrize('change_key', character_template(pop_key="name").keys())
    def test_modify_character(self, api, character, change_key, value):
        """
        Изменение данных персонажа:
        изменяем данные персонажа
        запрашиваем данные измененного песонажа
        убеждаемся, что полученные данные соответствуют измененным
        """
        data = json.loads(character.text)["result"]
        name = data["name"]
        data[change_key] = value
        result = api.modify_character(name, data)
        assert result.status_code == 200
        result = api.get_character(name)
        assert json.loads(result.text)["result"][0] == data

    @pytest.mark.parametrize('pop_key', character_template().keys())
    def test_invalid_modify_character(self, api, character, pop_key):
        """
        Изменение данных персонажа на некорректные:
        последовательно пробуем отправить json без каждого поля
        каждый раз получаем ожидаемый ответ 400
        """
        data = json.loads(character.text)["result"]
        name = data["name"]
        data.pop(pop_key)
        result = api.modify_character(name, data)
        assert result.status_code == 400


@pytest.mark.dependency(depends=["test_get_characters"])
def test_delete_existing_character(api, character):
    """
    Удаление персонажа:
    удаляем персонажа
    получаем ожидаемый результат
    пробуем запросить удаленного персонажа
    получаем ответ, что его нет
    """
    api.insert_character(character_template("test_character"))
    result = api.delete_character("test_character")
    character = api.get_character("test_character")
    assert "is deleted" in result.text and "No such name" in character.text


def test_delete_nonexistent_character(api):
    """
    Удаление несуществующего персонажа:
    удаляем персонажа
    получаем ожидаемый результат, что персонаж не найден
    """
    name = "i_do_not_exist"
    delete_result = api.delete_character(name)
    assert "No such name" in delete_result.text


@pytest.mark.dependency(depends=["test_delete_existing_character"])
def test_collection_reset(api):
    """
    Сброс коллекции:
    добавляем нового персонажа и берем из предыдущего теста имя удаленного персонажа
    отправляем запрос на сброс коллекции
    проверяем что добавленный персонаж теперь удален, а удаленный - восстановлен
    """
    api.insert_character(character_template("to_be_deleted"))
    api.reset_collection()
    deleted = api.get_character(api.deleted_character["name"])
    added = api.get_character("to_be_deleted")
    assert json.loads(deleted.text)["result"][0] == api.deleted_character and "No such name" in added.text


@pytest.mark.dependency(depends=["test_get_characters"])
def test_collection_limit(api, db_limit=500):
    """
    Добавление персонажа сверх лимита:
    вычисляем N - количество персонажей в коллекции
    успешно добавляем 500-N персонажей
    добавляем ещё одного
    получаем ответ, что коллекция заполнена
    пробуем запросить последнего добавленного персонажа на случай, если он все равно добавился
    """
    characters_needed = db_limit - len(api.characters)
    for i in range(characters_needed):
        api.insert_character(character_template("dummy" + str(i)))
    r = api.insert_character(character_template("failing"))
    assert r.status_code == 400 and json.loads(r.text) == {"error": "Collection can't contain more than 500 items"}
    character = api.get_character("failing")
    assert "No such name" in character.text
