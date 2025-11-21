# 日志映射工具 (Log Mapper)

## 简介
这是一个用于自动化整理测试日志文件的工具。它可以遍历指定目录下的 `.blf` 和 `.asc` 文件，根据预定义的 JSON 规则将文件复制并重命名到新的目标目录，同时保持原有的文件夹结构。

本工具提供 **图形界面 (GUI)** 和 **命令行** 两种使用方式。

## 功能特性
*   **自动扫描**: 递归查找源目录下的所有日志文件。
*   **灵活映射**: 支持 JSON 格式的映射规则。
*   **通配符支持**: 规则支持 `*` (任意字符) 和 `?` (单个字符) 通配符。
*   **智能重命名**:
    *   **一对一**: 如果目标目录下只有一个文件匹配规则，直接重命名文件。
    *   **多对一**: 如果目标目录下有多个文件匹配同一规则，自动创建文件夹并保留原文件名。
*   **目录清洗**: 自动移除与文件名同名的父文件夹，以及时间戳格式的文件夹 (如 `2025_6_19_12_18_43`)。
*   **图形界面**: 提供美观的现代化操作界面 (基于 ttkbootstrap)，无需编写代码。

## 快速开始

### 1. 准备规则文件
在任意位置创建 `mapping_rules.json` 文件，定义映射关系。

**格式示例**:
```json
{
    "目标文件名(不含后缀)": [
        "源文件名1",
        "源文件名通配符*"
    ],
    "应用程序有效时正常刷写": [
        "[TG01_TC01_SC02]*",
        "[TG01_TC01_SC01] 应用程序有效时正常刷写测试(9V)"
    ]
}
```

### 2. 运行工具

#### 方式一：使用可执行文件 (推荐)
1.  进入 `dist` 文件夹。
2.  双击运行 `LogMapper.exe`。
3.  在界面中选择：
    *   **源数据目录**: 存放原始日志的文件夹。
    *   **映射规则文件**: 刚才创建的 `mapping_rules.json`。
    *   **目标输出目录**: 整理后的文件存放位置。
4.  点击 **开始处理**。

#### 方式二：运行 Python 脚本
如果您安装了 Python 环境，也可以直接运行脚本：
```bash
pip install ttkbootstrap
python log_mapper_ui.py
```

#### 方式三：命令行模式
```bash
python log_mapper.py "E:\project_data\Test\Data" "mapping_rules.json" "E:\project_data\Test\Report"
```

## 映射逻辑详解

### 文件夹处理
工具会保留源文件的目录结构，但会进行以下优化：
1.  **去重**: 如果父文件夹名称与文件名相同，该层文件夹会被移除。
2.  **去时间戳**: 如果父文件夹名称符合 `YYYY_M_D_H_M_S` 格式，该层文件夹会被移除。

### 文件重命名
假设规则为 `"TargetName": ["SourceA*"]`：

*   **情况 A**: 目录下只有 `SourceA_01.blf`
    *   结果: `.../TargetName.blf`
*   **情况 B**: 目录下有 `SourceA_01.blf` 和 `SourceA_02.blf`
    *   结果:
        *   `.../TargetName/SourceA_01.blf`
        *   `.../TargetName/SourceA_02.blf`

## 开发与打包
如果您修改了源码，可以使用 PyInstaller 重新打包：
```bash
pip install pyinstaller ttkbootstrap
pyinstaller --noconsole --onefile --name "LogMapper" --collect-all ttkbootstrap log_mapper_ui.py
```
打包后的文件位于 `dist` 目录。
