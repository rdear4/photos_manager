# Photos Manager


## Features

## Dependencies

    #### System
    - ffmpeg

    #### Python packages
    - ffmpeg-python
    - PIL


## Versions
---

### v0.1
- [x] Add argparser
- [x] Add cProfiler
- [x] Add Logging

### v0.2
- [x] Add Create DB
- [x] Add DB Table for directories
- [x] Add DB Table for mediaFiles
- [x] Add Drop DB Tables ALL
- [x] Add Media Finder (Simple)

    #### Notes
    The "simple" version of the media finder will ONLY be the recusive function that searches all directories for other directories

### v0.3
- [x] Create dict with media info
        - Filepath, filetype, creation date, image data hash, exif data (if available)
- [x] Insert data into DB
- [x] Add support for MP4
- [x] Add support for M4V
- [x] Add support for MOV
- [x] Add support for JPG, JPEG, PNG

    #### Notes
    With this version, the process media function takes a list of filepaths of all media files that were found. If it's an image, it will load the image using PIL, hash the image, extract EXIF data (where available), return the dict with that info, and finally write that info to a database.

    


    