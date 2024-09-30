import random
import re
import signal
import sys
import unicodedata
from colorama import Fore, Style, init
import argparse
from sshkeyboard import listen_keyboard, stop_listening
from difflib import SequenceMatcher

result = None

# percentage of similarity, if it above ratio, it will consider as correct answer
ratio = 0.85

init(autoreset=True)

"""
TODO:
[Done] print annotation
[Done] check answer by vietnamese
[Done] + it has mainly 3 type of file (word, phrase, draft). Each type will proceed differently.
[Done] Key stroke detect
  Done Following task have problem, when running on WSL, library not work as expected cause WSL don't have access to hardware-level
  Done When answer by vietnamese (python keystrokes). Details of scenario of what you want? because it have user_input also.
      press 'enter':  skip. if you want to add previous word into wrong list
      press 'w':      add previous word to
      press 'space':  it mean we don't rememeber this word. This word will added into wrong list. 
      press 'i':      enter the answer with user input
      press 'h':      show help
  Key stroke for detect question just have eng and viet
[Done] + after done the list word and wrong word, automatically increase number of practice file 
[Done] + change commandline into 'python3 learn.py filename' instead of choose filename
[Done] + add highlighted text with phrase
[Done] after choose filename, it will select english as default if don't type 'vietnamese'
[Done] Fix bug when line don't have annotation
[Done] Show practice time when start
[Done] Remove the while loop of practic again
Optimize read_vocabulary function?
[No need] Fix functions for accept by english?
[Done] Detect ctrl + C signal and exit
[Done] Test answer with phrase and fix
[Done] Bug when press i, enter unicode, it don't show expected unicode
[Done] Answer with english and count the number of learning answer with english
[Done] When press 'Enter' first time, it will show example
Optimize when answer with English (example `handouts` is correct of 'handouts`)
[Done] Optimize when answer when tranlate from viet to english, compare 2 string and mark correct when it 90% similar
[Done] Auto add count of learning when not exist in file
[Done] Change script for handle translate to english
[Done] Change counter of file function
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
                        {"english": parts[0].strip(), "vietnamese": parts[1].strip()}
                    )
        elif "trans" in filename:
            for line in file:
                line = line.strip()
                parts = line.split(":")
                if len(parts) < 2:
                    continue
                else:
                    vocabulary.append(
                        {"english": parts[1].strip(), "vietnamese": parts[0].strip()}
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
                        # english = vacant
                        english = parts[0].strip()

                        # part_two = (adj - ˈveɪkənt, chỗ trống | the seat next to him was vacant)
                        part_two = parts[1].split(")")
                        phonetic = part_two[0].strip()

                        if "|" in part_two[1]:
                            # part_three = chỗ trống, the seat next to him was vacant
                            part_three = part_two[1].split("|")
                            vietnamese = part_three[0].strip().split(":")[1].strip()
                            annotation = part_three[1].strip()
                            vocabulary.append(
                                {
                                    "english": english,
                                    "phonetic": phonetic,
                                    "vietnamese": vietnamese,
                                    "annotation": annotation,
                                }
                            )
                        else:
                            vietnamese = parts[1].split(")")[1].strip()
                            vocabulary.append(
                                {
                                    "english": english,
                                    "phonetic": phonetic,
                                    "vietnamese": vietnamese
                                    # "annotation": annotation
                                }
                            )
    return vocabulary


def check_answer(question, answer, answer_with_viet):
    # print(f"{answer}, {question[2]}" if answer_with_viet else "{answer}, {question[0]}")
    if answer_with_viet:
        return answer == question["vietnamese"]
    else:
        return answer == question["english"]

def check_answer_similarity(question, answer, answer_with_viet=False):

    if answer_with_viet:
        print("ratio:", SequenceMatcher(None, question["english"], answer).ratio())
        if SequenceMatcher(None, question["vietnamese"], answer).ratio() > ratio:
            return True
        else: return False
    else:
        print("ratio:", SequenceMatcher(None, question["english"], answer).ratio())
        if SequenceMatcher(None, question["english"], answer).ratio() > ratio:
            return True
        else: return False

def print_vocabulary_list(vocabulary):
    print("English\tPronunciation\tTranslation\tAnnotate")
    for word in vocabulary:
        if "phonetic" in word:
            print(
                f"{word['english']}\t{word['phonetic']}\t{word['vietnamese']}\t{word.get('annotation','')}"
            )
        else:
            print(f"{word['english']}\t{word['vietnamese']}")

def highlight_differents_between_two_string(question, answer, answer_with_viet):
    if answer_with_viet:
        a = question["vietnamese"]
    else:
        a = question["english"]
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

# Can we detect it is vietnamese or english?
def output_answer(question, answer_with_viet):
    if answer_with_viet:
        print(f"{highlight_text(question['vietnamese'])} ")
    elif question.get('phonetic') != None:
        print(f"{highlight_text(question['english'])} ({highlight_text(question.get('phonetic'))})", end =' | ')
    else:
        print(f"{highlight_text(question['english'])}")
    if "annotation" in question:
        print(f"{question['annotation']}")


def signal_handler(sig, frame):
    print("\nCtrl+C detected! Exiting gracefully.")
    sys.exit(0)


def vocabulary_quiz(selected_file):
    global result
    # Loop for user practice again
    print("=============== new list voca ======================")
    vocabulary = read_vocabulary(selected_file)

    # print_vocabulary_list(vocabulary)
    # answer_with_viet == 1 <=> hiển thị tiếng anh, trả lời bằng tiếng việt
    print(
        "Choose the language that you answer (English or Vietnamese, Vietnamese as default):\n1. English\n2. Vietnamese"
    )
    try:
        choice = input("Your choice: ")
        if choice == "" or int(choice) != 1:
            answer_with_viet = 1
        else:
            answer_with_viet = 0
    except ValueError:
        answer_with_viet = False

    print(
        "Dịch từ tiếng Anh sang tiếng Việt:"
        if answer_with_viet
        else "Translate from English to Vietnamese:"
    )

    wrong_answers = []
    count = 0
    prev_question = None
    question = None
    print_counter_of_file(selected_file)
    # if question have fully part (eng, viet, phonetic, annotation)
    if "phonetic" in random.choice(vocabulary):
        # browse through each voca in list voca
        while vocabulary:
            result = None
            if question:
                prev_question = question
            question = random.choice(vocabulary)
            vocabulary.remove(question)
            count += 1

            # if answer with viet `Ex: debate (n - dɪˈbeɪt): ??`
            if answer_with_viet:
                print(
                    f"[{count}] {question['english']} ({question['phonetic']})",
                    end="",
                )
            else:
                print(f"[{count}] {question['vietnamese']}", end=": ")

            listen_keyboard(on_press=press, on_release=release)
            if result == "enter":
                output_answer(question, answer_with_viet)
                while True:
                    listen_keyboard(on_press=press, on_release=release)
                    if result == "enter":
                       break

            elif result == "space":
                # Add keystroke detection to this
                user_answer = input()
                if check_answer(question, user_answer, answer_with_viet):
                    if "annotation" in question:
                        print("  example:", question["annotation"])
                else:
                    output_answer(question, answer_with_viet)
                    print("wrong, added to list wrong word!")
                    wrong_answers.append(question)

            # add word to wrong list
            elif result == "w":
                wrong_answers.append(question)
                output_answer(question, answer_with_viet)
                print("    Added to wrong list")
                continue
            # show help or add previous word to wrong list
            elif result == "h" or result == "p":
                if result == "h":
                    print(
                        """
    press 'enter':  skip. if you want to add previous word into wrong list
    press 'p':      add previous word to wrong list
    press 'space':  enter the answer with user input
    press 'w':      it mean we don't rememeber this word. This word will added into wrong list. 
    press 'h':      show help"""
                    )
                elif result == "p":
                    wrong_answers.append(prev_question)
                    print("  [Added previous word to wrong list]")
                # Wait another input: 'enter' or 'space' or 'i'
                while True:
                    listen_keyboard(on_press=press, on_release=release)
                    if result == "enter":
                        output_answer(question, answer_with_viet)
                        break

                    elif result == "space":
                        # Add keystroke detection to this
                        user_answer = input()
                        if check_answer(question, user_answer, answer_with_viet):
                            if "annotation" in question:
                                print("  example:", question["annotation"])
                        else:
                            print("wrong, added to list wrong word!")
                            wrong_answers.append(question)
                        break

                    # add word to wrong list
                    elif result == "w":
                        wrong_answers.append(question)
                        print("    Added to wrong list")
                        break

    # question have just the eng, viet
    else:
        while vocabulary:
            question = random.choice(vocabulary)
            # print("question: ", question)
            if answer_with_viet:
                print(f"[{count}] {highlight_text(question['english'])}", end=": ")
            else:
                print(f"[{count}] {highlight_text(question['vietnamese'])}", end=": ")
            count += 1
            # Whether answer correct or not
            listen_keyboard(on_press=press, on_release=release)
            if result == "enter":
                output_answer(question, answer_with_viet)
                while True:
                    listen_keyboard(on_press=press, on_release=release)
                    if result == "enter":
                       break

            elif result == "space":
                # Add keystroke detection to this
                user_answer = input()
                if check_answer_similarity(question, user_answer, answer_with_viet):
                    if "annotation" in question:
                        print("  example:", question["annotation"])
                else:
                    output_answer(question, answer_with_viet)
                    print("wrong, added to list wrong word!")
                    highlight_differents_between_two_string(question, user_answer, answer_with_viet)
                    wrong_answers.append(question)

            # add word to wrong list
            elif result == "w":
                wrong_answers.append(question)
                output_answer(question, answer_with_viet)
                print("    Added to wrong list")
                continue
            # show help or add previous word to wrong list
            elif result == "h" or result == "p":
                if result == "h":
                    print(
                        """
    press 'enter':  skip. if you want to add previous word into wrong list
    press 'p':      add previous word to wrong list
    press 'space':  enter the answer with user input
    press 'w':      it mean we don't rememeber this word. This word will added into wrong list. 
    press 'h':      show help"""
                    )

                # Wait another input: 'enter' or 'space' or 'i'
                while True:
                    listen_keyboard(on_press=press, on_release=release)
                    if result == "enter":
                        output_answer(question, answer_with_viet)
                        break

                    elif result == "space":
                        # Add keystroke detection to this
                        user_answer = input()
                        if check_answer(question, user_answer, answer_with_viet):
                            if "annotation" in question:
                                print("  example:", question["annotation"])
                        else:
                            print("wrong, added to list wrong word!")
                            wrong_answers.append(question)
                        break

                    # add word to wrong list
                    elif result == "w":
                        wrong_answers.append(question)
                        print("    Added to wrong list")
                        break
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
    args = parser.parse_args()
    vocabulary_quiz(args.filename)
