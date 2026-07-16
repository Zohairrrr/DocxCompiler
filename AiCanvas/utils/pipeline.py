import os
import tensorflow as tf
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler,OneHotEncoder

class MNISTProdPipe:
    def __init__(self, stateDir:str):
        self.stateDir = stateDir
        self.scalarPath = os.path.join(stateDir,'scaler.pkl')
        self.encoderPath = os.path.join(stateDir,'encoder.pkl')