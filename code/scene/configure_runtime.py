"""Run with the Python environment holding requirements-advanced.txt. No refitting."""
from pathlib import Path
import json,sys,os,shutil
root=Path(__file__).resolve().parents[2]
for name,folder in [('scene_model.mat','development'),('advanced_models.joblib','advanced')]:
 source=root/'data/scene_models'/name;target=root/'data/local/scene'/folder/name
 if source.is_file():
  target.parent.mkdir(parents=True,exist_ok=True)
  if not target.exists():shutil.copy2(source,target)
p=root/'data/local/scene/advanced/runtime.json';p.parent.mkdir(parents=True,exist_ok=True)
p.write_text(json.dumps({'python':sys.executable,'pythonpath':os.environ.get('PYTHONPATH','')},indent=2))
print('Configured',p)
