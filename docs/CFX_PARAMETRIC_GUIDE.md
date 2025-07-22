# CFX参数化建模指南

## 🎯 概述

参数化CFX建模是CFD分析中的重要技术，允许通过改变参数值来研究不同设计条件下的流动特性。本指南将详细介绍如何在CFX自动化系统中实现高效的参数化建模。

## 📚 目录

1. [参数化建模基础](#参数化建模基础)
2. [CFX模型准备](#cfx模型准备)
3. [参数定义策略](#参数定义策略)
4. [模板设计原则](#模板设计原则)
5. [常见参数化场景](#常见参数化场景)
6. [高级技巧](#高级技巧)
7. [最佳实践](#最佳实践)
8. [故障排除](#故障排除)

---

## 🔬 参数化建模基础

### 什么是参数化建模

参数化建模是通过定义关键参数，系统性地研究这些参数对CFD结果影响的方法。

### 参数化的优势

- **效率提升**: 自动生成多个算例，减少重复工作
- **设计优化**: 快速探索设计空间，找到最优解
- **敏感性分析**: 了解参数对结果的影响程度
- **质量控制**: 标准化建模流程，减少人为错误

### 参数化类型

1. **几何参数化**: 改变几何尺寸和形状
2. **边界条件参数化**: 改变进出口条件
3. **材料属性参数化**: 改变流体或固体属性
4. **求解器参数化**: 改变数值方法和设置

---

## 🛠️ CFX模型准备

### 1. 创建基础CFX模型

#### 模型要求
- 完整的几何定义
- 合理的网格质量
- 基本的边界条件设置
- 初始的求解器配置

#### 检查清单
```checklist
☐ 几何完整性检查
☐ 网格质量验证 (正交性 > 0.1, 纵横比 < 100)
☐ 边界条件合理性
☐ 物理模型选择正确
☐ 初始条件设置
☐ 监测点定义
☐ 收敛性验证
```

### 2. 模型文件组织

```
project_folder/
├── model.cfx                    # 主CFX文件
├── geometry/                    # 几何文件
│   ├── baseline.gtm
│   └── modified_versions/
├── mesh/                        # 网格文件
│   ├── baseline.gtm
│   └── mesh_sensitivity/
├── templates/                   # 模板文件
│   ├── create_def.pre.j2
│   └── custom_templates/
└── results/                     # 结果文件
    ├── pressure_sweep/
    └── geometry_optimization/
```

### 3. 参数识别

#### 关键参数类型
```yaml
# 边界条件参数
boundary_parameters:
  inlet_pressure: [90000, 95000, 100000, 105000]  # Pa
  inlet_temperature: [288, 298, 308]              # K
  outlet_pressure: [85000, 90000, 95000]          # Pa
  mass_flow_rate: [1.0, 1.5, 2.0, 2.5]          # kg/s

# 几何参数
geometry_parameters:
  blade_angle: [30, 35, 40, 45]                   # degrees
  tip_clearance: [0.5, 1.0, 1.5, 2.0]           # mm
  hub_radius: [0.1, 0.12, 0.14]                  # m

# 材料参数
material_parameters:
  fluid_density: [1.0, 1.2, 1.4]                 # kg/m³
  dynamic_viscosity: [1.8e-5, 2.0e-5, 2.2e-5]   # Pa·s

# 求解器参数
solver_parameters:
  max_iterations: [3000, 5000, 8000]
  residual_target: [1e-5, 1e-6, 1e-7]
  turbulence_model: ["SST", "k-epsilon", "RSM"]
```

---

## 📊 参数定义策略

### 1. 单参数扫描

适用于研究单个参数的影响：

```yaml
# 压力扫描
parameter_study: "pressure_sweep"
pressure_list: [85000, 90000, 95000, 100000, 105000, 110000]

# 对应的模板设置
study_type: "single_parameter"
parameter_name: "outlet_pressure"
parameter_unit: "Pa"
baseline_conditions:
  inlet_pressure: 101325
  temperature: 288
  mass_flow: 2.0
```

### 2. 多参数扫描

研究多个参数的组合效应：

```yaml
# 全因子设计
parameter_study: "factorial_design"
parameters:
  pressure: [90000, 95000, 100000]
  temperature: [288, 298, 308]
  angle: [30, 35, 40]

# 生成 3×3×3 = 27 个算例
study_type: "full_factorial"
total_cases: 27
```

### 3. 优化导向的参数化

```yaml
# 拉丁超立方采样
parameter_study: "optimization"
sampling_method: "latin_hypercube"
sample_size: 50

design_variables:
  - name: "inlet_pressure"
    range: [90000, 110000]
    type: "continuous"
  - name: "blade_angle" 
    range: [25, 45]
    type: "continuous"
  - name: "tip_clearance"
    range: [0.5, 2.0]
    type: "continuous"

objectives:
  - name: "efficiency"
    type: "maximize"
  - name: "pressure_ratio"
    type: "maximize"
  - name: "mass_flow"
    type: "target"
    target_value: 2.0
```

---

## 🎨 模板设计原则

### 1. 模块化设计

将模板分解为可重用的模块：

```jinja2
{# 边界条件模块 #}
{% macro boundary_condition(boundary_name, boundary_type, location, conditions) %}
&replace BOUNDARY: {{ boundary_name }}
    Boundary Type = {{ boundary_type }}
    Location = {{ location }}
    BOUNDARY CONDITIONS:
        {% for condition in conditions %}
        {{ condition.section }}:
            {% for param, value in condition.parameters.items() %}
            {{ param }} = {{ value }}
            {% endfor %}
        END
        {% endfor %}
    END
END
{% endmacro %}

{# 使用宏 #}
{{ boundary_condition(
    boundary_name="Inlet",
    boundary_type="INLET", 
    location="Entire INLET_REGION",
    conditions=inlet_conditions
) }}
```

### 2. 参数验证

在模板中添加参数检查：

```jinja2
{# 参数验证 #}
{% if pressure_list | length == 0 %}
    {% error "pressure_list cannot be empty" %}
{% endif %}

{% for pressure in pressure_list %}
    {% if pressure < 0 %}
        {% error "Pressure values must be positive: " + pressure|string %}
    {% endif %}
{% endfor %}

{# 范围检查 #}
{% if max_iterations < 100 %}
    {% set max_iterations = 1000 %}
    {# Warning: max_iterations too low, set to 1000 #}
{% endif %}
```

### 3. 智能默认值

提供合理的默认参数：

```jinja2
{# 智能默认值设置 #}
{% set default_solver_settings = {
    "turbulence_model": "SST",
    "advection_scheme": "High Resolution",
    "max_iterations": 5000,
    "residual_target": "1e-6"
} %}

{# 根据应用类型调整默认值 #}
{% if application_type == "turbomachinery" %}
    {% set default_solver_settings = default_solver_settings | combine({
        "max_iterations": 8000,
        "residual_target": "1e-7",
        "turbulence_numerics": "Second Order"
    }) %}
{% elif application_type == "external_flow" %}
    {% set default_solver_settings = default_solver_settings | combine({
        "max_iterations": 3000,
        "turbulence_model": "k-epsilon"
    }) %}
{% endif %}
```

---

## 🔄 常见参数化场景

### 1. 叶轮机械参数化

```yaml
# 叶轮机械配置
application_type: "turbomachinery"
machine_type: "centrifugal_compressor"

# 性能参数扫描
performance_parameters:
  rotational_speed: [10000, 12000, 15000, 18000]  # rpm
  mass_flow_rate: [1.0, 1.5, 2.0, 2.5, 3.0]     # kg/s
  
# 几何参数
geometry_parameters:
  impeller_diameter: [0.2, 0.22, 0.24, 0.26]     # m
  blade_outlet_angle: [20, 25, 30, 35]           # degrees
  tip_clearance: [0.5, 1.0, 1.5]                 # mm

# 监测参数
performance_metrics:
  - pressure_ratio
  - isentropic_efficiency
  - polytropic_efficiency
  - surge_margin
  - power_consumption
```

对应的模板片段：
```jinja2
{# 叶轮机械专用监测表达式 #}
LIBRARY:
  CEL:
    EXPRESSIONS:
      {# 压比 #}
      Pressure_Ratio = areaAve(Total Pressure)@Impeller_Outlet / areaAve(Total Pressure)@Impeller_Inlet
      
      {# 等熵效率 #}
      Isentropic_Efficiency = (areaAve(Total Enthalpy)@Impeller_Outlet_Ideal - areaAve(Total Enthalpy)@Impeller_Inlet) / (areaAve(Total Enthalpy)@Impeller_Outlet - areaAve(Total Enthalpy)@Impeller_Inlet)
      
      {# 功率 #}
      Power = torque_z()@Impeller * 2 * pi * {{ rotational_speed }} / 60
      
      {# 比功 #}
      Specific_Work = Power / massFlow()@Impeller_Inlet
      
    END
  END
END
```

### 2. 传热问题参数化

```yaml
# 传热分析配置
application_type: "heat_transfer"
analysis_type: "conjugate_heat_transfer"

# 热边界条件参数
thermal_parameters:
  hot_inlet_temperature: [350, 375, 400, 425]     # K
  cold_inlet_temperature: [285, 295, 305]         # K
  wall_heat_flux: [1000, 2000, 5000, 10000]      # W/m²
  
# 材料属性参数
material_parameters:
  thermal_conductivity: [0.6, 1.0, 1.5]          # W/m·K
  specific_heat: [1000, 1200, 1500]              # J/kg·K
  
# 传热性能指标
heat_transfer_metrics:
  - overall_heat_transfer_coefficient
  - effectiveness
  - ntu_number
  - pressure_drop
  - pumping_power
```

### 3. 外流参数化

```yaml
# 外流分析配置
application_type: "external_flow"
flow_type: "vehicle_aerodynamics"

# 流动条件参数
flow_conditions:
  velocity: [20, 30, 40, 50, 60]                  # m/s
  angle_of_attack: [-5, 0, 5, 10, 15]            # degrees
  yaw_angle: [-10, -5, 0, 5, 10]                 # degrees
  
# 几何参数
geometry_variations:
  vehicle_height: [1.4, 1.5, 1.6]                # m
  front_area: [2.0, 2.2, 2.4]                    # m²
  rear_spoiler_angle: [0, 5, 10, 15]             # degrees

# 空气动力学指标
aerodynamic_metrics:
  - drag_coefficient
  - lift_coefficient
  - pressure_coefficient
  - y_plus_values
  - separation_points
```

---

## ⚡ 高级技巧

### 1. 条件参数化

根据条件动态调整参数：

```jinja2
{# 根据雷诺数调整湍流模型 #}
{% set reynolds_number = (density * velocity * characteristic_length) / viscosity %}

{% if reynolds_number < 2300 %}
    {% set turbulence_model = "Laminar" %}
    {% set wall_treatment = "No Slip Wall" %}
{% elif reynolds_number < 100000 %}
    {% set turbulence_model = "k-epsilon" %}
    {% set wall_treatment = "Scalable Wall Functions" %}
{% else %}
    {% set turbulence_model = "SST" %}
    {% set wall_treatment = "Automatic Wall Treatment" %}
{% endif %}

TURBULENCE:
    Option = {{ turbulence_model }}
    {% if turbulence_model != "Laminar" %}
    Wall Function = {{ wall_treatment }}
    {% endif %}
END
```

### 2. 多目标优化参数化

```yaml
# 多目标优化配置
optimization_setup:
  algorithm: "NSGA-II"
  population_size: 50
  generations: 100
  
  design_variables:
    - name: "blade_angle"
      type: "continuous"
      bounds: [25, 45]
      initial: 35
    - name: "tip_clearance"
      type: "continuous" 
      bounds: [0.5, 2.0]
      initial: 1.0
      
  objectives:
    - name: "efficiency"
      type: "maximize"
      weight: 0.6
    - name: "pressure_ratio"
      type: "maximize"
      weight: 0.3
    - name: "noise_level"
      type: "minimize"
      weight: 0.1
      
  constraints:
    - name: "mass_flow"
      type: "equality"
      target: 2.0
      tolerance: 0.05
    - name: "surge_margin"
      type: "inequality"
      bound: "> 0.1"
```

### 3. 自适应网格参数化

```jinja2
{# 根据参数自动调整网格密度 #}
{% if flow_regime == "transonic" or mach_number > 0.8 %}
    {% set mesh_density_factor = 1.5 %}
    {% set near_wall_layers = 20 %}
{% elif reynolds_number > 1000000 %}
    {% set mesh_density_factor = 1.2 %}
    {% set near_wall_layers = 15 %}
{% else %}
    {% set mesh_density_factor = 1.0 %}
    {% set near_wall_layers = 10 %}
{% endif %}

MESH ADAPTATION:
    Option = Automatic
    Adaptation Criterion = Solution Change
    Maximum Adaptation Levels = 3
    Mesh Density Factor = {{ mesh_density_factor }}
END
```

### 4. 并行计算优化

```jinja2
{# 根据案例复杂度调整并行设置 #}
{% set total_cells = domain_cells | sum %}
{% if total_cells > 10000000 %}
    {% set parallel_partitions = 32 %}
    {% set memory_per_partition = "8GB" %}
{% elif total_cells > 1000000 %}
    {% set parallel_partitions = 16 %}
    {% set memory_per_partition = "4GB" %}
{% else %}
    {% set parallel_partitions = 8 %}
    {% set memory_per_partition = "2GB" %}
{% endif %}

PARALLEL PROCESSING:
    Number of Partitions = {{ parallel_partitions }}
    Partition Algorithm = MeTiS
    Partition Interface Type = Automatic
END
```

---

## 💡 最佳实践

### 1. 参数命名规范

```yaml
# 好的命名示例
parameter_naming:
  descriptive: true
  units_included: true
  consistent_format: true

# 推荐格式
good_examples:
  - inlet_total_pressure_pa      # 描述性 + 单位
  - blade_outlet_angle_deg       # 清晰的物理含义
  - tip_clearance_mm            # 几何参数 + 单位
  - max_iterations_solver       # 求解器参数

# 避免的格式
bad_examples:
  - p1, p2, p3                  # 无意义的命名
  - temp                        # 不明确的缩写
  - x, y, z                     # 过于泛化
```

### 2. 参数范围设计

```yaml
# 参数范围设计原则
range_design:
  physical_meaning: true        # 确保物理意义
  feasible_range: true         # 在可行范围内
  sufficient_resolution: true   # 足够的分辨率
  
# 示例：压比范围设计
pressure_ratio_study:
  baseline: 1.5
  range: [1.2, 2.0]           # ±33% 变化范围
  points: [1.2, 1.35, 1.5, 1.65, 1.8, 2.0]
  rationale: "覆盖典型离心压缩机工作范围"
```

### 3. 计算资源规划

```yaml
# 计算资源评估
resource_planning:
  case_complexity:
    simple: 
      cells: "< 1M"
      time_per_case: "< 2 hours"
      cores_per_case: 8
    medium:
      cells: "1M - 10M" 
      time_per_case: "2-8 hours"
      cores_per_case: 16
    complex:
      cells: "> 10M"
      time_per_case: "> 8 hours"
      cores_per_case: 32
      
  total_estimation:
    cases: 50
    average_time: 4  # hours
    total_cpu_hours: 200
    wall_time: "1-2 days"  # 并行执行
```

### 4. 质量控制

```yaml
# 质量控制检查点
quality_control:
  pre_processing:
    - geometry_integrity
    - mesh_quality_metrics
    - boundary_condition_validation
    - physics_model_consistency
    
  during_processing:
    - convergence_monitoring
    - mass_conservation_check
    - energy_balance_verification
    - iterative_residual_tracking
    
  post_processing:
    - result_consistency_check
    - physical_reasonableness
    - trend_analysis
    - uncertainty_quantification
```

---

## 🚨 故障排除

### 1. 常见模板错误

#### 错误：变量未定义
```
UndefinedError: 'parameter_name' is undefined
```

**解决方案**：
```jinja2
{# 使用默认值 #}
{{ parameter_name | default("default_value") }}

{# 或添加条件检查 #}
{% if parameter_name is defined %}
    Parameter = {{ parameter_name }}
{% endif %}
```

#### 错误：语法错误
```
TemplateSyntaxError: unexpected char '&' at 45
```

**解决方案**：
```jinja2
{# 正确的CFX命令格式 #}
&replace BOUNDARY: {{ boundary_name }}
    {# 而不是 #}
&replace BOUNDARY: {{ boundary_name }}
```

### 2. 参数化验证

```python
# 参数验证脚本
def validate_parameters(config):
    """验证参数配置的合理性"""
    errors = []
    
    # 检查压力值
    if 'pressure_list' in config:
        for p in config['pressure_list']:
            if p <= 0:
                errors.append(f"Invalid pressure: {p}")
                
    # 检查温度值
    if 'temperature_list' in config:
        for t in config['temperature_list']:
            if t < 0:  # 绝对零度检查
                errors.append(f"Invalid temperature: {t}")
                
    # 检查几何参数
    if 'tip_clearance' in config:
        if config['tip_clearance'] < 0:
            errors.append("Tip clearance cannot be negative")
            
    return errors

# 使用验证
validation_errors = validate_parameters(config)
if validation_errors:
    print("Parameter validation failed:")
    for error in validation_errors:
        print(f"  - {error}")
```

### 3. 调试技巧

#### 模板调试
```bash
# 检查模板语法
python -c "
from jinja2 import Template
with open('templates/my_template.pre.j2', 'r') as f:
    template = Template(f.read())
print('Template syntax is valid')
"

# 测试模板渲染
python -c "
from jinja2 import Template
import yaml

with open('config/test_config.yaml', 'r') as f:
    config = yaml.safe_load(f)
    
with open('templates/my_template.pre.j2', 'r') as f:
    template = Template(f.read())
    
result = template.render(**config)
print(result)
"
```

#### 参数追踪
```yaml
# 启用调试模式
debug_mode: true
log_level: "DEBUG"
trace_parameters: true

# 参数日志记录
parameter_log:
  file: "parameter_trace.log"
  format: "json"
  include_timestamps: true
```

---

## 📈 性能优化建议

### 1. 批处理策略

```yaml
# 批处理配置
batch_processing:
  batch_size: 10              # 每批处理的案例数
  parallel_batches: 3         # 并行批次数
  memory_limit_per_batch: "32GB"
  time_limit_per_batch: "12 hours"
  
  error_handling:
    retry_failed_cases: true
    max_retries: 2
    continue_on_failure: true
```

### 2. 智能调度

```yaml
# 智能调度策略
scheduling:
  priority_queue: true
  resource_aware: true
  
  case_prioritization:
    - name: "baseline_cases"
      priority: 1
      description: "基准案例优先"
    - name: "optimization_cases"
      priority: 2
      description: "优化相关案例"
    - name: "sensitivity_cases"
      priority: 3
      description: "敏感性分析案例"
```

### 3. 结果管理

```yaml
# 结果管理策略
result_management:
  compression: true
  selective_storage: true
  
  storage_policy:
    monitor_files: "always"      # 监测文件总是保存
    result_files: "successful"   # 只保存成功的结果文件
    backup_files: "never"       # 不保存备份文件
    
  cleanup_schedule:
    temp_files: "immediate"      # 立即清理临时文件
    intermediate_files: "7days"  # 7天后清理中间文件
    old_results: "30days"       # 30天后归档旧结果
```

通过遵循本指南的建议和最佳实践，您可以高效地实现CFX参数化建模，提高CFD分析的质量和效率。记住，成功的参数化建模需要仔细的规划、系统的方法和持续的优化。
