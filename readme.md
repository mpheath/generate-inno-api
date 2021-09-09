# Generate Inno Setup Api


## Introduction

A Python script that reads from the Inno Setup XML source files that are used to create the official help documentation. The script will use xpath methods to get the data required.

It can make files for [SciTE](https://www.scintilla.org/SciTE.html) for autocomplete, calltips, styling etc.


## Generates

 * inno.properties
 * innocode.api
 * innocommon.api
 * innocomponents.api
 * innodirs.api
 * innofiles.api
 * innoicons.api
 * innoini.api
 * innoinstalldelete.api
 * innolangoptions.api
 * innolanguages.api
 * innopreprocessor.api
 * innoregistry.api
 * innorun.api
 * innosetup.api
 * innotasks.api
 * innotypes.api
 * innouninstalldelete.api
 * innouninstallrun.api

The reason for so many api files is that [make-scite-collection](https://github.com/mpheath/make-scite-collection) has an *inno\extension.lua* file which may change the api property setting depending on the Inno Setup section being currently edited. If all the api files were merged together, then directives, functions, keywords and procedures for all sections could cause confusion with the autocomplete and calltips in the current section being edited.

The files will be written into a folder named *output* in the same directory. Some files may be temporary such as a JSON file and cleaned XML files which maybe created for viewing what the operations and results are based on.


## Usage

 1. Get [main.zip](https://github.com/jrsoftware/issrc/archive/refs/heads/main.zip) source file from the *jrsoftware/issrc* repository. If you have the repository cloned then that could be a good alternative to use.
 2. Extract into the same directory as *gen_inno_api.py*.
 3. Rename *issrc-main* to *issrc* if needed, as a cloned repository is named the later and *issrc* is what the script is setup to use.
 4. Customize the settings at the top of *gen_inno_api.py* to your preference.
 5. Execute the script.


## Require

 * [main.zip](https://github.com/jrsoftware/issrc/archive/refs/heads/main.zip) or a clone of *jrsoftware/issrc* repository
 * [Python 3](https://www.python.org/)


## License

[gpl-3.0](http://www.gnu.org/licenses/gpl.html)
