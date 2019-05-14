# hdf5-vds-check

Check access to the source files of virtual datasets

When you read a virtual dataset, HDF5 will skip over source files it can't open,
giving you the virtual dataset's fill value instead.
It's not obvious whether you have a permissions problem, a missing file, or
a genuinely empty part of the dataset.

This tool checks all virtual datasets in a file to alerts you to any
problems opening the source files.

## Install

    pip install hdf5_vds_check

## Usage

    hdf5-vds-check file_with_virtual_datasets.h5

If any sources for virtual datasets can't be accessed, it will list details of
these, and then exit with status 1.
