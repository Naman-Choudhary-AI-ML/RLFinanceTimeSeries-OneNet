import os
import numpy as np
import pandas as pd
import pdb
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler as sklearn_StandardScaler

from utils.tools import StandardScaler
from utils.timefeatures import time_features

import warnings
warnings.filterwarnings('ignore')

class Dataset_ETT_hour(Dataset):
    def __init__(self, root_path, flag='train', delay_fb=False, size=None, 
                 features='S', data_path='ETTh1.csv', 
                 target='OT', scale=True, inverse=False, timeenc=0, freq='h', cols=None):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24*4*4
            self.label_len = 24*4
            self.pred_len = 24*4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train':0, 'val':1, 'test':2}
        self.set_type = type_map[flag]
        
        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq; self.delay_fb=delay_fb
        
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))

        #border1s = [0, 12*30*24 - self.seq_len, 12*30*24+4*30*24 - self.seq_len]
        #border2s = [12*30*24, 12*30*24+4*30*24, 12*30*24+8*30*24]
        border1s = [0, 4*30*24 - self.seq_len, 5*30*24 - self.seq_len]
        border2s = [4*30*24, 5*30*24, 20*30*24]
        

        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]
        
        if self.features=='M' or self.features=='MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features=='S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)

        else:
            data = df_data.values

        if self.timeenc == 2:
            train_df_stamp = df_raw[['date']][border1s[0]:border2s[0]]
            train_df_stamp['date'] = pd.to_datetime(train_df_stamp.date)
            train_date_stamp = time_features(train_df_stamp, timeenc=self.timeenc)
            date_scaler = sklearn_StandardScaler().fit(train_date_stamp)

            df_stamp = df_raw[['date']][border1:border2]
            df_stamp['date'] = pd.to_datetime(df_stamp.date)
            data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq)
            data_stamp = date_scaler.transform(data_stamp)
        else:
            df_stamp = df_raw[['date']][border1:border2]
            df_stamp['date'] = pd.to_datetime(df_stamp.date)
            data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq)

        self.data_x = data[border1:border2]
        if self.inverse:
            self.data_y = df_data.values[border1:border2]
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
        
    def __getitem__(self, index):
        if self.delay_fb and self.set_type==2:
            s_begin = index * self.pred_len
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len
        else:
            s_begin = index 
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        if self.inverse:
            seq_y = np.concatenate([self.data_x[r_begin:r_begin+self.label_len], self.data_y[r_begin+self.label_len:r_end]], 0)
        else:
            seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark
    
    def __len__(self):
        if self.delay_fb and self.set_type==2:
            return (len(self.data_x) - self.seq_len- self.pred_len) // self.pred_len
        else:
            return len(self.data_x) - self.seq_len- self.pred_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

class Dataset_ETT_minute(Dataset):
    def __init__(self, root_path, flag='train', delay_fb=False, size=None, 
                 features='S', data_path='ETTm1.csv', 
                 target='OT', scale=True, inverse=False, timeenc=0, freq='t', cols=None):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24*4*4
            self.label_len = 24*4
            self.pred_len = 24*4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train':0, 'val':1, 'test':2}
        self.set_type = type_map[flag]
        
        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq; self.delay_fb=delay_fb
        
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))

        #border1s = [0, 12*30*24*4 - self.seq_len, 12*30*24*4+4*30*24*4 - self.seq_len]
        #border2s = [12*30*24*4, 12*30*24*4+4*30*24*4, 12*30*24*4+8*30*24*4]
        border1s = [0, 4*30*24 - self.seq_len, 5*30*24 - self.seq_len]
        border2s = [4*30*24, 5*30*24, 20*30*24]

        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]
        
        if self.features=='M' or self.features=='MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features=='S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values

        if self.timeenc == 2:
            train_df_stamp = df_raw[['date']][border1s[0]:border2s[0]]
            train_df_stamp['date'] = pd.to_datetime(train_df_stamp.date)
            train_date_stamp = time_features(train_df_stamp, timeenc=self.timeenc)
            date_scaler = sklearn_StandardScaler().fit(train_date_stamp)

            df_stamp = df_raw[['date']][border1:border2]
            df_stamp['date'] = pd.to_datetime(df_stamp.date)
            data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq)
            data_stamp = date_scaler.transform(data_stamp)
        else:
            df_stamp = df_raw[['date']][border1:border2]
            df_stamp['date'] = pd.to_datetime(df_stamp.date)
            data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq)
        
        self.data_x = data[border1:border2]
        if self.inverse:
            self.data_y = df_data.values[border1:border2]
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
    
    def __getitem__(self, index):
        if self.delay_fb and self.set_type==2:
            s_begin = index * self.pred_len
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len
        else:
            s_begin = index 
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        if self.inverse:
            seq_y = np.concatenate([self.data_x[r_begin:r_begin+self.label_len], self.data_y[r_begin+self.label_len:r_end]], 0)
        else:
            seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark
    
    def __len__(self):
        if self.delay_fb and self.set_type==2:
            return (len(self.data_x) - self.seq_len- self.pred_len) // self.pred_len
        else:
            return len(self.data_x) - self.seq_len- self.pred_len + 1
    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)


class Dataset_Custom(Dataset):
    def __init__(self, root_path, flag='train', delay_fb=False, size=None, 
                 features='S', data_path='ETTh1.csv', 
                 target='OT', scale=True, inverse=False, timeenc=0, freq='h', cols=None):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24*4*4
            self.label_len = 24*4
            self.pred_len = 24*4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['train', 'test', 'val']
        type_map = {'train':0, 'val':1, 'test':2}
        self.set_type = type_map[flag]
        
        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq; self.delay_fb=delay_fb
        self.cols=cols
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))
        '''
        df_raw.columns: ['date', ...(other features), target feature]
        '''
        # cols = list(df_raw.columns); 
        
        if self.cols:
            cols=self.cols.copy()
            cols.remove(self.target)
        else:
            cols = list(df_raw.columns); cols.remove(self.target); cols.remove('date')
        df_raw = df_raw[['date']+cols+[self.target]]

        num_train = int(len(df_raw)*0.2)
        num_test = int(len(df_raw)*0.75)
        num_vali = len(df_raw) - num_train - num_test
        border1s = [0, num_train-self.seq_len, len(df_raw)-num_test-self.seq_len]
        border2s = [num_train, num_train+num_vali, len(df_raw)]
        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]
        
        if self.features=='M' or self.features=='MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features=='S':
            df_data = df_raw[[self.target]]

        if self.scale:
            train_data = df_data[border1s[0]:border2s[0]]
            self.scaler.fit(train_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values
            
        df_stamp = df_raw[['date']][border1:border2]
        df_stamp['date'] = pd.to_datetime(df_stamp.date)
        data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq)

        self.data_x = data[border1:border2]
        if self.inverse:
            self.data_y = df_data.values[border1:border2]
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
    
    def __getitem__(self, index):
        if self.delay_fb and self.set_type==2:
            s_begin = index * self.pred_len
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len
        else:
            s_begin = index 
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        if self.inverse:
            seq_y = np.concatenate([self.data_x[r_begin:r_begin+self.label_len], self.data_y[r_begin+self.label_len:r_end]], 0)
        else:
            seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark
    
    def __len__(self):
        if self.delay_fb and self.set_type==2:
            return (len(self.data_x) - self.seq_len- self.pred_len) // self.pred_len
        else:
            return len(self.data_x) - self.seq_len- self.pred_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

class Dataset_Pred(Dataset):
    def __init__(self, root_path, flag='pred',  delay_fb=False,  size=None, 
                 features='S', data_path='ETTh1.csv', 
                 target='OT', scale=True, inverse=False, timeenc=0, freq='15min', cols=None):
        # size [seq_len, label_len, pred_len]
        # info
        if size == None:
            self.seq_len = 24*4*4
            self.label_len = 24*4
            self.pred_len = 24*4
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]
        # init
        assert flag in ['pred']
        
        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq; self.delay_fb=delay_fb
        self.cols=cols
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path,
                                          self.data_path))
        '''
        df_raw.columns: ['date', ...(other features), target feature]
        '''
        if self.cols:
            cols=self.cols.copy()
            cols.remove(self.target)
        else:
            cols = list(df_raw.columns); cols.remove(self.target); cols.remove('date')
        df_raw = df_raw[['date']+cols+[self.target]]
        
        border1 = len(df_raw)-self.seq_len
        border2 = len(df_raw)
        
        if self.features=='M' or self.features=='MS':
            cols_data = df_raw.columns[1:]
            df_data = df_raw[cols_data]
        elif self.features=='S':
            df_data = df_raw[[self.target]]

        if self.scale:
            self.scaler.fit(df_data.values)
            data = self.scaler.transform(df_data.values)
        else:
            data = df_data.values
            
        tmp_stamp = df_raw[['date']][border1:border2]
        tmp_stamp['date'] = pd.to_datetime(tmp_stamp.date)
        pred_dates = pd.date_range(tmp_stamp.date.values[-1], periods=self.pred_len+1, freq=self.freq)
        
        df_stamp = pd.DataFrame(columns = ['date'])
        df_stamp.date = list(tmp_stamp.date.values) + list(pred_dates[1:])
        data_stamp = time_features(df_stamp, timeenc=self.timeenc, freq=self.freq[-1:])

        self.data_x = data[border1:border2]
        if self.inverse:
            self.data_y = df_data.values[border1:border2]
        else:
            self.data_y = data[border1:border2]
        self.data_stamp = data_stamp
    
    def __getitem__(self, index):
        if self.delay_fb and self.set_type==2:
            s_begin = index * self.pred_len
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len
        else:
            s_begin = index 
            s_end = s_begin + self.seq_len
            r_begin = s_end - self.label_len 
            r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        if self.inverse:
            seq_y = self.data_x[r_begin:r_begin+self.label_len]
        else:
            seq_y = self.data_y[r_begin:r_begin+self.label_len]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark
    
    def __len__(self):
        if self.delay_fb and self.set_type==2:
            return (len(self.data_x) - self.seq_len- self.pred_len) // self.pred_len
        else:
            return len(self.data_x) - self.seq_len- self.pred_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)

class FinancialDataset(Dataset):
    def __init__(self, root_path, flag='train', size=None, 
                 features='MS', data_path='finance.csv', 
                 target='Close', scale=True, inverse=False, timeenc=0, freq='b', cols = None):
        # size [seq_len, label_len, pred_len]
        if size is None:
            self.seq_len = 24  # customize based on your needs
            self.label_len = 1
            self.pred_len = 1
        else:
            self.seq_len = size[0]
            self.label_len = size[1]
            self.pred_len = size[2]

        assert flag in ['train', 'test', 'val']
        type_map = {'train': 0, 'val': 1, 'test': 2}
        self.set_type = type_map[flag]
        
        self.features = features
        self.target = target
        self.scale = scale
        self.inverse = inverse
        self.timeenc = timeenc
        self.freq = freq
        self.cols = cols
        
        self.root_path = root_path
        self.data_path = data_path
        self.__read_data__()

    def __read_data__(self):
        self.scaler = StandardScaler()
        df_raw = pd.read_csv(os.path.join(self.root_path, self.data_path))
        df_raw['Date'] = pd.to_datetime(df_raw['Date'])

        df_raw['day_of_week'] = df_raw['Date'].dt.dayofweek
        df_raw['day_of_month'] = df_raw['Date'].dt.day
        df_raw['month_of_year'] = df_raw['Date'].dt.month
        
        border1s = [0, int(len(df_raw)*0.7) - self.seq_len, int(len(df_raw)*0.9) - self.seq_len]
        border2s = [int(len(df_raw)*0.7), int(len(df_raw)*0.9), len(df_raw)]
        
        border1 = border1s[self.set_type]
        border2 = border2s[self.set_type]

        # Apply column selection based on 'cols' parameter
        # if self.cols:
        #     cols = self.cols.copy()
        #     if self.target in cols:
        #         cols.remove(self.target)
        #     if 'Date' in cols:
        #         cols.remove('Date')
        # else:
        #     # Default columns to include if 'cols' is not specified
        #     cols = list(df_raw.columns)
        #     cols.remove(self.target)
        #     cols.remove('Date')
        
        # df_data = df_raw[['Date'] + cols + [self.target]]


        # # df_data = df_raw if self.features == 'MS' else df_raw[[self.target] + ['Date']]

        # # if self.scale:
        # #     train_data = df_data.iloc[border1s[0]:border2s[0], :-1]
        # #     self.scaler.fit(train_data)
        # #     data = self.scaler.transform(df_data.iloc[:, :-1])
        # # else:
        # #     data = df_data.iloc[:, :-1].values

        # # self.data_x = data[border1:border2]
        # # self.data_y = df_data[self.target].values[border1:border2]
        # # self.data_stamp = df_data['Date'].values[border1:border2]

        # # if self.scale:
        # #     train_data = df_data.iloc[border1s[0]:border2s[0]][cols]
        # #     self.scaler.fit(train_data)
        # #     scaled_data = self.scaler.transform(df_data[cols])
        # #     df_data[cols] = scaled_data
        # numeric_cols = df_data.select_dtypes(include=[np.number]).columns.tolist()  # Select only numeric columns for scaling

        # if self.scale:
        #     train_data = df_data.loc[border1s[0]:border2s[0], numeric_cols]
        #     self.scaler.fit(train_data)
        #     scaled_data = self.scaler.transform(df_data.loc[:, numeric_cols])
        #     # Convert scaled_data back to a DataFrame and insert it back into df_data
        #     df_data.loc[:, numeric_cols] = scaled_data

        # self.data_x = df_data.loc[border1:border2, cols].values
        # self.data_y = df_data.loc[border1:border2, self.target].values
        # self.data_stamp = df_data.loc[border1:border2, 'Date'].values

        cols = [col for col in df_raw.columns if col not in ['Date', self.target, 'day_of_week', 'day_of_month', 'month_of_year']]
        print(cols)

        # if self.scale:
        #     train_data = df_raw.loc[border1s[0]:border2s[0], cols]
        #     self.scaler.fit(train_data)
        #     scaled_data = self.scaler.transform(df_raw.loc[:, cols])
        #     df_raw.loc[:, cols] = scaled_data

        # self.data_x = df_raw.loc[border1:border2, cols].values
        # self.data_y = df_raw.loc[border1:border2, self.target].values
        # self.data_stamp = df_raw.loc[border1:border2, ['day_of_week', 'day_of_month', 'month_of_year']].values
        
        if self.scale:
            train_data = df_raw.loc[border1s[0]:border2s[0], cols]
            self.scaler.fit(train_data)
            scaled_data = self.scaler.transform(df_raw.loc[:, cols])
            df_raw.loc[:, cols] = scaled_data

        # Storing data, target, and date-based features
        self.data_x = df_raw.loc[border1:border2, cols].values
        self.data_y = df_raw.loc[border1:border2, self.target].values.reshape(-1, 1)  # Ensuring y is always 2D
        self.data_stamp = df_raw.loc[border1:border2, ['day_of_week', 'day_of_month', 'month_of_year']].values

    def __getitem__(self, index):
        # s_begin = index
        # s_end = s_begin + self.seq_len
        # r_begin = s_end - self.label_len
        # r_end = r_begin + self.label_len + self.pred_len

        # seq_x = self.data_x[s_begin:s_end]
        # seq_y = self.data_y[r_begin:r_end]
        # seq_x_mark = self.data_stamp[s_begin:s_end]
        # seq_y_mark = self.data_stamp[r_begin:r_end]

        # return seq_x, seq_y, seq_x_mark, seq_y_mark
        s_begin = index
        s_end = s_begin + self.seq_len
        r_begin = s_end - self.label_len
        r_end = r_begin + self.label_len + self.pred_len

        seq_x = self.data_x[s_begin:s_end]
        seq_y = self.data_y[r_begin:r_end]
        seq_x_mark = self.data_stamp[s_begin:s_end]
        seq_y_mark = self.data_stamp[r_begin:r_end]

        return seq_x, seq_y, seq_x_mark, seq_y_mark

        # s_begin = index
        # s_end = s_begin + self.seq_len
        # r_begin = s_end - self.label_len
        # r_end = r_begin + self.label_len + self.pred_len

        # seq_x = self.data_x[s_begin:s_end]
        # seq_y = self.data_y[r_begin:r_end]
        # seq_x_mark = self.data_stamp[s_begin:s_end]  # Encoded date information
        # seq_y_mark = self.data_stamp[r_begin:r_end]  # Encoded date information
        # seq_y_shape = seq_y.shape[0]
        # seq_y = seq_y.reshape(seq_y_shape,1)

        # return seq_x, seq_y, seq_x_mark, seq_y_mark

    def __len__(self):
        return len(self.data_x) - self.seq_len - self.pred_len + 1

    def inverse_transform(self, data):
        return self.scaler.inverse_transform(data)