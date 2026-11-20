import tkinter as tk
from tkinter import messagebox, ttk
import random
import sqlite3
from datetime import date
import calendar
 
# =========================
# データベース初期設定
# =========================
DB_NAME = "study_app.db"
 
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    # 予定表テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            date TEXT NOT NULL
        )
    """)
    # 単語帳テーブル
    cur.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            word TEXT NOT NULL,
            meaning TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()
 
init_db()
 
# =========================
# 季節テーマ・カラー設定
# =========================
TEXT = "#2C3E50"
SUB_TEXT = "#7F8C8D"
 
PINK = "#F7C8D0"
BLUE = "#C9E4F6"
GREEN = "#CDE8D2"
 
SUBJECTS = ["数学", "英語", "国語", "理科", "社会"]
QUIZ_SUBJECTS = ["すべて"] + SUBJECTS
 
SEASON_THEMES = {
    "春 (桜)": {"bg": "#FFF0F5", "accent": "#FFB7C5", "effect": "petal", "color": "#FFC0CB"},
    "夏 (青空)": {"bg": "#F0F8FF", "accent": "#87CEEB", "effect": "sun", "color": "#FFFACD"},
    "秋 (紅葉)": {"bg": "#FDF5E6", "accent": "#DEB887", "effect": "leaf", "color": "#E08159"},
    "冬 (雪)": {"bg": "#F0F4F8", "accent": "#B0C4DE", "effect": "snow", "color": "#FFFFFF"},
    "宇宙 (夜空)": {"bg": "#141E30", "accent": "#243B55", "effect": "star", "color": "#FFFFFF"},
    "パステルミント": {"bg": "#E8F8F5", "accent": "#A3E4D7", "effect": "petal", "color": "#D1F2EB"},
    "サンセット": {"bg": "#FFF5EE", "accent": "#FF7E5F", "effect": "sun", "color": "#FEB47B"},
    "モダン (ダーク)": {"bg": "#232526", "accent": "#414345", "effect": "star", "color": "#888888"}
}
 
 
class StudyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Study Support App")
        self.root.geometry("400x700")
        self.root.resizable(False, False)
 
        self.current_season = "春 (桜)"
        self.current_menu = "ホーム"
 
        # カレンダー用の初期状態（当月・当日）
        today = date.today()
        self.cal_year = today.year
        self.cal_month = today.month
        self.selected_date = str(today)
 
        self.animation_id = None
        self.effect_particles = []
        self.current_quiz = None
        self.quiz_subject = "すべて"
 
        # タイマー用の変数（初期値10分 = 600秒）
        self.timer_seconds = 600
        self.selected_timer_minutes = 10
        self.timer_running = False
        self.timer_job = None
 
        self.tasks = [
            {"title": "英単語帳を見る", "time": 10, "color": PINK, "done": False},
            {"title": "数学を10問解く", "time": 10, "color": BLUE, "done": False},
            {"title": "参考書を読む", "time": 10, "color": GREEN, "done": False}
        ]
 
        self.show_main_layout()
 
    def clear_screen(self):
        if self.animation_id:
            try:
                self.root.after_cancel(self.animation_id)
            except:
                pass
            self.animation_id = None
        if self.timer_job:
            try:
                self.root.after_cancel(self.timer_job)
            except:
                pass
            self.timer_job = None
        self.timer_running = False
 
        for widget in self.root.winfo_children():
            widget.destroy()
 
    def show_main_layout(self):
        self.clear_screen()
        theme = SEASON_THEMES[self.current_season]
        is_dark = "ダーク" in self.current_season or "宇宙" in self.current_season
        bg_color = theme["bg"]
        fg_color = "#FFFFFF" if is_dark else TEXT
 
        # Canvasで背景とアニメーションを描画
        self.canvas = tk.Canvas(self.root, width=400, height=700, bg=bg_color, highlightthickness=0)
        self.canvas.place(x=0, y=0)
        self.setup_effects(theme["effect"], theme["color"])
 
        # メニュー切り替えボタン
        menu_frame = tk.Frame(self.root, bg=bg_color)
        menu_frame.place(x=15, y=15, width=370, height=40)
 
        menus = ["ホーム", "予定表", "タイマー", "単語帳", "クイズ"]
        for m in menus:
            btn_bg = theme["accent"] if self.current_menu == m else ("#333333" if is_dark else "#FFFFFF")
            btn_fg = fg_color if self.current_menu == m else (SUB_TEXT if not is_dark else "#AAAAAA")
            b = tk.Button(
                menu_frame, text=m, font=("Arial", 8, "bold"),
                bg=btn_bg, fg=btn_fg, relief="flat",
                command=lambda menu_name=m: self.switch_menu(menu_name)
            )
            b.pack(side="left", expand=True, fill="both", padx=1)
 
        # テーマ選択バー
        setting_frame = tk.Frame(self.root, bg=bg_color)
        setting_frame.place(x=15, y=65, width=370, height=30)
 
        tk.Label(setting_frame, text="テーマ:", bg=bg_color, fg=fg_color, font=("Arial", 9)).pack(side="left")
       
        self.season_var = tk.StringVar(value=self.current_season)
        season_cb = ttk.Combobox(setting_frame, textvariable=self.season_var, values=list(SEASON_THEMES.keys()), width=14, state="readonly")
        season_cb.pack(side="left", padx=5)
        season_cb.bind("<<ComboboxSelected>>", self.on_theme_changed)
 
        # コンテンツ表示エリア
        self.content_frame = tk.Frame(self.root, bg=bg_color)
        self.content_frame.place(x=15, y=105, width=370, height=575)
 
        self.render_content()
 
    def switch_menu(self, menu_name):
        self.current_menu = menu_name
        if menu_name != "クイズ":
            self.current_quiz = None
        self.show_main_layout()
 
    def on_theme_changed(self, event):
        self.current_season = self.season_var.get()
        self.show_main_layout()
 
    def render_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
 
        is_dark = "ダーク" in self.current_season or "宇宙" in self.current_season
        fg_color = "#FFFFFF" if is_dark else TEXT
        sub_fg = "#CCCCCC" if is_dark else SUB_TEXT
        bg_col = SEASON_THEMES[self.current_season]["bg"]
 
        # --- ホーム画面 ---
        if self.current_menu == "ホーム":
            tk.Label(self.content_frame, text="✨ 今日の学習状況", font=("Arial", 16, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=10)
           
            completed_count = sum(1 for t in self.tasks if t["done"])
            card = tk.Frame(self.content_frame, bg="#FFFFFF" if not is_dark else "#2C2C2C", padx=15, pady=15)
            card.pack(fill="x", pady=5)
            tk.Label(card, text=f"完了タスク: {completed_count} / {len(self.tasks)}", font=("Arial", 12, "bold"), fg=TEXT, bg=card["bg"]).pack(anchor="w")
 
            tk.Label(self.content_frame, text="📌 今日やること一覧", font=("Arial", 14, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=(20, 10))
            for task in self.tasks:
                t_card = tk.Frame(self.content_frame, bg=task["color"], padx=10, pady=10)
                t_card.pack(fill="x", pady=4)
                status = "✓ 完了" if task["done"] else "□ 未完了"
                tk.Label(t_card, text=f"{status} | {task['title']} ({task['time']}分)", font=("Arial", 11, "bold"), fg=TEXT, bg=task["color"]).pack(anchor="w")
 
        # --- 予定表画面（カレンダー形式） ---
        elif self.current_menu == "予定表":
            tk.Label(self.content_frame, text="📅 カレンダー & 予定", font=("Arial", 14, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=2)
           
            cal_nav_frame = tk.Frame(self.content_frame, bg=bg_col)
            cal_nav_frame.pack(fill="x", pady=2)
 
            tk.Button(cal_nav_frame, text="◀ 前月", font=("Arial", 8), command=self.prev_month).pack(side="left")
            tk.Label(cal_nav_frame, text=f"{self.cal_year}年 {self.cal_month}月", font=("Arial", 10, "bold"), fg=fg_color, bg=bg_col).pack(side="left", expand=True)
            tk.Button(cal_nav_frame, text="次月 ▶", font=("Arial", 8), command=self.next_month).pack(side="right")
 
            cal_grid_frame = tk.Frame(self.content_frame, bg="#DDDDDD" if not is_dark else "#444444", padx=1, pady=1)
            cal_grid_frame.pack(fill="x", pady=2)
 
            weekdays_jp = ["日", "月", "火", "水", "木", "金", "土"]
            for col_idx, day_name in enumerate(weekdays_jp):
                lbl = tk.Label(cal_grid_frame, text=day_name, font=("Arial", 8, "bold"), width=4, bg="#EEEEEE" if not is_dark else "#333333", fg=TEXT if not is_dark else "#FFFFFF")
                lbl.grid(row=0, column=col_idx, sticky="nsew", padx=1, pady=1)
                cal_grid_frame.grid_columnconfigure(col_idx, weight=1)
 
            all_schedules = self.get_schedules_db()
            scheduled_dates = {s[2] for s in all_schedules}
 
            calendar.setfirstweekday(calendar.SUNDAY)
            month_matrix = calendar.monthcalendar(self.cal_year, self.cal_month)
 
            for row_idx, week in enumerate(month_matrix, start=1):
                for col_idx, day in enumerate(week):
                    if day == 0:
                        lbl = tk.Label(cal_grid_frame, text="", width=4, height=1, bg=bg_col)
                        lbl.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
                    else:
                        date_str = f"{self.cal_year}-{self.cal_month:02d}-{day:02d}"
                        is_selected = (date_str == self.selected_date)
                        has_schedule = (date_str in scheduled_dates)
 
                        if is_selected:
                            btn_bg = SEASON_THEMES[self.current_season]["accent"]
                            btn_fg = TEXT
                        elif has_schedule:
                            btn_bg = GREEN if not is_dark else "#2E5A44"
                            btn_fg = TEXT if not is_dark else "#FFFFFF"
                        else:
                            btn_bg = "#FFFFFF" if not is_dark else "#2C2C2C"
                            btn_fg = TEXT if not is_dark else "#FFFFFF"
 
                        b = tk.Button(
                            cal_grid_frame, text=str(day), font=("Arial", 8, "bold" if is_selected else "normal"),
                            bg=btn_bg, fg=btn_fg, relief="flat", width=4, height=1,
                            command=lambda d=date_str: self.select_date(d)
                        )
                        b.grid(row=row_idx, column=col_idx, sticky="nsew", padx=1, pady=1)
 
            selected_frame = tk.Frame(self.content_frame, bg=bg_col)
            selected_frame.pack(fill="both", expand=True, pady=2)
 
            tk.Label(selected_frame, text=f"📌 {self.selected_date} の予定", font=("Arial", 9, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w")
 
            input_row = tk.Frame(selected_frame, bg=bg_col)
            input_row.pack(fill="x", pady=2)
            self.sch_title_entry = tk.Entry(input_row, font=("Arial", 9), width=22)
            self.sch_title_entry.pack(side="left", padx=(0, 5))
            tk.Button(input_row, text="追加", font=("Arial", 8, "bold"), bg=SEASON_THEMES[self.current_season]["accent"], fg=TEXT, command=self.add_schedule_action).pack(side="left")
 
            day_schedules = [s for s in all_schedules if s[2] == self.selected_date]
            list_container = tk.Frame(selected_frame, bg=bg_col)
            list_container.pack(fill="both", expand=True, pady=2)
 
            if not day_schedules:
                tk.Label(list_container, text="予定はありません", font=("Arial", 8), fg=sub_fg, bg=bg_col).pack(anchor="w", pady=2)
            else:
                for s_id, title, s_date in day_schedules:
                    s_card = tk.Frame(list_container, bg="#FFFFFF" if not is_dark else "#333333", padx=6, pady=2)
                    s_card.pack(fill="x", pady=1)
                    tk.Label(s_card, text=title, font=("Arial", 8), fg=TEXT if not is_dark else "#FFFFFF", bg=s_card["bg"]).pack(side="left")
                    tk.Button(s_card, text="削除", font=("Arial", 7), bg="#FFB7C5", fg=TEXT, command=lambda id=s_id: self.delete_schedule_action(id)).pack(side="right")
 
        # --- タイマー画面 ---
        elif self.current_menu == "タイマー":
            tk.Label(self.content_frame, text="⏱️ 集中タイマー", font=("Arial", 16, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=10)
           
            # 時間自由入力エリア
            input_time_frame = tk.Frame(self.content_frame, bg=bg_col)
            input_time_frame.pack(pady=10)
            tk.Label(input_time_frame, text="設定時間 (分):", font=("Arial", 10, "bold"), fg=fg_color, bg=bg_col).pack(side="left", padx=5)
            
            self.timer_entry = tk.Entry(input_time_frame, font=("Arial", 11), width=6)
            self.timer_entry.insert(0, str(self.selected_timer_minutes))
            self.timer_entry.pack(side="left", padx=5)
            
            tk.Button(
                input_time_frame, text="変更", font=("Arial", 9, "bold"),
                bg=SEASON_THEMES[self.current_season]["accent"], fg=TEXT, relief="flat",
                command=self.apply_custom_timer
            ).pack(side="left", padx=5)
 
            # 残り時間を 「MM:SS」形式に変換
            mins = self.timer_seconds // 60
            secs = self.timer_seconds % 60
            time_str = f"{mins:02d}:{secs:02d}"
 
            self.timer_label = tk.Label(self.content_frame, text=time_str, font=("Arial", 45, "bold"), fg=fg_color, bg=bg_col)
            self.timer_label.pack(pady=20)
 
            btn_text = "STOP" if self.timer_running else "START"
            self.timer_btn = tk.Button(
                self.content_frame, text=btn_text, font=("Arial", 12, "bold"),
                bg=SEASON_THEMES[self.current_season]["accent"], fg=TEXT, relief="flat",
                command=self.toggle_timer
            )
            self.timer_btn.pack(ipadx=20, ipady=10, pady=5)
 
        # --- 単語帳画面 ---
        elif self.current_menu == "単語帳":
            tk.Label(self.content_frame, text="📚 教科別 単語帳", font=("Arial", 16, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=5)
           
            w_form = tk.Frame(self.content_frame, bg=bg_col)
            w_form.pack(fill="x", pady=5)
 
            tk.Label(w_form, text="教科:", font=("Arial", 9), fg=fg_color, bg=bg_col).pack(anchor="w")
            self.w_sub_cb = ttk.Combobox(w_form, values=SUBJECTS, width=15, state="readonly")
            self.w_sub_cb.set(SUBJECTS[0])
            self.w_sub_cb.pack(anchor="w", pady=2)
 
            tk.Label(w_form, text="単語 / キーワード:", font=("Arial", 9), fg=fg_color, bg=bg_col).pack(anchor="w")
            self.word_entry = tk.Entry(w_form, font=("Arial", 10), width=25)
            self.word_entry.pack(anchor="w", pady=2)
 
            tk.Label(w_form, text="意味 / 解説:", font=("Arial", 9), fg=fg_color, bg=bg_col).pack(anchor="w")
            self.meaning_entry = tk.Entry(w_form, font=("Arial", 10), width=25)
            self.meaning_entry.pack(anchor="w", pady=2)
 
            tk.Button(w_form, text="単語を登録", font=("Arial", 9, "bold"), bg=SEASON_THEMES[self.current_season]["accent"], fg=TEXT, command=self.add_word_action).pack(anchor="w", pady=5)
 
            tk.Label(self.content_frame, text="📖 登録済み単語", font=("Arial", 12, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=(5, 5))
           
            words = self.get_words_db()
            for w_id, sub, word, meaning in words:
                w_card = tk.Frame(self.content_frame, bg="#FFFFFF" if not is_dark else "#333333", padx=8, pady=6)
                w_card.pack(fill="x", pady=2)
                tk.Label(w_card, text=f"[{sub}] {word} : {meaning}", font=("Arial", 10), fg=TEXT if not is_dark else "#FFFFFF", bg=w_card["bg"]).pack(side="left")
                tk.Button(w_card, text="削除", font=("Arial", 8), bg="#FFB7C5", fg=TEXT, command=lambda id=w_id: self.delete_word_action(id)).pack(side="right")
 
        # --- クイズ画面 ---
        elif self.current_menu == "クイズ":
            tk.Label(self.content_frame, text="🧠 単語四択クイズ", font=("Arial", 15, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=2)
            
            sub_select_frame = tk.Frame(self.content_frame, bg=bg_col)
            sub_select_frame.pack(fill="x", pady=5)
            tk.Label(sub_select_frame, text="出題科目:", font=("Arial", 9, "bold"), fg=fg_color, bg=bg_col).pack(side="left", padx=(0, 5))
            
            self.quiz_sub_cb = ttk.Combobox(sub_select_frame, values=QUIZ_SUBJECTS, width=12, state="readonly")
            self.quiz_sub_cb.set(self.quiz_subject)
            self.quiz_sub_cb.pack(side="left", padx=5)
            self.quiz_sub_cb.bind("<<ComboboxSelected>>", self.on_quiz_subject_changed)
 
            all_words = self.get_words_db()
            if self.quiz_subject == "すべて":
                filtered_words = all_words
            else:
                filtered_words = [w for w in all_words if w[1] == self.quiz_subject]
 
            if len(filtered_words) < 4:
                tk.Label(self.content_frame, text=f"⚠️ 「{self.quiz_subject}」の登録単語が\n4件未満です。\n別の科目を選ぶか、単語を追加してください。", font=("Arial", 10), fg=fg_color, bg=bg_col, justify="center").pack(pady=40)
            else:
                if not self.current_quiz:
                    self.load_new_quiz(filtered_words, all_words)
                
                q = self.current_quiz
                tk.Label(self.content_frame, text=f"【 出題教科: {q['subject']} 】", font=("Arial", 10, "bold"), fg=sub_fg, bg=bg_col).pack(pady=2)
                
                q_card = tk.Frame(self.content_frame, bg="#FFFFFF" if not is_dark else "#2C2C2C", padx=10, pady=15)
                q_card.pack(fill="x", pady=5)
                tk.Label(q_card, text=f"次の単語の意味はどれ？\n\n「 {q['word']} 」", font=("Arial", 12, "bold"), fg=TEXT if not is_dark else "#FFFFFF", bg=q_card["bg"], justify="center").pack()
 
                tk.Label(self.content_frame, text="👇 答えを選んでね", font=("Arial", 9, "bold"), fg=fg_color, bg=bg_col).pack(anchor="w", pady=2)
 
                for opt in q["options"]:
                    b = tk.Button(
                        self.content_frame, text=opt, font=("Arial", 9),
                        bg="#FFFFFF" if not is_dark else "#333333", fg=TEXT if not is_dark else "#FFFFFF",
                        relief="flat", width=34, pady=4,
                        command=lambda o=opt: self.check_quiz_answer(o)
                    )
                    b.pack(pady=2)
 
    # =========================
    # タイマー操作用メソッド
    # =========================
    def apply_custom_timer(self):
        if not self.timer_running:
            try:
                mins = int(self.timer_entry.get())
                if mins <= 0:
                    raise ValueError
                self.selected_timer_minutes = mins
                self.timer_seconds = mins * 60
                self.render_content()
            except ValueError:
                messagebox.showerror("エラー", "有効な整数（分）を入力してください。")
 
    def toggle_timer(self):
        if not self.timer_running:
            self.timer_running = True
            if hasattr(self, 'timer_btn'):
                self.timer_btn.config(text="STOP")
            self.run_timer()
        else:
            self.timer_running = False
            if self.timer_job:
                self.root.after_cancel(self.timer_job)
                self.timer_job = None
            if hasattr(self, 'timer_btn'):
                self.timer_btn.config(text="START")
 
    def run_timer(self):
        if self.timer_running:
            if self.timer_seconds > 0:
                self.timer_seconds -= 1
                mins = self.timer_seconds // 60
                secs = self.timer_seconds % 60
                if hasattr(self, 'timer_label'):
                    self.timer_label.config(text=f"{mins:02d}:{secs:02d}")
                self.timer_job = self.root.after(1000, self.run_timer)
            else:
                self.timer_running = False
                messagebox.showinfo("おつかれさま！", f"{self.selected_timer_minutes}分間よく頑張りました！🌷")
                if self.tasks:
                    self.tasks[0]["done"] = True
                self.timer_seconds = self.selected_timer_minutes * 60
                self.switch_menu("ホーム")
 
    # =========================
    # クイズ用のメソッド
    # =========================
    def on_quiz_subject_changed(self, event):
        self.quiz_subject = self.quiz_sub_cb.get()
        self.current_quiz = None
        self.render_content()
 
    def load_new_quiz(self, target_words, all_words):
        correct = random.choice(target_words)
        wrong_pool = [w[3] for w in all_words if w[3] != correct[3]]
        wrong_choices = random.sample(wrong_pool, min(3, len(wrong_pool)))
        options = wrong_choices + [correct[3]]
        random.shuffle(options)
        self.current_quiz = {
            "subject": correct[1],
            "word": correct[2],
            "correct_meaning": correct[3],
            "options": options
        }
 
    def check_quiz_answer(self, selected):
        if selected == self.current_quiz["correct_meaning"]:
            messagebox.showinfo("正解！", "すばらしい！正解です🎉")
        else:
            messagebox.showerror("残念...", f"不正解です...\n正解は「{self.current_quiz['correct_meaning']}」でした。")
        self.current_quiz = None
        self.render_content()
 
    # =========================
    # カレンダー操作メソッド
    # =========================
    def prev_month(self):
        if self.cal_month == 1:
            self.cal_month = 12
            self.cal_year -= 1
        else:
            self.cal_month -= 1
        self.render_content()
 
    def next_month(self):
        if self.cal_month == 12:
            self.cal_month = 1
            self.cal_year += 1
        else:
            self.cal_month += 1
        self.render_content()
 
    def select_date(self, date_str):
        self.selected_date = date_str
        self.render_content()
 
    # =========================
    # データベース操作メソッド
    # =========================
    def add_schedule_action(self):
        title = self.sch_title_entry.get()
        if title:
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO schedules (title, date) VALUES (?, ?)", (title, self.selected_date))
            conn.commit()
            conn.close()
            self.render_content()
        else:
            messagebox.showerror("エラー", "予定タイトルを入力してください。")
 
    def get_schedules_db(self):
        conn = sqlite3.connect(DB_NAME)
        rows = conn.execute("SELECT id, title, date FROM schedules ORDER BY date").fetchall()
        conn.close()
        return rows
 
    def delete_schedule_action(self, s_id):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM schedules WHERE id = ?", (s_id,))
        conn.commit()
        conn.close()
        self.render_content()
 
    def add_word_action(self):
        sub = self.w_sub_cb.get()
        word = self.word_entry.get()
        meaning = self.meaning_entry.get()
        if word and meaning:
            conn = sqlite3.connect(DB_NAME)
            conn.execute("INSERT INTO words (subject, word, meaning) VALUES (?, ?, ?)", (sub, word, meaning))
            conn.commit()
            conn.close()
            messagebox.showinfo("成功", "単語を登録しました！")
            self.switch_menu("単語帳")
        else:
            messagebox.showerror("エラー", "単語と意味を入力してください。")
 
    def get_words_db(self):
        conn = sqlite3.connect(DB_NAME)
        rows = conn.execute("SELECT id, subject, word, meaning FROM words ORDER BY id DESC").fetchall()
        conn.close()
        return rows
 
    def delete_word_action(self, w_id):
        conn = sqlite3.connect(DB_NAME)
        conn.execute("DELETE FROM words WHERE id = ?", (w_id,))
        conn.commit()
        conn.close()
        self.switch_menu("単語帳")
 
    def finish_task_from_timer(self):
        messagebox.showinfo("おつかれさま！", "10分間よく頑張りました！🌷")
        if self.tasks:
            self.tasks[0]["done"] = True
        self.switch_menu("ホーム")
 
    def setup_effects(self, effect_type, particle_color):
        self.effect_particles = []
        for _ in range(15):
            x = random.randint(0, 400)
            y = random.randint(0, 700)
            size = random.randint(6, 12)
           
            if effect_type in ["snow", "petal", "leaf"]:
                item = self.canvas.create_oval(x, y, x + size, y + size, fill=particle_color, outline="")
                self.effect_particles.append({"item": item, "speed": random.randint(1, 3), "dx": random.choice([-1, 1])})
            else:
                item = self.canvas.create_oval(x, y, x + 3, y + 3, fill=particle_color, outline="")
                self.effect_particles.append({"item": item, "speed": 0, "dx": 0})
 
        self.animate_effects()
 
    def animate_effects(self):
        for p in self.effect_particles:
            self.canvas.move(p["item"], p["dx"], p["speed"])
            pos = self.canvas.coords(p["item"])
            if pos and pos[1] > 700:
                self.canvas.coords(p["item"], random.randint(0, 400), -10, random.randint(0, 400)+10, 0)
       
        self.animation_id = self.root.after(50, self.animate_effects)
 
 
if __name__ == "__main__":
    root = tk.Tk()
    app = StudyApp(root)
    root.mainloop()
    
 