from sklearn.pipeline import Pipeline
from app.pipeline.bandpass import BandPassFilter
from app.pipeline.fft import FastFourierTransform
from app.pipeline.mel import Mel
from app.pipeline.zscore import ZScore

def melspec_zscore(model) -> Pipeline:
    pipeline = Pipeline([
        ('bandpass_filter', BandPassFilter(model)),
        ('fft', FastFourierTransform(model)),
        ('mel', Mel(model)),
        ('anomaly', ZScore()),
    ])
    return pipeline


def gmm(model) -> Pipeline:
    pipeline = Pipeline([
        ('bandpass_filter', BandPassFilter(model)),
        ('fft', FastFourierTransform(model)),
        ('mel', Mel(model)),
    ])
    return pipeline


