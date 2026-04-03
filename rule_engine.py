from config import RULES_CONFIG

class RuleEngine:
    """规则引擎类，实现装柜系统的各种规则"""
    
    def __init__(self):
        self.rules_config = RULES_CONFIG
    
    def is_large_cargo(self, length, width, height):
        """判断是否为大货"""
        threshold = self.rules_config['large_cargo_threshold']
        return length > threshold and width > threshold and height > threshold
    
    def can_stack(self, cargo1, cargo2):
        """判断货物是否可以堆叠"""
        # 检查承重限制
        if not cargo2.get('can_bear_weight', True):
            return False
        
        # 检查包装状态
        packaging_status = cargo2.get('packaging_status', '')
        if isinstance(packaging_status, str) and packaging_status.lower() in ['破损', '变形']:
            return False
        
        # 检查自叠限制
        if cargo1.get('self_stack_only', False):
            return False
        
        return True
    
    def get_loading_priority(self, cargo):
        """获取货物装载优先级"""
        priority = 0
        
        # 固定组合模型优先
        if cargo.get('is_fixed_combination', False):
            priority += 100
        
        # 底层摆放优先
        if cargo.get('bottom_only', False):
            priority += 80
        
        # 大货优先
        if self.is_large_cargo(cargo.get('length', 0), cargo.get('width', 0), cargo.get('height', 0)):
            priority += 60
        
        # 底层正放上层侧放优先
        if cargo.get('bottom_upright_top_side', False):
            priority += 40
        
        return priority
    
    def sort_cargoes(self, cargoes, strategy='width'):
        """按照指定策略排序货物"""
        if strategy == 'width':
            return sorted(cargoes, key=lambda x: x.get('width', 0), reverse=True)
        elif strategy == 'length':
            return sorted(cargoes, key=lambda x: x.get('length', 0), reverse=True)
        elif strategy == 'height':
            return sorted(cargoes, key=lambda x: x.get('height', 0), reverse=True)
        else:
            return cargoes
    
    def validate_placement(self, cargo, position, container):
        """验证货物摆放是否合法"""
        # 检查尺寸是否符合
        length, width, height = cargo.get('length', 0), cargo.get('width', 0), cargo.get('height', 0)
        container_length, container_width, container_height = container['length'], container['width'], container['height']
        
        if position['x'] + length > container_length:
            return False, "货物长度超出集装箱"
        if position['y'] + width > container_width:
            return False, "货物宽度超出集装箱"
        if position['z'] + height > container_height:
            return False, "货物高度超出集装箱"
        
        # 检查托盘木箱摆放方式
        packaging_type = cargo.get('packaging_type', '')
        if isinstance(packaging_type, str) and packaging_type.lower() in ['托盘', '木箱']:
            allowed_orientations = ['upright', 'upright_rotated']
            if cargo.get('orientation', '') not in allowed_orientations:
                return False, "托盘木箱只允许正放和正放旋转"
        
        # 检查底层摆放限制
        if cargo.get('bottom_only', False) and position['z'] > 10:
            return False, "底层摆放货物必须靠近箱底"
        
        # 检查顶层摆放限制
        top_placement = cargo.get('top_placement', '否')
        if top_placement == '是' and position['z'] < container_height - height - 0.1:
            return False, "顶层摆放货物必须放在顶部或单独放一排"
        
        # 检查码放要求
        placement_requirement = cargo.get('code_placement_requirements', '')
        if isinstance(placement_requirement, str):
            if placement_requirement == '正放':
                # 只允许正放（封箱口朝上）
                if cargo.get('orientation', '') not in ['upright']:
                    return False, "货物必须正放（封箱口朝上）"
            elif placement_requirement == '正放&侧放':
                # 只允许正放和侧放
                if cargo.get('orientation', '') not in ['upright', 'side']:
                    return False, "货物只能正放或侧放"
            elif placement_requirement == '正放&立放':
                # 只允许正放和立放
                if cargo.get('orientation', '') not in ['upright', 'upright_rotated']:
                    return False, "货物只能正放或立放"
        
        return True, "摆放合法"
    
    def can_stack_with(self, cargo1, cargo2):
        """检查两个货物是否可以堆叠"""
        # 检查承重限制
        if not cargo2.get('can_bear_weight', True):
            return False
        
        # 检查包装状态
        packaging_status = cargo2.get('packaging_status', '')
        if isinstance(packaging_status, str) and packaging_status.lower() in ['破损', '变形']:
            return False
        
        # 检查自叠限制
        self_stack = cargo1.get('self_stack', '否')
        if self_stack == '是' and cargo1.get('material_name', '') != cargo2.get('material_name', ''):
            return False
        
        return True
    
    def group_same_spec_cargoes(self, cargoes):
        """将相同规格的货物分组"""
        groups = {}
        for cargo in cargoes:
            key = (cargo.get('length', 0), cargo.get('width', 0), cargo.get('height', 0), cargo.get('weight', 0))
            if key not in groups:
                groups[key] = []
            groups[key].append(cargo)
        return list(groups.values())
