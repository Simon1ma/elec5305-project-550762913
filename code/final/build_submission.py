"""Build and verify the three-item final-project submission archive."""

from pathlib import Path
import hashlib
import zipfile

ROOT = Path(__file__).resolve().parents[2]
FINAL = ROOT / 'submissions/Final_Project_Submission.zip'
REPORT = ROOT / 'output/pdf/Final_Project_Yixiang_Ma.pdf'
VIDEO = ROOT / 'submissions/Final_Project_Demo.mp4'
REPO_URL = 'https://github.com/Simon1ma/elec5305-project-550762913'
RUN_URL = REPO_URL + '/blob/main/code/final/README.md'
LINK_NAME = 'GitHub_Code_Link.txt'


def main():
    assert REPORT.is_file() and VIDEO.is_file()
    link_text = f'GitHub source code: {REPO_URL}\nRun instructions: {RUN_URL}\n'
    expected = [LINK_NAME, REPORT.name, VIDEO.name]
    original_hashes = {
        REPORT.name: hashlib.sha256(REPORT.read_bytes()).hexdigest(),
        VIDEO.name: hashlib.sha256(VIDEO.read_bytes()).hexdigest(),
    }

    FINAL.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(FINAL, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr(LINK_NAME, link_text)
        archive.write(REPORT, REPORT.name)
        archive.write(VIDEO, VIDEO.name)

    with zipfile.ZipFile(FINAL) as archive:
        assert archive.namelist() == expected
        assert archive.testzip() is None
        assert archive.read(LINK_NAME).decode('utf-8') == link_text
        for name, digest in original_hashes.items():
            assert hashlib.sha256(archive.read(name)).hexdigest() == digest

    print('PASS: exactly three files;', FINAL.stat().st_size, 'bytes;', FINAL)


if __name__ == '__main__':
    main()
