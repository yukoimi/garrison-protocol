"""卫戍协议 — PyInstaller 入口"""
import sys
import os

# PyInstaller 打包后确保能导入 game 包
if getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from game.arcade_ui import run_arcade

if __name__ == "__main__":
    run_arcade()
