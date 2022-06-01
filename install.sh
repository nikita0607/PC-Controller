#!/bin/sh

# Set source and target directories

# if an argument is given it is used to select which fonts to install


if psython3 -m pip install -r requirements.txt ; then
    echo "Successfuly installed libraries!"
else
    echo "Set python destination: " ; read python
    $python -m pip install -r requirements.txt
fi
