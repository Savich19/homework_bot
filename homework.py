import logging
import os
import requests
import sys
import telegram
import time
from dotenv import load_dotenv
from http import HTTPStatus
from exceptions import (
    NotTwoHundred,
    NotList,
)


load_dotenv()

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    level=logging.DEBUG,
    filename='program.log',
    format='%(asctime)s, %(levelname)s, %(message)s'
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(stream=sys.stdout)
logger.addHandler(handler)


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""
    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса Практикума."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(
        url=ENDPOINT,
        headers=HEADERS,
        params=params
    )
    if response.status_code != HTTPStatus.OK:
        raise NotTwoHundred('Ошибка соединения')
    return response.json()


def check_response(response):
    """Проверка ответа API на корректность."""
    if not isinstance(response['homeworks'], list):
        raise NotList
    return response['homeworks']


def parse_status(homework):
    """Получение статуса конкретной домашки."""
    homework_name = homework['homework_name']
    homework_status = homework['status']
    verdict = HOMEWORK_STATUSES[homework_status]
    message = (
        f'Изменился статус проверки работы '
        f'"{homework_name}". {verdict}'
    )
    logger.info('Обработка данных словаря homework успешна')
    return message


def check_tokens():
    """Проверка переменных окружения."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = 'Переменные окружения найдены!'
        logger.info(message)
        return True
    message = 'Переменные окружения не найдены'
    logger.critical(message)
    return False


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    message = 'Добрый день, Александр!'
    send_message(bot, message)

    last_homeworks = {}

    while True:
        if check_tokens():
            try:
                response = get_api_answer(current_timestamp)
                logger.info('Запрос к API-сервису прошел успешно')
                homeworks = check_response(response)
                logger.info('Ответ от API-сервиса корректен')
                if not homeworks:
                    logger.info('Новых домашек нет. Сообщение не отправлено')
                else:
                    for homework in homeworks:
                        message = parse_status(homework)
                        homework_name = homework['homework_name']
                        if homework_name in last_homeworks.keys():
                            new_status = homework['status']
                            last_status = last_homeworks[homework_name]
                            if new_status != last_status:
                                send_message(bot, message)
                                logger.info(
                                    'Статус дз изменен. Сообщение отправлено')
                            else:
                                logger.info(
                                    'Статус дз тот же. Сообщение не отправим')
                        else:
                            send_message(bot, message)
                            logger.info(
                                'Найдена новое дз. Сообщение отправлено!')
                        last_homeworks[homework_name] = homework['status']
                    current_timestamp = response.get(
                        'current_date', current_timestamp)
            except NotTwoHundred:
                message = f'Статус сайта Практикума: {response.status_code}'
                logger.error(message)
                send_message(bot, message)
            except IndexError:
                message = 'Запрос к элементу списка с несуществующим индексом'
                logger.error(message)
                send_message(bot, message)
            except KeyError:
                message = 'Ключ словаря не найден в наборе ключей'
                logger.error(message)
                send_message(bot, message)
            except NotList:
                message = 'Полученный ответ - не список'
                logger.error(message)
                send_message(bot, message)
            except Exception as error:
                message = f'Сбой в работе программы: {error}'
                logger.error(message)
                send_message(bot, message)
            finally:
                time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
