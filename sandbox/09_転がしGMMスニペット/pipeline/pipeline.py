from sklearn.pipeline import Pipeline
from .bandpass import BandPassFilter
from .fft import FastFourierTransform
from .stft import ShortTimeFourierTransform
from .mel import Mel
from .zscore import ZScore
from .gmm import GMM

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
        ('stft', ShortTimeFourierTransform(model)),
        ('mel', Mel(model)),
        ('gmm', GMM(model))
    ])
    return pipeline