import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import sys
import json
import log_mapper

class LogMapperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("日志映射工具 (Log Mapper)")
        self.root.geometry("700x650")
        
        # 变量
        self.src_dir = ttk.StringVar()
        self.rule_file = ttk.StringVar()
        self.dst_dir = ttk.StringVar()
        self.rule_set_var = ttk.StringVar()

        # 布局
        self.create_widgets()

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 标题
        title_label = ttk.Label(main_frame, text="日志映射工具", font=("微软雅黑", 18, "bold"), bootstyle="primary")
        title_label.pack(pady=(0, 20))

        # 1. 规则文件 (Moved to top)
        self.rule_entry, self.rule_btn = self.create_input_group(main_frame, "映射规则文件 (JSON):", self.rule_file, self.browse_rule)

        # 2. 规则集选择
        self.create_combobox_group(main_frame, "选择映射规则集:", self.rule_set_var)

        # 3. 源目录 (Initially disabled)
        self.src_entry, self.src_btn = self.create_input_group(main_frame, "源数据目录 (Address A):", self.src_dir, self.browse_src, state=DISABLED)

        # 4. 目标目录 (Initially disabled)
        self.dst_entry, self.dst_btn = self.create_input_group(main_frame, "目标输出目录 (Address B):", self.dst_dir, self.browse_dst, state=DISABLED)

        # 5. 开始按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=20)
        start_btn = ttk.Button(btn_frame, text="开始处理", command=self.start_processing, bootstyle="success", width=20)
        start_btn.pack()

        # 6. 日志输出
        ttk.Label(main_frame, text="运行日志:", font=("微软雅黑", 10, "bold")).pack(anchor=W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill=BOTH, expand=YES)

    def create_input_group(self, parent, label_text, variable, command, state=NORMAL):
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)
        
        ttk.Label(frame, text=label_text, width=25).pack(side=LEFT, anchor=W)
        
        entry = ttk.Entry(frame, textvariable=variable, state=state)
        entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        btn = ttk.Button(frame, text="浏览", command=command, bootstyle="secondary-outline", state=state)
        btn.pack(side=LEFT)
        return entry, btn

    def create_combobox_group(self, parent, label_text, variable):
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)
        
        ttk.Label(frame, text=label_text, width=25).pack(side=LEFT, anchor=W)
        
        self.rule_set_combo = ttk.Combobox(frame, textvariable=variable, state="readonly")
        self.rule_set_combo.pack(side=LEFT, fill=X, expand=YES, padx=5)
        self.rule_set_combo.bind("<<ComboboxSelected>>", self.on_rule_set_changed)
        
        # 占位按钮，保持对齐
        ttk.Label(frame, width=8).pack(side=LEFT) # 这里的宽度大概对应 "浏览" 按钮的宽度

    def on_rule_set_changed(self, event):
        selection = self.rule_set_var.get()
        if hasattr(self, 'current_json_data') and self.current_json_data:
            if selection in self.current_json_data:
                rule_data = self.current_json_data[selection]
                if isinstance(rule_data, dict):
                    if "src_dir" in rule_data:
                        self.src_dir.set(rule_data["src_dir"])
                    if "dst_dir" in rule_data:
                        self.dst_dir.set(rule_data["dst_dir"])

    def browse_src(self):
        path = filedialog.askdirectory()
        if path:
            self.src_dir.set(path)

    def browse_dst(self):
        path = filedialog.askdirectory()
        if path:
            self.dst_dir.set(path)

    def browse_rule(self):
        path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
        if path:
            self.rule_file.set(path)
            self.load_config(path)

    def load_config(self, path):
        data = log_mapper.load_json_file(path, logger=self.log)
        if not data:
            return
        
        # Enable widgets
        self.src_entry.configure(state=NORMAL)
        self.src_btn.configure(state=NORMAL)
        self.dst_entry.configure(state=NORMAL)
        self.dst_btn.configure(state=NORMAL)

        self.current_json_data = data
        
        # Check format
        # New format: keys are rule set names, values are dicts containing "mapping_rules"
        is_new_format = False
        first_key = next(iter(data)) if data else None
        if first_key and isinstance(data[first_key], dict) and "mapping_rules" in data[first_key]:
            is_new_format = True
            
        if is_new_format:
            rule_sets = list(data.keys())
            self.rule_set_combo['values'] = rule_sets
            if rule_sets:
                self.rule_set_combo.current(0)
                self.on_rule_set_changed(None) # Trigger update
        else:
            self.log("错误: 规则文件格式不正确，仅支持包含 'mapping_rules' 的新格式。")
            self.rule_set_combo['values'] = []
            self.rule_set_combo.set('')

    def save_config(self):
        path = self.rule_file.get()
        if not path or not os.path.exists(path):
            return

        try:
            with open(path, 'r', encoding='utf-8-sig') as f:
                data = json.load(f)
        except:
            data = {}
            
        current_set = self.rule_set_var.get()
        
        # Check format again to decide how to save
        is_new_format = False
        if current_set in data and isinstance(data[current_set], dict) and "mapping_rules" in data[current_set]:
            is_new_format = True
            
        if is_new_format:
            data[current_set]["src_dir"] = self.src_dir.get()
            data[current_set]["dst_dir"] = self.dst_dir.get()
            
            try:
                with open(path, 'w', encoding='utf-8-sig') as f:
                    json.dump(data, f, indent=4, ensure_ascii=False)
            except Exception as e:
                self.log(f"保存配置失败: {e}")

    def log(self, message):
        self.root.after(0, self._update_log_text, message)

    def _update_log_text(self, message):
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)

    def start_processing(self):
        src = self.src_dir.get()
        rule = self.rule_file.get()
        dst = self.dst_dir.get()
        rule_set_name = self.rule_set_var.get()

        if not src or not rule or not dst:
            messagebox.showwarning("警告", "请填写所有路径！")
            return

        if not os.path.exists(src):
            messagebox.showerror("错误", "源目录不存在！")
            return
        
        if not os.path.exists(rule):
            messagebox.showerror("错误", "规则文件不存在！")
            return

        # 保存配置
        self.save_config()

        # 清空日志
        self.log_text.delete(1.0, END)
        self.log("正在启动任务...")
        
        # 在新线程中运行
        threading.Thread(target=self.run_logic, args=(src, rule, dst, rule_set_name), daemon=True).start()

    def run_logic(self, src, rule_path, dst, rule_set_name):
        try:
            # 1. 扫描
            files_map = log_mapper.scan_files(src, logger=self.log)
            
            # 2. 加载规则
            json_data = log_mapper.load_json_file(rule_path, logger=self.log)
            
            mapping_rules = {}
            
            # Check format
            if rule_set_name in json_data and isinstance(json_data[rule_set_name], dict) and "mapping_rules" in json_data[rule_set_name]:
                # New format
                mapping_rules = json_data[rule_set_name]["mapping_rules"]
                self.log(f"使用规则集: {rule_set_name}")
            else:
                self.log("错误: 规则文件格式不正确或未找到规则集。")
                return

            if not mapping_rules:
                self.log("错误: 有效规则为空！")
                return
            
            # 3. 处理
            log_mapper.process_mapping(files_map, mapping_rules, src, dst, logger=self.log)
            
            self.log("任务全部完成！")
            self.root.after(0, lambda: messagebox.showinfo("成功", "处理完成！"))
        except Exception as e:
            self.log(f"发生错误: {e}")
            self.root.after(0, lambda: messagebox.showerror("错误", f"运行中发生错误:\n{e}"))

if __name__ == "__main__":
    # 使用 cosmo 主题，看起来比较现代和干净
    root = ttk.Window(themename="cosmo")
    app = LogMapperUI(root)
    root.mainloop()


# pyinstaller --noconsole --onefile --name "LogMapper" d:\fanshuhua\桌面\日志映射工具\log_mapper_ui.py