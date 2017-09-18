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

from functools import partial
import json
import logging
from time import sleep
import sys

import requests

from config import VK_ACCESS_TOKEN

# levels (from low to high): DEBUG -> INFO -> WARNING -> ERROR -> CRITICAL.
logging.basicConfig(level=logging.ERROR, format='[line:%(lineno)d]# %(asctime)s * %(levelname)s *** %(message)s')
# logging.basicConfig(level=logging.DEBUG, format=u'[LINE:%(lineno)d]# %(levelname)-8s [%(asctime)s]  %(message)s')
# logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s', level=logging.DEBUG,
#                     filename=u'graduate_work.log')

VK_URL = 'https://api.vk.com/method/'
VK_VERSION = 5.68
SHORT_RUN = False # switcher for short running way - if SHORT_RUN = True then program check 117 friends instead of 834 friends
SHORT_RUN_COUNT = 117
ERROR_TOO_MANY_REQUESTS = 6
ERROR_USER_WAS_DELETED_OR_BANNED = 18
STEP_FOR_PRINT_PROGRESS = 5
MY_ERROR_CODE = 0
MY_OK_CODE = 1

class VkFriends():
    root_friend_id = None  # root_vk_id = '5030613'
    root_friend_first_name = None
    root_friend_last_name = None
    root_friends_count = 0
    root_friends_id_set = None
    groups_count = 0
    root_friend_groups_set = None
    different_group_set = None
    vk_group_result_list = []
    name = ''
    gid = None
    members_count = 0

    def __init__(self, vk_id):
        """ https://https://api.vk.com/method/users.get?
        :param vk_id: <int> or <str> user_id.
        :return: info about user (user_id).
        """
        self.root_friend_id = vk_id
        params = self.make_vk_params()
        execution_code, response_json = self._do_vk_users_get_request(params=params)
        if execution_code == MY_ERROR_CODE:
            print('Root friend ID is incorrect. Bye ...')
            exit(0)
        elif response_json['first_name'] == 'DELETED':
            print('Root friend is DELETED. Bye ...')
            exit(0)
        else:
            self.root_friend_first_name = response_json['first_name']
            self.root_friend_last_name = response_json['last_name']
            logging.debug('__init__: execution_code -> {}'.format(execution_code))
            logging.debug('response_json -> {}'.format(response_json))
            print('Root friend {} is founded.'.format(self.root_friend_id))

    def _do_vk_users_get_request(self, params):
        execution_code, response_json = self._do_vk_request('users.get', params)
        if execution_code == MY_OK_CODE:
            return execution_code, response_json['response'][0]
        else:
            return execution_code, response_json


    def _do_vk_request(self, method, params):
        """return result of requests to VK
        https://https://api.vk.com/method/?
         & access_token=<VK-token>
         & v=<версия интерфейса>
        :param method=<vk request metod>: <str>
        :return: <json> response.
        """
        request_have_done = False
        while not request_have_done:
            try:
                response = requests.get(VK_URL + method, params=params)
            except requests.exceptions.ConnectionError as err:  #  ConnectionError
                logging.warning('ConnectionError. Try to new connect.')
                sleep(2)
                continue
            except requests.exceptions.HTTPError as err:  #  ConnectionError
                logging.warning('HTTPError. Try to new connect.')
                sleep(2)
                continue

            else:
                if response.status_code == requests.codes.ok:
                    response_json = response.json()
                    if 'error' in response_json:
                        logging.info('Requests error: response.status_code -> {}'.format(response.status_code))
                        logging.info('_do_vk_request status_code -> {}'.format(response.status_code))
                        logging.info(response_json)
                        if response_json['error']['error_code'] == ERROR_TOO_MANY_REQUESTS:
                            continue
                        return MY_ERROR_CODE, response_json
                    request_have_done = True
                    return MY_OK_CODE, response_json


    def print_root_user_info(self):
        """print info about root user
        """
        print('Name: {} {}'.format(self.root_friend_first_name, self.root_friend_last_name))
        print('friend_count = {}'.format(self.root_friends_count))
        print('groups_count = {}'.format(self.groups_count))

    def make_vk_params(self, **kwargs):
        params = {
            'user_id': self.root_friend_id,
            'access_token': VK_ACCESS_TOKEN,
            'v': VK_VERSION
        }
        params.update(kwargs)
        return params

    def root_friend_make_groups_set(self):
        """make list of groups by root_friend (tim_leary)
        """
        groups_count, root_friend_groups_set = self._any_make_groups_set(self.root_friend_id)
        if groups_count == 0:
            logging.debug('root_friend_make_groups_set() not done')
            return MY_ERROR_CODE

        self.groups_count = groups_count
        self.root_friend_groups_set = root_friend_groups_set
        return MY_OK_CODE

    def _any_make_groups_set(self, vk_id):
        """make list of groups for any user
        """
        params = self.make_vk_params(user_id=vk_id)
        execution_code, response_json = self._do_vk_groups_get_request(params)
        if execution_code == MY_ERROR_CODE :
            logging.info('Error in _any_make_groups_set -> vk_id -> {}'.format(vk_id))
            logging.info(response_json)
            return execution_code, response_json
        else:
            groups_count = response_json['count']
            root_friend_groups_set = set(response_json['items'])
            return groups_count, root_friend_groups_set

    def _do_vk_groups_get_request(self, params):
        execution_code, response_json = self._do_vk_request('groups.get', params)
        if execution_code == MY_OK_CODE:
            return MY_OK_CODE, response_json['response']
        else:
            if response_json['error']['error_code'] == ERROR_USER_WAS_DELETED_OR_BANNED:
                return MY_ERROR_CODE, response_json['error']
            logging.debug(
                u'vk_id: {}, error code: {}, error_msg: {}'.format(params['user_id'], response_json['error']['error_code'],
                                                                   response_json['error']['error_msg']))
            return MY_ERROR_CODE, response_json['error']


    def make_different_group_list(self):
        if self.root_friends_count == 0:
            print('Root friend have no friends. Bye ...')
            exit(0)
        for counter, friend_id in enumerate(self.root_friends_id_set):
            if counter % STEP_FOR_PRINT_PROGRESS == 0:
                print('Find exclusive groups: {} friends of {}'.format(counter, len(self.root_friends_id_set)))
            friend_groups_set_num, friend_groups_set = self._any_make_groups_set(vk_id=friend_id)
            if friend_groups_set_num == 0:
                logging.info('root_friend_make_groups_set() not done, Error = {}'.format(friend_groups_set_num))
                continue
            else:
                self.root_friend_groups_set.difference_update(friend_groups_set)

        print('Find exclusive groups completed.')
        self.different_group_set = self.root_friend_groups_set
        print('Numbers of "tim_leary" exclusive groups -> {}'.format(len(self.root_friend_groups_set)))
        logging.debug(u'Numbers of "tim_leary" exclusive groups -> {}'.format(len(self.root_friend_groups_set)))

    def make_root_friend_id_set(self):
        """
        https://api.vk.com/method/users.get?
        user_id=<user_id> User, for which a list of friends is created
         & access_token=<VK-token>
         & v=<версия интерфейса VK>
         & count=<количество выводимых id друзей>
        :param self: <int> or <str> self.root_friend
        :return: <int> friend_count and <list> friend_id_list
        """
        if SHORT_RUN:
            params = self.make_vk_params(count=SHORT_RUN_COUNT)
        else:
            params = self.make_vk_params()
        execution_code, response_json = self._do_vk_friends_get_request(params=params)
        logging.info('make_root_friend_id_list: execution_code -> {}'.format(execution_code))
        logging.debug('response_json -> {}'.format(response_json))

        if execution_code:
            self.root_friends_count = response_json['count']
            friends_id_list = response_json['items']
            self.root_friends_id_set = set(friends_id_list)

    def _do_vk_friends_get_request(self, params):
        execution_code, response_json = self._do_vk_request('friends.get', params)
        logging.warning('_do_vk_friends_get_request: execution_code -> {}'.format(execution_code))
        logging.debug('response_json -> {}'.format(response_json))

        if execution_code == MY_OK_CODE:
            logging.warning('_do_vk_friends_get_request: try response_json =  after execution_code -> {}'.format(execution_code))
            return execution_code, response_json['response']
        else:
            logging.warning('_do_vk_friends_get_request: except KeyError after execution_code -> {}'.format(execution_code))
            return execution_code, response_json['error']

    def make_report_to_file(self):
        print('Making a report.')
        params = self.make_vk_params(extended=1)
        execution_code, response_json = self._do_vk_groups_get_request(params=params)
        group_list = response_json['items']

        for group in group_list:
            vk_group = {
                "name": '',
                "gid": None,
                "members_count": 0
            }

            if group['id'] in self.different_group_set:
                vk_group['gid'] = group['id']
                vk_group['name'] = group['name']
                execution_code, new_group = self._get_group_members_count(vk_group)
                if execution_code == 1:
                    self.vk_group_result_list.append(new_group)

        print('Saving report to file "{}".'.format('groups.json'))
        with open('groups.json', 'w', encoding='utf-8') as f:  # , encoding='utf-8'
            json.dump(self.vk_group_result_list, f, ensure_ascii=False)

        print('Have done.')

    def _get_group_members_count(self, vk_group_type):
        """ add with members_count of vk_group to vk_group <vk_group type>
        :param vk_group_type: <vk_group type>.
        :return: struct <vk_group type> with members_count of vk_group.
        """
        params = self.make_vk_params(extended=1, group_id=vk_group_type['gid'])
        execution_code, response_json = self._do_vk_request('groups.getMembers', params=params)

        if execution_code == MY_OK_CODE:
            vk_group_type['members_count'] = response_json['response']['count']
            return execution_code, vk_group_type
        else:
            return execution_code, response_json


def main():
    try:
        root_vk_id = sys.argv[1]
    except IndexError:
        root_vk_id = '5030613'  #  root_vk_id = '5030613' is tim_leary
    # root_vk_id = 50032764534200241237464765874659873465347856  # test ID
    # root_vk_id = 5003276453420024123  # test ID

    tim_leary = VkFriends(root_vk_id)
    tim_leary.make_root_friend_id_set()
    tim_leary.root_friend_make_groups_set()

    tim_leary.print_root_user_info()
    tim_leary.make_different_group_list()

    tim_leary.make_report_to_file()


if __name__ == '__main__':
    main()
