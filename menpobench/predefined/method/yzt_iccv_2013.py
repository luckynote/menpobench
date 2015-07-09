import subprocess
import numpy as np
import shutil
import os
from menpo.visualize import print_progress
from pathlib import Path
import menpo.io as mio
from menpobench.method.managed import managed_method
from menpobench.method.base import matlab_functions_dir, predefined_method_dir
from menpobench.base import TempDirectory
from scipy.io import savemat, loadmat


def images_to_mat(images, out_path):
    as_fortran = np.asfortranarray
    image_tuples = [{'pixels': as_fortran(im.rolled_channels()),
                     'gt_shape': as_fortran(im.landmarks['gt_shape'].lms.points),
                     # TODO: use bbox
                     'bbox': as_fortran(im.landmarks['gt_shape'].lms.points)}
                    for im in images]

    mat_out_path = out_path / 'menpobench_training_images.mat'
    print('Serializing training data to Matlab file: {}'.format(mat_out_path))
    savemat(str(mat_out_path), {'menpobench_training_images': image_tuples})


def save_images_to_dir(images, out_path, output_ext='.jpg'):
    if not out_path.exists():
        out_path.mkdir()
    for k, im in enumerate(print_progress(images)):
        mio.export_image(im, out_path / '{}{}'.format(k, output_ext))


def save_landmarks_to_dir(images, label, out_path, output_ext='.pts'):
    if not out_path.exists():
        out_path.mkdir()
    for k, im in enumerate(print_progress(images)):
        mio.export_landmark_file(im.landmarks[label],
                                 out_path / '{}{}'.format(k, output_ext))



class MatlabWrapper(object):

    def __init__(self, fitter):
        self.fitter = fitter

    def __call__(self, img_generator):
        results = []
        # for img in img_generator:
        #     img = menpo_preprocess(img)
        #     # obtain ground truth (original) landmarks
        #     gt_shape = img.landmarks['gt_shape'].lms
        #     results.append(self.fitter.fit(img, gt_shape, gt_shape=gt_shape))
        return results


def invoke_process(command_list):
    print(' '.join(command_list))
    subprocess.check_call(command_list)


def invoke_matlab(command):
    invoke_process(['matlab', '-wait', '-nosplash', '-nodesktop', '-nojvm',
                    "'{}'".format(command)])


def train_matlab_method(method_path, matlab_train_filename):
    # Get absolute path to the train method and copy across to the metho
    # folder
    matlab_train_path = predefined_method_dir() / matlab_train_filename
    shutil.copyfile(str(matlab_train_path),
                    str(method_path / 'menpobench_train.m'))

    # Call matlab bridge to train file - will drop out a model file
    invoke_matlab('addpath({}); menpobench_matlab_train({});'.format(
        matlab_functions_dir(), method_path))


def train(img_generator):
    with managed_method('yzt_iccv_2013', cleanup=False) as method_path:
        train_path = method_path / 'menpobench_train_images'
        images = list(img_generator)

        save_images_to_dir(images, train_path)
        save_landmarks_to_dir(images, 'gt_shape', train_path)

        train_matlab_method(method_path, 'yzt_iccv_2013.m')

        # return a callable that wraps the matlab fitter in order to integrate
        # with menpobench
        return MatlabWrapper(None)