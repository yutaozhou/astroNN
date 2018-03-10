import unittest
import numpy.testing as npt

import tensorflow as tf

from astroNN import MAGIC_NUMBER, keras_import_manager
from astroNN.nn.losses import mean_absolute_error, mean_squared_error
from astroNN.nn import magic_correction_term
from astroNN.nn.metrics import categorical_accuracy, binary_accuracy, mean_absolute_percentage_error, \
    mean_squared_logarithmic_error

keras = keras_import_manager()
get_session = keras.backend.get_session


class LossFuncTestCase(unittest.TestCase):
    def test_loss_func(self):
        y_pred = tf.Variable([2., 3., 4.])
        y_true = tf.Variable([2., MAGIC_NUMBER, 4.])

        # make sure loss functions handle magic_number correctly
        self.assertEqual(mean_absolute_error(y_true, y_pred).eval(session=get_session()), 0.)
        self.assertEqual(mean_squared_error(y_true, y_pred).eval(session=get_session()), 0.)

        # =============Magic correction term============= #
        y_true = tf.Variable([[2., MAGIC_NUMBER, MAGIC_NUMBER], [2., MAGIC_NUMBER, 4.]])
        npt.assert_array_equal(magic_correction_term(y_true).eval(session=get_session()), [3., 1.5])

        # =============multi dimensional case============= #
        y_pred = tf.Variable([[2., 3., 4.], [2., 3., 7.]])
        y_true = tf.Variable([[2., MAGIC_NUMBER, 4.], [2., MAGIC_NUMBER, 4.]])
        npt.assert_almost_equal(mean_absolute_error(y_true, y_pred).eval(session=get_session()), [0., 3. / 2.])
        npt.assert_almost_equal(mean_squared_error(y_true, y_pred).eval(session=get_session()), [0., 9. / 2])

        # =============Accuracy============= #
        y_pred = tf.Variable([[1., 0., 0.], [1., 0., 0.]])
        y_true = tf.Variable([[1., MAGIC_NUMBER, 1.], [0., MAGIC_NUMBER, 1.]])
        # Truth with Magic number is wrong
        npt.assert_array_equal(categorical_accuracy(y_true, y_pred).eval(session=get_session()), [1., 0.])
        npt.assert_almost_equal(binary_accuracy(y_true, y_pred).eval(session=get_session()), [1. / 2., 0.])

        # =============Percentage Accuracy============= #
        y_pred = tf.Variable([[1., 0., 0.], [1., 0., 0.]])
        y_true = tf.Variable([[1., MAGIC_NUMBER, 1.], [1., MAGIC_NUMBER, 1.]])
        # Truth with Magic number is wrong
        npt.assert_array_almost_equal(mean_absolute_percentage_error(y_true, y_pred).eval(session=get_session()),
                                      [50., 50.], decimal=3)

        # =============Mean Squared Log Error============= #
        y_pred = tf.Variable([[1., 0., 0.], [1., 0., 0.]])
        y_true = tf.Variable([[1., MAGIC_NUMBER, 1.], [1., MAGIC_NUMBER, 1.]])
        # Truth with Magic number is wrong
        npt.assert_array_almost_equal(mean_squared_logarithmic_error(y_true, y_pred).eval(session=get_session()),
                                      [0.24, 0.24], decimal=3)


if __name__ == '__main__':
    unittest.main()
