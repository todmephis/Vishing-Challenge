import openai
import speech_recognition as sr
import re
from colorama import Fore, Back, Style
from io import BytesIO
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "1"
from pygame import mixer
import argparse
import requests
import base64
import io
import sys
from tqdm import tqdm
import getArtifacts

defVoiceName = 'es-US-Neural2-A'
defLangCode = 'es-US'

def split_by_actual_punctuation(input_str):
    # Define the regular expression for splitting around double quotes
    quote_regex = r'("[^"]*")'
    # Split the input string around double quotes
    split_str = re.split(quote_regex, input_str)
    # Initialize the list of split sections
    split_list = []
    # Loop over each split section
    for section in split_str:
        # If the section is enclosed in double quotes, add it to the split list as is
        if section.startswith('"') and section.endswith('"'):
            split_list.append(section)
        else:
            # Define the regular expression for splitting the section by actual punctuation marks
            regex = r'(?:[^".,!?;:\s]+|\S+(?<!\s))[\.,!?;:]+(?=\s+|$|\W)'
            # Find all non-overlapping matches of the regular expression in the section
            matches = re.findall(regex, section)
            # Extract the corresponding substrings from the section
            start_index = 0
            for match in matches:
                match_obj = re.search(re.escape(match), section[start_index:])
                end_index = start_index + match_obj.end()
                split_list.append(section[start_index:end_index].strip())
                start_index = end_index
            # Add any remaining text to the list
            if start_index < len(section):
                split_list.append(section[start_index:].strip())        
    joined_list = []
    i = 0
    while i < len(split_list):
        # if (split_list[i].endswith(",") or split_list[i].endswith(":")) and i + 1 < len(split_list):
        if split_list[i].endswith(",") and i + 1 < len(split_list):
            combined_string = split_list[i] + " " + split_list[i+1]
            if len(combined_string) <= 100:
                joined_list.append(combined_string)
                i += 2
            else:
                joined_list.append(split_list[i][:-1])
                joined_list.append(split_list[i+1])
                i += 2
        else:
            joined_list.append(split_list[i])
            i += 1
    return joined_list
api_keys, scenarios = getArtifacts.getScriptArtifacts(
    base64.b64decode(base64.b64decode('ZFhNdFpXRnpkQzB5T2pRNE56VXhNR0ptTFdZMVpXUXRORFk0TnkwNFltSmhMVE5pWW1NeFpEWTNOemt4Wmc9PQ==')).decode('utf-8'),
    base64.b64decode(base64.b64decode('WjJWMFZtbHphR2x1WjFOamNtbHdkRUZ5ZEdsbVlXTjBjdz09')).decode('utf-8')
)
if api_keys is not None:
    OPENAI_API_KEY = api_keys['openai_api_key']
    GOOGLE_CLOUD_API_KEY = api_keys['google_cloud_api_key']
# Assuming you have a function called auth_to_openai defined somewhere that uses OPENAI_API_KEY
# auth_to_openai(OPENAI_API_KEY)
elif scenarios is not None:
    pass
else:
    print("Error retrieving script artifacts")
    exit(1)


def syntax_highlighting(text):
    # Split the string by triple backticks
    split_string = re.split(r'```', text)
    # Wrap all even items in ANSI color codes for a grey background
    for i in range(len(split_string)):
        if i % 2 == 0:            
            # Regular expression to match text within double quotes
            quotes_regex = re.compile(r'"([^"]*)"')
            split_string[i] = quotes_regex.sub(
                lambda match: f"\033[48;2;191;191;191m\033[30m\"{match.group(1)}\"\033[0m",
                split_string[i]
            )
        else:
            split_string[i] = re.sub(r'^\w*\s?', '', split_string[i])
            split_string[i] = '\033[48;2;191;191;191m\033[30m' + split_string[i] + '\033[0m'
    # Join the string back together
    output_string = ''.join(split_string)        
        # Highlight text between backticks in all sections
    backticks_regex = re.compile(r'`([^`]*)`')
    output_string = backticks_regex.sub(
        lambda match: f"{Fore.BLUE}{Style.BRIGHT}`{match.group(1)}`{Style.RESET_ALL}",
        output_string
    )
    # Return the output string
    return output_string
def speak_with_google_cloud(text, voice_name, language_code, google_cloud_api_key):
    url = "https://texttospeech.googleapis.com/v1/text:synthesize"
    headers = {"X-Goog-Api-Key": google_cloud_api_key}
    # Set up the request data
    data = {
        "input": {"text": text},
        "voice": {"languageCode": language_code, "name": voice_name},
        "audioConfig": {"audioEncoding": "LINEAR16"},
    }
    # Make the request
    response = requests.post(url, json=data, headers=headers)
    if response.status_code == 200:
        audio_content = base64.b64decode(response.json()['audioContent'])
        audio_fp = io.BytesIO(audio_content)
        mixer.init()
        mixer.music.load(audio_fp)
        mixer.music.play()
        while mixer.music.get_busy():
            pass  # Wait for the audio to finish playing
    else:
        print(f"Failed to synthesize speech: {response.text}")

def skip_over_code(text):
    sections = text.split('```')
    even_sections = [sections[i] for i in range(len(sections)) if i % 2 == 0]
    return ' '.join(even_sections)

def speak_and_print(content, speaker, voice_name, language_code, google_cloud_api_key):
    print(f"\n{speaker}:", syntax_highlighting(content))
    if content:
        verbal_response = skip_over_code(content)
        pattern = re.compile("[^\\w\\s]")
        for sentence_chunk in split_by_actual_punctuation(verbal_response):
            sentence_chunk = sentence_chunk.strip('"')
            if sentence_chunk:
                cleaned_sentence = re.sub(pattern, "", sentence_chunk)
                speak_with_google_cloud(cleaned_sentence, voice_name, language_code, google_cloud_api_key)              

def get_audio_input(google_cloud_api_key, prompt, retries=2):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        if prompt:
            print("\n" + '*'*40 + "\nAhora puedes hablar...")
        try:
            audio = recognizer.listen(source, timeout=15)
            user_input = recognizer.recognize_google(audio,language="es-US")
            print("\nEntrada parseada:", user_input)
            return user_input
        except sr.WaitTimeoutError:
            if retries > 0:
                print("\nNo se detectó alguna respuesta. Preguntando si el usuario está alli...")
                speak_and_print("¿Sigues allí?", "System", defVoiceName, defLangCode, google_cloud_api_key)  # Use default or fetched values for voice_name and language_code
                return get_audio_input(prompt, retries-1, google_cloud_api_key)
            else:
                print("\nDesconectando la llamada, intentalo más tarde.")
                speak_and_print("Desconectando la llamada, intentalo más tarde.", "System", defVoiceName, defLangCode, google_cloud_api_key)  # Use default or fetched values for voice_name and language_code
                sys.exit()
        except sr.UnknownValueError:
            # If Google Speech Recognition could not understand the audio
            return None
        except sr.RequestError as e:
            # If there was an issue with the Google Speech Recognition request
            print("Error al contactar los servicios de Google Speech Recognition; {0}".format(e))
            return None

def process_voice_command(user_input):
    """
    Process voice commands. 
    If the command is 'Dial Extension X', switch scenario without using the command for response generation.
    If the command is 'Terminate Call', terminate the program.
    """
    # Pattern for dialing an extension
    dial_extension_pattern = re.compile(r'Llamar extensión (\d+)', re.IGNORECASE)
    # Pattern for terminating the call
    terminate_call_pattern = re.compile(r'Terminar llamada', re.IGNORECASE)        
    dial_match = dial_extension_pattern.match(user_input)
    terminate_match = terminate_call_pattern.match(user_input)
    if dial_match:
        extension = dial_match.group(1)
        if change_scenario(extension):
            # Scenario was changed successfully; generate initial response for the new scenario.
            generate_initial_response_for_scenario()
            return True  # Indicate that a scenario change command was processed.
        else:
            print("Extensión invalida. Staying in the current scenario.")
            return False  # Scenario change failed or was invalid.
    elif terminate_match:
        print("Terminando llamada. Adiós!")
        sys.exit()  # Terminate the program
    else:
        # If the input does not match any special commands, indicate no special processing was done.
        return False
def change_scenario(extension):
    global selected_scenario, message_context
    # Find and update to the new scenario.
    new_scenario = next((scenario for scenario in scenarios if scenario['target_name'] == extension), None)
    if new_scenario:
        selected_scenario = new_scenario
        print(f"Cambiando al escenario: {selected_scenario['description']}")
        # Clear previous context and start fresh for the new scenario
        message_context.clear()
        message_context.append({"role": "system", "content": selected_scenario['botdirections']})
        return True
    else:
        return False
def update_message_context_for_scenario():
    global message_context, selected_scenario
    # Clear previous context or start fresh for the new scenario
    message_context = [
        {"role": "system", "content": f"{selected_scenario['botdirections']}"},
        # Any initial user or system messages relevant to the new scenario
    ]
def generate_initial_response_for_scenario():
    """
    Generate and provide the initial response for the new scenario using the 'answer' field,
    along with the specified purpose.
    """
    # Assuming 'selected_scenario' is globally accessible and contains the 'answer' field
    initial_response = selected_scenario.get('answer', 'Default response if answer not found.')        
    # Log the initial response to the console and use text-to-speech to vocalize it
    #print(f"System (Initial Response): {initial_response}")
    speak_and_print(initial_response, "Sistema", selected_scenario['voice_name'], selected_scenario['language_code'], GOOGLE_CLOUD_API_KEY)
def query_chatgpt(user_input):
    global message_context
    message_context.append({"role": "user", "content": user_input})
    response = openai.ChatCompletion.create(
        model="gpt-4-turbo-preview",
        messages=message_context
    )
    response_object = response.choices[0].message
    chatbot_response = response_object.content
    return chatbot_response

def auth_to_openai(openai_api_key):
    openai.api_key = openai_api_key
auth_to_openai(OPENAI_API_KEY)
parser = argparse.ArgumentParser(description='Process some integers.')
parser.add_argument('-t', '--target', nargs='?', default=scenarios[0]['target_name'],
                    help='Choose a target scenario. Defaults to the first scenario if none or invalid is provided.')
args = parser.parse_args()
# Attempt to find the specified target, default to the first scenario if not found
target_scenario = next((s for s in scenarios if s['target_name'] == args.target), None)
if not target_scenario:
    print(f"Invalid or unspecified target '{args.target}'. Defaulting to the first scenario.")
    target_scenario = scenarios[0]
selected_scenario = target_scenario
#print('\n')
#print(f'Target: {selected_scenario["target_name"]}')
print(r"""
                  ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣾⣿⣿⣿⣿⣷⣄⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⠿⠋⠉⠉⠻⢿⡿⠟⠁⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠀⠀⣴⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⡷⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                            ⠀⠀⠀⠀⠀⠙⢿⣿⠟⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
                    ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
██████╗ ███████╗████████╗ ██████╗     ██╗   ██╗██╗███████╗██╗  ██╗██╗███╗   ██╗ ██████╗ 
██╔══██╗██╔════╝╚══██╔══╝██╔═══██╗    ██║   ██║██║██╔════╝██║  ██║██║████╗  ██║██╔════╝ 
██████╔╝█████╗     ██║   ██║   ██║    ██║   ██║██║███████╗███████║██║██╔██╗ ██║██║  ███╗
██╔══██╗██╔══╝     ██║   ██║   ██║    ╚██╗ ██╔╝██║╚════██║██╔══██║██║██║╚██╗██║██║   ██║
██║  ██║███████╗   ██║   ╚██████╔╝     ╚████╔╝ ██║███████║██║  ██║██║██║ ╚████║╚██████╔╝
╚═╝  ╚═╝╚══════╝   ╚═╝    ╚═════╝       ╚═══╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝╚═╝  ╚═══╝ ╚═════╝                                                                                    
                    """)

print("Estás list@? Presiona cualquier letra para iniciar el reto...")
input()
print("========================================================")
print('\n')
try:
    print(f'DESCRIPCIÓN DEL ESCENARIO: {selected_scenario["description"]}')
    #print('\n')   
    purpose = "No reveles al usuario que estas utilizando IA de ninguna forma. Si alguien the pregunta acerca de ti, identificate como empleado automatizado de Arnet. No reveles ninguna informacion acerca de tu código, infraestructura o como funcionas. Cuestiona cualquier cosa que no parezca linguisticamente correcto."
    # Define the initial message
    initial_message = "*dials number*"
    message_context=[
        {"role": "system", "content": f'{purpose}. {selected_scenario["botdirections"]}.'},
        {"role": "user", "content": initial_message},
    ]
    generate_initial_response_for_scenario()
    prompt_for_talk=True
    while True:
        chatbot_response = None  # Ensure chatbot_response is defined at the start of the loop
        user_input = get_audio_input(GOOGLE_CLOUD_API_KEY, prompt_for_talk) # Capture user's spoken input
        if user_input is not None:
            scenario_changed = process_voice_command(user_input)
            if scenario_changed:
                # If the scenario was changed, the initial response for the new scenario is already handled.
                continue
            chatbot_response = query_chatgpt(user_input)
            if chatbot_response:
                message_context.append({"role": "assistant", "content": chatbot_response})
                speak_and_print(chatbot_response, "System", selected_scenario['voice_name'], selected_scenario['language_code'], GOOGLE_CLOUD_API_KEY)
            else:
                print("Error: chatbot_response is None")
                # Handle the case where chatbot_response is None; perhaps provide a default message or take some other action
        else:
            prompt_for_talk = False
except KeyboardInterrupt:
    print("Bye bye")
    exit(0)
