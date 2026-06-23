"""卫戍协议 - 主程序入口

运行方式:
  python -m game.main                          # 默认标准难度
  python -m game.main --difficulty 绝境        # 指定难度
  python -m game.main --strategy s8            # 指定策略
  python -m game.main --host                   # 局域网主机
  python -m game.main --connect 192.168.1.100  # 局域网客户端
  python -m game.main --name 玩家名             # 联机昵称
  python -m game.main --port 5555              # 指定端口
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def main():
    args = sys.argv[1:]
    difficulty, strategy_id = "标准", "s1"
    host_mode = False
    connect_ip = ""
    player_name = ""
    port = 5555
    for i, arg in enumerate(args):
        if arg == "--difficulty" and i+1 < len(args): difficulty = args[i+1]
        elif arg == "--strategy" and i+1 < len(args): strategy_id = args[i+1]
        elif arg == "--host": host_mode = True
        elif arg == "--connect" and i+1 < len(args): connect_ip = args[i+1]
        elif arg == "--name" and i+1 < len(args): player_name = args[i+1]
        elif arg == "--port" and i+1 < len(args):
            try: port = int(args[i+1])
            except: pass

    from game.arcade_ui import run_arcade
    if host_mode or connect_ip:
        run_arcade(difficulty, strategy_id, host=host_mode, connect=connect_ip,
                   player_name=player_name, port=port)
    else:
        run_arcade(difficulty, strategy_id)


if __name__ == "__main__":
    main()
