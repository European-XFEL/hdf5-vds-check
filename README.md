# hdf5-vds-check

Check access to the source files of virtual datasets

When you read a virtual dataset, HDF5 will skip over source files it can't open,
giving you the virtual dataset's fill value instead.
It's not obvious whether you have a permissions problem, a missing file, or
a genuinely empty part of the dataset.

This tool checks all virtual datasets in a file to alerts you to any
problems opening the source files.
