from database import get_container_load_material
from llm_parser import parse_all_fields, parse_field_meaning
from loading import LoadingSystem
from optimization import ContainerLoadingOptimizer
import pandas as pd

def explain_loading_plan(loading_plan):
    """
    使用大模型解释装柜方案
    :param loading_plan: 装载方案
    :return: 解释结果
    """
    from langchain_core.prompts import ChatPromptTemplate
    from all_env.util_llm import llm
    
    # 构建装柜方案摘要
    summary = f"装柜方案包含 {len(loading_plan)} 件货物\n"
    for i, cargo in enumerate(loading_plan[:5]):
        summary += f"{i+1}. {cargo.get('name', '未知')} - 位置: {cargo['position']}\n"
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", "你是物流装柜领域的专家，负责解释装柜方案的合理性和优化建议。"),
        ("human", "请解释以下装柜方案的合理性，并提供优化建议：\n{summary}")
    ])
    
    try:
        msg = prompt.format_messages(summary=summary)
        result = llm.invoke(msg).content.strip()
        return result
    except Exception as e:
        print(f"⚠️ 装柜方案解释失败：{str(e)}")
        return f"解释失败：{str(e)}"

def main():
    try:
        print("=== 装柜系统启动 ===")
        
        # 1. 从数据库获取数据
        print("\n1. 从数据库获取装柜数据")
        df = get_container_load_material()
        
        # 2. 使用大模型解析字段含义
        print("\n2. 解析字段含义")
        field_meanings = parse_all_fields(df)
        
        # 3. 数据预处理
        print("\n3. 数据预处理")
        cargoes = []
        for _, row in df.iterrows():
            # 修正字段映射和单位转换
            length_val = row.get('length_meters', '')
            width_val = row.get('width', '')
            height_val = row.get('high_value', '')  # high_value表示高度
            weight_val = row.get('single_piece_weight', '')
            length_unit = row.get('length_unit', 'MM')
            weight_unit = row.get('weight_unit', 'kg')
            
            # 处理NaN值和空值
            def safe_float(value):
                if value is None or pd.isna(value):
                    return 0
                try:
                    return float(str(value).strip())
                except (ValueError, TypeError):
                    return 0
            
            # 解析长度值
            length = safe_float(length_val)
            width = safe_float(width_val)
            height = safe_float(height_val)
            weight = safe_float(weight_val)
            
            # 单位转换
            # 长度单位转换为米
            if length_unit and str(length_unit).strip().upper() == 'MM':
                length /= 1000
                width /= 1000
                height /= 1000
            
            # 重量单位转换为千克（如果需要）
            if weight_unit and str(weight_unit).strip().upper() != 'KG':
                # 这里可以根据实际情况添加其他重量单位的转换
                pass
            
            # 对于长宽高不明确的视为0，不予装柜
            if length <= 0 or width <= 0 or height <= 0:
                continue
            
            # 获取单箱件数
            single_box_quantity = safe_float(row.get('single_box_quantity', 1))
            # 确保至少有一件
            quantity = max(1, int(single_box_quantity))
            
            # 为每个物料创建对应的货物实例
            for i in range(quantity):
                cargo = {
                    'id': f"{row.get('id', '')}_{i+1}",
                    'name': row.get('material_name', ''),
                    'length': length,
                    'width': width,
                    'height': height,
                    'weight': weight,
                    'packaging_type': row.get('package_category', ''),
                    'packaging_status': row.get('package_status', ''),
                    'can_bear_weight': row.get('is_bearing', '是') == '是',
                    'self_stack': row.get('is_self_stacked', '否'),  # 能否自叠
                    'top_placement': row.get('is_upper_middle_placement', '否'),  # 顶层摆放
                    'bottom_only': row.get('is_bottom_placement', '否') == '是',
                    'bottom_upright_top_side': row.get('whether_lower_layerupright_upper_layer_lateral', '否') == '是',
                    'code_placement_requirements': row.get('code_placement_requirements', ''),  # 码放要求
                    'is_fixed_combination': False
                }
                cargoes.append(cargo)
        
        print(f"预处理完成，共 {len(cargoes)} 件货物")
        
        # 4. 执行装柜逻辑
        print("\n4. 执行装柜逻辑")
        loading_system = LoadingSystem(container_type='20ft')
        loaded_cargoes = loading_system.load_cargoes(cargoes)
        
        # 5. 执行装柜优化
        print("\n5. 执行装柜优化")
        # 使用11.63m的集装箱尺寸
        optimizer = ContainerLoadingOptimizer(11.63, 2.63, 2.67)  # 11.63m集装箱尺寸（米）
        optimized_plan = optimizer.optimize_loading(cargoes)
        
        if optimized_plan:
            print("装柜优化成功")
        else:
            print("装柜优化失败")
        
        # 6. 大模型辅助解释
        print("\n6. 装柜方案解释")
        explanation = explain_loading_plan(optimized_plan)
        print("装柜方案解释：")
        print(explanation)
        
        # 7. 输出装柜结果
        print("\n7. 装柜结果")
        print(f"成功装载：{len(optimized_plan)} 件货物")
        
        # 计算空间利用率
        try:
            # 计算实际装载的货物体积
            total_loaded_volume = sum(float(c.get('length', 0)) * float(c.get('width', 0)) * float(c.get('height', 0)) for c in optimized_plan)
            container_volume = 11.63 * 2.63 * 2.67  # 11.63m集装箱体积 (约81.45 m³)
            volume_utilization = (total_loaded_volume / container_volume) * 100
            print(f"空间利用率：{volume_utilization:.2f}%")
        except (ValueError, TypeError, ZeroDivisionError):
            print("空间利用率：0.00%")
        
        # 打印前5件装载的货物信息
        print("\n前5件装载的货物：")
        for i, cargo in enumerate(optimized_plan[:5]):
            print(f"{i+1}. {cargo['name']} - 位置: {cargo['position']}")
        
        # 8. 保存优化结果到JSON文件，供3D展示使用
        import json
        try:
            # 准备保存的数据
            save_data = []
            for i, cargo in enumerate(optimized_plan):
                position = cargo.get('position', {'x': 0, 'y': 0, 'z': 0})
                save_data.append({
                    'id': i + 1,
                    'name': cargo.get('name', '未知'),
                    'length': float(cargo.get('length', 0)) * 1000,  # 转换为mm
                    'width': float(cargo.get('width', 0)) * 1000,   # 转换为mm
                    'height': float(cargo.get('height', 0)) * 1000,  # 转换为mm
                    'weight': float(cargo.get('weight', 0)),
                    'position': {
                        'x': position.get('x', 0) * 1000,  # 转换为mm
                        'y': position.get('y', 0) * 1000,  # 转换为mm
                        'z': position.get('z', 0) * 1000   # 转换为mm
                    }
                })
            
            # 保存到JSON文件
            with open('optimized_result.json', 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            print("\n优化结果已保存到 optimized_result.json 文件")
        except Exception as e:
            print(f"保存优化结果失败：{e}")
        
        print("\n装柜系统执行完成！")
        
    except Exception as e:
        print(f"程序执行失败：{str(e)}")

if __name__ == "__main__":
    main()
