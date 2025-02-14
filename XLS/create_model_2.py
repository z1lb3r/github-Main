import xlsxwriter

# Создаём книгу
workbook = xlsxwriter.Workbook('MiningFarmModel_NoExternalLinks.xlsx')

# Создаём все листы сразу – чтобы все ссылки были внутренними
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
    ["BTC Price (USD)",         94000,                  ""],
    ["USD Rate (RUB)",          100,                    ""],
    ["Mining Difficulty Growth (annual)", 0.20,         "Доходность падает на 20% каждый год"],
    ["Cost per Miner (RUB)",    100000,                 ""],
    ["Daily Yield per Miner (BTC)", 0.000067,           ""],
    ["GPU Installation Cost (RUB)", 60000000,           "с НДС"],
    ["Number of GPU Installations", 5,                 ""],
    ["Number of Containers",    5,                     ""],
    ["Miners per Container",    270,                   ""],
    ["Total Number of Miners",  "=B9*B10",             "5*270=1350"],
    ["CAPEX: Initial Investment (RUB)", "=(B8*B7)+(B9*B10*B5)", "300M+135M=435M"],
    ["Miner Replacement Period (years)", 3,              ""],
    ["Electricity Cost (RUB/kWh)", 2.5,                    ""],
    ["Service Cost (RUB/kWh)", 1,                          ""],
    ["Total Electricity Cost (RUB/kWh)", "=B14+B15",         "2.5+1=3.5"],
    ["Electricity Consumption per Miner (kW)", 3.5,          ""],
    ["Tax Rate",                0.15,                   ""],
    ["Loan Amount (RUB)",       "=B12",                 "435M руб"],
    ["Loan Interest Rate",      0.24,                   ""],
    ["Loan Term (years)",       5,                      ""],
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
    r = year  # строки начинаются с 1 (заголовок в строке 0)
    ws_rev5.write(r, 0, year)
    ws_rev5.write_formula(r, 1, f"=POWER(1-'Исходные данные'!$B$4, A{r+1}-1)")
    ws_rev5.write_formula(r, 2, f"='Исходные данные'!$B$6 * B{r+1}")
    ws_rev5.write_formula(r, 3, f"=C{r+1} * 'Исходные данные'!$B$2")
    ws_rev5.write_formula(r, 4, f"=D{r+1} * 'Исходные данные'!$B$3")
    ws_rev5.write_formula(r, 5, f"=E{r+1} * 365")
    ws_rev5.write_formula(r, 6, f"=F{r+1} * 'Исходные данные'!$B$11")

###############################################################################
# Лист "Доходы (8 лет)"
headers = ["Год", "Фактор снижения", "Daily Yield (BTC)", "Daily Yield (USD)",
           "Daily Yield (RUB)", "Annual Revenue per Miner (RUB)", "Total Annual Revenue (RUB)"]
for col, header in enumerate(headers):
    ws_rev8.write(0, col, header)
for year in range(1, 9):
    r = year
    ws_rev8.write(r, 0, year)
    ws_rev8.write_formula(r, 1, f"=POWER(1-'Исходные данные'!$B$4, A{r+1}-1)")
    ws_rev8.write_formula(r, 2, f"='Исходные данные'!$B$6 * B{r+1}")
    ws_rev8.write_formula(r, 3, f"=C{r+1} * 'Исходные данные'!$B$2")
    ws_rev8.write_formula(r, 4, f"=D{r+1} * 'Исходные данные'!$B$3")
    ws_rev8.write_formula(r, 5, f"=E{r+1} * 365")
    ws_rev8.write_formula(r, 6, f"=F{r+1} * 'Исходные данные'!$B$11")

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
ws_opex.write_formula(4, 1, "='Исходные данные'!$B$11 * B3")

###############################################################################
# Лист "КАПЕКС (5 лет)"
ws_capex5.write(0, 0, "Показатель")
ws_capex5.write(0, 1, "Значение (RUB)")
ws_capex5.write(1, 0, "Initial Investment")
ws_capex5.write_formula(1, 1, "='Исходные данные'!$B$12")
ws_capex5.write(2, 0, "Miner Replacement Cost (Year 3)")
ws_capex5.write_formula(2, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")

###############################################################################
# Лист "Финансирование (5 лет)"
# Здесь рассчитываем по схеме:
# • S = 435M/5 (запланированное погашение тела)
# • I = (остаток на начало года)*0.24
# • X = дополнительное погашение, равное EBT (из "P&L (5 лет)")
# • Остаток = (начальное тело) - S - X
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
# Здесь рассчитываем EBIT, Interest, EBT, Tax и Net Profit.
ws_pl5.write_row(0, 0, ["Год", "Revenue (RUB)", "OPEX (RUB)", "Depreciation (RUB)",
                         "EBIT (RUB)", "Interest (RUB)", "EBT (RUB)", "Tax (RUB)", "Net Profit (RUB)"])
dep = 45000000
for year in range(1, 6):
    r = year
    ws_pl5.write(r, 0, year)
    ws_pl5.write_formula(r, 1, "= 'Доходы (5 лет)'!G" + str(r+1) + " + 'Исходные данные'!$B$22")
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
ws_capex8.write_formula(2, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")
ws_capex8.write(3, 0, "Miner Replacement Cost (Year 6)")
ws_capex8.write_formula(3, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")

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
    ws_pl8.write_formula(r, 1, "= 'Доходы (8 лет)'!G" + str(r+1) + " + 'Исходные данные'!$B$22")
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
workbook.close()
