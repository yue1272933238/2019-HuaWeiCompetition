
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 11 09:41:00 2019

@author: 曹悦
"""
import sys
global totalTimePieces

def readFiles(car_path, road_path, cross_path):
    roads={}
    cars={}
    crosses={}
    
    f = open(road_path)
    line=f.readline()
    line=f.readline()
    while line:
        line=line.strip()
        line=line[1:len(line)-1].replace(' ', '')
        item=line.split(',')
        roads[int(item[0])]=[]
        for i in range(1, len(item)):
            roads[int(item[0])].append(int(item[i]))
        line=f.readline()
    f.close()
    
    f=open(car_path)
    line=f.readline()
    line=f.readline()
    while line:
        line=line.strip()
        line=line[1:len(line)-1].replace(' ', '')
        item=line.split(',')
        cars[int(item[0])]=[]
        for i in range(1, len(item)):
            cars[int(item[0])].append(int(item[i]))
        line=f.readline()
    f.close()
    
    f=open(cross_path)
    line=f.readline()
    line=f.readline()
    while line:
        line=line.strip()
        line=line[1:len(line)-1].replace(' ', '')
        item=line.split(',')
        crosses[int(item[0])]=[]
        for i in range(1, len(item)):
            crosses[int(item[0])].append(int(item[i]))
        line=f.readline()
    f.close()
    
    return cars, roads, crosses


#初始化整个环境
def init(crosses, roads, cars):
    
    #根据每辆车的始发地将他们放入到神奇车库中
    garage={}
    for x in crosses.keys():
        garage[x]=[]
    for x in cars.keys():
        garage[cars[x][0]].append(x)
    for x in garage.keys(): #将神奇车库里的车按照车号递增进行排序
        garage[x].sort()
    
    #建立地图
    Map={}
    for x in crosses.keys():
        Map[x]={}
    for (k,v) in roads.items():    
        Map[v[3]][v[4]]=[v[0], k]
        if v[5]:
            Map[v[4]][v[3]]=[v[0], k]
    
    
    #计算每个节点到其他节点的最短距离
    dist=[[float('inf') for i in range(len(crosses)+1)] for i in range(len(crosses)+1)]
    for i in range(1, len(crosses)+1):
        dist[i][i]=0
    for x in crosses.keys():
        for y in Map[x].keys():
            dist[x][y]=Map[x][y][0]
    for k in range(1, len(crosses)+1):
        for i in range(1, len(crosses)+1):
            for j in range(1, len(crosses)+1):
                dist[i][j]=min(dist[i][j], dist[i][k]+dist[k][j])
    
    
    #路况信息。以cross为调度关键，所有朝着cross[i]行进的马路，维护n个队列，每个队列代表一个车道
    transport={}
    for x in crosses.keys():
        transport[x]={}
        
    for x in roads.keys():
        start=roads[x][3]
        end=roads[x][4]
        numChannels=roads[x][2]
        isDuplex=roads[x][-1]
        
        transport[end][start]=[[] for i in range(numChannels)]
        transport[end][start].append(x)
        
        if isDuplex:
            transport[start][end]=[[] for i in range(numChannels)]
            transport[start][end].append(x)
            
    return garage, Map, dist, transport


#判断每辆车的转向
def turningOfCar(cur_car, cur_cross,  cur_road, crosses, cars, Map, dist):
    
    if cars[cur_car][1]==cur_cross: #cur_car当前朝向的路口就是它的终点
        return 0, -1, -1
    
    next_cross=-1
    distant=float('inf')
    for x in Map[cur_cross].keys():
        if Map[cur_cross][x][-1]==cur_road:  #来时的马路
            continue
        if Map[cur_cross][x][0]+dist[x][cars[cur_car][1]]<=distant:
            distant=Map[cur_cross][x][0]+dist[x][cars[cur_car][1]]
            next_cross=x
            
    next_road=Map[cur_cross][next_cross][-1]
        
    index1=crosses[cur_cross].index(cur_road)
    index2=crosses[cur_cross].index(next_road)
                
    if (index1-index2)%2==0:  #直行
        return 0, next_cross, next_road
    elif (index1-index2==-1) or (index1==3 and index2==0): #左转
        return -1, next_cross, next_road
    else:  #右转
        return 1, next_cross, next_road


#当前马路上要过路口并且优先级最高的车
def highestPriorCar(transport, cur_cross, pre_cross, cur_road, carSchedule):
    channelId=-1
    position=-1 #用这个变量来记录过马路并且优先级最高的车的位置
    temp=float('inf')
    
    for i in range( len(transport[cur_cross][pre_cross]) -1 ): #每条车道
        for j in range( len(transport[cur_cross][pre_cross][i]) ): #每一辆车
            car_id=transport[cur_cross][pre_cross][i][j] #第i个车道第j辆车的车号
            #当前这个车不过马路并且还没有被处理或者已经处理了，那么它后续的所有车也就不可能出路口了，直接退出当前的车道
            if carSchedule[car_id][-1]==0 or carSchedule[car_id][-1]==2:
                break        
            else:  
                #当前这个车会可能会过马路并且在更前排的位置，那么它后面的车就算也会过马路，但是优先级不会有它高，所以也退出当前车道
                if carSchedule[car_id][2]<temp:
                    channelId=i
                    position=j
                    temp=carSchedule[car_id][2]
                    break
                else:
                    break
                
    return channelId, position

#在调度之前，我们先要明确车辆会不会过路口，如果会过路口就先不处理，把它标成过路口等待处理状态1.

#如果车辆不过路口的话，就看它能不能前进，如果它即将要到达的地方没有别的车的阻碍，那就直接开过去，把它标成已经处理过的状态2.
#如果已经有车的阻碍，并且阻碍它的车已经是被处理过的了，那么就跟到那辆车屁股后面，把车的状态标记成2，
#如果阻碍它的车还没有被处理，就把这辆车标为不过路口并且等待处理状态0。
def carsInsideRoad(transport, carSchedule, roads, crosses, cars, Map, dist):
    crossIdSorted=list(transport.keys())
    crossIdSorted.sort()
    for cur_cross in crossIdSorted:#对每个路口都要处理
        for pre_cross in transport[cur_cross].keys(): #每个路口的四条马路
            cur_road=transport[cur_cross][pre_cross][-1] #当前的马路号
            for i in range(  len(transport[cur_cross][pre_cross])-1 ): #当前马路的每个车道的号码
                for j in range( len(transport[cur_cross][pre_cross][i]) ): #当前车道上的每一辆车
                    
                    cur_car=transport[cur_cross][pre_cross][i][j]
                    v1=min(roads[cur_road][1], cars[cur_car][2])
                    s1=carSchedule[cur_car][2] #这辆车距离路口的距离

                    #算一下当前这个车的S1，并判断这个车有没有可能会不会过路口，会过路口的话，就先不处理，标志为1
                    #不会过路口话就看这个车能不能往前开，可能被标志为2，也可能被标志为0两种情况              
                    #transport[cur_cross][pre_cross][channel][i-1]表示当前车的前一辆车，但是如果这辆车是本车道第一辆车的话，这个变量是不能成立的
                    if s1<v1: #这辆车可能会过路口（也包括到达终点的情况）
                        if j==0 or carSchedule[ transport[cur_cross][pre_cross][i][j-1] ][-1]!=2:
                            carSchedule[cur_car][-1]=1
                        else:
                            carSchedule[cur_car][2]=carSchedule[ transport[cur_cross][pre_cross][i][j-1] ][2]+1
                            carSchedule[cur_car][-1]=2
                    else: #这辆车绝对不会过路口
                        #这辆车不会被妨碍，直接开到它该去的地方
                        if j==0 or ( carSchedule[cur_car][2] - carSchedule[transport[cur_cross][pre_cross][i][j-1]][2] -1 )>=v1:
                            carSchedule[cur_car][2]=s1-v1
                            carSchedule[cur_car][-1]=2
                            
                        else:  #它的前面有车妨碍它去到该去的地方
                            x=transport[cur_cross][pre_cross][i][j-1] #前面一辆车的车号
                            if carSchedule[x][-1]==2: #这辆车前面堵着它的那辆车（前车）已经处理过了，开到前车的屁股后面去
                                carSchedule[cur_car][2]=carSchedule[x][2] + 1
                                carSchedule[cur_car][-1]=2
                            else: #堵着它的前车还没有被处理过，那么要等到堵着它的前车处理了，这辆车才能得到处理
                                carSchedule[cur_car][-1]=0


#对于那些会过马路的车辆或者是从车库刚放出来的车，我们要修改它的路口号，道路号，已经距离新路口的距离。
#我们要把它从原来的车道（车库）弹出，并且加入到新的马路车道上去。（这个代码在主函数中处理过了）

#对于那些出不了马路的车，直接修改carSchedule的信息。
def updateCarInfo(transport, cur_cross, next_cross, s, car_id, carSchedule):
    
    carSchedule[car_id][0]=next_cross
    carSchedule[car_id][1]=transport[next_cross][cur_cross][-1]
    carSchedule[car_id][2]=s
    carSchedule[car_id][3]=2


#当我们把一辆车过了马路后，与它同车道的后续车辆状态和位置可能都要跟着改变
def updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars):
    cur_road=transport[cur_cross][pre_cross][-1]
    for i in range( len(transport[cur_cross][pre_cross][channelId]) ):
        cur_car=transport[cur_cross][pre_cross][channelId][i]
        v=min(roads[cur_road][1], cars[cur_car][2])
        
        if carSchedule[cur_car][-1]==2: #已经处理过了（不出路口）、
            continue
        elif carSchedule[cur_car][-1]==1: #等待处理（有可能出路口）
            if i==0: #没有前车,等待过马路
                break
            assert carSchedule[ transport[cur_cross][pre_cross][channelId][i-1] ][-1]==2
            carSchedule[cur_car][2]=carSchedule[ transport[cur_cross][pre_cross][channelId][i-1] ][2]+1
            carSchedule[cur_car][-1]=2
        else: #不出路口，还没有被处理
            if i==0 or carSchedule[cur_car][2]-carSchedule[ transport[cur_cross][pre_cross][channelId][i-1] ][2]>v: #不会被挡
                carSchedule[cur_car][2]-=v
                carSchedule[cur_car][-1]=2
            else: #前面会被挡
                x=transport[cur_cross][pre_cross][channelId][i-1] #挡住它的车肯定是终止状态
                assert carSchedule[x][-1]==2
                carSchedule[cur_car][2]=carSchedule[x][2]+1
                carSchedule[cur_car][-1]=2


def bloakedByStraightCar(transport, cur_cross, road_id, carSchedule, crosses, cars, Map, dist):
    flag=False
    for x in transport[cur_cross].keys():
        if transport[cur_cross][x][-1]==road_id:
            flag=True
            break
    if not flag:
        return False  #不会妨碍，相应的车道不存在
    
    channelId, position=highestPriorCar(transport, cur_cross, x, road_id, carSchedule)
    if channelId==position==-1:
        return False
    if turningOfCar(transport[cur_cross][x][channelId][position], cur_cross, road_id, crosses, cars, Map, dist)[0]==0:
        return True
    return False
    

def bloakedByLeftTurningCar(transport, cur_cross, road_id, carSchedule, crosses, cars, Map, dist):
    flag=False
    for x in transport[cur_cross].keys():
        if transport[cur_cross][x][-1]==road_id:
            flag=True
            break
    if not flag:
        return False  #不会妨碍，相应的车道不存在
    
    channelId, position=highestPriorCar(transport, cur_cross, x, road_id, carSchedule)
    if channelId==position==-1:
        return False
    if turningOfCar(transport[cur_cross][x][channelId][position], cur_cross, road_id, crosses, cars, Map, dist)[0]==-1:
        return True
    return False


def canTurn(turning, cur_cross, cur_road, crosses, cars, transport, Map, dist, carSchedule):
    
    if turning==0: #如果这辆车是直行的，那么它就不会因为左拐和右拐问题被阻塞
        return True
    elif turning==-1: #如果这辆车是左转的
        index1=(crosses[cur_cross].index(cur_road)-1)%4  #crosses[cur_cross][index]代表可能阻挡cur_car的马路号
        if crosses[cur_cross][index1]==-1 or not bloakedByStraightCar(transport, cur_cross, crosses[cur_cross][index1], carSchedule, crosses, cars, Map, dist):
            return True
    else:  #这辆车是右转的
        index1=(crosses[cur_cross].index(cur_road)+1)%4 #因为 crosses[cur_cross][index1]这条马路上车辆的直行被阻塞
        index2=(crosses[cur_cross].index(cur_road)-2)%4 #因为 crosses[cur_cross][index2]这条马路上车辆的左拐被阻塞
        if (crosses[cur_cross][index1]==-1 or not bloakedByStraightCar(transport, cur_cross, crosses[cur_cross][index1], carSchedule, crosses, cars, Map, dist)) \
        and (crosses[cur_cross][index2]==-1 or not bloakedByLeftTurningCar(transport, cur_cross, crosses[cur_cross][index2], carSchedule, crosses, cars, Map, dist)):
            return True
    
    return False
    
    
#处理每条马路上可能会过路口的车，也就是状态为1的车辆
def carsAcrossRoad(transport, carSchedule, roads, cars, crosses, Map, dist, carRoute, T):  #处理每条马路上可能会过路口的车，也就是状态为1的车辆
    crossIdSorted=list(transport.keys())
    crossIdSorted.sort()
    for cur_cross in crossIdSorted:  #每个路口
        item=[]
        for x in transport[cur_cross].keys():
            item.append([x, transport[cur_cross][x][-1]])
        item=sorted(item, key=lambda x:x[1])
        
        for pre_cross, cur_road in item: #当前路口的每一条马路
            flag=True #flag代表当前这条马路上要出路口的车还有没有调度的必要
            while flag:
                #当前这个马路上有很多车道和很多的车，我们要找到过马路并且优先级最高的车，也就是 priorCar的位置
                channelId, position=highestPriorCar(transport, cur_cross, pre_cross, cur_road, carSchedule)
                if channelId==-1 and position==-1: #直接跳过这条马路
                    flag=False
                    break
                
                assert position==0
                pirorCar=transport[cur_cross][pre_cross][channelId][position]
                turning, next_cross, next_road=turningOfCar(pirorCar, cur_cross,  cur_road, crosses, cars, Map, dist)
                if not canTurn(turning, cur_cross, cur_road, crosses, cars, transport, Map, dist, carSchedule): #这辆车会因为其他马路上的车要过马路而被堵塞
                    flag=False
                    break
                
                if cars[pirorCar][1]==cur_cross:  #这辆车到达了终点
                    transport[cur_cross][pre_cross][channelId].pop(0)
                    updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars)
                    #del carSchedule[pirorCar]
                    global totalTimePieces
                    totalTimePieces+=(T-cars[pirorCar][-1])
                    continue
                    
                v2=min(roads[next_road][1], cars[pirorCar][2])
                s2=v2-carSchedule[pirorCar][2]
                if s2<=0:  #把它开到马路前面并且更新后续车辆
                    carSchedule[pirorCar][2]=0
                    carSchedule[pirorCar][-1]=2
                    updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars)
                    continue
                                    
                next_road_length=roads[next_road][0]
                for i in range( roads[next_road][2] ): #看下一条马路的每个车道能不能把pirorCar塞得下
                    #这条车道是空的，或者说这条车道的最后一辆车不会阻碍pirorCar，那么这辆车直接开过去它该去的地方，并且置为终结状态
                    if not transport[next_cross][cur_cross][i] or carSchedule[ transport[next_cross][cur_cross][i][-1] ][2] < next_road_length-s2:
                        new_s=next_road_length-s2
                        updateCarInfo(transport, cur_cross, next_cross, new_s, pirorCar, carSchedule)
                        transport[cur_cross][pre_cross][channelId].pop(0)
                        transport[next_cross][cur_cross][i].append(pirorCar)
                        carRoute[pirorCar].append(next_cross)
                        updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars)
                        break
                    else:
                        if carSchedule[ transport[next_cross][cur_cross][i][-1] ][-1]==2: #挡住pirorCar的车已经是终结状态了
                            if carSchedule[ transport[next_cross][cur_cross][i][-1] ][2]<next_road_length-1: #这条车道还塞得下pirorCar
                                new_s=carSchedule[ transport[next_cross][cur_cross][i][-1] ][2] + 1
                                updateCarInfo(transport, cur_cross, next_cross, new_s, pirorCar, carSchedule)
                                transport[cur_cross][pre_cross][channelId].pop(0)
                                transport[next_cross][cur_cross][i].append(pirorCar)
                                carRoute[pirorCar].append(next_cross)
                                updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars)
                                break
                            else:
                                if i==roads[next_road][2]-1: #直到最后一个车道都塞不下pirorCar，那就把这辆车开到原来那条马路的最前面
                                    carSchedule[pirorCar][2]=0
                                    carSchedule[pirorCar][-1]=2
                                    updateFollowingCars(transport, cur_cross, pre_cross, channelId, carSchedule, roads, cars)
                                    break
                                else:
                                    continue
                        else: #挡住它的车不是终结状态，还未处理，那么这辆车也不能进行任何处理，停在原地，并且整条马路都不会再进行任何处理
                            flag=False
                            break

#统计马路上的车辆数目
def NumOfCarsOnRoad(transport):
    cnt=0
    for cur_cross in transport.keys():
        for pre_cross in transport[cur_cross].keys(): #每个路口的四条马路
            for i in range(  len(transport[cur_cross][pre_cross][:-1]) ): #当前马路的每个车道的号码
                cnt+=len(transport[cur_cross][pre_cross][i])
    return cnt

#处理完所有马路上的车后，现在看看车库里的车能不能给放出来(车的出发时间要小于等于T)
def carsInGarage(transport, garage, dist, Map, carSchedule, T, cars, roads, carRoute):
    topLimit=1000-NumOfCarsOnRoad(transport) #这次放车最多能放多少辆车(可能现在所以车库里的车辆还达不到这个数)
    cnt=0
    
    crossIdSorted=list(transport.keys())
    crossIdSorted.sort()
    for cur_cross in crossIdSorted:    
        carStay=[]
        while garage[cur_cross] and cnt<topLimit:
            #对于每个路口的神奇车库里的每一辆车，先判断它的下一朝向路口，也就是确定它往哪里走
            waiting_car=garage[cur_cross].pop(0)
            if cars[waiting_car][-1]>T: #还没有到出发时间
                carStay.append(waiting_car)
                continue
               
            temp=float('inf')
            heading_cross=-1
            for x in Map[cur_cross]: #对于这辆车能够开向的每一个路口
                if dist[x][ cars[waiting_car][1] ] + Map[cur_cross][x][0]<temp:
                    temp  = dist[x][ cars[waiting_car][1] ] + Map[cur_cross][x][0]
                    heading_cross=x
                    
            heading_road=transport[heading_cross][cur_cross][-1]
            v=min(roads[heading_road][1], cars[waiting_car][2])
            for i in range( roads[heading_road][2] ):
                cur_channel_L=transport[heading_cross][cur_cross][i][:]  #cur_channel_L表示对应马路上某一条车道上的全部车辆列表
                #这条车道是空的，或者最后一辆车不会阻碍waiting_car，那么直接把waiting_car开到它该去的地方
                if not cur_channel_L or (carSchedule[cur_channel_L[-1]][2] < (roads[heading_road][0]-v)):
                    carRoute[waiting_car]+=[T, cur_cross, heading_cross]
                    transport[heading_cross][cur_cross][i].append(waiting_car)
                    new_s=roads[heading_road][0]-v
                    updateCarInfo(transport, cur_cross, heading_cross, new_s, waiting_car, carSchedule)
                    cnt+=1
                    #print (waiting_car)
                    break
                else:
                    if carSchedule[cur_channel_L[-1]][2]<roads[heading_road][0]-1: #这条车道还没满
                        carRoute[waiting_car]+=[T, cur_cross, heading_cross]
                        transport[heading_cross][cur_cross][i].append(waiting_car)
                        new_s=carSchedule[cur_channel_L[-1]][2]+1
                        updateCarInfo(transport, cur_cross, heading_cross, new_s, waiting_car, carSchedule)
                        cnt+=1
                        #print (waiting_car)
                        break    
                    else:
                        if i==roads[heading_road][2]-1: #直到最后一条车道都满了,waiting_car以为道路堵塞而不能发车
                            carStay.append(waiting_car)
                            break
                        else:
                            continue
        garage[cur_cross]+=carStay
        garage[cur_cross].sort()
        
        if cnt==topLimit:
            return
        
#是否调度完成了。如果现在车库里和路上都没有车了，说明调度完成了
def ScheduleFinished(garage, transport):
    cnt=0
    for x in garage.keys():
        cnt+=len(garage[x])
    for cur_cross in transport.keys():
        for pre_cross in transport[cur_cross].keys():
            for channel in transport[cur_cross][pre_cross][:-1]:
                cnt+=len(channel)
                
    if cnt==0:
        return True
    return False

def carsNotFinishedState(transport, carSchedule):
    for cur_cross in transport.keys():#对每个路口都要处理
        for pre_cross in transport[cur_cross].keys(): #每个路口的四条马路
            for i in range(  len(transport[cur_cross][pre_cross][:-1]) ): #当前马路的每个车道的号码
                for j in range( len(transport[cur_cross][pre_cross][i]) ): #当前车道上的每一辆车
                    cur_car=transport[cur_cross][pre_cross][i][j]
                    if carSchedule[cur_car][-1]!=2:
                        return True
    return False
    

def printCars(transport, carSchedule):
    for cur_cross in transport.keys():
        for pre_cross in transport[cur_cross].keys(): #每个路口的四条马路
            for i in range(  len(transport[cur_cross][pre_cross][:-1]) ): #当前马路的每个车道的号码
                for j in range( len(transport[cur_cross][pre_cross][i]) ): #当前车道上的每一辆车
                    cur_car=transport[cur_cross][pre_cross][i][j]
                    s1=carSchedule[cur_car][2]
                    
                    print ("cur_cross: "+str(cur_cross)+ " pre_cross:"+str(pre_cross)+ ' car_id:'+str(cur_car)+ ' 距离路口距离:'+str(s1) \
                           +' 状态'+str(carSchedule[cur_car][-1]))
    print ('\n')


def writeFile(carRoute, answer_path, Map):
    f=open(answer_path, 'w')
    temp=list(carRoute.keys())
    for i in range(len(temp)):
         #carRoute[x]代表车号为x这辆车的路线
        x=temp[i]
        length=len(carRoute[x])
        f.write('('+str(x)+', '+ str(carRoute[x][0])+', ')
        for j in range(1, length-2):
            road_id=Map[ carRoute[x][j] ][ carRoute[x][j+1] ][-1]
            f.write(str(road_id)+', ')
            
        road_id= Map[ carRoute[x][length-2] ][ carRoute[x][length-1] ][-1]
        f.write(str( road_id ))
        f.write(')')
        
        if i!=len(temp)-1:
            f.write('\n')
    
def main():
    # to read input file
    # process
    # to write output file
    if len(sys.argv) != 5:
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    cars, roads, crosses=readFiles(car_path, road_path, cross_path)
    carSchedule={}
    for x in cars.keys():
        carSchedule[x]=[-1, -1, -1, -1]
    
    carRoute={}
    for x in cars.keys():
        carRoute[x]=[]
        
    garage, Map, dist, transport=init(crosses, roads, cars)
    T=float('inf')
    for x in cars.keys():
        if cars[x][-1]<T:
            T=cars[x][-1]
    
    T-=1
    global totalTimePieces
    totalTimePieces=0
    while not ScheduleFinished(garage, transport):
        #新的一个时间片调度开始了，所有的车辆状态置为-1
        T+=1     
        for x in carSchedule.keys():
            carSchedule[x][-1]=-1
            
        carsInsideRoad(transport, carSchedule, roads, crosses, cars, Map, dist)
        while carsNotFinishedState(transport, carSchedule):
            carsAcrossRoad(transport, carSchedule, roads, cars, crosses, Map, dist, carRoute, T)
        #第T个时间片，看看每个路口有没有车能够上路(出发时间大于T的车辆一定不能上路，小于等于T的车辆有可能上路)
        carsInGarage(transport, garage, dist, Map, carSchedule, T, cars, roads, carRoute)

    print ('ScheduleFinished')
    print (T)
    print (totalTimePieces)
    writeFile(carRoute, answer_path, Map)

if __name__ == "__main__":
    main()