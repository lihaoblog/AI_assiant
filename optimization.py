import numpy as np
from typing import List, Dict, Tuple
from ortools.sat.python import cp_model

class ContainerLoadingOptimizer:
    """装柜优化计算核心模块"""
    
    def __init__(self, container_length, container_width, container_height):
        self.container_length = container_length
        self.container_width = container_width
        self.container_height = container_height
    
    def optimize_loading(self, cargoes):
        """
        使用Google OR-Tools CP-SAT和遗传算法优化装柜
        :param cargoes: 货物列表
        :return: 优化后的装载方案和未装载的货物
        """
        # 过滤掉无效货物
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
        
        # 计算集装箱体积
        container_volume = self.container_length * self.container_width * self.container_height
        
        # 按照装载顺序处理货物 - 优化分类和顺序
        # 1. 固定组合模型
        fixed_combination = [c for c in valid_cargoes if c.get('is_fixed_combination', False)]
        # 2. 底层摆放货物
        bottom_only = [c for c in valid_cargoes if c.get('bottom_only', False)]
        # 3. 大货（长宽高均大于75cm）
        large_cargoes = [c for c in valid_cargoes if all(float(c.get(dim, 0)) > 0.75 for dim in ['length', 'width', 'height'])]
        # 4. 底层正放上层侧放货物
        bottom_upright_top_side = [c for c in valid_cargoes if c.get('bottom_upright_top_side', False)]
        # 5. 不可承重货物
        non_bearing = [c for c in valid_cargoes if not c.get('can_bear_weight', True)]
        # 6. 包装状态为破损或变形的货物
        damaged = [c for c in valid_cargoes if isinstance(c.get('packaging_status', ''), str) and ('破损' in c.get('packaging_status', '') or '变形' in c.get('packaging_status', ''))]
        # 7. 相同规格货物
        same_spec_cargoes = []
        # 8. 余量货物
        remaining_cargoes = []
        
        # 分类货物
        processed = set()
        
        # 处理固定组合
        for cargo in fixed_combination:
            processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理底层摆放
        for cargo in bottom_only:
            if cargo.get('id', str(id(cargo))) not in processed:
                processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理大货
        for cargo in large_cargoes:
            if cargo.get('id', str(id(cargo))) not in processed:
                processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理底层正放上层侧放
        for cargo in bottom_upright_top_side:
            if cargo.get('id', str(id(cargo))) not in processed:
                processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理不可承重货物
        for cargo in non_bearing:
            if cargo.get('id', str(id(cargo))) not in processed:
                processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理破损或变形货物
        for cargo in damaged:
            if cargo.get('id', str(id(cargo))) not in processed:
                processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理相同规格货物
        # 基于长度、宽度、高度和重量分组
        spec_groups = {}
        for cargo in valid_cargoes:
            cargo_id = cargo.get('id', str(id(cargo)))
            if cargo_id not in processed:
                try:
                    key = (round(float(cargo.get('length', 0.1)), 2), 
                           round(float(cargo.get('width', 0.1)), 2), 
                           round(float(cargo.get('height', 0.1)), 2),
                           round(float(cargo.get('weight', 0.1)), 2))
                    if key not in spec_groups:
                        spec_groups[key] = []
                    spec_groups[key].append(cargo)
                except (ValueError, TypeError):
                    continue
        
        # 将相同规格的货物分组
        for group in spec_groups.values():
            if len(group) > 1:
                same_spec_cargoes.extend(group)
                for cargo in group:
                    processed.add(cargo.get('id', str(id(cargo))))
        
        # 处理余量货物
        for cargo in valid_cargoes:
            if cargo.get('id', str(id(cargo))) not in processed:
                remaining_cargoes.append(cargo)
        
        # 合并处理顺序 - 优化顺序以提高空间利用率
        # 1. 固定组合模型（最高优先级）
        # 2. 底层摆放货物（需要放在底部）
        # 3. 大货（体积大，先放）
        # 4. 底层正放上层侧放货物
        # 5. 相同规格货物（便于紧密排列）
        # 6. 余量货物
        # 7. 不可承重货物（放在上层）
        # 8. 破损或变形货物（放在上层）
        processing_order = fixed_combination + bottom_only + large_cargoes + bottom_upright_top_side + same_spec_cargoes + remaining_cargoes + non_bearing + damaged
        
        # 直接使用遗传算法（已优化的紧密排列策略）
        print("尝试遗传算法优化")
        result = self.genetic_algorithm_optimization(processing_order)
        # 容量限制后处理
        result = self.apply_volume_limit(result, container_volume)
        # 计算未装载的货物
        loaded_ids = {c.get('id', str(id(c))) for c in result}
        unloaded = [c for c in valid_cargoes if c.get('id', str(id(c))) not in loaded_ids]
        if unloaded:
            print(f"有 {len(unloaded)} 件货物未装载（超出容量）")
        print("遗传算法优化完成")
        return result
    
    def apply_volume_limit(self, cargoes, container_volume):
        """
        应用容量限制，确保总装载体积不超过集装箱容量
        :param cargoes: 货物列表
        :param container_volume: 集装箱体积
        :return: 调整后的货物列表
        """
        # 按货物体积排序（从大到小）
        sorted_cargoes = sorted(cargoes, key=lambda c: float(c.get('length', 0)) * float(c.get('width', 0)) * float(c.get('height', 0)), reverse=True)
        
        result = []
        total_volume = 0
        
        for cargo in sorted_cargoes:
            try:
                cargo_volume = float(cargo.get('length', 0)) * float(cargo.get('width', 0)) * float(cargo.get('height', 0))
                if total_volume + cargo_volume <= container_volume:
                    result.append(cargo)
                    total_volume += cargo_volume
                else:
                    break
            except (ValueError, TypeError):
                continue
        
        # 重新排序，保持原始顺序
        original_order = {c.get('id', str(id(c))): c for c in cargoes}
        result = [original_order[c.get('id', str(id(c)))] for c in result if c.get('id', str(id(c))) in original_order]
        
        return result
    
    def cp_sat_optimization(self, cargoes):
        """
        使用Google OR-Tools CP-SAT求解器优化装柜
        :param cargoes: 货物列表
        :return: 优化后的装载方案
        """
        model = cp_model.CpModel()
        
        # 过滤掉无效货物（尺寸为0或NaN的货物）
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
        
        # 变量
        positions = []
        rotations = []
        
        for i, cargo in enumerate(valid_cargoes):
            # 货物尺寸
            length = float(cargo.get('length', 0.1))
            width = float(cargo.get('width', 0.1))
            height = float(cargo.get('height', 0.1))
            
            # 旋转选项
            rot1 = model.NewBoolVar(f'rot1_{i}')  # 原始
            rot2 = model.NewBoolVar(f'rot2_{i}')  # 长宽交换
            rot3 = model.NewBoolVar(f'rot3_{i}')  # 长高交换
            rotations.append([rot1, rot2, rot3])
            
            # 位置变量
            x = model.NewIntVar(0, int(self.container_length * 100), f'x_{i}')
            y = model.NewIntVar(0, int(self.container_width * 100), f'y_{i}')
            z = model.NewIntVar(0, int(self.container_height * 100), f'z_{i}')
            
            # 旋转后的尺寸
            l1 = int(length * 100)
            w1 = int(width * 100)
            h1 = int(height * 100)
            
            l2 = w1
            w2 = l1
            h2 = h1
            
            l3 = l1
            w3 = h1
            h3 = w1
            
            # 确保货物在集装箱内
            model.Add(x + l1 * rot1 + l2 * rot2 + l3 * rot3 <= int(self.container_length * 100))
            model.Add(y + w1 * rot1 + w2 * rot2 + w3 * rot3 <= int(self.container_width * 100))
            model.Add(z + h1 * rot1 + h2 * rot2 + h3 * rot3 <= int(self.container_height * 100))
            
            # 确保只能选择一种旋转方式
            model.Add(rot1 + rot2 + rot3 == 1)
            
            # 处理装柜规则
            # 1. 底层摆放限制
            if cargo.get('bottom_only', False):
                # 底层货物优先放在底部
                model.Add(z <= 50)  # 限制在底部50cm以内
            
            # 2. 顶层摆放限制
            if cargo.get('top_placement', '否') == '是':
                # 顶层货物放在上部
                model.Add(z >= int(self.container_height * 100) - 200)  # 限制在上部200cm以内
            
            # 3. 托盘木箱只允许正放和正放旋转
            packaging_type = cargo.get('packaging_type', '')
            if isinstance(packaging_type, str) and ('托盘' in packaging_type or '木箱' in packaging_type):
                # 只允许rot1和rot2（正放和正放旋转）
                model.Add(rot3 == 0)
            
            # 4. 货物底部完全承重面（简化处理）
            # 这里可以添加更复杂的承重面检查
            
            positions.append((x, y, z))
        
        # 确保货物之间不重叠
        for i in range(len(valid_cargoes)):
            for j in range(i + 1, len(valid_cargoes)):
                # 货物i的尺寸
                l1_i = int(valid_cargoes[i].get('length', 0.1) * 100)
                w1_i = int(valid_cargoes[i].get('width', 0.1) * 100)
                h1_i = int(valid_cargoes[i].get('height', 0.1) * 100)
                
                # 货物j的尺寸
                l1_j = int(valid_cargoes[j].get('length', 0.1) * 100)
                w1_j = int(valid_cargoes[j].get('width', 0.1) * 100)
                h1_j = int(valid_cargoes[j].get('height', 0.1) * 100)
                
                # 不重叠约束
                x_i, y_i, z_i = positions[i]
                x_j, y_j, z_j = positions[j]
                
                # 货物i在货物j左边
                left = model.NewBoolVar(f'left_{i}_{j}')
                # 货物i在货物j右边
                right = model.NewBoolVar(f'right_{i}_{j}')
                # 货物i在货物j前面
                front = model.NewBoolVar(f'front_{i}_{j}')
                # 货物i在货物j后面
                back = model.NewBoolVar(f'back_{i}_{j}')
                # 货物i在货物j下面
                below = model.NewBoolVar(f'below_{i}_{j}')
                # 货物i在货物j上面
                above = model.NewBoolVar(f'above_{i}_{j}')
                
                model.Add(x_i + l1_i <= x_j).OnlyEnforceIf(left)
                model.Add(x_j + l1_j <= x_i).OnlyEnforceIf(right)
                model.Add(y_i + w1_i <= y_j).OnlyEnforceIf(front)
                model.Add(y_j + w1_j <= y_i).OnlyEnforceIf(back)
                model.Add(z_i + h1_i <= z_j).OnlyEnforceIf(below)
                model.Add(z_j + h1_j <= z_i).OnlyEnforceIf(above)
                
                model.Add(left + right + front + back + below + above >= 1)
        
        # 目标：最大化空间利用率
        total_volume = model.NewIntVar(0, int(self.container_length * self.container_width * self.container_height * 1000000), 'total_volume')
        volume_sum = sum(int(c.get('length', 0.1) * c.get('width', 0.1) * c.get('height', 0.1) * 1000000) for c in valid_cargoes)
        model.Add(total_volume == volume_sum)
        model.Maximize(total_volume)
        
        # 求解
        solver = cp_model.CpSolver()
        # 设置超时时间为30秒
        solver.parameters.max_time_in_seconds = 30.0
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            result = []
            for i, cargo in enumerate(valid_cargoes):
                x = solver.Value(positions[i][0]) / 100
                y = solver.Value(positions[i][1]) / 100
                z = solver.Value(positions[i][2]) / 100
                result.append({
                    **cargo,
                    'position': {'x': x, 'y': y, 'z': z}
                })
            return result
        else:
            return []
    
    def genetic_algorithm_optimization(self, cargoes, population_size=150, generations=300):
        """
        使用遗传算法增强优化
        :param cargoes: 货物列表
        :param population_size: 种群大小
        :param generations: 进化代数
        :return: 优化后的装载方案
        """
        # 过滤掉无效货物
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
        
        # 计算集装箱体积
        container_volume = self.container_length * self.container_width * self.container_height
        
        # 预处理货物信息，避免重复计算
        cargo_info = []
        for cargo in valid_cargoes:
            try:
                length = float(cargo.get('length', 0.1))
                width = float(cargo.get('width', 0.1))
                height = float(cargo.get('height', 0.1))
                weight = float(cargo.get('weight', 0.1))
                volume = length * width * height
                bottom_only = cargo.get('bottom_only', False)
                top_placement = cargo.get('top_placement', '否')
                can_bear_weight = cargo.get('can_bear_weight', True)
                self_stack = cargo.get('self_stack', '否')
                packaging_status = cargo.get('packaging_status', '')
                placement_requirement = cargo.get('code_placement_requirements', '')
                orientation = cargo.get('orientation', '')
                
                cargo_info.append({
                    'length': length,
                    'width': width,
                    'height': height,
                    'weight': weight,
                    'volume': volume,
                    'bottom_only': bottom_only,
                    'top_placement': top_placement,
                    'can_bear_weight': can_bear_weight,
                    'self_stack': self_stack,
                    'packaging_status': packaging_status,
                    'placement_requirement': placement_requirement,
                    'orientation': orientation
                })
            except (ValueError, TypeError):
                cargo_info.append({
                    'length': 0.1,
                    'width': 0.1,
                    'height': 0.1,
                    'weight': 0.1,
                    'volume': 0.001,
                    'bottom_only': False,
                    'top_placement': '否',
                    'can_bear_weight': True,
                    'self_stack': '是',
                    'packaging_status': '',
                    'placement_requirement': '',
                    'orientation': 'upright'
                })
        
        # 改进的适应度函数
        def calculate_fitness(solution):
            """计算适应度（空间利用率 + 不重叠惩罚 + 规则遵守 + 稳定性 + 容量限制 + 重心平衡）"""
            used_volume = 0
            overlap_penalty = 0
            rule_penalty = 0
            stability_score = 0
            capacity_penalty = 0
            center_of_gravity_penalty = 0
            weight_balance_penalty = 0
            
            # 计算使用体积和重量
            total_weight = 0
            weighted_x = 0
            weighted_y = 0
            weighted_z = 0
            
            for i, (cargo, pos) in enumerate(zip(valid_cargoes, solution)):
                info = cargo_info[i]
                length = info['length']
                width = info['width']
                height = info['height']
                weight = info['weight']
                volume = info['volume']
                
                used_volume += volume
                total_weight += weight
                
                # 计算重心
                cargo_center_x = pos['x'] + length / 2
                cargo_center_y = pos['y'] + width / 2
                cargo_center_z = pos['z'] + height / 2
                
                weighted_x += cargo_center_x * weight
                weighted_y += cargo_center_y * weight
                weighted_z += cargo_center_z * weight
                
                # 稳定性评分：越低的货物稳定性越高，且重货放在下面更稳定
                stability_score += pos['z'] * (1 + weight * 0.01)  # 重量越大，对稳定性影响越大
            
            # 容量限制惩罚
            if used_volume > container_volume:
                capacity_penalty = (used_volume - container_volume) * 10  # 超出容量的惩罚
            
            # 检查重叠
            for i in range(len(valid_cargoes)):
                info1 = cargo_info[i]
                l1 = info1['length']
                w1 = info1['width']
                h1 = info1['height']
                pos1 = solution[i]
                
                for j in range(i + 1, len(valid_cargoes)):
                    info2 = cargo_info[j]
                    l2 = info2['length']
                    w2 = info2['width']
                    h2 = info2['height']
                    pos2 = solution[j]
                    
                    # 检查是否重叠
                    if not (pos1['x'] + l1 <= pos2['x'] or pos2['x'] + l2 <= pos1['x'] or
                            pos1['y'] + w1 <= pos2['y'] or pos2['y'] + w2 <= pos1['y'] or
                            pos1['z'] + h1 <= pos2['z'] or pos2['z'] + h2 <= pos1['z']):
                        overlap_penalty += 20  # 重叠惩罚
            
            # 检查装柜规则
            for i, (cargo, pos) in enumerate(zip(valid_cargoes, solution)):
                info = cargo_info[i]
                length = info['length']
                width = info['width']
                height = info['height']
                weight = info['weight']
                bottom_only = info['bottom_only']
                top_placement = info['top_placement']
                can_bear_weight = info['can_bear_weight']
                self_stack = info['self_stack']
                packaging_status = info['packaging_status']
                placement_requirement = info['placement_requirement']
                orientation = info['orientation']
                
                # 1. 底层摆放限制
                if bottom_only:
                    if pos['z'] > 0.1:  # 超过10cm
                        rule_penalty += 15
                
                # 2. 顶层摆放限制
                if top_placement == '是':
                    if pos['z'] < self.container_height - height - 0.1:  # 低于顶部10cm
                        rule_penalty += 15
                
                # 3. 货物在集装箱内
                if (pos['x'] + length > self.container_length or
                    pos['y'] + width > self.container_width or
                    pos['z'] + height > self.container_height):
                    rule_penalty += 25
                
                # 4. 不可承重货物摆放在其他货物上方或单独摆放
                if not can_bear_weight:
                    # 检查是否在其他货物上方
                    for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                        if i != j:
                            other_info = cargo_info[j]
                            other_height = other_info['height']
                            if pos['z'] < other_pos['z'] + other_height:
                                rule_penalty += 15
                
                # 5. 自叠限制
                if self_stack == '否':
                    # 检查是否在其他货物上方
                    for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                        if i != j:
                            other_info = cargo_info[j]
                            other_height = other_info['height']
                            if pos['z'] < other_pos['z'] + other_height:
                                rule_penalty += 15
                
                # 6. 包装状态为破损或变形货物只允许摆放在其他货物上方或单独摆放
                if isinstance(packaging_status, str) and ('破损' in packaging_status or '变形' in packaging_status):
                    # 检查是否在其他货物上方
                    for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                        if i != j:
                            other_info = cargo_info[j]
                            other_height = other_info['height']
                            if pos['z'] < other_pos['z'] + other_height:
                                rule_penalty += 15
                
                # 7. 重量限制检查
                if weight > 20000:  # 假设集装箱最大承重20吨
                    rule_penalty += 20
                
                # 8. 码放要求检查
                if isinstance(placement_requirement, str):
                    if placement_requirement == '正放':
                        # 只允许正放（封箱口朝上）
                        if orientation not in ['upright']:
                            rule_penalty += 10
                    elif placement_requirement == '正放&侧放':
                        # 只允许正放和侧放
                        if orientation not in ['upright', 'side']:
                            rule_penalty += 10
                    elif placement_requirement == '正放&立放':
                        # 只允许正放和立放
                        if orientation not in ['upright', 'upright_rotated']:
                            rule_penalty += 10
            
            # 计算空间利用率
            volume_ratio = used_volume / container_volume
            
            # 计算货物之间的紧密程度奖励（确保货物贴在一起，没有空隙）
            compactness_reward = 0
            if len(valid_cargoes) > 1:
                for i in range(len(valid_cargoes)):
                    info1 = cargo_info[i]
                    l1 = info1['length']
                    w1 = info1['width']
                    h1 = info1['height']
                    pos1 = solution[i]
                    
                    for j in range(len(valid_cargoes)):
                        if i != j:
                            info2 = cargo_info[j]
                            l2 = info2['length']
                            w2 = info2['width']
                            h2 = info2['height']
                            pos2 = solution[j]
                            
                            # 计算货物之间的距离（确保贴在一起）
                            dx = max(0, pos1['x'] + l1 - pos2['x'], pos2['x'] + l2 - pos1['x'])
                            dy = max(0, pos1['y'] + w1 - pos2['y'], pos2['y'] + w2 - pos1['y'])
                            dz = max(0, pos1['z'] + h1 - pos2['z'], pos2['z'] + h2 - pos1['z'])
                            
                            # 距离越小，奖励越高，鼓励货物贴在一起
                            distance = dx + dy + dz
                            if distance < 0.01:  # 几乎贴在一起
                                compactness_reward += 50  # 最高奖励
                            elif distance < 0.05:  # 非常接近
                                compactness_reward += (0.05 - distance) * 1000
                            elif distance < 0.1:  # 接近
                                compactness_reward += (0.1 - distance) * 500
                            elif distance < 0.2:  # 较接近
                                compactness_reward += (0.2 - distance) * 100
            
            # 计算重心平衡惩罚
            if total_weight > 0:
                center_of_gravity_x = weighted_x / total_weight
                center_of_gravity_y = weighted_y / total_weight
                center_of_gravity_z = weighted_z / total_weight
                
                # 理想重心位置
                ideal_cog_x = self.container_length / 2
                ideal_cog_y = self.container_width / 2
                ideal_cog_z = self.container_height / 3  # 理想重心偏低
                
                # 计算重心偏移
                cog_offset_x = abs(center_of_gravity_x - ideal_cog_x)
                cog_offset_y = abs(center_of_gravity_y - ideal_cog_y)
                cog_offset_z = abs(center_of_gravity_z - ideal_cog_z)
                
                # 重心偏移惩罚
                center_of_gravity_penalty = (cog_offset_x + cog_offset_y + cog_offset_z * 2) * 2  # 高度方向偏移惩罚更重
            
            # 计算重量平衡惩罚
            # 检查每层的重量分布
            layers = {}
            for i, (cargo, pos) in enumerate(zip(valid_cargoes, solution)):
                info = cargo_info[i]
                weight = info['weight']
                layer = int(pos['z'] / 0.5)  # 每0.5米为一层
                if layer not in layers:
                    layers[layer] = 0
                layers[layer] += weight
            
            # 计算各层重量差异
            if layers:
                max_weight = max(layers.values())
                min_weight = min(layers.values())
                if max_weight > 0:
                    weight_balance_penalty = (max_weight - min_weight) / max_weight * 10
            
            # 综合适应度
            fitness = volume_ratio * 1000  # 空间利用率权重最高
            fitness += compactness_reward * 20  # 增加紧密排列奖励权重
            fitness -= overlap_penalty  # 重叠惩罚
            fitness -= rule_penalty  # 规则违反惩罚
            fitness -= stability_score * 0.01  # 稳定性评分（越低越好）
            fitness -= capacity_penalty * 0.001  # 容量超出惩罚（降低权重）
            fitness -= center_of_gravity_penalty  # 重心平衡惩罚
            fitness -= weight_balance_penalty  # 重量平衡惩罚
            
            return fitness
        
        # 智能初始化策略 - 从起点靠墙开始摆放，先满足宽，再满足高，最后满足长度
        def initialize_solution():
            """智能初始化解决方案 - 从起点靠墙开始摆放，先满足宽，再满足高，最后满足长度"""
            solution = []
            
            # 更智能的货物排序策略：按体积和形状因子排序
            def calculate_shape_factor(cargo):
                try:
                    length = float(cargo.get('length', 0.1))
                    width = float(cargo.get('width', 0.1))
                    height = float(cargo.get('height', 0.1))
                    volume = length * width * height
                    # 形状因子：越接近立方体，形状因子越大
                    shape_factor = (length * width * height) ** (1/3) / max(length, width, height)
                    # 优先考虑体积大且形状规则的货物
                    return volume * shape_factor
                except (ValueError, TypeError):
                    return 0
            
            # 按体积和形状因子排序，先放大型、形状规则的货物
            sorted_cargoes = sorted(valid_cargoes, key=calculate_shape_factor, reverse=True)
            
            # 记录已放置的货物位置
            placed_positions = []
            
            # 从起点（x=0, y=0, z=0）开始摆放
            # 按照先宽后高再长度的顺序
            
            for i, cargo in enumerate(sorted_cargoes):
                try:
                    length = float(cargo.get('length', 0.1))
                    width = float(cargo.get('width', 0.1))
                    height = float(cargo.get('height', 0.1))
                except (ValueError, TypeError):
                    length = 0.1
                    width = 0.1
                    height = 0.1
                
                # 尝试找到合适的位置 - 从起点靠墙开始，先满足宽，再满足高，最后满足长度
                best_position = None
                
                # 检查当前位置是否可以放置
                def check_position(x, y, z):
                    # 检查是否在集装箱内
                    if (x + length > self.container_length or
                        y + width > self.container_width or
                        z + height > self.container_height):
                        return False
                    
                    # 检查是否与已放置货物重叠
                    for placed_cargo, placed_pos in placed_positions:
                        try:
                            pl = float(placed_cargo.get('length', 0.1))
                            pw = float(placed_cargo.get('width', 0.1))
                            ph = float(placed_cargo.get('height', 0.1))
                            
                            if not (x + length <= placed_pos['x'] or placed_pos['x'] + pl <= x or
                                    y + width <= placed_pos['y'] or placed_pos['y'] + pw <= y or
                                    z + height <= placed_pos['z'] or placed_pos['z'] + ph <= z):
                                return False
                        except (ValueError, TypeError):
                            continue
                    return True
                
                # 1. 第一个货物必须放在起点（x=0, y=0, z=0）
                if i == 0:
                    # 强制放在起点位置
                    best_position = {'x': 0, 'y': 0, 'z': 0}
                    # 确保起点位置有效
                    try:
                        length = float(cargo.get('length', 0.1))
                        width = float(cargo.get('width', 0.1))
                        height = float(cargo.get('height', 0.1))
                        # 检查是否在集装箱内
                        if (length > self.container_length or
                            width > self.container_width or
                            height > self.container_height):
                            # 如果货物太大，使用网格搜索
                            found = False
                            for y in range(int(self.container_width / 0.1) + 1):
                                y_pos = y * 0.1
                                for z in range(int(self.container_height / 0.1) + 1):
                                    z_pos = z * 0.1
                                    for x in range(int(self.container_length / 0.1) + 1):
                                        x_pos = x * 0.1
                                        if check_position(x_pos, y_pos, z_pos):
                                            best_position = {'x': x_pos, 'y': y_pos, 'z': z_pos}
                                            found = True
                                            break
                                    if found:
                                        break
                                if found:
                                    break
                    except (ValueError, TypeError):
                        pass
                else:
                    # 2. 后续货物按照先宽后高再长度的顺序排列
                    # 遍历所有已放置的货物，尝试在其旁边放置
                    found = False
                    # 按先宽后高再长度的顺序尝试
                    # 先尝试宽度方向（y轴）
                    for placed_cargo, placed_pos in placed_positions:
                        try:
                            pl = float(placed_cargo.get('length', 0.1))
                            pw = float(placed_cargo.get('width', 0.1))
                            ph = float(placed_cargo.get('height', 0.1))
                            
                            # 尝试在宽度方向（右侧）放置
                            x = placed_pos['x']
                            y = placed_pos['y'] + pw
                            z = placed_pos['z']
                            if check_position(x, y, z):
                                best_position = {'x': x, 'y': y, 'z': z}
                                found = True
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    # 如果宽度方向没有位置，尝试高度方向（z轴）
                    if not found:
                        for placed_cargo, placed_pos in placed_positions:
                            try:
                                pl = float(placed_cargo.get('length', 0.1))
                                pw = float(placed_cargo.get('width', 0.1))
                                ph = float(placed_cargo.get('height', 0.1))
                                
                                # 尝试在高度方向（上方）放置
                                x = placed_pos['x']
                                y = placed_pos['y']
                                z = placed_pos['z'] + ph
                                if check_position(x, y, z):
                                    best_position = {'x': x, 'y': y, 'z': z}
                                    found = True
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    # 如果高度方向没有位置，尝试长度方向（x轴）
                    if not found:
                        for placed_cargo, placed_pos in placed_positions:
                            try:
                                pl = float(placed_cargo.get('length', 0.1))
                                pw = float(placed_cargo.get('width', 0.1))
                                ph = float(placed_cargo.get('height', 0.1))
                                
                                # 尝试在长度方向（后侧）放置
                                x = placed_pos['x'] + pl
                                y = placed_pos['y']
                                z = placed_pos['z']
                                if check_position(x, y, z):
                                    best_position = {'x': x, 'y': y, 'z': z}
                                    found = True
                                    break
                            except (ValueError, TypeError):
                                continue
                    
                    # 3. 如果仍然找不到位置，使用网格搜索
                    if not best_position:
                        grid_size = 0.1
                        for y in range(int(self.container_width / grid_size) + 1):
                            y_pos = y * grid_size
                            for z in range(int(self.container_height / grid_size) + 1):
                                z_pos = z * grid_size
                                for x in range(int(self.container_length / grid_size) + 1):
                                    x_pos = x * grid_size
                                    if check_position(x_pos, y_pos, z_pos):
                                        best_position = {'x': x_pos, 'y': y_pos, 'z': z_pos}
                                        found = True
                                        break
                                if found:
                                    break
                            if found:
                                break
                    
                    # 4. 如果仍然找不到位置，随机放置
                    if not best_position:
                        # 随机生成位置
                        x = np.random.uniform(0, max(0.1, self.container_length - length))
                        y = np.random.uniform(0, max(0.1, self.container_width - width))
                        z = np.random.uniform(0, max(0.1, self.container_height - height))
                        best_position = {'x': x, 'y': y, 'z': z}
                
                # 放置货物
                solution.append(best_position)
                placed_positions.append((cargo, best_position))
            
            # 恢复原始顺序
            original_order_solution = []
            cargo_to_pos = {}
            for cargo, pos in zip(sorted_cargoes, solution):
                # 使用货物的id作为键，确保唯一性
                cargo_id = cargo.get('id', str(id(cargo)))
                cargo_to_pos[cargo_id] = pos
            
            for cargo in valid_cargoes:
                cargo_id = cargo.get('id', str(id(cargo)))
                original_order_solution.append(cargo_to_pos.get(cargo_id, {'x': 0, 'y': 0, 'z': 0}))
            
            return original_order_solution
        
        # 初始化种群
        population = []
        for _ in range(population_size):
            solution = initialize_solution()
            population.append(solution)
        
        # 进化
        best_fitness_history = []
        convergence_counter = 0
        convergence_threshold = 10  # 连续10代适应度无显著变化则收敛
        fitness_improvement_threshold = 0.1  # 适应度改进阈值
        
        for gen in range(generations):
            # 计算适应度
            fitnesses = [calculate_fitness(sol) for sol in population]
            
            # 选择（精英选择 + 轮盘赌选择 + 锦标赛选择）
            # 精英保留 - 保留最优10个
            elite_size = 10
            sorted_population = [x for _, x in sorted(zip(fitnesses, population), key=lambda pair: pair[0], reverse=True)]
            elites = sorted_population[:elite_size]
            
            # 轮盘赌选择 + 锦标赛选择结合
            remaining_size = population_size - elite_size
            selected = []
            
            # 锦标赛选择
            tournament_size = 5
            for _ in range(remaining_size):
                # 随机选择锦标赛参与者
                tournament_indices = np.random.choice(range(len(population)), size=tournament_size, replace=False)
                # 选择锦标赛中的最佳个体
                tournament_fitnesses = [fitnesses[i] for i in tournament_indices]
                best_idx = tournament_indices[np.argmax(tournament_fitnesses)]
                selected.append(population[best_idx])
            
            # 交叉 - 多种交叉策略
            new_population = elites.copy()
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    parent1, parent2 = selected[i], selected[i+1]
                    # 交叉率设为0.7
                    if np.random.random() < 0.7:  # 交叉率
                        # 随机选择交叉策略
                        crossover_strategy = np.random.choice(['single_point', 'two_point', 'uniform'])
                        
                        if crossover_strategy == 'single_point':
                            # 单点交叉
                            crossover_point = np.random.randint(1, len(valid_cargoes) - 1)
                            child1 = parent1[:crossover_point] + parent2[crossover_point:]
                            child2 = parent2[:crossover_point] + parent1[crossover_point:]
                        elif crossover_strategy == 'two_point':
                            # 两点交叉
                            point1 = np.random.randint(1, len(valid_cargoes) - 1)
                            point2 = np.random.randint(point1 + 1, len(valid_cargoes))
                            child1 = parent1[:point1] + parent2[point1:point2] + parent1[point2:]
                            child2 = parent2[:point1] + parent1[point1:point2] + parent2[point2:]
                        else:
                            # 均匀交叉
                            child1, child2 = [], []
                            for j in range(len(valid_cargoes)):
                                if np.random.random() < 0.5:
                                    child1.append(parent1[j])
                                    child2.append(parent2[j])
                                else:
                                    child1.append(parent2[j])
                                    child2.append(parent1[j])
                        
                        new_population.extend([child1, child2])
            
            # 变异 - 多种变异策略
            for sol in new_population[elite_size:]:  # 精英不变异
                for i, pos in enumerate(sol):
                    if np.random.random() < 0.2:  # 增加变异率
                        info = cargo_info[i]
                        length = info['length']
                        width = info['width']
                        height = info['height']
                        
                        # 随机选择变异策略
                        mutation_strategy = np.random.choice(['local_search', 'random_mutation', 'neighbor_mutation'])
                        
                        if mutation_strategy == 'local_search':
                            # 局部搜索变异 - 尝试多个位置
                            best_score = -float('inf')
                            best_new_pos = pos.copy()
                            
                            # 生成多个候选位置
                            candidate_positions = []
                            # 围绕当前位置生成候选
                            for _ in range(15):  # 减少候选位置数量，提高效率
                                dx = np.random.normal(0, 0.3)
                                dy = np.random.normal(0, 0.3)
                                dz = np.random.normal(0, 0.3)
                                new_x = max(0, min(self.container_length - length, pos['x'] + dx))
                                new_y = max(0, min(self.container_width - width, pos['y'] + dy))
                                new_z = max(0, min(self.container_height - height, pos['z'] + dz))
                                candidate_positions.append({'x': new_x, 'y': new_y, 'z': new_z})
                            
                            # 评估候选位置
                            for new_pos_candidate in candidate_positions:
                                # 检查是否与其他货物重叠
                                overlap = False
                                for j, other_pos in enumerate(sol):
                                    if i != j:
                                        other_info = cargo_info[j]
                                        ol = other_info['length']
                                        ow = other_info['width']
                                        oh = other_info['height']
                                        
                                        if not (new_pos_candidate['x'] + length <= other_pos['x'] or other_pos['x'] + ol <= new_pos_candidate['x'] or
                                                new_pos_candidate['y'] + width <= other_pos['y'] or other_pos['y'] + ow <= new_pos_candidate['y'] or
                                                new_pos_candidate['z'] + height <= other_pos['z'] or other_pos['z'] + oh <= new_pos_candidate['z']):
                                            overlap = True
                                            break
                                
                                if not overlap:
                                    # 计算位置得分
                                    score = 0
                                    # 1. 空间利用率得分
                                    center_x = self.container_length / 2
                                    center_y = self.container_width / 2
                                    center_z = self.container_height / 2
                                    distance_to_center = ((new_pos_candidate['x'] + length/2 - center_x) ** 2 +
                                                        (new_pos_candidate['y'] + width/2 - center_y) ** 2 +
                                                        (new_pos_candidate['z'] + height/2 - center_z) ** 2) ** 0.5
                                    max_distance = ((center_x) ** 2 + (center_y) ** 2 + (center_z) ** 2) ** 0.5
                                    space_score = 1 - (distance_to_center / max_distance)
                                    
                                    # 2. 紧密程度得分
                                    compactness_score = 0
                                    for j, other_pos in enumerate(sol):
                                        if i != j:
                                            other_info = cargo_info[j]
                                            ol = other_info['length']
                                            ow = other_info['width']
                                            oh = other_info['height']
                                            
                                            dx = max(0, other_pos['x'] + ol - new_pos_candidate['x'], new_pos_candidate['x'] + length - other_pos['x'])
                                            dy = max(0, other_pos['y'] + ow - new_pos_candidate['y'], new_pos_candidate['y'] + width - other_pos['y'])
                                            dz = max(0, other_pos['z'] + oh - new_pos_candidate['z'], new_pos_candidate['z'] + height - other_pos['z'])
                                            dist = dx + dy + dz
                                            
                                            if dist < 0.5:
                                                compactness_score += (0.5 - dist) * 2
                                    
                                    score = space_score * 0.6 + compactness_score * 0.4
                                    
                                    if score > best_score:
                                        best_score = score
                                        best_new_pos = new_pos_candidate
                            
                            # 应用最佳位置
                            pos.update(best_new_pos)
                        
                        elif mutation_strategy == 'random_mutation':
                            # 随机变异
                            pos['x'] = np.random.uniform(0, max(0.1, self.container_length - length))
                            pos['y'] = np.random.uniform(0, max(0.1, self.container_width - width))
                            pos['z'] = np.random.uniform(0, max(0.1, self.container_height - height))
                        
                        else:
                            # 邻居变异 - 尝试在其他货物周围紧密排列
                            if len(valid_cargoes) > 1:
                                # 选择一个其他货物作为参考
                                other_indices = [j for j in range(len(valid_cargoes)) if j != i]
                                if other_indices:
                                    ref_index = other_indices[np.random.randint(len(other_indices))]
                                    ref_pos = sol[ref_index]
                                    ref_info = cargo_info[ref_index]
                                    ref_length = ref_info['length']
                                    ref_width = ref_info['width']
                                    ref_height = ref_info['height']
                                    
                                    # 尝试在参考货物的周围放置
                                    possible_positions = [
                                        # 右侧
                                        {'x': ref_pos['x'] + ref_length, 'y': ref_pos['y'], 'z': ref_pos['z']},
                                        # 后侧
                                        {'x': ref_pos['x'], 'y': ref_pos['y'] + ref_width, 'z': ref_pos['z']},
                                        # 上方
                                        {'x': ref_pos['x'], 'y': ref_pos['y'], 'z': ref_pos['z'] + ref_height}
                                    ]
                                    
                                    # 选择一个位置
                                    new_pos = possible_positions[np.random.randint(len(possible_positions))]
                                    pos['x'] = max(0, min(self.container_length - length, new_pos['x']))
                                    pos['y'] = max(0, min(self.container_width - width, new_pos['y']))
                                    pos['z'] = max(0, min(self.container_height - height, new_pos['z']))
                            else:
                                # 只有一个货物，随机变异
                                pos['x'] = max(0, min(self.container_length - length, pos['x'] + np.random.normal(0, 0.5)))
                                pos['y'] = max(0, min(self.container_width - width, pos['y'] + np.random.normal(0, 0.5)))
                                pos['z'] = max(0, min(self.container_height - height, pos['z'] + np.random.normal(0, 0.5)))
            
            # 保持种群大小并添加多样性
            # 确保种群多样性
            population = sorted(new_population, key=calculate_fitness, reverse=True)[:population_size]
            
            # 每5代引入新的随机个体，增加多样性
            if (gen + 1) % 5 == 0:
                # 替换适应度最低的2个个体
                if len(population) > 2:
                    new_individual = initialize_solution()
                    population[-1] = new_individual
            
            # 检查收敛
            best_fitness = max(fitnesses)
            best_fitness_history.append(best_fitness)
            
            if len(best_fitness_history) > 1:
                fitness_improvement = best_fitness_history[-1] - best_fitness_history[-2]
                if abs(fitness_improvement) < fitness_improvement_threshold:
                    convergence_counter += 1
                else:
                    convergence_counter = 0
            
            # 如果连续多代无显著改进，提前终止
            if convergence_counter >= convergence_threshold:
                print(f"  算法已收敛，提前终止于第 {gen + 1} 代")
                break
            
            # 每10代打印一次进度
            if (gen + 1) % 10 == 0:
                print(f"  第 {gen + 1} 代，最佳适应度: {best_fitness:.2f}")
        
        # 选择最优解
        best_solution = max(population, key=calculate_fitness)
        result = []
        for cargo, pos in zip(valid_cargoes, best_solution):
            result.append({
                **cargo,
                'position': pos
            })
        return result
