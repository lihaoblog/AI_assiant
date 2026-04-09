import numpy as np
from typing import List, Dict, Tuple, Optional
from enum import Enum

class RotationType(Enum):
    """三维旋转类型枚举"""
    RT_WHD = 0  # 宽×高×深 (原始方向)
    RT_HWD = 1  # 高×宽×深
    RT_HDW = 2  # 高×深×宽
    RT_DHW = 3  # 深×高×宽
    RT_DWH = 4  # 深×宽×高
    RT_WDH = 5  # 宽×深×高

class ContainerLoadingOptimizer:
    """装柜优化计算核心模块 - 确保货物不重叠"""
    
    def __init__(self, container_length, container_width, container_height):
        self.container_length = container_length
        self.container_width = container_width
        self.container_height = container_height
    
    def get_rotated_dimensions(self, length: float, width: float, height: float, rotation_type: RotationType) -> Tuple[float, float, float]:
        """
        获取旋转后的尺寸
        """
        if rotation_type == RotationType.RT_WHD:
            return (length, width, height)
        elif rotation_type == RotationType.RT_HWD:
            return (width, length, height)
        elif rotation_type == RotationType.RT_HDW:
            return (height, length, width)
        elif rotation_type == RotationType.RT_DHW:
            return (height, width, length)
        elif rotation_type == RotationType.RT_DWH:
            return (width, height, length)
        else:  # RT_WDH
            return (length, height, width)
    
    def optimize_loading(self, cargoes):
        """
        优化装柜，确保货物不重叠
        """
        valid_cargoes = []
        for cargo in cargoes:
            try:
                length = float(cargo.get('length', 0.1))
                width = float(cargo.get('width', 0.1))
                height = float(cargo.get('height', 0.1))
                if length > 0 and width > 0 and height > 0:
                    valid_cargoes.append(cargo)
            except (ValueError, TypeError):
                continue
        
        if not valid_cargoes:
            return []
        
        # 货物分类和排序
        sorted_cargoes = self._categorize_and_sort_cargoes(valid_cargoes)
        
        # 使用启发式算法进行装柜
        print("使用启发式算法优化装柜...")
        result = self._heuristic_loading(sorted_cargoes)
        
        return result
    
    def _categorize_and_sort_cargoes(self, cargoes: List[Dict]) -> List[Dict]:
        """
        货物分类和排序
        """
        def categorize_cargo(cargo):
            try:
                length = float(cargo.get('length', 0.1))
                width = float(cargo.get('width', 0.1))
                height = float(cargo.get('height', 0.1))
                weight = float(cargo.get('weight', 0.1))
                volume = length * width * height
                
                category = 0
                if cargo.get('bottom_only', False):
                    category = 0
                elif all(dim > 0.75 for dim in [length, width, height]):
                    category = 1
                elif weight > 500:
                    category = 2
                elif not cargo.get('can_bear_weight', True):
                    category = 3
                else:
                    category = 4
                
                return (category, -volume, -weight)
            except (ValueError, TypeError):
                return (5, 0, 0)
        
        return sorted(cargoes, key=categorize_cargo)
    
    def _heuristic_loading(self, cargoes: List[Dict]) -> List[Dict]:
        """
        启发式装柜算法 - 从里往外填满，货物靠在一起
        """
        placed_cargoes = []
        placed_positions = []
        placed_rotations = []
        
        for cargo in cargoes:
            best_position = None
            best_rotation = None
            best_score = -float('inf')
            
            try:
                length = float(cargo.get('length', 0.1))
                width = float(cargo.get('width', 0.1))
                height = float(cargo.get('height', 0.1))
            except (ValueError, TypeError):
                length = 0.1
                width = 0.1
                height = 0.1
            
            # 尝试所有6种旋转方式
            for rotation_type in RotationType:
                rotated_l, rotated_w, rotated_h = self.get_rotated_dimensions(length, width, height, rotation_type)
                
                # 寻找最佳放置位置
                position, score = self._find_best_position(
                    rotated_l, rotated_w, rotated_h, placed_cargoes, placed_positions, placed_rotations
                )
                
                if position and score > best_score:
                    best_position = position
                    best_rotation = rotation_type
                    best_score = score
            
            if best_position:
                placed_cargoes.append(cargo)
                placed_positions.append(best_position)
                placed_rotations.append(best_rotation)
            else:
                print(f"无法放置货物: {cargo.get('name', 'Unknown')}")
        
        # 生成结果
        result = []
        for i, cargo in enumerate(placed_cargoes):
            result.append({
                **cargo,
                'position': placed_positions[i],
                'rotation': placed_rotations[i].name
            })
        
        return result
    
    def _find_best_position(self, length: float, width: float, height: float, 
                           placed_cargoes: List[Dict], placed_positions: List[Dict], 
                           placed_rotations: List[RotationType]) -> Tuple[Optional[Dict], float]:
        """
        寻找最佳放置位置 - 从里往外填满，优先宽度，再高度，最后长度
        """
        best_position = None
        best_score = -float('inf')
        
        # 检查起点位置（从里往外的起点）
        if self._check_position_valid(0, 0, 0, length, width, height, placed_cargoes, placed_positions, placed_rotations):
            score = self._calculate_position_score(0, 0, 0, length, width, height)
            if score > best_score:
                best_position = {'x': 0, 'y': 0, 'z': 0}
                best_score = score
        
        # 从已放置货物周围寻找位置，按照优先顺序：宽度方向 > 高度方向 > 长度方向
        for i, (placed_cargo, placed_pos, placed_rot) in enumerate(zip(placed_cargoes, placed_positions, placed_rotations)):
            try:
                pl = float(placed_cargo.get('length', 0.1))
                pw = float(placed_cargo.get('width', 0.1))
                ph = float(placed_cargo.get('height', 0.1))
                
                # 考虑旋转后的尺寸
                rotated_pl, rotated_pw, rotated_ph = self.get_rotated_dimensions(pl, pw, ph, placed_rot)
                
                # 宽度方向（右侧）- 最高优先级
                x, y, z = placed_pos['x'], placed_pos['y'] + rotated_pw, placed_pos['z']
                if self._check_position_valid(x, y, z, length, width, height, placed_cargoes, placed_positions, placed_rotations):
                    score = self._calculate_position_score(x, y, z, length, width, height)
                    if score > best_score:
                        best_position = {'x': x, 'y': y, 'z': z}
                        best_score = score
                
                # 高度方向（上方）- 次优先级
                x, y, z = placed_pos['x'], placed_pos['y'], placed_pos['z'] + rotated_ph
                if self._check_position_valid(x, y, z, length, width, height, placed_cargoes, placed_positions, placed_rotations):
                    score = self._calculate_position_score(x, y, z, length, width, height)
                    if score > best_score:
                        best_position = {'x': x, 'y': y, 'z': z}
                        best_score = score
                
                # 长度方向（后侧）- 最后优先级
                x, y, z = placed_pos['x'] + rotated_pl, placed_pos['y'], placed_pos['z']
                if self._check_position_valid(x, y, z, length, width, height, placed_cargoes, placed_positions, placed_rotations):
                    score = self._calculate_position_score(x, y, z, length, width, height)
                    if score > best_score:
                        best_position = {'x': x, 'y': y, 'z': z}
                        best_score = score
                
                # 检查宽度方向的其他可能位置（确保货物靠在一起）
                for j, (other_cargo, other_pos, other_rot) in enumerate(zip(placed_cargoes, placed_positions, placed_rotations)):
                    if i != j:
                        try:
                            opl = float(other_cargo.get('length', 0.1))
                            opw = float(other_cargo.get('width', 0.1))
                            oph = float(other_cargo.get('height', 0.1))
                            rotated_opl, rotated_opw, rotated_oph = self.get_rotated_dimensions(opl, opw, oph, other_rot)
                            
                            # 检查与其他货物的宽度方向相邻位置
                            x, y, z = other_pos['x'], other_pos['y'] + rotated_opw, other_pos['z']
                            if self._check_position_valid(x, y, z, length, width, height, placed_cargoes, placed_positions, placed_rotations):
                                score = self._calculate_position_score(x, y, z, length, width, height)
                                if score > best_score:
                                    best_position = {'x': x, 'y': y, 'z': z}
                                    best_score = score
                        except (ValueError, TypeError):
                            continue
            except (ValueError, TypeError):
                continue
        
        return best_position, best_score
    
    def _check_position_valid(self, x: float, y: float, z: float, 
                             length: float, width: float, height: float,
                             placed_cargoes: List[Dict], placed_positions: List[Dict], 
                             placed_rotations: List[RotationType]) -> bool:
        """
        检查位置是否有效，确保不重叠
        """
        # 检查是否在集装箱内
        if (x < 0 or y < 0 or z < 0 or
            x + length > self.container_length or
            y + width > self.container_width or
            z + height > self.container_height):
            return False
        
        # 检查是否与已放置货物重叠
        for i, (placed_cargo, placed_pos, placed_rot) in enumerate(zip(placed_cargoes, placed_positions, placed_rotations)):
            try:
                pl = float(placed_cargo.get('length', 0.1))
                pw = float(placed_cargo.get('width', 0.1))
                ph = float(placed_cargo.get('height', 0.1))
                
                # 考虑旋转后的尺寸
                rotated_pl, rotated_pw, rotated_ph = self.get_rotated_dimensions(pl, pw, ph, placed_rot)
                
                # 检查碰撞
                if not (x + length <= placed_pos['x'] or placed_pos['x'] + rotated_pl <= x or
                        y + width <= placed_pos['y'] or placed_pos['y'] + rotated_pw <= y or
                        z + height <= placed_pos['z'] or placed_pos['z'] + rotated_ph <= z):
                    return False
            except (ValueError, TypeError):
                continue
        
        return True
    
    def _calculate_position_score(self, x: float, y: float, z: float,
                                  length: float, width: float, height: float) -> float:
        """
        计算位置得分 - 优先宽度，再高度，最后长度
        """
        score = 0
        
        # 宽度方向得分（越靠近左侧越好，优先级最高）
        score += (1 - y / self.container_width) * 5
        
        # 高度方向得分（越靠近底部越好，优先级次之）
        score += (1 - z / self.container_height) * 3
        
        # 长度方向得分（越靠近前侧越好，优先级最低）
        score += (1 - x / self.container_length) * 1
        
        # 空间利用率得分
        available_space = self.container_length * self.container_width * self.container_height
        used_space = length * width * height
        score += (used_space / available_space) * 10
        
        # 靠近已放置货物的得分（确保货物靠在一起）
        score += 2  # 基础得分
        
        return score
