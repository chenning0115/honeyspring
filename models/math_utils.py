import os
import sys
import bs4
import logging
import datetime as dt
import json
import re
import random
import math
import numpy as np

def cal_euler_distance(a, b):
    arr_a = np.asarray(a)
    arr_b = np.asarray(b)
    return np.sum((arr_a - arr_b) ** 2)
    
def cal_euler_distance_by_matrix(data):
    data = np.asarray(data)
    res = []
    row, col = data.shape
    for i in range(row):
        row_data = data[i]
        row_p2 = (row_data - data) ** 2
        row_dis2 = np.sum(row_p2, axis= 1)
        res.append(row_dis2)
        print('cal euler dis %s/%s done!' % (i ,row))
    ndres = np.asarray(res)
    # print(ndres[0,1])
    return ndres.tolist()
        
    

if __name__ == "__main__":
    data = np.asarray([[1,2,3],[4,5,6]])
    print(cal_euler_distance_by_matrix(data))