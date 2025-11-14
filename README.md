# タイル打診アプリ

## ⚡セットアップ
**❗パッケージマネージャーのuvがローカルにインストールされます❗**
```
# Windows PowerShell 例
git clone <REPO_URL>
cd tile_hammering_application
./install_uv.ps1   # uv 本体と .venv を生成（Unix 系は install_uv.sh）
uv sync            # uv.lock に従い依存を完全再現
./.venv/Scripts/activate  # Unix: source .venv/bin/activate
python main.py     # GUI 起動
```

## 📁ディレクトリ構成
```
├── app/             # アプリケーション
│   ├── base/        # MVC 基底クラス
│   ├── config/      # 設定画面
│   ├── initial/     # 初期画面
│   ├── main/        # メインウィンドウ
│   ├── model/       # Data classes (pydantic 不使用)
│   ├── pipeline/    # BPF・FFT・Mel など DSP モジュール
│   ├── test/        # 推論用画面
│   ├── train/       # 学習用画面
│   ├── ui/          # .ui (QtDesignerで作成)
│   ├── util/        # 共通ユーティリティ
│   └── yaml/        # 設定テンプレート
├── main.py          # エントリーポイント
├── main.spec        # exe化の設定
├── install_uv.ps1   # windowsでuvをインストールするスクリプト
├── uv.lock          # 完全固定依存
├── pyproject.toml   # プロジェクト設定
└── sandbox/         # 開発時の雑記
```