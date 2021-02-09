import re
import subprocess
from pathlib import Path

document_class = '\\documentclass'
begin_document = '\\begin{document}\n'
end_document = '\\end{document}\n'

init_file = '__init__.tex'
main_file = '__main__.tex'
preamble_file = '__preamble__.tex'


class TexFile:
    def __init__(self, path: Path):
        self.path = path
        self.preamble = []
        self.document = []
        self.magic_comment = []
        return

    def exists(self) -> bool:
        return self.path.is_file()

    def exists_dir(self) -> bool:
        return self.path.parent.is_dir()

    def copy(self, out=None) -> 'TexFile':
        if out is None:
            out = self.path
        tex_file = TexFile(out)
        tex_file.preamble = self.preamble.copy()
        tex_file.document = self.document.copy()
        return tex_file

    def read_for_preamble(self):
        self.clear_preamble()
        if not self.exists():
            return self
        with self.path.open(mode='r') as file:
            lines = self.__read(file)
        self.preamble = lines
        return self

    def read_for_document(self):
        self.clear_document()
        if not self.exists():
            return self
        with self.path.open(mode='r') as file:
            lines = self.__read(file)
        self.document = lines
        return self

    @staticmethod
    def __read(src_lines: list) -> list:
        lines = []
        for line in src_lines:
            # comment skip
            if line.strip().startswith('%'):
                continue
            lines.append(line)
        return lines

    def extend_preamble(self, src: 'TexFile') -> 'TexFile':
        self.preamble.extend(src.preamble)
        return self

    def extend_document(self, src: 'TexFile') -> 'TexFile':
        self.document.extend(src.document)
        return self

    def __add__(self, other: 'TexFile') -> 'TexFile':
        return self.extend_preamble(other).extend_document(other)

    def append_preamble(self, src_line: str) -> 'TexFile':
        self.preamble.append(src_line)
        return self

    def append_document(self, src_line: str) -> 'TexFile':
        self.document.append(src_line)
        return self

    def __input(self, line) -> 'TexFile':
        path = re.search(r'\\input{(.*)}', line).group(1)
        return TexFile(self.path.parent / Path(path))

    def build_preamble(self) -> 'TexFile':
        tex_file = self.copy()
        tex_file.preamble = []
        for line in self.preamble:
            # \input{}
            if r'\input' in line:
                tex_input_file = tex_file.__input(line).read_for_preamble()
                tex_file.extend_preamble(tex_input_file.build_preamble())
            else:
                tex_file.append_preamble(line)
        return tex_file

    def build_document(self) -> 'TexFile':
        tex_file = self.copy()
        tex_file.document = []
        for line in self.document:
            # \input
            if r'\input' in line:
                tex_input_file = tex_file.__input(line).read_for_document()
                tex_file.extend_document(tex_input_file.build_document())
            # 相互参照のサポートも追加したい
            else:
                tex_file.append_document(line)
        return tex_file

    # def build(self, out) -> 'TexFile':
    #     return (self
    #             .build_preamble()
    #             .build_document()
    #             .copy(out)
    #             )

    def clear_preamble(self):
        self.preamble = []
        return self

    def clear_document(self):
        self.document = []
        return self

    def write(self):
        # ディレクトリがなければ作成する
        if not self.exists_dir():
            self.path.parent.mkdir(parents=True)
        lines = []
        lines.extend(self.preamble)
        lines.append(begin_document)
        lines.extend(self.document)
        lines.append(end_document)
        with self.path.open(mode='w') as file:
            for line in lines:
                file.write(line)
        return


class LatexSection:
    def __init__(self, path: Path):
        self.path = path
        self.init = self.path / Path(init_file)
        self.main = self.path / Path(main_file)
        self.tex_path = path.parent / Path(path.stem + '.tex')


class LatexProject:
    def __init__(self, root: Path):
        self.root = root
        self.source = self.root / Path('src')
        self.out = self.root / Path('out')
        self.preamble = self.root / Path(preamble_file)

    def __relative_to(self, path: Path) -> Path:
        return path.relative_to(self.source)

    def __out_path(self, path: Path) -> Path:
        return self.out / self.__relative_to(path)

    # def build_preamble(self, src_path):
    #     src = TexFile(src_path)
    #     out_path = self.root / Path('etc/__preamble__.tex')
    #     if out_path.is_file():
    #         return
    #     src.read_for_preamble().build(out_path).write()
    #     return

    def build_init(self, section: LatexSection) -> Path:
        section_init = (TexFile(self.preamble)
                        .read_for_preamble()
                        .append_document('\\input{' + main_file + '}\n')
                        .copy(section.init)
                        )
        section_init.write()
        return section_init.path

    def build_main(self, section: LatexSection) -> Path:
        preamble = TexFile(self.preamble).read_for_preamble()
        section_main = TexFile(section.main).read_for_document().build_document()
        out_section_main = (preamble + section_main).copy(self.__out_path(section.tex_path))
        out_section_main.write()
        return out_section_main.path
