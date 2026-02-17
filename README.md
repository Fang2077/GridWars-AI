# GridWars-AI

这是一个基于 Python 的兵棋模拟项目（含 AI 对战与玩家对战模式），您可以使用该项目对AI的理解能力、决策能力等进行简易的测试

## 特性
- AI vs AI、玩家 vs AI 等模式
- 地图管理工具

## 快速开始
1. 克隆仓库：

   git clone https://github.com/Fang2077/GridWars-AI.git

2. 建议使用虚拟环境：

   python -m venv .venv
   source .venv/bin/activate

3. 安装依赖：

   pip install -r requirements.txt

4. 运行示例：

   python3 main.py

（注意：若要运行带图形界面的对战，请确保已安装并配置 `pygame`）

## 目录结构（摘要）
- `main.py`：程序入口
- `AI/`：AI 相关代码
- `MapManager.py`：地图管理
- `AI/jsoner/`：对话/配置记录器

## 贡献
欢迎提交 issue 与 pull request。详情见 `CONTRIBUTING.md`。

## 许可证
本仓库默认采用 MIT 许可证。详情见 `LICENSE` 文件。
