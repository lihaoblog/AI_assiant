import pymysql
import pandas as pd

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': '123456',
    'database': 'container_db'
}

try:
    # 连接数据库
    conn = pymysql.connect(**DB_CONFIG)
    print("✅ 数据库连接成功")
    
    # 查询所有数据
    query = "SELECT * FROM container_load_material"
    df = pd.read_sql(query, conn)
    print(f"✅ 从数据库获取数据成功，共 {len(df)} 条记录")
    
    # 显示前10条记录
    print("\n前10条记录：")
    print(df.head(10))
    
    # 检查复合材料压力容器_1465的数据
    print("\n复合材料压力容器_1465的数据：")
    container_1465 = df[df['material_name'].str.contains('1465', na=False)]
    print(container_1465)
    
    conn.close()
except Exception as e:
    print(f"❌ 数据库操作失败：{e}")
