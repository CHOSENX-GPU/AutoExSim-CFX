# CFX模板自定义快速入门

## 🎯 目标
学会如何自定义CFX .pre模板并在配置中使用，实现灵活的参数化CFX分析。

## ⏱️ 预计时间
15-30分钟

## 📋 前提条件
- 已安装CFX自动化系统
- 熟悉基本的CFX操作
- 了解YAML配置文件格式

---

## 🚀 步骤1：了解模板文件

### 查看现有模板
```bash
# 查看模板目录
ls templates/

# 输出:
# create_def.pre.j2              # 基础模板
# create_def_simple.pre.j2       # 简化模板  
# create_def_advanced.pre.j2     # 高级模板
```

### 基础模板语法
模板使用Jinja2语法，主要元素：

```jinja2
{{ variable_name }}              # 变量替换
{{ variable | default("值") }}   # 带默认值的变量
{% if condition %}...{% endif %} # 条件判断
{% for item in list %}...{% endfor %} # 循环
{# 这是注释 #}                   # 注释
```

---

## 🛠️ 步骤2：创建第一个自定义模板

### 复制基础模板
```bash
cp templates/create_def_simple.pre.j2 templates/my_first_template.pre.j2
```

### 编辑模板文件
在 `templates/my_first_template.pre.j2` 中修改：

```jinja2
COMMAND FILE:
  CFX Pre Version = {{ cfx_version | default("22.1") }}
END

{# 加载你的CFX文件 #}
>load filename={{ cfx_file_path }}, mode=cfx, overwrite=yes
> update

{# 压力参数数组 #}
!@P_def = ({{ pressure_list | join(',') }});

! foreach $P (@P_def) {
    !$path_name = ".";
    !mkdir $path_name."/{{ folder_prefix | default('Result_') }}$P/";

    FLOW: {{ flow_analysis_name | default("Flow Analysis 1") }}
        DOMAIN: {{ domain_name | default("Domain") }}
            &replace BOUNDARY: {{ outlet_boundary_name | default("Outlet") }}
                Boundary Type = OUTLET
                Location = {{ outlet_location | default("Entire OUTLET") }}
                BOUNDARY CONDITIONS:
                    FLOW REGIME:
                        Option = Subsonic
                    END
                    MASS AND MOMENTUM:
                        Option = Average Static Pressure
                        Pressure Profile Blend = {{ pressure_blend | default("0.05") }}
                        Relative Pressure = $P [{{ pressure_unit | default("Pa") }}]
                    END
                END
            END
        END
        
        {# 可选：添加自定义求解器设置 #}
        {% if custom_solver_settings %}
        &replace SOLVER CONTROL:
            CONVERGENCE CONTROL:
                Maximum Number of Iterations = {{ max_iterations | default("3000") }}
            END
            CONVERGENCE CRITERIA:
                Residual Target = {{ residual_target | default("0.00001") }}
            END
        END
        {% endif %}
    END

    > update
    !$file_name = "{{ folder_prefix | default('Result_') }}$P";
    !$def_name = "$P";
    > writeCaseFile filename=$path_name/$file_name/$def_name.def, operation=write def file
    > update
! }
> update
```

---

## ⚙️ 步骤3：创建配置文件

创建 `config/my_first_project.yaml`：

```yaml
# 指定使用你的自定义模板
pre_template_path: "templates/my_first_template.pre.j2"

# 项目基础设置
project_name: "My_First_CFX_Project"
cfx_mode: "local"
auto_detect_cfx: true

# CFX文件和参数
cfx_file_path: "your_model.cfx"      # 替换为你的CFX文件路径
cfx_version: "22.1"
pressure_list: [2000, 2500, 3000]   # 你要研究的压力值

# 模型参数（对应模板中的变量）
flow_analysis_name: "My Flow Analysis"
domain_name: "Main Domain"
outlet_boundary_name: "Main Outlet"
outlet_location: "Entire OUTLET_REGION"
pressure_unit: "Pa"
pressure_blend: "0.05"

# 输出设置
folder_prefix: "Pressure_"           # 结果文件夹前缀
def_file_prefix: "Case_"            # def文件前缀

# 可选：自定义求解器设置
custom_solver_settings: true        # 启用自定义求解器设置
max_iterations: 4000
residual_target: "0.000001"

# 服务器连接（如果需要）
ssh_host: "your.cluster.address"
ssh_user: "your_username"
remote_base_path: "/home/your_username/CFX_Jobs"

# 其他标准设置
cluster_type: "university"
scheduler_type: "SLURM"
enable_node_detection: false
enable_monitoring: true
```

---

## 🧪 步骤4：测试你的模板

### 干运行测试
```bash
# 测试模板生成（不实际执行）
python main.py --config config/my_first_project.yaml --dry-run --pressures 2000 2500 3000
```

### 检查生成的文件
查看生成的.pre文件内容是否正确：

```bash
# 查看生成的pre文件
cat output_directory/generated_script.pre
```

应该看到类似内容：
```
COMMAND FILE:
  CFX Pre Version = 22.1
END

>load filename=your_model.cfx, mode=cfx, overwrite=yes
> update

!@P_def = (2000,2500,3000);

! foreach $P (@P_def) {
    !$path_name = ".";
    !mkdir $path_name."/Pressure_$P/";
    
    FLOW: My Flow Analysis
        DOMAIN: Main Domain
            &replace BOUNDARY: Main Outlet
                ...
```

---

## 🎨 步骤5：进阶自定义

### 添加条件逻辑
```jinja2
{# 根据压力值设置不同的迭代次数 #}
{% if pressure_value > 5000 %}
Maximum Number of Iterations = 8000
{% else %}
Maximum Number of Iterations = 5000
{% endif %}
```

### 添加循环处理
```jinja2
{# 处理多个监测点 #}
{% for monitor in custom_monitors | default([]) %}
MONITOR POINT: {{ monitor.name }}
    Expression Value = {{ monitor.expression }}
    Option = Expression
END
{% endfor %}
```

### 在配置中使用
```yaml
custom_monitors:
  - name: "Mass Flow In"
    expression: "massFlow()@Inlet"
  - name: "Mass Flow Out"
    expression: "massFlow()@Outlet"
  - name: "Pressure Drop"
    expression: "areaAve(Total Pressure)@Inlet - areaAve(Pressure)@Outlet"
```

---

## ✅ 步骤6：运行完整流程

### 首次运行
```bash
# 完整运行（如果有服务器连接）
python main.py --config config/my_first_project.yaml --pressures 2000 2500 3000

# 或者仅生成文件（本地测试）
python main.py --config config/my_first_project.yaml --mode step --step generate_pre --pressures 2000 2500 3000
```

### 验证结果
检查是否生成了预期的文件结构：
```
output_directory/
├── Pressure_2000/
│   └── 2000.def
├── Pressure_2500/
│   └── 2500.def
└── Pressure_3000/
    └── 3000.def
```

---

## 🔧 常见问题解决

### 问题1：模板语法错误
**错误信息**: `TemplateSyntaxError`

**解决方法**:
```bash
# 检查模板语法
python -c "
from jinja2 import Template
with open('templates/my_first_template.pre.j2', 'r') as f:
    Template(f.read())
print('Template syntax is valid')
"
```

### 问题2：变量未定义
**错误信息**: `UndefinedError: 'variable_name' is undefined`

**解决方法**:
- 在配置文件中添加缺失的变量
- 或在模板中使用默认值：`{{ variable_name | default("default_value") }}`

### 问题3：生成的pre文件不正确
**解决方法**:
1. 使用`--dry-run`模式检查生成的内容
2. 确认配置文件中的参数名与模板中的变量名匹配
3. 检查Jinja2语法是否正确

---

## 📚 下一步学习

### 高级主题
1. **多域模板**: 处理复杂的多域CFX模型
2. **参数化几何**: 结合CFX的几何参数化功能
3. **自动化后处理**: 添加CFX-Post的自动化处理

### 参考资源
- [完整模板语法指南](./TEMPLATE_GUIDE.md)
- [配置示例集合](./TEMPLATE_EXAMPLES.md)
- [系统架构文档](./ARCHITECTURE.md)

### 实践建议
1. 从简单模板开始，逐步增加复杂性
2. 为每个项目创建专门的模板
3. 维护模板的版本控制
4. 定期测试模板的兼容性

---

## 🎉 恭喜！

你已经学会了CFX模板自定义的基础知识。现在可以：

✅ 创建自定义.pre模板  
✅ 在配置文件中设置模板参数  
✅ 使用条件逻辑和循环  
✅ 测试和调试模板  
✅ 运行参数化CFX分析  

继续探索更高级的功能，让CFX分析更加高效和自动化！
