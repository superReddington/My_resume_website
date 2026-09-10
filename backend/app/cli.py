"""命令行调试：python -m app.cli "你的问题"
"""

import sys

from dotenv import load_dotenv

load_dotenv()

from app.db.pool import init_db
from app.agent.graph import run_once


def main() -> None:
    if len(sys.argv) < 2:
        print('用法: python -m app.cli "你的问题"')
        sys.exit(1)
    init_db()
    question = " ".join(sys.argv[1:])
    print(run_once(question))


if __name__ == "__main__":
    main()
