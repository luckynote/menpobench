from menpobench.method import MenpoFitWrapper
from menpobench.preprocess import menpo_preprocess
from menpofit.aam import AAMBuilder, LucasKanadeAAMFitter
from menpo.feature import fast_dsift

def train(img_generator):
    # clean up the images with the standard menpo preprocessing
    images = [menpo_preprocess(img) for img in img_generator]
    # build the AAM
    aam = AAMBuilder(features=fast_dsift,
                     normalization_diagonal=120,
                     n_levels=3).build(images, verbose=True, group='gt')
    fitter = LucasKanadeAAMFitter(aam, n_shape=0.9, n_appearance=0.9)

    # return a callable that wraps the menpo fitter in order to integrate with
    # menpobench
    return MenpoFitWrapper(fitter)
