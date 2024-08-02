def search_vocabulary(files, target_word):
  found_lines = []
  for file_name in files:
    try:
      with open(file_name, 'r') as file:
        for line in file:
          if target_word in line:
            found_lines.append(line)
    except FileNotFoundError:
      print(f"File not found: {file_name}")
  return found_lines

if __name__ == "__main__":
  file_names = ["Voca_01.txt", "Voca_02.txt"]
  while True:
    target_word = input("nhập từ bạn cần tìm: ")
    
    if not target_word:
      break

    found_lines = search_vocabulary(file_names, target_word)

    if found_lines:
      print(f"Các dòng chứa '{target_word}': ")
      for line in found_lines:
        print(line, end="")
    else:
      print(f"Không tìm thấy '{target_word}' trong bất kỳ file nào.")
