# Changelog
Any changes made by **`Team 2P`** that make it into the `main` branch are logged here.

A changelog for commits and changes before this version will not be added.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## bruker_control.py v1.9.2 - 2022-02-28
Dr. [Talmo Pereira](https://github.com/talmo) informed me that we should be encoding our videos using
the `H264` video codec instead of using `DIVX` encoding. It allows for nearly lossless compression and
creates `.mp4` videos that are reliably seekable. This small update changes the video codec used and also
grabs the microscope's framerate to use it for the video codec's writing to disk. This *should* fix a bug
that graduate student Deryn LeDuke came across while aligning video frames to voltage recording data. Talmo
also said that we should be performing a linear interpolation between data streams so they are all in a common
time base, regardless of the framerates being the same (or very close to the same), but this is something that
must be done post-hoc. Real-time alignment may be possible, but I have not found an easy way to do that yet.
Also noted during testing is that a single camera uses approximately 320MB/s of available ethernet bandwidth.
The local machine only appears to have 500MB worth of bandwidth total likely due to the type of ethernet card
that's present. If the lab would like to add an additional machine vision camera, we would need to upgrade
this machine's card to handle both datastreams. It was also discovered during testing that having remote
connections to other machines (something that would not happen during a recording normally) yields a large
increase in the number of dropped frames nearly totaling 6-7 minutes. Using as little of the network as
possible should be a priority while the recordings are underway.

Here's to hoping this fixes the bug and offers more reliable video-seeking/time-stamp effectiveness.

:heart: Jeremy Delahanty

### Changed

**_Python_**

*`video_utils.py`: `capture_recording()`*

The `capture_recording()` function now takes a new argument called `framerate`. It is for exactly what
it sounds like: specifying the framerate for the video codec. This value is gathered by `prairieview_utils`
and submitted for the recording so it is using the same value as the microscope that is triggering the
camera, the *true* framerate. It still remains to be seen if this solves the timing issue that Deryn
discovered, but I feel confident that it will after consulting people/resources online. A true test will be
performed the week of 2/28/21 on a small recording where voltage values can be aligned to the video stream.
The codec used by the software is also different. To support nearly lossless compression of video data that is
still reliably seekable, the `DIVX` video encoder has been replaced by the `H264` codec. In `opencv` with `FFMPEG`,
the codec is accessed by using an open source `H264` library provided by Cisco called `OpenH264`. This required
the addition of `.dll` binary to the `bruker_control` environment. See below for details. In order to use this
codec with the appropriate container, the file format of the facial video recordings has also been changed to
`.mp4` per Talmo's recommendation/documentation in `SLEAP`.

### Added

**_Video Codec: openh264-1.8.0-win64.dll_**

This codec provided by Cisco can be downloaded in full [here](https://github.com/cisco/openh264). For this
use case, all that is necessary is just one `.dll` file: `openh264-1.8.0-win64.dll`. This file can be found
[here](https://github.com/cisco/openh264/releases). This repository relies upon v1.8.0. In order to use it
with `opencv`, you have to include the binary in a specific location. At least in this software, it had to
be placed in this location:

- `C:\ProgramData\Anaconda3\envs\bruker_control\bin\openh264-1.8.0-win64.dll`

If it is *not* in this binary location, `opencv` and `ffmpeg` will fail to find the library
and the video will not be recorded to disk.

**_Python_**

*`prairieview_utils.py`: `get_microscope_framerate()`*

The value of the microscope's framerate appears to change very slightly each time Prairie View is started on the order
of about 0.01 FPS. This, in addition to the bug that Deryn discovered, make it vital that the framerate used by the encoder
is the same as that used by the microscope. This function will grab the current `PVStateShard` value for `framerate`, convert
that value from a string to a float, and round it up to the nearest 2 decimal places (hundreths). This value is returned and
later fed into `capture_recording()` for use as the framerate the encoder will use.

## bruker_control.py v1.9.0 - 2022-02-02 *Get Yoked*
A few new changes are here in this version of the repository primarily on the `Python side`, but also
some small changes have been made to an `Arduino` file to enable new functionality. There's also a new
way of performing different types of trials: Yoked trials! `bruker_control` got stronger in this update
and can do some new exercises for you. Read on to find out! 🏋️

:heart: Jeremy Delahanty

### Changed

**_Python_**

*`check_session_punishments()` and `check_session_rewards()`*

The method used for checking if too many punishment/reward trials were created in a `trialArray` was not
functioning properly. Previously successive `or` statements were used. Now, a check is performed for if
a `trial` is in a list of relevant trial types. Further, a trial set passes the checks if the number of
trials equals the max number of sequential trials of that type. The set fails now only if it exceeds that
number.

*Video Utils Change*
The location and size of the presented videos of the subject's face is now different. The video has been
downscaled by 50% and is placed in the bottom right corner of the screen so it is out of the way of
the Prarie View's windows. Note that the output video file is still the same.


**_Arduino_**

The `deryn_fd_disc.ino` file now has the ability to receive/parse LED trials which accompany all trial sets
given by `bruker_control`. It does not yet have the trial definitions for catch trials and LED stimulations
because they have not been requested.

### Added

**_Configuration File_**

The configuration file has a new parameter inside of `beh_metadata`: yoked. If true, `bruker_control`
will know to perform checks/load yoked trial sets for the given experimental subject type.

**_Directory Structures: Local_**

Due to users not all using the specialk style subject metadata files, a more generic method of creating
yoked trial sets was written. At runtime, `bruker_control` will check for an already existing trialset that
is located in the following folder:

```Raw Data
└── deryn_fd
    ├── config
    ├── microscopy
    ├── video
    ├── yoked <-- here
    └── zstacks
```

Files that are written here for a given day with a given plane will have the following format:
`YYYYMMDD_SUBJECTGROUP_PLANE#_yoked.json`

The subject groups will be experimental (exp) or control (con). These will be gathered at the command line.

For example:
`20220202_exp_plane1_yoked.json` and `20220202_con_plane1_yoked.json`.

There will be a new configuration file generated for each day, each group, and each plane that will be reused
for the animals in the group.

The format of the file is similar to how trial sets are stored in a given configuration file written at
the end of a particular recording. Meaning the data is stored as follows:

```
{beh_metadata:
    trialArray{[1,1,1,0,1,0,0...},
    ITIArray{[...]},
    toneArray{[...]},
    LEDArray{[...]}
}
```

This was done so accessing yoked files' arrays would be the exact same as accessing a configuraiton file
that is written at the end of a given animal's session, thereby (hopefully) reducing downstream processing
changes.

**_Command Line Arguments_**

To accomodate yoked trial sessions, a new command line argument has been added: -g/--group

This encodes which group the subject belongs to: experimental or control. To make it easier to type
for users, the abbreviations `exp` and `con` are used. These choices are enforced by the argument
parser in case someone accidentally writes the command incorrectly.

Now, the command line arguments look like this:

- -p TEAM_PROJECT (ie specialk_cs)
- -i IMAGING_PLANES
- -s SUBJECT_ID
- -g EXPERIMENT_GROUP

The experimental group is optional and defaults to `None` if it is not given.

**_Python_**

*Yoked Configuration Checks*
- check_yoked_config(): Searches for already existing yoked trialset for a given day, experimental group, and plane number.
- write_yoked_config(): If a trial set was *not* found by `check_yoked_config()`, one is generated in the usual manner with `trial_utils`. Once created, it is written to the local file system in the `yoked` file. 


## bruker_control.py v1.8.6 - 2021-11-18
Several larger changes have been done in this version predominantly for filenaming and the NWB capabilities.
They are described below. All modifications for this version have been done on the `Python` side of things.

### Changed

**_Directory Structures: Local_**

Discussions referenced in Issue #57 were resolved to alter the directory structures that are used for
reading/writing data to the local disk Raw Data.

Previously, the directory tree for writing raw data was:
```Raw Data
└── teams
    └── specialk <-- team
        └── cs <-- project
            ├── config
            ├── microscopy
            ├── video
            └── zstacks
```

Directories for writing raw data are now organized like this:
```Raw Data
└── specialk_cs <-- team_project
    ├── config
    ├── microscopy
    ├── video
    └── zstacks
```

The code in `bruker_control.py` has been updated to reflect the new directory structures.

**_Directory Structures: Server_**

The directories on the server have also been updated. This changes how configuration files
are read and where the transfer utility shell script sends data at the end of the day.

Previously, the directory for finding configurations and subject information looked like this:
```
snlktdata
└── specialk
    ├── 2p_template_configs
    └── subject_metadata
        └── cs
```

The directory for raw data looked like this:
```
snlktdata
└── raw
    └── specialk
        └── cs
            ├── config
            ├── microscropy
            ├── video
            └── zstacks

```

Now, directories for configurations and raw data are structured like this:

```
_DATA/
└── specialk_cs
    ├── 2p
    │   ├── config
    │   ├── processed
    │   └── raw
    │       └── SUBJECT_ID
    │           └── DATE
    │               ├── config.json
    │               ├── microscopy
    │               ├── video.avi
    │               └── zstacks
    └── subjects
```

The code in `bruker_control.py` as well as the `bruker_transfer_utility.sh` script
has been updated to reflect these directory changes.

**_Weight Files_**

Subject weights are no longer stored inside of the `subjectid.yml` as before. It was
determined that metadata files should be as static as possible. Therefore, a new file
inside the `subjects` directory in the `_DATA` directory described above called
`subjectid_weights.yml` has been created.

**_Exceptions_**

Previous exception classes were needlessly specific. They have been generalized to
the category of exception to expect. For example, `SubjectMultiple` and `SubjectMissing`
have been turned into `SubjectError` where the argument to the exception is now the message
delivered to the user. The same has been done for configuration file exceptions.

**_Command Line Arguments_**

The new structuring of the directories for data collection and transfer required changes
of the command line arguments. Further, because `bruker_control` no longer generates
NWB Files at runtime, the `experimenter` argument has been removed. 

The parameters are now:
- -p TEAM_PROJECT (ie specialk_cs)
- -i IMAGING_PLANES
- -s SUBJECT_ID

When typing out the command, it used to look like:

`bruker_control.py -t specialk -p cs -i 1 -s CSC000 -e "Experimenter Name"`

Now, it looks like this:

`bruker_control.py -p specialk_cs -i 1 -s CSC000`

This is simpler to type, more concise, and much more specific to collecting data
from the Bruker microscope as NWB generation is no longer part of the system.

**_Configuration File and config_utils.py_**

A new field for checking weights has been added to the configuration file for behavior in a given project.

It was determined that mandatory weighing of subjects before the experiment starts is
one, not explicitly necessary for every project and, two, would render the system more
difficult to use if/when a scale is broken or unavailable. However, because some projects
require the subject be weighed for each day and it could be something they forget, the
boolean `weight_check` field has been created.

If true, `config_utils` will search for the subject's weight file described above and
check if there's a weight that's been recorded for the current day in `YYYMMDD` format.

If no weight is recorded, an exception is raised under `SubjectError`.

If false, `config_utils` will pass this check.

**_Main Repository Organization_**

There were several nested `bruker_control` statements required when executing
`bruker_control` in the command line. It looked like this:

`python Documents\gitrepos\bruker_control\bruker_control\bruker_control.py ...`

This looks confusing and can be confusing to type. Therefore, the files containing
the actual `Python` script are now inside a directory called `main`. Now, invoking
`bruker_control` looks like this:

`python Documents\gitrepos\bruker_control\main\bruker_control.py ...`

Not a perfect solution, but somewhat better than it was. An easy to use
shortcut or link is under development.

### Removed

**_NWB File Generation: nwb_utils.py_**

`nwb_utils.py` has been removed from the repository. It was determined in Issue #57
that `bruker_control` should be exclusively focused upon the collection of data off
the scope. Therefore, NWB File generation has been removed from the repository.

The utility module `nwb_utils.py` can now be found in the `bruker_pipeline` repo
which has yet to have been made public.

## bruker_control.py v1.8.2 Hotfix - 2021-10-27
Small fix to versioning numbers, longer timing for `set_laser_lambda` as it was too short
when going between laser wavelengths. Changed where Z-stack `tqdm` progress bar occurs
and made timing more representative of actual progress.

## bruker_control.py v.1.8.0 *Stimulate Your Mind* 🔦 🎆 🧠 - 2021-10-27
Welcome to v1.8.0! There's plenty to be thankful for as we move towards November, and
one of those things is optogenetics and big bright LEDs! This update adds a hefty amount,
so eat slowly and try not to stuff yourself like a turkey 🦃 just yet.

There's some enhancements made to the trial structure generation to handle stimulations as well as
more expressive metadata for behavioral experiments that encode how stimulations are to
be performed for the session. There's also some additional exception handling classes for
if/when something is entered incorrectly thought they're not comprehensive. The documentation 
also has a couple changes.

:heart: Jeremy Delahanty

### Added

**_Python_**

New command line parameter: Project
**Required**
- --project, -p:

If you're one of the teams that has more than one project going, this argument requires a
two letter code that references the project's name.

*Stimulation Configuration* - behavior_projectcode_config.json
- stim: true/false Do you want stimulations to happen during the trial?
- stimFrequency: Metadata about pulse rate in Hz
- stimPulseTime: Metadata about how long an individual pulse occurs in ms
- stimLabmda: Frequency of stimluation LED being used in the experiment
- stimDeliveryTime_PreCS: Amount of time before a given trial the stimulation should occur
- stimDeliveryTime_Total: How long the stimulation should occur
- stimStartPosition: 0-indexed position of which trials should be LED stimulation trials
- numStimReward: Number of LED trials where the subject should be given a reward
- numStimPunish: Number of LED trials where the subject should be given a punishment
- numStimAlone: Number of LED trials where the subject will receive only LED stimulation
- LEDArray: Array of timepoints where the LED stimulation should be triggered by the Arduino

*`trial_utils.py`: Stimulation Trial Rules*
A few new functions have been added for handling LED stimulation trial structure generation.

- `gen_trialArray_nostim()`: Builds trial structure according to configuraiton rules without LED
stimulation trials
- `gen_trialArray_stim()`: Builds trial structure according to configuration rules with LED
stimulation trials.
- `gen_LEDArray()`: Generates timestamp array for when LED trials should be triggered.
- `flip_stim_trials()`: Flips non-stimulation trials into LED trials within the range of
requested LED trials. Checks to ensure that no more than user configured number of punish
trials are given in a row.
- `flip_stim_only()`: Flips stimulation trials to LED only trials.
- `check_session_stim_only()`: Performs check that no more than 2 LED Only trials are given
in a row.

*`config_utils.py`: New exception classes and enhanced configuration*
Configuration exception classes that are more helpful for when something is missing/malformed
have been made. There's also new handling for the configuration stimulation fields.
**Classes**

- `ProjectNWBConfigMissing(Exception)`
- `ProjectNWBConfigMultiple(Exception)`
- `ProjectTemplateMissing(Exception)`
- `ProjectTemplateMultiple(Exception)`
- `SubjectMultiple(Exception)`
- `SubjectMissing(Exception)`
- `SubjectMissingWeight(Exception)`

**Functions**

- `build_server_directory()`: Builds directory to `snlkt/data/raw/` for the appropriate
project and subject for that day's imaging. This is where NWBFiles will be written
and where the day's imaging data will be written to.

*`nwb_utils.py`: Determine Sessions for CMS Project and XML Exception Handling*
Due to the use of stimulations and voltage outputs in the new paradigm, the
`xml.etree.ElementTree` parser crashes when reading the `.env` file when it
encounters invalid characters that are produced in v1.0 XML but are not supported
until v1.1. Microsoft's .NET implementation does not yet correct for this, but 
per Michael Fox (Senior Software Engineer at Bruker who has been helping me enormously)
Microsoft has let this (minor) problem persist for decades. The use of `lxml` has been
added to the program should the `xml.etree` module fail as it has an option to escape
badly formed XML with the `recover=True` option.

*`prairieview_utils.py`: Setting Channels and Lasers*
New functions are present for telling Prairie View to use different channels when
appropriate for what functional indicator is being imaged at the time of the
experiment.

- `set_one_channel_zseries`: Sets appropirate channel for imaging a specific
indicator. Uses either Red (Ch1) or Green (Ch2).


**_Arduino_**

The Arduino sketch for team specialk has been updated to handle the new transferring
of LED array, LED Trial types, LED Timings, and LED Triggers. Doc strings have been added
for all these new functions in the source.

- `typeLED()`: Used for determining what kind of LED trial is occuring and prints it to
Serial monitor for the user.
- `setLEDStart()`: Used for calculating when to send an LED trigger
- `brukerTriggerLED()`: Sends signal to Bruker DAQ if an LED is scheduled to occur.

**_Shell Scripting_**

A new script called `bruker_transfer_utility.sh` has been written for automatic transferring
of files to the server. It is currently only usable by team Specialk because it is the only
team that has the directory structure built and ready to use on the file server. It's use is
simple and is outlined in the updated `README` at the end of the document. It uses the tool
`rsync` to conduct the file transfer to the SNL server.

**_Prairie View_**

A new "Mark Points Series" has been incorporated for team specialk as has a new "Voltage
Output" experiment that is synced with "Mark Points" when a Stimulation Experiment is
being conducted.

### Changed

**_Python_**

There are some minor changes associated with how things operate in Python.

*`serialtransfer_utils.py`*
- Introduced new metadata variable for transmission that encodes the stimulation array.

*`prairieview_utils.py`*
- Added a progress bar and increased amount of time for laser changes to 5 seconds in `set_laser_lambda`
- Added a progress bar for z-stacks in `z-stack` so the terminal doesn't look like it's hanging during
operation.

**_Arudino_**

The Serial Monitor is a little less busy now. Far fewer things are printed to the terminal in favor
of a cleaner appearance for just trial type, trial number, and when the stimuli is delivered to the subject.
This has only been done for Specialk because I'm unsure if other teams would want/request this.

**_Prairie View_**

The team specialk Voltage Recording has been changed to include the LED590 stimulations if the session
calls for it.


## bruker_control.py v.1.6.0 *Big Mac* - 2021-10-02

This is v1.6.0!  It might be spooky season, but have no fear! This update isn't so scary.
This update adds automated z-stack functionality to the system as well as some enhanced
`subject_metadata` information parsing for performing z-stack to t-series recordings
seamlessly. Lots of things have been changed so take a bite of the *Big Mac* update by
reading on! 🍔

:heart: Jeremy Delahanty

### Added

Z-stack functions added to `prairieview_utils` with the following functions:
- set_galvo_galvo() Function for gathering Z-stack images
- set_laser_lambda() for changing laser wavelengths according to imaging indicators
- set_zseries_filename() Sets filename and directories for Z-stacks correctly
- set_zseries_parameters() Sets up the Z-series values for step size, start/stop positions
- get_imaging_indicators() Gathers indicator information from surgical metadata in a subject

Configuration Information:
**Required**
- `zstack_metadata`: Whether to perform a z-stack or not in a given experiment as well as
the values required by Prairie View for setting up the acquisition correctly.

**Optional**
- Surgery metadata added to subject metadata files

### Changed
- Moved virus information to subject metadata from project metadata
- Moved `get_subject_metadata()` to `config_utils`
- Set coordinates for `origin_coords` using surgical information for imaging plane in NWB file
per Ryan Ly's advice.


## Configurations- 2021-09-16

### Added
- Example animal configuration .yml file
- Example project NWB file

### Changed
- Updated example Arduino configuration to enhanced version

### Removed
- Old template Arduino configuration files.

## bruker_disc_deryn.ino v1.0.1 - 2021-09-16

### Added

Doc strings for all functions now present that are accurate to project's setup.

### Changed

Corrected some typos in the documentation

## bruker_disc_specialk.ino v1.0.1 - 2021-09-15

### Changed

Start new ITI after presentation of sucrose droplet is complete. Now both Deryn and Austin's projects
start ITIs the moment the tone is complete.

Removed ITI delivery output from specialk Arduino sketch.

## bruker_control.py v1.0.0 - 2021-09-13
This is v1.0! There's been several things added and several things changed after refactoring the code
for a few weeks. Check out the info below!

:heart: Jeremy Delahanty

Each section, if it has a block of text, also has a short `In summary` section in case it's TLDR.

### Added

#### _Arduino_
- Doc strings for functions in Arduino sketches
- Added ITI and tone specific DAQ outputs
- Catch trial functionality
- Automatic resetting of Arduino after experiment is finished
- Semantic versioning for sketches

#### _Prairie View_
- Project specific configurations for Prairie View recordings' data output
- Automated Z-plane acquisition for file naming (ie 20210913_MOUSEID_plane1_**-221.12**_...)
- Automated switching to `Resonant Galvo` mode in case user forgets to select it

#### _Python: bruker_control_
- Doc strings for every function
- More descriptive inline comments in functions
- Read the Docs technical documentation hosted ([found here!](bruker-control.readthedocs.io/en/latest/))
- Semantic versioning
- Exceptions for missing configurations and camera disconnects
- Enhanced configuration and customization for trial structure
- Catch trials added
- Writing out list of missing video frames to configuration file
- **(Optional)** Experimenter argument at command line
- **(Optional)** Automated parsing of Prairie View `.env` files for NWB specific microscope information
- **(Optional)** Automated writing of base NWB files to specific directory on the server for a project.

#### _Directory Structures_
Each team that interfaces with the Bruker system will have a folder on the server named `2p_template_configs`.
This will contain the template configuration file for the team's experiment runtime and, if desired, a project
specific configuration file that can be reused for building NWB files later on.
Another optional addition is if you would like to have your base files written to the server in automatically
generated locations appropriate for your subject's place in the experimental timeline.
For example, if you are recording from an animal for its baseline experiment, the system will correctly identify
the animal as being in the baseline stage, build a location on the server for that subject with the appropriate
names, and write a baseline file for you the moment the recording is finished. Given that the experimenter knows
precisely how many 2P recording sessions will be collected for a given subject, an appropriate automated solution
can be implemented for each new project or team.

In summary:
- **Required** Team specific template configuration directory that is hosted on the server
- **(Optional)** Subject metadata directory that is hosted on the server

#### _Metadata and Configuration Files_
Users can have subject specific and project specific metadata files added to their directories.
An optional addition is to have a set of metadata files for animals that contain NWB specific information.
This information includes the subject's ID, strain, date of birth, genotype, sex, and weight.
These could be used when generating NWB files later or, if desired, at runtime of the experiment.
These files are not part of the repository itself, but can be used with it. Examples of them are present
on the repository in the `configs` directory.

In summary:
- **Required** Project specific template
- **(Optional)** Subject specific metadata files
- **(Optional)** Project specific configuration files

#### _NWB Support_
As described above, if the user would like to build a base NWB file at the end of the recording, `bruker_control.py`
is now capable of doing so. Once the microscopy session is completed, the program will grab relevant metadata for
the subject and project from the files described above as well as parse the Prairie View `.env` file that is generated by
the recording. The program will then build a base NWB file for the subject's recording to which the recording's data
can be added to at a later time. These files are written directly to the server in the subject's appropriate experimental
location as described in the _`Directory Structures`_ section above.

In summary:
- If desired, a base NWB file can be generated once the experiment is finished and would be written to the subject's appropriate
directory on the server automatically.

### Changed
- CLI (Command Line Interface) has different arguments: `-t` for the team - formerly `-p` for project - as in `specialk`, `-i` for number of imaging planes,
`-s` for subject - formerly `-m` for mouse - ID, and `-e` for experimenter if using the NWB functionality.
- Arduino variables that were once called `noise` are now all changed to `tone` **EXCEPT** in the case of the `noise` boolean flag.
This cannot be changed to `tone` as tone is a protected name for the `tone()` function in Arduino's IDE.
- Changed Arduino sketch name for team `specialk` to be more specific for the team.
- Raw data is written to a `team` directory instead of a `studies` directory
- Raw Prairie View data is written into a folder with `_raw` appended to the end of it as in `YYYYMMDD_SUBJECTID_PLANE#_PLANELOCATION_raw`.
- README.md updated with (very basic) `bruker_control.py` procedure
- Stimulus presentation now overlaps the end of the tone by default

### Removed
- Unused Arduino sketches and configuration files
- `Behavior only` and its associated functions have been deprecated and removed from the repository
- `Sucrose only` and its associated functions have been deprecated and removed from the repository
- The `behavior` directory for the raw data has been removed as Prairie View does not support having different
directories for placing the raw microscopy and voltage recording files.
