"""PyInstaller hook: exclude arcade/VERSION file to avoid dir/file conflict."""
from PyInstaller.utils.hooks import collect_data_files, copy_metadata

# Collect arcade data except the problematic VERSION file
datas = []
for src, dst in collect_data_files('arcade'):
    if 'VERSION' in src and not src.endswith('.py'):
        continue
    datas.append((src, dst))
