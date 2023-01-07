import os
import json
import random
#import pyperclip
import math
import numpy
from thefuzz import fuzz

#Unused feature as of now
from PIL import Image

mode_lookup = {
    "and": 0,
    "or": 1,
    "xor": 2,
    "nand": 3,
    "nor": 4,
    "xnor": 5
}
def logic_id(gate):
    try:
        return mode_lookup[gate.lower()]
    except:
        return 405, "Cannot find this mode"
#Unused feature as of now
def get_path():
    return [x[0] for x in os.walk(os.getenv('APPDATA')+"\\Axolot Games\\Scrap Mechanic\\User")][1]

#Unused feature as of now
def blueprint_search(search_term):
    blueprints = [x[0] for x in os.walk(get_path()+"\\Blueprints")]
    highest_ratio = [0,0,0]
    for i in range(len(blueprints)):
        if i==0:
            continue
        with open(blueprints[i]+"\\description.json") as f:
            data = json.load(f)
        check = fuzz.token_sort_ratio(data['name'],search_term)
        if check > highest_ratio[0]:
            highest_ratio[0] = check
            highest_ratio[1] = data['name']
            highest_ratio[2] = blueprints[i]

    return highest_ratio


def ctrl_exec(code,x=False):
    if x:
        code = code.replace("x", str(x))
    exec('global i; i = %s' % code)
    global i
    return i

def calc_outputs(code=None,min_x=None,max_x=None):
    try:
        print(ctrl_exec(code,10))
    except:
        return 400, "Could not compile the code"
    else:
        #Generates all the outputs it should have.
        global outputs
        outputs = {str(x):str(ctrl_exec(code,x)) for x in range(int(min_x),int(max_x)+1)}
        return outputs

def generate_binary_output_length():
    global longest_binary
    longest_binary = 0
    for i in outputs:
        if int(outputs[i]) >= longest_binary:
            longest_binary = int(outputs[i])
    return longest_binary


class blueprint():
    def __init__(self):
        self.finished_blueprint = {}
        self.ids = []
    def construct(self):
        with open("data.json") as f:
            data = json.load(f)
        template = data['template']['blueprint_file']
        self.finished_blueprint = template

    def place(self,x,y,z,mode,color):
        if type(mode) == str:
            mode = logic_id(mode)
        if self.finished_blueprint == {}:
            return 400, "Blueprint not constructed! Use blueprint.construct() to construct it"
        with open("data.json") as f:
            data = json.load(f)
        found_id = False
        while not found_id:
            rand_id = random.randint(0,30000)
            if not rand_id in self.ids:
                found_id=True
                self.ids.append(rand_id)
        logic_template = data['template']['logic_gate']

        logic_template['color'] = color
        logic_template['pos']['x'] = x
        logic_template['pos']['y'] = y
        logic_template['pos']['z'] = z
        logic_template['controller']['id'] = rand_id
        logic_template['controller']['mode'] = mode

        try:
            self.finished_blueprint['bodies'][0]['childs'].append(logic_template)
        except:
            return 405, "Method not allowed self.finished_blueprint['bodies'][0]['childs'] += logic_template"
        else:
            return rand_id
    def connect(self,id1,id2):
        if self.finished_blueprint == {}:
            return 400, "Blueprint not constructed! Use blueprint().construct() to construct it"
        for i in range(len(self.finished_blueprint['bodies'][0]['childs'])):
            if self.finished_blueprint['bodies'][0]['childs'][i]['controller']['id'] == id1:
                if not self.finished_blueprint['bodies'][0]['childs'][i]['controller']['controllers']:
                    self.finished_blueprint['bodies'][0]['childs'][i]['controller']['controllers']=[{"id":id2}]
                else:
                    self.finished_blueprint['bodies'][0]['childs'][i]['controller']['controllers'].append({"id":id2})
            else:
                #return 400, f"Connecting could not be achieved from {id1} to {id2}"
                pass

def generate_binary_input(blueprintf,min_x,max_x):
    if blueprintf.finished_blueprint == {}:
        return 404, "Could not find the blueprint"
    offset_x = -3
    offset_y = -2
    global binary_bit_lookup
    global binary_bit_lookup_inverse
    binary_bit_lookup_inverse = []
    binary_bit_lookup = []
    for i in range(min_x.bit_length(),max_x.bit_length()):
        id1 = blueprintf.place(offset_x,offset_y,1,"or","#FF0000")
        id2 = blueprintf.place(offset_x,offset_y+1,1,"nor","#0000FF")
        blueprintf.connect(id1,id2)
        binary_bit_lookup.append(id1)
        binary_bit_lookup_inverse.append(id2)
        offset_x+=1

    return blueprintf,binary_bit_lookup
def generate_binary_output(blueprintf):
    if blueprintf.finished_blueprint == {}:
        return 404, "Could not find the blueprint"
    offset_x = -3
    offset_y = -2
    global binary_bit_lookup2
    binary_bit_lookup2 = []
    for i in range(longest_binary.bit_length()):
        id1 = blueprintf.place(offset_x,offset_y,2,"or","#FFFF00")
        binary_bit_lookup2.append(id1)
        offset_x+=1

    return blueprintf,binary_bit_lookup2
def gen_rom(blueprintf,max_x):
    #Calculate biggest output
    max_x = int(max_x)



    #Iterate the outputs, so you can place one logic block per ROM value.
    for i,_ in outputs.items():
        #The block_id for the block placing is being returned when decalring it as a variable.
        block_id = blueprintf.place(-3,-1,2,"and","#000000")
        str_bin = str(bin(int(outputs[i])))[2:]
        str_bin = '0'*(longest_binary.bit_length()-len(str(bin(int(outputs[i])))[2:]))+str(bin(int(outputs[i])))[2:]
        #Iterating over the outputs so you can get the correct outputs.
        for j in range(longest_binary.bit_length()):
            j = (j+1)*-1 #Convert J to index backwards to read first bit.
            if str_bin[j] == "1":
                blueprintf.connect(block_id,binary_bit_lookup2[j])
                #DEBUG print(f"Connected {block_id} to {binary_bit_lookup2[j]} where bit was {str_bin[j]}")

        #Iterate over inputs.
        str_bin_in = '0'*(longest_binary.bit_length()-len(str(bin(int(i)))[2:]))+str(bin(int(i)))[2:]
        for k in range(max_x.bit_length()):
            k = k*-1
            if str_bin_in[k] == "1":
                blueprintf.connect(binary_bit_lookup[k],block_id)
            if str_bin_in[k] == "0":
                blueprintf.connect(binary_bit_lookup_inverse[k],block_id)

            
        
                
    return blueprintf







import argparse
import colorama
import uuid
import names

from colorama import Fore, Back, Style, init
init()


parser = argparse.ArgumentParser(description="To generate a ROM for a Python math equation")
parser.add_argument("--input",required=False)
parser.add_argument("--min_x",required=False)
parser.add_argument("--max_x",required=False)
parser.add_argument("--setup",required=False)

clear = lambda: os.system('cls')
args = parser.parse_args()
#print(args.input, args.min_x, args.max_x)

ascii_art = Fore.CYAN + """
  _                 _       _____ ______ _   _ 
 | |               (_)     / ____|  ____| \ | |
 | |     ___   __ _ _  ___| |  __| |__  |  \| |
 | |    / _ \ / _` | |/ __| | |_ |  __| | . ` |
 | |___| (_) | (_| | | (__| |__| | |____| |\  |
 |______\___/ \__, |_|\___|\_____|______|_| \_|
               __/ |                           
              |___/       
""" + Fore.YELLOW + "\n          Made by byggmesterPRO       \n\n" + Style.RESET_ALL

class dataJson:
	def __init__(self):
		with open("data.json") as f:
			self.data = json.load(f)
	def read(self):
		return self.data
	def write(self, new_data):
		with open("data.json", "w") as f:
			self.data = json.dump(new_data, f)
		return self.data

def screen_refresh(message="\n"):
	clear()
	print(ascii_art)
	print(message)


def setup_gen():
	pass
def main():
	data = dataJson().read()
	quit_loop = False
	setup_loop = True
	gen_loop = True
	if args.setup and not args.input and not args.min_x and not args.max_x:
		setup_loop = False
	elif args.input and args.min_x and args.max_x and not args.setup:
		gen_loop = False
	else:
		print("Too many or lack of inputs!\n")
		print("Quitting...")
		quit_loop = True
	while not quit_loop:
		def ask():
			user_response = input(">>> ")
			if user_response.lower() == "quit" or "cancel":
				screen_refresh("Successfully canceled")
				setup_loop = True

			if user_response.lower() == "exit":
				quit_loop = True

			return user_response
		while not setup_loop:
			if args.setup:
				print(f"\nYou are now about to edit the settings\nIf you want to cancel this setup at any time write '{Fore.GREEN}cancel{Style.RESET_ALL}'")
				creation_overwrite = ask("\nDo you want to overwrite a creation? Other option is to create a new one. y\n?").lower()
				if creation_overwrite == "y" or "yes":
					data['settings']['creation_overwrite'] == True
					#data = dataJson.write(data)
					print("\nSettings saved, will now overwrite a creation!")
					print("This is not yet DONE! So nothing really happened lmao sorry.")
				elif creation_overwrite == "n" or "no" or "":
					data['settings']['creation_overwrite'] == False
					data = dataJson().write()
					print("\nSettings saved, will now create a new creation with a random UUID name.")
				print("\nTo be honest settings aren't really done, so you gotta accept that ")
		while not gen_loop:
			try:
				int(args.min_x)
				int(args.max_x)
			except:
				quit_loop = True
				gen_loop = True
				print("Seems like some of your inputs were wrong! Remember that min_x and max_x has to be numbers!\n")
				print("Quitting...")
				break
			print(f"Generating blueprint using the following input/math equation {Fore.LIGHTGREEN_EX}{args.input}{Style.RESET_ALL} and min_x {Fore.LIGHTGREEN_EX}{args.min_x}{Style.RESET_ALL} and max_x {Fore.LIGHTGREEN_EX}{args.max_x}{Style.RESET_ALL}")
			inp = args.input
			max_x = int(args.max_x)
			min_x = int(args.min_x)
			print("Retrieving appdata blueprint folder...\n")
			try:
				appdata_path = get_path()
			except:
				print("Path not found, contact byggmesterPRO#8206")
				quit_loop = True
				gen_loop = True
				break
			print("Path found! Here:"  + appdata_path)
			outputs = calc_outputs(code=inp,min_x=min_x,max_x=max_x)
			generate_binary_output_length()
			if len(outputs) > 255:
				quit_loop = True
				gen_loop = True
				print("Too many outputs, can't generate blueprint!\nQuitting...")
				break
			creation = blueprint()
			creation.construct()
			bin_in = generate_binary_input(creation,min_x,max_x)
			bin_out = generate_binary_output(bin_in[0])
			creationf = gen_rom(bin_out[0],max_x)
			rand_uuid= str(uuid.uuid4())
			rand_name = names.get_first_name()
			path = os.path.join(appdata_path+"\\Blueprints", rand_uuid)
			os.mkdir(path)
			with open(path+"\\blueprint.json", "w") as f:
				json.dump(creationf.finished_blueprint,f, indent=2)

			description = {
				"description" : str(outputs),
				"localId" : rand_uuid,
				"name" : rand_name,
				"type" : "Blueprint",
				"version" : 0
						}

			with open(path+"\\description.json", "w") as f:
				json.dump(description,f, indent=2)
			print(f"Blueprint has been generated with the name {Fore.LIGHTGREEN_EX}{rand_name}{Style.RESET_ALL}")
			print("Restart your game to see the blueprint!")
			quit_loop = True
			gen_loop = True
			break
				









			

			

if __name__ == "__main__":
    screen_refresh()
    main()
    #print(blueprint_search("Control RAM"))
    """
    parser = argparse.ArgumentParser(description="Test generator")
    parser.add_argument("--test",required=False)
    args = parser.parse_args()

    if args.test:

        #print(calc_outputs(code="round(32768/round(x+128))-128",min_x="1",max_x=127))
        #print(longest_binary, "Binary Output")
        creation = blueprint()
        creation.construct()
        #print(creation.finished_blueprint)
        bin_in = generate_binary_input(creation,127)
        bin_out = generate_binary_output(bin_in[0])
        #print(binary_bit_lookup)
        #print(binary_bit_lookup2)
        creationf = gen_rom(bin_out[0],"127")
        creationf = json.dumps(creationf.finished_blueprint,indent=2)
        #print(creationf)
        #pyperclip.copy(creationf)
    """