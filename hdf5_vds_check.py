"""Check access to the source files of virtual datasets

When you read a virtual dataset, HDF5 will skip over source files it can't open,
giving you the virtual dataset's fill value instead.
It's not obvious whether you have a permissions problem, a missing file, or
a genuinely empty part of the dataset.

This script checks all virtual datasets in a file to alerts you to any
problems opening the source files.
"""

import argparse
from collections import defaultdict
import h5py
import os
import sys

def print_problem(filename, details):
    print("  {}:".format(filename))
    print("    ", details)

def check_dataset(path, obj):
    print("Checking virtual dataset:", path)

    files_datasets = defaultdict(list)
    n_maps = 0
    for vmap in obj.virtual_sources():
        n_maps += 1
        files_datasets[vmap.file_name].append(vmap.dset_name)

    n_ok = 0
    for src_path, src_dsets in files_datasets.items():
        try:
            # stat() gives nicer error messages for missing files, so
            # try that first.
            os.stat(src_path)
            src_file = h5py.File(src_path, 'r')
        except Exception as e:
            print_problem(src_path, e)
            continue

        for src_dset in src_dsets:
            try:
                ds = src_file[src_dset]
            except KeyError:
                print_problem(src_path, "Missing dataset: {}".format(src_dset))
            else:
                if isinstance(ds, h5py.Dataset):
                    n_ok += 1
                else:
                    print_problem(src_path,
                                  "Not a dataset: {}".format(src_dset))
        src_file.close()

    print("  {}/{} sources accessible".format(n_ok, n_maps))
    print()
    return n_maps - n_ok  # i.e number of inaccessible mappings

def find_virtual_datasets(file: h5py.File):
    """Return a list of 2-tuples: (path in file, dataset)"""
    res = []

    def visit(path, obj):
        if isinstance(obj, h5py.Dataset) and obj.is_virtual:
            res.append((path, obj))

    file.visititems(visit)
    return sorted(res)


def check_file(filename):
    n_problems = 0

    with h5py.File(filename, 'r') as f:
        virtual_dsets = find_virtual_datasets(f)

        print(f"Found {len(virtual_dsets)} virtual datasets to check.")

        for path, ds in virtual_dsets:
            n_problems += check_dataset(path, ds)

    if not virtual_dsets:
        pass
    elif n_problems == 0:
        print("All virtual data sources accessible")
    else:
        print("ERROR: Access problems for virtual data sources")

    return n_problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('file', help="File containing virtual datasets to check")
    args = ap.parse_args(argv)

    n_problems = check_file(args.file)

    if n_problems > 0:
        return 1

if __name__ == '__main__':
    sys.exit(main())
