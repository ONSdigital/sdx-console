from console import app
import logging

import operator
from ftplib import FTP
from datetime import datetime
from structlog import wrap_logger

import console.settings as settings

logger = wrap_logger(logging.getLogger(__name__))


PATHS = {
    "pck": settings.SDX_FTP_DATA_PATH,
    "image": settings.SDX_FTP_IMAGE_PATH + "/Images",
    "index": settings.SDX_FTP_IMAGE_PATH + "/Index",
    "receipt": settings.SDX_FTP_RECEIPT_PATH,
    "json": settings.SDX_FTP_DATA_PATH
}


class ConsoleFtp(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._ftp.quit()

    def __init__(self):
        self._ftp = FTP(settings.FTP_PATH)
        self._ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)
        self._mlsd_enabled = True
        try:
            # Perform a simple mlsd test to see if the ftp server has the extra functionality:
            len([fname for fname, fmeta in self._ftp.mlsd(path=PATHS['pck'])])
        except Exception as e:
            logger.error("Exception initialising consoleftp", exception=e)
            app.config['USE_MLSD'] = False
            self._mlsd_enabled = False

    def get_folder_contents(self, path):

        file_list = []

        if self._mlsd_enabled:
            for fname, fmeta in self._ftp.mlsd(path=path):
                if fname not in ('.', '..', '.DS_Store'):
                    meta = {
                        'name': fname,
                        'modify': datetime.strptime(fmeta['modify'], '%Y%m%d%H%M%S').isoformat(),
                        'size': fmeta['size']
                    }
                    file_list.append(meta)

        else:
            pre = []
            self._ftp.dir("{}".format(path), pre.append)
            for unparsed_line in pre:
                bits = unparsed_line.split()
                date_string = ' '.join([bits[0], bits[1]])
                fname = ' '.join(bits[3:])
                # the isdigit() checks this is a file and a directory
                if fname not in ('.', '..', '.DS_Store') and bits[2].isdigit():
                    meta = {
                        'name': fname,
                        'modify': datetime.strptime(date_string, '%m-%d-%y %I:%M%p').isoformat(),
                        'size': int(bits[2])
                    }
                    file_list.append(meta)

        file_list.sort(key=operator.itemgetter('modify'), reverse=True)
        return file_list

    def get_file_contents(self, datatype, filename):
        self._ftp.retrbinary("RETR " + PATHS[datatype] + "/" + filename, open('tmpfile', 'wb').write)
        transferred = open('tmpfile', 'r')
        return transferred.read()
