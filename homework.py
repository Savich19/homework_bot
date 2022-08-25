import logging
import os
import requests
import telegram
from dotenv import load_dotenv
import time


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


def send_message(bot, message):
    """Отправка сообщения в Telegram чат."""

    bot.send_message(TELEGRAM_CHAT_ID, message)


def get_api_answer(current_timestamp):
    """Запрос к эндпоинту API-сервиса Практикума."""

    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            url=ENDPOINT,
            headers=HEADERS,
            params=params
        )
        return response.json()
    except Exception as error:
        message = f'Сбой в получении доступа к сайту Практикума: {error}'
        logging.error(message)


def check_response(response):
    """Проверка ответа API на корректность."""

    try:
        return response['homeworks']
    except IndexError:
        message = f'Ошибка в индексе по ключу homeworks: {error}'
        logging.error(message)
    except Exception as error:
        message = f'Значения ключа homeworks повреждены: {error}'
        logging.error(message)


def parse_status(homework):
    """Извлечение из информации о конкретной
    домашней работе статус этой работы."""

    try:
        homework_name = homework['homework_name']
        homework_status = homework['status']
        verdict = HOMEWORK_STATUSES[homework_status]
        message = (f'Изменился статус проверки работы '
                   f'"{homework_name}". {verdict}')
        logging.info('Обработка данных словаря homework успешна')
    except TypeError as error:
        message = f'Ошибка {error} в получении информации'
        logging.error(message)
    except Exception as error:
        message = f'Ошибка {error} в получении информации'
        logging.error(message)
    finally:
        return message


def check_tokens():
    """Проверка переменных окружения."""

    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        message = f'Переменные окружения найдены!'
        logging.info(message)
        return True
    message = f'Переменные окружения не найдены'
    logging.error(message)
    return False


def main():
    """Основная логика работы бота."""

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())

    message = 'Добрый день, Александр!'
    send_message(bot, message)

    last_homeworks = {}

    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.info('Запрос к API-сервису прошел успешно')
            homeworks = check_response(response)
            logging.info('Ответ от API-сервиса корректен')
            if not homeworks:
                logging.info('Домашек нет. Сообщение не отправлено')
            else:
                for homework in homeworks:
                    message = parse_status(homework)
                    homework_name = homework['homework_name']
                    if homework_name in last_homeworks.keys():
                        new_status = homework['status']
                        last_status = last_homeworks[homework_name]
                        if new_status != last_status:
                            send_message(bot, message)
                            logging.info(
                                'Статус дз изменился. Сообщение отправлено')
                        else:
                            logging.info(
                                'Статус дз тот же. Сообщение не отправлено')
                    else:
                        send_message(bot, message)
                        logging.info(
                            'Найдена новая домашка. Сообщение отправлено!')
                    last_homeworks[homework_name] = homework['status']
                current_timestamp = response.get(
                    'current_date', current_timestamp)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=message
            )
            logging.error(message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
