import os
import io
import paramiko

from paramiko.pkey import base64

server = "sftp.pmel.noaa.gov"
username = "ncei_sftp"
# path_to_ssh = os.path.join("/Users/kamb", ".ssh")
# path_to_hosts_file = os.path.join(path_to_ssh, "known_hosts")
# path_to_pkey_file = os.path.join(path_to_ssh, "ncei-key-rsa")

#

key_guts = os.environ.get("NCEI_SFTP_KEY")
host_key = os.environ.get("SFTP_HOST_KEY")

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
ssh.get_host_keys().add(hostname=server, keytype=key_type, key=keyObj)
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

try:
    ssh.connect(
        server,
        username=username,
        pkey=pkey,
        look_for_keys=False,
        disabled_algorithms={"pubkeys": ["rsa-sha2-512", "rsa-sha2-256"]},
    )
except:
    print("STFP server appears to be down!!!")
