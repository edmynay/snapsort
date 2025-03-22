intro = r'''
snapsort
(ss)

Functionality:
Organize your photos and videos by their creation date.
It scans <input_dir> for media files,
reads creation date from metadata (EXIF),
and MOVES files under <output_dir> into folders by date:

<output_dir>/YYYY/MM/YYYY_MM_dd_HH_mm_ss.<ext>

Once discovered, each file is handled with multiprocessing,
for utilizing multicore CPUs efficiently.

Prints realtime progress using configurable progress bar.

WARNING: YOUR FILES WILL BE MOVED FROM SOURCE LOCATION.
         CONSIDER BACKUP CREATION!

Usege:
1. Install exiftool
2. Sort your files:
python3 /path/to/snapsort.py <output_dir> <input_dir>
3. Its recommend to create alias in your ~/.bashrc (Linux) or ~/.zshrc (Mac):
alias ss='python3 /path/to/snapsort.py <output_dir>'

On Windows:
notepad $PROFILE
Set-Alias ss "python3 C:\path\to\snapsort.py <output_dir>"

So you can use script as following:
ss <input_dir>

Positional arguments:
input_dir      Directory containing unsorted media files.
output_dir     Directory where sorted files will be placed.
               Hint: use output_dir on same physical disk as input_dir for fast file movement!
Examples:
ss ~/Pictures/PHOTOS ~/Downloads/Camera

Created on 1 May. 2016

@author: edmynay
'''

import argparse
import datetime
import errno
import logging
import multiprocessing
import os
import re
import shutil
from subprocess import check_output
from threading import Event, Thread
import time
import traceback



MEDIA_FILETYPES = (
# ---------------------------------- PHOTO -------------------------------------
'jpg',
'jpeg',
'png',
'bmp',
# ---------------------------------- VIDEO -------------------------------------
'mov',
'3gp',
'3gpp',
'mp4',
'avi',
'wmv',
)

DIGITAL_ERA_START = datetime.datetime(2004, 1, 1)
MULTI = True  # better turn off on some network storages

# Fields in priority order
priority_fields = [
    'Date/Time Original',
    'File Modification Date/Time',
    'GPS Date Stamp',
    'GPS Date/Time',
    'Create Date'
]
num_files = 0


log_file = os.path.join(os.path.dirname(__file__), "debug.log")  # Log file in the same directory

with open(log_file, 'w') as file:
    file.truncate(0)

# Configure logging
logging.basicConfig(
    level=logging.ERROR,  # Set the logging level (e.g., DEBUG, INFO, WARNING, ERROR)
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format with timestamp
    datefmt='%Y-%m-%d %H:%M:%S',  # Timestamp format
    handlers=[
        logging.FileHandler(log_file),  # Output to file
        # logging.StreamHandler()         # Output to console
    ]
)

def file_move(source_full_file_name, target_user_folder):

    with MOVED_COUNTER.get_lock():
        MOVED_COUNTER.value += 1

    logging.debug(f'Call file_move{str((source_full_file_name, target_user_folder))}')
    file_ext = source_full_file_name.split('.')[-1].lower()

    if file_ext not in MEDIA_FILETYPES:
        logging.warning(f'not a media file: {source_full_file_name}')
        return  # Do not handle unknown file types

    # Fetch internal create timestamps for some formats
    try:
        # Getting file timestamps using exiftool as a more accurate source
        cmd = ["exiftool", "-time:all", source_full_file_name]
        logging.debug(f'exiftool cmd: {cmd}')
        printout = check_output(cmd).decode()
        logging.debug(f'exiftool printout:\n{printout}')

        # Regex for matching date/time strings like '2019:01:01 11:56:01'

        date_pattern = re.compile(r'(\d{4}:\d{2}:\d{2} \d{2}:\d{2}:\d{2})')

        # Initialize
        selected_date = None

        for field in priority_fields:
            for line in printout.splitlines():
                if line.strip().startswith(field):
                    match = date_pattern.search(line)
                    if match:
                        date_str = match.group(1)
                        try:
                            t = datetime.datetime.strptime(date_str, '%Y:%m:%d %H:%M:%S')
                            if t > DIGITAL_ERA_START:
                                file_date = t
                                logging.debug(f'Selected date from field "{field}": {t}')
                                break
                        except ValueError as e:
                            logging.warning(f"Failed to parse date from field '{field}': {line} -> {e}")
            if file_date:
                break

        if not file_date:
            logging.error(f'No valid timestamp found for {source_full_file_name}')
            return
        else:
            logging.debug(f"Selected file date: {file_date}")

        # set correct file access and modification time
        # os.utime(source_full_file_name, (datetime.datetime.timestamp(file_date), datetime.datetime.timestamp(file_date)))
    except:
        # file_date = datetime.datetime.fromtimestamp(min(os.path.getctime(source_full_file_name),
        #                                                 os.path.getmtime(source_full_file_name)))

        logging.error(f'Error determining timestamps of the file:\n{source_full_file_name}\n:{traceback.format_exc()}')
        return

    target_folder = os.path.join(target_user_folder, str(file_date.year), str(file_date.month))  # Crates yyyy\mm subfolders
    file_name = '_'.join((str(file_date.year),
                         '{:0>2d}'.format(file_date.month),
                         '{:0>2d}'.format(file_date.day),
                         '{:0>2d}'.format(file_date.hour),
                         '{:0>2d}'.format(file_date.minute),
                         '{:0>2d}'.format(file_date.second)))
    file_name_with_ext = f'{file_name}.{file_ext}'
    target_full_file_name = os.path.join(target_folder, file_name_with_ext)

    if os.path.exists(target_full_file_name):
        if (os.path.getsize(source_full_file_name)
         == os.path.getsize(target_full_file_name)):     # if file sizes are the same, consider its the same file
            os.remove(source_full_file_name)             # so just delete source file
            return
        else:                                            # otherwise step new file number to latest consecutive
            target_full_file_name_no_ext = target_full_file_name[:target_full_file_name.rindex('.')]

            i = 1
            while True:
                target_full_file_name = f'{target_full_file_name_no_ext}_{i}.{file_ext}'
                if not os.path.exists(target_full_file_name):
                    break
                i += 1

    if os.path.getsize(source_full_file_name) > 0:
        while True:  # make file creating target dir if needed
            try:
                shutil.move(source_full_file_name, target_full_file_name)
                logging.debug(f'Call shutil.move{str((source_full_file_name, target_full_file_name))}')
                break
            except FileNotFoundError as e:
                if e.errno == errno.ENOENT:
                    os.makedirs(target_folder, exist_ok=True)
                else:
                    logging.debug(f'Unexpected FileNotFoundError during moving file from\n'
                                  f'{source_full_file_name}\nto\n{target_full_file_name}:\n{traceback.format_exc()}')
    else:
        os.remove(source_full_file_name)  # clean 0 size source file as leftover

    logging.debug(f'Finish file_move{str((source_full_file_name, target_user_folder))}')


def draw_progress_bar(progress, l=40, prefix='', borders='[]', fill='#'):
    bar_length = int((progress if progress < 1 else 1) * l)
    # Dynamically align the bar to 'l' width
    print(f'\r{prefix}{borders[0]}{fill * bar_length:<{l}}{borders[1]} {progress:.2%}', end='')


def init_globals(counter):
    # https://stackoverflow.com/questions/53617425/sharing-counter-between-processes-with-multiprocessing-starmap
    global MOVED_COUNTER
    MOVED_COUNTER = counter


def drive_progress_bar(stop_event):
    while not stop_event.is_set():
        if num_files:
            with MOVED_COUNTER.get_lock():
                    draw_progress_bar(MOVED_COUNTER.value / num_files, prefix='Moving files: ')
        time.sleep(0.1)


if __name__ == '__main__':

    start_time = time.time()
    MOVED_COUNTER = multiprocessing.Value('i', 0)  # Global progress counter
    stop_event = Event()

    parser = argparse.ArgumentParser(description=intro, formatter_class=argparse.RawDescriptionHelpFormatter)

    parser.add_argument('target', type=str, help='Target directory to copy files to')
    parser.add_argument('source', type=str, help='Source directory to copy files from')

    args = parser.parse_args()

    source = args.source
    logging.debug(f'source={source}')
    target = args.target
    logging.debug(f'target={target}')

    if MULTI:
        pool = multiprocessing.Pool(initializer=init_globals, initargs=(MOVED_COUNTER,))
    else:
        pool = multiprocessing.Pool(processes=1, initializer=init_globals, initargs=(MOVED_COUNTER,))

    # Start progress bar deamon
    daemon_thread = Thread(target=drive_progress_bar, args=(stop_event,))
    daemon_thread.daemon = True  # Set the thread as a daemon
    daemon_thread.start()

    logging.debug(f'Starting checking files in {source}')
    num_files = 0
    for root, dirs, files in os.walk(source):
        logging.debug(f'Start handling root={root}, dirs={dirs}, files={files}')
        for filename in files:
            if filename.startswith("._"):  # Skip AppleDouble files
                continue
            elif filename.lower().endswith(MEDIA_FILETYPES):
                file_path = os.path.join(root, filename)
                logging.debug(f'Copying file: {file_path}')
                pool.apply_async(file_move, (file_path, target))
                # file_move(file_path, target)
                num_files += 1
        logging.debug(f'Finish handling root={root}, dirs={dirs}, files={files}')

    pool.close()
    pool.join()

    # Signal the progress bar thread to stop
    stop_event.set()
    daemon_thread.join()  # Wait for the thread to finish

    print(f'\nMoved {num_files} files in {time.time() - start_time:.2f} seconds')
