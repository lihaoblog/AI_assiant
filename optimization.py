import numpy as np
from typing import List, Dict, Tuple, Optional
from ortools.sat.python import cp_model
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
    """装柜优化计算核心模块 - 参考装箱大师等主流装柜软件算法"""
    
    def __init__(self, container_length, container_width, container_height):
        self.container_length = container_length
        self.container_width = container_width
        self.container_height = container_height
        self.rotation_cache = {}  # 旋转结果缓存
    
    def get_rotated_dimensions(self, length: float, width: float, height: float, rotation_type: RotationType) -> Tuple[float, float, float]:
        """
        获取旋转后的尺寸
        :param length: 原始长度
        :param width: 原始宽度
        :param height: 原始高度
        :param rotation_type: 旋转类型
        :return: 旋转后的(长度, 宽度, 高度)
        """
        cache_key = (length, width, height, rotation_type.value)
        if cache_key in self.rotation_cache:
            return self.rotation_cache[cache_key]
        
        if rotation_type == RotationType.RT_WHD:
            result = (length, width, height)
        elif rotation_type == RotationType.RT_HWD:
            result = (width, length, height)
        elif rotation_type == RotationType.RT_HDW:
            result = (height, length, width)
        elif rotation_type == RotationType.RT_DHW:
            result = (height, width, length)
        elif rotation_type == RotationType.RT_DWH:
            result = (width, height, length)
        else:  # RT_WDH
            result = (length, height, width)
        
        self.rotation_cache[cache_key] = result
        return result
    
    def optimize_loading(self, cargoes):
        """
        使用混合算法（启发式+遗传算法）优化装柜
        :param cargoes: 货物列表
        :return: 优化后的装载方案和未装载的货物
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
        
        container_volume = self.container_length * self.container_width * self.container_height
        
        # 货物分类和排序
        sorted_cargoes = self._categorize_and_sort_cargoes(valid_cargoes)
        
        # 使用混合算法优化
        print("使用混合算法优化装柜...")
        result = self._hybrid_algorithm_optimization(sorted_cargoes, container_volume)
        
        # 容量限制后处理
        result = self.apply_volume_limit(result, container_volume)
        
        # 计算未装载的货物
        loaded_ids = {c.get('id', str(id(c))) for c in result}
        unloaded = [c for c in valid_cargoes if c.get('id', str(id(c))) not in loaded_ids]
        if unloaded:
            print(f"有 {len(unloaded)} 件货物未装载（超出容量）")
        
        return result
    
    def _categorize_and_sort_cargoes(self, cargoes: List[Dict]) -> List[Dict]:
        """
        货物分类和排序 - 参考装箱大师规则
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
    
    def _hybrid_algorithm_optimization(self, cargoes: List[Dict], container_volume: float, population_size: int = 150, generations: int = 300) -> List[Dict]:
        """
        混合算法优化 - 结合启发式算法和遗传算法
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
        
        cargo_info = self._preprocess_cargo_info(valid_cargoes)
        
        # 适应度函数
        def calculate_fitness(solution):
            return self._calculate_multi_objective_fitness(solution, valid_cargoes, cargo_info, container_volume)
        
        # 初始化种群 - 使用启发式算法
        population = []
        for _ in range(population_size):
            solution = self._heuristic_initialization(valid_cargoes, cargo_info)
            population.append(solution)
        
        # 遗传算法进化
        best_fitness_history = []
        convergence_counter = 0
        convergence_threshold = 10
        
        for gen in range(generations):
            fitnesses = [calculate_fitness(sol) for sol in population]
            
            # 精英保留
            elite_size = 10
            sorted_population = [x for _, x in sorted(zip(fitnesses, population), key=lambda pair: pair[0], reverse=True)]
            elites = sorted_population[:elite_size]
            
            # 锦标赛选择
            selected = []
            tournament_size = 5
            for _ in range(population_size - elite_size):
                tournament_indices = np.random.choice(range(len(population)), size=tournament_size, replace=False)
                tournament_fitnesses = [fitnesses[i] for i in tournament_indices]
                best_idx = tournament_indices[np.argmax(tournament_fitnesses)]
                selected.append(population[best_idx])
            
            # 交叉
            new_population = elites.copy()
            for i in range(0, len(selected), 2):
                if i + 1 < len(selected):
                    parent1, parent2 = selected[i], selected[i+1]
                    if np.random.random() < 0.7:
                        child1, child2 = self._crossover(parent1, parent2, valid_cargoes)
                        new_population.extend([child1, child2])
            
            # 变异
            for sol in new_population[elite_size:]:
                if np.random.random() < 0.2:
                    self._mutation(sol, valid_cargoes, cargo_info)
            
            # 保持种群大小
            population = sorted(new_population, key=calculate_fitness, reverse=True)[:population_size]
            
            # 每5代引入新的启发式个体
            if (gen + 1) % 5 == 0 and len(population) > 2:
                new_individual = self._heuristic_initialization(valid_cargoes, cargo_info)
                population[-1] = new_individual
            
            # 检查收敛
            best_fitness = max(fitnesses)
            best_fitness_history.append(best_fitness)
            
            if len(best_fitness_history) > 1:
                fitness_improvement = best_fitness_history[-1] - best_fitness_history[-2]
                if abs(fitness_improvement) < 0.1:
                    convergence_counter += 1
                else:
                    convergence_counter = 0
            
            if convergence_counter >= convergence_threshold:
                print(f"  算法已收敛，提前终止于第 {gen + 1} 代")
                break
            
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
    
    def _preprocess_cargo_info(self, cargoes: List[Dict]) -> List[Dict]:
        """预处理货物信息"""
        cargo_info = []
        for cargo in cargoes:
            try:
                length = float(cargo.get('length', 0.1))
                width = float(cargo.get('width', 0.1))
                height = float(cargo.get('height', 0.1))
                weight = float(cargo.get('weight', 0.1))
                volume = length * width * height
                
                cargo_info.append({
                    'length': length,
                    'width': width,
                    'height': height,
                    'weight': weight,
                    'volume': volume,
                    'bottom_only': cargo.get('bottom_only', False),
                    'top_placement': cargo.get('top_placement', '否'),
                    'can_bear_weight': cargo.get('can_bear_weight', True),
                    'self_stack': cargo.get('self_stack', '是'),
                    'packaging_status': cargo.get('packaging_status', ''),
                    'placement_requirement': cargo.get('code_placement_requirements', ''),
                    'orientation': cargo.get('orientation', '')
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
        return cargo_info
    
    def _calculate_multi_objective_fitness(self, solution, cargoes, cargo_info, container_volume):
        """
        计算多目标适应度 - 空间利用率 + 稳定性 + 重心平衡 + 紧密排列
        """
        used_volume = 0
        overlap_penalty = 0
        rule_penalty = 0
        stability_score = 0
        compactness_reward = 0
        width_priority_reward = 0
        height_priority_reward = 0
        length_priority_reward = 0
        
        total_weight = 0
        weighted_x = 0
        weighted_y = 0
        weighted_z = 0
        
        for i, (cargo, pos) in enumerate(zip(cargoes, solution)):
            info = cargo_info[i]
            length = info['length']
            width = info['width']
            height = info['height']
            weight = info['weight']
            volume = info['volume']
            
            used_volume += volume
            total_weight += weight
            
            cargo_center_x = pos['x'] + length / 2
            cargo_center_y = pos['y'] + width / 2
            cargo_center_z = pos['z'] + height / 2
            
            weighted_x += cargo_center_x * weight
            weighted_y += cargo_center_y * weight
            weighted_z += cargo_center_z * weight
            
            stability_score += pos['z'] * (1 + weight * 0.01)
            
            width_priority_reward += (1 - pos['y'] / self.container_width) * 50
            height_priority_reward += (1 - pos['z'] / self.container_height) * 30
            length_priority_reward += (1 - pos['x'] / self.container_length) * 20
        
        # 检查重叠
        for i in range(len(cargoes)):
            info1 = cargo_info[i]
            l1, w1, h1 = info1['length'], info1['width'], info1['height']
            pos1 = solution[i]
            
            for j in range(i + 1, len(cargoes)):
                info2 = cargo_info[j]
                l2, w2, h2 = info2['length'], info2['width'], info2['height']
                pos2 = solution[j]
                
                if not (pos1['x'] + l1 <= pos2['x'] or pos2['x'] + l2 <= pos1['x'] or
                        pos1['y'] + w1 <= pos2['y'] or pos2['y'] + w2 <= pos1['y'] or
                        pos1['z'] + h1 <= pos2['z'] or pos2['z'] + h2 <= pos1['z']):
                    overlap_penalty += 20
        
        # 检查装柜规则
        for i, (cargo, pos) in enumerate(zip(cargoes, solution)):
            info = cargo_info[i]
            length, width, height, weight = info['length'], info['width'], info['height'], info['weight']
            
            if info['bottom_only'] and pos['z'] > 0.1:
                rule_penalty += 15
            
            if info['top_placement'] == '是' and pos['z'] < self.container_height - height - 0.1:
                rule_penalty += 15
            
            if (pos['x'] + length > self.container_length or
                pos['y'] + width > self.container_width or
                pos['z'] + height > self.container_height):
                rule_penalty += 25
        
        # 计算紧密程度
        if len(cargoes) > 1:
            for i in range(len(cargoes)):
                info1 = cargo_info[i]
                l1, w1, h1 = info1['length'], info1['width'], info1['height']
                pos1 = solution[i]
                
                for j in range(len(cargoes)):
                    if i != j:
                        info2 = cargo_info[j]
                        l2, w2, h2 = info2['length'], info2['width'], info2['height']
                        pos2 = solution[j]
                        
                        dx = max(0, pos1['x'] + l1 - pos2['x'], pos2['x'] + l2 - pos1['x'])
                        dy = max(0, pos1['y'] + w1 - pos2['y'], pos2['y'] + w2 - pos1['y'])
                        dz = max(0, pos1['z'] + h1 - pos2['z'], pos2['z'] + h2 - pos1['z'])
                        
                        distance = dx + dy + dz
                        if distance < 0.01:
                            compactness_reward += 50
                        elif distance < 0.05:
                            compactness_reward += (0.05 - distance) * 1000
                        elif distance < 0.1:
                            compactness_reward += (0.1 - distance) * 500
                        elif distance < 0.2:
                            compactness_reward += (0.2 - distance) * 100
        
        # 计算重心平衡
        center_of_gravity_penalty = 0
        if total_weight > 0:
            cog_x = weighted_x / total_weight
            cog_y = weighted_y / total_weight
            cog_z = weighted_z / total_weight
            
            ideal_cog_x = self.container_length / 2
            ideal_cog_y = self.container_width / 2
            ideal_cog_z = self.container_height / 3
            
            cog_offset = abs(cog_x - ideal_cog_x) + abs(cog_y - ideal_cog_y) + abs(cog_z - ideal_cog_z) * 2
            center_of_gravity_penalty = cog_offset * 2
        
        # 综合适应度
        volume_ratio = used_volume / container_volume
        fitness = volume_ratio * 1000
        fitness += compactness_reward * 20
        fitness += width_priority_reward
        fitness += height_priority_reward
        fitness += length_priority_reward
        fitness -= overlap_penalty
        fitness -= rule_penalty
        fitness -= stability_score * 0.01
        fitness -= center_of_gravity_penalty
        
        return fitness
    
    def _heuristic_initialization(self, cargoes: List[Dict], cargo_info: List[Dict]) -> List[Dict]:
        """
        启发式初始化 - 参考装箱大师规则
        """
        solution = []
        placed_positions = []
        
        for i, cargo in enumerate(cargoes):
            info = cargo_info[i]
            length = info['length']
            width = info['width']
            height = info['height']
            
            best_position = None
            best_rotation = None
            best_score = -float('inf')
            
            # 尝试所有6种旋转方式
            for rotation_type in RotationType:
                rotated_l, rotated_w, rotated_h = self.get_rotated_dimensions(length, width, height, rotation_type)
                
                # 检查是否允许旋转
                if not self._is_rotation_allowed(cargo, rotation_type):
                    continue
                
                # 寻找最佳位置
                position, score = self._find_best_position(
                    rotated_l, rotated_w, rotated_h, placed_positions, cargoes, cargo_info, i
                )
                
                if position and score > best_score:
                    best_position = position
                    best_rotation = rotation_type
                    best_score = score
            
            if best_position:
                solution.append(best_position)
                placed_positions.append((cargo, best_position, best_rotation))
            else:
                # 如果找不到合适位置，随机放置
                x = np.random.uniform(0, max(0.1, self.container_length - length))
                y = np.random.uniform(0, max(0.1, self.container_width - width))
                z = np.random.uniform(0, max(0.1, self.container_height - height))
                solution.append({'x': x, 'y': y, 'z': z})
                placed_positions.append((cargo, {'x': x, 'y': y, 'z': z}, RotationType.RT_WHD))
        
        return solution
    
    def _is_rotation_allowed(self, cargo: Dict, rotation_type: RotationType) -> bool:
        """检查旋转是否允许"""
        placement_requirement = cargo.get('code_placement_requirements', '')
        if isinstance(placement_requirement, str):
            if placement_requirement == '正放':
                return rotation_type in [RotationType.RT_WHD, RotationType.RT_WDH]
            elif placement_requirement == '正放&侧放':
                return rotation_type in [RotationType.RT_WHD, RotationType.RT_WDH, RotationType.RT_HWD, RotationType.RT_DWH]
        return True
    
    def _find_best_position(self, length: float, width: float, height: float, 
                           placed_positions: List, cargoes: List[Dict], 
                           cargo_info: List[Dict], current_index: int) -> Tuple[Optional[Dict], float]:
        """寻找最佳放置位置"""
        best_position = None
        best_score = -float('inf')
        
        # 检查起点位置
        if self._check_position_valid(0, 0, 0, length, width, height, placed_positions):
            score = self._calculate_position_score(0, 0, 0, length, width, height, cargoes, cargo_info, current_index, placed_positions)
            if score > best_score:
                best_position = {'x': 0, 'y': 0, 'z': 0}
                best_score = score
        
        # 从已放置货物周围寻找位置
        for placed_cargo, placed_pos, _ in placed_positions:
            try:
                pl = float(placed_cargo.get('length', 0.1))
                pw = float(placed_cargo.get('width', 0.1))
                ph = float(placed_cargo.get('height', 0.1))
                
                # 宽度方向（右侧）- 优先
                if self._check_position_valid(placed_pos['x'], placed_pos['y'] + pw, placed_pos['z'], 
                                             length, width, height, placed_positions):
                    score = self._calculate_position_score(placed_pos['x'], placed_pos['y'] + pw, placed_pos['z'],
                                                          length, width, height, cargoes, cargo_info, current_index, placed_positions)
                    if score > best_score:
                        best_position = {'x': placed_pos['x'], 'y': placed_pos['y'] + pw, 'z': placed_pos['z']}
                        best_score = score
                
                # 高度方向（上方）- 次之
                if self._check_position_valid(placed_pos['x'], placed_pos['y'], placed_pos['z'] + ph,
                                             length, width, height, placed_positions):
                    score = self._calculate_position_score(placed_pos['x'], placed_pos['y'], placed_pos['z'] + ph,
                                                          length, width, height, cargoes, cargo_info, current_index, placed_positions)
                    if score > best_score:
                        best_position = {'x': placed_pos['x'], 'y': placed_pos['y'], 'z': placed_pos['z'] + ph}
                        best_score = score
                
                # 长度方向（后侧）- 最后
                if self._check_position_valid(placed_pos['x'] + pl, placed_pos['y'], placed_pos['z'],
                                             length, width, height, placed_positions):
                    score = self._calculate_position_score(placed_pos['x'] + pl, placed_pos['y'], placed_pos['z'],
                                                          length, width, height, cargoes, cargo_info, current_index, placed_positions)
                    if score > best_score:
                        best_position = {'x': placed_pos['x'] + pl, 'y': placed_pos['y'], 'z': placed_pos['z']}
                        best_score = score
            except (ValueError, TypeError):
                continue
        
        return best_position, best_score
    
    def _check_position_valid(self, x: float, y: float, z: float, 
                             length: float, width: float, height: float,
                             placed_positions: List) -> bool:
        """检查位置是否有效"""
        # 检查是否在集装箱内
        if (x + length > self.container_length or
            y + width > self.container_width or
            z + height > self.container_height):
            return False
        
        # 检查是否与已放置货物重叠
        for placed_cargo, placed_pos, _ in placed_positions:
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
    
    def _calculate_position_score(self, x: float, y: float, z: float,
                                  length: float, width: float, height: float,
                                  cargoes: List[Dict], cargo_info: List[Dict],
                                  current_index: int, placed_positions: List) -> float:
        """计算位置得分"""
        score = 0
        
        # 宽度方向得分（越靠近左侧越好）
        score += (1 - y / self.container_width) * 3
        
        # 高度方向得分（越靠近底部越好）
        score += (1 - z / self.container_height) * 2
        
        # 长度方向得分（越靠近前侧越好）
        score += (1 - x / self.container_length) * 1
        
        # 紧密程度得分
        compactness_score = 0
        for placed_cargo, placed_pos, _ in placed_positions:
            try:
                pl = float(placed_cargo.get('length', 0.1))
                pw = float(placed_cargo.get('width', 0.1))
                ph = float(placed_cargo.get('height', 0.1))
                
                # 计算距离
                dx = max(0, x + length - placed_pos['x'], placed_pos['x'] + pl - x)
                dy = max(0, y + width - placed_pos['y'], placed_pos['y'] + pw - y)
                dz = max(0, z + height - placed_pos['z'], placed_pos['z'] + ph - z)
                
                distance = dx + dy + dz
                if distance < 0.5:
                    compactness_score += (0.5 - distance) * 2
            except (ValueError, TypeError):
                continue
        
        score += compactness_score * 0.4
        
        return score
    
    def _crossover(self, parent1: List[Dict], parent2: List[Dict], cargoes: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """交叉操作"""
        if len(cargoes) < 2:
            return parent1.copy(), parent2.copy()
        
        crossover_point = np.random.randint(1, len(cargoes) - 1)
        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]
        
        return child1, child2
    
    def _mutation(self, solution: List[Dict], cargoes: List[Dict], cargo_info: List[Dict]):
        """变异操作"""
        if not solution:
            return
        
        i = np.random.randint(len(solution))
        info = cargo_info[i]
        length, width, height = info['length'], info['width'], info['height']
        
        # 随机选择变异策略
        mutation_type = np.random.choice(['local_search', 'random', 'neighbor'])
        
        if mutation_type == 'local_search':
            # 局部搜索 - 尝试多个候选位置
            best_score = -float('inf')
            best_pos = solution[i].copy()
            
            for _ in range(10):
                dx = np.random.normal(0, 0.3)
                dy = np.random.normal(0, 0.3)
                dz = np.random.normal(0, 0.3)
                
                new_x = max(0, min(self.container_length - length, solution[i]['x'] + dx))
                new_y = max(0, min(self.container_width - width, solution[i]['y'] + dy))
                new_z = max(0, min(self.container_height - height, solution[i]['z'] + dz))
                
                score = self._calculate_position_score(new_x, new_y, new_z, length, width, height,
                                                       cargoes, cargo_info, i, [])
                if score > best_score:
                    best_score = score
                    best_pos = {'x': new_x, 'y': new_y, 'z': new_z}
            
            solution[i] = best_pos
        
        elif mutation_type == 'random':
            # 随机变异
            solution[i]['x'] = np.random.uniform(0, max(0.1, self.container_length - length))
            solution[i]['y'] = np.random.uniform(0, max(0.1, self.container_width - width))
            solution[i]['z'] = np.random.uniform(0, max(0.1, self.container_height - height))
        
        else:
            # 邻居变异
            if len(cargoes) > 1:
                other_indices = [j for j in range(len(cargoes)) if j != i]
                if other_indices:
                    ref_index = other_indices[np.random.randint(len(other_indices))]
                    ref_pos = solution[ref_index]
                    ref_info = cargo_info[ref_index]
                    
                    possible_positions = [
                        {'x': ref_pos['x'] + ref_info['length'], 'y': ref_pos['y'], 'z': ref_pos['z']},
                        {'x': ref_pos['x'], 'y': ref_pos['y'] + ref_info['width'], 'z': ref_pos['z']},
                        {'x': ref_pos['x'], 'y': ref_pos['y'], 'z': ref_pos['z'] + ref_info['height']}
                    ]
                    
                    new_pos = possible_positions[np.random.randint(len(possible_positions))]
                    solution[i]['x'] = max(0, min(self.container_length - length, new_pos['x']))
                    solution[i]['y'] = max(0, min(self.container_width - width, new_pos['y']))
                    solution[i]['z'] = max(0, min(self.container_height - height, new_pos['z']))
    
    def apply_volume_limit(self, cargoes: List[Dict], container_volume: float) -> List[Dict]:
        """应用容量限制"""
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
        
        original_order = {c.get('id', str(id(c))): c for c in cargoes}
        result = [original_order[c.get('id', str(id(c)))] for c in result if c.get('id', str(id(c))) in original_order]
        
        return result
    
    def quick_adjust_loading(self, current_solution: List[Dict], additional_cargoes: List[Dict]) -> List[Dict]:
        """
        快速响应调整机制 - 支持追加货物时的快速重新计算
        :param current_solution: 当前装载方案
        :param additional_cargoes: 追加的货物
        :return: 调整后的装载方案
        """
        # 合并当前货物和追加货物
        all_cargoes = current_solution + additional_cargoes
        
        # 重新优化
        return self.optimize_loading(all_cargoes)
