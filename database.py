import pymysql
import pandas as pd
from config import DB_CONFIG

def get_container_load_material():
    """
    从container_load_material表获取数据
    :return: 数据 DataFrame
    """
    conn = None
    try:
        conn = pymysql.connect(**DB_CONFIG)
        query = "SELECT * FROM container_load_material"
        df = pd.read_sql(query, conn)
        print(f"从数据库获取数据成功，共 {len(df)} 条记录")
        return df
    except pymysql.Error as e:
        print(f"数据库操作失败：{e}")
        raise
    finally:
        if conn:
            conn.close()
