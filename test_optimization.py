#!/usr/bin/env python3
"""
测试装柜优化算法性能
"""

import sys
import os
from optimization import ContainerLoadingOptimizer

def generate_test_cargoes():
    """生成测试货物数据"""
    cargoes = [
        # 大货
        {
            'id': '1',
            'name': '大货1',
            'length': 1.5,
            'width': 1.2,
            'height': 1.0,
            'weight': 800,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 重货
        {
            'id': '2',
            'name': '重货1',
            'length': 1.0,
            'width': 0.8,
            'height': 0.6,
            'weight': 1200,
            'bottom_only': True,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 普通货物
        {
            'id': '3',
            'name': '普通货1',
            'length': 0.8,
            'width': 0.6,
            'height': 0.4,
            'weight': 300,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放&侧放',
            'orientation': 'upright'
        },
        # 相同规格货物1
        {
            'id': '4',
            'name': '相同货1',
            'length': 0.5,
            'width': 0.5,
            'height': 0.5,
            'weight': 200,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 相同规格货物2
        {
            'id': '5',
            'name': '相同货1',
            'length': 0.5,
            'width': 0.5,
            'height': 0.5,
            'weight': 200,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 不可承重货物
        {
            'id': '6',
            'name': '不可承重货',
            'length': 0.6,
            'width': 0.4,
            'height': 0.3,
            'weight': 50,
            'bottom_only': False,
            'can_bear_weight': False,
            'self_stack': '否',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 小货
        {
            'id': '7',
            'name': '小货1',
            'length': 0.3,
            'width': 0.3,
            'height': 0.3,
            'weight': 100,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 小货
        {
            'id': '8',
            'name': '小货2',
            'length': 0.3,
            'width': 0.3,
            'height': 0.3,
            'weight': 100,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 小货
        {
            'id': '9',
            'name': '小货3',
            'length': 0.3,
            'width': 0.3,
            'height': 0.3,
            'weight': 100,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        },
        # 小货
        {
            'id': '10',
            'name': '小货4',
            'length': 0.3,
            'width': 0.3,
            'height': 0.3,
            'weight': 100,
            'bottom_only': False,
            'can_bear_weight': True,
            'self_stack': '是',
            'packaging_status': '',
            'placement_requirement': '正放',
            'orientation': 'upright'
        }
    ]
    return cargoes

def test_optimization():
    """测试优化算法"""
    # 20英尺集装箱尺寸（米）
    container_length = 5.9
    container_width = 2.35
    container_height = 2.39
    
    # 初始化优化器
    optimizer = ContainerLoadingOptimizer(container_length, container_width, container_height)
    
    # 生成测试货物
    cargoes = generate_test_cargoes()
    print(f"测试货物数量: {len(cargoes)}")
    
    # 运行优化
    print("\n运行装柜优化...")
    result = optimizer.optimize_loading(cargoes)
    
    # 计算装载率
    container_volume = container_length * container_width * container_height
    loaded_volume = 0
    for item in result:
        try:
            length = float(item.get('length', 0))
            width = float(item.get('width', 0))
            height = float(item.get('height', 0))
            loaded_volume += length * width * height
        except (ValueError, TypeError):
            continue
    
    loading_rate = (loaded_volume / container_volume) * 100
    print(f"\n装载结果:")
    print(f"装载货物数量: {len(result)}")
    print(f"装载体积: {loaded_volume:.2f} 立方米")
    print(f"集装箱体积: {container_volume:.2f} 立方米")
    print(f"装载率: {loading_rate:.2f}%")
    
    # 打印详细装载信息
    print("\n详细装载信息:")
    for i, item in enumerate(result):
        pos = item.get('position', {})
        print(f"{i+1}. {item.get('name')} - 位置: ({pos.get('x', 0):.2f}, {pos.get('y', 0):.2f}, {pos.get('z', 0):.2f}) - 尺寸: {item.get('length')}x{item.get('width')}x{item.get('height')}")
    
    return loading_rate

if __name__ == "__main__":
    test_optimization()
