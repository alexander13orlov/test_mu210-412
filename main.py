import logging
import time
from pymodbus.client import ModbusSerialClient as ModbusClient
import csv
import os
import csv
# import glob
from pymodbus.exceptions import ModbusException
# from pymodbus.pdu import ExceptionResponse

print("Текущая рабочая директория:", os.getcwd())
print("Файлы в директории:", os.listdir('.'))

exit
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

def write_register(client, address, value, slave=1, function_code=6):
    """Запись значения в регистр с выбором функции записи
    Args:
        client: Modbus клиент
        address: Адрес регистра
        value: Значение для записи
        slave: Адрес устройства (по умолчанию 1)
        function_code: Код функции (6 - запись одного регистра, 16 - запись нескольких регистров)
    """
    try:
        if function_code == 6:
            # Функция 06 (0x06) - запись одного регистра
            response = client.write_register(
                address=address,
                value=value,
                slave=slave
            )
            logger.info(f"Запись через функцию 06: регистр {address} = {value}")
            
        elif function_code == 16:
            # Функция 16 (0x10) - запись нескольких регистров
            # Для одного значения преобразуем в список
            response = client.write_registers(
                address=address,
                values=[value],
                slave=slave
            )
            logger.info(f"Запись через функцию 16: регистр {address} = {value}")
            
        else:
            logger.error(f"Неподдерживаемый код функции: {function_code}")
            return False

        if response.isError():
            logger.error(f"Modbus error: {response}")
            return False
            
        return True
        
    except ModbusException as e:
        logger.error(f"Ошибка записи: {e}")
        return False
def read_register(client, address, slave=1):
    """Чтение значения регистра"""
    try:
        response = client.read_holding_registers(address=address, count=1, slave=slave)
        if response.isError():
            logger.error(f"Modbus error: {response}")
            return None
        value = response.registers[0]
        logger.info(f"Прочитано: регистр {address} = {value}")
        return value
    except ModbusException as e:
        logger.error(f"Ошибка чтения: {e}")
        return None

def generate_mu412_param(all_params):
    mu412 = {}
    output_params_map = {
        "FreqAddr": "Частота генератора импульсов",
        "impNumberAddr": "Количество импульсов генератора импульсов",
        "counterAddr": "Значение счётчика генератора импульсов",
        "type": 'Режим работы выхода'
    }
    
    for output_num in range(1, 25):  # Проверяем все выходы 1-24
        group_name = f"Выход {output_num}"
        do_key = f"do{output_num}"
        
        if group_name in all_params:
            group_params = all_params[group_name]
            
            # Проверяем наличие всех необходимых параметров
            if all(param in group_params for param in output_params_map.values()):
                mu412[do_key] = {
                    key: group_params[rus_name]["address"]
                    for key, rus_name in output_params_map.items()
                }
    
    return mu412

def parse_modbus_params(filename):
    """
    Парсит CSV-файл параметров Modbus в структурированный словарь
    Возвращает словарь: {группа: {параметр: свойства}}
    """
    params = {}
    
    with open(filename, 'r', encoding='utf-8-sig') as f:  # utf-8-sig для обработки BOM
        # Пропускаем заголовки (первые 8 строк)
        for _ in range(8):
            next(f)
        
        reader = csv.reader(f, delimiter=';')
        for row in reader:
            if len(row) < 8:
                continue
                
            # Извлекаем данные из строки
            param_name = row[0].strip()
            group = row[1].strip()
            address = int(row[2])
            address_hex = row[3].strip()
            num_registers = int(row[4])
            read_func = row[5].strip() if row[5].strip() != '-' else None
            write_func = row[6].strip() if row[6].strip() != '-' else None
            data_type = row[7].strip()
            
            # Добавляем в структуру
            if group not in params:
                params[group] = {}
                
            params[group][param_name] = {
                "address": address,
                "address_hex": address_hex,
                "num_registers": num_registers,
                "read_func": read_func,
                "write_func": write_func,
                "data_type": data_type
            }
    
    return params

 # Загрузка параметров из файла
all_params = parse_modbus_params("parameters_mu210-412.csv")

# Генерация структуры
MU412_PARAM = generate_mu412_param(all_params)
output_type = {"logLevel":0, "pwm_lo":1, "pwm_hi":2, "genImp":3}
currentDO = MU412_PARAM["do3"]

def preset(client, freq, numImp, fc=16):
   
    preset2(client, 2, 1)
     # 0. Установка типа выхода
    # if not write_register(client, currentDO["type"], output_type["logLevel"], function_code=fc):
    #     return
    # if not write_register(client, currentDO["type"], output_type["genImp"], function_code=fc):
        # return
    # 1. Запись частоты=0 в регистр currentDO["FreqAddr"]
    if not write_register(client, currentDO["FreqAddr"],freq, function_code=fc):
        return
    # time.sleep(1)
    # 4. Запись 0 в регистр currentDO["impNumberAddr"]
    if not write_register(client, currentDO["impNumberAddr"], 0, function_code=fc):
        return
    logger.info("Запуск импульсов !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # 2. Запись количества импульсов impNum1 в регистр currentDO["impNumberAddr"]
    if not write_register(client, currentDO["impNumberAddr"], numImp, function_code=fc):
        return
        # Ожидание обнуления регистра currentDO["impNumberAddr"]
    logger.info(f"Ожидание {numImp/freq+1}сек обнуления регистра impNumberAddr...")
    time.sleep(numImp/freq+0.5) # прибавка +0.5сек критична, когда было +0,1 он пропускал следующую генерацию, 0.5сек вроде хватает

def preset2(client, freq, numImp, fc=16):
   

     # 0. Установка типа выхода
    # if not write_register(client, currentDO["type"], output_type["logLevel"], function_code=fc):
    #     return
    # if not write_register(client, currentDO["type"], output_type["genImp"], function_code=fc):
        # return
    # 1. Запись частоты=0 в регистр currentDO["FreqAddr"]
    if not write_register(client, currentDO["FreqAddr"],freq, function_code=fc):
        return
    # time.sleep(1)
    # 4. Запись 0 в регистр currentDO["impNumberAddr"]
    if not write_register(client, currentDO["impNumberAddr"], 0, function_code=fc):
        return
    logger.info("Запуск импульсов !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        # 2. Запись количества импульсов impNum1 в регистр currentDO["impNumberAddr"]
    if not write_register(client, currentDO["impNumberAddr"], numImp, function_code=fc):
        return
        # Ожидание обнуления регистра currentDO["impNumberAddr"]
    logger.info(f"Ожидание {numImp/freq+1}сек обнуления регистра impNumberAddr...")
    # time.sleep(numImp/freq+1)


def main():
  
    client = ModbusClient(
        port='COM3',          # Укажите ваш COM-порт
        baudrate=9600,        # Скорость обмена
        parity='N',           # Четность
        stopbits=1,           # Стоп-биты
        bytesize=8,           # Размер байта
        timeout=3,            # Таймаут (сек)
        retries=3             # Количество попыток
    )
    
    try:
        if not client.connect():
            raise ConnectionError("Не удалось подключиться к устройству")
        # Установка соединения
        logger.info("Подключение к устройству...")
        if not client.connect():
            logger.error("Не удалось подключиться к устройству")
            return
        
        logger.info("Соединение установлено успешно")
        preset(client, 500, 20)
        preset(client, 1000, 30)
        preset(client, 2000, 60)
        preset(client, 4000, 120)
        preset(client, 8000, 200)
        preset(client, 16000, 400)
        preset(client, 30000, 800)
        preset(client, 50000, 900)
        preset(client, 60000, 1000)
        logger.info("Все операции успешно завершены!")

    except Exception as e:
        logger.exception(f"Критическая ошибка: {e}")
    finally:
        client.close()
        logger.info("Соединение закрыто")

if __name__ == "__main__":
    main()