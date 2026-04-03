import sys
import os

# 把 all_env 所在的父目录加入 Python 搜索路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'LLM_tool')))

from all_env.util_llm import llm
from langchain_core.prompts import ChatPromptTemplate

def parse_field_meaning(field_name, field_value):
    """
    使用大模型解析字段含义
    :param field_name: 字段名
    :param field_value: 字段值
    :return: 解析结果
    """
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是物流装柜领域的专家，负责解析装柜数据字段的含义。注意：长度单位统一为毫米（mm），重量单位统一为千克（kg）。"),
        ("human", "请解析以下装柜数据字段的含义：\n字段名：{field_name}\n字段值：{field_value}\n\n请提供简洁明了的解析结果。")
    ])
    
    try:
        msg = prompt.format_messages(field_name=field_name, field_value=field_value)
        result = llm.invoke(msg).content.strip()
        return result
    except Exception as e:
        print(f"字段解析失败 [{field_name}]：{str(e)}")
        return f"解析失败：{str(e)}"

def parse_all_fields(df):
    """
    解析所有字段的含义
    :param df: 数据 DataFrame
    :return: 解析结果字典
    """
    parsed_fields = {}
    for column in df.columns:
        # 取第一个非空值作为示例
        sample_value = df[column].dropna().iloc[0] if not df[column].dropna().empty else ""
        meaning = parse_field_meaning(column, sample_value)
        parsed_fields[column] = meaning
        print(f"字段：{column} → 含义：{meaning}")
    return parsed_fields
