# Self Driving Collision Avoidance Project for CMP400 at Abertay University

# Note if you wish to start a new model to train using this
This project uses a default model when running this, and is ordinarily configured to use this model to train. If you wish to train a new model, uncomment-out lines 1458 to 1463 in "cmpfourhundred_manual_control.py" & on line 149, changed "LOADING_MODEL" to "False" to create a new model.

# Parts of note
The cmpfourhundred_manual_control.py is based off of "manual_control.py" given in the examples folder of a CARLA distribution for version 0.10.0. The other python files in attatched to the repo have been built from the ground up.
Everything pertaining to the actual RL takes place in manual_control and RL_2ndtry (which is named this since it was the 2ndtry file, which ended up keeping its name).

The instructions on how to run this program are included in the readme.html

# Download the release for a working project
https://drive.google.com/file/d/16fxnYaJZu-tln1AqAhdWgeaSvxJb02B7/view?usp=drive_link
