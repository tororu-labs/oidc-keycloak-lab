from __future__ import annotations

import sys
from pathlib import Path

# テスト実行時に app ディレクトリをモジュール検索パスに追加する。
sys.path.insert(0, str(Path(__file__).parent))
