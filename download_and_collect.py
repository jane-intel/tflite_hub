import os
from collections import defaultdict

import wget

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf

DIRECTORY = "/Users/missjane/PycharmProjects/tflite_hub/models"
URLs = [
    # 1 - 10
    "https://tfhub.dev/captain-pool/lite-model/esrgan-tf2/1?lite-format=tflite",
    # 2
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/prediction/1?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/fp16/transfer/1?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/prediction/1?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/magenta/arbitrary-image-stylization-v1-256/int8/transfer/1?lite-format=tflite",
    # 3
    "https://tfhub.dev/google/lite-model/spice/1?lite-format=tflite",
    # 4
    "https://tfhub.dev/google/lite-model/aiy/vision/classifier/birds_V1/3?lite-format=tflite",
    # 5
    "https://tfhub.dev/google/lite-model/movenet/singlepose/thunder/3?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/movenet/singlepose/thunder/tflite/float16/4?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/movenet/singlepose/thunder/tflite/int8/4?lite-format=tflite",
    # 6
    "https://tfhub.dev/google/lite-model/movenet/multipose/lightning/tflite/float16/1?lite-format=tflite",
    # 7
    "https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/3?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/float16/4?lite-format=tflite",
    "https://tfhub.dev/google/lite-model/movenet/singlepose/lightning/tflite/int8/4?lite-format=tflite",
    # 8
    "https://tfhub.dev/google/lite-model/yamnet/tflite/1?lite-format=tflite",
    # 9
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/dr/predict/1?lite-format=tflite",
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/dr/transfer/1?lite-format=tflite",
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/fp16/predict/1?lite-format=tflite",
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/fp16/transfer/1?lite-format=tflite",
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/int8/predict/1?lite-format=tflite",
    "https://tfhub.dev/sayakpaul/lite-model/arbitrary-image-stylization-inceptionv3/int8/transfer/1?lite-format=tflite",
    # 10
    "https://tfhub.dev/tensorflow/lite-model/efficientdet/lite2/detection/default/1?lite-format=tflite",
    "https://tfhub.dev/tensorflow/lite-model/efficientdet/lite2/detection/metadata/1?lite-format=tflite",
]


def stats_per_model(path: str):
    result = defaultdict(int)
    error = None
    try:
        interpreter = tf.lite.Interpreter(path)
        for op_attrs in interpreter._get_ops_details():
            result[op_attrs['op_name']] += 1
    except Exception as e:
        error = str(e)
    print("Done", path)
    return result, error


if __name__ == "__main__":
    model_to_ops = dict()
    errors = dict()
    for url in URLs:
        model_path = wget.download(url, DIRECTORY)
        stats, error = stats_per_model(model_path)
        os.remove(model_path)
        model_to_ops[model_path] = stats
        if error is not None:
            errors[model_path] = error

    # report
    for model, stats in model_to_ops.items():
        print(model)
        for op in sorted(stats):
            print(op, stats[op])

    for error in errors:
        print(model)
        print(error)
