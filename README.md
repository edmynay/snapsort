# snapsort
by edmynay

## Functionality:
Organize your photos and videos by their creation date.
It scans <input_dir> for media files,
reads creation date from metadata (EXIF),
and MOVES files under <output_dir> into folders by date:

<output_dir>/YYYY/MM/YYYY_MM_dd_HH_mm_ss.<ext>

Once discovered, each file is handled with multiprocessing,
for utilizing multicore CPUs efficiently.

Prints realtime progress using configurable progress bar.

**WARNING: YOUR FILES WILL BE MOVED FROM SOURCE LOCATION.\
         CONSIDER BACKUP CREATION!**

## Usage:
1. Install exiftool
2. Its recommend to create alias in your ~/.bashrc (Linux) or ~/.zshrc (Mac)
alias ss='python3 /path/to/snapsort.py'

   On Windows:\
notepad $PROFILE\
Set-Alias ss "python3 C:\path\to\snapsort.py"

3. Sort your files:
ss <input_dir> <output_dir>

### Positional arguments:
input_dir      Directory containing unsorted media files.
output_dir     Directory where sorted files will be placed.
               Hint: use output_dir on same physical disk as input_dir for fast file movement!
## Example:
ss ~/Downloads/Camera ~/Pictures/PHOTOS

Created on 1 May. 2016

@author: edmynay
