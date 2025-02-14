import xlsxwriter

workbook = xlsxwriter.Workbook('MiningFarmModel_DiffLoan_With8Years_Final.xlsx')

###############################################################################
# Лист "Исходные данные"
ws_data = workbook.add_worksheet('Исходные данные')
ws_data.write(0, 0, "Параметр")
ws_data.write(0, 1, "Значение")
ws_data.write(0, 2, "Описание/Формула")
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
    for j, value in enumerate(row):
        ws_data.write(i, j, value)

###############################################################################
# Лист "Доходы (5 лет)"
ws_rev5 = workbook.add_worksheet('Доходы (5 лет)')
headers = ["Год", "Фактор снижения", "Daily Yield (BTC)", "Daily Yield (USD)",
           "Daily Yield (RUB)", "Annual Revenue per Miner (RUB)", "Total Annual Revenue (RUB)"]
for col, header in enumerate(headers):
    ws_rev5.write(0, col, header)
for year in range(1, 6):
    r = year
    ws_rev5.write(r, 0, year)
    ws_rev5.write_formula(r, 1, f"=POWER(1-'Исходные данные'!$B$4, A{r+1}-1)")
    ws_rev5.write_formula(r, 2, f"='Исходные данные'!$B$6 * B{r+1}")
    ws_rev5.write_formula(r, 3, f"=C{r+1} * 'Исходные данные'!$B$2")
    ws_rev5.write_formula(r, 4, f"=D{r+1} * 'Исходные данные'!$B$3")
    ws_rev5.write_formula(r, 5, f"=E{r+1} * 365")
    ws_rev5.write_formula(r, 6, f"=F{r+1} * 'Исходные данные'!$B$11")

###############################################################################
# Лист "Доходы (8 лет)"
ws_rev8 = workbook.add_worksheet('Доходы (8 лет)')
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
ws_opex = workbook.add_worksheet('ОПЕКС')
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
ws_capex5 = workbook.add_worksheet('КАПЕКС (5 лет)')
ws_capex5.write(0, 0, "Показатель")
ws_capex5.write(0, 1, "Значение (RUB)")
ws_capex5.write(1, 0, "Initial Investment")
ws_capex5.write_formula(1, 1, "='Исходные данные'!$B$12")
ws_capex5.write(2, 0, "Miner Replacement Cost (Year 3)")
ws_capex5.write_formula(2, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")

###############################################################################
# Лист "Финансирование (5 лет)"
ws_fin5 = workbook.add_worksheet('Финансирование (5 лет)')
headers_fin5 = ["Год",
                "Loan1 Total Payment (RUB)",
                "Loan2 Total Payment (RUB)",
                "Суммарный Payment (RUB)"]
for col, header in enumerate(headers_fin5):
    ws_fin5.write(0, col, header)
for year in range(1, 6):
    r = year
    ws_fin5.write(r, 0, year)
    # Loan 1: Principal = -('Исходные данные'!$B$12/5); Interest = -((435M - (year-1)*(435M/5))*0.24)
    ws_fin5.write_formula(r, 1,
        f"=IF(A{r+1}>=1, -(( 'Исходные данные'!$B$12/5 ) + ( 'Исходные данные'!$B$12 - (A{r+1}-1)*( 'Исходные данные'!$B$12/5 ))*'Исходные данные'!$B$20), 0)")
    # Loan 2: активен, если год>=3 и год<=7; Principal = -((135M)/5); Interest = -((135M - (year-3)*(135M/5))*0.24)
    ws_fin5.write_formula(r, 2,
        f"=IF(AND(A{r+1}>=3, A{r+1}<=7), -(((135000000)/5) + ((135000000 - (A{r+1}-3)*((135000000)/5))*'Исходные данные'!$B$20)), 0)")
    ws_fin5.write_formula(r, 3, f"=B{r+1} + C{r+1}")

###############################################################################
# Лист "P&L (5 лет)"
ws_pl5 = workbook.add_worksheet('P&L (5 лет)')
pl_headers5 = ["Год", "Revenue (RUB)", "OPEX (RUB)", "Depreciation (RUB)",
               "EBIT (RUB)", "Interest (RUB)", "EBT (RUB)", "Tax (RUB)",
               "Net Profit (RUB)"]
for col, header in enumerate(pl_headers5):
    ws_pl5.write(0, col, header)
dep = 45000000
for year in range(1, 6):
    r = year
    ws_pl5.write(r, 0, year)
    ws_pl5.write_formula(r, 1, f"= 'Доходы (5 лет)'!G{r+1} + 'Исходные данные'!$B$22")
    ws_pl5.write_formula(r, 2, "='ОПЕКС'!B5")
    ws_pl5.write(r, 3, dep)
    ws_pl5.write_formula(r, 4, f"=B{r+1} - C{r+1} - D{r+1}")
    ws_pl5.write_formula(r, 5, f"='Финансирование (5 лет)'!$D${r+1}")
    ws_pl5.write_formula(r, 6, f"=E{r+1} + F{r+1}")
    ws_pl5.write_formula(r, 7, f"=G{r+1} * 'Исходные данные'!$B$18")
    ws_pl5.write_formula(r, 8, f"=G{r+1} - H{r+1}")

###############################################################################
# Лист "КАПЕКС (8 лет)" – для 8-летнего варианта
ws_capex8 = workbook.add_worksheet('КАПЕКС (8 лет)')
ws_capex8.write(0, 0, "Показатель")
ws_capex8.write(0, 1, "Значение (RUB)")
ws_capex8.write(1, 0, "Initial Investment")
ws_capex8.write_formula(1, 1, "='Исходные данные'!$B$12")
ws_capex8.write(2, 0, "Miner Replacement Cost (Year 3)")
ws_capex8.write_formula(2, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")
ws_capex8.write(3, 0, "Miner Replacement Cost (Year 6)")
ws_capex8.write_formula(3, 1, "='Исходные данные'!$B$9*'Исходные данные'!$B$10*'Исходные данные'!$B$5")

###############################################################################
# Лист "Финансирование (8 лет)" – для 8-летнего варианта
# Здесь три займа:
# Loan 1: Initial Investment: 435M, Term = 8 (начинается с года 1)
# Loan 2: Replacement Loan (Year 3): 135M, Term = 8 (начинается с года 3)
# Loan 3: Replacement Loan (Year 6): 135M, Term = 8 (начинается с года 6)
ws_fin8 = workbook.add_worksheet('Финансирование (8 лет)')
ws_fin8.write(0, 0, "Год")
ws_fin8.write(0, 1, "Loan 1 Total Payment (RUB)")
ws_fin8.write(0, 2, "Loan 2 Total Payment (RUB)")
ws_fin8.write(0, 3, "Loan 3 Total Payment (RUB)")
ws_fin8.write(0, 4, "Суммарный Payment (RUB)")
for year in range(1, 9):
    r = year
    ws_fin8.write(r, 0, year)
    # Loan 1: Principal_1 = -('Исходные данные'!$B$12/8)
    ws_fin8.write_formula(r, 1,
        f"=IF(A{r+1}>=1, -(( 'Исходные данные'!$B$12/8 ) + ( 'Исходные данные'!$B$12 - (A{r+1}-1)*( 'Исходные данные'!$B$12/8 ))*'Исходные данные'!$B$20), 0)")
    # Loan 2: Replacement, активен, если год>=3; Principal_2 = -((135M)/8)
    ws_fin8.write_formula(r, 2,
        f"=IF(A{r+1}>=3, -(((135000000)/8) + ((135000000 - (A{r+1}-3)*((135000000)/8))*'Исходные данные'!$B$20)), 0)")
    # Loan 3: Replacement, активен, если год>=6; Principal_3 = -((135M)/8)
    ws_fin8.write_formula(r, 3,
        f"=IF(A{r+1}>=6, -(((135000000)/8) + ((135000000 - (A{r+1}-6)*((135000000)/8))*'Исходные данные'!$B$20)), 0)")
    ws_fin8.write_formula(r, 4, f"=B{r+1} + C{r+1} + D{r+1}")

###############################################################################
# Лист "P&L (8 лет)" – отчет о прибылях и убытках для 8-летнего варианта
ws_pl8 = workbook.add_worksheet('P&L (8 лет)')
pl_headers8 = ["Год", "Revenue (RUB)", "OPEX (RUB)", "Depreciation (RUB)",
               "EBIT (RUB)", "Interest (RUB)", "EBT (RUB)", "Tax (RUB)",
               "Net Profit (RUB)"]
for col, header in enumerate(pl_headers8):
    ws_pl8.write(0, col, header)
dep = 45000000
for year in range(1, 9):
    r = year
    ws_pl8.write(r, 0, year)
    ws_pl8.write_formula(r, 1, f"= 'Доходы (8 лет)'!G{r+1} + 'Исходные данные'!$B$22")
    ws_pl8.write_formula(r, 2, "='ОПЕКС'!B5")
    ws_pl8.write(r, 3, dep)
    ws_pl8.write_formula(r, 4, f"=B{r+1} - C{r+1} - D{r+1}")
    ws_pl8.write_formula(r, 5, f"= 'Финансирование (8 лет)'!$E${r+1}")
    ws_pl8.write_formula(r, 6, f"=E{r+1} + F{r+1}")
    ws_pl8.write_formula(r, 7, f"=G{r+1} * 'Исходные данные'!$B$18")
    ws_pl8.write_formula(r, 8, f"=G{r+1} - H{r+1}")

###############################################################################
workbook.close()
