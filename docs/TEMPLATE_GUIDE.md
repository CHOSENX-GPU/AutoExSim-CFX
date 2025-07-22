# CFX .pre模板自定义指南

## 概述

CFX自动化系统使用Jinja2模板引擎来生成CFX Pre脚本(.pre文件)。通过自定义模板，您可以灵活地控制CFX模型的参数化设置，满足不同的计算需求。

## 📁 模板文件位置

模板文件存放在 `templates/` 目录下，系统提供了以下预定义模板：

- `create_def.pre.j2` - 基础模板
- `create_def_simple.pre.j2` - 简化模板
- `create_def_advanced.pre.j2` - 高级模板

## 🎯 模板语法基础

### 1. 变量替换

使用双花括号 `{{ }}` 来插入变量：

```jinja2
# CFX文件路径
>load filename={{ cfx_file_path }}, mode=cfx, overwrite=yes

# 压力值
Relative Pressure = $P [{{ pressure_unit | default("Pa") }}]

# 迭代次数
Maximum Number of Iterations = {{ max_iterations | default("5000") }}
```

### 2. 默认值设置

使用 `| default()` 过滤器设置默认值：

```jinja2
CFX Pre Version = {{ cfx_version | default("22.1") }}
Pressure Profile Blend = {{ pressure_blend | default("0.05") }}
```

### 3. 条件判断

使用 `{% if %}` 来条件性包含内容：

```jinja2
{# 只在需要时修改入口边界条件 #}
{% if modify_inlet %}
&replace BOUNDARY: {{ inlet_boundary_name }}
    # 入口边界条件设置
{% endif %}
```

### 4. 循环处理

使用 `{% for %}` 来处理列表数据：

```jinja2
{# 自定义表达式 #}
{% for expr in custom_expressions | default([]) %}
{{ expr.name }} = {{ expr.formula }}
{% endfor %}

{# 压力参数数组 #}
!@P_def = ({{ pressure_list | join(',') }});
```

### 5. 注释

使用 `{# #}` 添加模板注释：

```jinja2
{# 这是模板注释，不会出现在生成的文件中 #}
{###################模型参数设置################### #}
```

## ⚙️ 配置文件中的模板参数

### 基础参数

在配置文件的 YAML 中定义模板变量：

```yaml
# CFX模型参数
cfx_version: "22.1"
cfx_file_path: "model.cfx"
flow_analysis_name: "Flow Analysis 1"
domain_name: "S1"
outlet_boundary_name: "S1 Outlet"
inlet_boundary_name: "R1 Inlet"
outlet_location: "Entire R2_OUTFLOW"
pressure_blend: "0.05"
pressure_unit: "Pa"

# 求解器参数
max_iterations: 5000
min_iterations: 1
residual_target: "0.000001"
turbulence_numerics: "First Order"
advection_scheme: "High Resolution"

# 文件输出参数
folder_prefix: "P_Out_"
def_file_prefix: ""
output_base_path: "/path/to/output"
```

### 高级参数配置

```yaml
# 流体参数
fluid_density: 1.225
mean_radius: 0.2505
rotational_speed: 2930
mass_scale_factor_in: 10
mass_scale_factor_out: -9

# 边界条件
modify_inlet: true
inlet_condition_type: "Total Pressure"
inlet_total_pressure: "0 [Pa]"
flow_regime: "Subsonic"
pressure_averaging: "Average Over Whole Outlet"

# 监测设置
enable_efficiency_monitor: true
efficiency_method: "Total to Total"
monitor_balances: "Full"
monitor_forces: "Full"

# 自定义表达式
custom_expressions:
  - name: "Custom_Ratio"
    formula: "massFlow()@Inlet / massFlow()@Outlet"
  - name: "Pressure_Drop"
    formula: "areaAve(Total Pressure)@Inlet - areaAve(Pressure)@Outlet"

# 自定义监测点
custom_monitors:
  - name: "Custom Monitor 1"
    expression: "Custom_Ratio"
    coord_frame: "Coord 0"
    output_file: "custom_monitor.csv"
  - name: "Pressure Drop"
    expression: "Pressure_Drop"

# 附加边界条件
additional_boundary_conditions:
  - parameter: "Turbulent Viscosity Ratio"
    value: "10"
  - parameter: "Heat Transfer Coefficient"
    value: "25 [W m^-2 K^-1]"
```

## 🛠️ 创建自定义模板

### 步骤1：复制基础模板

```bash
cp templates/create_def_simple.pre.j2 templates/my_custom_template.pre.j2
```

### 步骤2：修改模板内容

根据您的需求修改模板，例如添加新的边界条件：

```jinja2
{# 自定义壁面边界条件 #}
{% if wall_boundary_settings %}
&replace BOUNDARY: {{ wall_boundary_name | default("Wall") }}
    Boundary Type = WALL
    Location = {{ wall_location }}
    BOUNDARY CONDITIONS:
        HEAT TRANSFER:
            Option = {{ heat_transfer_option | default("Adiabatic") }}
            {% if heat_transfer_option == "Fixed Temperature" %}
            Fixed Temperature = {{ wall_temperature | default("300 [K]") }}
            {% elif heat_transfer_option == "Heat Flux" %}
            Heat Flux = {{ wall_heat_flux | default("0 [W m^-2]") }}
            {% endif %}
        END
        MASS AND MOMENTUM:
            Option = {{ wall_roughness_option | default("Smooth Wall") }}
            {% if wall_roughness_option == "Rough Wall" %}
            Roughness Height = {{ wall_roughness | default("0.0001 [m]") }}
            {% endif %}
        END
    END
END
{% endif %}
```

### 步骤3：在配置文件中指定模板

```yaml
# 指定自定义模板
pre_template_path: "templates/my_custom_template.pre.j2"

# 添加对应的参数
wall_boundary_settings: true
wall_boundary_name: "Blade Surface"
wall_location: "Entire BLADE"
heat_transfer_option: "Fixed Temperature"
wall_temperature: "350 [K]"
wall_roughness_option: "Rough Wall"
wall_roughness: "0.0002 [m]"
```

## 📊 模板参数完整列表

### CFX环境参数
```yaml
cfx_version: "22.1"                    # CFX版本
cfx_file_path: "model.cfx"             # CFX模型文件路径
```

### 分析设置参数
```yaml
flow_analysis_name: "Flow Analysis 1"   # 流动分析名称
domain_name: "S1"                       # 计算域名称
```

### 边界条件参数
```yaml
# 出口边界
outlet_boundary_name: "S1 Outlet"       # 出口边界名称
outlet_location: "Entire R2_OUTFLOW"    # 出口位置
pressure_blend: "0.05"                  # 压力混合因子
pressure_unit: "Pa"                     # 压力单位
flow_regime: "Subsonic"                 # 流动状态
pressure_averaging: "Average Over Whole Outlet"  # 压力平均方式

# 入口边界
inlet_boundary_name: "R1 Inlet"         # 入口边界名称
inlet_location: "Entire R1_INFLOW"      # 入口位置
modify_inlet: false                      # 是否修改入口条件
inlet_condition_type: "Total Pressure"  # 入口条件类型
inlet_total_pressure: "0 [Pa]"          # 入口总压
inlet_mass_flow: "1.0 [kg s^-1]"       # 入口质量流量
```

### 求解器参数
```yaml
# 迭代控制
max_iterations: 5000                     # 最大迭代次数
min_iterations: 1                        # 最小迭代次数
residual_target: "0.000001"             # 残差目标
residual_type: "RMS"                     # 残差类型

# 数值方法
turbulence_numerics: "First Order"      # 湍流数值方法
advection_scheme: "High Resolution"     # 对流格式
length_scale_option: "Conservative"     # 长度尺度选项
timescale_control: "Auto Timescale"     # 时间尺度控制
timescale_factor: 1.0                   # 时间尺度因子
```

### 监测参数
```yaml
# 基础监测
enable_efficiency_monitor: true         # 启用效率监测
efficiency_method: "Total to Total"     # 效率计算方法
efficiency_type: "Both Compression and Expansion"  # 效率类型
monitor_balances: "Full"                # 平衡监测
monitor_forces: "Full"                  # 力监测
monitor_particles: "Full"               # 粒子监测
monitor_residuals: "Full"               # 残差监测
monitor_totals: "Full"                  # 总量监测

# 流体参数（用于监测表达式）
fluid_density: 1.225                    # 流体密度
mean_radius: 0.2505                     # 平均半径
rotational_speed: 2930                  # 转速
mass_scale_factor_in: 10                # 入口质量流量缩放
mass_scale_factor_out: -9               # 出口质量流量缩放
```

### 输出参数
```yaml
# 文件命名
folder_prefix: "P_Out_"                 # 文件夹前缀
def_file_prefix: ""                     # def文件前缀
output_base_path: "."                   # 输出基础路径

# 结果文件
enable_result_files: true               # 启用结果文件
file_compression: "Compressed"          # 文件压缩
results_option: "Standard"              # 结果选项
```

## 🔧 高级功能

### 1. 多域模板

```jinja2
{# 处理多个计算域 #}
{% for domain in domains | default([]) %}
DOMAIN: {{ domain.name }}
    {% for boundary in domain.boundaries %}
    &replace BOUNDARY: {{ boundary.name }}
        Boundary Type = {{ boundary.type }}
        Location = {{ boundary.location }}
        # 边界条件...
    END
    {% endfor %}
END
{% endfor %}
```

配置：
```yaml
domains:
  - name: "Rotor"
    boundaries:
      - name: "Rotor Inlet"
        type: "INLET"
        location: "Entire ROTOR_INLET"
      - name: "Rotor Outlet"  
        type: "INTERFACE"
        location: "Entire ROTOR_OUTLET"
  - name: "Stator"
    boundaries:
      - name: "Stator Inlet"
        type: "INTERFACE" 
        location: "Entire STATOR_INLET"
```

### 2. 参数化几何

```jinja2
{# 几何参数化 #}
{% if geometric_parameters %}
GEOMETRY MODIFICATION:
    {% for param in geometric_parameters %}
    {{ param.name }} = {{ param.value }} [{{ param.unit }}]
    {% endfor %}
END
{% endif %}
```

### 3. 材料属性定义

```jinja2
{# 自定义材料属性 #}
{% if custom_materials %}
{% for material in custom_materials %}
LIBRARY:
    MATERIALS:
        {{ material.name }}:
            Material Description = {{ material.description }}
            PROPERTIES:
                Option = General Material
                EQUATION OF STATE:
                    Density = {{ material.density }}
                    Option = {{ material.equation_of_state }}
                END
                DYNAMIC VISCOSITY:
                    Dynamic Viscosity = {{ material.viscosity }}
                    Option = Value
                END
            END
        END
    END
END
{% endfor %}
{% endif %}
```

## 🚀 使用示例

### 示例1：基础参数化

配置文件 `config/my_project.yaml`：
```yaml
# 指定模板
pre_template_path: "templates/create_def_simple.pre.j2"

# 基础参数
cfx_file_path: "pump_model.cfx"
pressure_list: [101325, 102000, 103000]
flow_analysis_name: "Pump Analysis"
domain_name: "Impeller"
outlet_boundary_name: "Outlet"
max_iterations: 3000
```

### 示例2：复杂边界条件

```yaml
pre_template_path: "templates/create_def_advanced.pre.j2"

# 修改入口条件
modify_inlet: true
inlet_boundary_name: "Mass Flow Inlet"
inlet_condition_type: "Mass Flow Rate"
inlet_mass_flow: "2.5 [kg s^-1]"

# 自定义表达式
custom_expressions:
  - name: "Efficiency"
    formula: "(areaAve(Total Pressure)@Outlet - areaAve(Total Pressure)@Inlet) / (0.5 * 1000 * 50^2)"
  - name: "Power"
    formula: "torque_z()@Impeller * 2 * pi * 1500 / 60"

# 自定义监测
custom_monitors:
  - name: "Pump Efficiency"
    expression: "Efficiency"
  - name: "Power Consumption"
    expression: "Power"
    output_file: "power_monitor.csv"
```

### 示例3：多参数扫描

```yaml
# 压力和转速双参数扫描
pressure_list: [90000, 95000, 100000, 105000, 110000]
rotational_speeds: [1000, 1500, 2000, 2500, 3000]

# 在模板中处理双参数
# （需要自定义模板来支持双重循环）
```

## 📝 最佳实践

### 1. 模板组织
- 为不同类型的分析创建专门的模板
- 使用有意义的模板文件名
- 添加充分的注释说明

### 2. 参数命名
- 使用描述性的参数名
- 保持参数命名的一致性
- 为所有参数提供合理的默认值

### 3. 错误处理
- 为必需参数添加验证
- 使用条件判断避免无效配置
- 提供清晰的错误信息

### 4. 版本控制
- 对模板文件进行版本控制
- 记录模板的修改历史
- 保持向后兼容性

## 🔍 调试模板

### 1. 检查生成的.pre文件
```bash
# 使用干运行模式查看生成的文件
python main.py --config config.yaml --dry-run --pressures 2187
```

### 2. 验证语法
```bash
# 检查Jinja2模板语法
python -c "
from jinja2 import Template, Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('templates'))
template = env.get_template('your_template.pre.j2')
print('Template syntax is valid')
"
```

### 3. 测试渲染
```python
# Python脚本测试模板渲染
from jinja2 import Template

with open('templates/your_template.pre.j2', 'r') as f:
    template_content = f.read()

template = Template(template_content)
test_vars = {
    'cfx_file_path': 'test.cfx',
    'pressure_list': [2187, 2189],
    'max_iterations': 5000
}

rendered = template.render(**test_vars)
print(rendered)
```

## 📞 技术支持

如果在使用模板过程中遇到问题：

1. 检查模板语法是否正确
2. 验证配置文件中的参数名是否匹配
3. 查看生成的.pre文件是否符合预期
4. 检查CFX Pre是否能正确执行生成的脚本

更多高级用法请参考 Jinja2 官方文档：https://jinja.palletsprojects.com/
