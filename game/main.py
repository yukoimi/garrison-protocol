"""卫戍协议 - 主程序入口

运行方式:
  python -m game.main                    # 默认标准难度
  python -m game.main --difficulty 绝境   # 指定难度
  python -m game.main --strategy s8      # 指定策略
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    args = sys.argv[1:]
    difficulty, strategy_id = "标准", "s1"
    for i, arg in enumerate(args):
        if arg == "--difficulty" and i+1 < len(args): difficulty = args[i+1]
        elif arg == "--strategy" and i+1 < len(args): strategy_id = args[i+1]

    from game.arcade_ui import run_arcade
    run_arcade(difficulty, strategy_id)


if __name__ == "__main__":
    main()
