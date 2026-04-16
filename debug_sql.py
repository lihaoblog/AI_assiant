import datetime

# 测试用例
demand_time = '2026-04-18'
webaz = 2

# 计算定义时间
def_date = datetime.datetime.strptime(demand_time, '%Y-%m-%d') - datetime.timedelta(days=webaz)
print(f"需求时间: {demand_time}")
print(f"收货处理时间: {webaz}")
print(f"定义时间: {def_date.date()}")

# 计算星期
# 原始逻辑: 0=周日, 1=周一, ..., 6=周六
original_weekday = (def_date.weekday() + 1) % 7
print(f"原始逻辑星期 (0=周日): {original_weekday}")

# SQL WEEKDAY(): 0=周一, 1=周二, ..., 6=周日
sql_weekday = def_date.weekday()
print(f"SQL WEEKDAY() (0=周一): {sql_weekday}")

# 分析条件
print("\n原始逻辑条件:")
print(f"定义时间(星期)='4' (周四) AND 时间差={webaz}")
print("应该执行: DATEDELTA(需求日,-收货处理时间)-1 = 2026-04-18 - 2天 - 1天 = 2026-04-15")

print("\nSQL条件:")
print(f"WEEKDAY(定义时间)={sql_weekday} AND O.WEBAZ={webaz}")
print(f"当前SQL执行的条件: 当WEEKDAY=3 AND O.WEBAZ=2时，返回定义时间(2026-04-16)")
print("但应该执行: 当WEEKDAY=3 AND O.WEBAZ=2时，返回定义时间-1天(2026-04-15)")

# 修正后的SQL逻辑
print("\n修正后的SQL逻辑:")
print("CASE")
print("    WHEN O.WEBAZ IS NULL THEN NULL")
print("    -- 周日 (原始逻辑: 6, SQL: 6)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 6")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周六 (原始逻辑: 5, SQL: 5)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 5 AND O.WEBAZ = 1")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 5 AND (O.WEBAZ = 0 OR O.WEBAZ > 1)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周五 (原始逻辑: 4, SQL: 4)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND O.WEBAZ = 1")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND O.WEBAZ = 2")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 4 AND (O.WEBAZ > 2 OR O.WEBAZ = 0)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周四 (原始逻辑: 3, SQL: 3)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND (O.WEBAZ > 0 AND O.WEBAZ < 3)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND O.WEBAZ = 3")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 3 AND (O.WEBAZ = 0 OR O.WEBAZ > 3)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周三 (原始逻辑: 2, SQL: 2)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND (O.WEBAZ > 0 AND O.WEBAZ < 4)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND O.WEBAZ = 4")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 2 AND (O.WEBAZ = 0 OR O.WEBAZ > 4)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周二 (原始逻辑: 1, SQL: 1)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND (O.WEBAZ > 0 AND O.WEBAZ < 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND O.WEBAZ = 5")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 1 AND (O.WEBAZ = 0 OR O.WEBAZ > 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    -- 周一 (原始逻辑: 0, SQL: 0)")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 0 AND (O.WEBAZ > 0 AND O.WEBAZ < 6)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 1 DAY")
print("    WHEN WEEKDAY(DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY)) = 0 AND (O.WEBAZ = 0 OR O.WEBAZ > 5)")
print("         THEN DATE_SUB(SUBSTR(m.demand_time,1,10), INTERVAL O.WEBAZ DAY) - INTERVAL 2 DAY")
print("    ELSE ''")
print("END AS 自定义时间")
