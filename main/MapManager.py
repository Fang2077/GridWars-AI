"""
    width
_________________________
|                       |
|                       |
|                       |  length
|                       |
|_______________________|

"""
import json

class MapManager:
    def __init__(self):
        self.path_map = 'MapData.json'
        self.length = None
        self.width = None
        self.MapData = None #CreatMap以后的所有Map方法以self.MapData为准

    def upgrade(self):
        with open(self.path_map, "w", encoding="utf-8") as f:
            json.dump(
                self.MapData,
                f,
                ensure_ascii=False,
                indent=4,
                separators=(', ', ': ')
            )
        self.MapData = self.MapData
        return True


    def CreateMap(self,length,width):
        self.length = length
        self.width = width
        MapData = []
        for i in range(length):
            row = []
            for j in range(width):
                SingleDict = {'count':0,'type':'','pass':True}#[i,j]i：行，j：列
                row.append(SingleDict)
            MapData.append(row)
        with open(self.path_map, "w", encoding="utf-8") as f:
            json.dump(
                MapData,
                f,
                ensure_ascii=False,
                indent=4,
                separators=(', ', ': ')
            )
        self.MapData = MapData
        return MapData
    
    def AddUnit(self,count,type,pos):
        length = 0
        width = 0
        for query1 in self.MapData:
            for query2 in query1:
                if pos == [length,width]:
                    self.MapData[length][width]['type'] = type
                    self.MapData[length][width]['count'] = count
                    with open(self.path_map, "w", encoding="utf-8") as f:
                        json.dump(
                            self.MapData,
                            f,
                            ensure_ascii=False,
                            indent=4,
                            separators=(', ', ': ')
                        )
                    return True
                width = width + 1
                if width > self.width - 1:
                    width = 0
            length = length + 1
        
    def Astar(self,PosStart, PosEnd):
        """
        A*路径查找算法（自动推导地图行列数）
        参数：
            MapData: 二维地图数据，格式为 [[{'pass': bool}, ...], ...]（第一层行，第二层列）
            PosStart: 起点坐标 [y, x]（行，列）
            PosEnd: 终点坐标 [y, x]（行，列）
        返回：
            最短路径列表 [[y1,x1], [y2,x2], ...]，无路径返回空列表
        """
        MapData = self.MapData
        # 自动推导地图行列数（行=height，列=width）
        MapHeight = len(MapData)  # 行（height）= 二维列表第一层长度
        if MapHeight == 0:
            print("错误：地图数据为空")
            return []
        MapWidth = len(MapData[0])  # 列（width）= 二维列表第二层长度
        
        # 初始化核心数据结构
        OpenList = []  # 格式：[pos, f, g] → [ [y,x], f值, g值 ]
        CloseList = []  # 仅存储已扩展的节点坐标 [y,x]
        ParentDict = {}  # 记录父节点，用于路径回溯 → {(y,x): (父节点y, 父节点x)}
        
        # 校验起点/终点合法性
        def is_valid_pos(pos):
            """校验坐标是否合法（在地图内+可通行）"""
            y, x = pos
            if 0 <= y < MapHeight and 0 <= x < MapWidth:
                return MapData[y][x]['pass']
            return False
        
        # 起点/终点非法直接返回
        if not is_valid_pos(PosStart):
            print(f"错误：起点{PosStart}非法（越界或不可通行）")
            return []
        if not is_valid_pos(PosEnd):
            print(f"错误：终点{PosEnd}非法（越界或不可通行）")
            return []
        if PosStart == PosEnd:
            print("起点和终点重合")
            return [PosStart]
        
        # 初始化起点（g=0，h=曼哈顿距离，f=g+h）
        h_start = abs(PosStart[0]-PosEnd[0]) + abs(PosStart[1]-PosEnd[1])
        f_start = 0 + h_start
        OpenList.append([PosStart, f_start, 0])
        
        # A*主循环
        while True:
            # 终止条件1：OpenList为空（无路径）
            if not OpenList:
                print("未找到有效路径")
                return []
            
            # 1. 从OpenList中取f值最小的节点作为当前节点
            CurrentPoint = min(OpenList, key=lambda x: x[1])
            CurrentPos, CurrentF, CurrentG = CurrentPoint
            
            # 2. 终止条件2：找到终点 → 回溯路径
            if CurrentPos == PosEnd:
                path = []
                current = tuple(CurrentPos)
                # 回溯父节点直到起点
                while current in ParentDict:
                    path.append(list(current))
                    current = ParentDict[current]
                path.append(PosStart)
                path.reverse()  # 反转得到 起点→终点 顺序
                return path
            
            # 3. 将当前节点移出OpenList，加入CloseList（标记为已扩展）
            OpenList.remove(CurrentPoint)
            if CurrentPos not in CloseList:
                CloseList.append(CurrentPos)
            
            # 4. 生成当前节点的4个邻居（上下左右）
            directions = [
                [0, -1],  # left（列-1）
                [0, 1],   # right（列+1）
                [1, 0],   # up（行+1）
                [-1, 0]   # down（行-1）
            ]
            PosNeighbors = []
            for dy, dx in directions:
                ny = CurrentPos[0] + dy
                nx = CurrentPos[1] + dx
                PosNeighbors.append([ny, nx])
            
            # 5. 校验邻居合法性（不越界+可通行+未扩展）
            InRuleNeibors = []
            for TestPoint in PosNeighbors:
                if is_valid_pos(TestPoint) and TestPoint not in CloseList:
                    InRuleNeibors.append(TestPoint)
            
            # 6. 计算合法邻居的f/g值，更新OpenList
            for Htester in InRuleNeibors:
                # 邻居G值 = 当前节点G值 + 1（每步移动代价为1）
                neighbor_g = CurrentG + 1
                # 邻居H值（曼哈顿距离）
                neighbor_h = abs(Htester[0]-PosEnd[0]) + abs(Htester[1]-PosEnd[1])
                # 邻居F值
                neighbor_f = neighbor_g + neighbor_h
                
                # 检查邻居是否已在OpenList中
                is_in_open = False
                for idx, item in enumerate(OpenList):
                    if item[0] == Htester:
                        is_in_open = True
                        # 若新G值更小，更新F/G值（更优路径）
                        if neighbor_g < item[2]:
                            OpenList[idx] = [Htester, neighbor_f, neighbor_g]
                            ParentDict[tuple(Htester)] = tuple(CurrentPos)
                        break
                # 不在OpenList中 → 新增
                if not is_in_open:
                    OpenList.append([Htester, neighbor_f, neighbor_g])
                    ParentDict[tuple(Htester)] = tuple(CurrentPos)