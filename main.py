from loading import LoadingSystem
from optimization import ContainerLoadingOptimizer
import json

def generate_test_cargoes():
    """生成测试用的货物数据"""
    cargoes = []
    
    # 大货（单位：米）
    cargoes.append({
        'id': '1',
        'name': '大型设备',
        'length': 2.0,
        'width': 1.5,
        'height': 1.8,
        'weight': 1500,
        'packaging_type': '木箱',
        'packaging_status': '完好',
        'can_bear_weight': True,
        'self_stack': '是',
        'top_placement': '否',
        'bottom_only': True,
        'bottom_upright_top_side': False,
        'code_placement_requirements': '正放',
        'is_fixed_combination': False
    })
    
    # 中型货物（单位：米）
    for i in range(2, 7):
        cargoes.append({
            'id': str(i),
            'name': f'中型货物{i-1}',
            'length': 1.2,
            'width': 0.8,
            'height': 0.6,
            'weight': 200,
            'packaging_type': '纸箱',
            'packaging_status': '完好',
            'can_bear_weight': True,
            'self_stack': '是',
            'top_placement': '否',
            'bottom_only': False,
            'bottom_upright_top_side': False,
            'code_placement_requirements': '正放&侧放',
            'is_fixed_combination': False
        })
    
    # 小型货物（单位：米）
    for i in range(7, 27):
        cargoes.append({
            'id': str(i),
            'name': f'小型货物{i-6}',
            'length': 0.4,
            'width': 0.3,
            'height': 0.2,
            'weight': 20,
            'packaging_type': '纸箱',
            'packaging_status': '完好',
            'can_bear_weight': True,
            'self_stack': '是',
            'top_placement': '否',
            'bottom_only': False,
            'bottom_upright_top_side': False,
            'code_placement_requirements': '正放',
            'is_fixed_combination': False
        })
    
    # 不可承重货物（单位：米）
    cargoes.append({
        'id': '27',
        'name': '易碎品',
        'length': 0.5,
        'width': 0.5,
        'height': 0.5,
        'weight': 10,
        'packaging_type': '纸箱',
        'packaging_status': '完好',
        'can_bear_weight': False,
        'self_stack': '否',
        'top_placement': '是',
        'bottom_only': False,
        'bottom_upright_top_side': False,
        'code_placement_requirements': '正放',
        'is_fixed_combination': False
    })
    
    # 破损货物（单位：米）
    cargoes.append({
        'id': '28',
        'name': '破损货物',
        'length': 0.6,
        'width': 0.4,
        'height': 0.3,
        'weight': 15,
        'packaging_type': '纸箱',
        'packaging_status': '破损',
        'can_bear_weight': False,
        'self_stack': '否',
        'top_placement': '是',
        'bottom_only': False,
        'bottom_upright_top_side': False,
        'code_placement_requirements': '正放',
        'is_fixed_combination': False
    })
    
    return cargoes

def main():
    try:
        print("=== 装柜系统启动 ===")
        
        # 1. 生成测试数据
        print("\n1. 生成测试装柜数据")
        cargoes = generate_test_cargoes()
        print(f"生成完成，共 {len(cargoes)} 件货物")
        
        # 2. 执行装柜逻辑
        print("\n2. 执行装柜逻辑")
        loading_system = LoadingSystem(container_type='20ft')
        loaded_cargoes = loading_system.load_cargoes(cargoes)
        
        # 3. 执行装柜优化
        print("\n3. 执行装柜优化")
        # 使用20英尺集装箱尺寸（米）
        optimizer = ContainerLoadingOptimizer(5.898, 2.352, 2.393)  # 20英尺集装箱尺寸（米）
        optimized_plan = optimizer.optimize_loading(cargoes)
        
        if optimized_plan:
            print("装柜优化成功")
        else:
            print("装柜优化失败")
        
        # 4. 输出装柜结果
        print("\n4. 装柜结果")
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
        
        # 5. 保存优化结果到JSON文件，供3D展示使用
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
        print("\n请打开 visualization.html 文件查看3D可视化效果")
        
    except Exception as e:
        print(f"程序执行失败：{str(e)}")

if __name__ == "__main__":
    main()
