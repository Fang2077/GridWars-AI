import os
import sys

# 1. 获取当前脚本（AIvsAI.py）的绝对路径
current_file = os.path.abspath(__file__)
# 2. 获取当前脚本所在目录（game_mode）
current_dir = os.path.dirname(current_file)
# 3. 获取上级目录（main/）—— 往上退1级
parent_dir = os.path.dirname(current_dir)
# 4. 将上级目录加入sys.path（Python会在这里找模块）
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

import random
import ast
import pygame
from MapManager import MapManager
from AI_functions import create_bot

# ===================== Pygame 渲染模块 =====================
# 棋盘渲染配置
GRID_SIZE = 60
GRID_COUNT = 6
BOARD_OFFSET = (50, 50)
SCREEN_WIDTH = BOARD_OFFSET[0] + GRID_SIZE * GRID_COUNT + 50
SCREEN_HEIGHT = BOARD_OFFSET[1] + GRID_SIZE * GRID_COUNT + 50

# 颜色配置
COLORS = {
    'background': (240, 240, 240),
    'grid_empty': (200, 200, 200),
    'grid_border': (0, 0, 0),
    'camp_red': (255, 80, 80),
    'camp_black': (80, 80, 80),
    'soldier_red': (255, 150, 150),
    'soldier_black': (100, 100, 100)
}

# 初始化 Pygame 渲染器
pygame.init()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("兵棋游戏 - 实时渲染")
clock = pygame.time.Clock()

def grid_to_pixel(grid_pos):
    """逻辑坐标[行,列]转像素坐标"""
    row, col = grid_pos
    x = BOARD_OFFSET[0] + col * GRID_SIZE
    y = BOARD_OFFSET[1] + row * GRID_SIZE
    return (x, y)

def render_board(map_data):
    """渲染棋盘（核心函数）"""
    # 处理 Pygame 窗口事件（避免卡死）
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
    
    # 清空屏幕
    screen.fill(COLORS['background'])
    
    # 绘制所有格子
    for row in range(len(map_data)):
        for col in range(len(map_data[row])):
            pixel_x, pixel_y = grid_to_pixel((row, col))
            grid_rect = pygame.Rect(pixel_x, pixel_y, GRID_SIZE, GRID_SIZE)
            
            # 获取格子数据
            cell = map_data[row][col]
            count = cell['count']
            type_ = cell['type']
            
            # 选择底色
            if type_ == 'camp':
                bg_color = COLORS['camp_red'] if count > 0 else COLORS['camp_black']
            elif type_ == 'soldier':
                bg_color = COLORS['soldier_red'] if count > 0 else COLORS['soldier_black']
            else:
                bg_color = COLORS['grid_empty']
            
            # 绘制格子和边框
            pygame.draw.rect(screen, bg_color, grid_rect)
            pygame.draw.rect(screen, COLORS['grid_border'], grid_rect, 1)
    
    # 更新画面
    pygame.display.flip()
    clock.tick(5)

# ===================== 逻辑模块 =====================
#规定名称：营地：camp，战士：soldier，阵营：red\black

#初始化地图（6*6）
maper = MapManager()
maper.CreateMap(6,6)
maper.AddUnit(1,'camp',[0,0])
maper.AddUnit(-1,'camp',[5,5])

#全局变量初始化
DiceCount = 0
Player = 'red'  #玩家（红方先行）
ChooseList = [] #选项列表
RedCampNum = 0    #红营地数
BlackCampNum = 0  #黑营地数
RedSoldierNum = 0   #红战士数
BlackSoldierNum = 0 #黑战士数
LoopLock = True
MainLoopLock = True
mistake_times = 0

#骰子：生成随机数（1-6）
def dice():
    DiceNum = random.randint(1,6)
    return DiceNum  

def CreatSoldier(Player,pos,DiceCount):
    #1.检验pos的pass是否为True（敌我双方所有单位均可叠加点数）
    #2.检验是否其上下左右存在己方camp
    #3.将count与pos上的count相加

    TargetCount = maper.MapData[pos[0]][pos[1]]['count']
    valid = maper.MapData[pos[0]][pos[1]]['pass']
    PosNeighbors = [
    [pos[0],pos[1]-1],#left
    [pos[0],pos[1]+1],#right
    [pos[0]+1,pos[1]],#up
    [pos[0]-1,pos[1]] #down
    ]
    InRuleNeibors = []#合法邻居列表
    num = 0#周围的camp数

    for TestPoint in PosNeighbors:
        # 合法条件：1. 不越界 2. 非障碍 
        if 0 <= TestPoint[0] < maper.length and 0 <= TestPoint[1] < maper.width:  # 不越界
            if maper.MapData[TestPoint[0]][TestPoint[1]]['pass'] == True:  # 非障碍
                    InRuleNeibors.append(TestPoint)
    for i in InRuleNeibors:
        if maper.MapData[i[0]][i[1]]['type'] == 'camp':
            if Player == 'red' and maper.MapData[i[0]][i[1]]['count'] > 0 or Player == 'black' and maper.MapData[i[0]][i[1]]['count'] < 0:
                num = num + 1
    if num == 0:
        return False
    
    if valid == False:
        return False
    
    else:
        if Player == 'red':
            TargetCount = TargetCount + DiceCount
        elif Player == 'black':
            TargetCount = TargetCount - DiceCount
        maper.MapData[pos[0]][pos[1]]['count'] = TargetCount
        maper.MapData[pos[0]][pos[1]]['type'] = 'soldier'
        #所有流通点数来源
        return True

def MoveSoldier(Player,start,end,DiceCount):
    #1.检验起点、终点是否为障碍
    #2.判断起点单位是否为战士
    #3.判断玩家阵营和选中是否相符
    #4.检验路程是否超过摇到的点数
    #5.将起点的点数与终点的点数相加
    #6.起点点数清零
    #7.若判断终点最终所有单位死亡即点数归零，将type置空

    type = maper.MapData[start[0]][start[1]]['type']
    valid1 = maper.MapData[start[0]][start[1]]['pass']
    valid2 = maper.MapData[end[0]][end[1]]['pass']
    StratCount = maper.MapData[start[0]][start[1]]['count']
    EndCount = maper.MapData[end[0]][end[1]]['count']
    path = maper.Astar(start,end)

    if valid1 != True or valid2 != True:
        return False
    
    elif type == 'camp':
        return False
    
    elif Player == 'red' and maper.MapData[start[0]][start[1]]['count']<=0:
        return False
    elif Player == 'black' and maper.MapData[start[0]][start[1]]['count']>=0:
        return False
    
    elif len(path)-1 > DiceCount:
            return False
    
    elif maper.MapData[end[0]][end[1]]['type'] == 'camp':#营地升级
        EndCount = StratCount + EndCount
        maper.MapData[end[0]][end[1]]['count'] = EndCount
        maper.MapData[start[0]][start[1]]['count'] = 0
        maper.MapData[start[0]][start[1]]['type'] = ''
        if EndCount == 0:#营地死亡判断
            maper.MapData[end[0]][end[1]]['type'] = ''
        return True

    else:
        EndCount = StratCount + EndCount
        maper.MapData[end[0]][end[1]]['count'] = EndCount
        maper.MapData[end[0]][end[1]]['type'] = 'soldier'
        maper.MapData[start[0]][start[1]]['count'] = 0
        maper.MapData[start[0]][start[1]]['type'] = ''
        if EndCount == 0:#战士死亡判断
            maper.MapData[end[0]][end[1]]['type'] = ''
        DiceCount = DiceCount+1-len(path)
        return True
        
def CreatCamp(Player,pos,DiceCount):
    #1.判断点数是否为6
    #2.判断选中是否pass不为true
    #3.判断周围邻居是否不存在己方soldier
    #4.判断所选位置是否存在点数

    TargetCount = maper.MapData[pos[0]][pos[1]]['count']
    valid = maper.MapData[pos[0]][pos[1]]['pass']
    PosNeighbors = [
    [pos[0],pos[1]-1],#left
    [pos[0],pos[1]+1],#right
    [pos[0]+1,pos[1]],#up
    [pos[0]-1,pos[1]] #down
    ]
    InRuleNeibors = []#合法邻居列表
    num = 0#周围的己方soldier数

    if DiceCount != 6:
        return False
    
    elif valid != True:
        return False
    
    for TestPoint in PosNeighbors:
        # 合法条件：1. 不越界 2. 可通行
        if 0 <= TestPoint[0] < maper.length and 0 <= TestPoint[1] < maper.width:  # 不越界
            if maper.MapData[TestPoint[0]][TestPoint[1]]['pass'] == True:  # 可通行
                    InRuleNeibors.append(TestPoint)
    for i in InRuleNeibors:
        if maper.MapData[i[0]][i[1]]['type'] == 'soldier':
            if Player == 'red' and maper.MapData[i[0]][i[1]]['count'] > 0 or Player == 'black' and maper.MapData[i[0]][i[1]]['count'] < 0:
                num = num + 1
    if num == 0:
        return False
    
    if TargetCount != 0:
        return False
    
    if Player == 'red':
        maper.AddUnit(1,'camp',pos)
        return True
    elif Player == 'black':
        maper.AddUnit(-1,'camp',pos)
        return True

#计算双方营地和士兵数
def CountCampSoldier():
    global RedCampNum
    global BlackCampNum
    global RedSoldierNum
    global BlackSoldierNum
    RedCampNum = 0
    BlackCampNum = 0
    RedSoldierNum = 0
    BlackSoldierNum = 0
    for i in maper.MapData:
        for j in i:
            if j['count']>0 and j['type'] == 'camp':
                RedCampNum = RedCampNum + 1
            elif j['count']<0 and j['type'] == 'camp':
                BlackCampNum = BlackCampNum + 1
            elif j['count']>0 and j['type'] == 'soldier':
                RedSoldierNum = RedSoldierNum + 1
            elif j['count']<0 and j['type'] == 'soldier':
                BlackSoldierNum = BlackSoldierNum + 1
    return True


def print_map_simple(map_data):
    # 打印列索引（顶部表头）
    print("    " + " ".join([f"{col:^6}" for col in range(len(map_data[0]))]))
    print("    " + "-" * (6 * len(map_data[0]) - 1))  # 分隔线
    
    # 遍历每一行（行索引 i，行数据 row）
    for i, row in enumerate(map_data):
        row_str = [f"{i:2} |"]  # 行索引前缀
        # 遍历该行的每个坐标点
        for cell in row:
            count = cell['count']
            type_ = cell['type']
            # 只显示关键信息：有类型/非0count则展示，否则显示空
            if type_ or count != 0:
                # 格式化显示：类型(计数)，居中对齐6个字符
                cell_str = f"{type_}({count})".center(6)
            else:
                cell_str = "      "  # 空位置（6个空格）
            row_str.append(cell_str)
        # 打印当前行
        print("".join(row_str))


def RedTrun(tokens):
    global DiceCount,ChooseList,LoopLock
    UserCommand = tokens
    if UserCommand[0] == 'create_soldier' and 'create_soldier' in ChooseList:
            pos = ast.literal_eval(UserCommand[1])
            try:
                judge = CreatSoldier('red',pos,DiceCount)
            except:judge = False
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染

    elif UserCommand[0] == 'move_soldier' and 'move_soldier' in ChooseList:
            pos1 = ast.literal_eval(UserCommand[1])
            pos2 = ast.literal_eval(UserCommand[2])
            try:
                judge = MoveSoldier('red',pos1,pos2,DiceCount)
            except:judge = False
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染

    elif UserCommand[0] == 'create_camp' and 'create_camp' in ChooseList:
            pos = ast.literal_eval(UserCommand[1])
            try:
                judge = CreatCamp('red',pos,DiceCount)
            except:judge = False
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染

def BlackTrun(tokens):
    global DiceCount,ChooseList,LoopLock
    UserCommand = tokens
    if UserCommand[0] == 'create_soldier' and 'create_soldier' in ChooseList:
            pos = ast.literal_eval(UserCommand[1])
            try:
                judge = CreatSoldier('black',pos,DiceCount)
            except:judge = False
            print_map_simple(maper.MapData)
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染

    elif UserCommand[0] == 'move_soldier' and 'move_soldier' in ChooseList:
            pos1 = ast.literal_eval(UserCommand[1])
            pos2 = ast.literal_eval(UserCommand[2])
            try:
                judge = MoveSoldier('black',pos1,pos2,DiceCount)
            except:judge = False
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染

    elif UserCommand[0] == 'create_camp' and 'create_camp' in ChooseList:
            pos = ast.literal_eval(UserCommand[1])
            try:
                judge = CreatCamp('black',pos,DiceCount)
            except:judge = False
            if judge == True:
                LoopLock = False
            print_map_simple(maper.MapData)
            render_board(maper.MapData)  # 新增：执行指令后渲染


'''bot1_base_url = input('bot1 base_url:')
bot2_base_url = input('bot2 base_url:')
bot1_api_key = input('bot1 api_key:')
bot2_api_key = input('bot2 api_key:')
bot1_model_name = input('bot1 model_name:')
bot2_model_name = input('bot2 model_name:')'''

bot1 = create_bot('6c6ca4d4-7909-44a2-a944-02607f1e1563','https://ark.cn-beijing.volces.com/api/v3','doubao-seed-2-0-pro-260215')
bot2 = create_bot('6c6ca4d4-7909-44a2-a944-02607f1e1563','https://ark.cn-beijing.volces.com/api/v3','doubao-seed-1-6-lite-251015')
print_map_simple(maper.MapData)
render_board(maper.MapData)  # 新增：初始渲染棋盘


def main():
    global LoopLock,MainLoopLock,ChooseList,DiceCount,RedCampNum,RedSoldierNum,BlackCampNum,BlackSoldierNum,mistake_times
    print('=====red=====')
    DiceCount = dice()
    mistake_times = 0
    print(f'\nDiceCount = {DiceCount}')
    #1.dicecount = 0-5 and RedSoldierNum != 0:生成或移动战士棋
    #2.dicecount = 6 and RedSoldierNum != 0:生成或移动战士棋或生成营地
    #1.创建战士棋2.移动战士棋3.创建营地
    CountCampSoldier()#各单位数量统计
    if DiceCount == 6 and RedSoldierNum != 0 :
        ChooseList = ['create_soldier','move_soldier','create_camp']
    elif DiceCount == 6 and RedSoldierNum == 0:
        ChooseList = ['create_soldier']
    elif DiceCount !=6 and RedSoldierNum != 0:
        ChooseList = ['create_soldier','move_soldier']
    elif DiceCount !=6 and RedSoldierNum == 0:
        ChooseList = ['create_soldier']
    promot = f"当前合法指令{ChooseList}"
    print(promot)
    LoopLock = True
    while LoopLock:
        AIpromot = f'{promot}\n{str(maper.MapData)} '
        try:
            command = bot1.ask_questions(f'你当前是红队，你这一轮摇到的点数是{DiceCount}\n{AIpromot}')
        except Exception as e:
            print(f"AI调用失败:{e}\n程序已经自动终止")
            sys.exit()
        print(command)
        tokens = command.strip().split()
        try:
            RedTrun(tokens)
        except Exception as e:
            print(f'执行失败:{e}')
            mistake_times = mistake_times+1
            if mistake_times == 4:
                LoopLock = False
                RedCampNum = 0
            pass
    print_map_simple(maper.MapData)
    render_board(maper.MapData)
    #胜负判断
    CountCampSoldier()#各单位数量统计
    if(RedCampNum == 0):
        print('Black win')
        MainLoopLock = False
    elif(BlackCampNum == 0):
        print('Red win')
        MainLoopLock = False

    print('=====black=====')
    DiceCount = dice()
    print(f'\nDiceCount = {DiceCount}')
    #1.dicecount = 0-5 and RedSoldierNum != 0:生成或移动战士棋
    #2.dicecount = 6 and RedSoldierNum != 0:生成或移动战士棋或生成营地
    #1.创建战士棋2.移动战士棋3.创建营地
    CountCampSoldier()#各单位数量统计
    if DiceCount == 6 and BlackSoldierNum != 0 :
        ChooseList = ['create_soldier','move_soldier','create_camp']
    elif DiceCount == 6 and BlackSoldierNum == 0:
        ChooseList = ['create_soldier']
    elif DiceCount !=6 and BlackSoldierNum != 0:
        ChooseList = ['create_soldier','move_soldier']
    elif DiceCount !=6 and BlackSoldierNum == 0:
        ChooseList = ['create_soldier']
    promot = f"当前合法指令{ChooseList}"
    print(promot)
    LoopLock = True
    while LoopLock:
        AIpromot = f'{promot}\n{str(maper.MapData)} '
        try:
            command = bot2.ask_questions(f'你当前是黑队，你这一轮摇到的点数是{DiceCount}\n{AIpromot}')
        except Exception as e:
            print(f"AI调用失败:{e}\n程序已经自动终止")
            sys.exit()
        print(command)
        tokens = command.strip().split()
        try:
            BlackTrun(tokens)
        except Exception as e:
            print(f'执行失败:{e}')
            mistake_times = mistake_times+1
            if mistake_times == 4:
                LoopLock = False
                BlackSoldierNum = 0
            pass
    print_map_simple(maper.MapData)
    render_board(maper.MapData)
    #胜负判断
    CountCampSoldier()#各单位数量统计
    if(RedCampNum == 0):
        print('Black win')
        MainLoopLock = False
    elif(BlackCampNum == 0):
        print('Red win')
        MainLoopLock = False


if __name__ == "__main__":
    while MainLoopLock:
        main()