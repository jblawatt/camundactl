from pathlib import Path
from os import sep as SLASH
import mkdocs_gen_files

src_root = Path("camundactl")
api_doc_tree = []
for path in src_root.glob("**/*.py"):
    doc_path = Path("api_doc", path.relative_to(src_root)).with_suffix(".md")

    with mkdocs_gen_files.open(doc_path, "w") as f:
        print("[TOC]", file=f)
        ident = ".".join(path.with_suffix("").parts)
        print("::: " + ident, file=f)
    api_doc_tree.append(path.relative_to(src_root))

with mkdocs_gen_files.open("api_doc.md", "w") as f:
    # assumes files in api_doc_tree to be ordered by directory
    already_used = []
    for doc_path in api_doc_tree:
        markdown_file = Path(doc_path).with_suffix('.md')
        levels = str(markdown_file).count(SLASH)
        if levels <= 0 and src_root not in already_used:
            print(f"{src_root}\n\n", file=f)
            already_used.append(src_root)
        elif levels >= 1:
            file_path = str(markdown_file).split(SLASH)
            directory_path = file_path[:-1]
            module_name = file_path[levels-1:levels][0]
            if directory_path not in already_used:
                print(f"{'    ' * (levels - 1)}- {module_name}", file=f)
                already_used.append(directory_path)
        file_name = str(doc_path).split(SLASH)[-1:][0]
        print(f"{'    ' * levels}- [{file_name}]({Path('api_doc', markdown_file)})", file=f)