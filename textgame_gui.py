"""불시착: 원시 행성의 생존자 - Tkinter GUI 버전

같은 폴더의 textgame.py(게임 로직)를 불러와서 사용합니다.
게임 로직이 print()로 내보내는 메시지는 화면 아래 로그 창으로 보냅니다.
"""
import contextlib
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

import textgame as tg

FONT = ("Malgun Gothic", 10)
FONT_BOLD = ("Malgun Gothic", 10, "bold")
FONT_TITLE = ("Malgun Gothic", 12, "bold")
FONT_BANNER = ("Malgun Gothic", 15, "bold")

# 서바이벌 팔레트: 어두운 이끼/흙색 + 호박색 포인트
BG = "#1b1f17"          # 배경 (검은 이끼)
PANEL = "#262c1f"       # 탭/패널
LOG_BG = "#10130d"      # 기록 창
FG = "#d9d2b6"          # 기본 글자 (양피지)
MUTED = "#8a8668"       # 보조 글자
AMBER = "#d4a63c"       # 강조
OLIVE = "#4a5a2e"       # 기본 버튼
OLIVE_HOVER = "#62763a"
OLIVE_PRESS = "#364320"
DIS_BG = "#2a2e23"
DIS_FG = "#66664f"
RUST = "#a65a1f"        # 우주선 수리 버튼
BLOOD = "#7a2f22"       # 종료 버튼
NIGHT = "#35476a"       # 휴식 버튼
GOOD = "#7fb069"
WARN = "#e0a43a"
DANGER = "#c9503a"


def _button_style(style, name, bg, hover, press, fg=FG):
    style.configure(name, background=bg, foreground=fg, bordercolor="#0e100a",
                    lightcolor=bg, darkcolor=bg, focuscolor=bg,
                    padding=(12, 7), relief="flat", font=FONT)
    style.map(name,
              background=[("disabled", DIS_BG), ("pressed", press), ("active", hover)],
              foreground=[("disabled", DIS_FG)],
              bordercolor=[("disabled", "#1a1d15")])


def _bar_style(style, name, color):
    style.configure(name, troughcolor=LOG_BG, background=color, bordercolor="#0e100a",
                    lightcolor=color, darkcolor=color, thickness=16)


def apply_theme(root):
    """서바이벌 분위기의 다크 테마 적용 (clam 테마는 색상 변경이 가능)"""
    root.configure(bg=BG)
    style = ttk.Style(root)
    style.theme_use("clam")

    style.configure(".", background=BG, foreground=FG, font=FONT,
                    fieldbackground=LOG_BG, bordercolor="#0e100a")
    style.configure("TFrame", background=BG)
    style.configure("TLabel", background=BG, foreground=FG)
    style.configure("Title.TLabel", font=FONT_TITLE, foreground=AMBER)
    style.configure("Section.TLabel", font=FONT_BOLD, foreground=AMBER)
    style.configure("Hint.TLabel", foreground=MUTED)
    style.configure("Banner.TLabel", background="#0f120c", foreground=AMBER,
                    font=FONT_BANNER, anchor="center", padding=(0, 10))

    style.configure("TLabelframe", background=BG, bordercolor="#4d5238", relief="solid")
    style.configure("TLabelframe.Label", background=BG, foreground=AMBER, font=FONT_BOLD)

    edge = "#4d5238"
    style.configure("TNotebook", background=BG, bordercolor=edge, lightcolor=edge,
                    darkcolor=edge, tabmargins=(2, 6, 2, 0))
    style.configure("TNotebook.Tab", background="#2a3022", foreground="#a9a58a",
                    padding=(14, 6), font=FONT_BOLD, bordercolor=edge,
                    lightcolor="#2a3022", darkcolor="#2a3022")
    style.map("TNotebook.Tab",
              background=[("selected", OLIVE), ("active", "#3a4526")],
              lightcolor=[("selected", OLIVE), ("active", "#3a4526")],
              darkcolor=[("selected", OLIVE), ("active", "#3a4526")],
              foreground=[("selected", "#f2ecd0"), ("active", FG)])

    _button_style(style, "TButton", OLIVE, OLIVE_HOVER, OLIVE_PRESS)
    _button_style(style, "Ship.TButton", RUST, "#c26d2a", "#85470f")
    _button_style(style, "Rest.TButton", NIGHT, "#46598a", "#27354f")
    _button_style(style, "Danger.TButton", BLOOD, "#97392a", "#5c2118")

    _bar_style(style, "EnergyOk.Horizontal.TProgressbar", GOOD)
    _bar_style(style, "EnergyMid.Horizontal.TProgressbar", WARN)
    _bar_style(style, "EnergyLow.Horizontal.TProgressbar", DANGER)
    _bar_style(style, "Ship.Horizontal.TProgressbar", RUST)

    style.configure("Vertical.TScrollbar", background="#3a4526", troughcolor=LOG_BG,
                    bordercolor="#0e100a", arrowcolor=FG, lightcolor="#3a4526", darkcolor="#3a4526")
    style.map("Vertical.TScrollbar", background=[("active", OLIVE_HOVER)])


def safe(text):
    """Tk에서 문제될 수 있는 BMP 밖 이모지(🪓, 🚀 등)를 제거"""
    cleaned = "".join(ch for ch in text if ord(ch) <= 0xFFFF)
    return " ".join(cleaned.split())


# ==============================
# 로그 창으로 print 출력 보내기
# ==============================
class LogWriter:
    TAGS = {
        "bad": "#e0674f",
        "warn": "#e8b04a",
        "good": "#8fc47a",
        "night": "#a995d8",
    }

    def __init__(self, text_widget):
        self.text = text_widget
        self.buf = ""
        for tag, color in self.TAGS.items():
            self.text.tag_configure(tag, foreground=color)

    def write(self, s):
        self.buf += s
        while "\n" in self.buf:
            line, self.buf = self.buf.split("\n", 1)
            self._emit(line)
        return len(s)

    def flush(self):
        pass

    def _emit(self, line):
        raw = line.strip()
        if not raw or set(raw) <= set("=-"):   # 빈 줄, 구분선 생략
            return
        if raw.startswith("❌"):
            tag = "bad"
        elif raw.startswith("⚠"):
            tag = "warn"
        elif raw.startswith(("🎉", "✨")):
            tag = "good"
        elif raw.startswith("🌙"):
            tag = "night"
        else:
            tag = ""
        msg = safe(raw)
        if not msg:
            return
        self.text.config(state="normal")
        self.text.insert("end", msg + "\n", tag)
        self.text.see("end")
        self.text.config(state="disabled")


# ==============================
# GUI용 행동 함수 (로직은 textgame의 Player/표를 그대로 사용)
# ==============================
def upgrade_tool(player, key):
    tool = player.tools[key]
    nxt = tool.level + 1
    if nxt not in tg.UPGRADES[key]:
        print("이미 최대 레벨입니다.")
        return
    cost = tg.UPGRADES[key][nxt]
    if not player.can_afford(cost):
        print("❌ 재료가 부족합니다.")
        return
    player.pay(cost)
    tool.upgrade()
    print(f"✨ {tool.name}를 Lv.{tool.level}로 강화했습니다! (내구도 {tool.durability})")


def repair_tool(player, key):
    tool = player.tools[key]
    cost = tg.REPAIR_COSTS[key]
    if not tool.broken:
        print("부서지지 않은 도구는 수리할 필요가 없습니다.")
        return
    if not player.can_afford(cost):
        print(f"❌ 재료가 부족합니다. ({tg.format_cost(cost)} 필요)")
        return
    player.pay(cost)
    tool.restore()
    print(f"🔧 {tool.name}를 수리했습니다.")


def repair_ship(player):
    cost, _ = tg.get_ship_cost(player.ship_repair)
    if not player.can_afford(cost):
        print("❌ 재료가 부족합니다.")
        return
    player.pay(cost)
    progress = tg.random.randint(12, 22)
    player.ship_repair = min(100, player.ship_repair + progress)
    print(f"🔧 우주선을 수리했습니다! 진행도 +{progress}% (현재 {player.ship_repair}%)")
    if player.ship_repair >= 100:
        print("✨ 우주선 수리가 완료되었습니다!")


# ==============================
# 메인 앱
# ==============================
class GameApp:
    def __init__(self, root, name):
        self.root = root
        self.player = tg.Player(name)
        self.day = 1
        self.finished = False
        self.buttons = []          # (버튼, 활성 조건 함수)

        root.title("불시착: 원시 행성의 생존자")
        root.geometry("760x700")
        root.minsize(680, 620)
        apply_theme(root)
        root.protocol("WM_DELETE_WINDOW", self.quit_game)

        self._build_banner()
        self._build_status()
        self._build_tabs()
        self._build_bottom()
        self._build_log()

        self.writer = LogWriter(self.log)
        with contextlib.redirect_stdout(self.writer):
            print("타 행성의 새틀라이트 어택으로 우주선이 반파되었습니다.")
            print("나무, 돌, 철, 희귀 광석을 모아 우주선을 수리하고 행성을 탈출하세요.")
            print(f"생존을 시작합니다, {name}님. 목표: 우주선 수리 진행도 100%")
        self.refresh()

    # ---------- UI 구성 ----------
    def _build_banner(self):
        self.banner = ttk.Label(self.root, text="◆  불시착 : 원시 행성의 생존자  ◆",
                                style="Banner.TLabel")
        self.banner.pack(fill="x")

    def _build_status(self):
        frame = ttk.LabelFrame(self.root, text="상태", padding=8)
        frame.pack(fill="x", padx=10, pady=(10, 4))
        frame.columnconfigure(1, weight=1)

        self.lbl_day = ttk.Label(frame, style="Title.TLabel")
        self.lbl_day.grid(row=0, column=0, columnspan=3, sticky="w")

        ttk.Label(frame, text="에너지").grid(row=1, column=0, sticky="w", pady=2)
        self.bar_energy = ttk.Progressbar(frame, maximum=self.player.max_energy,
                                          style="EnergyOk.Horizontal.TProgressbar")
        self.bar_energy.grid(row=1, column=1, sticky="ew", padx=6)
        self.lbl_energy = ttk.Label(frame, width=10)
        self.lbl_energy.grid(row=1, column=2, sticky="e")

        ttk.Label(frame, text="우주선").grid(row=2, column=0, sticky="w", pady=2)
        self.bar_ship = ttk.Progressbar(frame, maximum=100, style="Ship.Horizontal.TProgressbar")
        self.bar_ship.grid(row=2, column=1, sticky="ew", padx=6)
        self.lbl_ship = ttk.Label(frame, width=10)
        self.lbl_ship.grid(row=2, column=2, sticky="e")

        self.lbl_tools = ttk.Label(frame)
        self.lbl_tools.grid(row=3, column=0, columnspan=3, sticky="w", pady=(4, 0))
        self.lbl_inv = ttk.Label(frame)
        self.lbl_inv.grid(row=4, column=0, columnspan=3, sticky="w")
        self.lbl_skill = ttk.Label(frame)
        self.lbl_skill.grid(row=5, column=0, columnspan=3, sticky="w")

    def _add_button(self, parent, text, command, condition, style=None, **grid):
        opts = {"style": style} if style else {}
        btn = ttk.Button(parent, text=text, command=command, **opts)
        btn.grid(**grid)
        self.buttons.append((btn, condition))
        return btn

    def _build_tabs(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill="x", padx=10, pady=4)
        p = self.player

        # --- 탐험 탭 ---
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  탐험  ")
        for c in range(3):
            tab.columnconfigure(c, weight=1)

        rows = [
            ("벌목", "axe", tg.CHOP_AREAS, tg.chop_wood, "맨손으로 나무 줍기"),
            ("채광", "pickaxe", tg.MINE_AREAS, tg.mine, "맨손으로 돌 줍기"),
        ]
        for r, (title, key, areas, fn, hand_text) in enumerate(rows):
            ttk.Label(tab, text=title, style="Section.TLabel").grid(
                row=r * 2, column=0, sticky="w", pady=(6 if r else 0, 2))
            for c, area in enumerate(("normal", "deep")):
                cfg = areas[area]
                self._add_button(
                    tab, f"{cfg['label']} (에너지 {cfg['energy']})\n{cfg['desc']}",
                    lambda f=fn, a=area: self.act(f, a),
                    lambda k=key, cost=cfg["energy"]:
                        not p.tools[k].broken and p.energy >= cost,
                    row=r * 2 + 1, column=c, sticky="ew", padx=3, pady=2)
            self._add_button(
                tab, f"{hand_text} (에너지 {tg.BARE_HAND_ENERGY})",
                lambda f=fn: self.act(f, "hand"),
                lambda k=key: p.tools[k].broken and p.energy >= tg.BARE_HAND_ENERGY,
                row=r * 2 + 1, column=2, sticky="ew", padx=3, pady=2)

        ttk.Label(tab, text="※ 도구가 부서지면 맨손 줍기만 가능합니다. 채광은 항상 자원을 얻습니다.",
                  style="Hint.TLabel").grid(row=4, column=0, columnspan=3, sticky="w", pady=(8, 0))

        # --- 캠프 탭 ---
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  캠프 (강화/수리)  ")
        tab.columnconfigure(0, weight=1)

        self.up_labels, self.rep_labels = {}, {}

        ttk.Label(tab, text="도구 강화", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        for i, key in enumerate(("axe", "pickaxe"), 1):
            lbl = ttk.Label(tab, justify="left")
            lbl.grid(row=i, column=0, sticky="w", pady=2)
            self.up_labels[key] = lbl
            self._add_button(
                tab, "강화", lambda k=key: self.act(upgrade_tool, k),
                lambda k=key: self._can_upgrade(k),
                row=i, column=1, padx=6, pady=2)

        ttk.Label(tab, text="도구 수리 (부서진 도구만)", style="Section.TLabel").grid(
            row=3, column=0, sticky="w", pady=(10, 0))
        for i, key in enumerate(("axe", "pickaxe"), 4):
            lbl = ttk.Label(tab, justify="left")
            lbl.grid(row=i, column=0, sticky="w", pady=2)
            self.rep_labels[key] = lbl
            self._add_button(
                tab, "수리", lambda k=key: self.act(repair_tool, k),
                lambda k=key: p.tools[k].broken and p.can_afford(tg.REPAIR_COSTS[k]),
                row=i, column=1, padx=6, pady=2)

        # --- 우주선 탭 ---
        tab = ttk.Frame(nb, padding=10)
        nb.add(tab, text="  우주선 수리  ")
        self.lbl_ship_cost = ttk.Label(tab, justify="left")
        self.lbl_ship_cost.pack(anchor="w", pady=(0, 8))
        btn = ttk.Button(tab, text="수리 시도하기", style="Ship.TButton",
                         command=lambda: self.act(repair_ship))
        btn.pack(anchor="w")
        self.buttons.append((
            btn, lambda: p.can_afford(tg.get_ship_cost(p.ship_repair)[0])))

    def _build_bottom(self):
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=10, pady=4)
        self._add_button(bar, "휴식하기 (다음날, 에너지 회복)", self.rest,
                         lambda: True, style="Rest.TButton", row=0, column=0, padx=(0, 6))
        ttk.Button(bar, text="게임 종료", style="Danger.TButton",
                   command=self.quit_game).grid(row=0, column=1)

    def _build_log(self):
        frame = ttk.LabelFrame(self.root, text="기록", padding=4)
        frame.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.log = tk.Text(frame, height=10, wrap="word", state="disabled", font=FONT,
                           bg=LOG_BG, fg=FG, insertbackground=FG, relief="flat",
                           padx=8, pady=6, selectbackground=OLIVE, highlightthickness=0)
        scroll = ttk.Scrollbar(frame, command=self.log.yview)
        self.log.config(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        self.log.pack(side="left", fill="both", expand=True)

    # ---------- 조건 / 갱신 ----------
    def _can_upgrade(self, key):
        tool = self.player.tools[key]
        nxt = tool.level + 1
        return nxt in tg.UPGRADES[key] and self.player.can_afford(tg.UPGRADES[key][nxt])

    def refresh(self):
        p = self.player
        inv = p.inventory
        axe, pick = p.tools["axe"], p.tools["pickaxe"]
        log, mining = p.skills["logging"], p.skills["mining"]

        self.lbl_day.config(text=f"{p.name}  |  {self.day}일차")
        self.bar_energy["value"] = p.energy
        self.lbl_energy.config(text=f"{p.energy}/{p.max_energy}")
        ratio = p.energy / p.max_energy
        level = "Ok" if ratio > 0.5 else "Mid" if ratio > 0.25 else "Low"
        self.bar_energy.config(style=f"Energy{level}.Horizontal.TProgressbar")
        self.lbl_energy.config(foreground=DANGER if p.energy < tg.MIN_ACTION_ENERGY else FG)
        self.bar_ship["value"] = p.ship_repair
        self.lbl_ship.config(text=f"{p.ship_repair}%")

        def dur(t):
            return f"{t.durability}/{tg.get_tool_durability(t.level)}" if not t.broken else "부서짐"

        self.lbl_tools.config(
            text=f"도끼 Lv.{axe.level} (내구도 {dur(axe)})   |   곡괭이 Lv.{pick.level} (내구도 {dur(pick)})")
        self.lbl_inv.config(
            text=f"나무 {inv['wood']}   돌 {inv['stone']}   철 {inv['iron']}   희귀광석 {inv['rare_ore']}")
        self.lbl_skill.config(
            text=f"벌목 Lv.{log.level} ({log.exp}/{log.required_exp})   |   "
                 f"채광 Lv.{mining.level} ({mining.exp}/{mining.required_exp})")

        for key, lbl in self.up_labels.items():
            tool = p.tools[key]
            nxt = tool.level + 1
            if nxt in tg.UPGRADES[key]:
                lbl.config(text=f"{tool.name} Lv.{tool.level} → Lv.{nxt}\n필요: {tg.format_cost(tg.UPGRADES[key][nxt])}")
            else:
                lbl.config(text=f"{tool.name} Lv.{tool.level}\n최대 레벨입니다.")
        for key, lbl in self.rep_labels.items():
            tool = p.tools[key]
            state = f"필요: {tg.format_cost(tg.REPAIR_COSTS[key])}" if tool.broken else "정상 상태"
            lbl.config(text=f"{tool.name} 수리\n{state}")

        cost, mult = tg.get_ship_cost(p.ship_repair)
        self.lbl_ship_cost.config(
            text=f"현재 진행도: {p.ship_repair}%\n"
                 f"이번 수리 필요 재료 (배율 x{mult}):\n{tg.format_cost(cost)}")

        for btn, cond in self.buttons:
            ok = (not self.finished) and cond()
            btn.config(state="normal" if ok else "disabled")

    # ---------- 행동 ----------
    def act(self, fn, *args):
        if self.finished:
            return
        with contextlib.redirect_stdout(self.writer):
            fn(self.player, *args)
            if 0 < self.player.energy < tg.MIN_ACTION_ENERGY and self.player.ship_repair < 100:
                print("⚠️ 에너지가 거의 남아있지 않습니다. 휴식을 권합니다.")
        self._check_ending()
        self.refresh()

    def rest(self):
        if self.finished:
            return
        self.day += 1
        with contextlib.redirect_stdout(self.writer):
            self.player.rest()
            print(f"🌙 {self.day}일차가 밝았습니다...")
        self.refresh()

    def _check_ending(self):
        if self.player.ship_repair >= 100 and not self.finished:
            self.finished = True
            self.banner.config(text="★  행성 탈출 성공  ★", foreground=GOOD)
            with contextlib.redirect_stdout(self.writer):
                tg.show_ending(self.player, self.day)
            self.refresh()
            messagebox.showinfo(
                "행성 탈출 성공!",
                f"우주선 수리가 완료되었습니다!\n\n생존자: {self.player.name}\n생존 일수: {self.day}일",
                parent=self.root)

    def quit_game(self):
        if self.finished or messagebox.askyesno(
                "게임 종료",
                f"정말 종료할까요?\n현재 우주선 수리도: {self.player.ship_repair}%",
                parent=self.root):
            self.root.destroy()


def main():
    root = tk.Tk()
    root.withdraw()
    name = simpledialog.askstring("불시착: 원시 행성의 생존자",
                                  "당신의 이름을 입력하세요:", parent=root)
    name = (name or "").strip() or "생존자"
    root.deiconify()
    GameApp(root, name)
    root.mainloop()


if __name__ == "__main__":
    main()
