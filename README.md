# TF Lite statistics collector from TF Hub

TensorFlow Hub provides large variety of models.
This repository helps to go through all TF Lite models in TFHub one-by-one and collect statistics about operations in them.
Each model will be kept on the machine only for necessary amount of time to avoid out-of-memory

## How to collect information

### Set up environment using virtualenv
```shell
pip install -r requirements.txt
playwright install chromium
```

### Collect statistics
1 step. Scrub all the links to tflite models from TFHub site (may take ~15 minutes)
```shell
python collect_links_to_models.py
```
As a result of the first step you will find a file `log.dsv`. It could be read via excel-like pro

2 step.
```shell
python download_and_collect.py
```
