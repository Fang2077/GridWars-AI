import os
import sys
current_file = os.path.abspath(__file__)
project_root = os.path.dirname(current_file)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from openai import OpenAI

class create_bot:
    """AI对战平台的Bot类（移除记忆功能）"""
    def __init__(self,api_key,base_url,model_name):
        self.api_key = api_key
        self.base_url = base_url
        self.model_name = model_name
        
        # 系统提示词（格式化优化，更易维护）
        self.system_prompt = self._get_system_prompt()

    def _get_system_prompt(self):
        """封装系统提示词，便于维护"""
        prompt = """一、游戏概述
这是一个双AI回合制策略游戏。
- 地图大小：10×10网格
- 阵营：红队（正数阵营）、黑队（负数阵营）
- 单位类型：营地（Base）、战士（Warrior）
- 核心机制：所有单位以“带符号整数点数”作为唯一属性
- 阵营由点数符号决定：正数=红队，负数=黑队，0=单位消失

二、基本定义
1. 阵营规则
- 点数>0 → 红队
- 点数<0 → 黑队
- 点数=0 → 单位立即消失

2. 单位类型
- 营地（Base）：生产战士、可被攻击、可升级、用于胜负判定
- 战士（Warrior）：可移动、可冲突、可攻击敌方营地、可升级己方营地

三、初始状态
- 地图为空棋盘（默认无障碍）
- 红队初始营地：(0,0)，点数+1
- 黑队初始营地：(9,9)，点数-1

四、回合流程
每回合按以下顺序执行：
Step1：掷骰，获得1-6随机整数D
Step2：必须且只能选择一种行动（A/B/C）：

A. 建造战士（任意D均可）
条件：
- 只能在己方营地上下左右四邻格
- 目标格为空且非障碍
效果：生成点数=D的战士（红+D，黑-D）

B. 移动战士（任意D均可）
条件：
- 选择一个己方战士
- 向上下左右移动一格
- 目标格在地图内且合法
效果：移动后立即结算冲突

C. 建造营地（仅D=6时可选）
条件：
- 当前阵营场上至少有一个战士
- 可在任意己方战士上下左右四邻格
- 目标格为空
效果：红队生成+1营地，黑队生成-1营地

五、冲突规则
1. 战士 vs 战士
result = A点数 + B点数
- result>0 → 红队战士，点数=result
- result<0 → 黑队战士，点数=result
- result=0 → 双方消失

2. 战士 vs 敌方营地
result = 战士点数 + 营地点数
- result>0 → 红队单位，点数=result
- result<0 → 黑队单位，点数=result
- result=0 → 格子清空

3. 战士 vs 己方营地（升级）
result = 战士点数 + 营地点数
- 战士消失
- 营地点数更新为result

六、胜负判定
任意一方所有营地被消灭 → 对方立即获胜

七、约束规则
1. 所有单位必须在地图范围内
2. 不允许重叠单位，冲突必须立即结算
3. 点数为0的单位立即消失
4. 每回合只能执行一次行动
5.基地不可移动

八、数学本质
整数加法对抗系统，阵营由符号决定，资源在战士与营地之间转化，随机数驱动策略博弈

九、指令格式（仅输出以下格式，无其他内容）
1. create_soldier [行,列]
2. move_soldier [行,列] [行,列]  # 第一个=起始点，第二个=终点
3. create_camp [行,列]

十、输出要求
仅按照上述指令格式输出结果，不添加任何额外说明、解释或备注。（用户会提供给你一个二维数组用于表示每个格子的具体状态，第一个维度是行，第二个维度是列，此外还会告知你当前的身份、摇取到的点数）

注意：使用move_soldier指令时可以采取起点和终点之间有间隔的策略，比如[1,0]和[3,4]两个坐标并不连贯，条件：你需要计算单位在两个不相邻坐标点之间的移动次数，移动次数必须小于摇到的点数
"""
        return prompt

    def ask_questions(self, user_input):
        """
        核心问答功能（移除记忆逻辑）
        :param user_input: 用户/游戏传入的输入（地图数据+骰子数+合法指令）
        :return: AI生成的指令（纯格式输出，无额外内容）
        """
        # 初始化OpenAI客户端
        client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )

        # 构造对话消息（无历史记忆，仅当前输入+系统提示）
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_input}
        ]

        # 调用API获取回复
        response = client.chat.completions.create(
            model=self.model_name,  # 使用配置中的模型名，更灵活
            messages=messages,
            temperature=0.7,  # 适度随机性，符合策略游戏需求
            max_tokens=100  # 限制输出长度，避免冗余
        )

        # 提取纯回复内容（无任何额外处理）
        answer = response.choices[0].message.content.strip()
        return answer