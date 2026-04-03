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
        
        # 按照装载顺序处理货物
        # 1. 固定组合模型
        fixed_combination = [c for c in valid_cargoes if c.get('is_fixed_combination', False)]
        # 2. 底层摆放货物
        bottom_only = [c for c in valid_cargoes if c.get('bottom_only', False)]
        # 3. 大货（长宽高均大于75cm）
        large_cargoes = [c for c in valid_cargoes if all(float(c.get(dim, 0)) > 0.75 for dim in ['length', 'width', 'height'])]
        # 4. 底层正放上层侧放货物
        bottom_upright_top_side = [c for c in valid_cargoes if c.get('bottom_upright_top_side', False)]
        # 5. 相同规格货物
        same_spec_cargoes = []
        # 6. 余量货物
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
        # 处理相同规格
        # 这里简化处理，实际需要根据规格分组
        # 处理余量
        for cargo in valid_cargoes:
            if cargo.get('id', str(id(cargo))) not in processed:
                remaining_cargoes.append(cargo)
        
        # 合并处理顺序
        processing_order = fixed_combination + bottom_only + large_cargoes + bottom_upright_top_side + same_spec_cargoes + remaining_cargoes
        
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
    
    def genetic_algorithm_optimization(self, cargoes, population_size=200, generations=500):
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
        
        # 改进的适应度函数
        def calculate_fitness(solution):
            """计算适应度（空间利用率 + 不重叠惩罚 + 规则遵守 + 稳定性 + 容量限制）"""
            used_volume = 0
            overlap_penalty = 0
            rule_penalty = 0
            stability_score = 0
            capacity_penalty = 0
            
            # 计算使用体积
            for cargo, pos in zip(valid_cargoes, solution):
                try:
                    length = float(cargo.get('length', 0.1))
                    width = float(cargo.get('width', 0.1))
                    height = float(cargo.get('height', 0.1))
                    used_volume += length * width * height
                    
                    # 稳定性评分：越低的货物稳定性越高
                    stability_score += pos['z'] * 0.1
                except (ValueError, TypeError):
                    continue
            
            # 容量限制惩罚
            if used_volume > container_volume:
                capacity_penalty = (used_volume - container_volume) * 10  # 超出容量的惩罚
            
            # 检查重叠
            for i in range(len(valid_cargoes)):
                for j in range(i + 1, len(valid_cargoes)):
                    cargo1 = valid_cargoes[i]
                    pos1 = solution[i]
                    cargo2 = valid_cargoes[j]
                    pos2 = solution[j]
                    
                    try:
                        l1 = float(cargo1.get('length', 0.1))
                        w1 = float(cargo1.get('width', 0.1))
                        h1 = float(cargo1.get('height', 0.1))
                        l2 = float(cargo2.get('length', 0.1))
                        w2 = float(cargo2.get('width', 0.1))
                        h2 = float(cargo2.get('height', 0.1))
                        
                        # 检查是否重叠
                        if not (pos1['x'] + l1 <= pos2['x'] or pos2['x'] + l2 <= pos1['x'] or
                                pos1['y'] + w1 <= pos2['y'] or pos2['y'] + w2 <= pos1['y'] or
                                pos1['z'] + h1 <= pos2['z'] or pos2['z'] + h2 <= pos1['z']):
                            overlap_penalty += 20  # 重叠惩罚
                    except (ValueError, TypeError):
                        continue
            
            # 检查装柜规则
            for i, (cargo, pos) in enumerate(zip(valid_cargoes, solution)):
                try:
                    # 1. 底层摆放限制
                    if cargo.get('bottom_only', False):
                        if pos['z'] > 0.5:  # 超过50cm
                            rule_penalty += 5
                    
                    # 2. 顶层摆放限制
                    if cargo.get('top_placement', '否') == '是':
                        if pos['z'] < self.container_height - 2.0:  # 低于上部200cm
                            rule_penalty += 5
                    
                    # 3. 货物在集装箱内
                    length = float(cargo.get('length', 0.1))
                    width = float(cargo.get('width', 0.1))
                    height = float(cargo.get('height', 0.1))
                    
                    if (pos['x'] + length > self.container_length or
                        pos['y'] + width > self.container_width or
                        pos['z'] + height > self.container_height):
                        rule_penalty += 10
                    
                    # 4. 托盘木箱只允许正放和正放旋转
                    packaging_type = cargo.get('packaging_type', '')
                    if isinstance(packaging_type, str) and ('托盘' in packaging_type or '木箱' in packaging_type):
                        # 这里简化处理，实际需要考虑旋转
                        pass
                    
                    # 5. 不可承重货物摆放在其他货物上方或单独摆放
                    if not cargo.get('can_bear_weight', True):
                        # 检查是否在其他货物上方
                        for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                            if i != j:
                                try:
                                    other_height = float(other_cargo.get('height', 0.1))
                                    if pos['z'] < other_pos['z'] + other_height:
                                        rule_penalty += 5
                                except (ValueError, TypeError):
                                    continue
                    
                    # 6. 自叠限制
                    if cargo.get('self_stack', '否') == '否':
                        # 检查是否在其他货物上方
                        for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                            if i != j:
                                try:
                                    other_height = float(other_cargo.get('height', 0.1))
                                    if pos['z'] < other_pos['z'] + other_height:
                                        rule_penalty += 5
                                except (ValueError, TypeError):
                                    continue
                    
                    # 7. 包装状态为破损或变形货物只允许摆放在其他货物上方或单独摆放
                    packaging_status = cargo.get('packaging_status', '')
                    if isinstance(packaging_status, str) and ('破损' in packaging_status or '变形' in packaging_status):
                        # 检查是否在其他货物上方
                        for j, (other_cargo, other_pos) in enumerate(zip(valid_cargoes, solution)):
                            if i != j:
                                try:
                                    other_height = float(other_cargo.get('height', 0.1))
                                    if pos['z'] < other_pos['z'] + other_height:
                                        rule_penalty += 5
                                except (ValueError, TypeError):
                                    continue
                    
                except (ValueError, TypeError):
                    continue
            
            # 计算空间利用率
            volume_ratio = used_volume / container_volume
            
            # 计算货物之间的紧密程度奖励
            compactness_reward = 0
            if len(valid_cargoes) > 1:
                for i in range(len(valid_cargoes)):
                    for j in range(i + 1, len(valid_cargoes)):
                        try:
                            cargo1 = valid_cargoes[i]
                            pos1 = solution[i]
                            cargo2 = valid_cargoes[j]
                            pos2 = solution[j]
                            
                            l1 = float(cargo1.get('length', 0.1))
                            w1 = float(cargo1.get('width', 0.1))
                            h1 = float(cargo1.get('height', 0.1))
                            l2 = float(cargo2.get('length', 0.1))
                            w2 = float(cargo2.get('width', 0.1))
                            h2 = float(cargo2.get('height', 0.1))
                            
                            # 计算货物之间的距离
                            dx = max(0, pos1['x'] + l1 - pos2['x'], pos2['x'] + l2 - pos1['x'])
                            dy = max(0, pos1['y'] + w1 - pos2['y'], pos2['y'] + w2 - pos1['y'])
                            dz = max(0, pos1['z'] + h1 - pos2['z'], pos2['z'] + h2 - pos1['z'])
                            
                            # 距离越小，奖励越高
                            distance = dx + dy + dz
                            if distance < 0.3:  # 距离小于0.3米
                                compactness_reward += (0.3 - distance) * 10  # 增加奖励权重
                            elif distance < 0.5:
                                compactness_reward += (0.5 - distance) * 5
                        except (ValueError, TypeError):
                            continue
            
            # 综合适应度
            fitness = volume_ratio * 100  # 空间利用率权重最高
            fitness += compactness_reward * 2  # 增加紧密排列奖励权重
            fitness -= overlap_penalty  # 重叠惩罚
            fitness -= rule_penalty  # 规则违反惩罚
            fitness -= stability_score  # 稳定性评分（越低越好）
            fitness -= capacity_penalty * 0.1  # 容量超出惩罚（降低权重）
            
            return fitness
        
        # 智能初始化策略 - 紧密排列
        def initialize_solution():
            """智能初始化解决方案 - 紧密排列"""
            solution = []
            
            # 按货物尺寸排序，先放大型货物
            sorted_cargoes = sorted(valid_cargoes, key=lambda c: float(c.get('length', 0.1)) * float(c.get('width', 0.1)) * float(c.get('height', 0.1)), reverse=True)
            
            # 记录已放置的货物位置
            placed_positions = []
            
            for cargo in sorted_cargoes:
                try:
                    length = float(cargo.get('length', 0.1))
                    width = float(cargo.get('width', 0.1))
                    height = float(cargo.get('height', 0.1))
                except (ValueError, TypeError):
                    length = 0.1
                    width = 0.1
                    height = 0.1
                
                # 尝试找到合适的位置 - 紧密排列策略
                max_attempts = 100  # 增加尝试次数
                best_position = None
                min_distance = float('inf')
                
                for _ in range(max_attempts):
                    # 基于规则的位置生成
                    if cargo.get('bottom_only', False):
                        # 底层货物 - 紧密排列
                        x = np.random.uniform(0, max(0.1, self.container_length - length))
                        y = np.random.uniform(0, max(0.1, self.container_width - width))
                        z = 0  # 直接放在底部
                    elif cargo.get('top_placement', '否') == '是':
                        # 顶层货物 - 紧密排列
                        x = np.random.uniform(0, max(0.1, self.container_length - length))
                        y = np.random.uniform(0, max(0.1, self.container_width - width))
                        z = self.container_height - height  # 直接放在顶部
                    else:
                        # 普通货物 - 尝试在已放置货物周围紧密排列
                        if placed_positions:
                            # 选择一个已放置的货物作为参考
                            ref_cargo, ref_pos = placed_positions[np.random.randint(len(placed_positions))]
                            ref_length = float(ref_cargo.get('length', 0.1))
                            ref_width = float(ref_cargo.get('width', 0.1))
                            ref_height = float(ref_cargo.get('height', 0.1))
                            
                            # 尝试在参考货物的右侧、后侧或上方放置
                            possible_positions = [
                                # 右侧
                                {'x': ref_pos['x'] + ref_length, 'y': ref_pos['y'], 'z': ref_pos['z']},
                                # 后侧
                                {'x': ref_pos['x'], 'y': ref_pos['y'] + ref_width, 'z': ref_pos['z']},
                                # 上方
                                {'x': ref_pos['x'], 'y': ref_pos['y'], 'z': ref_pos['z'] + ref_height}
                            ]
                            
                            # 随机选择一个位置
                            pos = possible_positions[np.random.randint(len(possible_positions))]
                            x = pos['x']
                            y = pos['y']
                            z = pos['z']
                        else:
                            # 第一个货物，放在角落
                            x = 0
                            y = 0
                            z = 0
                    
                    # 确保位置在集装箱内
                    x = max(0, min(x, self.container_length - length))
                    y = max(0, min(y, self.container_width - width))
                    z = max(0, min(z, self.container_height - height))
                    
                    # 检查是否与已放置货物重叠
                    overlap = False
                    for placed_cargo, placed_pos in placed_positions:
                        try:
                            pl = float(placed_cargo.get('length', 0.1))
                            pw = float(placed_cargo.get('width', 0.1))
                            ph = float(placed_cargo.get('height', 0.1))
                            
                            if not (x + length <= placed_pos['x'] or placed_pos['x'] + pl <= x or
                                    y + width <= placed_pos['y'] or placed_pos['y'] + pw <= y or
                                    z + height <= placed_pos['z'] or placed_pos['z'] + ph <= z):
                                overlap = True
                                break
                        except (ValueError, TypeError):
                            continue
                    
                    if not overlap:
                        # 计算与其他货物的最小距离
                        distance = float('inf')
                        for placed_cargo, placed_pos in placed_positions:
                            try:
                                pl = float(placed_cargo.get('length', 0.1))
                                pw = float(placed_cargo.get('width', 0.1))
                                ph = float(placed_cargo.get('height', 0.1))
                                
                                # 计算距离
                                dx = max(0, placed_pos['x'] + pl - x, x + length - placed_pos['x'])
                                dy = max(0, placed_pos['y'] + pw - y, y + width - placed_pos['y'])
                                dz = max(0, placed_pos['z'] + ph - z, z + height - placed_pos['z'])
                                dist = dx + dy + dz
                                if dist < distance:
                                    distance = dist
                            except (ValueError, TypeError):
                                continue
                        
                        # 选择距离最小的位置
                        if distance < min_distance:
                            min_distance = distance
                            best_position = {'x': x, 'y': y, 'z': z}
                
                if best_position:
                    solution.append(best_position)
                    placed_positions.append((cargo, best_position))
                else:
                    # 如果找不到合适位置，随机放置
                    x = np.random.uniform(0, max(0.1, self.container_length - length))
                    y = np.random.uniform(0, max(0.1, self.container_width - width))
                    z = np.random.uniform(0, max(0.1, self.container_height - height))
                    solution.append({'x': x, 'y': y, 'z': z})
            
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
        for gen in range(generations):
            # 计算适应度
            fitnesses = [calculate_fitness(sol) for sol in population]
            
            # 选择（精英选择 + 轮盘赌选择）
            # 精英保留 - 保留最优5个
            elite_size = 5
            sorted_population = [x for _, x in sorted(zip(fitnesses, population), key=lambda pair: pair[0], reverse=True)]
            elites = sorted_population[:elite_size]
            
            # 轮盘赌选择
            remaining_size = population_size - elite_size
            fitness_sum = sum(max(0, f) for f in fitnesses)
            if fitness_sum == 0:
                selected = sorted_population[elite_size:elite_size + remaining_size]
            else:
                probabilities = [max(0, f) / fitness_sum for f in fitnesses]
                selected_indices = np.random.choice(range(len(population)), size=remaining_size, p=probabilities)
                selected = [population[i] for i in selected_indices]
            
            # 交叉
            new_population = elites.copy()
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    parent1, parent2 = selected[i], selected[i+1]
                    # 交叉率设为0.65
                    if np.random.random() < 0.65:  # 交叉率
                        child1, child2 = [], []
                        
                        # 单点交叉
                        crossover_point = np.random.randint(1, len(valid_cargoes) - 1)
                        child1 = parent1[:crossover_point] + parent2[crossover_point:]
                        child2 = parent2[:crossover_point] + parent1[crossover_point:]
                        
                        new_population.extend([child1, child2])
            
            # 变异 - 紧密排列策略
            for sol in new_population[elite_size:]:  # 精英不变异
                for i, pos in enumerate(sol):
                    if np.random.random() < 0.15:  # 增加变异率
                        cargo = valid_cargoes[i]
                        try:
                            length = float(cargo.get('length', 0.1))
                            width = float(cargo.get('width', 0.1))
                            height = float(cargo.get('height', 0.1))
                        except (ValueError, TypeError):
                            length = 0.1
                            width = 0.1
                            height = 0.1
                        
                        # 智能变异 - 紧密排列
                        if cargo.get('bottom_only', False):
                            # 底层货物变异 - 尝试紧密排列
                            pos['x'] = np.random.uniform(0, max(0.1, self.container_length - length))
                            pos['y'] = np.random.uniform(0, max(0.1, self.container_width - width))
                            pos['z'] = 0  # 直接放在底部
                        elif cargo.get('top_placement', '否') == '是':
                            # 顶层货物变异 - 尝试紧密排列
                            pos['x'] = np.random.uniform(0, max(0.1, self.container_length - length))
                            pos['y'] = np.random.uniform(0, max(0.1, self.container_width - width))
                            pos['z'] = self.container_height - height  # 直接放在顶部
                        else:
                            # 普通货物变异 - 尝试在其他货物周围紧密排列
                            if len(valid_cargoes) > 1:
                                # 选择一个其他货物作为参考
                                other_indices = [j for j in range(len(valid_cargoes)) if j != i]
                                if other_indices:
                                    ref_index = other_indices[np.random.randint(len(other_indices))]
                                    ref_cargo = valid_cargoes[ref_index]
                                    ref_pos = sol[ref_index]
                                    try:
                                        ref_length = float(ref_cargo.get('length', 0.1))
                                        ref_width = float(ref_cargo.get('width', 0.1))
                                        ref_height = float(ref_cargo.get('height', 0.1))
                                        
                                        # 尝试在参考货物的右侧、后侧或上方放置
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
                                    except (ValueError, TypeError):
                                        # 如果失败，使用随机变异
                                        pos['x'] = max(0, min(self.container_length - length, pos['x'] + np.random.normal(0, 0.5)))
                                        pos['y'] = max(0, min(self.container_width - width, pos['y'] + np.random.normal(0, 0.5)))
                                        pos['z'] = max(0, min(self.container_height - height, pos['z'] + np.random.normal(0, 0.5)))
                            else:
                                # 只有一个货物，随机变异
                                pos['x'] = max(0, min(self.container_length - length, pos['x'] + np.random.normal(0, 0.5)))
                                pos['y'] = max(0, min(self.container_width - width, pos['y'] + np.random.normal(0, 0.5)))
                                pos['z'] = max(0, min(self.container_height - height, pos['z'] + np.random.normal(0, 0.5)))
            
            # 保持种群大小
            population = sorted(new_population, key=calculate_fitness, reverse=True)[:population_size]
            
            # 每10代打印一次进度
            if (gen + 1) % 10 == 0:
                best_fitness = max(fitnesses)
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
