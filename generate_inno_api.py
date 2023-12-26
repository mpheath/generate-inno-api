#!python3

'''Generate inno.properties and several inno*.api files for use with SciTE.

Run the script next to issrc source folder which is available from:
  https://github.com/jrsoftware/issrc

The script was created from Inno Setup v6.2.0 source and may work with previous
versions. Should work with later versions and could be updated if it does not.
'''

import xml.etree.ElementTree
import os, re, textwrap
import json


settings = {
    # Dictionary output to json file or printed for inspection.
    # 0=None, 1=Print, 2=Write.
    'dic_output': 0,

    # Create clean xml files for inspection.
    'clean_xml_files': False,

    # Make styles like make-scite-collection.
    'update_styles': False,

    # Maximun number of wrapped lines for calltip descriptions.
    # None=all, >= 1=number of lines.
    'max_lines': 5}


def get_common_parameters():
    '''From isetup.xml for get_section_lists().'''

    words = set()

    for key in root['isetup'].findall('./topic[@title="Common Parameters"]'
                                      '/body/paramlist/param'):
        name = key.get('name')
        words.add(name + ':')

    words = sorted(words, key=str.lower)

    return words


def get_components_and_tasks_parameters():
    '''From isetup.xml for get_section_lists().'''

    words = set()

    for key in root['isetup'].findall('./topic'
                                      '[@title="Components and Tasks Parameters"]'
                                      '/body/paramlist/param'):
        name = key.get('name')
        words.add(name + ':')

    words = sorted(words, key=str.lower)

    return words


def get_section_lists():
    '''From isetup.xml for inno{section}.api files.'''

    common_parameters = get_common_parameters()
    components_tasks_parameters = get_components_and_tasks_parameters()
    subdic = {}

    re_names = re.compile(r'\[([a-zA-Z]+)\]')
    re_ctp = re.compile(r'^Components and Tasks Parameters$', re.M)
    re_cp = re.compile(r'^Common Parameters$', re.M)
    re_langopts = re.compile(r'^\w+=', re.M)

    for key in root['isetup'].findall('./topic'):
        title = key.get('title')

        if not title:
            continue

        sections = re_names.findall(title)

        if not sections:
            continue

        for section in sections:

            section = section.lower()

            if section in subdic:
                continue

            subdic[section] = []

            # LangOptions keys in precode.
            if section == 'langoptions':
                precode = key.find('body/precode')

                if precode is not None:
                    subdic[section].extend(re_langopts.findall(precode.text))
                    continue

            # Add Parameters.
            param = key.findall('body/paramlist/param')

            if not param:
                continue

            for item in param:
                name = item.get('name')

                # CopyMode deprecated as of IS 3.0.5 (2002-12-16).
                if section == 'files':
                    if name == 'CopyMode':
                        continue

                # Section run and uninstallrun share parameters except these.
                if section == 'run':
                    if name == 'RunOnceId':
                        continue

                if section == 'uninstallrun':
                    if name in ('Description', 'StatusMsg'):
                        continue

                subdic[section].append(name + ':')

            # Add Flags.
            params = key.findall('body/paramlist/param/flaglist/flag')

            if params:
                for item in params:
                    name = item.get('name')

                    # Section Run and UninstallRun share flags except these.
                    if section == 'uninstallrun':
                        if name in ('postinstall', 'runasoriginaluser',
                                    'skipifnotsilent', 'skipifsilent',
                                    'unchecked'):
                            continue

                    # Section Run postinstall flag states isreadme
                    # flag is deprecated in the Files section.
                    if section == 'files':
                        if name == 'isreadme':
                            continue

                    if name not in subdic[section]:
                        subdic[section].append(name)

            # Add Dirs attributes that are embedded.
            if section in ('files', 'dirs'):
                for item in ('external', 'hidden',
                             'notcontentindexed',
                             'readonly', 'system'):

                    if item not in subdic[section]:
                        subdic[section].append(item)

            # Add Registry attributes that are embedded.
            if section == 'registry':
                for item in ('HKCU', 'HKLM', 'HKCR', 'HKU', 'HKCC', 'HKA',
                             'none', 'string', 'expandsz', 'multisz',
                             'dword', 'qword', 'binary'):

                    if item not in subdic[section]:
                        subdic[section].append(item)

            # Add Common parameters.
            txt = key.find('body')

            for item in txt.itertext():
                item = item.strip()

                if item:
                    if re_ctp.search(item):
                        subdic[section].extend(components_tasks_parameters)

                    if re_cp.search(item):
                        subdic[section].extend(common_parameters)

            # Add Check parameter.
            if section not in ('code', 'custommessages', 'messages'):
                subdic[section].append('Check:')

            subdic[section].sort()

    subdic['installdelete'] = subdic['uninstalldelete']

    return subdic


def get_constants():
    '''From isetup.xml for innocommon.api.'''

    words = set()

    # Pattern to match like {constants}.
    re_names = re.compile(r'\{[a-zA-Z0-9]+[:\}]')

    key = root['isetup'].find('./topic[@name="consts"]/body')

    # Get auto constants.
    for td in key.findall('indent/table/tr/td'):
        if td.text is not None:
            if td.text.startswith('auto'):
                words.add('{' + td.text + '}')

    # Get all other constants.
    for dt in key.findall('dl/dt'):
        matches = re_names.findall(dt.text)

        for item in matches:
            words.add(item)

    # Add some prefixes.
    for item in ('{%', '{#', '{code:'):
        words.add(item)

    words = sorted(words, key=str.lower)

    return words


def get_event_functions():
    '''From isx.xml for innocode.api.'''

    words = []

    # Pattern: func|proc, name, (parameters), :, return;.
    re_names = re.compile(r'([f|p]\w+)'
                          r'\s+(\w+)'
                          r'(\(.*?\)){0,1}'
                          r':{0,1}'
                          r'\s*(\w*);$')

    wrapper = textwrap.TextWrapper(max_lines=settings['max_lines'])

    for key in root['isx'].findall('./topic/body/dl'):
        for items in zip(key.findall('dt'), key.findall('dd')):
            dt = items[0].text
            dd = items[1].text

            if not dt.startswith(('function', 'procedure')):
                continue

            word = re_names.findall(dt)

            if word:
                word = list(word[0])

                dd = dd.strip() if dd is not None else ''

                dd = '\\n'.join(wrapper.wrap(dd))

                if word[2] == '':
                    word[2] = '()'

                word.append(dd)
                words.append(word)

    return words


def get_functions():
    '''From isxfunc.xml for innocode.api.'''

    words = []

    # Pattern: func|proc, name, (parameters), :, return;.
    re_names = re.compile(r'([f|p]\w+)'
                          r'\s+(\w+)'
                          r'(\(.*?\)){0,1}'
                          r':{0,1}'
                          r'\s*(\w*);$')

    wrapper = textwrap.TextWrapper(max_lines=settings['max_lines'])

    for key in root['isxfunc'].findall('./isxfunc/category/subcategory/function'):
        word = key.find('prototype')
        word = word.text if word is not None else ''

        desc = key.find('description')
        desc = desc.text if desc is not None else ''

        desc = '\\n'.join(wrapper.wrap(desc))

        if word.startswith(('function', 'procedure')):
            matches = re_names.findall(word)

            if matches:
                item = list(matches[0])
                if item[2] == '':
                    item[2] = '()'

                item.append(desc)
                words.append(item)

    words.sort(key=lambda x: x[1])

    return words


def get_parameters():
    '''From isetup.xml for inno.properties.'''

    words = set()

    for key in root['isetup'].findall('./topic/body/paramlist/param'):
        word = key.get('name')

        if word:

            # Deprecated in Files section as of IS 3.0.5 (2002-12-16).
            if word == 'CopyMode':
                continue

            words.add(word)

    # Listed in isx.xml, not isetup.xml.
    for item in ('AfterInstall', 'BeforeInstall', 'Check'):
        if item not in words and item.lower() not in words:
            words.add(item)

    words = sorted(words, key=str.lower)

    return words


def get_pascal():
    '''No XML file, only literal keywords for inno.properties and innocode.api.'''

    words = ['and', 'begin', 'break', 'case', 'const', 'continue',
             'do', 'downto', 'else', 'end', 'except', 'exit', 'false',
             'finally', 'for', 'function', 'if', 'not', 'of', 'on',
             'or', 'procedure', 'repeat', 'then', 'to', 'true',
             'try', 'type', 'until', 'uses', 'var', 'while', 'with']

    words.sort()

    return words


def get_preprocessor():
    '''From ispp.xml for inno.properties.'''

    words = set()

    for key in root['ispp'].findall('./topic/topic[@id="directives"]'
                                    '/topic/title'):

        word = key.text.split(', ')

        if word:
            words.update(word)

    words = sorted(words, key=str.lower)

    return words


def get_preprocessor_functions():
    '''From ispp.xml for innopreprocessor.api.'''

    words = []

    # Pattern: return, name, (parameters).
    re_names = re.compile(r'^(\w+)'
                          r'\s+(\w+)'
                          r'(\(.*?\))$')

    for key in root['ispp'].findall('./topic/topic[@id="funcs"]'
                                    '/topic/section[@title="Prototype"]'
                                    '/pre/line'):

        word = re_names.findall(key.text)

        if word and word[0] not in words:
            words.append(word[0])

    words.sort(key=lambda x: x[1])

    return words


def get_preprocessor_vars():
    '''From ispp.xml for innopreprocessor.api.'''

    words = []

    for key in root['ispp'].findall('./topic/topic[@id="predefinedvars"]'
                                    '/keywords/kwd'):
        if key is not None:
            words.append(key.text)

    words.sort(key=str.lower)

    return words


def get_sections():
    '''From isetup.xml for inno.properties.'''

    words = []

    re_names = re.compile(r'\[([a-zA-Z]+)\] section$')

    for key in root['isetup'].findall('./topic/keyword'):
        word = key.get('value')

        if word:
            substring = re_names.match(word)

            if substring:
                words.append(substring.group(1))

    # May not be listed in Setup Script Sections.
    if 'Code' not in words and 'code' not in words:
        words.append('Code')

    words.sort(key=str.lower)

    return words


def get_setup():
    '''From isetup.xml for inno.properties'''

    words = set()

    for key in root['isetup'].findall('./setuptopic'):
        word = key.get('directive')

        if word:
            body = key.find('body')

            # Deprecated items start text with the word Obsolete.
            if body is not None:
                if body.text.strip().startswith('Obsolete'):
                    continue

            # BackColor and BackColor2 exist in the same tag.
            if word == 'BackColor':
                word2 = key.get('title', '')

                if 'BackColor2' in word2:
                    words.add('BackColor2')

            words.add(word)

    words = sorted(words, key=str.lower)

    return words


def parse(file):
    '''Parse XML file and return an ElementTree instance of root.'''

    # Read the xml file.
    with open(file) as r:
        content = r.read()

    # Remove entities and tags that cause problems.
    content = content.replace('&copy;', '')
    content = content.replace('&nbsp;', ' ')

    content = content.replace('<br/>\n', '\n')
    content = content.replace('<br/>', '\n')

    for item in ('b', 'i', 'p', 'tt'):
        content = content.replace('<' + item + '>', '')
        content = content.replace('</' + item + '>', '')

    content = re.sub(r'<link .+?>(.*?)</link>', r'\1', content, flags=re.I)
    content = re.sub(r'<a .+?>(.*?)</a>', r'\1', content, flags=re.I)
    content = re.sub(r'<anchorlink .+?>(.*?)</anchorlink>', r'\1', content, flags=re.I)

    # Make a cleaned xml file to view.
    file = os.path.join('output', os.path.basename(file))

    if settings['clean_xml_files']:
        if not os.path.isfile(file):
            with open(file, 'w') as w:
                w.write(content)

    # Get the root.
    root = xml.etree.ElementTree.fromstring(content)

    return root


# Header and footer for a new inno.properties.
header = r'''# Define SciTE settings for Inno Setup script files.

file.patterns.inno=*.iss;*.isl

filter.inno=Inno Setup (iss isl)|$(file.patterns.inno)|

*filter.inno=$(filter.inno)

lexer.$(file.patterns.inno)=inno

*language.innosetup=&InnoSetup|iss||

comment.block.inno=;~
'''

footer = r'''# User defined keywords
keywords6.$(file.patterns.inno)=

# Properties styles

# Default
style.inno.0=
# Comment
style.inno.1=$(colour.number),$(font.comment)
# Keyword
style.inno.2=$(colour.keyword)
# Parameter
style.inno.3=$(colour.keyword)
# Section
style.inno.4=back:#FFFFC0
# Preprocessor
style.inno.5=$(colour.preproc)
# Preprocessor (inline)
style.inno.6=$(colour.preproc)
# Pascal comment
style.inno.7=$(colour.code.comment.line),$(font.comment)
# Pascal keyword
style.inno.8=$(colour.keyword)
# User defined keyword
style.inno.9=$(colour.keyword)
# Double quoted string
style.inno.10=$(colour.string)
# Single quoted string
style.inno.11=$(colour.char)
# Identifier - lexer internal. It is an error if any text is in this style.
style.inno.12=$(colour.notused)

#if PLAT_WIN
#	# Replace PATH_TO_INNOSETUP by the path to your InnoSetup installation
#	command.compile.$(file.patterns.inno)="PATH_TO_INNOSETUP\iscc.exe" $(FileNameExt)
#	command.go.$(file.patterns.inno)="PATH_TO_INNOSETUP\Compil32.exe" $(FileNameExt)
'''


if __name__ == '__main__':

    # Check if source directory exist.
    if not os.path.isdir('issrc'):
        exit('Require directory named issrc')

    # Customize footer properties True or False.
    if settings['update_styles']:

        # Set default style to a variable.
        footer = footer.replace('style.inno.0=\n', 'style.inno.0=$(colour.default)\n')

        # Remove back and bolden section head.
        footer = footer.replace('style.inno.4=back:#FFFFC0\n', 'style.inno.4=bold\n')

    # Make output folder to save files.
    dirpath = os.path.join('output', 'api')

    if not os.path.exists(dirpath):
        os.makedirs(dirpath)

    # Prepare to wrap some text.
    wrapper = textwrap.TextWrapper()

    # Dictionary to store the root instances of the parsed files.
    root = {}

    # Dictionary to store the keyword dictionaries or lists.
    dic = {}

    # Populate the dictionary.
    dic['pascal'] = get_pascal()

    root['isetup'] = parse(os.path.join('issrc', 'ISHelp', 'isetup.xml'))
    dic['constants'] = get_constants()
    dic['parameters'] = get_parameters()
    dic['sections'] = get_sections()
    dic['setup'] = get_setup()
    dic['section'] = get_section_lists()

    for item in dic['setup']:
        dic['section']['setup'].append(item + '=')

    root['isx'] = parse(os.path.join('issrc', 'ISHelp', 'isx.xml'))
    dic['event_functions'] = get_event_functions()

    root['isxfunc'] = parse(os.path.join('issrc', 'ISHelp', 'isxfunc.xml'))
    dic['functions'] = get_functions()

    root['ispp'] = parse(os.path.join('issrc', 'Projects', 'ISPP', 'Help', 'ispp.xml'))
    dic['preprocessor'] = get_preprocessor()
    dic['preprocessor_funcs'] = get_preprocessor_functions()
    dic['preprocessor_vars'] = get_preprocessor_vars()


    # Make a new inno.properties.
    with open(os.path.join('output', 'inno.properties'), 'w') as w:
        w.write(header + '\n')

        # Sections.
        words = dic['sections']

        w.write('# Sections\n'
                'keywords.$(file.patterns.inno)=\\\n' +
                ' \\\n'.join( wrapper.wrap(' '.join(words).lower())) + '\n\n')

        # Keywords.
        words = dic['setup']

        w.write('# Keywords\n'
                'keywords2.$(file.patterns.inno)=\\\n' +
                ' \\\n'.join(wrapper.wrap(' '.join(words).lower())) + '\n\n')

        # Parameters.
        words = dic['parameters']

        w.write('# Parameters\n'
                'keywords3.$(file.patterns.inno)=\\\n' +
                ' \\\n'.join(wrapper.wrap(' '.join(words).lower())) + '\n\n')

        # Preprocessor keywords.
        words = dic['preprocessor']
        words = [word.replace('#', '') for word in words]

        w.write('# Preprocessor directives\n'
                'keywords4.$(file.patterns.inno)=\\\n' +
                ' \\\n'.join(wrapper.wrap(' '.join(words).lower())) + '\n\n')

        # Pascal keywords.
        words = dic['pascal']

        w.write('# Pascal keywords\n'
                'keywords5.$(file.patterns.inno)=\\\n' +
                ' \\\n'.join(wrapper.wrap(' '.join(words).lower())) + '\n\n')

        w.write(footer.strip() + '\n')


    # Write common api file.
    with open(os.path.join('output', 'api', 'innocommon.api'), 'w') as w:
        for item in dic['constants']:
            w.write(item + '\n')


    # Write Setup api file.
    with open(os.path.join('output', 'api', 'innosetup.api'), 'w') as w:
        for item in dic['setup']:
            w.write(item + '=\n')


    # Write Code api file.
    with open(os.path.join('output', 'api', 'innocode.api'), 'w') as w:

        # Pascal functions.
        for item in dic['functions']:
            pattern = '{1}{2}{0}'

            if item[3]:
                pattern += ' -> {3}'

            if item[4]:
                pattern += '\\n{4}'

            w.write(pattern.format(*item) + '\n')

        # Pascal event functions.
        for item in dic['event_functions']:
            pattern = '{1}{2}event {0}'

            if item[3]:
                pattern += ' -> {3}'

            if item[4]:
                pattern += '\\n{4}'

            w.write(pattern.format(*item) + '\n')

        # Pascal keywords.
        for item in sorted(dic['pascal'] + ['Result'], key=str.lower):
            if item in ('false', 'true'):
                w.write(item.capitalize() + '\n')
            else:
                w.write(item + '\n')


    # Write Preprocessor api file.
    with open(os.path.join('output', 'api', 'innopreprocessor.api'), 'w') as w:
        for item in dic['preprocessor']:
            w.write(item + '\n')

        for item in dic['preprocessor_vars']:
            w.write(item + '\n')

        for item in dic['preprocessor_funcs']:
            w.write('{1}{2}preprocess function -> {0}'.format(*item) + '\n')


    # Write inno{section}.api files.
    for key, value in dic['section'].items():
        if not value:
            continue

        file = os.path.join('output', 'api', 'inno{}.api'.format(key.lower()))

        with open(file, 'w') as w:
            for item in value:
                w.write(item + '\n')


    # Write json file or just print for verification.
    if settings['dic_output'] > 0:
        if settings['dic_output'] == 1:
            print(json.dumps(dic, indent=4, sort_keys=True))
        elif settings['dic_output'] == 2:
            with open(os.path.join('output', 'dic.json'), 'w') as w:
                json.dump(dic, w, indent=4, sort_keys=True)

    print('done')
