# ---------------------------------------------------------#
#   astroNN.models.CVAE: Contain Variational Autoencoder Model
# ---------------------------------------------------------#
import os

import keras.backend as K
import numpy as np
from keras import regularizers
from keras.callbacks import ReduceLROnPlateau, CSVLogger
from keras.layers import MaxPooling1D, Conv1D, Dense, Flatten, Lambda, Reshape, Multiply, Add
from keras.models import Model, Input, Sequential

from astroNN.apogee.plotting import ASPCAP_plots
from astroNN.models.ConvVAEBase import ConvVAEBase
from astroNN.models.utilities.normalizer import Normalizer
from astroNN.models.utilities.custom_layers import KLDivergenceLayer


class Apogee_CVAE(ConvVAEBase, ASPCAP_plots):
    """
    NAME:
        VAE
    PURPOSE:
        To create Variational Autoencoder
    HISTORY:
        2017-Dec-21 - Written - Henry Leung (University of Toronto)
    """

    def __init__(self):
        """
        NAME:
            model
        PURPOSE:
            To create Variational Autoencoder
        INPUT:
        OUTPUT:
        HISTORY:
            2017-Dec-21 - Written - Henry Leung (University of Toronto)
        """
        super(Apogee_CVAE, self).__init__()

        self.name = '2D Convolutional Variational Autoencoder'
        self._model_identifier = 'APOGEE_CVAE'
        self._implementation_version = '1.0'
        self.batch_size = 64
        self.initializer = 'he_normal'
        self.activation = 'relu'
        self.optimizer = 'rmsprop'
        self.num_filters = [2, 4]
        self.filter_length = 8
        self.pool_length = 4
        self.num_hidden = [128, 64]
        self.latent_dim = 2
        self.max_epochs = 100
        self.lr = 0.005
        self.reduce_lr_epsilon = 0.0005
        self.reduce_lr_min = 0.0000000001
        self.reduce_lr_patience = 4
        self.epsilon_std = 1.0
        self.task = 'regression'
        self.keras_encoder = None
        self.keras_vae = None
        self.l1 = 1e-7
        self.l2 = 1e-7

        self.input_norm_mode = 3
        self.labels_norm_mode = 3

    def model(self):
        input_tensor = Input(shape=self.input_shape)
        cnn_layer_1 = Conv1D(kernel_initializer=self.initializer, activation=self.activation, padding="same",
                             filters=self.num_filters[0],
                             kernel_size=self.filter_length, kernel_regularizer=regularizers.l2(self.l2))(input_tensor)
        cnn_layer_2 = Conv1D(kernel_initializer=self.initializer, activation=self.activation, padding="same",
                             filters=self.num_filters[1],
                             kernel_size=self.filter_length, kernel_regularizer=regularizers.l2(self.l2))(cnn_layer_1)
        maxpool_1 = MaxPooling1D(pool_size=self.pool_length)(cnn_layer_2)
        flattener = Flatten()(maxpool_1)
        layer_4 = Dense(units=self.num_hidden[0], kernel_regularizer=regularizers.l1(self.l1),
                        kernel_initializer=self.initializer, activation=self.activation)(flattener)
        layer_5 = Dense(units=self.num_hidden[1], kernel_regularizer=regularizers.l1(self.l1),
                        kernel_initializer=self.initializer, activation=self.activation)(layer_4)
        z_mu = Dense(units=self.latent_dim, activation="linear", name='mean_output',
                            kernel_regularizer=regularizers.l1(self.l1))(layer_5)
        z_log_var = Dense(units=self.latent_dim, activation='linear', name='sigma_output',
                             kernel_regularizer=regularizers.l1(self.l1))(layer_5)

        z_mu, z_log_var = KLDivergenceLayer()([z_mu, z_log_var])
        z_sigma = Lambda(lambda t: K.exp(.5 * t))(z_log_var)

        eps = Input(tensor=K.random_normal(stddev=1.0, shape=(K.shape(input_tensor)[0], self.latent_dim)))
        z_eps = Multiply()([z_sigma, eps])
        z = Add()([z_mu, z_eps])

        decoder = Sequential()
        decoder.add(Dense(units=self.num_hidden[1], kernel_regularizer=regularizers.l1(self.l1),
                        kernel_initializer=self.initializer, activation=self.activation, input_dim=self.latent_dim))
        decoder.add(Dense(units=self.num_hidden[0], kernel_regularizer=regularizers.l1(self.l1),
                        kernel_initializer=self.initializer, activation=self.activation))
        decoder.add(Dense(units=self.input_shape[0] * self.num_filters[1], kernel_regularizer=regularizers.l2(self.l2),
                        kernel_initializer=self.initializer, activation=self.activation))
        output_shape = (self.batch_size, self.input_shape[0], self.num_filters[1])
        decoder.add(Reshape(output_shape[1:]))
        decoder.add(Conv1D(kernel_initializer=self.initializer, activation=self.activation, padding="same",
                               filters=self.num_filters[1],
                               kernel_size=self.filter_length, kernel_regularizer=regularizers.l2(self.l2)))
        decoder.add(Conv1D(kernel_initializer=self.initializer, activation=self.activation, padding="same",
                               filters=self.num_filters[0],
                               kernel_size=self.filter_length, kernel_regularizer=regularizers.l2(self.l2)))
        decoder.add(Conv1D(kernel_initializer=self.initializer, activation='linear', padding="same",
                              filters=1, kernel_size=self.filter_length))

        x_pred = decoder(z)
        vae = Model(inputs=[input_tensor, eps], outputs=x_pred)
        encoder = Model(input_tensor, z_mu)

        return vae, encoder, decoder

    def sampling(self, args):
        z_mean, z_log_var = args
        epsilon = K.random_normal(shape=(K.shape(z_mean)[0], self.latent_dim), mean=0., stddev=self.epsilon_std)
        return z_mean + K.exp(z_log_var / 2) * epsilon

    def train(self, input_data, input_recon_target):
        # Call the checklist to create astroNN folder and save parameters
        self.pre_training_checklist_child(input_data, input_recon_target)

        csv_logger = CSVLogger(self.fullfilepath + 'log.csv', append=True, separator=',')

        if self.task == 'classification':
            raise RuntimeError('astroNN VAE does not support classification task')

        reduce_lr = ReduceLROnPlateau(monitor='val_loss', factor=0.5, epsilon=self.reduce_lr_epsilon,
                                      patience=self.reduce_lr_patience, min_lr=self.reduce_lr_min, mode='min',
                                      verbose=2)

        self.keras_model.fit_generator(generator=self.training_generator,
                                       steps_per_epoch=self.num_train // self.batch_size,
                                       validation_data=self.validation_generator,
                                       validation_steps=self.val_num // self.batch_size,
                                       epochs=self.max_epochs, max_queue_size=20, verbose=2, workers=os.cpu_count(),
                                       callbacks=[reduce_lr, csv_logger])

        # Call the post training checklist to save parameters
        self.post_training_checklist_child()

        return None