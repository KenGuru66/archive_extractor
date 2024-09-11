# Archive Extractor

This Python script extracts a specified archive and all nested archives recursively. It supports a wide range of archive formats and is designed to work efficiently with large numbers of files.

## Features

- Recursively extracts archives
- Supports `.7z`, `.zip`, `.tar.gz`, `.tgz`, `.tar`, `.tar.bz2`, `.tbz2`, `.tar.xz`, `.txz`, `.rar` formats
- Displays extraction statistics
- Supports multi-threading for faster extraction
- Automatically removes original archives after successful extraction

## Usage

To use this script, run the following command:

##sh
python script.py <archive_path> <extract_to>
<archive_path>: Path to the main archive file to extract.
<extract_to>: Directory where the extracted files will be stored.

For example:
- python script.py /path/to/archive.7z /path/to/destination/
- To display the help message:
python script.py --help

## Requirements
Python 3.x
rich library for better console output
rarfile library for handling .rar archives

You can install the required libraries using pip:
- pip install rich rarfile

sudo apt update &&
sudo apt install p7zip-full

## License
This project is licensed under the MIT License. See the LICENSE file for details.
