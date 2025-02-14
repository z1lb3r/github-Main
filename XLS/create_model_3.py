import xlsxwriter

# Создаём книгу
workbook = xlsxwriter.Workbook('MiningFarmModel_NoExternalLinks.xlsx')

# Основные листы
ws_data    = workbook.add_worksheet('Исходные данные')
ws_rev5    = workbook.add_worksheet('Доходы (5 лет)')
ws_rev8    = workbook.add_worksheet('Доходы (8 лет)')
ws_opex    = workbook.add_worksheet('ОПЕКС')
ws_capex5  = workbook.add_worksheet('КАПЕКС (5 лет)')
ws_fin5    = workbook.add_worksheet('Финансирование (5 лет)')
ws_pl5     = workbook.add_worksheet('P&L (5 лет)')
ws_capex8  = workbook.add_worksheet('КАПЕКС (8 лет)')
ws_fin8    = workbook.add_worksheet('Финансирование (8 лет)')
ws_pl8     = workbook.add_worksheet('P&L (8 лет)')

###############################################################################
# Лист "Исходные данные"
ws_data.write_row(0, 0, ["Параметр", "Значение", "Описание/Формула"])

data = [
    # 1. Курс биткойна 94 000$
    ["BTC Price (USD)",         94000,                  ""],
    # 2. Курс доллара 100 руб
    ["USD Rate (RUB)",          100,                    ""],
    # 3. Годовой рост сложности (доходность падает на 20% каждый год)
    ["Mining Difficulty Growth (annual)", 0.20,         "Доходность падает на 20% каждый год"],
    # 4. Стоимость одного майнера 100 000 руб
    ["Cost per Miner (RUB)",    100000,                 ""],
    # 5. Доходность майнера в день (BTC)
    ["Daily Yield per Miner (BTC)", 0.000067,           ""],
    # 6. Стоимость установки ГПУ: 60 000 000 руб с НДС
    ["GPU Installation Cost (RUB)", 60000000,           "с НДС"],
    # 7. Количество установок (ГПУ): 5
    ["Number of GPU Installations", 5,                 ""],
    # 8. Количество контейнеров: 5
    ["Number of Containers",    5,                     ""],
    # 9. Майнеров в контейнере: 270
    ["Miners per Container",    270,                   ""],
    # 10. Общее число майнеров = Кол-во контейнеров * Майнеров в контейнере
    ["Total Number of Miners",  "=B8*B9",             "5*270 = 1350"],
    # 11. CAPEX: Первоначальные инвестиции = (GPU установки) + (майнеры)
    #    = (B7 * B6) + (B8 * B9 * B4) = (5*60,000,000) + (5*270*100,000) = 300M + 135M = 435M руб
    ["CAPEX: Initial Investment (RUB)", "=(B7*B6)+(B8*B9*B4)", "300M + 135M = 435M"],
    # 12. Период замены майнеров: каждые 3 года
    ["Miner Replacement Period (years)", 3,              ""],
    # 13. Стоимость электроэнергии 2.5 руб/кВт с НДС
    ["Electricity Cost (RUB/kWh)", 2.5,                    ""],
    # 14. Стоимость обслуживания и поддержки оборудования: 1 руб/кВт с НДС
    ["Service Cost (RUB/kWh)", 1,                          ""],
    # 15. Итого затраты на электроэнергию: 2.5 + 1 = 3.5 руб/кВт
    ["Total Electricity Cost (RUB/kWh)", "=B13+B14",         "2.5 + 1 = 3.5"],
    # 16. (Параметр электроэнергопотребления на майнер не указан, но можно задать, например, 3.5 кВт)
    ["Electricity Consumption per Miner (kW)", 3.5,          ""],
    # 17. Ставка налога: 15%
    ["Tax Rate",                0.15,                   ""],
    # 18. Сумма кредита = Первоначальные инвестиции, то есть =CAPEX (ячейка B11)
    ["Loan Amount (RUB)",       "=B11",                 "435M руб"],
    # 19. Ставка по кредиту: 24%
    ["Loan Interest Rate",      0.24,                   ""],
    # 20. Срок кредита (лет): 5
    ["Loan Term (years)",       5,                      ""],
    # 21. Доход от продажи тепла (если применимо)
    ["Heat Sale Revenue (RUB/year)", 24805432,           "Доход от продажи тепла"]
]

for i, row in enumerate(data, start=1):
    ws_data.write_row(i, 0, row)


###############################################################################
# Лист "Доходы (5 лет)"
headers = ["Год", "Фактор снижения", "Daily Yield (BTC)", "Daily Yield (USD)",
           "Daily Yield (RUB)", "Annual Revenue per Miner (RUB)", "Total Annual Revenue (RUB)"]
for col, header in enumerate(headers):
    ws_rev5.write(0, col, header)
for year in range(1, 6):
    r = year
    ws_rev5.write(r, 0, year)
    ws_rev5.write_formula(r, 1, f"=POWER(1-'Исходные данные'!$B$3, A{r+1}-1)")
    ws_rev5.write_formula(r, 2, f"='Исходные данные'!$B$5 * B{r+1}")
    ws_rev5.write_formula(r, 3, f"=C{r+1} * 'Исходные данные'!$B$2")
    ws_rev5.write_formula(r, 4, f"=D{r+1} * 'Исходные данные'!$B$2")
    ws_rev5.write_formula(r, 5, f"=E{r+1} * 365")
    ws_rev5.write_formula(r, 6, f"=F{r+1} * 'Исходные данные'!$B$10")

###############################################################################
# Лист "Доходы (8 лет)"
headers = ["Год", "Фактор снижения", "Daily Yield (BTC)", "Daily Yield (USD)",
           "Daily Yield (RUB)", "Annual Revenue per Miner (RUB)", "Total Annual Revenue (RUB)"]
for col, header in enumerate(headers):
    ws_rev8.write(0, col, header)
for year in range(1, 9):
    r = year
    ws_rev8.write(r, 0, year)
    ws_rev8.write_formula(r, 1, f"=POWER(1-'Исходные данные'!$B$3, A{r+1}-1)")
    ws_rev8.write_formula(r, 2, f"='Исходные данные'!$B$5 * B{r+1}")
    ws_rev8.write_formula(r, 3, f"=C{r+1} * 'Исходные данные'!$B$2")
    ws_rev8.write_formula(r, 4, f"=D{r+1} * 'Исходные данные'!$B$2")
    ws_rev8.write_formula(r, 5, f"=E{r+1} * 365")
    ws_rev8.write_formula(r, 6, f"=F{r+1} * 'Исходные данные'!$B$10")

###############################################################################
# Лист "ОПЕКС"
ws_opex.write(0, 0, "Показатель")
ws_opex.write(0, 1, "Значение")
ws_opex.write(1, 0, "Daily Consumption per Miner (kWh)")
ws_opex.write_formula(1, 1, "='Исходные данные'!$B$17 * 24")
ws_opex.write(2, 0, "Annual Consumption per Miner (kWh)")
ws_opex.write_formula(2, 1, "=B2 * 365")
ws_opex.write(3, 0, "Annual Electricity Cost per Miner (RUB)")
ws_opex.write_formula(3, 1, "=B2 * 'Исходные данные'!$B$16")
ws_opex.write(4, 0, "Total Annual Electricity Cost (RUB)")
ws_opex.write_formula(4, 1, "='Исходные данные'!$B$10 * B3")

###############################################################################
# Лист "КАПЕКС (5 лет)"
ws_capex5.write(0, 0, "Показатель")
ws_capex5.write(0, 1, "Значение (RUB)")
ws_capex5.write(1, 0, "Initial Investment")
ws_capex5.write_formula(1, 1, "='Исходные данные'!$B$12")
ws_capex5.write(2, 0, "Miner Replacement Cost (Year 3)")
ws_capex5.write_formula(2, 1, "=135000000")

###############################################################################
# Лист "Финансирование (5 лет)"
ws_fin5.write_row(0, 0, ["Год", "Запланированное погашение", "Процент", "Общий платёж", "Доп. погашение (EBT)", "Остаток тела"])
for year in range(1, 6):
    r = year
    ws_fin5.write(r, 0, year)
    ws_fin5.write_formula(r, 1, "='Исходные данные'!$B$12/5")
    if year == 1:
        ws_fin5.write_formula(r, 2, "='Исходные данные'!$B$12 * 'Исходные данные'!$B$20")
        ws_fin5.write_formula(r, 4, "='P&L (5 лет)'!G2")
        ws_fin5.write_formula(r, 3, "=B" + str(r+1) + " + C" + str(r+1))
        ws_fin5.write_formula(r, 5, "='Исходные данные'!$B$12 - B" + str(r+1) + " - D" + str(r+1))
    else:
        ws_fin5.write_formula(r, 2, "=F" + str(r) + " * 'Исходные данные'!$B$20")
        ws_fin5.write_formula(r, 4, "='P&L (5 лет)'!G" + str(r+1))
        ws_fin5.write_formula(r, 3, "=B" + str(r+1) + " + C" + str(r+1))
        ws_fin5.write_formula(r, 5, "=F" + str(r) + " - B" + str(r+1) + " - D" + str(r+1))

###############################################################################
# Лист "P&L (5 лет)"
ws_pl5.write_row(0, 0, ["Год", "Revenue (RUB)", "OPEX (RUB)", "Depreciation (RUB)",
                         "EBIT (RUB)", "Interest (RUB)", "EBT (RUB)", "Tax (RUB)", "Net Profit (RUB)"])
dep = 45000000
for year in range(1, 6):
    r = year
    ws_pl5.write(r, 0, year)
    ws_pl5.write_formula(r, 1, "= 'Доходы (5 лет)'!G" + str(r+1) + " + 'Исходные данные'!$B$21")
    ws_pl5.write_formula(r, 2, "='ОПЕКС'!B5")
    ws_pl5.write(r, 3, dep)
    ws_pl5.write_formula(r, 4, "=B" + str(r+1) + " - C" + str(r+1) + " - D" + str(r+1))
    if year == 1:
        ws_pl5.write_formula(r, 5, "='Исходные данные'!$B$12 * 'Исходные данные'!$B$20")
    else:
        ws_pl5.write_formula(r, 5, "= 'Финансирование (5 лет)'!F" + str(r) + " * 'Исходные данные'!$B$20")
    ws_pl5.write_formula(r, 6, "=E" + str(r+1) + " - F" + str(r+1))
    ws_pl5.write_formula(r, 7, "=G" + str(r+1) + " * 'Исходные данные'!$B$18")
    ws_pl5.write_formula(r, 8, "=G" + str(r+1) + " - H" + str(r+1))

###############################################################################
# Лист "КАПЕКС (8 лет)"
ws_capex8.write(0, 0, "Показатель")
ws_capex8.write(0, 1, "Значение (RUB)")
ws_capex8.write(1, 0, "Initial Investment")
ws_capex8.write_formula(1, 1, "='Исходные данные'!$B$12")
ws_capex8.write(2, 0, "Miner Replacement Cost (Year 3)")
ws_capex8.write_formula(2, 1, "=135000000")
ws_capex8.write(3, 0, "Miner Replacement Cost (Year 6)")
ws_capex8.write_formula(3, 1, "=135000000")

###############################################################################
# Лист "Финансирование (8 лет)"
ws_fin8.write_row(0, 0, ["Год", "Запланированное погашение", "Процент", "Общий платёж", "Доп. погашение (EBT)", "Остаток тела"])
for year in range(1, 9):
    r = year
    ws_fin8.write(r, 0, year)
    ws_fin8.write_formula(r, 1, "='Исходные данные'!$B$12/8")
    if year == 1:
        ws_fin8.write_formula(r, 2, "='Исходные данные'!$B$12 * 'Исходные данные'!$B$20")
        ws_fin8.write_formula(r, 4, "='P&L (8 лет)'!G2")
        ws_fin8.write_formula(r, 3, "=B" + str(r+1) + " + C" + str(r+1))
        ws_fin8.write_formula(r, 5, "='Исходные данные'!$B$12 - B" + str(r+1) + " - D" + str(r+1))
    else:
        ws_fin8.write_formula(r, 2, "=F" + str(r) + " * 'Исходные данные'!$B$20")
        ws_fin8.write_formula(r, 4, "='P&L (8 лет)'!G" + str(r+1))
        ws_fin8.write_formula(r, 3, "=B" + str(r+1) + " + C" + str(r+1))
        ws_fin8.write_formula(r, 5, "=F" + str(r) + " - B" + str(r+1) + " - D" + str(r+1))

###############################################################################
# Лист "P&L (8 лет)"
ws_pl8.write_row(0, 0, ["Год", "Revenue (RUB)", "OPEX (RUB)", "Depreciation (RUB)",
                         "EBIT (RUB)", "Interest (RUB)", "EBT (RUB)", "Tax (RUB)", "Net Profit (RUB)"])
for year in range(1, 9):
    r = year
    ws_pl8.write(r, 0, year)
    ws_pl8.write_formula(r, 1, "= 'Доходы (8 лет)'!G" + str(r+1) + " + 'Исходные данные'!$B$21")
    ws_pl8.write_formula(r, 2, "='ОПЕКС'!B5")
    ws_pl8.write(r, 3, dep)
    ws_pl8.write_formula(r, 4, "=B" + str(r+1) + " - C" + str(r+1) + " - D" + str(r+1))
    if year == 1:
        ws_pl8.write_formula(r, 5, "='Исходные данные'!$B$12 * 'Исходные данные'!$B$20")
    else:
        ws_pl8.write_formula(r, 5, "= 'Финансирование (8 лет)'!F" + str(r) + " * 'Исходные данные'!$B$20")
    ws_pl8.write_formula(r, 6, "=E" + str(r+1) + " - F" + str(r+1))
    ws_pl8.write_formula(r, 7, "=G" + str(r+1) + " * 'Исходные данные'!$B$18")
    ws_pl8.write_formula(r, 8, "=G" + str(r+1) + " - H" + str(r+1))

###############################################################################
# Новые листы для кредита на замену майнеров

# 1. Лист "Финансирование замены (5 лет)"
ws_fin_replace5 = workbook.add_worksheet('Финанс. замены (5 л)')
ws_fin_replace5.write_row(0, 0, ["Год", "Запланированное погашение", "Процент", "Общий платёж", "Остаток тела"])
# Для модели на 5 лет кредит на замену майнеров (135M) берётся в 3-м году и имеет срок погашения 5 лет
for year in range(1, 6):
    row_idx = year
    ws_fin_replace5.write(row_idx, 0, year)
    if year < 3:
        ws_fin_replace5.write(row_idx, 1, 0)
        ws_fin_replace5.write(row_idx, 2, 0)
        ws_fin_replace5.write(row_idx, 3, 0)
        ws_fin_replace5.write(row_idx, 4, 0)
    elif year == 3:
        ws_fin_replace5.write_formula(row_idx, 1, "=135000000/5")
        ws_fin_replace5.write_formula(row_idx, 2, "=135000000 * 'Исходные данные'!$B$20")
        ws_fin_replace5.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace5.write_formula(row_idx, 4, "=135000000 - B" + str(row_idx+1))
    else:
        ws_fin_replace5.write_formula(row_idx, 1, "=135000000/5")
        ws_fin_replace5.write_formula(row_idx, 2, "=E" + str(row_idx) + " * 'Исходные данные'!$B$20")
        ws_fin_replace5.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace5.write_formula(row_idx, 4, "=E" + str(row_idx) + " - B" + str(row_idx+1))

# 2. Лист "Фин. замены (8 л, 3 г)"
ws_fin_replace8_3 = workbook.add_worksheet('Фин. замены (8 л, 3 г)')
ws_fin_replace8_3.write_row(0, 0, ["Год", "Запланированное погашение", "Процент", "Общий платёж", "Остаток тела"])
# Здесь кредит на замену (135M) берётся в 3-м году и погашается дифференцировано в течение 8 лет
for year in range(1, 9):
    row_idx = year
    ws_fin_replace8_3.write(row_idx, 0, year)
    if year < 3:
        ws_fin_replace8_3.write(row_idx, 1, 0)
        ws_fin_replace8_3.write(row_idx, 2, 0)
        ws_fin_replace8_3.write(row_idx, 3, 0)
        ws_fin_replace8_3.write(row_idx, 4, 0)
    elif year == 3:
        ws_fin_replace8_3.write_formula(row_idx, 1, "=135000000/8")
        ws_fin_replace8_3.write_formula(row_idx, 2, "=135000000 * 'Исходные данные'!$B$20")
        ws_fin_replace8_3.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace8_3.write_formula(row_idx, 4, "=135000000 - B" + str(row_idx+1))
    else:
        ws_fin_replace8_3.write_formula(row_idx, 1, "=135000000/8")
        ws_fin_replace8_3.write_formula(row_idx, 2, "=E" + str(row_idx) + " * 'Исходные данные'!$B$20")
        ws_fin_replace8_3.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace8_3.write_formula(row_idx, 4, "=E" + str(row_idx) + " - B" + str(row_idx+1))

# 3. Лист "Фин. замены (8 л, 6 г)"
ws_fin_replace8_6 = workbook.add_worksheet('Фин. замены (8 л, 6 г)')
ws_fin_replace8_6.write_row(0, 0, ["Год", "Запланированное погашение", "Процент", "Общий платёж", "Остаток тела"])
# Здесь кредит на замену (135M) берётся в 6‑м году и погашается дифференцировано в течение 8 лет
for year in range(1, 9):
    row_idx = year
    ws_fin_replace8_6.write(row_idx, 0, year)
    if year < 6:
        ws_fin_replace8_6.write(row_idx, 1, 0)
        ws_fin_replace8_6.write(row_idx, 2, 0)
        ws_fin_replace8_6.write(row_idx, 3, 0)
        ws_fin_replace8_6.write(row_idx, 4, 0)
    elif year == 6:
        ws_fin_replace8_6.write_formula(row_idx, 1, "=135000000/8")
        ws_fin_replace8_6.write_formula(row_idx, 2, "=135000000 * 'Исходные данные'!$B$20")
        ws_fin_replace8_6.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace8_6.write_formula(row_idx, 4, "=135000000 - B" + str(row_idx+1))
    else:
        ws_fin_replace8_6.write_formula(row_idx, 1, "=135000000/8")
        ws_fin_replace8_6.write_formula(row_idx, 2, "=E" + str(row_idx) + " * 'Исходные данные'!$B$20")
        ws_fin_replace8_6.write_formula(row_idx, 3, "=B" + str(row_idx+1) + " + C" + str(row_idx+1))
        ws_fin_replace8_6.write_formula(row_idx, 4, "=E" + str(row_idx) + " - B" + str(row_idx+1))

###############################################################################
workbook.close()
