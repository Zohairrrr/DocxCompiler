import os
import tensorflow as tf
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler,OneHotEncoder

class MNISTProdPipe:
    def __init__(self, stateDir:str):
        self.stateDir = stateDir
        self.scalerPath = os.path.join(stateDir,'scaler.pkl')
        self.encoderPath = os.path.join(stateDir,'encoder.pkl')

        #for the mean and std to be between 0 and 1
        self.scaler = StandardScaler()
        self.encoder = OneHotEncoder(sparse_output=False)

        if not os.path.exists(self.stateDir):
            os.makedirs(self.stateDir)

    def extractRawData(self)->tuple:
        path = tf.keras.utils.get_file(
            'mnist.npz',
            origin='https://storage.googleapis.com/tensorflow/tf-keras-datasets/mnist.npz'
        )
        with np.load(path,allow_pickle=True) as f:
            xTrain, yTrain = f['x_train'], f['y_train']
            xTest, yTest = f['x_test'], f['y_test']
        return np.concatenate((xTrain,xTest),axis = 0),np.concatenate((yTrain,yTest),axis = 0)
    
    def buildPipelines(self, batchSize: int = 64) -> tuple[tf.data.Dataset, tf.data.Dataset]:
        images, labels = self._extract_raw_data()
        