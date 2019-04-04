# 2019-
该项目实现了2019华为软件精英挑战赛的初赛赛题，主要侧重的是调度器的实现。其他部分的处理还有待优化。

实验环境： ubuntu16.04 + python3.5.2

一、主要的数据结构如下：
1. cars,roads,crosses是根据输入文件创建的字典。
   cars的key是车号id，value是一个list,list中存放了这辆车的【始发地，目的地，最高速度，出发时间】。
   roads的key是马路号id，value是一个list,list中存放了这条马路的【道路长度，最高限速，车道数目，起始点id，终点id， 是否双向】。
   crosses的key是路口id，value是一个与之相连通的道路号的list。
   
2. Map是根据roads和crosses建立起来的地图信息，是一个dict。以路口号id为主键。描述的是从当前这个路口出发，可以直接抵达的下一路口id，以及相应的道路长度和道路号id。
  
3. transport代表整个交通过程中的路况信息，是一个dict，其主键key是每一个路口号。因为对每个路口遍历道路时，只调度该道路出路口的方向。所以transport
[1][2]就代表，从2号路口驶来，正朝着1号路口行驶的所有的车辆的id(分车道来存放的，一个车道用一个list表示，list中存放的就是当前车道上的车辆id)。
  
4. carSchedule代表了行进中的车辆的具体信息，是一个dict。其主键是车辆id，value是一个list，内容分别代表【该车辆当前朝着哪个路口，在那条马路上，距离路口的距离多远，车辆的状态】。根据它所朝向的路口，所在的马路，以及距离路口的位置，就能确定车辆的具体位置。车辆的状态分为3种，第一种是0，代表它不会出路口并且还没有被调度；第二种是1，代表它会出路口，但还没有被调度；第三种是2，代表车辆在当前的时间片已经调度完成了。
  
5. garage代表神奇车库，是个dict，主键是路口号，value是停在当前车库中的所有车辆，是个list，根据车辆的起始地来初始化它。dist代表每两个路口之间的最短距离，是个二维list。carRoute用于存放车辆的路径，主键是车辆id。

二、主要的函数如下：
1. carsInsideRoad是看那些不出路口的车，能走的尽量走。并且根据每辆车的s1(距离路口的距离)和v，为每辆车打标记。
2. carsAcrossRoad是对每个路口处需要过马路的所有车辆(也就是标记为1的车辆)执行过马路。我们每将一辆车过马路，就更新一下这辆车所在车道的后续车辆。
3. carsInGarage表示从车库中放车上路。主函数中在执行carsInGarage之前，所有的车辆现在的状态都是2状态了。如果还有车辆不是2状态，就说明整个路况中发生了死锁情况。在程序运行起来之后，可以每从车库中成功的放出一辆车，都会输出它的车号，如果发现输出界面卡住不动了，那就是死锁了。

整体代码的主框架如下：

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

三、其他说明:
    该代码最主要的部分就是carsInsideRoad、carsAcrossRoad、carsInGarage这三个函数。关于车辆的路径规划问题(对于每辆车判断下一次如何转向)。代码中是根据距离最短来做的，也就是turningOfCar这个函数，和从出车库放车上路时carsInGarage中如下的代码部分：
            
            temp=float('inf')
            heading_cross=-1
            for x in Map[cur_cross]: #对于这辆车能够开向的每一个路口
                if dist[x][ cars[waiting_car][1] ] + Map[cur_cross][x][0]<temp:
                    temp  = dist[x][ cars[waiting_car][1] ] + Map[cur_cross][x][0]
                    heading_cross=x        
            heading_road=transport[heading_cross][cur_cross][-1]
   
   只要根据自己规划好的路径，对于每一辆车判断好它的每次转弯。对这两个部分就行修改，就可以将自己的调度策略与调度器很好的结合和利用。
    
        
