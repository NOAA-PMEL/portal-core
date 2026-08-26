import os
import portal_core.sftp.sftp_init as sftp_init

def mkdir_p(sftp, remote_directory):
    """Change to this directory, recursively making new folders if needed.
    Returns True if any folders were created."""
    if remote_directory == '/':
        # absolute path so change directory to root
        sftp.chdir('/')
        return
    if remote_directory == '':
        # top-level relative directory must exist
        return
    try:
        sftp.chdir(remote_directory) # sub-directory exists
    except IOError:
        dirname, basename = os.path.split(remote_directory.rstrip('/'))
        mkdir_p(sftp, dirname) # make parent directories
        sftp.mkdir(basename) # sub-directory missing, so created it
        sftp.chdir(basename)
        return True


def send_bag(bag, dashboard_user, data_submitter, submission_id):
    full_bag = os.path.abspath(bag)
    sftp = sftp_init.ssh.open_sftp()
    bag_name = os.path.basename(bag)
    remote_path = os.path.join("/data/data_submit", dashboard_user, data_submitter, str(submission_id))
    p = mkdir_p(sftp, remote_path)
    remote_file = os.path.join("/data/data_submit", dashboard_user, data_submitter, str(submission_id), bag_name)
    if p:
        print('Made path', p)
    try:
        # DEBUG print('local dir', full_bag)
        # DEBUG print('remote dir', sftp.getcwd())
        # DEBUG print('remote file', remote_file)
        sftp.put(full_bag, remote_file) # At this point, you are in remote_path
    except Exception as e:
        print('sftp failed', e)
        raise Exception('SFTP failed.') from e
    finally:
        sftp.close()


def put(in_file, out_file):
    sftp = sftp_init.ssh.open_sftp()
    try:
        sftp.put(in_file, out_file) # At this point, you are in remote_path
    except Exception as e:
        print('sftp failed', e)
        raise Exception('SFTP failed.') from e
    finally:
        sftp.close()