"""第13回 倉庫番・演習版：完成デモを読み、別の構造へ処理を移植する。

演習の進め方
  ① TODO 1：WASDでプレイヤーを移動（範囲外に出さない）
  ② TODO 2：壁にぶつかると移動できないようにする
  ③ TODO 3：箱を押す処理を追加（壁や別の箱の手前では止まる）

完成デモと関数名やデータ構造が違います。必要な判定を読み取り、
このファイルの引数・変数に合わせて作り直しましょう。
演習途中でも実行できます（最初は移動キーを押しても動きません）。
"""

# 画面の左上が (0, 0)。右へ行くと x が増え、下へ行くと y が増える。
# WASD の差分：w=(0,-1), s=(0,1), a=(-1,0), d=(1,0)
KEY_TO_VECTOR = {"w": (0, -1), "s": (0, 1), "a": (-1, 0), "d": (1, 0)}

# # は壁、. はゴール、$ は箱、@ はプレイヤー。
# * はゴール上の箱、+ はゴール上のプレイヤー。
# 複数行文字列を splitlines() で行ごとのリストに変換する。
MAP_TEXT = [
    """#########
#       #
#  .    #
#  $    #
#  @    #
#       #
#########""",
    """##########
#        #
#  ..    #
#  $$    #
#   @    #
#        #
##########""",
    """###########
#         #
#         #
#    #    #
#    #    #
#  . # $  #
#      @  #
###########""",
]


def new_board(level_text):
    """ステージの文字列を読み、管理データを作る。引数：文字列。戻り値：辞書。"""
    rows = level_text.splitlines()
    if not rows or any(len(row) != len(rows[0]) for row in rows):
        raise ValueError("マップの横幅を揃えてください")
    board = {
        "size": (len(rows[0]), len(rows)),
        "solid": set(),  # 壁の座標集合
        "targets": set(),  # ゴールの座標集合
        "crates": set(),  # 箱の座標集合
        "hero": None,     # プレイヤーの座標
        "steps": 0,
        "past": [],       # 一手戻すための履歴
    }
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            p = (x, y)
            if ch == "#":
                board["solid"].add(p)
            if ch in ".+*":
                board["targets"].add(p)
            if ch in "$*":
                board["crates"].add(p)
            if ch in "@+":
                if board["hero"] is not None:
                    raise ValueError("プレイヤーは1人にしてください")
                board["hero"] = p
    if board["hero"] is None or not board["crates"] or len(board["crates"]) != len(board["targets"]):
        raise ValueError("プレイヤー1人、箱とゴールは同数にしてください")
    return board


def print_board(board):
    """現在の盤面を画面に表示する。引数：board。戻り値：なし。"""
    width, height = board["size"]
    print("\n" * 2 + "=== SOKOBAN : EXERCISE ===")
    print("# 壁  . ゴール  $ 箱  @ プレイヤー  * ゴール上の箱")
    for y in range(height):
        output = ""
        for x in range(width):
            p = (x, y)
            if p == board["hero"]:
                output += "+" if p in board["targets"] else "@"
            elif p in board["crates"]:
                output += "*" if p in board["targets"] else "$"
            elif p in board["solid"]:
                output += "#"
            elif p in board["targets"]:
                output += "."
            else:
                output += " "
        print(output)
    print(f"移動回数: {board['steps']} | WASD 移動 / U 戻す / R 再開 / Q 終了")


def in_field(board, point):
    """座標が盤面内か調べる。引数：board, (x,y)。戻り値：bool。"""
    x, y = point
    w, h = board["size"]
    return 0 <= x < w and 0 <= y < h


def next_position(origin, vector):
    """座標の足し算。引数：(x,y), (dx,dy)。戻り値：(x2,y2)。"""
    return (origin[0] + vector[0], origin[1] + vector[1])


def can_enter(board, destination):
    """TODO 2：壁判定。引数：board, 移動先座標。戻り値：移動可ならTrue。

    まず TODO 1 では呼ばなくてもよい。
    TODO 2 では、盤面内か、壁に含まれるかを確認しよう。
    デモ版では walls という名前だが、演習版では solid に入っている。
    """
    # TODO 2: 条件を実装する（現状では壁も通過できる）
    return in_field(board, destination) and destination not in board["solid"]


def push_crate(board, crate_position, vector):
    """箱を押せる場合だけ移動させる。"""

    # 箱を押した後の位置
    destination = next_position(crate_position, vector)

    # 壁または盤面外なら押せない
    if not can_enter(board, destination):
        return False

    # 移動先に別の箱があれば押せない
    if destination in board["crates"]:
        return False

    # 元の位置から箱を取り除く
    board["crates"].remove(crate_position)

    # 新しい位置に箱を置く
    board["crates"].add(destination)

    return True

def apply_move(board, direction_key):
    """プレイヤーの移動、壁判定、箱押しを処理する。"""

    # WASD以外のキーは無効
    if direction_key not in KEY_TO_VECTOR:
        return False

    # 移動方向を取得
    vector = KEY_TO_VECTOR[direction_key]

    # プレイヤーの現在位置
    current = board["hero"]

    # 次の移動先を計算
    destination = next_position(current, vector)

    # 壁や盤面外なら移動しない
    if not can_enter(board, destination):
        return False

    # 移動前の状態を保存（Undo用）
    previous_hero = board["hero"]
    previous_crates = board["crates"].copy()

    # 移動先に箱がある場合
    if destination in board["crates"]:

        # 箱を押せなければ移動しない
        if not push_crate(board, destination, vector):
            return False

    # 移動前の状態を履歴に保存
    board["past"].append((previous_hero, previous_crates))

    # プレイヤーの位置を更新
    board["hero"] = destination

    # 移動回数を増やす
    board["steps"] += 1

    return True

def step_back(board):
    """Undoを実行。引数：board。戻り値：なし。"""
    if board["past"]:
        board["hero"], board["crates"] = board["past"].pop()
        board["steps"] -= 1


def completed(board):
    """すべての箱がゴール上にあるか調べる。引数：board。戻り値：bool。"""
    return board["crates"] == board["targets"]


def start():
    """キー入力・ステージ進行を管理する。戻り値：なし。"""
    index = 0
    board = new_board(MAP_TEXT[index])
    while True:
        print_board(board)
        if completed(board):
            print("ステージクリア！")
            index += 1
            if index == len(MAP_TEXT):
                print("全ステージクリア！")
                break
            input("Enterで次のステージへ...")
            board = new_board(MAP_TEXT[index])
            continue
        key = input("操作 > ").strip().lower()[:1]
        if key == "q":
            break
        if key == "r":
            board = new_board(MAP_TEXT[index])
        elif key == "u":
            step_back(board)
        else:
            apply_move(board, key)


if __name__ == "__main__":
    start()
