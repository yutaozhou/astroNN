###############################################################################
#   normalizer.py: top-level class for normalizer
###############################################################################
import numpy as np

from astroNN import MAGIC_NUMBER


class Normalizer(object):
    """Top-level class for a normalizer"""

    def __init__(self, mode=None):
        """
        NAME:
            __init__
        PURPOSE:
            To define a normalizer
        HISTORY:
            2018-Jan-06 - Written - Henry Leung (University of Toronto)
        """

        self.normalization_mode = mode

        self.featurewise_center = False
        self.datasetwise_center = False

        self.featurewise_std_normalization = False
        self.datasetwise_std_normalization = False

    def normalize(self, data):

        mean_labels = 0.
        std_labels = 1.

        if self.normalization_mode == 0:
            self.featurewise_center = False
            self.datasetwise_center = False
            self.featurewise_std_normalization = False
            self.datasetwise_std_normalization = False
        elif self.normalization_mode == 1:
            self.featurewise_center = False
            self.datasetwise_center = True
            self.featurewise_std_normalization = False
            self.datasetwise_std_normalization = True
        elif self.normalization_mode == 2:
            self.featurewise_center = True
            self.datasetwise_center = False
            self.featurewise_std_normalization = True
            self.datasetwise_std_normalization = False
        elif self.normalization_mode == 3:
            self.featurewise_center = True
            self.datasetwise_center = False
            self.featurewise_std_normalization = False
            self.datasetwise_std_normalization = False
        elif self.normalization_mode == 255:
            # Used to normalize 8bit images
            self.featurewise_center = False
            self.datasetwise_center = False
            self.featurewise_std_normalization = False
            self.datasetwise_std_normalization = False
            mean_labels = 127.5
            std_labels = 127.5

        print('====Message from {}===='.format(self.__class__.__name__))
        print('You selected mode: {}'.format(self.normalization_mode))
        print('Featurewise Center: {}'.format(self.featurewise_center))
        print('Datawise Center: {}'.format(self.datasetwise_center))
        print('Featurewise std Center: {}'.format(self.featurewise_std_normalization))
        print('Datawise std Center: {}'.format(self.datasetwise_std_normalization))
        print('====Message ends====')

        data_array = np.array(data)

        if self.featurewise_center is True:
            mean_labels = np.zeros(data_array.shape[1])
            for i in range(data_array.shape[1]):
                not9999_index = np.where(data_array[:, i] != MAGIC_NUMBER)
                mean_labels[i] = np.mean((data_array[:, i])[not9999_index], axis=0)
                (data_array[:, i])[not9999_index] -= mean_labels[i]

        if self.datasetwise_center is True:
            mean_labels = np.mean(data_array[(data_array != MAGIC_NUMBER)])
            data_array[(data_array != MAGIC_NUMBER)] -= mean_labels

        if self.featurewise_std_normalization is True:
            std_labels = np.ones(data_array.shape[1])
            for i in range(data_array.shape[1]):
                not9999_index = np.where(data_array[:, i] != MAGIC_NUMBER)
                std_labels[i] = np.std((data_array[:, i])[not9999_index], axis=0)
                (data_array[:, i])[not9999_index] /= std_labels[i]

        if self.datasetwise_center is True:
            std_labels = np.std(data_array[(data_array != MAGIC_NUMBER)])
            data_array[(data_array != MAGIC_NUMBER)] /= std_labels

        if self.normalization_mode == 255:
            data_array -= mean_labels
            data_array /= std_labels

        return data_array, mean_labels, std_labels


class Denormalizer(object):
    """Top-level class for Denormalizer"""

    def __init__(self, mode=1):
        """
        NAME:
            __init__
        PURPOSE:
            To define a denormalizer
        HISTORY:
            2018-Jan-06 - Written - Henry Leung (University of Toronto)
        """

        self.normalization_mode = mode

        self.featurewise_center = False
        self.samplewise_center = False

        self.featurewise_std_normalization = False
        self.samplewise_std_normalization = False

    def denormalize(self, data):
        pass