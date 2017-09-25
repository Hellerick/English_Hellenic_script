import os
import platform
import re
import pickle

# rules:
# https://ru.wikipedia.org/wiki/%D0%90%D0%BD%D0%B3%D0%BB%D0%BE-%D1%80%D1%83%D1%81%D1%81%D0%BA%D0%B0%D1%8F_%D0%BF%D1%80%D0%B0%D0%BA%D1%82%D0%B8%D1%87%D0%B5%D1%81%D0%BA%D0%B0%D1%8F_%D1%82%D1%80%D0%B0%D0%BD%D1%81%D0%BA%D1%80%D0%B8%D0%BF%D1%86%D0%B8%D1%8F

project_path = {
    'DESKTOP-62BVD4A': 'd:\KPV\Github\English_Hellenic_script',
    'hellerick-C17A': r'/home/hellerick/PycharmProjects/English_Hellenic_script',
    'Superkomp': r'D:\HCF\PyCharmProjects\English_Hellenic_script',
}[platform.node()]

Grecocoptic_2017 = 'GC7'

system = Grecocoptic_2017

English_alphabet = 'abcdefghijklmnopqrstuvwxyzáâéëíïúſ'

hyphenate = True


def translit_grc(word):
    if system == 'GC7':
        translit_pairs=[
            ['ce', 'ϡε'], ['ci', 'ϡι'], ['cy', 'ϡι'], ['ya', 'ια'], ['ye', 'ιε'],
            ['yi', 'ιι'], ['yo', 'ιο'], ['yu', 'ιυ'], ['ch', 'ϭ'],
            ['sh', 'ϭ'], ['th', 'θ'],
            ['a', 'α'], ['b', 'β'], ['c', 'κ'],
            ['d', 'δ'], ['e', 'ε'], ['f', 'φ'], ['g', 'γ'], ['h', '῾'], ['i', 'ι'],
            ['j', 'ϫ'], ['k', 'κ'], ['l', 'λ'], ['m', 'μ'], ['n', 'ν'],
            ['o', 'ο'], ['p', 'π'], ['q', 'κ'], ['r', 'ρ'], ['s', 'σ'], ['t', 'τ'],
            ['u', 'υ'], ['v', 'ϝ'], ['w', 'ϝ'], ['x', 'ξ'], ['y', 'ι'], ['z', 'ζ'],
            ['á', 'ά']
        ]
    for pair in translit_pairs:
        word = word.replace(*pair)
    word = re.sub(r'σ\b', r'ς', word)
    for a,b in zip('αεηιοόωῳ', 'ἁἑἡἱὁὅὑὡᾡ'):
        word = re.sub('῾'+a, b, word)
    return word


def try_lat_phonet_matching(prev_grc, next_lat, next_phonet, rules):
    global watch
    watch += f'\n - {prev_grc}, {next_lat}, {repr(next_phonet)}'
    if next_lat=='' and next_phonet==[]:
        # print(f' : {prev_grc}')
        return prev_grc
    else:
        for rule in rules:
            if re.match(rule[0], next_lat) and re.match(rule[1], ' '.join(next_phonet)):
                # print('   rule:', rule)
                if rule[1]=='':
                    phonet_len = 0
                else:
                    phonet_len = len(re.match(rule[1], ' '.join(next_phonet)).group().split())
                attempt = try_lat_phonet_matching(
                    prev_grc+rule[2],
                    next_lat[re.match(rule[0], next_lat).span()[1]:],
                    next_phonet[phonet_len:],
                    rules
                )
                if attempt:
                    # watch += '\n'+repr(rule)
                    return attempt


def phonet_grc(lat, phonet, rules=[]):
    global watch
    watch = f'{lat} [{phonet}]'
    cyr = try_lat_phonet_matching(prev_grc='', next_lat=lat, next_phonet=phonet.split(), rules=rules)
    if cyr == None:
        print(watch)
        raise Exception('Not matched!')
    # print('phonet_grc', cyr)
    return cyr


def convert_word(word, grc_dict):
    if word == '':
        return word
    if word[0].isupper():
        if len(word)<2 or word[1].islower() or word[1] in ['’']:
            case = 'title'
        else:
            case = 'allcaps'
    else:
        case = 'lower'
    word = grc_dict[word.lower()]
    if case == 'title':
        word = word[0].upper() + word[1:]
    elif case == 'allcaps':
        word = word.upper()
    # print('convert_word', word)
    return word


def convert_text(text, grc_dict):
    text = re.sub(r'(['+English_alphabet+r',]\s)I\b', r'\1i', text)
    text = re.sub(r'(['+English_alphabet+r',]\s?—\s?)I\b', r'\1i', text)
    text = re.split('(['+English_alphabet+English_alphabet.upper()+'’]*['+English_alphabet+English_alphabet.upper()+'][0-9]?)', text)
    #print(f'Text <{text}>')
    for n, word in enumerate(text):
        if n%2 == 1:
            text[n] = convert_word(word, grc_dict)
    return ''.join(text)


def try_breaking(word, grc_dict, phonet_dict, rules):
    boundary = sorted(list(range(1, len(word))), key = lambda x: abs(x - len(word)/2))
    for b in boundary:
        if (word[:b] in grc_dict or word[:b] in phonet_dict) and (word[b:] in grc_dict or word[b:] in phonet_dict):
            print(f'Word broken: {word[:b]} + {word[b:]}')
            returned = [grc_dict[w] if w in grc_dict else phonet_grc(w, phonet_dict[w], rules) for w in [word[:b], word[b:]]]
            return '¬'.join(returned)


def postprocess(grc_dict, user_dict, full_normalization = False):
    lat_words = grc_dict.keys()
    grc_words = '\n'.join(grc_dict.values()) # т̈
    grc_words = re.sub(r'σ\b', r'ς', grc_words)
    for a,b in zip('αεηιοόωῳ', 'ἁἑἡἱὁὅὑὡᾡ'):
        grc_words = re.sub('῾'+a, b, grc_words)
    grc_dict = dict(zip(lat_words, grc_words.split('\n')))
    for word in user_dict:
        grc_dict[word] = user_dict[word]
    return grc_dict


def dialog_mode(grc_dict):
    while True:
        u = input()
        try:
            print(grc_dict[u.lower()])
        except KeyError:
            pass
        if u == '':
            return None


def make_local_dictionary(file_path, word_list):
    local_dict_path = re.sub(r'\.[a-z]+\Z', '.Dictionary.txt', file_path)
    user_dict_path = os.path.join(project_path, 'Dictionaries', 'User_dict.'+system+'.txt')
    US_dict_path = os.path.join(project_path, 'Dictionaries', 'cmudict.0.7a')
    UK_dict_path = os.path.join(project_path, 'Dictionaries', 'beep-1.0')
    local_dict_path = os.path.join(project_path, 'Dictionaries', 'Local_dict.txt')
    local_dict_pickle_path = os.path.join(project_path, 'Dictionaries', 'Local_dict.pickle')

    if os.path.exists(local_dict_pickle_path):
        return pickle.load(open(local_dict_pickle_path, mode='rb'))

    rules_path = os.path.join(project_path, 'Transcription_rules.'+system+'.txt')
    with open(rules_path, mode='rt', encoding='utf8') as f:
        rules =  f.read()

    rules = re.sub(r'#.*?\n', r'\n', rules)
    rules = rules.split('\n')
    rules = [re.sub(r'(.*)#.*', r'\1', line) for line in rules]
    rules = [line for line in rules if line != '']
    rules = [re.split(r' ?= ?', line) for line in rules]
    for r in rules:
        if r[1] == '-': r[1] = ''
    for r in rules:
        if r[2] == '-': r[2] = ''
    rules.sort(key = lambda x: len(x[1]), reverse=True)
    rules.sort(key = lambda x: len(x[0]), reverse=True)
    rules.sort(key = lambda x: x[1]=='')
    # for r in rules: print(r)

    with open(user_dict_path, mode='rt', encoding='utf8') as f:
        user_dict =  f.read()
    user_dict = re.sub(r'  +', r' ', user_dict)
    user_dict = re.sub(r'#.*?\n', r'\n', user_dict)
    user_dict = re.sub(r' ?\n ?', r'\n', user_dict)
    user_dict = user_dict.split('\n')
    user_dict = [re.sub(r'(.*)#.*', r'\1', line) for line in user_dict]
    user_dict = [line for line in user_dict if line != '']
    user_dict = [re.split(r' ?= ?', line) for line in user_dict]
    user_dict = {line[0]:line[1] for line in user_dict}
    # print(user_dict)

    with open(US_dict_path, mode='rt', encoding='utf8') as f:
        US_dict =  f.read()
    US_dict = re.sub(r';.*?\n', r'\n', US_dict)
    # US_dict = re.sub(r'\(1\)', r'', US_dict)
    US_dict = re.sub(r"'", r'’', US_dict)
    US_dict = US_dict.split('\n')
    # US_dict = [re.sub(r'(.*);.*', r'\1', line) for line in US_dict]
    US_dict = [line for line in US_dict if line != '']
    US_dict = [re.split(r'  ', line) for line in US_dict]
    US_dict = {line[0].lower():line[1] for line in US_dict}
    # print(US_dict)

    with open(UK_dict_path, mode='rt', encoding='utf8') as f:
        UK_dict =  f.read()
    UK_dict = re.sub(r'#.*?\n', r'\n', UK_dict)
    UK_dict = re.sub(r'\(1\)', r'', UK_dict)
    UK_dict = re.sub(r"'", r'’', UK_dict)
    UK_dict = UK_dict.split('\n')
    # UK_dict = [re.sub(r'(.*)#.*', r'\1', line) for line in UK_dict]
    UK_dict = [line for line in UK_dict if line != '']
    UK_dict = [re.split(r'\s+', line) for line in UK_dict]
    UK_dict = {line[0].lower():' '.join(line[1:]).upper() for line in UK_dict}
    # print(UK_dict)

    phonet_dict = dict()
    # for word in word_list:
    #     if word in US_dict:
    #         phonet_dict[word] = US_dict[word]
    #     elif word in UK_dict:
    #         phonet_dict[word] = UK_dict[word]
    for word in US_dict:
        phonet_dict[word] = US_dict[word]
    for word in UK_dict:
        if not word in phonet_dict:
            phonet_dict[word] = UK_dict[word]

    grc_dict = {word:user_dict[word] for word in user_dict}
    for word in word_list:
        if not word in user_dict and word in phonet_dict:
            grc_dict[word] = phonet_grc(word, phonet_dict[word], rules)
    for word in word_list:
        if not word in grc_dict:
            attempt = try_breaking(word, grc_dict, phonet_dict, rules)
            if attempt:
                grc_dict[word] = attempt
            else:
                print('Not found:', word)
                grc_dict[word] = translit_grc(word)
    if system=='GC7':
        grc_dict = postprocess(grc_dict, user_dict, full_normalization=False)
    grc_dict = eval(hyphenate_code(repr(grc_dict)))
    # print('make_local_dictionary', grc_dict)

    grc_list = sorted([word+' = '+grc_dict[word] for word in grc_dict])
    grc_list = '\n'.join(grc_list)
    with open(local_dict_path, mode='wt', encoding='utf8') as f:
        f.write(grc_list)

    if not 'default.txt' in file_path:
        pickle.dump(grc_dict, open(local_dict_pickle_path, mode='wb'))

    return grc_dict


def hyphenate_code(code):
    # ¬
    if hyphenate:
        vow = 'аеёиіоуъыэюяѵѡ'
        dia = '́̀̈'
        con = 'бвв̆гджзҙѕйіклмнпрсҫтўфхцчшщѵѳџ'
        trucon = re.sub('[іѵ]', '', con)
        let = vow+dia+con+'ь'
        vow, dia, con, let, trucon = [f'[{x}]' for x in [vow, dia, con, let, trucon]]
        code = re.sub(r'('+let+'+)', r'<<\1>>', code)
        code = re.sub(r'('+con+'ь?'+vow+')', r'¬\1', code)
        code = re.sub(r'в¬̆', r'¬в̆', code)
        code = re.sub(r'('+vow+'|'+dia+')('+vow+')', r'\1¬\2', code)
        code = re.sub(r'('+vow+')¬й', r'\1й¬', code)
        code = re.sub(r'('+vow+')¬й', r'\1й¬', code)
        code = re.sub(r'(а|о)¬у', r'\1у', code)
        for c in ['дж', 'жў', 'іу']:
            code = re.sub(c[0]+'¬'+c[1], '¬'+c, code)
        for c in ['еі', 'аі', 'аѵ', 'оі', 'оѵ', 'ѵе', 'ѵі', 'ѵо', 'іа', 'іѵ']:
            code = re.sub(c[0]+'¬'+c[1], c, code)
        code = re.sub(r'¬([лмнр])('+trucon+')', r'\1¬\2', code)
        code = re.sub(r'¬([лмнр])('+trucon+')', r'\1¬\2', code)
        code = re.sub(r'¬('+con+r')\1', r'\1¬\1', code)
        code = re.sub(r'¬([лмнр])('+trucon+')', r'\1¬\2', code)
        code = re.sub(r'([бгдкптф])¬([лр])', r'¬\1\2', code)
        code = re.sub(r'¬([дт])л', r'\1¬л', code)
        code = re.sub(r'(['+con+'])¬([лр])', r'¬\1\2', code)
        code = re.sub(r'¬?('+con+')¬іу', r'¬\1іу', code)
        code = re.sub(r'¬('+con+'+¬>>)', r'\1', code)
        # print('HYPHEN', code[-50:])
        code = re.sub(r'ѵ¬('+vow+')', r'¬ѵ\1', code)
        code = re.sub(r'¬рѵ('+vow+')', r'р¬ѵ\1', code)
        code = re.sub(r'с¬т', r'¬ст', code)
        code = re.sub(r'¬>>', r'>>', code)
        code = re.sub(r'<<¬+', r'<<', code)
        code = re.sub(r'¬('+vow+dia+'?)>>', r'\1>>', code)
        code = re.sub(r'<<('+trucon+'+'+dia+'?|'+vow+dia+'?)¬', r'<<\1', code)
        code = re.sub(r'(<<|>>)', r'', code)
        code = re.sub(r'¬', r'­', code)
    else:
        code = re.sub('¬','',code)
    return code


def convert_code(code, file_path=os.path.join(project_path, 'default.txt')):
    code = re.sub(r'\{[^}]+\}\{=([^}]+)\}', r'\1', code) # {U.S.}{=Ю.С.}
    code = re.sub(r'\{(\d)\}', r'\1', code) # use{1}
    code = re.sub(r'\{<([^}]+)>\}', r'<!--(--\1--)-->', code) # {<III>} Not to be cyrillized
    code = re.sub(r'['+English_alphabet.upper()+English_alphabet+r']+\{=([^}]+?)\}', r'\1', code) # Dukh{=Дух}
    code = re.split('(<[^>]+>)', code)
    word_list = list()
    for n, text in enumerate(code):
        if n%2 == 0:
            local_list = re.findall('['+English_alphabet+'’]*['+English_alphabet+'][0-9]?', text.lower())
            word_list += local_list
    word_list = sorted(list(set(word_list)))
    word_list_path = re.sub(r'\.[a-z]+\Z', '.WordList.txt', file_path)
    with open(word_list_path, 'wt', encoding='utf8') as word_list_file:
        word_list_file.write('\n'.join(word_list))
    grc_dict = make_local_dictionary(file_path, word_list)
    for n, text in enumerate(code):
        if n%2 == 0:
            code[n] = convert_text(text, grc_dict)
    code = ''.join(code)
    code = re.sub(r'<!--\(--([^>]+)--\)-->', r'\1', code)
    return code


def convert_file(file_path):
    with open(file_path, mode='rt', encoding='utf8') as f:
        code = f.read()
    code = convert_code(code)
    output_path = re.sub(r'(.*)\.([a-zA-Z0-9]+)', r'\1.Cyr.\2', file_path)
    with open(output_path, mode='wt', encoding='utf8') as f:
        f.write(code)


def main():

    # file_path = os.path.join(project_path, 'Examples', 'Eoin Colfer. Artemis Fowl 01.html')
    file_path = r"D:\HCF\Dropbox\Job-shared\Lib\Ransome, Arthur\Ransome - Swallows and Amazons.fodt"
    file_path = r"D:\HCF\PyCharmProjects\English_Hellenic_script\Examples\About the Greek alphabet.txt"

    if True:
        convert_file(file_path)

    if True:
        print(convert_code('''
    derived
    '''))

    # print(convert_code('''sometimes'''))
    print(watch)

    # print(hyphenate_code('іу'))


if __name__ == '__main__':
    main()