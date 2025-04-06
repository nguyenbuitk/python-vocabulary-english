import random
import re
import signal
import sys
import unicodedata
from colorama import Fore, Style, init
import argparse
from sshkeyboard import listen_keyboard, stop_listening
from difflib import SequenceMatcher
from deep_translator import GoogleTranslator
import difflib

result = None

# percentage of similarity, if it above ratio, it will consider as correct answerv 
ratio = 0.92

init(autoreset=True)

"""
TODO:
[Done] print annotation
[Done] check answer by vn
[Done] + it has mainly 3 type of file (word, phrase, draft). Each type will proceed differently.
[Done] Key stroke detect
  Done Following task have problem, when running on WSL, library not work as expected cause WSL don't have access to hardware-level
  Done When answer by vn (python keystrokes). Details of scenario of what you want? because it have user_input also.
      press 'enter':  skip. if you want to add previous word into wrong list
      press 'w':      add previous word to
      press 'space':  it mean we don't rememeber this word. This word will added into wrong list. 
      press 'i':      enter the answer with user input
      press 'h':      show help
  Key stroke for detect question just have eng and viet
[Done] + after done the list word and wrong word, automatically increase number of practice file 
[Done] + change commandline into 'python3 learn.py filename' instead of choose filename
[Done] + add highlighted text with phrase
[Done] after choose filename, it will select en as default if don't type 'vn'
[Done] Fix bug when line don't have annotation
[Done] Show practice time when start
[Done] Remove the while loop of practic again
Optimize read_vocabulary function?
[No need] Fix functions for accept by en?
[Done] Detect ctrl + C signal and exit
[Done] Test answer with phrase and fix
[Done] Bug when press i, enter unicode, it don't show expected unicode
[Done] Answer with en and count the number of learning answer with en
[Done] When press 'Enter' first time, it will show example
Optimize when answer with en (example `handouts` is correct of 'handouts`)
[Done] Optimize when answer when tranlate from viet to en, compare 2 string and mark correct when it 90% similar
[Done] Auto add count of learning when not exist in file
[Done] Change script for handle translate to en
[Done] Change counter of file function
[Done] Use translate API
??Change  read_vocabulary function for read all file or not??
Trouble issue when annotation have vietnamese. Ex:
    Comparison between:
        String 1: she lay down 'nằm' on the couch to watch tv
        String 2: she lay on chair for waching tv            
        she lay down 'nằm' on the couch to watch tv
        ratio: 0.9534883720930233
[Done] Script for learning sentence files
change script for learning file with only sentence of vietnamese?
Change the read_voca function ??
                                                             ┌─────────────────────┐
                                              ┌──────────────►answer with sentences│
                                      ┌───────┼──────┐       └─────────────────────┘
                           ┌──────────►answer with en│       ┌─────────────────────┐
                      ┌────┼────┐     └──────────────┴───────►answer with one word │
          ┌───────────►full voca│     ┌──────────────┐       └─────────────────────┘
    ┌─────┼────┐      └─────────┴─────►answer with vi│                              
    │ file type│                      └──────────────┘                              
    └─────┬────┘      ┌─────────┐     ┌──────────────┐                              
          └───────────►sentences│     │answer with en│                              
                      └─────────┘     └──────────────┘                              

When answer with english sentence, display the two correct answer, correct answer in file and correct answer with api
[Done] Change the way of display hightlight text
    Ex:
    String 1: she hung her clothes on wire hangers.
    String 2: she hanged her cloth on the metal 
Features: count the average ratio
[Done] Optimize all function, script
Dùng API để chỉnh sửa file trước khi đưa ra câu hỏi, điều này giúp giảm thời gian loading cho các lần học sau!
"""


def press(key):
    global result
    if key == "esc":
        stop_listening()
    elif key == "h" or key == "p":
        stop_listening()
        result = key
    elif key == "space" or key == "enter" or key == "w":
        result = key
        stop_listening()


def release(key):
    pass


def processing_file(filename):
    pass

def read_vocabulary(filename):
    vocabulary = []
    with open(filename, "r", encoding="utf-8") as file:
        # Open sentences file
        if "phrase" in filename or "Phrase" in filename:
            for line in file:
                line = line.strip()
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                else:
                    vocabulary.append(
                        {"en": parts[0].strip(), "vn": parts[1].strip()}
                    )
        
        else:
            for line in file:
                # a soft opening (n - sɒft ˈəʊpənɪŋ) buổi khai trương nhỏ | the restaurant had a soft opening
                # line example: vacant(adj - ˈveɪkənt)chỗ trống | the seat next to him was vacant
                line = line.strip()
                if line:
                    parts = line.split("(")
                    if len(parts) < 1:
                        continue
                    elif len(parts) < 2 or parts[0] == "end":
                        # print("not enough infor")
                        if len(parts[0]) < 5:
                            continue
                        else: 
                            vocabulary.append(
                                {
                                    "en": parts[0],
                                }
                            )
                    else:
                        # en = vacant
                        # parts[0] = a soft opening
                        en = parts[0].strip()

                        # part_two = (adj - ˈveɪkənt, chỗ trống | the seat next to him was vacant)
                        # parts[1] = n - sɒft ˈəʊpənɪŋ) buổi khai trương nhỏ | the restaurant had a soft opening
                        part_two = parts[1].split(")")
                        
                        # part_two = ["n - sɒft ˈəʊpənɪŋ","buổi khai trương nhỏ | the restaurant had a soft opening"]
                        phonetic = part_two[0].strip()

                        if "|" in part_two[1]:
                            # part_three = ["buổi khai trương nhỏ", "the restaurant had a soft opening"]
                            part_three = part_two[1].split("|")
                            vn = part_three[0].strip()
                            annotation = part_three[1].strip()
                            vocabulary.append(
                                {
                                    "en": en,
                                    "phonetic": phonetic,
                                    "vn": vn,
                                    "annotation": annotation,
                                }
                            )
                        else:
                            vn = parts[1].split(")")[1].strip()
                            vocabulary.append(
                                {
                                    "en": en,
                                    "phonetic": phonetic,
                                    "vn": vn
                                    # "annotation": annotation
                                }
                            )
    return vocabulary


def check_answer(question, answer, answer_with_viet,  trans_to_en=False):
    # If trans_to_en = True, check the setences english instead of single word
    # print(f"{answer}, {question[2]}" if answer_with_viet else "{answer}, {question[0]}")
    if answer_with_viet:
        ratio_score = SequenceMatcher(None, question["vn"].lower(), answer.lower()).ratio()
        print("ratio:", ratio_score)
        if ratio_score > ratio:
            return True
        else: return False
    else:
        if trans_to_en:
            correct_answer = question.get('annotation') if question.get('annotation') else question['en']
            correct_answer_2 = translate_en_vi(question.get('sentence_vi'), trans_to_vi=False)
            ratio_score = SequenceMatcher(None, correct_answer.lower().strip('.'), answer.lower()).ratio()
            ratio_score_2 = SequenceMatcher(None, correct_answer_2.lower().strip('.'), answer.lower()).ratio()
            question["annotation2"] = {"higher_score": ratio_score_2 > ratio_score, "value": correct_answer_2}
            print("ratio:", max(ratio_score, ratio_score_2))
            if max(ratio_score, ratio_score_2) > ratio:
                return True
            else: return False
        else:
            return answer == question["en"]

def print_vocabulary_list(vocabulary):
    print("en\tPronunciation\tTranslation\tAnnotate")
    for word in vocabulary:
        if "phonetic" in word:
            print(
                f"{word['en']}\t{word['phonetic']}\t{word['vn']}\t{word.get('annotation','')}"
            )
        else:
            print(f"{word['en']}\t{word.get('vn')}")

def tokenize(s):
    return re.split('\s+', s)
def untokenize(ts):
    return ' '.join(ts)

def equalize(s1, s2):
    l1 = tokenize(s1)
    l1_highlight = l1
    l2 = tokenize(s2)
    l2_highlight = l2 
    res1 = []
    res2 = []
    prev = difflib.Match(0,0,0)
    for match in difflib.SequenceMatcher(a=l1, b=l2).get_matching_blocks():
        if (prev.a + prev.size != match.a):
            for i in range(prev.a + prev.size, match.a):
                l1_highlight[i] = "\033[92m" + l1[i] +  "\033[0m"
                # ele = ["\033[91m" + '_' * len(l1[i]) + "\033[0m"]
                # ele = ['_' * len(l1[i])]

                # res2 += ele
            res1 += l1_highlight[prev.a + prev.size:match.a]
        if (prev.b + prev.size != match.b):
            for i in range(prev.b + prev.size, match.b):
                l2_highlight[i] = "\033[91m" + l2[i] +  "\033[0m"
                # ele = ['_' * len(l2[i])]
                # res1 += ele
            res2 += l2[prev.b + prev.size:match.b]
        res1 += l1[match.a:match.a+match.size]
        res2 += l2[match.b:match.b+match.size]
        prev = match

    return untokenize(res1), untokenize(res2)


def show_comparison(s1, s2, width=40, margin=10, sidebyside=True, compact=False):
    s1, s2 = equalize(s1,s2)
    print(s1)
    print(s2)
def highlight_differents_between_two_string(question, answer, answer_with_viet, trans_to_en=False):
    if trans_to_en and question.get('annotation'):
        question['en'] = question['annotation']
    correct_answer = question['vn'] if answer_with_viet else question['en']
    correct_answer = correct_answer.lower()
    answer = answer.lower()
    
    if question.get('annotation2'):
        correct_answer_2 = question['annotation2']['value'].lower().strip('.')
        print("Default ans vs api answer")
        show_comparison(correct_answer, correct_answer_2)
    
        # if the ratio of api answer is higher
        if question['annotation2']['higher_score'] == True:
            print("Your answer with api answer")
            show_comparison(correct_answer_2, answer)
            return
    
    # if the ratio of default is higher
    print("Default answer vs your answer")
    show_comparison(correct_answer, answer)
    
def highlight_differents_between_two_string_2(question, answer, answer_with_viet, trans_to_en=False):
    if trans_to_en and question.get('annotation'):
        question['en'] = question['annotation']
    a = question['vn'] if answer_with_viet else question['en']
    a = a.lower()
    answer = answer.lower()
    result_a = []
    result_b = []
    # Loop through both strings, character by character
    for i in range(max(len(a), len(answer))):
        char_a = a[i] if i < len(a) else ''
        char_b = answer[i] if i < len(answer) else ''
        
        if char_a != char_b:
            result_a.append(f'\033[91m{char_a}\033[0m' if char_a else ' ')  # Red for differences in 'a'
            result_b.append(f'\033[92m{char_b}\033[0m' if char_b else ' ')  # Green for differences in 'b'
        else:
            result_a.append(char_a)  # Unchanged text as is
            result_b.append(char_b)

    # Join and return the highlighted results
    highlighted_a = ''.join(result_a)
    highlighted_b = ''.join(result_b)
    
    print(f"Comparison between:\Correct\t: {highlighted_a}\nYour ans\t: {highlighted_b}")
    return highlighted_a, highlighted_b

def highlight_text(text):
    return re.sub(r"`([^`]+)`", f"{Fore.GREEN}`\\1`{Style.RESET_ALL}", text)

def update_counter_of_file(filename, answer_with_viet=True, trans_to_en=False):
    with open(filename, "r", encoding="utf-8") as file:
        data = file.readlines()
    try:
        a = int(data[0])
    except Exception as e:
        data_new = "0\n"
        data.insert(0,data_new)
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data_new)
    try:
        a = int(data[1])
    except Exception as e:
        data_new = "0\n"
        data.insert(1,data_new)
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data_new)
    try:
        a = int(data[2])
    except Exception as e:
        data_new = "0\n"
        data.insert(2,data_new)
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data_new)
    if trans_to_en:
        data[2] = str(int(data[2]) + 1) + "\n"
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data)
    elif answer_with_viet:
        data[0] = str(int(data[0]) + 1) + "\n"
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data)
    else:
        data[1] = str(int(data[1]) + 1) + "\n"
        with open(filename, "w", encoding="utf-8") as file:
            file.writelines(data)
        
def print_counter_of_file(filename):
    with open(filename, "r", encoding="utf-8") as file:
        data = file.readlines()
    try:
        a = int(data[0])
    except Exception as e:
        print("Practice times when answer with vi: 0")
        print("Practice times when answer with en: 0")
        print("Practice times when answer with sentences: 0")
    else:
        data[0] = data[0].strip()
        print(f"Practice times when answer with vi:", data[0])
        print(f"Practice times when answer with en:", data[1].strip())
        print(f"Practice times when answer with sentences:", data[2].strip())

# Can we detect it is vn or en?
def output_answer(question, answer_with_viet, trans_to_en=False):
    # Output sentences if trans_to_en = True
    if trans_to_en:
        print(f"{question['annotation']}") if question.get('annotation') else print(question['en'])
        return
    if answer_with_viet:
        print(f" {highlight_text(question.get('vn'))}")
    elif question.get('phonetic') != None:
        print(f"{highlight_text(question.get('en'))} ({highlight_text(question.get('phonetic'))})", end =' | ')
    else:
        print(f" {highlight_text(question.get('en'))}")
    if "annotation" in question:
        print(f"{question['annotation']}")

def print_help():
    print("""
    press 'enter':  skip. if you want to add previous word into wrong list
    press 'space':  enter the answer with user input
    press 'w':      it means we don't remember this word. This word will be added into wrong list. 
    press 'h':      show help
    your input?
    """)

def handle_keystrokes(question, wrong_answer, answer_with_viet, trans_to_en=False):
    global result
    while True:
        listen_keyboard(on_press=press, on_release=release)
        if result == "enter":
            output_answer(question, answer_with_viet, trans_to_en)
            break
        
        elif result == "space":
            user_answer = input()
            if check_answer(question, user_answer, answer_with_viet, trans_to_en):
                if "annotation" in question and trans_to_en is False:
                    print("  example:", question["annotation"])
                if trans_to_en:
                    highlight_differents_between_two_string(question, user_answer, answer_with_viet, trans_to_en)
            else:
                if trans_to_en:
                    highlight_differents_between_two_string(question, user_answer, answer_with_viet, trans_to_en)
                    while True:
                        user_answer = input()
                        if check_answer(question, user_answer, answer_with_viet, trans_to_en):
                            highlight_differents_between_two_string(question, user_answer, answer_with_viet, trans_to_en)
                            break
                else:
                    output_answer(question, answer_with_viet, trans_to_en)
                    print("wrong, added to list wrong word!")
                    wrong_answer.append(question)
            break
        
        elif result == "w":
            wrong_answer.append(question)
            print("    Added to wrong list")
            break
        
        elif result == "h":
            print_help()
        
        # elif result == "p":
        #     if prev_question:
        #         wrong_answer.append(prev_question)
        #         print("  [Added previous word to wrong list]")
        #     break

def ask_question(count, question, answer_with_viet, trans_to_en=False):
    if trans_to_en:
        # Print the vn sentence
        if 'vn' in question:
            question['sentence_vi'] = question['vn']
            print(f"[{count}] {question['vn']}", end=": ")
            return
        if question.get('annotation'):
            question['sentence_vi'] = translate_en_vi(question.get('annotation')) 
        else: question['sentence_vi'] = translate_en_vi(question['en'])
        print(f"[{count}] {question['sentence_vi']}", end=": ")
    else:
        if answer_with_viet:
            print(f"[{count}] {question.get('en')} ({question.get('phonetic')})", end="")
        else:
            print(f"[{count}] {question.get('vn')}", end=": ")

def signal_handler(sig, frame):
    print("\nCtrl+C detected! Exiting gracefully.")
    sys.exit(0)

# default trans from en to vi
def translate_en_vi(text, trans_to_vi=True):
    if trans_to_vi:
        translator = GoogleTranslator(source = 'en', target ='vi')
        translation = translator.translate(text)
        return translation
    else: 
        translator = GoogleTranslator(source = 'vi', target ='en')
        translation = translator.translate(text)
        return translation
    
def vocabulary_quiz(selected_file, answer_with_viet, trans_to_en=False):
    global result
    vocabulary = read_vocabulary(selected_file)
    
    # # Can move this to parameter ??
    # print("Choose the language that you answer (English or Vietnamese, Vietnamese as default):")
    # print("1. English\n2. Vietnamese")
    # try:
    #     choice = input("Your choice: ")
    #     answer_with_viet = 1 if choice == "" or int(choice) != 1 else 0
    # except ValueError:
    #     answer_with_viet = 1
    
    print("Translate from Vietnamese to English:" if answer_with_viet else "Translate from English to Vietnamese:")

    wrong_answers = []
    count = 0
    prev_question = None
    print_counter_of_file(selected_file)

    # If this file 
    if "phonetic" in random.choice(vocabulary):
        while vocabulary:
            result = None
            # prev_question = question if 'question' in locals() else None
            question = random.choice(vocabulary)
            vocabulary.remove(question)
            count += 1

            # How to handle the situation of user want to trans to english?
            if trans_to_en:
                ask_question(count, question, answer_with_viet, trans_to_en=True)
                handle_keystrokes(question, wrong_answers, answer_with_viet,  trans_to_en=True)
            else:
                ask_question(count, question, answer_with_viet)
                handle_keystrokes(question, wrong_answers, answer_with_viet)
    else:
        while vocabulary:
            result = None
            question = random.choice(vocabulary)
            vocabulary.remove(question)
            count += 1
            ask_question(count, question, answer_with_viet, trans_to_en=True)
            handle_keystrokes(question, wrong_answers, answer_with_viet,  trans_to_en=True)
    
    if wrong_answers:
        print("\nList wrong word:")
        print_vocabulary_list(wrong_answers)

    update_counter_of_file(selected_file, answer_with_viet=answer_with_viet, trans_to_en=trans_to_en)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # Do something about here, so what when running python3 Voca_28.txt, it will take Voca_28.txt as argument and input to file
    parser = argparse.ArgumentParser(description="Learning Vocabulary")
    parser.add_argument("--file", required=True, help="The vocabulary file to use for the quiz")
    parser.add_argument("--lang", choices=["en", "vn"], required=True, help = "Choose for answer with vietnamese or english")
    parser.add_argument("--trans_to_en", action='store_true', help = "Add this flag if you want to translate to english")
    args = parser.parse_args()
    answer_with_viet = True if args.lang == "vn" else False
    vocabulary_quiz(args.file, answer_with_viet, args.trans_to_en)
