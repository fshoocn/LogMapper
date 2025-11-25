import os
import shutil
import json
import sys
import re

def default_logger(msg):
    print(msg)

def scan_files(src_dir, logger=default_logger):
    """
    遍历查找地址A下所有的blf文件和ASC文件
    返回一个字典: {文件名(含后缀): [完整路径1, 完整路径2, ...]}
    """
    file_map = {}
    # 支持的扩展名，不区分大小写
    valid_extensions = {'.blf', '.asc'}
    
    logger(f"正在扫描目录: {src_dir} ...")
    for root, dirs, files in os.walk(src_dir):
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext in valid_extensions:
                full_path = os.path.join(root, file)
                if file not in file_map:
                    file_map[file] = []
                file_map[file].append(full_path)
    
    logger(f"扫描完成，共找到 {len(file_map)} 个唯一文件名的文件。")
    return file_map

def load_json_file(file_path, logger=default_logger):
    """
    读取 JSON 文件内容
    """
    logger(f"正在读取文件: {file_path} ...")
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception as e:
        logger(f"读取文件失败: {e}")
        return None

def load_rules(rule_file_path, logger=default_logger):
    """
    加载映射规则文件 (JSON格式)
    """
    return load_json_file(rule_file_path, logger) or {}

def process_mapping(file_map, rules, src_root, dst_root, logger=default_logger):
    """
    根据规则复制并重命名文件
    """
    logger("开始处理映射和复制...")
    
    # 1. 预处理 file_map，方便查找。
    file_map_no_ext = {}
    for filename_with_ext, paths in file_map.items():
        name_no_ext, ext = os.path.splitext(filename_with_ext)
        if name_no_ext not in file_map_no_ext:
            file_map_no_ext[name_no_ext] = {}
        if ext not in file_map_no_ext[name_no_ext]:
            file_map_no_ext[name_no_ext][ext] = []
        file_map_no_ext[name_no_ext][ext].extend(paths)

    # 2. 收集所有待处理的任务并分组
    # 结构: key=rule_target, value=[(src_full_path, src_filename_with_ext)]
    tasks = {}

    for rule_target, source_list in rules.items():
        # 找出该规则匹配到的所有源文件名(无后缀)
        matched_source_names = set()
        for pattern in source_list:
            # 检查是否包含通配符 * 或 ?
            if '*' in pattern or '?' in pattern:
                # 将通配符转换为正则表达式
                regex_pattern = re.escape(pattern).replace(r'\*', '.*').replace(r'\?', '.')
                try:
                    regex_obj = re.compile(f'^{regex_pattern}$', re.IGNORECASE)
                    for filename in file_map_no_ext.keys():
                        if regex_obj.match(filename):
                            matched_source_names.add(filename)
                except re.error as e:
                    logger(f"警告: 规则 '{pattern}' 转换正则失败: {e}")
            else:
                # 精确匹配
                if pattern in file_map_no_ext:
                    matched_source_names.add(pattern)
        
        # 对每个匹配到的源文件名，收集文件路径
        for source_name in matched_source_names:
            for ext, paths in file_map_no_ext[source_name].items():
                for src_path in paths:
                    # 不再计算源文件的相对路径，直接归入 rule_target 组
                    if rule_target not in tasks:
                        tasks[rule_target] = []
                    tasks[rule_target].append((src_path, source_name + ext))

    # 3. 执行任务
    count = 0
    for rule_target, src_files in tasks.items():
        # 判断该规则下匹配到的文件数量
        is_multi = len(src_files) > 1
        
        for src_path, src_filename in src_files:
            try:
                if is_multi:
                    # 多对一：创建 Target 文件夹，保留原文件名
                    # rule_target 可能包含相对路径，例如 "Sub/TargetName"
                    final_target_dir = os.path.join(dst_root, rule_target)
                    final_path = os.path.join(final_target_dir, src_filename)
                else:
                    # 一对一：直接重命名为 Target.ext
                    # rule_target 可能包含相对路径，例如 "Sub/TargetName"
                    target_rel_path = os.path.dirname(rule_target) # "Sub" or ""
                    target_name = os.path.basename(rule_target)    # "TargetName"
                    
                    final_target_dir = os.path.join(dst_root, target_rel_path)
                    
                    # 获取后缀
                    _, ext = os.path.splitext(src_filename)
                    final_path = os.path.join(final_target_dir, target_name + ext)
                
                if not os.path.exists(final_target_dir):
                    os.makedirs(final_target_dir)
                
                logger(f"复制: {src_path} -> {final_path}")
                shutil.copy2(src_path, final_path)
                count += 1
            except Exception as e:
                logger(f"复制失败: {src_path}, 错误: {e}")

    logger(f"处理完成，共复制了 {count} 个文件。")

if __name__ == "__main__":
    # 默认配置 (当不使用命令行参数且JSON中无路径时使用)
    default_input_dir = r"E:\project_data\DK033-A1\测试报告\SW007\测试数据"
    default_output_dir = r"D:\fanshuhua\桌面\日志映射工具\新建文件夹"
    default_rule_file = r"mapping_rules.json"

    input_dir_a = default_input_dir
    output_dir_b = default_output_dir
    rule_file = default_rule_file
    
    using_cli_args = False

    # 如果是命令行参数传入
    if len(sys.argv) >= 4:
        input_dir_a = sys.argv[1]
        rule_file = sys.argv[2]
        output_dir_b = sys.argv[3]
        using_cli_args = True

    # 检查规则文件是否存在
    if not os.path.exists(rule_file):
        # 尝试在当前脚本目录下查找
        current_dir = os.path.dirname(os.path.abspath(__file__))
        potential_rule_file = os.path.join(current_dir, "mapping_rules.json")
        if os.path.exists(potential_rule_file):
            rule_file = potential_rule_file
        else:
            print(f"错误: 规则文件不存在: {rule_file}")
            sys.exit(1)

    # 1. 加载规则 (提前加载以获取路径配置)
    json_data = load_rules(rule_file)
    mapping_rules = {}
    
    # 解析规则 (仅支持新格式)
    # 检查是否是新格式 (值是字典且包含 mapping_rules)
    first_key = next(iter(json_data)) if json_data else None
    if first_key and isinstance(json_data[first_key], dict) and "mapping_rules" in json_data[first_key]:
        print(f"检测到多规则集格式，默认使用第一个规则集: {first_key}")
        rule_set = json_data[first_key]
        mapping_rules = rule_set.get("mapping_rules", {})
        
        # 如果没有使用命令行参数，尝试使用配置文件中的路径
        if not using_cli_args:
             if "src_dir" in rule_set and rule_set["src_dir"]:
                 input_dir_a = rule_set["src_dir"]
             if "dst_dir" in rule_set and rule_set["dst_dir"]:
                 output_dir_b = rule_set["dst_dir"]
    else:
        print("错误: 规则文件格式不正确，仅支持包含 'mapping_rules' 的新格式。")
        sys.exit(1)

    if not mapping_rules:
        print("错误: 有效规则为空！")
        sys.exit(1)

    print(f"源目录: {input_dir_a}")
    print(f"目标目录: {output_dir_b}")

    # 检查输入目录是否存在
    if not os.path.exists(input_dir_a):
        print(f"错误: 输入目录不存在: {input_dir_a}")
        sys.exit(1)

    # 2. 扫描文件
    files_map = scan_files(input_dir_a)
    
    # 3. 执行映射和复制
    process_mapping(files_map, mapping_rules, input_dir_a, output_dir_b)
