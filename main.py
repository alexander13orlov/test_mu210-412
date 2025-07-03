import logging
import time
from pymodbus.client import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusException
from pymodbus.pdu import ExceptionResponse

# Настройка логгирования
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Форматтер для логов
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

# Консольный логгер
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Файловый логгер
file_handler = logging.FileHandler('modbus_operations.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def write_register(client, address, value, unit=1):
    """Запись значения в регистр с обработкой ошибок"""
    try:
        response = client.write_register(address, value, unit=unit)
        if isinstance(response, ExceptionResponse):
            logger.error(f"Modbus error: {response}")
            return False
        logger.info(f"Успешная запись: регистр {address} = {value}")
        return True
    except ModbusException as e:
        logger.error(f"Ошибка записи: {e}")
        return False

def read_register(client, address, unit=1):
    """Чтение значения регистра с обработкой ошибок"""
    try:
        response = client.read_holding_registers(address, 1, slave=unit)
        if response.isError() or isinstance(response, ExceptionResponse):
            logger.error(f"Modbus error: {response}")
            return None
        value = response.registers[0]
        logger.info(f"Прочитано: регистр {address} = {value}")
        return value
    except ModbusException as e:
        logger.error(f"Ошибка чтения: {e}")
        return None

def main():
    # Параметры подключения (замените на актуальные для вашего устройства)
    port = 'COM1'           # Укажите правильный COM-порт
    baudrate = 9600         # Скорость обмена
    parity = 'N'            # Четность
    stopbits = 1            # Стоп-биты
    bytesize = 8            # Размер байта

    # Создание Modbus-клиента
    client = ModbusClient(
        method='rtu',
        port=port,
        baudrate=baudrate,
        parity=parity,
        stopbits=stopbits,
        bytesize=bytesize
    )

    try:
        # Установка соединения
        logger.info("Подключение к устройству...")
        if not client.connect():
            logger.error("Не удалось подключиться к устройству")
            return
        
        logger.info("Соединение установлено успешно")
        
        # 1. Запись a=2 в регистр 372 (0x174)
        if not write_register(client, 372, 2):
            return
        
        # 2. Запись b=1000 в регистр 404 (0x194)
        if not write_register(client, 404, 1000):
            return
        
        # 3. Ожидание обнуления регистра 538 (0x21A)
        logger.info("Ожидание обнуления регистра 538...")
        while True:
            value = read_register(client, 538)
            if value is None:
                return
            if value == 0:
                logger.info("Регистр 538 достиг 0")
                break
            time.sleep(0.5)  # Пауза между опросами
        
        # 4. Запись 0 в регистр 404
        if not write_register(client, 404, 0):
            return
        
        # 5. Запись b=800 в регистр 404 (0x194)
        if not write_register(client, 404, 800):
            return
        
        # 6. Повторное ожидание обнуления регистра 538
        logger.info("Ожидание обнуления регистра 538...")
        while True:
            value = read_register(client, 538)
            if value is None:
                return
            if value == 0:
                logger.info("Регистр 538 достиг 0")
                break
            time.sleep(0.5)
        
        # 7. Запись 0 в регистр 404
        if not write_register(client, 404, 0):
            return
        
        logger.info("Все операции успешно завершены!")

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        client.close()
        logger.info("Соединение закрыто")

if __name__ == "__main__":
    main()