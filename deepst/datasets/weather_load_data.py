# -*- coding: utf-8 -*-
from __future__ import print_function
import os
import pickle
import numpy as np

from deepst.datasets import load_stdata
from ..preprocessing import MinMaxNormalization
from ..preprocessing import remove_incomplete_days
from ..config import Config
from ..datasets.STMatrix import STMatrix
from ..preprocessing import timestamp2vec

np.random.seed(1337)  # for reproducibility

# parameters
DATAPATH = Config().DATAPATH


def divide_test_train(XC,XP,XT,Y,len_test):
    XC_train = XC[:len(XC)-len_test]
    XC_test =  XC[len(XC)-len_test:]
    XP_train = XP[:len(XP)-len_test]
    XP_test =  XP[len(XP)-len_test:]
    XT_train = XT[:len(XT)-len_test]
    XT_test =  XT[len(XT)-len_test:]
    Y_train = Y[:len(Y)-len_test]
    Y_test =  Y[len(Y)-len_test:]
    return XC_train,XC_test,XP_train,XP_test,XT_train,XT_test,Y_train,Y_test
def create_dataset_weather(data_all,len_closeness, len_period, len_trend,len_test):
    data_len = len(data_all)
    offset = len_closeness + len_period + len_trend
    XC = []
    XP = []
    XT = []
    Y = []
    for i in range(offset,data_len):
        _XC = data_all[i-len_closeness:i]
        _XP = data_all[i-len_closeness-len_period:i-len_closeness]
        _XT = data_all[i-len_closeness-len_period-len_trend:i-len_closeness-len_period]
        XC.append(_XC)
        XP.append(_XP)
        XT.append(_XT)
        Y.append(np.array([data_all[i]]))

    XC=np.asarray(XC)
    XP = np.asarray(XP)
    XT = np.asarray(XT)
    Y = np.asarray(Y)
    XC_train, XC_test, XP_train, XP_test, XT_train, XT_test, Y_train, Y_test = divide_test_train(XC,XP,XT,Y,len_test)
    X_train = []
    X_test = []
    for l, X_ in zip([len_closeness, len_period, len_trend], [XC_train, XP_train, XT_train]):
        if l > 0:
            X_train.append(X_)
    for l, X_ in zip([len_closeness, len_period, len_trend], [XC_test, XP_test, XT_test]):
        if l > 0:
            X_test.append(X_)

    print("dbgjason")
    print(X_train[0].shape)
    print(X_train[1].shape)
    print(X_train[2].shape)

    return X_train, X_test, Y_train, Y_test

#used
def load_data_weather(T=24, nb_flow=1, len_closeness=None, len_period=None, len_trend=None, len_test=None,
              preprocess_name='preprocessing.pkl', meta_data=True,external_dim=8):
    assert (len_closeness + len_period + len_trend > 0)

    data = pickle.load(open('train_features.pkl'))
    data_all = []
    for dt in data:
        data_all.append(dt.squeeze())
    data_all = np.asarray(data_all)
    X_train, X_test, Y_train, Y_test = create_dataset_weather(data_all,len_closeness,len_period,len_trend,len_test)
    if meta_data==False:
        metadata_dim = None
    else:
        metadata_dim = external_dim
    return X_train, Y_train, X_test, Y_test,  metadata_dim



#dummy
def load_data(T=24, nb_flow=2, len_closeness=None, len_period=None, len_trend=None, len_test=None,
              preprocess_name='preprocessing.pkl', meta_data=True):
    assert (len_closeness + len_period + len_trend > 0)
    # load data
    data, timestamps = load_stdata(os.path.join(DATAPATH, 'BikeNYC', 'NYC14_M16x8_T60_NewEnd.h5'))
    # print(timestamps)
    # remove a certain day which does not have 48 timestamps
    data, timestamps = remove_incomplete_days(data, timestamps, T)
    data = data[:, :nb_flow]
    data[data < 0] = 0.
    data_all = [data]
    timestamps_all = [timestamps]
    # minmax_scale
    data_train = data[:-len_test]
    print('train_data shape: ', data_train.shape)
    mmn = MinMaxNormalization()
    mmn.fit(data_train)
    data_all_mmn = []
    for d in data_all:
        data_all_mmn.append(mmn.transform(d))

    fpkl = open('preprocessing.pkl', 'wb')
    for obj in [mmn]:
        pickle.dump(obj, fpkl)
    fpkl.close()

    XC, XP, XT = [], [], []
    Y = []
    timestamps_Y = []
    for data, timestamps in zip(data_all_mmn, timestamps_all):
        # instance-based dataset --> sequences with format as (X, Y) where X is a sequence of images and Y is an image.
        st = STMatrix(data, timestamps, T, CheckComplete=False)
        _XC, _XP, _XT, _Y, _timestamps_Y = st.create_dataset(len_closeness=len_closeness, len_period=len_period,
                                                             len_trend=len_trend)
        XC.append(_XC)
        XP.append(_XP)
        XT.append(_XT)
        Y.append(_Y)
        timestamps_Y += _timestamps_Y

    XC = np.vstack(XC)
    XP = np.vstack(XP)
    XT = np.vstack(XT)
    Y = np.vstack(Y)
    print("XC shape: ", XC.shape, "XP shape: ", XP.shape, "XT shape: ", XT.shape, "Y shape:", Y.shape)
    XC_train, XP_train, XT_train, Y_train = XC[:-len_test], XP[:-len_test], XT[:-len_test], Y[:-len_test]
    XC_test, XP_test, XT_test, Y_test = XC[-len_test:], XP[-len_test:], XT[-len_test:], Y[-len_test:]

    timestamp_train, timestamp_test = timestamps_Y[:-len_test], timestamps_Y[-len_test:]
    X_train = []
    X_test = []
    for l, X_ in zip([len_closeness, len_period, len_trend], [XC_train, XP_train, XT_train]):
        if l > 0:
            X_train.append(X_)
    for l, X_ in zip([len_closeness, len_period, len_trend], [XC_test, XP_test, XT_test]):
        if l > 0:
            X_test.append(X_)
    print('train shape:', XC_train.shape, Y_train.shape, 'test shape: ', XC_test.shape, Y_test.shape)
    # load meta feature
    if meta_data:
        meta_feature = timestamp2vec(timestamps_Y)
        metadata_dim = meta_feature.shape[1]
        meta_feature_train, meta_feature_test = meta_feature[:-len_test], meta_feature[-len_test:]
        X_train.append(meta_feature_train)
        X_test.append(meta_feature_test)
    else:
        metadata_dim = None
    for _X in X_train:
        print(_X.shape, )
    print()
    for _X in X_test:
        print(_X.shape, )
    print()
    return X_train, Y_train, X_test, Y_test, mmn, metadata_dim, timestamp_train, timestamp_test
