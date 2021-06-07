import xml.etree.ElementTree as et
import csv, sys, logging, os, time, io
import pandas as pd



path_to_xml = sys.argv[1]
path = ''.join((os.path.split(path_to_xml)[:1]))
file_extension = os.path.splitext(path_to_xml)[1]

    # Создаем папки вокруг XML-файла, если их нет
if not os.path.isdir(path + '/log'):
    os.mkdir(path + '/log')
if not os.path.isdir(path + '/arh'):
    os.mkdir(path + '/arh')
if not os.path.isdir(path + '/bad'):
    os.mkdir(path + '/bad')

    # Базовый кфг логгера + путь создания логов в папке log
logging.basicConfig(level = logging.DEBUG, filename=os.path.join(path + '/log', 'app.log'), filemode='w', format='%(name)s - %(levelname)s - %(message)s')

    # Функция обработки XML-файла и преобразования его в CSV-файл
def xml_to_csv(file_path):
    parser = et.XMLParser(encoding='utf-8')
    xtree = et.parse(file_path, parser=parser)
    xroot = xtree.getroot()

    # Создание csv-файла с именем XML-файла
    csv_name = os.path.splitext(os.path.basename(file_path))[0]
    csv_file = open(path + '/' + csv_name + '.csv', 'w') # Создание файла csv - в директории рядом с XML-файлом
    logging.info('Creating csv-file')

    # Начало обработки
    csvwriter = csv.writer(csv_file, delimiter = ';')

    # Получение имени физического файла XML
    reestrName =os.path.splitext(os.path.basename(file_path))[0]

    # Получение даты из путя, как указано в задании СлЧаст/ОбщСвСч/ИдФайл/ДатаФайл
    date = (xroot.find('СлЧаст').find('ОбщСвСч').find('ИдФайл').find('ДатаФайл')).text

    # Ряд с названием файла реестра и датой
    static_row = [reestrName, date]

    # Формирование рядов для выгрузки в csv_file
    for child in xroot.findall('ИнфЧаст'):
        main_row = []
        for child1 in child.findall('Плательщик'):
            row = []
            get_acc = (child1.find('ЛицСч')).text
            row.append(get_acc)
            get_full_name = (child1.find('ФИО')).text
            row.append(get_full_name)
            get_adress = (child1.find('Адрес')).text
            row.append(get_adress)
            get_period = (child1.find('Период')).text
            row.append(get_period)
            get_amount = (child1.find('Сумма')).text

            # Если сумма не записана, то None = |плати сколько хочешь в таблице|
            if get_amount is None:
                get_amount = 'Плати сколько хочешь'
            # Если нельзя конвертировать во float, то присваиваем значение None, для дальнейшей обрабокти в Pandas
            elif is_float(get_amount) == False:
                get_amount = None
            # 2 знака после запятой, если число float
            else:
                get_amount = "{:.2f}".format(float(get_amount))

            row.append(get_amount)
            main_row.append(static_row + row)

    # Создание DataFrame pandas
    df = pd.DataFrame(main_row)

    # Проверка на дубликаты и удаление дубликатов + отправка логов об удалении аккаунтов (ЛицСч + Период)
    if df.duplicated(subset=[2,5], keep=False).any() == True:
        duplicateCheck = df.duplicated(subset=[2,5], keep=False)
        logging.info('Удалены повторяющиеся строки(ЛицСч; Период): ' + str(df[duplicateCheck][2] +'; '+ df[duplicateCheck][5]))
        df = df.drop_duplicates(subset=[2,5], keep=False)

    #Если в строке нет ключевых элементтов (Ключевые элементы - ЛицСч и Период)
    if df[2].isna().any() == True:
        account_indexs = df[df[2].isna()].index.tolist()
        logging.info('Удалена строка(и)! В строке(ах) № ' + str(account_indexs) + ' отсутсвует ключевой элемент ЛицСч')
        df = df.dropna(subset=[2])
    if df[5].isna().any() == True:
        period_indexs = df[df[5].isna()].index.tolist()
        logging.info('Удалена строка(и)! В строке(ах) № ' + str(period_indexs) + ' отсутсвует ключевой элемент Период')
        df = df.dropna(subset=[5])


    # Проверка и удаление строк с неправильным форматом Периода и запись в логи
    df[5] = pd.to_datetime(df[5], format='%m%Y', errors='coerce')
    if df[5].isna().any() == True:
        incorrect_periods = df[df[5].isna()].index.tolist()
        logging.info('Удалены строки № '+ str(incorrect_periods) + ' с неверным периодом.')
        df = df.dropna(subset=[5])
    df[5] = df[5].dt.strftime('%m%Y')



    # Удаление неверных значений из поля СУММА
    if df[6].isna().any() == True:
        incorrect_amounts = df[df[6].isna()].index.tolist()
        logging.info('Удалены строки № ' + str(incorrect_amounts) + ' с неверным значением СУММЫ')
        df = df.dropna(subset=[6])


    df.to_csv(csv_file, index=False, header=False, sep=';', encoding='utf-8')
    csv_file.close()
    os.replace(path_to_xml, path + '\\arh\\' + reestrName + '.xml')

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

if file_extension == '.xml':
    # Открытие файла кодировки cp1251
    with open(path_to_xml, encoding='cp1251') as fh:
        data = fh.read()
    # Преобразование файла в utf-8, для дальнейшей корректной работы
    with open(path_to_xml, 'wb') as fh:
        fh.write(data.encode('utf-8'))
    xml_to_csv(path_to_xml)
else:
    logging.critical('ФАЙЛ НЕ XML-расширения, работа остановлена.')
    os.replace(path_to_xml, path + '\\bad\\' + os.path.splitext(os.path.basename(path_to_xml))[0] + file_extension)
    os.abort()
