#coding=utf-8
'''
Author = Eric_Chan
Create_Time = 2015/11/29
'''
import jieba
import numpy as np
import time
import sys
from multiprocessing import Process,Queue
jieba.initialize()
time.sleep(1)

def loadData(filename,startNum,endNum,u=0): #输入读取的文件
    t1 = time.time()
    print "开始读取数据集..."

    file1 = open(filename,'r')
    line = file1.readline()
    messageList = [] #记录短信的列表
    classVec = [] #记录短信对应的属性, 1 代表垃圾短信 0 代表普通短信
    for i in range(startNum):
        line = file1.readline()
    for i in range(endNum):
        temp = line.split('\t')
        classVec.append(int(temp[1-u]))
        messageList.append(list(jieba.cut(temp[2-u])))
        line = file1.readline()
    file1.close()

    t2 = time.time()
    print "读取完毕,花费时间:%is\n"%(t2-t1)

    return messageList,classVec

def createVocabList(messageList):#创建一个词库,包含全部训练集中的所有词语
    t1 = time.time()
    print "开始构建词库..."

    vocabSet = set([])
    for i in messageList:
        vocabSet = vocabSet | set(i)

    t2 = time.time()
    print "词库构建完毕,花费时间:%is\n"%(t2-t1)
    return list(vocabSet)

def createVecInVocabList(message,vocabList):#输入一条短信,返回该短信基于某词库的向量
    returnVec = [0] * len(vocabList)
    for word in message:
        if word in vocabList:
            returnVec[vocabList.index(word)] = 1
    return returnVec

def trainNBO(trainMatrix,trainClassVec,nSpam,p0Num,p1Num,p0Denom = 2.0 , p1Denom = 2.0): #训练贝叶斯分类器,输入 每条信息对应的向量构成的矩阵  每条信息对应是否为垃圾信息的向量
    t1 = time.time()
    print "开始训练分类器..."

    message_num = len(trainMatrix) #训练集信息的数量
    # words_num = len(trainMatrix[0])#词库的大小
    nSpam += sum(trainClassVec) #垃圾短信的概率
    # p0Num = np.ones(words_num) ; p1Num = np.ones(words_num)
    # p0Denom = 2.0 ; p1Denom = 2.0
    for i in range(message_num):
        print "    训练中...   %i%%"%(i/float(message_num)*100),
        sys.stdout.write("\r")
        if trainClassVec[i] == 0:
            p0Num += trainMatrix[i]
            p0Denom += sum(trainMatrix[i])
        else:
            p1Num += trainMatrix[i]
            p1Denom += sum(trainMatrix[i])
    # p1Vect = np.log(p1Num / p1Denom)
    # p0Vect = np.log(p0Num / p0Denom)

    t2 = time.time()
    print "该阶段训练器训练完毕,花费时间:%is\n"%(t2-t1)
    np.savetxt("P0NUM.txt",p0Num)
    np.savetxt("P1NUM.txt",p1Num)
    f = open("datasave.txt",'w')
    f.write(str(nSpam) + '\n'
            +str(p0Denom) + '\n'
            +str(p1Denom) + '\n')
    f.close()
    print "n_spam:  ",nSpam
    print "p0_denom:",p0Denom
    print "p1_denom:",p1Denom

def classifyNB(messageVec,p0Vec,p1Vec,pSpam):#输入 短信向量 普通短信的词语向量概率 垃圾短信的词语向量概率 垃圾短信出现的概率
    p0 = sum(messageVec * p0Vec) + np.log(1-pSpam)
    p1 = sum(messageVec * p1Vec) + np.log(pSpam)
    if p1 > p0:
        return 1
    else:return 0

def createMatrix(messageList,vocabList):#输入短信列表和词库 返回短信-短信向量矩阵
    t1 = time.time()
    print "开始构建向量矩阵..."

    num = len(messageList)
    n = num/3
    def Pro(N1,N2,getReturn=None,isP=False):
        returnMatrix = []
        if isP:
            for i in range(num)[N1:N2]:
                # print "    构建中...   %i%%"%(i/float(n)*100),       #?
                print "    构建中...   %i%%"%(i/float(num)*100),       #??
                sys.stdout.write("\r")
                returnMatrix.append(createVecInVocabList(messageList[i],vocabList=vocabList))
        else:
            for i in range(num)[N1:N2]:
                returnMatrix.append(createVecInVocabList(messageList[i],vocabList=vocabList))
        # getReturn.put(returnMatrix)                                 #?
        return returnMatrix
    # getReturn1 = Queue();getReturn2 = Queue();getReturn3 = Queue()  #?
    # P1 = Process(target=Pro,args=(0,n,getReturn1,True))             #?
    # P2 = Process(target=Pro,args=(n,2*n,getReturn2))                #?
    # P3 = Process(target=Pro,args=(2*n,3*n,getReturn3))              #?
    # P1.start()                                                      #?
    # P2.start()                                                      #?
    # P3.start()                                                      #?
    # matrix = getReturn1.get() + getReturn2.get() + getReturn3.get() #?
    matrix = Pro(0,num,None,True)

    t2 = time.time()
    print "矩阵构建完毕,花费时间:%is\n"%(t2-t1)
    return matrix

def getTestScore(realList,resultList):#输入原始数据和判定数据,得出评估得分
    num = len(realList)
    A = 0.
    B = 0.
    C = 0.
    D = 0.
    for i in range(num):
        if realList[i]==resultList[i]:
            if realList[i] == 0:
                A += 1
            else:
                D += 1
        else:
            if realList[i] == 0:
                C += 1
            else:
                B += 1
    print "垃圾短信准确率:",D/(B+D)
    print "垃圾短信查全率:",D/(C+D)
    print "正确短信准确率:",A/(A+C)
    print "正确短信查全率:",A/(A+B)
    print "总分:" ,0.7*(0.65*(D/(B+D))+0.35*(D/(C+D))) + 0.3*(0.65*(A/(A+C)) + 0.35*(A/(A+B)))

def writeResult(fileName,resultList):
    file1 = open(fileName,'w')
    for i in range(len(resultList)):
        xuhao = str(800000 + i + 1)
        file1.write(xuhao+','+str(resultList[i])+'\n')
    file1.close()

def startTrain(startNum,count): #输入 训练集的起点 和 训练集的个数
    "读取训练集"
    train_message,train_vec = loadData("database/80W.txt",startNum,count)

    "构建词库"
    # vocabList = createVocabList(train_message[:100000])
    # vocabList = sorted(vocabList)
    # file1 = open("VocabList.txt",'w')
    # for word in vocabList:
    #     file1.write(word.encode('utf8')+'\n')
    # file1.close()
    file1 = open("VocabList.txt",'r')
    line = file1.readline()
    vocabList = []
    while line:
        vocabList.append(line.strip().decode('utf8'))
        line = file1.readline()
    file1.close()


    "构建训练短信-向量矩阵"
    train_matrix = createMatrix(train_message,vocabList)

    "训练贝叶斯分类器"
    try:
        f = open("datasave.txt",'r')
        n_spam = int(f.readline())
        p0_denom = float(f.readline())
        p1_denom = float(f.readline())
        f.close()
        p0_num = np.loadtxt("P0NUM.txt")
        p1_num = np.loadtxt("P1NUM.txt")
    except:#进行第一次训练
        n_spam = 0
        p0_denom = 2.0
        p1_denom = 2.0
        p0_num = np.ones(len(vocabList))
        p1_num = np.ones(len(vocabList))

    trainNBO(train_matrix,train_vec,n_spam,p0_num,p1_num,p0_denom,p1_denom)
    f = open("finished.txt",'w') #保存训练进度
    f.write(str(startNum+count))
    f.close()

for i in range(150)[int(open("finished.txt",'r').readline())/5000:]:
    print "------------------------------------"
    print "开始第%i次训练,剩余%i次"%((i+1),(149-i))
    startTrain(i*5000,5000)
    time.sleep(60)












'''
"读取测试集,构建矩阵"
test_message,teemee,test_index = loadData("database/20W.txt",200000,1)   #测试集
test_matrix = createMatrix(test_message,vocabList=vocabList)

"开始对测试集进行分类"
t1 = time.time()
print "开始进行分类..."
test_result = []
for i in range(len(test_matrix)):
    print "分类中...",i
    test_result.append(classifyNB(test_matrix[i],p0_vect,p1_vect,p_spam))
t2 = time.time()
print "分类结束,花费时间:%is\n"%(t2-t1)

"将结果导出txt文本"
# getTestScore(test_vec,test_result)
writeResult("result.txt",test_result)
'''