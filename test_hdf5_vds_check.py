# coding: utf-8
from pathlib import Path

import h5py
import numpy as np

import hdf5_vds_check

def test_check_file(tmp_path):
    filename = str(tmp_path / 'test.h5')

    noaccess = (tmp_path / 'noaccess.h5')
    noaccess.touch()
    noaccess.chmod(0)

    with h5py.File(filename, 'w') as f:
        f['exists'] = np.arange(10, dtype=np.float32)

        layout = h5py.VirtualLayout((10, 10), np.float32)

        # 0: valid, accessible mapping
        layout[0] = h5py.VirtualSource('test.h5', 'exists', (10,))
        # 1: file exists, but dataset doesn't
        layout[1] = h5py.VirtualSource('test.h5', 'nonexists', (10,))
        # 2: file doesn't exist
        layout[2] = h5py.VirtualSource('testnothere.h5', 'nonexists', (10,))
        # 3: file exists, but don't have read permission
        layout[3] = h5py.VirtualSource('noaccess.h5', 'blah', (10,))
        # 4: valid, using . to refer to the same file
        layout[4] = h5py.VirtualSource('.', 'exists', (10,))
        # 5: valid (if weird): the basename is tried when an absolute path doesn't exist
        layout[5] = h5py.VirtualSource("/nonexistant/path/test.h5", 'exists', (10,))
        # 6: file doesn't exist (absolute path)
        layout[2] = h5py.VirtualSource('/nonexistant/path/testnothere.h5', 'nonexists', (10,))

        f.create_virtual_dataset('vds', layout)

    assert hdf5_vds_check.check_file(Path(filename)) == 4  # n inaccessible sources
