import speech_recognition as sr
import requests
from bs4 import BeautifulSoup
# Initialize the recognizer
recognizer = sr.Recognizer()
def get_audio(timeout=10):
    try:
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=0.2)
            print('Listening...')
            audio = recognizer.listen(source, timeout=timeout)  # Set a timeout for listening
            command = recognizer.recognize_google(audio)
            command = command.lower()
            print(f"Recognized text: {command}")
            return command
    except sr.WaitTimeoutError:
        print('Timeout exceeded. No speech detected.')
    except sr.UnknownValueError:
        print('Speech recognition could not understand audio.')
    except sr.RequestError as e:
        print(f'Speech recognition request failed: {e}')
    return ""
def preprocess_text(text):
    words = text.split()
    new_words = []
    for i in range(len(words)):
        if i == 0 or words[i] != words[i - 1]:
            new_words.append(words[i])
    preprocessed_text = ' '.join(new_words)
    return preprocessed_text


def calculate_lcs_dp_table(a, b):
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n):
        for j in range(m):
            if a[i] == b[j]:
                dp[i + 1][j + 1] = dp[i][j] + 1
            else:
                dp[i + 1][j + 1] = max(dp[i + 1][j], dp[i][j + 1])

    return dp


def backtrack_lcs_sequence(dp, a, b):
    i, j = len(a), len(b)
    lcs = []
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            lcs.append(a[i - 1])
            i -= 1
            j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return lcs[::-1]


def compare_texts(input_text, recognized_text):
    input_words = input_text.split()
    recognized_words = recognized_text.split()
    lcs_dp_table = calculate_lcs_dp_table(input_words, recognized_words)
    lcs_sequence = backtrack_lcs_sequence(lcs_dp_table, input_words, recognized_words)
    input_index = 0
    recognized_index = 0
    word_comparison = []
    for word in lcs_sequence:
        while input_index < len(input_words) and input_words[input_index] != word:
            word_comparison.append((input_words[input_index], "", False))
            input_index += 1
        while recognized_index < len(recognized_words) and recognized_words[recognized_index] != word:
            word_comparison.append(("", recognized_words[recognized_index], False))
            recognized_index += 1
        word_comparison.append((word, word, True))
        input_index += 1
        recognized_index += 1

    while input_index < len(input_words):
        word_comparison.append((input_words[input_index], "", False))
        input_index += 1

    while recognized_index < len(recognized_words):
        word_comparison.append(("", recognized_words[recognized_index], False))
        recognized_index += 1

    return word_comparison


def fetch_pronunciation(word):
    try:
        url = f"https://www.dictionary.com/browse/{word}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        pronunciation = soup.find('span', {'class': 'pron-spell-content'})
        return pronunciation.text if pronunciation else None
    except Exception as e:
        print(f"Error fetching pronunciation for {word}: {e}")
        return None


def generate_assessment_report(input_text, recognized_text, word_comparison):
    print("\nAssessment Report")
    print(f"Original Text: {input_text}")
    print(f"Recognized Text: {recognized_text}\n")

    correct_words = 0
    total_words = len(word_comparison)
    word_accuracy = []
    for input_word, recognized_word, is_correct in word_comparison:
        if is_correct:
            print(f"Correctly Spoken: {input_word}")
            correct_words += 1
            word_accuracy.append(1.0)  # Word accuracy is 1.0 (100%)
        else:
            if input_word and recognized_word:
                matching_chars = sum(1 for a, b in zip(input_word, recognized_word) if a == b)
                accuracy = matching_chars / max(len(input_word), len(recognized_word))
                word_accuracy.append(accuracy)
            else:
                word_accuracy.append(0.0)  # Word accuracy is 0.0 (0%)

            print(f"Incorrectly Spoken: {input_word} -> {recognized_word}")
            correct_pronunciation = fetch_pronunciation(input_word)
            spoken_pronunciation = fetch_pronunciation(recognized_word)
            if correct_pronunciation:
                print(f"   Correct Pronunciation: {correct_pronunciation}")
            if spoken_pronunciation:
                print(f"   Your Pronunciation: {spoken_pronunciation}")

    overall_accuracy = (correct_words / total_words) * 100
    print(f"\nOverall Accuracy: {overall_accuracy:.2f}%\n")

    print("Word Accuracy Report:")
    for idx, (input_word, recognized_word, _) in enumerate(word_comparison):
        accuracy = word_accuracy[idx] * 100
        if input_word and recognized_word:
            print(f"{input_word} -> {recognized_word}: {accuracy:.2f}%")
        elif input_word:
            print(f"{input_word} -> [MISSING]: {accuracy:.2f}%")
        elif recognized_word:
            print(f"[MISSING] -> {recognized_word}: {accuracy:.2f}%")


# Main loop
while True:
    try:
        input_text = input("Enter the text string you want to speak: ")

        if not input_text:
            print("No input text provided. Please try again.")
            continue

        input_text = preprocess_text(input_text)
        recognized_text = get_audio()

        if recognized_text:
            recognized_text = preprocess_text(recognized_text)
            word_comparison = compare_texts(input_text.lower(), recognized_text.lower())
            generate_assessment_report(input_text.lower(), recognized_text.lower(), word_comparison)
        else:
            print("No speech detected. Match Percentage: 0.00%")
    except KeyboardInterrupt:
        print("Program terminated by user.")
        break
