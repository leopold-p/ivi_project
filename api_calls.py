import requests
from urllib.parse import quote


class API:
    def __init__(self, address, user, password):
        self.address = address
        self.session = requests.session()
        self.session.auth = (user, password)

    def __request(self, method, url, data=None):
        return self.session.request(method, self.address+quote(url), json=data)

    def get_all_characters(self):
        # GET http://rest.test.ivi.ru/characters
        return self.__request('GET', 'characters')

    def get_character(self, name):
        # GET http://rest.test.ivi.ru/character/{name}
        return self.__request('GET', 'character/{}'.format(name))

    def insert_character(self, data):
        # POST http://rest.test.ivi.ru/character
        return self.__request('POST', 'character', data)

    def modify_character(self, name, data):
        # PUT http://rest.test.ivi.ru/character/{name}
        return self.__request('PUT', 'character/{}'.format(name), data)

    def delete_character(self, name):
        # DELETE http://rest.test.ivi.ru/character/{name}
        return self.__request('DELETE', 'character/{}'.format(name))

    def reset_collection(self):
        # POST http://rest.test.ivi.ru/reset
        return self.__request('POST', 'reset')


if __name__ == '__main__':
    api = API('http://rest.test.ivi.ru/', 'pashtet123@gmail.com', 'hgJH768Cv23')
    api.reset_collection()
