"""
Determine product monikers and current (latest) git hashes that are part
of the provenance of this package's products ('0-*'); write to file.

This program requires python version 3.6 or later, and is importable as a 
python module.
"""

  # From the Python standard library:
import os
import sys
import argparse
import subprocess
import importlib

  # From other external Python packages:

  # Custom utilities:


# *This* package must be first in the tuple of packages below:
Pypackages_to_query = ("PREFIRE_L0", "PREFIRE_tools")

product_monikers = {1:"0P-TPLD", 2:"0P-TBUS",
                    0:"0C-TPLD", 51:"0S-IPLD", 52:"0S-TBUS"}


#--------------------------------------------------------------------------
def main(anchor_path, proc_mode):
    """Driver routine."""

    this_sourcedir = os.path.join(anchor_path, "..", "source", "python")
    sys.path.append(this_sourcedir)

    this_environ = os.environ.copy()

    product_moniker = product_monikers[proc_mode]

    # Build up string of product/algorithm monikers and git hash strings:
    git_cmd1 = ["git", "rev-parse", "--short=8", "--verify", "HEAD"]
    git_cmd2 = ["git", "diff", "--quiet"]
    beg_dir = os.getcwd()
    pg_pieces = [product_moniker, '(']
    initial_pass = True
    pkg = []
    chk_PCRTM_rootdir, PCRTM_rootdir = (None, None)
    for pkg_name in Pypackages_to_query:
        if not initial_pass:
            pg_pieces.append('+')
        not_PREFIRE_PCRTM = ("PREFIRE_PCRTM" not in pkg_name)

        if not_PREFIRE_PCRTM:
            # Import this package, save resulting object in list:
            pkg.append(importlib.import_module(pkg_name))

            # Read in algorithm moniker:
            with open(pkg[-1].filepaths.scipkg_version_fpath, 'r') as in_f:
                line = in_f.readline()
                pg_pieces.append(line.split()[0])

            pkg_dir = pkg[-1].filepaths.package_dir
        else:
            pkg_dir = os.path.join(this_sourcedir, pkg_name)
            with open(os.path.join(pkg_dir, "include",
                                   "build_provenance.txt")) as bp:
                line_tokens = bp.readline().split()
                pg_pieces.append(line_tokens[0].strip())
                PCRTM_prov = line_tokens[1].strip()
                PCRTM_rootdir = os.path.dirname(line_tokens[2].strip())

        # Set output filepath (for *this* package):
        if initial_pass:
            try:
                output_fpath = pkg[-1].filepaths.scipkg_prdgitv_fpath
            except:
                output_fpath = (
                            pkg[-1].filepaths.scipkg_prdgitv_fpaths[proc_mode])
            initial_pass = False

        # Get latest commit hash, other provenance info, and/or perform checks:
        os.chdir(pkg_dir)
        modstr = ''                # Default if git and/or .git/ are not
        commit_abbrev = "unknown"  #  present/working
        if not_PREFIRE_PCRTM:
            if "pyPCRTM" in pkg_name:
                with open(os.path.join("data",
                                       "build_provenance.txt"), 'r') as bp:
                    line_tokens = bp.readline().split()
                    chk_PCRTM_prov = line_tokens[3].strip()
                    chk_PCRTM_rootdir = line_tokens[1].strip()

            try:
                cproc = subprocess.run(git_cmd1, stdout=subprocess.PIPE)
                commit_abbrev = cproc.stdout.decode().strip()
                cproc = subprocess.run(git_cmd2, stdout=subprocess.PIPE)
                if cproc.returncode != 0:
                    modstr = "(modified)"
            except:  # git and/or .git/ are not present/working
                pass  # Use default values
        else:
            commit_abbrev = PCRTM_prov
        pg_pieces.append(commit_abbrev+modstr)

        if (chk_PCRTM_rootdir is not None) and (PCRTM_rootdir is not None):
            e_msg = None
            if chk_PCRTM_prov != PCRTM_prov:
                e_msg = ("ERROR: pyPCRTM was built with PCRTM {}, which does "
                         "not match PCRTM {} that is provided in "
                         "source/".format(chk_PCRTM_prov, PCRTM_prov))
            if chk_PCRTM_rootdir != PCRTM_rootdir:
                e_msg = ("ERROR: pyPCRTM was built with PCRTM from {}, which "
                         "does not match PCRTM from {} that is provided in "
                         "source/".format(chk_PCRTM_rootdir, PCRTM_rootdir))
            if e_msg is not None:
                raise ValueError(e_msg)
        os.chdir(beg_dir)

    # Assemble output string and write to a file:
    pg_pieces.append(')')
    with open(output_fpath, 'w') as out_f:
        text_to_write = ' '.join(pg_pieces) + '\n'
        out_f.write(text_to_write)


if __name__ == "__main__":
    # Determine fully-qualified filesystem location of this script:
    anchor_path = os.path.abspath(os.path.dirname(sys.argv[0]))

    # Process arguments:
    arg_description = ("Determine product monikers and current (latest) git "
                       "hashes that are part of the provenance of this "
                       "package's products ('0-*'); write to "
                       "file.")
    arg_parser = argparse.ArgumentParser(description=arg_description)

    args = arg_parser.parse_args()

    proc_mode = int(os.environ["PROC_MODE"])

    # Run driver:
    main(anchor_path, proc_mode)
