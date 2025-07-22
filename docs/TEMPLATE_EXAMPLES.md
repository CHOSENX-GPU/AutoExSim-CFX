# CFX模板配置示例

本文档提供了不同复杂度的CFX模板配置示例，帮助用户根据需求选择合适的模板和配置。

## 📝 基础配置 - 简单参数化

### 配置文件：`config/simple_project.yaml`

```yaml
# 使用简化模板
pre_template_path: "templates/create_def_simple.pre.j2"

# 基础CFX设置
cfx_file_path: "my_model.cfx"
pressure_list: [2187, 2189, 2191]

# 基础参数
flow_analysis_name: "Flow Analysis 1"
domain_name: "S1"
outlet_boundary_name: "S1 Outlet"
outlet_location: "Entire R2_OUTFLOW"
pressure_unit: "Pa"
pressure_blend: "0.05"

# 求解器设置
max_iterations: 3000
residual_target: "0.00001"

# 输出设置
folder_prefix: "P_Out_"
def_file_prefix: "Case_"
```

### 适用场景
- 简单的参数化研究
- 只需要改变出口压力
- 使用默认的CFX设置
- 初学者使用

---

## 🔧 中级配置 - 边界条件定制

### 配置文件：`config/advanced_project.yaml`

```yaml
# 使用高级模板
pre_template_path: "templates/create_def_advanced.pre.j2"

# CFX环境
cfx_version: "22.1"
cfx_file_path: "turbomachinery_model.cfx"
pressure_list: [95000, 100000, 105000, 110000]

# 分析设置
flow_analysis_name: "Compressor Analysis"
domain_name: "Rotor"

# 边界条件
outlet_boundary_name: "Rotor Outlet"
outlet_location: "Entire ROTOR_OUTLET"
inlet_boundary_name: "Rotor Inlet"
pressure_blend: "0.02"
pressure_unit: "Pa"

# 修改入口条件
modify_inlet: true
inlet_condition_type: "Mass Flow Rate"
inlet_mass_flow: "2.5 [kg s^-1]"
inlet_location: "Entire ROTOR_INLET"

# 求解器高级设置
max_iterations: 8000
min_iterations: 100
residual_target: "0.000001"
turbulence_numerics: "Second Order"
advection_scheme: "High Resolution"

# 监测设置
enable_efficiency_monitor: true
efficiency_method: "Total to Total"
fluid_density: 1.2
mean_radius: 0.15
rotational_speed: 15000

# 自定义监测
custom_monitors:
  - name: "Mass Flow Ratio"
    expression: "massFlow()@Rotor_Inlet / massFlow()@Rotor_Outlet"
  - name: "Power"
    expression: "torque_z()@Rotor * 2 * pi * 15000 / 60"
```

### 适用场景
- 叶轮机械分析
- 需要修改多个边界条件
- 自定义监测参数
- 高精度计算要求

---

## 🚀 高级配置 - 多域多参数

### 配置文件：`config/multi_domain_project.yaml`

```yaml
# 自定义多域模板
pre_template_path: "templates/create_def_multi_domain.pre.j2"

# CFX设置
cfx_version: "22.1" 
cfx_file_path: "full_stage_model.cfx"
pressure_list: [90000, 95000, 100000, 105000, 110000]
rotational_speeds: [12000, 15000, 18000]  # 双参数扫描

# 多域设置
domains:
  - name: "Rotor"
    boundaries:
      - name: "Rotor Inlet"
        type: "INLET"
        location: "Entire ROTOR_INLET"
        condition_type: "Total Pressure"
        total_pressure: "101325 [Pa]"
      - name: "Rotor Outlet"
        type: "INTERFACE"
        location: "Entire ROTOR_OUTLET"
  
  - name: "Stator"
    boundaries:
      - name: "Stator Inlet"
        type: "INTERFACE"
        location: "Entire STATOR_INLET"
      - name: "Stator Outlet"
        type: "OUTLET"
        location: "Entire STATOR_OUTLET"
        condition_type: "Average Static Pressure"

# 自定义材料
custom_materials:
  - name: "Hot Air"
    description: "High temperature air"
    density: "1.0 [kg m^-3]"
    viscosity: "2.0e-5 [kg m^-1 s^-1]"
    equation_of_state: "Ideal Gas"

# 复杂表达式
custom_expressions:
  - name: "Overall_Efficiency"
    formula: "(areaAve(Total Enthalpy)@Stator_Outlet - areaAve(Total Enthalpy)@Rotor_Inlet) / (torque_z()@Rotor * 2 * pi * omega / 60)"
  - name: "Pressure_Ratio"
    formula: "areaAve(Total Pressure)@Stator_Outlet / areaAve(Total Pressure)@Rotor_Inlet"
  - name: "Temperature_Rise"
    formula: "areaAve(Total Temperature)@Stator_Outlet - areaAve(Total Temperature)@Rotor_Inlet"

# 详细监测
custom_monitors:
  - name: "Stage Efficiency"
    expression: "Overall_Efficiency"
    output_file: "stage_efficiency.csv"
  - name: "Pressure Ratio"
    expression: "Pressure_Ratio"
    output_file: "pressure_ratio.csv"
  - name: "Temperature Rise"
    expression: "Temperature_Rise"
  - name: "Rotor Torque"
    expression: "torque_z()@Rotor"
    coord_frame: "Rotating Frame"

# 高级求解器设置
max_iterations: 10000
residual_target: "0.0000001"
turbulence_numerics: "Second Order"
advection_scheme: "Specified Blend Factor"
blend_factor: 0.75
convergence_acceleration: true
```

### 适用场景
- 多级叶轮机械
- 复杂几何和边界条件
- 详细的性能分析
- 研究级计算

---

## 🎛️ 专业配置 - 传热和粗糙度

### 配置文件：`config/heat_transfer_project.yaml`

```yaml
pre_template_path: "templates/create_def_heat_transfer.pre.j2"

# 基础设置
cfx_file_path: "heat_exchanger_model.cfx"
pressure_list: [100000, 105000, 110000]
temperature_list: [300, 320, 340, 360]  # 双参数：压力和温度

# 传热边界条件
wall_boundary_settings: true
wall_boundaries:
  - name: "Hot Wall"
    location: "Entire HOT_SURFACE"
    heat_transfer_option: "Fixed Temperature"
    wall_temperature: "400 [K]"
    roughness_option: "Rough Wall"
    roughness_height: "0.0001 [m]"
  
  - name: "Cold Wall"
    location: "Entire COLD_SURFACE" 
    heat_transfer_option: "Heat Flux"
    wall_heat_flux: "-5000 [W m^-2]"
    roughness_option: "Smooth Wall"

# 流体域设置
fluid_domains:
  - name: "Hot Fluid"
    inlet_temperature: "380 [K]"
    material: "Water"
  - name: "Cold Fluid"
    inlet_temperature: "300 [K]"
    material: "Water"

# 传热监测
heat_transfer_monitors:
  - name: "Heat Transfer Rate"
    expression: "heatFlow()@Hot_Wall"
  - name: "Overall Heat Transfer Coefficient"
    expression: "heatFlow()@Hot_Wall / (areaAve(Temperature)@Hot_Wall - areaAve(Temperature)@Cold_Wall) / area()@Hot_Wall"
  - name: "Effectiveness"
    expression: "heatFlow()@Hot_Wall / (massFlow()@Hot_Inlet * cp * (T_hot_inlet - T_cold_inlet))"

# 高精度设置
energy_equation: true
buoyancy_effects: true
radiation_model: "P1 Model"
turbulent_heat_flux: "Generalized Gradient Diffusion Hypothesis"
```

---

## 📊 配置选择指南

### 根据项目复杂度选择

| 项目类型 | 推荐模板 | 配置复杂度 | 适用场景 |
|---------|---------|-----------|----------|
| 简单参数化 | `create_def_simple.pre.j2` | ⭐ | 学习、验证、简单研究 |
| 标准分析 | `create_def.pre.j2` | ⭐⭐ | 常规CFD分析 |
| 高级分析 | `create_def_advanced.pre.j2` | ⭐⭐⭐ | 叶轮机械、复杂边界条件 |
| 多域分析 | 自定义模板 | ⭐⭐⭐⭐ | 多级机械、热交换器 |
| 研究级 | 完全自定义 | ⭐⭐⭐⭐⭐ | 前沿研究、特殊应用 |

### 参数数量指南

- **1-5个参数**: 使用简单模板
- **5-15个参数**: 使用高级模板  
- **15+个参数**: 考虑自定义模板
- **多类型参数**: 使用专门的多参数模板

### 性能考虑

- **快速原型**: 简单模板 + 低迭代次数
- **生产计算**: 高级模板 + 优化设置
- **研究计算**: 自定义模板 + 高精度设置

---

## 🔧 模板切换

### 在同一项目中切换模板

```yaml
# 在配置文件中轻松切换
# pre_template_path: "templates/create_def_simple.pre.j2"      # 简单版本
pre_template_path: "templates/create_def_advanced.pre.j2"     # 高级版本
# pre_template_path: "templates/my_custom_template.pre.j2"     # 自定义版本
```

### 批量模板对比

```bash
# 使用不同模板运行同样的参数
python main.py --config config/simple_version.yaml --pressures 2187 2189
python main.py --config config/advanced_version.yaml --pressures 2187 2189
```

通过这些示例，用户可以根据自己的需求选择合适的模板配置，并逐步从简单配置过渡到复杂配置。
