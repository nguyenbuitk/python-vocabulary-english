import random
import re
import unicodedata
from colorama import Fore, Style, init
init(autoreset=True)


'''
to do:
vv print annotation
vv check answer by vietnamese
draw desire follow of app? 
  + it has mainly 3 type of file (word, phrase, draft). Each type will proceed differently. 
  + when answer by vietnamese:  
    press 'enter': skip. if you want to add previous word into wrong list, press 'w' 
    press 'space', it mean we don't rememeber this word. This word will added into wrong list. 
  + after done the list word and wrong word, automatically increase number of practice file 
  + change commandline into 'python3 learn.py filename' instead of choose filename
  + add highlighted text with phrase
  + after choose filename, it will display instead of current manner: 
    you want answer by english or vietnamese: 
    1. english 
    2. vietnamese 
'''
def read_vocabulary(filename):
  vocabulary = []
  with open(filename, 'r', encoding='utf-8') as file:
    # Open draft file
    if "phrase" in filename:
      for line in file:
        line = line.strip()
        parts = line.split(':')
        if len(parts) < 2:
          continue
        else:
          vocabulary.append({
            'english': parts[0].strip(),
            'vietnamese': parts[1].strip()
          })
          
      
    # Open word and draft file
    else: 
      for line in file:
        # line example: vacant(adj - ˈveɪkənt)chỗ trống | the seat next to him was vacant
        line = line.strip()
        if line:
          parts = line.split('(')
          if len(parts) < 2 or parts[0] == "end":
            # print("not enough infor")
            continue
          else:
            # english = vacant
            english = parts[0].strip()
            
            # part_two = (adj - ˈveɪkənt, chỗ trống | the seat next to him was vacant)
            part_two = parts[1].split(')')
            phonetic = part_two[0].strip()

            if '|' in part_two[1]:
              # part_three = chỗ trống, the seat next to him was vacant
              part_three = part_two[1].split('|')
              vietnamese = part_three[0].strip()
              annotation = part_three[1].strip()
              vocabulary.append({
                "english": english,
                "phonetic": phonetic,
                "vietnamese": vietnamese,
                "annotation": annotation
              })
            else:
              vietnamese = parts[1].split(')')[1].strip()
              vocabulary.append({
                "english": english,
                "phonetic": phonetic,
                "vietnamese": vietnamese,
                "annotation": annotation
              })
  return vocabulary

def check_answer(question, answer, is_english):
    # print(f"{answer}, {question[2]}" if is_english else "{answer}, {question[0]}")
    if is_english:
        return answer == question['vietnamese']
    else:
        return answer == question['english']

def print_vocabulary_list(vocabulary):
  print("English\tPronunciation\tTranslation\tAnnotate")
  for word in vocabulary:
    if 'phonetic' in word:
      print(f"{word['english']}\t{word['phonetic']}\t{word['vietnamese']}\t{word.get('annotation','')}")
    else:
      print(f"{word['english']}\t{word['vietnamese']}")

    
def highlight_text(text):
    return re.sub(r'`([^`]+)`', f'{Fore.RED}`\\1`{Style.RESET_ALL}', text)
  
def vocabulary_quiz(files):
  while True:
    print("Choose a file to practice vocabulary: ")
    for i, file in enumerate(files):
      print(f"{i + 1}. {file}")
    file_choice = int(input("Enter the number of file: ")) - 1
    if 0 <= file_choice < len(files):
      selected_file = files[file_choice]
    else:
      print("Invalid file choice. Please choose a valid file.")
      continue
    
    vocabulary = read_vocabulary(selected_file)
    
    # print_vocabulary_list(vocabulary)
    # is_english == 1 <=> hiển thị tiếng anh, trả lời bằng tiếng việt
    is_english = input("Choose the language is displayed (English or Vietnamese): ").strip().lower() == 'english'
    
    print("Dịch từ tiếng Anh sang tiếng Việt:" if is_english else "Translate from English to Vietnamese:")
    
    wrong_answers = []
    count = 0
    question = random.choice(vocabulary)
    if 'phonentic' in question:
      # browse through each voca in list voca
      while vocabulary:
        question = random.choice(vocabulary)
        # print("question: ", question)
        if is_english:
          print(f"[{count}] {question['english']} ({question['phonetic']})", end=': ')
        else:
          print(f"[{count}] {question['vietnamese']}", end=': ')
        count += 1

        user_answer = input()
        # Whether answer correct or not
        if check_answer(question, user_answer, is_english) or user_answer == 'n':
            if (user_answer == 'n'):
              print(question['vietnamese'])
            if 'annotation' in question:
              print("  example:", question['annotation'])
        else:
            wrong_answers.append(question)
            print(f"Wrong! The correct answer is: {question['vietnamese'] if is_english else question['english']}")
            if 'annotation' in question:
              print("  example: ", question['annotation'])
        vocabulary.remove(question)
    else:
      while vocabulary:
        question = random.choice(vocabulary)
        # print("question: ", question)
        if is_english:
          print(f"[{count}] {highlight_text(question['english'])}", end=': ')
        else:
          print(f"[{count}] {highlight_text(question['vietnamese'])}", end=': ')
        count += 1

        user_answer = input()
        # Whether answer correct or not
        if check_answer(question, user_answer, is_english) or user_answer == 'n':
            if (user_answer == 'n'):
              print(question['vietnamese'])
            if 'annotation' in question:
              print("  example:", question['annotation'])
        else:
            wrong_answers.append(question)
            print(f"Wrong! The correct answer is: {highlight_text(question['vietnamese']) if is_english else highlight_text(question['english'])}")
        vocabulary.remove(question)

    if wrong_answers:
      print("\nList wrong word:")
      print_vocabulary_list(wrong_answers)

    continue_quiz = input("Do you want to continue (yes/no)? ")
    if continue_quiz.lower() != 'yes':
        break
if __name__ == '__main__':
    files = ['Voca_01.txt', 'Voca_02.txt', 'Voca_32.txt', 'Voca_33.txt', 'Voca_34.txt', 'Voca_35.txt', 'Voca_40.txt', 'Voca_41.txt', "Voca_40_phrase.md"]  # Thay thế danh sách tệp của bạn tại đây
    vocabulary_quiz(files)
