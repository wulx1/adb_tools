# -*- coding: utf-8 -*-
# @Time : 2025/3/24 20:27
# @Author : longswu
# @File : main.py

import shlex
import shutil
import sys
import tkinter as tk
from datetime import datetime
from tkinter import ttk, filedialog, messagebox, scrolledtext, simpledialog
import threading
import subprocess
import logging
import re
import os
import time
from typing import List, Optional

class ADBGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ADB小工具")
        self.root.geometry("1000x800")
        self.root.withdraw()  # 先隐藏窗口
        self.adb_path = self._find_adb()
        self.devices = []
        self.current_device = None
        self.logcat_process = None

        # 初始化UI
        self._init_ui()
        self._center_window()
        self.root.deiconify()  # 设置完成后再显示
    def _center_window(self):
        """无闪烁居中方案"""
        self.root.update_idletasks()
        width = 1000
        height = 800
        x = (self.root.winfo_screenwidth() - width) // 2
        y = (self.root.winfo_screenheight() - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")

    def _init_ui(self):
        """初始化用户界面"""
        # 设备管理区域
        device_frame = ttk.LabelFrame(self.root, text="设备管理", padding=10)
        device_frame.pack(fill=tk.X, padx=10, pady=5)

        self.device_combobox = ttk.Combobox(device_frame, state="readonly")
        self.device_combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        ttk.Button(device_frame, text="刷新设备", command=self.refresh_devices).pack(side=tk.LEFT, padx=5)
        ttk.Button(device_frame, text="设备信息", command=self.show_device_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(device_frame, text="无线连接", command=self.wireless_connect).pack(side=tk.LEFT, padx=5)
        ttk.Button(device_frame, text="重启设备", command=self.reboot_device).pack(side=tk.LEFT, padx=5)

        # 应用管理区域
        app_frame = ttk.LabelFrame(self.root, text="应用管理", padding=10)
        app_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(app_frame, text="安装APK", command=self.install_apk).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="应用列表", command=self.list_installed_apps).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="进程信息", command=self.show_process_info).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="启动应用", command=self.start_apk).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="卸载应用", command=self.uninstall_app).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="清除数据", command=self.clear_app_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(app_frame, text="杀掉进程", command=self.kill_current_app_process).pack(side=tk.LEFT, padx=5)

        # 文件管理区域
        file_frame = ttk.LabelFrame(self.root, text="文件管理", padding=10)
        file_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(file_frame, text="上传文件", command=self.push_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="下载文件", command=self.pull_file).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="获取SP游戏日志", command=self.get_letsgoLOG).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="获取SP体验包游戏日志", command=self.get_readygoLOG).pack(side=tk.LEFT, padx=5)
        ttk.Button(file_frame, text="获取adb日志", command=self.get_adbLOG).pack(side=tk.LEFT, padx=5)

        # 屏幕操作区域
        screen_frame = ttk.LabelFrame(self.root, text="屏幕操作", padding=10)
        screen_frame.pack(fill=tk.X, padx=10, pady=5)

        ttk.Button(screen_frame, text="截图", command=self.take_screenshot).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="录屏", command=self.record_screen).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="开始录屏", command=self.start_recording).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="停止录屏", command=self.stop_recording).pack(side=tk.LEFT, padx=5)

        # 其他操作
        screen_frame = ttk.LabelFrame(self.root, text="其他操作", padding=10)
        screen_frame.pack(fill=tk.X, padx=10, pady=5)
        ttk.Button(screen_frame, text="模拟点击", command=self.simulate_tap).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="输入文本", command=self.input_text).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="Home键", command=lambda: self.send_keyevent("KEYCODE_HOME")).pack(side=tk.LEFT,padx=5)
        ttk.Button(screen_frame, text="返回键", command=lambda: self.send_keyevent("KEYCODE_BACK")).pack(side=tk.LEFT,padx=5)
        ttk.Button(screen_frame, text="电源键", command=lambda: self.send_keyevent("KEYCODE_POWER")).pack(side=tk.LEFT,padx=5)
        ttk.Button(screen_frame, text="设置分辨率", command=self.set_screen_resolution).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="常亮开启", command=lambda: self.set_screen_timeout(0)).pack(side=tk.LEFT, padx=5)
        ttk.Button(screen_frame, text="常亮关闭", command=lambda: self.set_screen_timeout(30000)).pack(side=tk.LEFT,padx=5)

        # 日志区域
        log_frame = ttk.LabelFrame(self.root, text="日志输出", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        ttk.Button(log_frame, text="开始日志", command=self.start_logcat).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_frame, text="停止日志", command=self.stop_logcat).pack(side=tk.LEFT, padx=5)
        ttk.Button(log_frame, text="清空日志", command=self.clear_log).pack(side=tk.RIGHT, padx=2)
        ttk.Button(log_frame, text="保存日志", command=self.save_log).pack(side=tk.RIGHT, padx=2)

        # 初始化设备列表
        self.refresh_devices()

    def _execute_adb(self, command: str, device: Optional[str] = None) -> str:
        """执行ADB命令"""
        device = device or self.current_device
        if not device:
            raise ValueError("未选择设备")
        full_cmd = f"{self.adb_path} -s {device} {command}"
        try:
            result = subprocess.check_output(full_cmd, shell=True, stderr=subprocess.STDOUT).decode("utf-8").strip()
            self.log(f"执行命令: {full_cmd}\n结果: {result}")
            return result
        except subprocess.CalledProcessError as e:
            self.log(f"命令执行失败: {e.output.decode().strip()}")
            raise

    def log(self, message: str):
        """在日志区域显示消息"""
        self.log_text.insert(tk.END, f"{message}\n")
        # self.log_text.insert(tk.END, f"{datetime.now().strftime('%H:%M:%S')} - {message}\n")
        self.log_text.see(tk.END)

    def refresh_devices(self):
        """刷新设备列表"""
        self.devices = self._get_devices()
        self.device_combobox["values"] = self.devices
        if self.devices:
            self.device_combobox.current(0)
            self.current_device = self.devices[0]
            self.log(f"已选择设备: {self.current_device}")
        else:
            self.log("未找到设备")

    def _get_devices(self) -> List[str]:
        """获取已连接设备列表"""
        result = subprocess.check_output(f"{self.adb_path} devices", shell=True).decode("utf-8")
        return [line.split("\t")[0] for line in result.splitlines()[1:] if line.strip()]

    def reboot_device(self):
        """重启设备"""
        if messagebox.askyesno("确认", "确定要重启设备吗？"):
            self._execute_adb("reboot")
            self.log("设备已重启")

    def install_apk(self):
        """安装APK"""
        apk_path = filedialog.askopenfilename(title="选择APK文件", filetypes=[("APK文件", "*.apk")])
        if apk_path:
            self._execute_adb(f"install {apk_path}")
            self.log(f"已安装APK: {apk_path}")

    def start_apk(self):
        """启动APK"""
        package_name = "com.tencent.letsgo/com.epicgames.ue4.GameActivityExt"
        package_name = simpledialog.askstring(
            "启动应用",
            "请输入要启动的包名：",
            initialvalue="com.tencent.letsgo/com.epicgames.ue4.GameActivityExt"  # 提供默认值
        )
        if package_name and self._check_device():
            try:
                self._execute_adb(f"shell am start -n {package_name}")
                self.log(f"已启动: {package_name}")
            except Exception as e:
                self.log(f"启动失败: {str(e)}")
    def uninstall_app(self):
        """卸载应用"""
        # package_name = simpledialog.askstring("卸载应用", "请输入包名：")
        package_name = "com.tencent.letsgo"
        package_name = simpledialog.askstring(
            "卸载应用",
            "请输入要卸载的包名：",
            initialvalue="com.tencent.letsgo"  # 提供默认值
        )
        if package_name and self._check_device():
            try:
                self._execute_adb(f"uninstall {package_name}")
                self.log(f"已卸载: {package_name}")
            except Exception as e:
                self.log(f"卸载失败: {str(e)}")

    def clear_app_data(self):
        """清除应用数据"""
        package_name = "com.tencent.letsgo"
        package_name = simpledialog.askstring(
            "清掉数据",
            "请输入要清掉数据的包名：",
            initialvalue="com.tencent.letsgo"  # 提供默认值
        )
        if package_name:
            self._execute_adb(f"shell pm clear {package_name}")
            self.log(f"已清除应用数据: {package_name}")

    def kill_current_app_process(self):
        """智能终止当前应用进程"""
        try:
            # 方案1：让用户输入包名
            package_name = simpledialog.askstring(
                "终止进程",
                "请输入要终止的包名：",
                initialvalue="com.tencent.letsgo"  # 提供默认值
            )
            if not package_name:
                return

            # 使用封装方法执行，确保指定设备
            self._execute_adb(f"shell am force-stop {shlex.quote(package_name)}")
            self.log(f"已终止进程: {package_name}")
            messagebox.showinfo("成功", "进程已终止")

        except subprocess.CalledProcessError as e:
            error_msg = e.output.decode("utf-8", errors="ignore").strip()
            if "does not exist" in error_msg:
                messagebox.showerror("错误", "应用未运行或包名错误")
            else:
                messagebox.showerror("错误", f"终止失败: {error_msg}")
        except Exception as e:
            messagebox.showerror("错误", f"未知错误: {str(e)}")

    def push_file(self):
        """上传文件"""
        local_path = filedialog.askopenfilename(title="选择文件")
        if local_path:
            remote_path = simpledialog.askstring("上传文件", "请输入设备存储路径：")
            if remote_path:
                self._execute_adb(f"push {local_path} {remote_path}")
                self.log(f"已上传文件到: {remote_path}")

    def pull_file(self):
        """下载文件"""
        remote_path = simpledialog.askstring("下载文件", "请输入设备文件路径：")
        if remote_path:
            local_path = filedialog.asksaveasfilename(title="保存文件")
            if local_path:
                self._execute_adb(f"pull {remote_path} {local_path}")
                self.log(f"已下载文件到: {local_path}")

    def get_letsgoLOG(self):
        """获取执行路径下的日志文件
        /sdcard/Android/data/com.tencent.letsgo/files/UE4Game/LetsGo/LetsGo/Saved/Logs
        """
        if not self._check_device():
            return
        remote_dir = "/sdcard/Android/data/com.tencent.letsgo/files/UE4Game/LetsGo/LetsGo/Saved/Logs"
        local_dir = filedialog.askdirectory(title="选择保存日志的目录")
        if local_dir:
            try:
                self._execute_adb(f"pull {shlex.quote(remote_dir)} {shlex.quote(local_dir)}")
                messagebox.showinfo("成功", "日志下载完成")
            except Exception as e:
                messagebox.showerror("错误", f"日志下载失败: {e}")

    def get_readygoLOG(self):
        """
        体验日志文件
        /sdcard/Android/data/com.tencent.readygo/files/UE4Game/LetsGo/LetsGo/Saved/Logs
        """
        if not self._check_device():
            return
        remote_dir = "/sdcard/Android/data/com.tencent.readygo/files/UE4Game/LetsGo/LetsGo/Saved/Logs"
        local_dir = filedialog.askdirectory(title="选择保存日志的目录")
        if local_dir:
            try:
                self._execute_adb(f"pull {shlex.quote(remote_dir)} {shlex.quote(local_dir)}")
                messagebox.showinfo("成功", "日志下载完成")
            except Exception as e:
                messagebox.showerror("错误", f"日志下载失败: {e}")

    def get_adbLOG(self):
        """获取ADB日志并保存到文件"""
        if not self._check_device():
            return
        filename = filedialog.asksaveasfilename(
            title="保存ADB日志",
            defaultextension=".txt",
            initialfile='adbLog',
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if filename:
            try:
                command = [self.adb_path, '-s', self.current_device, 'logcat', '-d']
                with open(filename, 'wb') as f:  # 使用二进制模式避免编码问题
                    process = subprocess.Popen(command, stdout=f, stderr=subprocess.PIPE)
                    _, stderr = process.communicate()

                    if process.returncode != 0:
                        raise subprocess.CalledProcessError(
                            process.returncode,
                            command,
                            output=None,
                            stderr=stderr
                        )

                self.log(f"ADB日志已保存至: {filename}")
                messagebox.showinfo("操作成功", "日志已成功保存！")
            except Exception as e:
                error_msg = f"保存日志失败: {str(e)}"
                if stderr:
                    error_msg += f"\n错误详情: {stderr.decode('utf-8', errors='replace')}"
                self.log(error_msg)
                messagebox.showerror("操作失败", error_msg)


    def _check_device(self) -> bool:
        """检查设备是否有效"""
        if not self.current_device:
            messagebox.showerror("错误", "请先选择设备")
            return False
        return True

    def take_screenshot(self):
        """智能生成截图文件名"""
        if not self._check_device():
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"screenshot_{timestamp}.png"

        save_path = filedialog.asksaveasfilename(
            title="保存截图",
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG文件", "*.png")]
        )
        if save_path:
            remote_path = "/sdcard/screenshot.png"
            self._execute_adb(f"shell screencap -p {remote_path}")
            self._execute_adb(f"pull {remote_path} {save_path}")
            self._execute_adb(f"shell rm {remote_path}")
            self.log(f"截图已保存: {save_path}")


    def record_screen(self):
        """录屏"""
        duration = simpledialog.askinteger("录屏", "请输入录屏时长（秒）：", minvalue=1, maxvalue=600)
        if duration:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_name = f"screenshot_{timestamp}.mp4"

            save_path = filedialog.asksaveasfilename(
                title="保存截图",
                initialfile=default_name,
                defaultextension=".mp4",
                filetypes=[("MP4文件", "*.mp4")]
            )
            if save_path:
                remote_path = "/sdcard/record.mp4"
                self._execute_adb(f"shell screenrecord --time-limit {duration} {remote_path}")
                self._execute_adb(f"pull {remote_path} {save_path}")
                self._execute_adb(f"shell rm {remote_path}")
                self.log(f"录屏已保存: {save_path}")

    def start_recording(self):
        """开始录屏"""
        if not self._check_device():
            return

        # 生成唯一文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.remote_video_path = f"/sdcard/recording_{timestamp}.mp4"

        # 启动后台录屏进程
        self.record_process = subprocess.Popen(
            f"{self.adb_path} -s {self.current_device} shell screenrecord {self.remote_video_path}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        self.log("录屏已开始...")

    def stop_recording(self):
        """停止录屏并保存"""
        if not hasattr(self, 'record_process') or not self.record_process:
            self.log("没有正在进行的录屏")
            return
        try:
            # 终止设备端进程
            pid = self._execute_adb("shell pidof screenrecord").strip()
            if not pid:
                raise RuntimeError("未找到录屏进程")
            # 使用 kill 命令发送 SIGINT
            self._execute_adb(f"shell kill -2 {pid}")  # -2 = SIGINT
            # 等待文件写入
            time.sleep(2)
            # 保存文件
            save_path = filedialog.asksaveasfilename(
                title="保存录屏",
                initialfile=f"recording_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp4",
                defaultextension=".mp4",
                filetypes=[("MP4文件", "*.mp4")]
            )
            if save_path:
                self._execute_adb(f"pull {self.remote_video_path} {shlex.quote(save_path)}")
                self._execute_adb(f"shell rm {self.remote_video_path}")
                self.log(f"录屏已保存: {save_path}")
        except subprocess.TimeoutExpired:
            self.log("警告：录屏进程未正常退出")
        finally:
            self.record_process = None


    #TODO 后续增加一些adb功能
    def show_device_info(self):
        """显示设备详细信息"""
        if not self._check_device():
            return
        try:
            info = [
                ("型号", "ro.product.model"),
                ("品牌", "ro.product.brand"),
                ("系统版本", "ro.build.version.release"),
                ("SDK版本", "ro.build.version.sdk"),
                ("设备序列号", "ro.serialno"),
                ("屏幕分辨率", "wm size"),
                ("CPU信息", "cpuinfo"),
            ]

            result = "设备信息：\n"
            for name, cmd in info:
                if cmd.startswith("ro") or cmd.startswith("wm"):
                    output = self._execute_adb(f"shell getprop {cmd}") if "wm" not in cmd else self._execute_adb(
                        f"shell {cmd}")
                else:
                    output = self._execute_adb(f"shell cat /proc/{cmd}")
                result += f"{name}: {output}\n"

            messagebox.showinfo("设备信息", result)
        except Exception as e:
            self.log(f"获取设备信息失败: {str(e)}")

    def wireless_connect(self):
        """无线连接设备"""
        if "usb" not in self.current_device.lower():
            messagebox.showinfo("提示", "请先通过USB连接设备")
            return
        ip = simpledialog.askstring("无线连接", "请输入设备IP地址：")
        port = simpledialog.askinteger("无线连接", "请输入端口号：", initialvalue=5555)

        if ip and port:
            try:
                # 先重置连接方式
                self._execute_adb("tcpip 5555")
                time.sleep(2)  # 等待端口重启

                # 执行连接命令
                connect_cmd = f"connect {ip}:{port}"
                result = subprocess.check_output(f"{self.adb_path} {connect_cmd}",
                                                 shell=True,
                                                 stderr=subprocess.STDOUT).decode()
                self.log(f"无线连接结果：{result.strip()}")
            except subprocess.CalledProcessError as e:
                self.log(f"连接失败：{e.output.decode().strip()}")

    def simulate_tap(self):
        """模拟屏幕点击"""
        if not self._check_device():
            return

        try:
            x = simpledialog.askinteger("输入坐标", "X坐标：")
            y = simpledialog.askinteger("输入坐标", "Y坐标：")
            if x is not None and y is not None:
                self._execute_adb(f"shell input tap {x} {y}")
                self.log(f"已模拟点击坐标 ({x}, {y})")
        except ValueError:
            messagebox.showerror("错误", "请输入有效数字坐标")

    def input_text(self):
        """输入文本到当前焦点"""
        text = simpledialog.askstring("输入文本", "请输入要发送的文本：")
        if text and self._check_device():
            try:
                # 处理特殊字符（空格需要转义）
                escaped_text = text.replace(" ", "%s").replace("'", "")
                self._execute_adb(f'shell input text "{escaped_text}"')
                self.log(f"已输入文本: {text}")
            except Exception as e:
                self.log(f"输入失败: {str(e)}")

    def send_keyevent(self, keycode: str):
        """发送按键事件"""
        if self._check_device():
            try:
                self._execute_adb(f"shell input keyevent {keycode}")
                self.log(f"已发送按键: {keycode}")
            except Exception as e:
                self.log(f"按键发送失败: {str(e)}")

    def list_installed_apps(self):
        """显示已安装应用列表"""
        if not self._check_device():
            return

        try:
            packages = self._execute_adb("shell pm list packages -3").splitlines()
            top = tk.Toplevel(self.root)
            top.title("已安装应用列表（第三方）")

            def center_and_resize(window):
                # 确保窗口尺寸已计算完成
                window.update_idletasks()
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()

                # 设置窗口尺寸（400x200）
                window.geometry("400x300")

                # 计算居中坐标
                x = (screen_width - 400) // 2
                y = (screen_height - 200) // 2
                window.geometry(f"400x300+{x}+{y}")

                # 禁止调整窗口大小
                window.resizable(False, False)

            # 调用函数
            center_and_resize(top)

            search_frame = ttk.Frame(top)
            search_frame.pack(fill=tk.X, padx=10, pady=10)

            search_var = tk.StringVar()
            search_entry = ttk.Entry(search_frame, textvariable=search_var)
            search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

            listbox = tk.Listbox(top)
            scrollbar = ttk.Scrollbar(top, orient="vertical", command=listbox.yview)
            listbox.configure(yscrollcommand=scrollbar.set)
            def update_list(*args):
                filter_text = search_var.get().lower()
                listbox.delete(0, tk.END)
                for pkg in packages:
                    if filter_text in pkg.lower():
                        listbox.insert(tk.END, pkg.replace("package:", ""))

            search_var.trace_add("write", update_list)
            update_list()  # 初始加载

            listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        except Exception as e:
            self.log(f"获取应用列表失败: {str(e)}")

    def set_screen_resolution(self):
        """设置屏幕分辨率"""
        if not self._check_device():
            return

        res = simpledialog.askstring("设置分辨率", "格式：宽x高\n（如：1080x1920，输入reset恢复默认）")
        if res:
            try:
                self._execute_adb(f"shell wm size {res}")
                self.log(f"分辨率已设置为：{res}")
            except Exception as e:
                self.log(f"设置失败：{str(e)}")

    def set_screen_timeout(self, timeout: int):
        """设置屏幕超时时间"""
        if not self._check_device():
            return

        try:
            self._execute_adb(f"shell settings put system screen_off_timeout {timeout}")
            status = "常亮" if timeout == 0 else f"{timeout // 1000}秒"
            self.log(f"屏幕超时已设置为：{status}")
        except Exception as e:
            self.log(f"设置失败：{str(e)}")

    def show_process_info(self):
        """显示应用进程信息"""
        package = simpledialog.askstring("进程信息", "请输入包名：")
        if package and self._check_device():
            try:
                meminfo = self._execute_adb(f"shell dumpsys meminfo {package}")
                top = tk.Toplevel(self.root)
                top.title(f"{package} 内存信息")

                text = scrolledtext.ScrolledText(top, wrap=tk.WORD)
                text.insert(tk.END, meminfo)
                text.pack(fill=tk.BOTH, expand=True)
            except Exception as e:
                self.log(f"获取进程信息失败：{str(e)}")

    def start_logcat(self):
        """开始日志"""
        if self.logcat_process is None:
            self.logcat_process = subprocess.Popen(
                f"{self.adb_path} -s {self.current_device} logcat",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True
            )
            threading.Thread(target=self._read_logcat, daemon=True).start()
            self.log("日志已开始")

    def stop_logcat(self):
        """停止日志"""
        if self.logcat_process:
            self.logcat_process.terminate()
            self.logcat_process = None
            self.log("日志已停止")

    def _read_logcat(self):
        """读取日志输出"""
        while self.logcat_process:
            output = self.logcat_process.stdout.readline()
            if output:
                self.log_text.insert(tk.END, output.decode("utf-8"))
                self.log_text.see(tk.END)
            else:
                break

    def clear_log(self):
        """清空日志"""
        self.log_text.delete(1.0, tk.END)

    def save_log(self):
        """保存日志"""
        filename = f"adb_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = filedialog.asksaveasfilename(
            initialfile=filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")]
        )
        if path:
            with open(path, "w") as f:
                f.write(self.log_text.get(1.0, tk.END))
            self._safe_log(f"日志已保存到: {path}")

    @staticmethod
    def _find_adb() -> str:
        """改进的ADB路径查找"""
        if getattr(sys, 'frozen', False):
            # 打包后路径：临时解压目录
            base_dir = sys._MEIPASS
        else:
            # 开发环境路径
            base_dir = os.path.dirname(__file__)

        # 查找adb资源目录
        adb_dir = os.path.join(base_dir, "adb_resources")
        adb_path = os.path.join(adb_dir, "adb.exe")

        if os.path.exists(adb_path):
            return adb_path

        # 备用查找系统PATH
        sys_path = shutil.which("adb")
        if sys_path:
            return sys_path

        messagebox.showerror("错误", "找不到ADB程序，请检查adb_resources目录")
        sys.exit(1)

# 运行GUI
if __name__ == "__main__":
    root = tk.Tk()
    app = ADBGUI(root)
    root.mainloop()