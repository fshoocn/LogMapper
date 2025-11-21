import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from tkinter import filedialog, messagebox, scrolledtext
import threading
import os
import sys
import log_mapper

class LogMapperUI:
    def __init__(self, root):
        self.root = root
        self.root.title("日志映射工具 (Log Mapper)")
        self.root.geometry("700x600")
        
        # 变量
        self.src_dir = ttk.StringVar()
        self.rule_file = ttk.StringVar()
        self.dst_dir = ttk.StringVar()

        # 布局
        self.create_widgets()

    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=BOTH, expand=YES)

        # 标题
        title_label = ttk.Label(main_frame, text="日志映射工具", font=("微软雅黑", 18, "bold"), bootstyle="primary")
        title_label.pack(pady=(0, 20))

        # 1. 源目录
        self.create_input_group(main_frame, "源数据目录 (Address A):", self.src_dir, self.browse_src)

        # 2. 规则文件
        self.create_input_group(main_frame, "映射规则文件 (JSON):", self.rule_file, self.browse_rule)

        # 3. 目标目录
        self.create_input_group(main_frame, "目标输出目录 (Address B):", self.dst_dir, self.browse_dst)

        # 4. 开始按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=X, pady=20)
        start_btn = ttk.Button(btn_frame, text="开始处理", command=self.start_processing, bootstyle="success", width=20)
        start_btn.pack()

        # 5. 日志输出
        ttk.Label(main_frame, text="运行日志:", font=("微软雅黑", 10, "bold")).pack(anchor=W, pady=(10, 5))
        self.log_text = scrolledtext.ScrolledText(main_frame, height=15, font=("Consolas", 9))
        self.log_text.pack(fill=BOTH, expand=YES)

    def create_input_group(self, parent, label_text, variable, command):
        frame = ttk.Frame(parent)
        frame.pack(fill=X, pady=5)
        
        ttk.Label(frame, text=label_text, width=25).pack(side=LEFT, anchor=W)
        
        entry = ttk.Entry(frame, textvariable=variable)
        entry.pack(side=LEFT, fill=X, expand=YES, padx=5)
        
        btn = ttk.Button(frame, text="浏览", command=command, bootstyle="secondary-outline")
        btn.pack(side=LEFT)

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

    def log(self, message):
        self.root.after(0, self._update_log_text, message)

    def _update_log_text(self, message):
        self.log_text.insert(END, message + "\n")
        self.log_text.see(END)

    def start_processing(self):
        src = self.src_dir.get()
        rule = self.rule_file.get()
        dst = self.dst_dir.get()

        if not src or not rule or not dst:
            messagebox.showwarning("警告", "请填写所有路径！")
            return

        if not os.path.exists(src):
            messagebox.showerror("错误", "源目录不存在！")
            return
        
        if not os.path.exists(rule):
            messagebox.showerror("错误", "规则文件不存在！")
            return

        # 清空日志
        self.log_text.delete(1.0, END)
        self.log("正在启动任务...")
        
        # 在新线程中运行
        threading.Thread(target=self.run_logic, args=(src, rule, dst), daemon=True).start()

    def run_logic(self, src, rule, dst):
        try:
            # 1. 扫描
            files_map = log_mapper.scan_files(src, logger=self.log)
            
            # 2. 加载规则
            mapping_rules = log_mapper.load_rules(rule, logger=self.log)
            
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