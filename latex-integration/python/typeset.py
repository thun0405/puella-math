import os
import subprocess
import sys
from pathlib import Path

import latex


def main(src):
    src_path = Path(src)
    root_path = get_project_root(src_path)

    project = latex.LatexProject(root_path)
    section = latex.LatexSection(src_path)

    out_path = project.build_main(section)
    latexmk(out_path)

    print('Typeset, done.')
    return


def get_project_root(path: Path) -> Path:
    parents = path.parents
    for parent in parents:
        if 'src' in parent.name:
            return parent.parent
    raise Exception('Path is not under a project.')


def latexmk(path: Path):
    src = str(path)
    out_dir = '-output-directory=' + str(path.parent)
    rc_file = '../etc/latexmk/.latexmkrc'
    cmd = ['latexmk', '-pv', '-r', rc_file, out_dir, src]
    cp = subprocess.run(cmd, encoding='utf-8', stderr=subprocess.PIPE)
    print(cp.stderr)


if __name__ == '__main__':
    args = sys.argv
    main(args[1])
