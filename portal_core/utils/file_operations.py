"""
Helper functions for file operations
"""
import hashlib
import os
import shutil
import base64
from datetime import datetime
from pathlib import Path

UPLOAD_DIRECTORY = os.environ.get("UPLOAD_DIRECTORY")
ARCHIVE_DIRECTORY = os.environ.get("ARCHIVE_DIRECTORY")

# Helper function to compute hash
# https://stackoverflow.com/questions/22058048/hashing-a-file-in-python
def sha256sum(filename):
    h = hashlib.sha256()
    b = bytearray(128 * 1024)
    mv = memoryview(b)
    with open(filename, "rb", buffering=0) as f:
        while n := f.readinto(mv):
            h.update(mv[:n])
    return h.hexdigest()

def archive_file(file_name, dashboard_user, sid):
    to_move = os.path.join(UPLOAD_DIRECTORY, str(sid), file_name)
    destination = os.path.join(
        ARCHIVE_DIRECTORY,
        str(sid),
        file_name + "." + datetime.now().isoformat(),
    )
    Path(ARCHIVE_DIRECTORY, str(sid)).mkdir(
        parents=True, exist_ok=True
    )
    shutil.move(to_move, destination)


def save_file(submission_id, contents, filename):
    data = contents.encode("utf8").split(b";base64,")[1]
    with open(
        os.path.join(UPLOAD_DIRECTORY, str(submission_id), filename), "wb"
    ) as fp:
        fp.write(base64.decodebytes(data))
