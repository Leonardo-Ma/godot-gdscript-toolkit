"""GDScript code metrics calculator

Experimental tool which converts GDScript code to Python and runs radon tool on it.

Usage:
  gdradon cc <path>... [options]

Options:
  -h --help                  Show this screen.
  --version                  Show version.
  --max-complexity=<value>   Fail when complexity exceeds value.

Examples:
  gdradon cc file1.gd file2.gd path/
"""
import sys
from typing import List
from importlib.metadata import version as pkg_version

from docopt import docopt
from radon.complexity import cc_rank, cc_visit
from radon.visitors import Function
from radon.cli.colors import LETTERS_COLORS, RANKS_COLORS, RESET

from gdtoolkit.common.utils import find_gd_files_from_paths
from gdtoolkit.gd2py import convert_code

Path = str


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    arguments = docopt(
        __doc__,
        version="gdradon {}".format(pkg_version("gdtoolkit")),
    )

    max_complexity = arguments["--max-complexity"]
    threshold = int(max_complexity) if max_complexity is not None else None

    files: List[Path] = find_gd_files_from_paths(arguments["<path>"])
    failed = False

    for file_path in files:
        if not _cc(file_path, threshold):
            failed = True

    if failed:
        sys.exit(1)



def _cc(file_path: str, max_complexity: int = None) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8") as handle:
            python_code = convert_code(handle.read())
            results = cc_visit(python_code)
            if not results:
                return True

            violations = []

            for result in results:
                if (
                    max_complexity is not None
                    and result.complexity > max_complexity
                ):
                    violations.append(result)

            if not violations:
                return True

            print(file_path)
            for result in violations:
                letter = "F" if isinstance(result, Function) else "C"
                rank = cc_rank(result.complexity)

                print(
                    "    {}{}{} {}:{} {} - {}{} ({}){}".format(
                        LETTERS_COLORS[letter],
                        letter,
                        RESET,
                        result.lineno,
                        result.col_offset,
                        result.name,
                        RANKS_COLORS[rank],
                        rank,
                        result.complexity,
                        RESET,
                    )
                )

            return False
    except OSError as exception:
        print(
            "Cannot open file '{}': {}".format(file_path, exception.strerror),
            file=sys.stderr,
        )
        return False
    except Exception as exception:  # pylint: disable=broad-except
        print(
            "Cannot process file '{}' due to exception: {}".format(
                file_path, exception
            ),
            file=sys.stderr,
        )
        return False

