"""Check access to the source files of virtual datasets

When you read a virtual dataset, HDF5 will skip over source files it can't open,
giving you the virtual dataset's fill value instead.
It's not obvious whether you have a permissions problem, a missing file, or
a genuinely empty part of the dataset.

This script checks all virtual datasets in a file to alerts you to any
problems opening the source files.
"""

import argparse
import os
import sys
from collections import defaultdict
from pathlib import Path

import h5py

__version__ = '1.1'

def print_problem(filename, details):
    print("  {}:".format(filename))
    print("    ", details)

def resolve_source_file(src_file_name: str, vds_file: Path) -> Path:
    """Resolve the path for a VDS source file

    As described in the docs for H5Pset_virtual:
    https://support.hdfgroup.org/documentation/hdf5/latest/group___d_c_p_l.html#gadec895092dbbedb94f85d9cacf8924f5
    """
    if src_file_name == ".":
        return vds_file

    src_file_name = Path(src_file_name)
    if src_file_name.is_absolute():
        # If an absolute path is not found, the basename is tried as a relative
        # path instead. We're probably not handling all the different cases
        # on Windows correctly - I'm focusing on Linux.
        if not src_file_name.is_file():
            resolved = resolve_source_file(src_file_name.name, vds_file)
            if resolved.is_file():
                return resolved

        return src_file_name

    # In this path, we have a relative path to the source file

    if 'HDF5_VDS_PREFIX' in os.environ:
        prefixes = [Path(p) for p in os.environ['HDF5_VDS_PREFIX'].split(os.pathsep)]
    else:
        prefixes = []
    # By default, relative paths are from the folder containing the VDS file.
    prefixes.append(vds_file.parent)

    for prefix in prefixes:
        if (p := prefix / src_file_name).is_file():
            return p

    # Fallback: just use the relative path from the CWD
    return src_file_name



def check_dataset(path, obj, vds_file: Path):
    print("Checking virtual dataset:", path)

    files_datasets = defaultdict(list)
    n_maps = 0
    for vmap in obj.virtual_sources():
        n_maps += 1
        files_datasets[vmap.file_name].append(vmap.dset_name)

    n_ok = 0
    for src_path, src_dsets in files_datasets.items():
        try:
            resolved_path = resolve_source_file(src_path, vds_file)
            # stat() gives nicer error messages for missing files, so
            # try that first.
            os.stat(resolved_path)
            src_file = h5py.File(resolved_path, 'r')
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


def check_file(filename: Path):
    n_problems = 0

    with h5py.File(filename, 'r') as f:
        virtual_dsets = find_virtual_datasets(f)

        print(f"Found {len(virtual_dsets)} virtual datasets to check.")

        for path, ds in virtual_dsets:
            print("In check_file", type(filename))
            n_problems += check_dataset(path, ds, filename)

    if not virtual_dsets:
        pass
    elif n_problems == 0:
        print("All virtual data sources accessible")
    else:
        print("ERROR: Access problems for virtual data sources")

    return n_problems


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument('file', type=Path,
                    help="File containing virtual datasets to check")
    args = ap.parse_args(argv)

    n_problems = check_file(args.file)

    if n_problems > 0:
        return 1

if __name__ == '__main__':
    sys.exit(main())
