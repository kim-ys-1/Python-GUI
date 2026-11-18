import random
import time

# ==============================
# 상수 / 밸런스 테이블
# ==============================
MIN_ACTION_ENERGY = 15      # 가장 싼 작업(근처 숲 벌목)의 에너지
BARE_HAND_ENERGY = 15       # 맨손 채집 에너지

RESOURCE_NAMES = {"wood": "나무", "stone": "돌", "iron": "철", "rare_ore": "희귀광석"}

TOOL_DURABILITY = {1: 30, 2: 50, 3: 80}
DURABILITY_REDUCTION = {1: 0, 2: 1, 3: 2}   # 도구 레벨별 내구도 소모 감소

AXE_WOOD_BONUS = {1: 0, 2: 2, 3: 4}
PICK_STONE_BONUS = {1: 0, 2: 3, 3: 5}
PICK_IRON_BONUS = {1: 0, 2: 1, 3: 2}

# 도구 강화 비용 {도구: {목표 레벨: 재료}}
UPGRADES = {
    "axe": {2: {"wood": 12, "iron": 4},
            3: {"wood": 20, "iron": 8, "rare_ore": 2}},
    "pickaxe": {2: {"wood": 8, "iron": 6},
                3: {"wood": 15, "iron": 10, "rare_ore": 3}},
}

# 부서진 도구 수리 비용
# (맨손 채집으로 구할 수 있는 나무/돌만 사용 → 막힘 방지)
REPAIR_COSTS = {
    "axe": {"wood": 5, "stone": 3},
    "pickaxe": {"wood": 3, "stone": 5},
}

CHOP_AREAS = {
    "normal": {"label": "근처 숲", "energy": 15, "exp": 1, "bonus": 0,
               "desc": "나무 보통"},
    "deep": {"label": "울창한 원시림", "energy": 25, "exp": 2, "bonus": 3,
             "desc": "나무 많음"},
}

# main : 매번 반드시 나오는 주 자원 (자원, (최소, 최대))
# bonus: 추가로 나올 수 있는 부 자원 (확률, 자원, (최소, 최대))
# → 한 번 채광하면 항상 1개 이상 얻는다 (꽝 없음)
MINE_AREAS = {
    "normal": {
        "label": "일반 광산", "energy": 20, "exp": 1,
        "desc": "돌 위주, 철 소량",
        "main": ("stone", (3, 6)),
        "bonus": (0.35, "iron", (1, 3)),
    },
    "deep": {
        "label": "깊은 광맥", "energy": 32, "exp": 2,
        "desc": "철 위주, 희귀광석 소량",
        "main": ("iron", (3, 5)),
        "bonus": (0.30, "rare_ore", (1, 2)),
    },
}

MINE_MESSAGES = {
    "stone": "🪨 돌을 채취했습니다. 돌 +{n}",
    "iron": "⛓️ 철을 채취했습니다. 철 +{n}",
}
BONUS_MESSAGES = {
    "iron": "⛓️ 철이 조금 섞여 나왔습니다. 철 +{n}",
    "rare_ore": "💎 희귀 광석을 발견했습니다! 희귀광석 +{n}",
}


# ==============================
# 공통 유틸
# ==============================
def ask(prompt="선택: "):
    return input(prompt).strip()


def format_cost(cost):
    return " + ".join(f"{RESOURCE_NAMES[k]} {v}" for k, v in cost.items())


def get_required_exp(level):
    """레벨이 오를수록 필요 경험치 증가"""
    return 20 + (level - 1) * 8


def get_skill_bonus(level):
    """숙련 보너스"""
    if level <= 1:
        return 0
    elif level <= 3:
        return level - 1
    elif level <= 6:
        return 2 + (level - 3) * 2
    else:
        return 8 + (level - 6) * 3


def get_tool_durability(level):
    return TOOL_DURABILITY.get(level, TOOL_DURABILITY[3])


# ==============================
# 도구 / 숙련도 / 플레이어
# ==============================
class Tool:
    def __init__(self, name, icon):
        self.name = name
        self.icon = icon
        self.level = 1
        self.durability = get_tool_durability(1)

    @property
    def broken(self):
        return self.durability <= 0

    def wear(self, low, high):
        """내구도 소모. 부서졌으면 True"""
        loss = max(1, random.randint(low, high) - DURABILITY_REDUCTION[self.level])
        self.durability = max(0, self.durability - loss)
        return self.broken

    def restore(self):
        self.durability = get_tool_durability(self.level)

    def upgrade(self):
        self.level += 1
        self.restore()


class Skill:
    def __init__(self, name):
        self.name = name
        self.level = 1
        self.exp = 0

    @property
    def required_exp(self):
        return get_required_exp(self.level)

    def add_exp(self, amount=1):
        self.exp += amount
        while self.exp >= self.required_exp:
            self.exp -= self.required_exp
            self.level += 1
            print(f"🎉 {self.name} 숙련도가 올랐습니다! (Lv.{self.level})")


class Player:
    def __init__(self, name):
        self.name = name
        self.energy = 100
        self.max_energy = 100

        self.tools = {"axe": Tool("도끼", "🪓"), "pickaxe": Tool("곡괭이", "⛏️")}
        self.inventory = {key: 0 for key in RESOURCE_NAMES}
        self.skills = {"logging": Skill("벌목"), "mining": Skill("채광")}
        self.ship_repair = 0

    # --- 재료 ---
    def can_afford(self, cost):
        return all(self.inventory[k] >= v for k, v in cost.items())

    def pay(self, cost):
        for k, v in cost.items():
            self.inventory[k] -= v

    # --- 에너지 ---
    def spend_energy(self, cost):
        if self.energy < cost:
            print(f"❌ 에너지가 부족합니다. (필요: {cost})")
            return False
        self.energy -= cost
        return True

    def rest(self):
        self.energy = self.max_energy
        print("😴 잠시 쉬며 체력을 회복했습니다. 에너지가 모두 찼습니다.")

    # --- 상태 표시 ---
    def show_status(self):
        axe, pick = self.tools["axe"], self.tools["pickaxe"]
        inv = self.inventory
        log, mine_ = self.skills["logging"], self.skills["mining"]
        print("\n" + "=" * 55)
        print(f"👤 {self.name} | 에너지: {self.energy}/{self.max_energy}")
        print(f"🪓 도끼 Lv.{axe.level} (내구도 {axe.durability}) | "
              f"⛏️ 곡괭이 Lv.{pick.level} (내구도 {pick.durability})")
        print(f"📦 나무: {inv['wood']} | 돌: {inv['stone']} | 철: {inv['iron']} | 희귀광석: {inv['rare_ore']}")
        print(f"⭐ 벌목 Lv.{log.level} ({log.exp}/{log.required_exp}) | "
              f"채광 Lv.{mine_.level} ({mine_.exp}/{mine_.required_exp})")
        print(f"🚀 우주선 수리 진행도: {self.ship_repair}%")
        print("=" * 55)


# ==============================
# 장소 선택
# ==============================
def select_area(activity, tool):
    """장소 선택. 'normal' / 'deep' / 'hand'(맨손) / None(취소) 반환"""
    areas = CHOP_AREAS if activity == "벌목" else MINE_AREAS
    normal, deep = areas["normal"], areas["deep"]

    print(f"\n{activity}할 장소를 선택하세요.")

    if tool.broken:
        print(f"⚠️ {tool.name}가 부서져 있어 맨손으로만 작업할 수 있습니다.")
        print(f"1. 맨손으로 모으기 (에너지 {BARE_HAND_ENERGY}, 소량)")
        print("2. 돌아가기")
        while True:
            choice = ask()
            if choice == "1":
                return "hand"
            if choice == "2":
                return None
            print("잘못된 입력입니다.")

    print(f"1. {normal['label']} (에너지 {normal['energy']}, {normal['desc']})")
    print(f"2. {deep['label']} (에너지 {deep['energy']}, {deep['desc']})")
    print("3. 돌아가기")

    while True:
        choice = ask()
        if choice == "1":
            return "normal"
        if choice == "2":
            return "deep"
        if choice == "3":
            return None
        print("잘못된 입력입니다.")


# ==============================
# 벌목
# ==============================
def chop_wood(player, area):
    axe = player.tools["axe"]

    # 맨손 채집 (도구가 없어도 게임이 막히지 않도록)
    if area == "hand":
        if not player.spend_energy(BARE_HAND_ENERGY):
            return
        gained = random.randint(1, 2)
        player.inventory["wood"] += gained
        print(f"🤲 맨손으로 나뭇가지를 주워 모았습니다. 나무 +{gained}")
        return

    cfg = CHOP_AREAS[area]
    if axe.broken:
        print("❌ 도끼가 부서져 사용할 수 없습니다.")
        return
    if not player.spend_energy(cfg["energy"]):
        return

    broke = axe.wear(2, 5)

    logging = player.skills["logging"]
    base = random.randint(3, 7)
    gained = base + get_skill_bonus(logging.level) + cfg["bonus"] + AXE_WOOD_BONUS[axe.level]
    player.inventory["wood"] += gained
    logging.add_exp(cfg["exp"])

    print(f"🪓 [{cfg['label']}] 나무를 베어냈습니다. 나무 +{gained}")
    if broke:
        print("⚠️ 도끼가 완전히 부서졌습니다!")


# ==============================
# 채광
# ==============================
def mine(player, area):
    pick = player.tools["pickaxe"]

    if area == "hand":
        if not player.spend_energy(BARE_HAND_ENERGY):
            return
        gained = random.randint(1, 2)
        player.inventory["stone"] += gained
        print(f"🤲 맨손으로 돌멩이를 주워 모았습니다. 돌 +{gained}")
        return

    cfg = MINE_AREAS[area]
    if pick.broken:
        print("❌ 곡괭이가 부서져 사용할 수 없습니다.")
        return
    if not player.spend_energy(cfg["energy"]):
        return

    broke = pick.wear(3, 6)

    mining = player.skills["mining"]
    skill_bonus = get_skill_bonus(mining.level)
    tool_bonus = {
        "stone": PICK_STONE_BONUS[pick.level],
        "iron": PICK_IRON_BONUS[pick.level],
        "rare_ore": 0,
    }

    # 주 자원: 항상 획득 (숙련 + 도구 보너스)
    kind, (low, high) = cfg["main"]
    gained = random.randint(low, high) + skill_bonus + tool_bonus[kind]
    player.inventory[kind] += gained
    print(f"[{cfg['label']}] " + MINE_MESSAGES[kind].format(n=gained))

    # 부 자원: 확률적으로 추가 획득
    chance, bkind, (blow, bhigh) = cfg["bonus"]
    if random.random() < chance:
        bgained = random.randint(blow, bhigh) + tool_bonus[bkind]
        player.inventory[bkind] += bgained
        print(f"[{cfg['label']}] " + BONUS_MESSAGES[bkind].format(n=bgained))

    mining.add_exp(cfg["exp"])

    if broke:
        print("⚠️ 곡괭이가 완전히 부서졌습니다!")


# ==============================
# 제작 (도구 3단계)
# ==============================
def craft_menu(player):
    order = ["axe", "pickaxe"]
    while True:
        print("\n🔨 간이 제작대")
        print("-" * 45)
        for i, key in enumerate(order, 1):
            tool = player.tools[key]
            nxt = tool.level + 1
            if nxt in UPGRADES[key]:
                cost = UPGRADES[key][nxt]
                mark = "✅" if player.can_afford(cost) else "❌"
                print(f"{i}. {tool.name} 강화 (Lv.{tool.level} → {nxt}: {format_cost(cost)}) {mark}")
            else:
                print(f"{i}. {tool.name} (최대 레벨 Lv.{tool.level})")
        print(f"{len(order) + 1}. 돌아가기")

        choice = ask()
        if choice == str(len(order) + 1):
            break
        if choice not in ("1", "2"):
            print("잘못된 입력입니다.")
            continue

        key = order[int(choice) - 1]
        tool = player.tools[key]
        nxt = tool.level + 1
        if nxt not in UPGRADES[key]:
            print("이미 최대 레벨입니다.")
            continue

        cost = UPGRADES[key][nxt]
        if not player.can_afford(cost):
            print("❌ 재료가 부족합니다.")
            continue

        player.pay(cost)
        tool.upgrade()
        print(f"✨ {tool.name}를 Lv.{tool.level}로 강화했습니다! (내구도 {tool.durability})")


# ==============================
# 도구 수리 (부서진 도구만 표시)
# ==============================
def repair_tools(player):
    while True:
        print("\n🔧 도구 수리")
        broken = [key for key in ("axe", "pickaxe") if player.tools[key].broken]

        if not broken:
            print("현재 부서진 도구가 없습니다.")
            print("1. 돌아가기")
            if ask() == "1":
                break
            print("잘못된 입력입니다.")
            continue

        for i, key in enumerate(broken, 1):
            tool = player.tools[key]
            print(f"{i}. {tool.name} 수리 ({format_cost(REPAIR_COSTS[key])})")
        print(f"{len(broken) + 1}. 돌아가기")

        choice = ask()
        if choice == str(len(broken) + 1):
            break
        if not (choice.isdigit() and 1 <= int(choice) <= len(broken)):
            print("잘못된 입력입니다.")
            continue

        key = broken[int(choice) - 1]
        tool = player.tools[key]
        cost = REPAIR_COSTS[key]
        if player.can_afford(cost):
            player.pay(cost)
            tool.restore()
            print(f"{tool.icon} {tool.name}를 수리했습니다.")
        else:
            print(f"❌ 재료가 부족합니다. ({format_cost(cost)} 필요)")


# ==============================
# 우주선 수리 (진행도별 배율)
# ==============================
def get_repair_multiplier(progress):
    if progress < 30:
        return 1.0
    elif progress < 60:
        return 1.3
    elif progress < 80:
        return 1.6
    else:
        return 2.0


def get_ship_cost(progress):
    mult = get_repair_multiplier(progress)
    base = {"wood": 10, "stone": 8, "iron": 6, "rare_ore": 1}
    # round: 부동소수점 오차(예: 9.6000000001) 방지
    cost = {k: int(round(v * mult, 6)) for k, v in base.items()}
    cost["rare_ore"] = max(1, cost["rare_ore"])
    return cost, mult


def ship_repair_menu(player):
    print("\n🚀 반파된 우주선 앞")
    print(f"현재 수리 진행도: {player.ship_repair}%")

    cost, mult = get_ship_cost(player.ship_repair)
    print("-" * 45)
    print(f"이번 수리에 필요한 재료 (배율 x{mult}):")
    print(f"  {format_cost(cost)}")
    print("-" * 45)
    print("1. 수리 시도하기")
    print("2. 돌아가기")

    choice = ask()
    if choice == "1":
        if not player.can_afford(cost):
            print("❌ 재료가 부족합니다.")
            return

        player.pay(cost)
        progress = random.randint(12, 22)
        player.ship_repair = min(100, player.ship_repair + progress)

        print(f"\n🔧 우주선을 수리했습니다! 진행도 +{progress}%")
        print(f"현재 우주선 상태: {player.ship_repair}%")
        if player.ship_repair >= 100:
            print("\n✨ 우주선 수리가 완료되었습니다!")
    elif choice != "2":
        print("잘못된 입력입니다.")


# ==============================
# 캠프
# ==============================
def camp(player):
    while True:
        print("\n🏕️ 임시 캠프")
        print("1. 간이 제작대 이용 (도구 강화)")
        print("2. 도구 수리")
        print("3. 캠프를 떠난다")

        choice = ask()
        if choice == "1":
            craft_menu(player)
        elif choice == "2":
            repair_tools(player)
        elif choice == "3":
            break
        else:
            print("잘못된 입력입니다.")


# ==============================
# 엔딩
# ==============================
def show_ending(player, day):
    axe, pick = player.tools["axe"], player.tools["pickaxe"]
    print("\n" + "=" * 55)
    print("🚀 우주선 수리 완료! 행성 탈출 성공!")
    print("=" * 55)
    print(f"생존자: {player.name}")
    print(f"생존 일수: {day}일")
    print(f"최종 벌목 숙련: Lv.{player.skills['logging'].level}")
    print(f"최종 채광 숙련: Lv.{player.skills['mining'].level}")
    print(f"최종 도끼 등급: Lv.{axe.level} | 곡괭이 등급: Lv.{pick.level}")
    print()
    print("반파된 우주선을 고쳐 하늘로 올라갑니다.")
    print("이 원시 행성에서의 고된 시간이 드디어 끝났습니다.")
    print("집으로 돌아가는 길이 열렸습니다...")
    print("=" * 55)


# ==============================
# 메인 루프
# ==============================
def next_day(player, day):
    player.rest()
    day += 1
    print(f"\n🌙 {day}일차가 밝았습니다...")
    time.sleep(0.7)
    return day


def main():
    print("=" * 55)
    print("🌌 불시착: 원시 행성의 생존자")
    print("=" * 55)
    print("타 행성의 새틀라이트 어택으로 우주선이 반파되었습니다.")
    print("당신은 이름 모를 원시행성에 불시착했습니다.")
    print("나무, 돌, 철, 희귀 광석을 모아")
    print("망가진 우주선을 수리하고 이 행성을 탈출해야 합니다.\n")

    name = ask("당신의 이름을 입력하세요: ") or "생존자"
    player = Player(name)

    print(f"\n생존을 시작합니다, {player.name}님.")
    print("목표: 우주선 수리 진행도 100% 달성\n")

    day = 1

    while True:
        if player.ship_repair >= 100:
            show_ending(player, day)
            break

        print(f"\n===== {day}일차 =====")
        player.show_status()

        if player.energy < MIN_ACTION_ENERGY:
            print("\n😵 에너지가 부족하여 벌목/채광을 할 수 없습니다. (캠프·우주선 수리·휴식은 가능)")

        print("\n무엇을 하시겠습니까?")
        print("1. 벌목하기")
        print("2. 채광하기")
        print("3. 캠프 가기 (제작/수리)")
        print("4. 우주선 수리하기")
        print("5. 휴식하기 (다음날)")
        print("6. 게임 종료")

        choice = ask()

        if choice == "1":
            if player.energy < MIN_ACTION_ENERGY:
                print("❌ 에너지가 부족합니다. 휴식이 필요합니다.")
                continue
            area = select_area("벌목", player.tools["axe"])
            if area:
                chop_wood(player, area)
        elif choice == "2":
            if player.energy < MIN_ACTION_ENERGY:
                print("❌ 에너지가 부족합니다. 휴식이 필요합니다.")
                continue
            area = select_area("채광", player.tools["pickaxe"])
            if area:
                mine(player, area)
        elif choice == "3":
            camp(player)
        elif choice == "4":
            ship_repair_menu(player)
        elif choice == "5":
            day = next_day(player, day)
        elif choice == "6":
            print(f"\n게임을 종료합니다. 현재 우주선 수리도: {player.ship_repair}%")
            break
        else:
            print("잘못된 입력입니다.")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\n\n게임을 종료합니다.")
