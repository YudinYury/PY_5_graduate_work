"""graduate work
Задание:
Вывести список групп в ВК в которых состоит пользователь, но не состоит никто из его друзей.
В качестве жертвы, на ком тестировать, можно использовать: https://vk.com/tim_leary

Входные данные:
имя пользователя или его id в ВК, для которого мы проводим исследование
Внимание: и имя пользователя (tim_leary) и id (5030613)  - являются валидными входными данными
Ввод можно организовать любым способом:
из консоли
из параметров командной строки при запуске
из переменной
Выходные данные:
файл groups.json в формате
[
{
“name”: “Название группы”,
“gid”: “идентификатор группы”,
“members_count”: количество_участников_собщества
},
{
…
}
]
Форматирование не важно, важно чтобы файл был в формате json

Требования к программе:
Программа не падает, если один из друзей пользователя помечен как “удалён” или “заблокирован”
Показывает что не зависла: рисует точку или чёрточку на каждое обращение к api
Не падает, если было слишком много обращений к API
(Too many requests per second)
Ограничение от ВК: не более 3х обращений к API в секунду.
Могут помочь модуль time (time.sleep) и конструкция (try/except)
Код программы удовлетворяет PEP8

Дополнительные требования (не обязательны для получения диплома):
Показывает прогресс:  сколько осталось до конца работы (в произвольной форме: сколько обращений к API, сколько минут,
сколько друзей или групп осталось обработать)
Восстанавливается если случился ReadTimeout
Показывать в том числе группы, в которых есть общие друзья, но не более, чем N человек, где N задаётся в коде

Псевдокод:
Получаем список групп tim_leary -> tim_leary_groups_list
Получаем список друзей tim_leary -> friends
По каждому другу получаем список его групп и проверяем наличие group_id в списке tim_leary_groups_list:
    при совпадении удаляем group_id из tim_leary_groups_list
По оставшимся в tim_leary_groups_list номерам group_id ->  записываем в файл groups.json
   ->

"""

import json
import logging
from time import sleep

import requests

from config import VK_ACCESS_TOKEN
from config import root_vk_id  #  root_vk_id = '5030613'

# levels (from low to high): DEBUG, INFO, WARNING, ERROR, CRITICAL.
logging.basicConfig(level=logging.INFO, format='[LINE:%(lineno)d]# %(asctime)s - %(levelname)s - %(message)s')
# logging.basicConfig(level=logging.DEBUG, format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
# logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG,
#                     filename=u'graduate_work.log')

VK_URL = 'https://api.vk.com/method/'
VK_VERSION = 5.68
SHORT_RUN = False # switcher for short running way - check 117 friends instead of 834 friends

class VkFriends():
    root_friend_id = None  # root_vk_id = '5030613'
    root_friend_first_name = None
    root_friend_last_name = None
    root_friends_count = 0
    root_friends_id_list = []
    root_friends_id_set = None
    groups_count = 0
    root_friend_groups_set = None
    different_group_set = None
    vk_group_result_list = []
    dot_count = 0  # counter for "progress line"
    name = ''
    gid = None
    members_count = 0

    def __init__(self, vk_id):
        """
        https://https://api.vk.com/method/users.get?
        user_id=<user_id>
         & access_token=<VK-token>
         & v=<версия интерфейса>
        :param vk_id: <int> or <str> user_id.
        :return: <json> info about user (user_id).
        """
        self.root_friend_id = vk_id
        # params = {
        #     'user_ids': self.root_friend_id,
        #     'access_token': VK_ACCESS_TOKEN,
        #     # 'count': 3,
        #     'v': VK_VERSION
        # }
        params = self.make_vk_params()
        execution_code, response_json = self._do_vk_request('users.get', params)
        response_json = response_json['response'][0]
        self.root_friend_first_name = response_json['first_name']
        self.root_friend_last_name = response_json['last_name']
        logging.info('__init__: execution_code -> {}'.format(execution_code))
        logging.info('response_json -> {}'.format(response_json))

        if not response_json :
            print('Root friend ID is incorrect. Bye ...')
            exit(0)
        elif response_json['first_name'] == 'DELETED':
            print('Root friend is DELETED. Bye ...')
            exit(0)
        else:
            print('Root friend {} is founded.'.format(self.root_friend_id))

    def print_root_user_info(self):
        print('--------- info about root friend ---------')
        print('Name: {} {}'.format(self.root_friend_first_name, self.root_friend_last_name))
        print('friend_count = {}'.format(self.root_friends_count))
        # print('self.friend_id_list =', self.friend_id_set)
        print('groups_count = {}'.format(self.groups_count))

    def make_vk_params(self, *args):
        params = {
            'user_id': self.root_friend_id,
            'access_token': VK_ACCESS_TOKEN,
            'v': VK_VERSION
        }
        for i in args:
            params.update(i.items())
        return params

    def print_dot(self):
        """
        print "progress bar" from a lot of dot
        30 dots - border for clearing "progress bar"
        """

        # if self.dot_count == 30:
        #     self.dot_count = 0
        #     print('.')
        # else:
        #     self.dot_count += 1
        #     print('.', end='')

    def get_group_members_count(self, vk_group):
        # vk_group = {
        #     "name": '',
        #     "gid": None,
        #     "members_count": 0
        # }
        params = {
            'group_id': vk_group['gid'],
            'access_token': VK_ACCESS_TOKEN,
            'extended': 1,
            'v': VK_VERSION
        }
        sleep(0.400)
        response = requests.get('https://api.vk.com/method/groups.getMembers', params=params).json()
        vk_group['members_count'] = response['response']['count']
        return vk_group

    def make_report_to_file(self):
        params = {
            'user_id': self.root_friend_id,
            'access_token': VK_ACCESS_TOKEN,
            'extended': 1,
            'v': VK_VERSION
        }
        print('Making a report.')
        response = requests.get('https://api.vk.com/method/groups.get', params=params).json()
        # group_count = response['response']['count']
        group_list = response['response']['items']

        for group in group_list:
            vk_group = {
                "name": '',
                "gid": None,
                "members_count": 0
            }

            if group['id'] in self.different_group_set:
                vk_group['gid'] = group['id']
                vk_group['name'] = group['name']
                new_group = self.get_group_members_count(vk_group)
                self.vk_group_result_list.append(new_group)
                # print(vk_group)
            else:
                continue
        # print(self.vk_group_result_list)

        print('Saving report to file.')
        with open('groups.json', 'w', encoding='utf-8') as f:  # , encoding='utf-8'
            json.dump(self.vk_group_result_list, f, ensure_ascii=False)

        with open('groups.json.txt', 'w', encoding='utf-8') as f:
            json.dump(self.vk_group_result_list, f, ensure_ascii=False)
        print('Have done.')

    def _do_vk_users_get_request(self, params):
        response = self._do_vk_request(self, 'users.get', params)
        if response.status_code == requests.codes.ok:
            response_json = response.json()['response'][0]
            # response_json = response.json()
        else:
            # print(response.raise_for_status())
            return 0
        # print(response_json)
        if response_json['first_name'] == 'DELETED':
            print('Root user was DELETED.')
            return 0
        else:
            return response_json

    def root_friend_make_groups_set(self):
        params = self.make_vk_params()
        groups_count, root_friend_groups_set = self._any_make_groups_set(self.root_friend_id)
        if groups_count == 0:
            logging.debug('root_friend_make_groups_set() not done')
            return 0

        self.groups_count = groups_count
        self.root_friend_groups_set = root_friend_groups_set
        return 1

    def _any_make_groups_set(self, vk_id):
        params = self.make_vk_params()
        params['user_id'] = vk_id
        execution_code, response_json = self._do_vk_groups_get_request(params)
        if execution_code == 0:
            logging.info('do not done _any_make_groups_set -> vk_id -> {}'.format(vk_id))
            return 0, response_json
        else:
            groups_count = response_json['count']
            root_friend_groups_set = set(response_json['items'])
            return groups_count, root_friend_groups_set

    def _do_vk_groups_get_request(self, params):
        execution_code, response_json = self._do_vk_request('groups.get', params)
        try:
            response_json = response_json['response']
            return 1, response_json
        except KeyError:
            # print(response_json)
            logging.error(u'vk_id: {}, error code: {}, error_msg: {}'.format(params['user_id'],
                                                                    response_json['error']['error_code'],
                                                                    response_json['error']['error_msg']))
            if response_json['error']['error_code'] == 18:
                # logging.debug('ID={} -> {}'.format(params['user_id'], response_json['error']['error_msg']))
                # logging.error('ID={} -> {}'.format(params['user_id'], response_json['error']['error_msg']))
                return 0, response_json['error']
                # continue
            logging.debug(
                u'vk_id: {}, error code: {}, error_msg: {}'.format(params['user_id'], response_json['error']['error_code'],
                                                                   response_json['error']['error_msg']))
            return 0, response_json['error']

    def make_different_group_list(self):
        counter = 0
        for friend_id in self.root_friends_id_set:
            if counter % 10 == 0:
                print('Find exclusive groups: {} from {}'.format(counter, len(self.root_friends_id_set)))
            friend_groups_set_num, friend_groups_set = self._any_make_groups_set(vk_id=friend_id)
            counter += 1
            if friend_groups_set_num == 0:
                logging.info('root_friend_make_groups_set() not done, Error = {}'.format(friend_groups_set_num))
                continue
            else:
                self.root_friend_groups_set.difference_update(friend_groups_set)

        print('Find exclusive groups completed: {} from {}'.format(counter, len(self.root_friends_id_set)))
        self.different_group_set = self.root_friend_groups_set
        print('Numbers of "tim_leary" exclusive groups: {}'.format(len(self.different_group_set)))
        logging.debug(u'Numbers of "tim_leary" exclusive groups: {}'.format(len(self.different_group_set)))
        logging.debug(u'different_group_set = {}'.format(self.root_friend_groups_set))

    def make_root_friend_id_list(self):
        """
        https://api.vk.com/method/users.get?
        user_id=<user_id> User, for which a list of friends is created
         & access_token=<VK-token>
         & v=<версия интерфейса VK>
         & count=<количество выводимых id друзей>
        :param self: <int> or <str> self.root_friend
        :return: <int> friend_count and <list> friend_id_list
        """
        params = self.make_vk_params()
        if SHORT_RUN:
            params['count'] = 117
        execution_code, response_json = self._do_vk_friends_get_request(params=params)
        logging.info('make_root_friend_id_list: execution_code -> {}'.format(execution_code))
        logging.debug('response_json -> {}'.format(response_json))

        if execution_code:
            self.root_friends_count = response_json['count']
            self.root_friends_id_list = response_json['items']
            self.root_friends_id_set = set(self.root_friends_id_list)

    def _do_vk_friends_get_request(self, params):
        execution_code, response_json = self._do_vk_request('friends.get', params)
        logging.info('_do_vk_friends_get_request: execution_code -> {}'.format(execution_code))
        logging.debug('response_json -> {}'.format(response_json))
        try:
            response_json = response_json['response']
        except KeyError:
            response_json = response_json['error']
            execution_code = 0
        finally:
            return execution_code, response_json

    def _do_vk_request(self, method, params):
        """
        https://https://api.vk.com/method/?
         & access_token=<VK-token>
         & v=<версия интерфейса>
        :param method=<vk request metod>: <str>
        :return: <json> response.
        """
        any_vk_metods = ['users.get', 'friends.get', 'groups.get', 'groups.getMembers']
        logging.info('_do_vk_request() -> {}'.format(method))
        if not method in any_vk_metods:
            print('You try to call incorrect request "{}"'.format(method))
            return 0

        sleep(0.335)
        # response = requests.get('https://api.vk.com/method/users.get', params=params)
        response = requests.get(VK_URL + method, params=params)
        if response.status_code == requests.codes.ok:
            response_json = response.json()
            request_have_done = True

            return 1, response_json
        else:
            logging.info('response')
            logging.error('response')
            return 0, response

        # request_have_done = False
        # while not request_have_done:
        #
        #     logging.info('raise_for_status -> {}'.format(response.raise_for_status()))
        #     continue



def main():
    # root_vk_id = 50032764534200241237464765874659873465347856  # test ID
    tim_leary = VkFriends(root_vk_id) #  root_vk_id = '5030613' is tim_leary

    tim_leary.make_root_friend_id_list()

    tim_leary.root_friend_make_groups_set()
    tim_leary.print_root_user_info()
    tim_leary.make_different_group_list()

    tim_leary.make_report_to_file()


if __name__ == '__main__':
    main()
