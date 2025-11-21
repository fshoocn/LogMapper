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

def load_rules(rule_file_path, logger=default_logger):
    """
    加载映射规则文件 (JSON格式)
    返回字典: {目标文件名: [源文件名列表]}
    """
    rules = {}
    logger(f"正在加载规则文件: {rule_file_path} ...")
    try:
        with open(rule_file_path, 'r', encoding='utf-8-sig') as f:
            rules = json.load(f)
    except Exception as e:
        logger(f"加载规则文件失败: {e}")
        return {}
        
    count = sum(len(v) for v in rules.values())
    logger(f"加载完成，共 {len(rules)} 个目标组，包含 {count} 个源文件规则。")
    return rules

def process_mapping(file_map, rules, src_root, dst_root, logger=default_logger):
    """
    根据规则复制并重命名文件
    """
    logger("开始处理映射和复制...")
    
    # 1. 预处理 file_map，方便查找。
    # 新结构: {文件名无后缀: {后缀: [路径列表]}}
    file_map_no_ext = {}
    for filename_with_ext, paths in file_map.items():
        name_no_ext, ext = os.path.splitext(filename_with_ext)
        if name_no_ext not in file_map_no_ext:
            file_map_no_ext[name_no_ext] = {}
        if ext not in file_map_no_ext[name_no_ext]:
            file_map_no_ext[name_no_ext][ext] = []
        file_map_no_ext[name_no_ext][ext].extend(paths)

    # 2. 收集所有待处理的任务并分组
    # 结构: key=(dst_dir_path, target_name_no_ext), value=[(src_full_path, src_filename_with_ext)]
    # 这样可以判断在同一个目标目录下，是否有多个文件映射到同一个 Target
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
        
        # 对每个匹配到的源文件名，处理其具体文件路径
        for source_name in matched_source_names:
            for ext, paths in file_map_no_ext[source_name].items():
                for src_path in paths:
                    # 计算目标基础目录 (base_target_dir)
                    rel_path = os.path.relpath(src_path, src_root)
                    rel_dir = os.path.dirname(rel_path)
                    
                    # 特殊情况处理：移除 "文件名同名文件夹" 和 "时间戳文件夹"
                    target_rel_dir = rel_dir
                    while True:
                        parent_dir_name = os.path.basename(target_rel_dir)
                        if not parent_dir_name:
                            break
                            
                        # 检查是否是时间戳 (例如 2025_6_19_12_18_43)
                        is_timestamp = bool(re.match(r'^\d{4}_\d{1,2}_\d{1,2}_\d{1,2}_\d{1,2}_\d{1,2}$', parent_dir_name))
                        
                        # 检查是否与源文件名一致
                        is_same_name = (parent_dir_name == source_name)
                        
                        if is_timestamp or is_same_name:
                            target_rel_dir = os.path.dirname(target_rel_dir)
                        else:
                            break
                        
                    base_target_dir = os.path.join(dst_root, target_rel_dir)
                    
                    # 将任务加入分组
                    key = (base_target_dir, rule_target)
                    if key not in tasks:
                        tasks[key] = []
                    tasks[key].append((src_path, source_name + ext))

    # 3. 执行任务
    count = 0
    for (base_target_dir, rule_target), src_files in tasks.items():
        # 判断该目录下，映射到该 Target 的文件数量
        # 如果 > 1，说明在该目录下有多个文件映射到同一个 Target -> 创建文件夹
        # 如果 == 1，说明在该目录下只有一个文件映射到该 Target -> 直接重命名
        is_multi = len(src_files) > 1
        
        for src_path, src_filename in src_files:
            try:
                if is_multi:
                    # 多对一：创建 Target 文件夹，保留原文件名
                    final_target_dir = os.path.join(base_target_dir, rule_target)
                    final_path = os.path.join(final_target_dir, src_filename)
                else:
                    # 一对一：直接重命名为 Target.ext
                    final_target_dir = base_target_dir
                    # 获取后缀
                    _, ext = os.path.splitext(src_filename)
                    final_path = os.path.join(final_target_dir, rule_target + ext)
                
                if not os.path.exists(final_target_dir):
                    os.makedirs(final_target_dir)
                
                logger(f"复制: {src_path} -> {final_path}")
                shutil.copy2(src_path, final_path)
                count += 1
            except Exception as e:
                logger(f"复制失败: {src_path}, 错误: {e}")

    logger(f"处理完成，共复制了 {count} 个文件。")

if __name__ == "__main__":
    # 配置区域
    # 输入地址 A
    input_dir_a = r"E:\project_data\DK033-A1\测试报告\SW007\测试数据"
    # 输出地址 B
    output_dir_b = r"D:\fanshuhua\桌面\日志映射工具\新建文件夹"
    # 映射规则文件路径
    rule_file = r"mapping_rules.json"

    # 如果是命令行参数传入，可以在这里修改
    if len(sys.argv) >= 4:
        input_dir_a = sys.argv[1]
        rule_file = sys.argv[2]
        output_dir_b = sys.argv[3]

    # 检查路径是否存在
    if not os.path.exists(input_dir_a):
        print(f"错误: 输入目录不存在: {input_dir_a}")
        # sys.exit(1) # 如果需要强制退出取消注释
    
    if not os.path.exists(rule_file):
        # 尝试在当前脚本目录下查找
        current_dir = os.path.dirname(os.path.abspath(__file__))
        rule_file = os.path.join(current_dir, "mapping_rules.json")
        if not os.path.exists(rule_file):
            print(f"错误: 规则文件不存在: {rule_file}")
            sys.exit(1)

    # 1. 扫描文件
    files_map = scan_files(input_dir_a)
    
    # 2. 加载规则
    mapping_rules = load_rules(rule_file)
    
    # 3. 执行映射和复制
    process_mapping(files_map, mapping_rules, input_dir_a, output_dir_b)
