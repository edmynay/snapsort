# snapsort
by edmynay, 1.05.2016

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
2. Sort your files:
python3 /path/to/snapsort.py <output_dir> <input_dir>
3. Its recommend to create alias in your ~/.bashrc (Linux) or ~/.zshrc (Mac)
alias ss='python3 /path/to/snapsort.py <output_dir>'

   On Windows:\
notepad $PROFILE\
Set-Alias ss "python3 C:\path\to\snapsort.py <output_dir>"

    So you can use script as following:\
ss <input_dir>




### Positional arguments:
output_dir     Directory where sorted files will be placed.\
               Hint: use output_dir on same physical disk as input_dir for fast file movement!\

input_dir      Directory containing unsorted media files.
## Example:
ss ~/Downloads/Camera
