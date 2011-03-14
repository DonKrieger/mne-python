"""
===============================================================
Non-parametric 1 sample cluster statistic on single trial power
===============================================================

This script shows how to estimate significant clusters
in time-frequency power estimates. It uses a non-parametric
statistical procedure based on permutations and cluster
level statistics.

The procedure consists in :
- extracting epochs
- compute single trial power estimates
- baseline line correct the power estimates (power ratios)
- compute stats to see if ratio deviates from 1.

"""
# Authors: Alexandre Gramfort <gramfort@nmr.mgh.harvard.edu>
#
# License: BSD (3-clause)

print __doc__

import numpy as np

import mne
from mne import fiff
from mne.time_frequency import single_trial_power
from mne.stats import permutation_cluster_t_test
from mne.datasets import sample

###############################################################################
# Set parameters
data_path = sample.data_path('..')
raw_fname = data_path + '/MEG/sample/sample_audvis_raw.fif'
event_fname = data_path + '/MEG/sample/sample_audvis_raw-eve.fif'
event_id = 1
tmin = -0.2
tmax = 0.5

# Setup for reading the raw data
raw = fiff.Raw(raw_fname)
events = mne.read_events(event_fname)

include = []
exclude = raw.info['bads'] + ['MEG 2443', 'EEG 053'] # bads + 2 more

# picks MEG gradiometers
picks = fiff.pick_types(raw.info, meg='grad', eeg=False,
                                stim=False, include=include, exclude=exclude)

picks = [picks[97]]
ch_name = raw.info['ch_names'][picks[0]]

# Load condition 1
event_id = 1
epochs = mne.Epochs(raw, events, event_id,
                    tmin, tmax, picks=picks, baseline=(None, 0))
data = epochs.get_data() # as 3D matrix
data *= 1e13 # change unit to fT / cm

# Time vector
times = 1e3 * epochs.times # change unit to ms

frequencies = np.arange(7, 30, 3) # define frequencies of interest
Fs = raw.info['sfreq'] # sampling in Hz
epochs_power = single_trial_power(data, Fs=Fs,
                                   frequencies=frequencies,
                                   n_cycles=3, use_fft=False)

epochs_power = epochs_power[:,0,:,:] # only 1 channel to get a 3D matrix
# do ratio with baseline power:
epochs_power /= np.mean(epochs_power[:,:,times < 0], axis=2)[:,:,None]
# null hypothesis is that the ratio is 1 (set it to 0 for stats below)
epochs_power -= 1.0
                                   ###############################################################################
# Compute statistic
threshold = 6.0
T_obs, clusters, cluster_p_values, H0 = \
                   permutation_cluster_t_test(epochs_power,
                               n_permutations=100, threshold=threshold, tail=0)

###############################################################################
# View time-frequency plots
import pylab as pl
pl.clf()
pl.subplots_adjust(0.12, 0.08, 0.96, 0.94, 0.2, 0.43)
pl.subplot(2, 1, 1)
evoked_data = np.mean(data, 0)
pl.plot(times, evoked_data.T)
pl.title('Evoked response (%s)' % ch_name)
pl.xlabel('time (ms)')
pl.ylabel('Magnetic Field (fT/cm)')
pl.xlim(times[0], times[-1])
pl.ylim(-100, 200)

pl.subplot(2, 1, 2)

# Create new stats image with only significant clusters
T_obs_plot = np.nan * np.ones_like(T_obs)
for c, p_val in zip(clusters, cluster_p_values):
    if p_val <= 0.05:
        T_obs_plot[c] = T_obs[c]

pl.imshow(T_obs, cmap=pl.cm.gray, extent=[times[0], times[-1],
                                          frequencies[0], frequencies[-1]],
                                  aspect='auto', origin='lower')
pl.imshow(T_obs_plot, cmap=pl.cm.jet, extent=[times[0], times[-1],
                                          frequencies[0], frequencies[-1]],
                                  aspect='auto', origin='lower')

pl.xlabel('time (ms)')
pl.ylabel('Frequency (Hz)')
pl.title('Induced power (%s)' % ch_name)
pl.show()