import datetime

# 测试用例
test_dates = [
    '2026-04-13',  # 周日
    '2026-04-14',  # 周一
    '2026-04-15',  # 周二
    '2026-04-16',  # 周三
    '2026-04-17',  # 周四
    '2026-04-18',  # 周五
    '2026-04-19',  # 周六
]

print("日期测试:")
for date_str in test_dates:
    d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    weekday = d.weekday()  # 0=周一, 1=周二, ..., 6=周日
    isoweekday = d.isoweekday()  # 1=周一, 2=周二, ..., 7=周日
    custom_weekday = (weekday + 1) % 7  # 0=周日, 1=周一, ..., 6=周六
    print(f"日期: {date_str}, WEEKDAY(): {weekday}, 自定义(0=周日): {custom_weekday}")

# 修正后的SQL逻辑
print("\n修正后的SQL逻辑:")
print("CASE")
print("    WHEN O.WEBAZ IS NULL THEN NULL")
print("    -- 周日 (自定义: 0, SQL: 6)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 6")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周六 (自定义: 6, SQL: 5)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 5 AND O.WEBAZ = 1")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 5 AND (O.WEBAZ = 0 OR O.WEBAZ > 1)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周五 (自定义: 5, SQL: 4)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND O.WEBAZ = 1")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND O.WEBAZ = 2")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND (O.WEBAZ > 2 OR O.WEBAZ = 0)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周四 (自定义: 4, SQL: 3)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND (O.WEBAZ > 0 AND O.WEBAZ < 3)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND O.WEBAZ = 3")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND (O.WEBAZ = 0 OR O.WEBAZ > 3)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周三 (自定义: 3, SQL: 2)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND (O.WEBAZ > 0 AND O.WEBAZ < 4)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND O.WEBAZ = 4")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND (O.WEBAZ = 0 OR O.WEBAZ > 4)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周二 (自定义: 2, SQL: 1)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND (O.WEBAZ > 0 AND O.WEBAZ < 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND O.WEBAZ = 5")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND (O.WEBAZ = 0 OR O.WEBAZ > 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周一 (自定义: 1, SQL: 0)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 0 AND (O.WEBAZ > 0 AND O.WEBAZ < 6)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 0 AND (O.WEBAZ = 0 OR O.WEBAZ > 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    ELSE ''")
print("END AS 自定义时间")

# 测试具体用例
print("\n测试具体用例:")
demand_time = '2026-04-18'
webaz = 2
def_date = datetime.datetime.strptime(demand_time, '%Y-%m-%d') - datetime.timedelta(days=webaz)
print(f"需求时间: {demand_time}")
print(f"收货处理时间: {webaz}")
print(f"定义时间: {def_date.date()}")
print(f"定义时间星期: 周四")
print(f"WEEKDAY(): {def_date.weekday()}")
print(f"预期结果: 2026-04-15")
