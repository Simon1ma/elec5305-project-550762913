"""Build one complete assessment ZIP. Private data inclusion is explicit and local."""
from pathlib import Path
import argparse, hashlib, json, zipfile
ROOT=Path(__file__).resolve().parents[2]
REPO='https://github.com/Simon1ma/elec5305-project-550762913'
def digest(path):
    with path.open('rb') as file:return hashlib.file_digest(file,'sha256').hexdigest()
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--output',type=Path,default=ROOT/'submissions/Final_Project_Submission.zip')
    parser.add_argument('--include-local',action='store_true')
    parser.add_argument('--local-data-root',type=Path,default=ROOT/'data/local')
    args=parser.parse_args();output=args.output.resolve();output.parent.mkdir(parents=True,exist_ok=True)
    report=ROOT/'output/pdf/Final_Project_Yixiang_Ma.pdf';video=ROOT/'submissions/Final_Project_Demo.mp4'
    assert report.is_file() and video.is_file()
    files={report.name:report,video.name:video}
    for folder in ['code','docs','results','data/demo_public','data/scene_models']:
        for path in (ROOT/folder).rglob('*'):
            if not path.is_file():continue
            rel=path.relative_to(ROOT)
            if any(part in ['__pycache__','tmp','demo_runtime'] for part in rel.parts) or path.suffix=='.pyc':continue
            files[str(Path('Code')/rel).replace('\\','/')]=path
    for name in ['START_PROJECT.m','check_submission.m','check_personal_submission.m','START_HERE_MATLAB.txt','README.md','index.md','.gitignore','.gitattributes']:
        files['Code/'+name]=ROOT/name
    if args.include_local:
        for folder in ['scene','scene_bridge','scene_adaptive']:
            source=args.local_data_root/folder;assert source.is_dir(),source
            for path in source.rglob('*'):
                if not path.is_file():continue
                rel=path.relative_to(args.local_data_root)
                if any(part in ['__pycache__','tmp','demo_runtime'] for part in rel.parts) or path.name=='runtime.json':continue
                files[str(Path('Code/data/local')/rel).replace('\\','/')]=path
        for name in ['deep-filter.exe','DeepFilterNet3_onnx.tar.gz']:
            source=args.local_data_root/'latency2'/name;assert source.is_file()
            files['Code/data/local/latency2/'+name]=source
    readme="""ELEC5305 Final Project - Yixiang Ma - SID 550762913
Revised 14 November 2026

This single ZIP includes the report, 181-second demonstration video, code link,
complete working source, public example, frozen models/features and result tables.

MATLAB: fully extract ZIP, set Current Folder to Code, run START_PROJECT.
Run START_PROJECT('check') for public-data numerical self-checks.
Requires Signal Processing Toolbox; tested on Windows 11 / MATLAB R2026a Update 5.
The public example requires no Python or further download. All four Wiener
methods are rerun; the DFNet3 quick-demo option plays explicitly saved output.

"""
    if args.include_local:
        readme+="""This assessment ZIP also includes the private personal recordings and all 27
mixtures/outputs. Run START_PROJECT('personal') for the full enhancement app,
START_PROJECT('personal_scene') for the 18-recording MATLAB centroid scene app,
and START_PROJECT('personal_check') for the 27-mixture numerical self-check.
Advanced MFCC classification requires Audio Toolbox and configured Python:
install the two requirement files described in Code/START_HERE_MATLAB.txt,
then run python code/scene/configure_runtime.py. No refitting is required.
The original personal files remain excluded from public GitHub.

"""
    readme+="""Public-corpus full evaluation downloads are documented in Code/code/final/README.md.
The project website and online report/video links are in GitHub_Code_Link.txt.
No second ZIP is required. AI assistance is acknowledged in the report.
"""
    links=f'GitHub code: {REPO}\nProject website: https://simon1ma.github.io/elec5305-project-550762913/\nRun instructions: {REPO}/blob/main/START_HERE_MATLAB.txt\nVideo: {REPO}/blob/main/submissions/Final_Project_Demo.mp4\n'
    evidence={'revision_date':'2026-11-14','private_personal_data_included':args.include_local,'report_sha256':digest(report),'video_sha256':digest(video),'file_count':len(files),'video_seconds':181}
    with zipfile.ZipFile(output,'w',zipfile.ZIP_DEFLATED,compresslevel=3,allowZip64=True) as archive:
        archive.writestr('README_START_HERE.txt',readme);archive.writestr('GitHub_Code_Link.txt',links)
        archive.writestr('VERIFICATION.json',json.dumps(evidence,indent=2)+'\n')
        for name,path in sorted(files.items()):archive.write(path,name)
    with zipfile.ZipFile(output) as archive:
        assert archive.testzip() is None
        assert archive.read(report.name)==report.read_bytes();assert archive.read(video.name)==video.read_bytes()
        assert 'Code/START_PROJECT.m' in archive.namelist()
        assert not any(name.endswith('.zip') for name in archive.namelist())
    output.with_suffix('.zip.sha256').write_text(digest(output)+'  '+output.name+'\n')
    print('PASS: one ZIP, report/video identity and CRC checks;',output,output.stat().st_size,'bytes',flush=True)
if __name__=='__main__':main()
