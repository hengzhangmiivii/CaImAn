import logging
import os

import numpy as np
import scipy

from caiman.paths import caiman_datadir
from caiman.source_extraction.cnmf.utilities import dict_compare


class CNMFParams(object):

    def __init__(self, n_processes=1, K=30, gSig=[5, 5], gSiz=None, ssub=2, tsub=2, p=2, p_ssub=2, p_tsub=2,
                 thr=0.8, do_merge=True,
                 method_init='greedy_roi', nb=1, nb_patch=1, del_duplicates=False,
                 n_pixels_per_process=None, block_size=None, num_blocks_per_run=20, check_nan=True,
                 normalize_init=True, options_local_NMF=None, remove_very_bad_comps=False, alpha_snmf=10e2,
                 update_background_components=True, low_rank_background=True, rolling_sum=False, min_corr=.85,
                 min_pnr=20, ring_size_factor=1.5, center_psf=False, ssub_B=2, init_iter=2, fr=30, decay_time=0.4,
                 min_SNR=2.5, rf=None, stride=None, memory_fact=1, border_pix=0,
                 method_deconvolution='oasis',
                 minibatch_shape=100, rolling_length=100, minibatch_suff_stat=3,
                 rval_thr=0.8, s_min=None, thresh_fitness_delta=-20, thresh_fitness_raw=None, thresh_overlap=0.5,
                 num_times_comp_updated=np.inf, max_comp_update_shape=np.inf, batch_update_suff_stat=False,
                 use_dense=True, simultaneously=False, n_refit=0, N_samples_exceptionality=None,
                 max_num_added=1, min_num_trial=3, thresh_CNN_noisy=0.5,
                 ):
        """Dictionary for setting the CNMF parameters.

        Any parameter that is not set get a default value specified
        by the dictionary default options

        dims: The dimensions of the movie

        T: The number of frames in the movie.

        PATCH PARAMS
            rf: Half-size of patch

            stride: overlap of patch

            memory_fact: A memory factor for patches

            border_pix: Number of pixels to exclude on the border.

            low_rank_background:bool
                whether to update the using a low rank approximation. In the False case all the nonzero elements of the background components are updated using hals
                (to be used with one background per patch)

        MERGE PARAMS
            do_merge: Whether or not to merge

            thr: The merge threshold for spatial correlation.

        PRE-PROCESS PARAMS#############

            sn: None,
                noise level for each pixel

            noise_range: [0.25, 0.5]
                     range of normalized frequencies over which to average

            noise_method': 'mean'
                     averaging method ('mean','median','logmexp')

            max_num_samples_fft': 3*1024

            n_pixels_per_process: 1000

            compute_g': False
                flag for estimating global time constant

            p : 2
                 order of AR indicator dynamics

            lags: 5
                number of lags to be considered for time constant estimation

            include_noise: False
                    flag for using noise values when estimating g

            pixels: None
                 pixels to be excluded due to saturation

            check_nan: True

        INIT PARAMS###############

            n_processes: The number of processes to use, determines amount of memory to use.

            K:     30
                number of components

            gSig: [5, 5]
                  size of bounding box

            gSiz: [int(round((x * 2) + 1)) for x in gSig],

            ssub:   2
                spatial downsampling factor

            tsub:   2
                temporal downsampling factor

            nIter: 5
                number of refinement iterations

            kernel: None
                user specified template for greedyROI

            maxIter: 5
                number of HALS iterations

            method: method_init
                can be greedy_roi or sparse_nmf, local_NMF

            max_iter_snmf : 500

            alpha_snmf: 10e2

            sigma_smooth_snmf : (.5,.5,.5)

            perc_baseline_snmf: 20

            nb:  1
                number of background components

            normalize_init:
                whether to pixelwise equalize the movies during initialization

            options_local_NMF:
                dictionary with parameters to pass to local_NMF initializer

        SPATIAL PARAMS##########

            dims: dims
                number of rows, columns [and depths]

            method: 'dilate','ellipse', 'dilate'
                method for determining footprint of spatial components ('ellipse' or 'dilate')

            dist: 3
                expansion factor of ellipse
            n_pixels_per_process: n_pixels_per_process
                number of pixels to be processed by eacg worker

            medw: (3,)*len(dims)
                window of median filter
            thr_method: 'nrg'
               Method of thresholding ('max' or 'nrg')

            maxthr: 0.1
                Max threshold

            nrgthr: 0.9999
                Energy threshold


            extract_cc: True
                Flag to extract connected components (might want to turn to False for dendritic imaging)

            se: np.ones((3,)*len(dims), dtype=np.uint8)
                 Morphological closing structuring element

            ss: np.ones((3,)*len(dims), dtype=np.uint8)
                Binary element for determining connectivity


            update_background_components:bool
                whether to update the background components in the spatial phase

            method_ls:'lasso_lars'
                'nnls_L0'. Nonnegative least square with L0 penalty
                'lasso_lars' lasso lars function from scikit learn
                'lasso_lars_old' lasso lars from old implementation, will be deprecated

        TEMPORAL PARAMS###########

            ITER: 2
                block coordinate descent iterations

            method:'oasis', 'cvxpy',  'oasis'
                method for solving the constrained deconvolution problem ('oasis','cvx' or 'cvxpy')
                if method cvxpy, primary and secondary (if problem unfeasible for approx solution)

            solvers: ['ECOS', 'SCS']
                 solvers to be used with cvxpy, can be 'ECOS','SCS' or 'CVXOPT'

            p:
                order of AR indicator dynamics

            memory_efficient: False

            bas_nonneg: True
                flag for setting non-negative baseline (otherwise b >= min(y))

            noise_range: [.25, .5]
                range of normalized frequencies over which to average

            noise_method: 'mean'
                averaging method ('mean','median','logmexp')

            lags: 5,
                number of autocovariance lags to be considered for time constant estimation

            fudge_factor: .96
                bias correction factor (between 0 and 1, close to 1)

            nb

            verbosity: False

            block_size : block_size
                number of pixels to process at the same time for dot product. Make it smaller if memory problems

        QUALITY EVALUATION PARAMETERS###########

            fr: 30
                Imaging rate

            decay_time: 0.5
                length of decay of typical transient (in seconds)

            min_SNR: 2.5
                trace SNR threshold

            SNR_lowest: 0.5
                minimum required trace SNR

            rval_thr: 0.8
                space correlation threshold

            rval_lowest: -1
                minimum required space correlation

            use_cnn: True
                flag for using the CNN classifier

            min_cnn_thr: 0.9
                CNN classifier threshold

            cnn_lowest: 0.1
                minimum required CNN threshold

            gSig_range: None
                gSig scale values for CNN classifier

        """

        self.patch = {
            'ssub': p_ssub,             # spatial downsampling factor
            'tsub': p_tsub,              # temporal downsampling factor
            'only_init': True,
            'skip_refinement': False,
            'remove_very_bad_comps': remove_very_bad_comps,
            'nb': nb_patch,
            'in_memory': True,
            'rf': rf,
            'stride': stride,
            'memory_fact': memory_fact,
            'n_processes': n_processes,
            'border_pix': border_pix,
            'low_rank_background': low_rank_background,
            'del_duplicates': del_duplicates
        }

        self.preprocess = {'sn': None,                  # noise level for each pixel
                            # range of normalized frequencies over which to average
                            'noise_range': [0.25, 0.5],
                            # averaging method ('mean','median','logmexp')
                            'noise_method': 'mean',
                            'max_num_samples_fft': 3 * 1024,
                            'n_pixels_per_process': n_pixels_per_process,
                            'compute_g': False,            # flag for estimating global time constant
                            'p': p,                        # order of AR indicator dynamics
                            # number of autocovariance lags to be considered for time
                            # constant estimation
                            'lags': 5,
                            'include_noise': False,        # flag for using noise values when estimating g
                            'pixels': None,
                            # pixels to be excluded due to saturation
                            'check_nan': check_nan
                            }

        gSig = gSig if gSig is not None else [-1, -1]

        self.init = {'K': K,                  # number of components,
                      'gSig': gSig,                               # size of bounding box
                      'gSiz': [np.int((np.ceil(x) * 2) + 1) for x in gSig] if gSiz is None else gSiz,
                      'ssub': ssub,             # spatial downsampling factor
                      'tsub': tsub,             # temporal downsampling factor
                      'nIter': 5,               # number of refinement iterations
                      'kernel': None,           # user specified template for greedyROI
                      'maxIter': 5,              # number of HALS iterations
                      'method': method_init,     # can be greedy_roi or sparse_nmf, local_NMF
                      'max_iter_snmf': 500,
                      'alpha_snmf': alpha_snmf,
                      'sigma_smooth_snmf': (.5, .5, .5),
                      'perc_baseline_snmf': 20,
                      'nb': nb,                 # number of background components
                      # whether to pixelwise equalize the movies during initialization
                      'normalize_init': normalize_init,
                      # dictionary with parameters to pass to local_NMF initializaer
                      'options_local_NMF': options_local_NMF,
                      'rolling_sum': rolling_sum,
                      'rolling_length': rolling_length,
                      'min_corr': min_corr,
                      'min_pnr': min_pnr,
                      'ring_size_factor': ring_size_factor,
                      'center_psf': center_psf,
                      'ssub_B': ssub_B,
                      'init_iter': init_iter
                      }

        self.spatial = {
            # method for determining footprint of spatial components ('ellipse' or 'dilate')
            'method': 'dilate',  # 'ellipse', 'dilate',
            'dist': 3,                       # expansion factor of ellipse
            # number of pixels to be processed by each worker
            'n_pixels_per_process': n_pixels_per_process,
            # window of median filter
            'medw': None,
            'thr_method': 'nrg',  # Method of thresholding ('max' or 'nrg')
            'maxthr': 0.1,                                 # Max threshold
            'nrgthr': 0.9999,                              # Energy threshold
            # Flag to extract connected components (might want to turn to False for dendritic imaging)
            'extract_cc': True,
            # Morphological closing structuring element
            'se': None,
            # Binary element for determining connectivity
            'ss': None,
            'expandCore': None,
            'normalize_yyt_one': True,
            'block_size': block_size,
            'num_blocks_per_run': num_blocks_per_run,
            'nb': nb,                                      # number of background components
            # 'nnls_L0'. Nonnegative least square with L0 penalty
            'method_ls': 'lasso_lars',
            #'lasso_lars' lasso lars function from scikit learn
            #'lasso_lars_old' lasso lars from old implementation, will be deprecated
            # whether to update the background components in the spatial phase
            'update_background_components': update_background_components,
        }

        self.temporal = {
            'ITER': 2,                   # block coordinate descent iterations
            # method for solving the constrained deconvolution problem ('oasis','cvx' or 'cvxpy')
            'method': method_deconvolution,  # 'cvxpy', # 'oasis'
            # if method cvxpy, primary and secondary (if problem unfeasible for approx
            # solution) solvers to be used with cvxpy, can be 'ECOS','SCS' or 'CVXOPT'
            'solvers': ['ECOS', 'SCS'],
            'p': p,                      # order of AR indicator dynamics
            'memory_efficient': False,
            'num_blocks_per_run': num_blocks_per_run,
            # flag for setting non-negative baseline (otherwise b >= min(y))
            'bas_nonneg': False,
            # range of normalized frequencies over which to average
            'noise_range': [.25, .5],
            # averaging method ('mean','median','logmexp')
            'noise_method': 'mean',
            # number of autocovariance lags to be considered for time constant estimation
            'lags': 5,
            # bias correction factor (between 0 and 1, close to 1)
            'fudge_factor': .96,
            'nb': nb,                   # number of background components
            'verbosity': False,
            # number of pixels to process at the same time for dot product. Make it
            # smaller if memory problems
            'block_size': block_size,
            's_min': s_min,  # minimum spike threshold
        }
        self.merging = {
            'do_merge': do_merge,
            'thr': thr,
        }
        self.quality = {
            'decay_time': decay_time,  # length of decay of typical transient (in seconds)
            'min_SNR': min_SNR,  # transient SNR threshold
            'SNR_lowest': 0.5,  # minimum accepted SNR value
            'rval_thr': rval_thr,  # space correlation threshold
            'rval_lowest': -1,  # minimum accepted space correlation
            'fr': fr,  # imaging frame rate
            'use_cnn': True,  # use CNN based classifier
            'min_cnn_thr': 0.9,  # threshold for CNN classifier
            'cnn_lowest': 0.1,  # minimum accepted value for CNN classifier
            'gSig_range': None  # range for gSig scale for CNN classifier
        }
        self.online = {
            'expected_comps': 500,  # number of expected components
            'min_SNR': min_SNR,  # minimum SNR for accepting a new trace
            'N_samples_exceptionality': N_samples_exceptionality,  # timesteps to compute SNR
            'thresh_fitness_raw': None,  # threshold for trace SNR (computed below)
            'rval_thr': rval_thr,  # space correlation threshold
            'use_dense': use_dense,  # flag for representation and storing of A and b
            'max_num_added': max_num_added,  # maximum number of new components for each frame
            'min_num_trial': min_num_trial,  # number of mew possible components for each frame
            'path_to_model': os.path.join(caiman_datadir(), 'model',
                                          'cnn_model_online.h5'),
                                          # path to CNN model for testing new comps
            'sniper_mode': True,  # flag for using CNN
            'use_peak_max': False,  # flag for finding candidate centroids
            'use_both': False,  # flag for using both CNN and space correlation
            'init_batch': 200,  # length of mini batch for initialization
            'simultaneously': simultaneously,  # demix and deconvolve simultaneously
            'n_refit': n_refit,  # Additional iterations to simultaneously refit
            'thresh_CNN_noisy': thresh_CNN_noisy,  # threshold for online CNN classifier
            'epochs': 1,  # number of epochs
            'ds_factor': 1,  # spatial downsampling for faster processing
            'motion_correct': True,  # flag for motion correction
            'max_shifts': 10,  # maximum shifts during motion correction
            'minibatch_shape': minibatch_shape,  # number of frames in each minibatch
            'minibatch_suff_stat': minibatch_suff_stat,
            'update_num_comps': True,  # flag for searching for new components
            'init_method': 'bare',  # initialization method for first batch,
            'thresh_fitness_delta': thresh_fitness_delta,
            'thresh_overlap': thresh_overlap,
            'num_times_comp_updated': num_times_comp_updated,
            'max_comp_update_shape': max_comp_update_shape,
            'batch_update_suff_stat': batch_update_suff_stat
        }
        if N_samples_exceptionality is None:
            self.online['N_samples_exceptionality'] = np.ceil(fr*decay_time).astype('int')
        if thresh_fitness_raw is None:
            self.online['thresh_fitness_raw'] = scipy.special.log_ndtr(-self.online['min_SNR']) * self.online['N_samples_exceptionality']
        else:
            self.online['thresh_fitness_raw'] = thresh_fitness_raw
        self.online['max_shifts'] = np.int(self.online['max_shifts']/self.online['ds_factor'])

    def set(self, group, val_dict, set_if_not_exists=False):
        """ Add key-value pairs to a group. Existing key-value pairs will be overwritten if specified in val_dict,
            but not deleted.

        Args:
            group: The name of the group.
            val_dict: A dictionary with key-value pairs to be set for the group.
            set_if_not_exists: Whether to set a key-value pair in a group if the key does not currently exist in the group.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {}'.format(group))

        d = getattr(self, group)
        for k,v in val_dict.items():
            if k not in d and not set_if_not_exists:
                logging.warning("NOT setting value of key {} in group {}, because no prior key existed...".format(k, group))
            else:
                d[k] = v

    def get(self, group, key):
        """ Get a value for a given group and key. Raises an exception if no such group/key combination exists.

        Args:
            group: The name of the group.
            key: The key for the property in the group of interest.

        Returns: The value for the group/key combination.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {}'.format(group))

        d = getattr(self, group)
        if key not in d:
            raise KeyError('No key {} in group {}'.format(key, group))

        return d[key]

    def get_group(self, group):
        """ Get the dictionary of key-value pairs for a group.

        Args:
            group: The name of the group.
        """

        if not hasattr(self, group):
            raise KeyError('No group in CNMFParams named {}'.format(group))

        return getattr(self, group)

    def __eq__(self, other):

        if type(other) != CNMFParams:
            return False

        parent_dict1 = self.to_dict()
        parent_dict2 = other.to_dict()

        key_diff = np.setdiff1d(parent_dict1.keys(), parent_dict2.keys())
        if len(key_diff) > 0:
            return False

        for k1,child_dict1 in parent_dict1.items():
            child_dict2 = parent_dict2[k1]
            added, removed, modified, same = dict_compare(child_dict1, child_dict2)
            if len(added) != 0 or len(removed) != 0 or len(modified) != 0 or len(same) != len(child_dict1):
                return False

        return True

    def to_dict(self):
        return {'spatial_params':self.spatial, 'temporal_params':self.temporal,
                'init_params':self.init, 'preprocess_params':self.preprocess,
                'patch_params':self.patch, 'online':self.online, 'quality':self.quality,
                'merging':self.merging
        }