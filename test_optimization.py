#!/usr/bin/env python3
"""
测试优化后的装柜算法性能
"""

from optimization import ContainerLoadingOptimizer
import time
import json

# 生成模拟货物数据
def generate_test_cargoes():
    """生成测试用的货物数据"""
    cargoes = []
    
    # 大货
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
    
    # 中型货物
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
    
    # 小型货物
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
    
    # 不可承重货物
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
    
    # 破损货物
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

def test_optimization():
    """测试优化算法性能"""
    print("=== 测试装柜算法优化性能 ===")
    
    # 生成测试数据
    cargoes = generate_test_cargoes()
    print(f"生成 {len(cargoes)} 件测试货物")
    
    # 初始化优化器（20英尺集装箱尺寸）
    optimizer = ContainerLoadingOptimizer(5.9, 2.35, 2.39)  # 20英尺集装箱尺寸（米）
    
    # 测试时间
    start_time = time.time()
    
    # 执行优化
    optimized_plan = optimizer.optimize_loading(cargoes)
    
    end_time = time.time()
    execution_time = end_time - start_time
    
    print(f"优化执行时间: {execution_time:.2f} 秒")
    
    # 计算空间利用率
    if optimized_plan:
        print(f"成功装载: {len(optimized_plan)} 件货物")
        
        # 计算实际装载的货物体积
        total_loaded_volume = sum(
            float(c.get('length', 0)) * float(c.get('width', 0)) * float(c.get('height', 0)) 
            for c in optimized_plan
        )
        
        # 20英尺集装箱体积
        container_volume = 5.9 * 2.35 * 2.39  # 约33.2 m³
        volume_utilization = (total_loaded_volume / container_volume) * 100
        
        print(f"空间利用率: {volume_utilization:.2f}%")
        
        # 打印前5件装载的货物信息
        print("\n前5件装载的货物:")
        for i, cargo in enumerate(optimized_plan[:5]):
            print(f"{i+1}. {cargo['name']} - 位置: {cargo['position']}")
        
        # 保存优化结果
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
        
        with open('test_optimized_result.json', 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        print("\n测试结果已保存到 test_optimized_result.json 文件")
    else:
        print("装柜优化失败")

if __name__ == "__main__":
    test_optimization()
