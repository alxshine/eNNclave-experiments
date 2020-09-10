import os
import os.path as path

import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.python.keras.preprocessing import sequence
from tensorflow.python.keras.preprocessing import text

# Vectorization parameters

# Range (inclusive) of n-gram sizes for tokenizing text.
NGRAM_RANGE = (1, 2)

# Limit on the number of features. We use the top 20K features.
TOP_K = 20000

# Whether text should be split into word or character n-grams.
# One of 'word', 'char'.
TOKEN_MODE = 'word'

# Minimum document/corpus frequency below which a token will be discarded.
MIN_DOCUMENT_FREQUENCY = 2

# Limit on the length of text sequences. Sequences longer than this
# will be truncated.
MAX_SEQUENCE_LENGTH = 500


def get_all_layers(model):
    """ Get all layers of model, including ones inside a nested model """
    layers = []
    for l in model.layers:
        if hasattr(l, 'layers'):
            layers += get_all_layers(l)
        else:
            layers.append(l)
    return layers


def preprocess_vgg(images):
    processed_images = np.empty((len(images), 224, 224, 3))
    for i, image_path in enumerate(images):
        image = tf.io.read_file(image_path)
        try:
            image = tf.image.decode_jpeg(image, channels=3)
        except tf.errors.InvalidArgumentError:
            image = tf.image.decode_bmp(image, channels=3)
        image = tf.cast(image, tf.float32)
        image = (image / 127.5) - 1
        image = tf.image.resize(image, (224, 224))
        processed_images[i] = image
    return processed_images


def preprocess(x, y, img_size):
    image = tf.io.read_file(x)
    image = tf.image.decode_jpeg(image, channels=3)
    image = tf.cast(image, tf.float32)
    image = (image / 127.5) - 1
    image = tf.image.resize(image, (img_size, img_size))

    return image, y


def preprocess_flowers(x, y):
    return preprocess(x, y, 224)


def preprocess_lfw(x, y):
    return preprocess(x, y, 250)


def preprocess_faces(x, y):
    return preprocess(x, y, 224)


def preprocess_mnist(x, y):
    x = tf.cast(x, tf.float32)
    x = (x / 127.5) - 1
    return x, y


def preprocess_224(x, y):
    return preprocess(x, y, 224)


def preprocess_250(x, y):
    return preprocess(x, y, 250)


def generate_dataset(x, y, preprocess_function=preprocess_224,
                     batch_size=32, repeat=True, shuffle=True):
    ds = tf.data.Dataset.from_tensor_slices((x, y))
    if preprocess_function is not None:
        ds = ds.map(preprocess_function)

    if shuffle:
        ds = ds.shuffle(buffer_size=batch_size)
    if repeat:
        ds = ds.repeat()

    ds = ds.batch(batch_size)
    ds = ds.prefetch(buffer_size=tf.data.experimental.AUTOTUNE)

    return ds


def get_num_classes(labels):
    """Gets the total number of classes.

    # Arguments
        labels: list, label values.
            There should be at lease one sample for values in the
            range (0, num_classes -1)

    # Returns
        int, total number of classes.

    # Raises
        ValueError: if any label value in the range(0, num_classes - 1)
            is missing or if number of classes is <= 1.
    """
    num_classes = max(labels) + 1
    missing_classes = [i for i in range(num_classes) if i not in labels]
    if len(missing_classes):
        raise ValueError('Missing samples with label value(s) '
                         '{missing_classes}. Please make sure you have '
                         'at least one sample for every label value '
                         'in the range(0, {max_class})'.format(
            missing_classes=missing_classes,
            max_class=num_classes - 1))

    if num_classes <= 1:
        raise ValueError('Invalid number of labels: {num_classes}.'
                         'Please make sure there are at least two classes '
                         'of samples'.format(num_classes=num_classes))
    return num_classes


def get_num_words_per_sample(sample_texts):
    """Gets the median number of words per sample given corpus.

    # Arguments
        sample_texts: list, sample texts.

    # Returns
        int, median number of words per sample.
    """
    num_words = [len(s.split()) for s in sample_texts]
    return np.median(num_words)


def get_dataset_from_model_path(model_path):
    basename = path.basename(model_path)
    without_extension, _ = path.splitext(basename)
    dataset = without_extension.split('_')[0]
    return dataset
