# 数据库配置
DB_CONFIG = {
    'host': '10.1.55.129',
    'port': 26768,
    'user': 'digitaladmin',
    'password': '123qaz!@WSX',
    'database': 'digital_employees',
    'charset': 'utf8mb4'
}

# 容器尺寸配置（标准集装箱）
CONTAINER_SIZES = {
    '20ft': {'length': 589.8, 'width': 235.2, 'height': 239.3},  # 单位：cm
    '40ft': {'length': 1203.2, 'width': 235.2, 'height': 239.3},
    '40ft_hc': {'length': 1203.2, 'width': 235.2, 'height': 269.0}
}

# 规则引擎配置
RULES_CONFIG = {
    'max_weight': 28000,  # 最大载重（kg）
    'pallet_only_upright': True,  # 托盘木箱只允许正放和正放旋转
    'full_bearing_surface': True,  # 货物底部完全承重面
    'large_cargo_threshold': 75,  # 大货阈值（cm）
    'loading_sequence': [
        'fixed_combinations',
        'bottom_only',
        'large_cargo',
        'bottom_upright_top_side',
        'same_spec_adjacent',
        'remaining_mixed'
    ]
}
