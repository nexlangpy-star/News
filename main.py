import flet as ft
import asyncio
import subprocess
import sys
import os
import signal
import psutil
from pathlib import Path
import threading
import time

class BotManager:
    def __init__(self):
        self.bot_process = None
        self.bot_file_path = None
        self.is_running = False
        self.monitor_thread = None
        self.stop_monitoring = False
        self.proxies = [
            {
                "server": "oneproxys.best",
                "port": 443,
                "secret": "eed68360458af63073bac1394e8c7a48da6f6e6570726f7879732e62657374"
            },
            {
                "server": "207.180.203.24",
                "port": 443,
                "secret": "7uBwJkgHh8uyF8nq_Te86VtzMy5hbWF6b25hd3MuY29t"
            }
        ]
        self.current_proxy_index = 0

    def get_proxy_string(self):
        proxy = self.proxies[self.current_proxy_index]
        return f"http://{proxy['server']}:{proxy['port']}"

    def get_mtproto_proxy_string(self):
        proxy = self.proxies[self.current_proxy_index]
        return f"tg://proxy?server={proxy['server']}&port={proxy['port']}&secret={proxy['secret']}"

    def switch_proxy(self):
        self.current_proxy_index = (self.current_proxy_index + 1) % len(self.proxies)

    def run_bot(self, file_path):
        if not file_path or not os.path.exists(file_path):
            return False, "ملف البوت غير موجود"

        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            proxy = self.proxies[self.current_proxy_index]
            env["HTTP_PROXY"] = self.get_proxy_string()
            env["HTTPS_PROXY"] = self.get_proxy_string()
            env["MT_PROXY"] = self.get_mtproto_proxy_string()
            tg_proxy = self.get_mtproto_proxy_string()
            env["TG_PROXY"] = tg_proxy
            env["TELETHON_PROXY"] = tg_proxy
            
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            preexec_fn = os.setsid if sys.platform != "win32" else None

            self.bot_process = subprocess.Popen(
                [sys.executable, file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=creationflags,
                preexec_fn=preexec_fn,
                cwd=os.path.dirname(file_path)
            )
            
            self.bot_file_path = file_path
            self.is_running = True
            self.stop_monitoring = False
            
            self.monitor_thread = threading.Thread(target=self._monitor_bot, daemon=True)
            self.monitor_thread.start()
            
            return True, "تم تشغيل البوت بنجاح"
        except Exception as e:
            return False, f"خطأ في تشغيل البوت: {str(e)}"

    def _monitor_bot(self):
        while not self.stop_monitoring and self.is_running:
            if self.bot_process and self.bot_process.poll() is not None:
                self._handle_bot_crash()
            time.sleep(3)

    def _handle_bot_crash(self):
        if self.stop_monitoring or not self.is_running:
            return
        
        self.switch_proxy()
        
        try:
            env = os.environ.copy()
            env["PYTHONUNBUFFERED"] = "1"
            
            proxy = self.proxies[self.current_proxy_index]
            env["HTTP_PROXY"] = self.get_proxy_string()
            env["HTTPS_PROXY"] = self.get_proxy_string()
            env["MT_PROXY"] = self.get_mtproto_proxy_string()
            tg_proxy = self.get_mtproto_proxy_string()
            env["TG_PROXY"] = tg_proxy
            env["TELETHON_PROXY"] = tg_proxy

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            preexec_fn = os.setsid if sys.platform != "win32" else None

            self.bot_process = subprocess.Popen(
                [sys.executable, self.bot_file_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                creationflags=creationflags,
                preexec_fn=preexec_fn,
                cwd=os.path.dirname(self.bot_file_path)
            )
        except Exception:
            pass

    def stop_bot(self):
        self.stop_monitoring = True
        self.is_running = False
        
        if self.bot_process:
            try:
                if sys.platform == "win32":
                    subprocess.run(['taskkill', '/F', '/T', '/PID', str(self.bot_process.pid)], capture_output=True)
                else:
                    os.killpg(os.getpgid(self.bot_process.pid), signal.SIGTERM)
                    try:
                        self.bot_process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        os.killpg(os.getpgid(self.bot_process.pid), signal.SIGKILL)
            except:
                pass
            self.bot_process = None

    def disable_battery_optimization(self):
        if sys.platform == "win32":
            try:
                subprocess.run(['powercfg', '/change', 'standby-timeout-ac', '0'], capture_output=True)
                subprocess.run(['powercfg', '/change', 'standby-timeout-dc', '0'], capture_output=True)
                subprocess.run(['powercfg', '/change', 'monitor-timeout-ac', '0'], capture_output=True)
                subprocess.run(['powercfg', '/change', 'monitor-timeout-dc', '0'], capture_output=True)
                subprocess.run(['powercfg', '/change', 'disk-timeout-ac', '0'], capture_output=True)
                subprocess.run(['powercfg', '/change', 'disk-timeout-dc', '0'], capture_output=True)
                return True, "تم تعطيل إعدادات توفير الطاقة"
            except:
                return False, "تعذر تعطيل إعدادات الطاقة"
        elif sys.platform == "darwin":
            try:
                subprocess.run(['caffeinate', '-d', '-i', '-m', '-s', '-u', '-t', '3600'], capture_output=True)
                return True, "تم منع السكون مؤقتاً"
            except:
                return False, "تعذر منع السكون"
        else:
            return True, "نظام Linux - لا حاجة لتعديلات إضافية"

def main(page: ft.Page):
    page.title = "مدير تشغيل البوتات الاحترافي"
    page.theme_mode = ft.ThemeMode.DARK
    page.window.width = 600
    page.window.height = 700
    page.window.resizable = False
    page.padding = 30
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.bgcolor = ft.Colors.BLACK87
    
    bot_manager = BotManager()
    
    file_path = ft.Ref[ft.Text]()
    status_text = ft.Ref[ft.Text]()
    status_color = ft.Ref[ft.Colors]()
    progress_bar = ft.Ref[ft.ProgressBar]()
    start_button = ft.Ref[ft.ElevatedButton]()
    stop_button = ft.Ref[ft.ElevatedButton]()
    upload_button = ft.Ref[ft.ElevatedButton]()
    
    selected_file = None
    
    def update_status(message, is_error=False):
        status_text.current.value = message
        status_color.current.color = ft.Colors.RED if is_error else ft.Colors.GREEN_400
        page.update()
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        nonlocal selected_file
        if e.files:
            selected_file = e.files[0].path
            file_path.current.value = f"📁 {os.path.basename(selected_file)}"
            upload_button.current.disabled = False
            update_status("✅ تم اختيار الملف بنجاح")
            page.update()
    
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)
    
    def upload_file(e):
        nonlocal selected_file
        if selected_file:
            if not selected_file.endswith('.py'):
                update_status("❌ يجب اختيار ملف بايثون (.py)", True)
                return
            
            bot_manager.bot_file_path = selected_file
            start_button.current.disabled = False
            upload_button.current.disabled = True
            update_status("📦 تم تجهيز البوت للتشغيل")
            page.update()
    
    def start_bot(e):
        if not bot_manager.bot_file_path:
            update_status("❌ الرجاء رفع ملف البوت أولاً", True)
            return
        
        progress_bar.current.visible = True
        start_button.current.disabled = True
        stop_button.current.disabled = False
        page.update()
        
        bot_manager.disable_battery_optimization()
        
        def run():
            success, message = bot_manager.run_bot(bot_manager.bot_file_path)
            progress_bar.current.visible = False
            if success:
                update_status("🚀 البوت يعمل الآن في الخلفية بشكل دائم")
                start_button.current.disabled = True
                stop_button.current.disabled = False
                start_button.current.bgcolor = ft.Colors.GREEN_700
            else:
                update_status(message, True)
                start_button.current.disabled = False
                stop_button.current.disabled = True
            page.update()
        
        threading.Thread(target=run, daemon=True).start()
    
    def stop_bot(e):
        progress_bar.current.visible = True
        page.update()
        
        def run_stop():
            bot_manager.stop_bot()
            progress_bar.current.visible = False
            start_button.current.disabled = False
            stop_button.current.disabled = True
            start_button.current.bgcolor = ft.Colors.BLUE_700
            update_status("⏹️ تم إيقاف البوت")
            page.update()
        
        threading.Thread(target=run_stop, daemon=True).start()
    
    header = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.ROBOT, size=60, color=ft.Colors.BLUE_400),
            ft.Text("مدير تشغيل البوتات", size=32, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
            ft.Text("قم برفع ملف البوت وتشغيله في الخلفية بشكل دائم", size=14, color=ft.Colors.GREY_400),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        margin=ft.margin.only(bottom=30)
    )
    
    file_section = ft.Container(
        content=ft.Column([
            ft.Text("اختر ملف البوت", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
            ft.Container(height=10),
            ft.Row([
                ft.ElevatedButton(
                    "اختر ملف Python",
                    icon=ft.icons.UPLOAD_FILE,
                    on_click=lambda _: file_picker.pick_files(allowed_extensions=["py"]),
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_700,
                        padding=20,
                    ),
                    expand=True
                ),
            ]),
            ft.Container(height=10),
            ft.Text(ref=file_path, value="لم يتم اختيار أي ملف", size=14, color=ft.Colors.GREY_400),
            ft.Container(height=10),
            ft.ElevatedButton(
                "تأكيد رفع البوت",
                ref=upload_button,
                icon=ft.icons.CHECK_CIRCLE,
                on_click=upload_file,
                disabled=True,
                style=ft.ButtonStyle(
                    color=ft.Colors.WHITE,
                    bgcolor=ft.Colors.GREEN_700,
                    padding=20,
                ),
                expand=True
            ),
        ]),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.GREY_900,
        border=ft.border.all(1, ft.Colors.GREY_700),
        margin=ft.margin.only(bottom=20)
    )
    
    proxy_info = ft.Container(
        content=ft.Column([
            ft.Text("معلومات البروكسي", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
            ft.Container(height=10),
            ft.Text("البروكسي الأساسي: oneproxys.best:443", size=13, color=ft.Colors.GREY_400),
            ft.Text("البروكسي الاحتياطي: 207.180.203.24:443", size=13, color=ft.Colors.GREY_400),
            ft.Text("يتم التبديل تلقائياً عند توقف البوت", size=12, color=ft.Colors.ORANGE_300),
        ]),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.GREY_900,
        border=ft.border.all(1, ft.Colors.GREY_700),
        margin=ft.margin.only(bottom=20)
    )
    
    control_section = ft.Container(
        content=ft.Column([
            ft.Text("لوحة التحكم", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
            ft.Container(height=15),
            ft.Row([
                ft.ElevatedButton(
                    "تشغيل البوت",
                    ref=start_button,
                    icon=ft.icons.PLAY_ARROW,
                    on_click=start_bot,
                    disabled=True,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.BLUE_700,
                        padding=20,
                    ),
                    expand=True
                ),
                ft.ElevatedButton(
                    "إيقاف البوت",
                    ref=stop_button,
                    icon=ft.icons.STOP,
                    on_click=stop_bot,
                    disabled=True,
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        bgcolor=ft.Colors.RED_700,
                        padding=20,
                    ),
                    expand=True
                ),
            ]),
            ft.Container(height=15),
            ft.ProgressBar(ref=progress_bar, visible=False, height=8, color=ft.Colors.BLUE_400),
        ]),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.GREY_900,
        border=ft.border.all(1, ft.Colors.GREY_700),
        margin=ft.margin.only(bottom=20)
    )
    
    status_section = ft.Container(
        content=ft.Column([
            ft.Text("حالة النظام", size=16, weight=ft.FontWeight.W_500, color=ft.Colors.BLUE_200),
            ft.Container(height=10),
            ft.Row([
                ft.Icon(ft.icons.CIRCLE, size=16, ref=status_color, color=ft.Colors.GREY_400),
                ft.Text(ref=status_text, value="في انتظار رفع البوت", size=14, color=ft.Colors.GREY_400),
            ]),
        ]),
        padding=20,
        border_radius=15,
        bgcolor=ft.Colors.GREY_900,
        border=ft.border.all(1, ft.Colors.GREY_700),
    )
    
    page.add(
        header,
        file_section,
        proxy_info,
        control_section,
        status_section
    )
    
    page.update()

ft.app(target=main)
