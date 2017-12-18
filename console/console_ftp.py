from console import app
from io import BytesIO
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
    "json": settings.SDX_RESPONSE_JSON_PATH
}


class ConsoleFtp(object):

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self._ftp.quit()

    def __init__(self):
        self._ftp = FTP(settings.FTP_HOST)
        self._ftp.login(user=settings.FTP_USER, passwd=settings.FTP_PASS)
        self._mlsd_enabled = app.config['USE_MLSD']

    def get_folder_contents(self, path):

        file_list = []
        metadata_available = True

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
            """ Parts of this block might look strange but are there for a good reason.
            Using the LIST command (which is what .dir is doing), there is no standard
            format the data will be returned in (one of the reasons mlsd was created).

            Because of this, we can be fairly sure the filename is the last element, but
            nothing else.  Currently we deal with 2 different formats for 2 different servers
            so we try the 2 known formats, and if that doesn't work (i.e., an Exception
            is thrown because the datetime was in a different place) we catch the Exception
            and display N/A to the user because we can't be certain of what the format
            will be.

            An error isn't logged in these exceptions because if it happens once, it will happen
            every time and will unlikely ever be changed so we won't flood the logs with
            needless messages.
            """
            pre = []
            self._ftp.dir("{}".format(path), pre.append)

            for unparsed_line in pre:
                logger.info("Unparsed line", line=unparsed_line)
                bits = unparsed_line.split()
                meta = {}
                try: # First we'll assume it's a windows based FTP server

                    date_string = ' '.join([bits[0], bits[1]])
                    modify = datetime.strptime(date_string, '%m-%d-%y %I:%M%p').isoformat()
                    fname = ' '.join(bits[3:])
                    # If this works then we're on a windows based FTP server and can continue
                    if fname not in ('.', '..', '.DS_Store') and bits[2].isdigit():
                        meta['modify'] = modify
                        meta['fname'] = ' '.join(bits[3:])
                        meta['size'] = int(bits[2])
                except Exception: # We next test for a unix based FTP server
                    try:
                        date_string = ' '.join([bits[5], bits[6], bits[7]])
                        modify = datetime.strptime(date_string, '%b %d %H:%M').isoformat(),
                        fname = ' '.bits[-1]
                        if fname not in ('.', '..', '.DS_Store') and bits[1].isdigit():
                            meta['modify'] = modify
                            meta['name'] = fname,
                            meta['size'] = int(bits[4])
                    except Exception:
                        # If neither of the above work, we don't know what format the
                        # list is coming back in, and we just don't give any metadata
                        # and assume the name is the last element
                        meta['name'] = ' '.bits[-1]
                        meta['modify'] = 'N/A'
                        meta['size'] = 'N/A'
                        metadata_available = False


                    meta = {
                        'name': fname,
                    }
                    file_list.append(meta)

        if metadata_available:
            file_list.sort(key=operator.itemgetter('modify'), reverse=True)
        return file_list

    """ Searches for a file in the FTP server and returns it in binary
    format.  It's up to the function calling this one to convert the output
    into a more useful format.
    """
    def get_file_contents(self, datatype, filename):
        ftp_file = BytesIO()
        self._ftp.retrbinary("RETR " + PATHS[datatype] + "/" + filename, ftp_file.write)
        ftp_file.seek(0)
        return ftp_file.read()
