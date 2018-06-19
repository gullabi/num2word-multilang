# num2word_multilang
Scripts for number normalization in multiple languages.

## Installation
The script uses the `inflect` module of python and apertium translation tool.

To install `inflect` either use the `requirements.txt`:
```
pip install -r requirements.txt
```
or simpy,
```
pip install inflect
```

And to install `apertium` in a debian distribution:
```
apt-get install apertium apertium-all-dev
```

## Use
For a ascii text file of a given language
```
python num2word-multilang.py text.txt <in-file> <out-file> <lang>
```

Currently the language is assumed to be catalan, and if no out_file is given `<in-file>_norm.txt` is created at the path of the `<in-file>`.

In addition to the `<out-file>` the script creates a log file `num2word.log` which includes only the replaced lines comparing the old and new versions.

## Notes and assumptions
There are certain assumptions which go into the normalizations, specifically concerning the `.` and `,` digit seperators. 

* The `.`s are assumed to be digit signifiers and taken out (i.e. 250.000 -> 250000)
* The `,`s are assumed to be digit seperators and replaced with its written form (4,12 -> 4 coma 12)

These rules are language and corpus dependent and should be always revised.
