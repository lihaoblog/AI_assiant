from rule_engine import RuleEngine
from config import CONTAINER_SIZES

class LoadingSystem:
    """装载系统类，实现装柜过程和顺序逻辑"""
    
    def __init__(self, container_type='20ft'):
        self.rule_engine = RuleEngine()
        self.container = CONTAINER_SIZES.get(container_type, CONTAINER_SIZES['20ft'])
        self.loaded_cargoes = []
        self.current_position = {'x': 0, 'y': 0, 'z': 0}
    
    def load_cargoes(self, cargoes):
        """执行装载过程"""
        print(f"=== 开始装柜，集装箱类型：{self.container}")
        
        # 1. 对固定组合模型进行处理
        fixed_combinations = [c for c in cargoes if c.get('is_fixed_combination', False)]
        self._process_fixed_combinations(fixed_combinations)
        
        # 2. 对只允许底层摆放的货物进行处理
        bottom_only = [c for c in cargoes if c.get('bottom_only', False)]
        self._process_bottom_only(bottom_only)
        
        # 3. 对大货进行处理
        large_cargoes = [c for c in cargoes if self.rule_engine.is_large_cargo(
            c.get('length', 0), c.get('width', 0), c.get('height', 0)
        )]
        self._process_large_cargoes(large_cargoes)
        
        # 4. 对底层正放上层侧放的货物进行处理
        bottom_upright_top_side = [c for c in cargoes if c.get('bottom_upright_top_side', False)]
        self._process_bottom_upright_top_side(bottom_upright_top_side)
        
        # 5. 对相同规格货物相邻摆放规则处理
        remaining_cargoes = [c for c in cargoes if c not in fixed_combinations + bottom_only + large_cargoes + bottom_upright_top_side]
        same_spec_groups = self.rule_engine.group_same_spec_cargoes(remaining_cargoes)
        self._process_same_spec_groups(same_spec_groups)
        
        # 6. 余量货物混合搭配处理
        final_remaining = [c for c in cargoes if c not in self.loaded_cargoes]
        self._process_remaining_mixed(final_remaining)
        
        print(f"=== 装柜完成，共装载 {len(self.loaded_cargoes)} 件货物")
        return self.loaded_cargoes
    
    def _process_fixed_combinations(self, cargoes):
        """处理固定组合模型"""
        if not cargoes:
            return
        
        print("=== 处理固定组合模型 ===")
        sorted_cargoes = self.rule_engine.sort_cargoes(cargoes, 'length')
        for cargo in sorted_cargoes:
            self._load_single_cargo(cargo)
    
    def _process_bottom_only(self, cargoes):
        """处理只允许底层摆放的货物"""
        if not cargoes:
            return
        
        print("=== 处理底层摆放货物 ===")
        sorted_cargoes = self.rule_engine.sort_cargoes(cargoes, 'width')
        for cargo in sorted_cargoes:
            # 重置z坐标为0，确保在底层
            self.current_position['z'] = 0
            self._load_single_cargo(cargo)
    
    def _process_large_cargoes(self, cargoes):
        """处理大货"""
        if not cargoes:
            return
        
        print("=== 处理大货 ===")
        sorted_cargoes = self.rule_engine.sort_cargoes(cargoes, 'length')
        for cargo in sorted_cargoes:
            self._load_single_cargo(cargo)
    
    def _process_bottom_upright_top_side(self, cargoes):
        """处理底层正放上层侧放的货物"""
        if not cargoes:
            return
        
        print("=== 处理底层正放上层侧放货物 ===")
        # 底层正放
        for cargo in cargoes:
            cargo['orientation'] = 'upright'
            self._load_single_cargo(cargo)
        
        # 上层侧放
        for cargo in cargoes:
            cargo['orientation'] = 'side'
            self._load_single_cargo(cargo)
    
    def _process_same_spec_groups(self, groups):
        """处理相同规格货物"""
        if not groups:
            return
        
        print("=== 处理相同规格货物 ===")
        for group in groups:
            sorted_group = self.rule_engine.sort_cargoes(group, 'width')
            for cargo in sorted_group:
                self._load_single_cargo(cargo)
    
    def _process_remaining_mixed(self, cargoes):
        """处理余量货物混合搭配"""
        if not cargoes:
            return
        
        print("=== 处理余量货物 ===")
        sorted_cargoes = self.rule_engine.sort_cargoes(cargoes, 'height')
        for cargo in sorted_cargoes:
            self._load_single_cargo(cargo)
    
    def _load_single_cargo(self, cargo):
        """装载单个货物"""
        # 验证摆放是否合法
        valid, message = self.rule_engine.validate_placement(cargo, self.current_position, self.container)
        if not valid:
            print(f"货物摆放失败：{message}")
            return
        
        # 记录装载信息
        cargo['position'] = self.current_position.copy()
        self.loaded_cargoes.append(cargo)
        print(f"装载货物：{cargo.get('name', '未知')} 到位置 {self.current_position}")
        
        # 更新当前位置（从箱头向箱尾，箱一侧到另一侧）
        length, width = cargo.get('length', 0), cargo.get('width', 0)
        self.current_position['y'] += width
        
        # 如果超出宽度，换行到下一列
        if self.current_position['y'] + width > self.container['width']:
            self.current_position['y'] = 0
            self.current_position['x'] += length
        
        # 如果超出长度，换层
        if self.current_position['x'] + length > self.container['length']:
            self.current_position['x'] = 0
            self.current_position['y'] = 0
            self.current_position['z'] += cargo.get('height', 0)
