# This is a centralized module (within this package) where other modules can
#  obtain selected path information and default filepaths.

import os.path

code_dir = os.path.dirname(os.path.realpath(__file__))
package_dir = os.path.abspath(os.path.join(code_dir, "..", "..", ".."))
package_ancillary_data_dir = os.path.abspath(os.path.join(package_dir,
                                                          "dist", "ancillary"))

scipkg_version_fpath = os.path.join(package_dir, "VERSION.txt")

_possible_modes = [0, 1, 2, 51, 52]

tmp_fpaths = [os.path.join(package_dir, "dist",
             "prdgit_version_m{}.txt".format(str(x))) for x in _possible_modes]
scipkg_prdgitv_fpaths = {}
for mode, fpath in zip(_possible_modes, tmp_fpaths):
    scipkg_prdgitv_fpaths[mode] = fpath
