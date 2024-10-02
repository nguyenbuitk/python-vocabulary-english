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

result = None

# percentage of similarity, if it above ratio, it will consider as correct answer
ratio = 0.85

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
use translate API
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


def read_vocabulary(filename):
    vocabulary = []
    with open(filename, "r", encoding="utf-8") as file:
        # Open draft file
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
        elif "trans" in filename:
            for line in file:
                line = line.strip()
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                else:
                    vocabulary.append(
                        {"en": parts[1].strip(), "vn": parts[0].strip()}
                    )
        # Open word and draft file type
        else:
            for line in file:
                # line example: vacant(adj - ˈveɪkənt)chỗ trống | the seat next to him was vacant
                line = line.strip()
                if line:
                    parts = line.split("(")
                    if len(parts) < 2 or parts[0] == "end":
                        # print("not enough infor")
                        continue
                    else:
                        # en = vacant
                        en = parts[0].strip()

                        # part_two = (adj - ˈveɪkənt, chỗ trống | the seat next to him was vacant)
                        part_two = parts[1].split(")")
                        phonetic = part_two[0].strip()

                        if "|" in part_two[1]:
                            # part_three = chỗ trống, the seat next to him was vacant
                            part_three = part_two[1].split("|")
                            vn = part_three[0].strip().split(":")[1].strip()
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


def check_answer(question, answer, answer_with_viet, similar=False):
    # print(f"{answer}, {question[2]}" if answer_with_viet else "{answer}, {question[0]}")
    if answer_with_viet:
        if similar:
            print("ratio:", SequenceMatcher(None, question["en"], answer).ratio())
            if SequenceMatcher(None, question["vn"].lower(), answer.lower()).ratio() > ratio:
                return True
            else: return False
        return answer == question["vn"]
    else:
        if similar:
            print("ratio:", SequenceMatcher(None, question["en"], answer).ratio())
            if SequenceMatcher(None, question["en"].lower(), answer.lower()).ratio() > ratio:
                return True
            else: return False
        return answer == question["en"]

def check_answer_similarity(question, answer, answer_with_viet=False):

    if answer_with_viet:
        print("ratio:", SequenceMatcher(None, question["en"], answer).ratio())
        if SequenceMatcher(None, question["vn"].lower(), answer.lower()).ratio() > ratio:
            return True
        else: return False
    else:
        print("ratio:", SequenceMatcher(None, question["en"], answer).ratio())
        if SequenceMatcher(None, question["en"].lower(), answer.lower()).ratio() > ratio:
            return True
        else: return False

def print_vocabulary_list(vocabulary):
    print("en\tPronunciation\tTranslation\tAnnotate")
    for word in vocabulary:
        if "phonetic" in word:
            print(
                f"{word['en']}\t{word['phonetic']}\t{word['vn']}\t{word.get('annotation','')}"
            )
        else:
            print(f"{word['en']}\t{word['vn']}")

def highlight_differents_between_two_string(question, answer, answer_with_viet):
    if answer_with_viet:
        a = question["vn"].lower()
    else:
        a = question["en"].lower()
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
    
    print(f"Comparison between:\nString 1: {highlighted_a}\nString 2: {highlighted_b}")
    return highlighted_a, highlighted_b

def highlight_text(text):
    return re.sub(r"`([^`]+)`", f"{Fore.GREEN}`\\1`{Style.RESET_ALL}", text)

def update_counter_of_file(filename, answer_with_viet=True):
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
            
    if answer_with_viet:
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
        print("Practice times when answer with viet:",0)
        print("Practice times when answer with eng:",0)
    else:
        data[0] = data[0].strip()
        print(f"Practice times when answer with viet:", data[0])
        print(f"Practice times when answer with eng:", data[1])

# Can we detect it is vn or en?
def output_answer(question, answer_with_viet):
    if answer_with_viet:
        print(f" {highlight_text(question['vn'])}")
    elif question.get('phonetic') != None:
        print(f" {highlight_text(question['en'])} ({highlight_text(question.get('phonetic'))})", end =' | ')
    else:
        print(f" {highlight_text(question['en'])}")
    if "annotation" in question:
        print(f"{question['annotation']}")

def print_help():
    print("""
    press 'enter':  skip. if you want to add previous word into wrong list
    press 'p':      add previous word to wrong list
    press 'space':  enter the answer with user input
    press 'w':      it means we don't remember this word. This word will be added into wrong list. 
    press 'h':      show help
    """)

def handle_keystrokes(question, prev_question, wrong_answer, answer_with_viet, similarity=False):
    global result
    while True:
        listen_keyboard(on_press=press, on_release=release)
        if result == "enter":
            output_answer(question, answer_with_viet)
            break
        
        elif result == "space":
            user_answer = input()
            if check_answer(question, user_answer, answer_with_viet, similarity):
                if "annotation" in question:
                    print("  example:", question["annotation"])
                if similarity:
                    highlight_differents_between_two_string(question, user_answer, answer_with_viet)
            else:
                output_answer(question, answer_with_viet)
                print("wrong, added to list wrong word!")
                wrong_answer.append(question)
                if similarity:
                    highlight_differents_between_two_string(question, user_answer, answer_with_viet)
                    while True:
                        user_answer = input()
                        if check_answer_similarity(question, user_answer, answer_with_viet):
                            highlight_differents_between_two_string(question, user_answer, answer_with_viet)
                            break
            break
        
        elif result == "w":
            wrong_answer.append(question)
            print("    Added to wrong list")
            break
        
        elif result == "h":
            print_help()
        
        elif result == "p":
            if prev_question:
                wrong_answer.append(prev_question)
                print("  [Added previous word to wrong list]")
            break

def ask_question(count, question, answer_with_viet):
    if answer_with_viet:
        print(f"[{count}] {question['en']} ({question['phonetic']})", end="")
    else:
        print(f"[{count}] {question['vn']}", end=": ")

def signal_handler(sig, frame):
    print("\nCtrl+C detected! Exiting gracefully.")
    sys.exit(0)

def translate_to_vietnamese(text):
    translator = GoogleTranslator(source = 'en', target ='vi')
    translation = translator.translate(text)
    return translation

def vocabulary_quiz(selected_file, trans_to_en=False):
    global result
    vocabulary = read_vocabulary(selected_file)
    
    # Can move this to parameter ??
    print("Choose the language that you answer (English or Vietnamese, Vietnamese as default):")
    print("1. English\n2. Vietnamese")
    try:
        choice = input("Your choice: ")
        answer_with_viet = 1 if choice == "" or int(choice) != 1 else 0
    except ValueError:
        answer_with_viet = 1
    
    print("Translate from Vietnamese to English:" if answer_with_viet else "Translate from English to Vietnamese:")

    wrong_answers = []
    count = 0
    prev_question = None
    print_counter_of_file(selected_file)

    # If this file 
    if "phonetic" in random.choice(vocabulary):
        while vocabulary:
            result = None
            prev_question = question if 'question' in locals() else None
            question = random.choice(vocabulary)
            vocabulary.remove(question)
            count += 1

            ask_question(count, question, answer_with_viet)
            handle_keystrokes(question, prev_question, wrong_answers, answer_with_viet)
    else:
        while vocabulary:
            question = random.choice(vocabulary)
            count += 1
            ask_question(count, question, answer_with_viet)
            if answer_with_viet:
                handle_keystrokes(question, prev_question, wrong_answers, answer_with_viet)
            else:
                handle_keystrokes(question, prev_question, wrong_answers, answer_with_viet, similarity=True)
            vocabulary.remove(question)
    
    if wrong_answers:
        print("\nList wrong word:")
        print_vocabulary_list(wrong_answers)

    update_counter_of_file(selected_file,answer_with_viet=answer_with_viet)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    # Do something about here, so what when running python3 Voca_28.txt, it will take Voca_28.txt as argument and input to file
    parser = argparse.ArgumentParser(description="Learning Vocabulary")
    parser.add_argument("filename", help="The vocabulary file to use for the quiz")
    parser.add_argument("--trans_to_en", action='store_true', help = "Add this flag if you want to translate to english")
    args = parser.parse_args()
    vocabulary_quiz(args.filename, args.trans_to_en)
