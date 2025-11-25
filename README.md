# 日志映射工具 (Log Mapper)

## 简介
这是一个用于自动化整理测试日志文件的工具。它可以遍历指定目录下的 `.blf` 和 `.asc` 文件，根据预定义的 JSON 规则将文件复制并重命名到新的目标目录。

本工具提供 **图形界面 (GUI)** 和 **命令行** 两种使用方式。

## 功能特性
*   **自动扫描**: 递归查找源目录下的所有日志文件。
*   **多规则集支持**: 单个 JSON 文件可包含多套映射规则，通过下拉菜单快速切换。
*   **配置持久化**: 自动保存源目录和目标目录配置到 JSON 文件中。
*   **灵活映射**:
    *   支持 **相对路径** 导出（例如 `子文件夹/目标文件名`）。
    *   支持 `*` (任意字符) 和 `?` (单个字符) 通配符匹配源文件。
*   **智能重命名**:
    *   **一对一**: 如果规则匹配单个文件，直接重命名为目标文件名。
    *   **多对一**: 如果规则匹配多个文件，自动创建目标文件夹并保留原文件名。
*   **图形界面**: 提供美观的现代化操作界面 (基于 ttkbootstrap)，交互流程优化。

## 快速开始

### 1. 准备规则文件 (JSON v2 格式)
在任意位置创建 `mapping_rules.json` 文件。新版格式支持多规则集：

```json
{
    "默认规则集": {
        "src_dir": "D:/Logs/Input",
        "dst_dir": "D:/Logs/Output",
        "mapping_rules": {
            "目标文件名(不含后缀)": [
                "源文件名1",
                "源文件名通配符*"
            ],
            "子文件夹/特定测试/应用程序刷写": [
                "[TG01_TC01_SC02]*"
            ]
        }
    },
    "项目B规则集": {
        "src_dir": "E:/ProjectB/Data",
        "dst_dir": "E:/ProjectB/Report",
        "mapping_rules": {
            ...
        }
    }
}
```

### 2. 运行工具

#### 方式一：使用可执行文件 (推荐)
1.  进入 `dist` 文件夹，双击运行 `LogMapper.exe`。
2.  **第一步**：点击顶部的“浏览”选择 **映射规则文件**。
    *   *注意：未加载规则文件前，目录选择框处于禁用状态。*
3.  **第二步**：在“选择映射规则集”下拉框中选择要使用的规则。
    *   工具会自动加载该规则集保存的源目录和目标目录。
4.  **第三步**：确认或修改 **源数据目录** 和 **目标输出目录**。
5.  点击 **开始处理**。
    *   *注意：点击开始后，当前的路径配置会自动保存回 JSON 文件。*

#### 方式二：运行 Python 脚本
如果您安装了 Python 环境，也可以直接运行脚本：
```bash
pip install ttkbootstrap
python log_mapper_ui.py
```

## 映射逻辑详解

### 路径生成规则
新版工具不再依赖源文件的目录结构，而是完全根据 **目标输出目录** + **规则定义的相对路径** 生成最终位置。

假设目标目录为 `D:\Output`，规则为 `"FolderA/TargetName": ["Source*"]`：

*   **情况 A (一对一)**: 目录下只有 `Source_01.blf`
    *   结果: `D:\Output\FolderA\TargetName.blf`
*   **情况 B (多对一)**: 目录下有 `Source_01.blf` 和 `Source_02.blf`
    *   结果:
        *   `D:\Output\FolderA\TargetName\Source_01.blf`
        *   `D:\Output\FolderA\TargetName\Source_02.blf`

## 开发与打包
如果您修改了源码，可以使用 PyInstaller 重新打包：
```bash
pip install pyinstaller ttkbootstrap
pyinstaller --noconsole --onefile --name "LogMapper" --collect-all ttkbootstrap log_mapper_ui.py
```
打包后的文件位于 `dist` 目录。
