import xlsxwriter

# Создаем новый Excel-файл
workbook = xlsxwriter.Workbook('MiningFarmModel.xlsx')

##########################################
# Лист "Исходные данные"
ws_data = workbook.add_worksheet('Исходные данные')
# Заголовки
ws_data.write(0, 0, "Параметр")
ws_data.write(0, 1, "Значение")
ws_data.write(0, 2, "Описание/Формула")

# Заполняем исходные данные (ячейки в Excel начинаются с 1, поэтому row=1 -> Excel row 2)
ws_data.write(1, 0, "Курс биткойна (USD)")
ws_data.write(1, 1, 94000)

ws_data.write(2, 0, "Курс доллара (RUB)")
ws_data.write(2, 1, 100)

ws_data.write(3, 0, "Стоимость одного майнера (RUB)")
ws_data.write(3, 1, 100000)

ws_data.write(4, 0, "Доходность майнера в день (BTC)")
ws_data.write(4, 1, 0.000067)

ws_data.write(5, 0, "Доходность майнера в день (USD)")
# Формула: =B5*B2, где B5 — доходность в BTC, B2 — курс биткойна
ws_data.write_formula(5, 1, '=B5*B2')

ws_data.write(6, 0, "Доходность майнера в день (RUB)")
# Формула: =B6*B3, где B6 — доходность в USD, B3 — курс доллара
ws_data.write_formula(6, 1, '=B6*B3')

ws_data.write(7, 0, "Количество контейнеров")
ws_data.write(7, 1, 5)

ws_data.write(8, 0, "Количество майнеров на контейнер")
ws_data.write(8, 1, 270)

ws_data.write(9, 0, "Общее число майнеров")
# Формула: =B8*B9 (5 контейнеров * 270 майнеров)
ws_data.write_formula(9, 1, '=B8*B9')

ws_data.write(10, 0, "Стоимость установки ГПУ (RUB)")
ws_data.write(10, 1, 60000000)

ws_data.write(11, 0, "Количество установок (ГПУ)")
ws_data.write(11, 1, 5)

ws_data.write(12, 0, "КАПЕКС: Первоначальные инвестиции (RUB)")
ws_data.write(12, 1, 550000000)

ws_data.write(13, 0, "Срок замены майнеров (лет)")
ws_data.write(13, 1, 3)

ws_data.write(14, 0, "Стоимость электроэнергии (RUB/кВт·ч с НДС)")
ws_data.write(14, 1, 2.5)

ws_data.write(15, 0, "Стоимость обслуживания (RUB/кВт·ч с НДС)")
ws_data.write(15, 1, 1)

ws_data.write(16, 0, "Общая стоимость электроэнергии с обслуживанием (RUB/кВт·ч)")
# Формула: =B15+B16 (2.5 + 1)
ws_data.write_formula(16, 1, '=B15+B16')

ws_data.write(17, 0, "Потребление электроэнергии (кВт) одним майнером")
ws_data.write(17, 1, 3.5)

ws_data.write(18, 0, "Налоговая ставка")
ws_data.write(18, 1, 0.15)

ws_data.write(19, 0, "Кредит: Сумма (RUB)")
ws_data.write(19, 1, 550000000)

ws_data.write(20, 0, "Кредит: Ставка (годовая)")
ws_data.write(20, 1, 0.24)

ws_data.write(21, 0, "Кредит: Срок (лет)")
ws_data.write(21, 1, 5)

##########################################
# Лист "Доходы"
ws_rev = workbook.add_worksheet('Доходы')
ws_rev.write(0, 0, "Показатель")
ws_rev.write(0, 1, "Значение")
ws_rev.write(0, 2, "Описание/Формула")

ws_rev.write(1, 0, "Доходность майнера в день (BTC)")
ws_rev.write_formula(1, 1, "='Исходные данные'!B5")

ws_rev.write(2, 0, "Доходность майнера в день (USD)")
ws_rev.write_formula(2, 1, "='Исходные данные'!B6")

ws_rev.write(3, 0, "Доходность майнера в день (RUB)")
ws_rev.write_formula(3, 1, "='Исходные данные'!B7")

ws_rev.write(4, 0, "Годовая выручка одного майнера (RUB)")
ws_rev.write_formula(4, 1, "='Исходные данные'!B7*365")

ws_rev.write(5, 0, "Общая годовая выручка (RUB)")
# Общая выручка = (Общее число майнеров) * (годовая выручка одного майнера)
ws_rev.write_formula(5, 1, "='Исходные данные'!B10*B5")

##########################################
# Лист "ОПЕКС"
ws_opex = workbook.add_worksheet('ОПЕКС')
ws_opex.write(0, 0, "Показатель")
ws_opex.write(0, 1, "Значение")
ws_opex.write(0, 2, "Описание/Формула")

ws_opex.write(1, 0, "Дневное потребление (кВт·ч) одного майнера")
# Потребление одного майнера (кВт) * 24 часа
ws_opex.write_formula(1, 1, "='Исходные данные'!B18*24")

ws_opex.write(2, 0, "Годовое потребление одного майнера (кВт·ч)")
ws_opex.write_formula(2, 1, "=B2*365")

ws_opex.write(3, 0, "Стоимость электроэнергии с обслуживанием (RUB/кВт·ч)")
# Ссылка на общую стоимость (2.5+1)
ws_opex.write_formula(3, 1, "='Исходные данные'!B17")  # Если "Общая стоимость" находится в ячейке B17

ws_opex.write(4, 0, "Годовая стоимость электроэнергии для одного майнера (RUB)")
# Формула: (Годовое потребление) * (стоимость 1 кВт·ч)
ws_opex.write_formula(4, 1, "=B3*B4")

ws_opex.write(5, 0, "Общие годовые операционные расходы (электроэнергия) (RUB)")
ws_opex.write_formula(5, 1, "='Исходные данные'!B10*B5")

##########################################
# Лист "КАПЕКС"
ws_capex = workbook.add_worksheet('КАПЕКС')
ws_capex.write(0, 0, "Показатель")
ws_capex.write(0, 1, "Значение")
ws_capex.write(0, 2, "Описание/Формула")

ws_capex.write(1, 0, "Первоначальные инвестиции (RUB)")
ws_capex.write_formula(1, 1, "='Исходные данные'!B13")

ws_capex.write(2, 0, "Замена майнеров через 3 года (RUB)")
# Замена майнеров = (Общее число майнеров) * (Стоимость одного майнера)
ws_capex.write_formula(2, 1, "='Исходные данные'!B10*'Исходные данные'!B4")

ws_capex.write(3, 0, "Амортизация майнеров (лет)")
ws_capex.write(3, 1, 3)
ws_capex.write(3, 2, "Срок замены майнеров")

##########################################
# Лист "Финансирование"
ws_fin = workbook.add_worksheet('Финансирование')
ws_fin.write(0, 0, "Показатель")
ws_fin.write(0, 1, "Значение")
ws_fin.write(0, 2, "Описание/Формула")

ws_fin.write(1, 0, "Сумма кредита (RUB)")
ws_fin.write_formula(1, 1, "='Исходные данные'!B20")

ws_fin.write(2, 0, "Ставка кредита (годовая)")
ws_fin.write_formula(2, 1, "='Исходные данные'!B21")

ws_fin.write(3, 0, "Срок кредита (лет)")
ws_fin.write_formula(3, 1, "='Исходные данные'!B22")

ws_fin.write(4, 0, "Аннуитетный платеж (RUB)")
# Функция PMT: =PMT(ставка, срок, -сумма_кредита)
ws_fin.write_formula(4, 1, "=PMT(B3,B4,-B2)")

##########################################
# Лист "P&L" (Отчет о прибылях и убытках)
ws_pl = workbook.add_worksheet('P&L')
# Заголовки
headers = ["Показатель", "Год 1", "Год 2", "Год 3", "Год 4", "Год 5"]
for col, header in enumerate(headers):
    ws_pl.write(0, col, header)

ws_pl.write(1, 0, "Выручка (RUB)")
for col in range(1, 6):
    ws_pl.write_formula(1, col, "='Доходы'!B6")

ws_pl.write(2, 0, "ОПЕКС (электроэнергия) (RUB)")
for col in range(1, 6):
    ws_pl.write_formula(2, col, "='ОПЕКС'!B6")

ws_pl.write(3, 0, "Амортизация (майнеры) (RUB)")
for col in range(1, 6):
    ws_pl.write_formula(3, col, "='КАПЕКС'!B3/3")

ws_pl.write(4, 0, "EBIT (RUB)")
ws_pl.write_formula(4, 1, "=B2-B3-B4")
ws_pl.write_formula(4, 2, "=C2-C3-C4")
ws_pl.write_formula(4, 3, "=D2-D3-D4")
ws_pl.write_formula(4, 4, "=E2-E3-E4")
ws_pl.write_formula(4, 5, "=F2-F3-F4")

ws_pl.write(5, 0, "Процентные расходы (RUB)")
# Пример упрощенного расчета процентов (аннуитет платеж * ставка)
for col in range(1, 6):
    ws_pl.write_formula(5, col, "='Финансирование'!B4*'Финансирование'!B3")

ws_pl.write(6, 0, "EBT (RUB)")
ws_pl.write_formula(6, 1, "=B4-B5")
ws_pl.write_formula(6, 2, "=C4-C5")
ws_pl.write_formula(6, 3, "=D4-D5")
ws_pl.write_formula(6, 4, "=E4-E5")
ws_pl.write_formula(6, 5, "=F4-F5")

ws_pl.write(7, 0, "Налог (15%) (RUB)")
for col in range(1, 6):
    ws_pl.write_formula(7, col, "=B6*'Исходные данные'!B19")

ws_pl.write(8, 0, "Чистая прибыль (RUB)")
ws_pl.write_formula(8, 1, "=B6-B7")
ws_pl.write_formula(8, 2, "=C6-C7")
ws_pl.write_formula(8, 3, "=D6-D7")
ws_pl.write_formula(8, 4, "=E6-E7")
ws_pl.write_formula(8, 5, "=F6-F7")

##########################################
# Лист "Cash Flow" (Денежный поток)
ws_cf = workbook.add_worksheet('Cash Flow')
cf_headers = ["Показатель", "Год 1", "Год 2", "Год 3", "Год 4", "Год 5"]
for col, header in enumerate(cf_headers):
    ws_cf.write(0, col, header)

ws_cf.write(1, 0, "Начальный баланс (RUB)")
for col in range(1, 6):
    ws_cf.write(1, col, 0)

ws_cf.write(2, 0, "Операционный денежный поток (RUB)")
# Операционный поток = чистая прибыль + амортизация
ws_cf.write_formula(2, 1, "='P&L'!B9 + 'КАПЕКС'!B3/3")
for col in range(2, 6):
    # Для простоты здесь копируем одно и то же значение
    ws_cf.write_formula(2, col, "='P&L'!B9 + 'КАПЕКС'!B3/3")

ws_cf.write(3, 0, "Инвестиционный поток (RUB)")
# В год 1 – первоначальные инвестиции; в год 3 – замена майнеров
ws_cf.write_formula(3, 1, "=-'Исходные данные'!B13")
ws_cf.write_formula(3, 3, "=-'КАПЕКС'!B3")
for col in [2,4,5]:
    ws_cf.write(3, col, 0)

ws_cf.write(4, 0, "Финансовый поток (RUB)")
# Отражаем аннуитетный платеж как отток
for col in range(1, 6):
    ws_cf.write_formula(4, col, "=-'Финансирование'!B4")

ws_cf.write(5, 0, "Свободный денежный поток (RUB)")
for col in range(1, 6):
    # Свободный поток = операционный + инвестиционный + финансовый поток
    col_letter = chr(65 + col)  # A=65, B=66, etc.
    ws_cf.write_formula(5, col, "=%s2+%s3+%s4" % (col_letter, col_letter, col_letter))

# Закрываем книгу (сохраняем файл)
workbook.close()
