import random
import tkinter as tk
from tkinter import messagebox

MAX_TRIES = 9
DIGITS = 4

BG = "#000000"
COLORS = {
    "green": "#2E9E4F",
    "yellow": "#E6B800",
    "red": "#D32F2F",
}
FONT = "맑은 고딕"


class NumBaseGame:
    def __init__(self, root):
        self.root = root
        root.title("숫자 야구 힌트 게임")
        root.configure(bg=BG)
        root.resizable(False, False)

        tk.Label(
            root,
            text="1~9 사이 숫자 4개를 입력하세요 (중복 가능)\n"
                 "초록: 숫자·자리 일치 / 노랑: 숫자만 일치 / 빨강: 없음",
            font=(FONT, 10), bg=BG, fg="white",
        ).pack(padx=12, pady=(12, 6))

        # 입력 영역
        input_frame = tk.Frame(root, bg=BG)
        input_frame.pack(pady=6)
        self.entry = tk.Entry(input_frame, font=(FONT, 16), width=8,
                              justify="center", bg="#222222", fg="white",
                              insertbackground="white", relief="flat",
                              disabledbackground="#111111",
                              disabledforeground="#777777")
        self.entry.pack(side="left", padx=4)
        self.entry.bind("<Return>", lambda e: self.submit())
        self.btn = tk.Button(input_frame, text="입력", width=6, command=self.submit)
        self.btn.pack(side="left", padx=4)

        self.status = tk.Label(root, text="", font=(FONT, 10), bg=BG, fg="white")
        self.status.pack()

        # 기록 보드: 맨 위가 가장 최근 입력, 이전 기록은 아래로 밀려남
        board = tk.Frame(root, bg=BG)
        board.pack(padx=12, pady=8)
        self.cells = []
        for r in range(MAX_TRIES):
            row = []
            for c in range(DIGITS):
                lbl = tk.Label(board, text="", width=3, height=1,
                               font=(FONT, 18, "bold"),
                               bg=BG, fg="white",
                               relief="flat", bd=0, highlightthickness=0)
                lbl.grid(row=r, column=c, padx=4, pady=4)
                row.append(lbl)
            self.cells.append(row)

        tk.Button(root, text="새 게임", command=self.new_game).pack(pady=(0, 12))

        self.new_game()

    def new_game(self):
        self.rand_num = random.choices(range(1, 10), k=DIGITS)
        self.history = []  # 각 원소: (guess, result), 0번이 최신
        self.finished = False
        self.redraw()
        self.entry.config(state="normal")
        self.entry.delete(0, tk.END)
        self.btn.config(state="normal")
        self.status.config(text=f"남은 기회: {MAX_TRIES}")
        self.entry.focus_set()

    def redraw(self):
        for r, row in enumerate(self.cells):
            if r < len(self.history):
                guess, result = self.history[r]
                for c, lbl in enumerate(row):
                    lbl.config(text=str(guess[c]), bg=COLORS[result[c]])
            else:
                for lbl in row:
                    lbl.config(text="", bg=BG)

    def judge(self, guess):
        """각 자리의 결과('green'/'yellow'/'red') 리스트를 반환"""
        result = ["red"] * DIGITS
        remaining = self.rand_num.copy()

        # 1단계: 자리까지 맞는 것
        for i, x in enumerate(guess):
            if x == self.rand_num[i]:
                result[i] = "green"
                remaining.remove(x)

        # 2단계: 숫자만 맞는 것
        for i, x in enumerate(guess):
            if result[i] == "green":
                continue
            if x in remaining:
                result[i] = "yellow"
                remaining.remove(x)

        return result

    def submit(self):
        if self.finished:
            return

        text = self.entry.get().strip()
        if len(text) != DIGITS or not all(ch in "123456789" for ch in text):
            messagebox.showwarning("입력 오류", f"1~9 사이 숫자 {DIGITS}개를 입력하세요.")
            return

        guess = [int(ch) for ch in text]
        result = self.judge(guess)

        # 새 기록을 맨 위에 넣어 기존 기록을 한 칸씩 아래로 밀어냄
        self.history.insert(0, (guess, result))
        self.redraw()

        tries = len(self.history)
        self.entry.delete(0, tk.END)
        self.status.config(text=f"남은 기회: {MAX_TRIES - tries}")

        if result.count("green") == DIGITS:
            self.end_game()
            messagebox.showinfo("정답", f"정답입니다! ({tries}번 만에 성공)")
        elif tries >= MAX_TRIES:
            self.end_game()
            answer = "".join(map(str, self.rand_num))
            messagebox.showinfo("실패", f"기회를 모두 사용했습니다.\n정답은 {answer} 입니다.")

    def end_game(self):
        self.finished = True
        self.entry.config(state="disabled")
        self.btn.config(state="disabled")


if __name__ == "__main__":
    root = tk.Tk()
    NumBaseGame(root)
    root.mainloop()