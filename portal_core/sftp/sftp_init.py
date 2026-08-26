import os
import io
import paramiko

from paramiko.pkey import base64

SERVER = "sftp.pmel.noaa.gov"
USERNAME = "ncei_sftp"

_ssh = None

def get_ssh():
    """
    Connect to the NCEI SFTP server, once per process.

    Deliberately not done at import: base is a libary, and importing must
    not require credentials or reach the network.
    """
    global _ssh
    if _ssh is not None:
        return _ssh

    key_guts = os.environ.get("NCEI_SFTP_KEY")
    host_key = os.environ.get("SFTP_HOST_KEY")
    if not key_guts or not host_key:
        raise RuntimeError(
            "NCEI_SFTP_KEY and SFTP_HOST_KEY must be set to use SFTP transfer."
        )

    key_string = f"""\
    -----BEGIN OPENSSH PRIVATE KEY----- 
    {key_guts}
    -----END OPENSSH PRIVATE KEY-----
    """

    pkey = paramiko.Ed25519Key.from_private_key(io.StringIO(key_string))
    ssh = paramiko.SSHClient()

    key_type, key_data = host_key.split(maxsplit=1)
    keyObj = paramiko.PKey.from_type_string(key_type, base64.decodebytes(key_data.encode()))

    # add to host keys
    ssh.get_host_keys().add(
        hostname=SERVER, 
        keytype=key_type, 
        key=keyObj
        )
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    ssh.connect(
        SERVER,
        username=USERNAME,
        pkey=pkey,
        look_for_keys=False,
        disabled_algorithms={"pubkeys": ["rsa-sha2-512", "rsa-sha2-256"]},
    )

    _ssh = ssh
    return _ssh
