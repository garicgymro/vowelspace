import os,re,ast,datetime#,webcolors
import numpy as np
import matplotlib.pyplot as plt
import pickle
import random
import pandas as pd


newroundline = re.compile(r'.*new round.*\n*')
senderline = re.compile(r'Sender\:.*\#(\d).*\n*')
breakline = re.compile(r'.*(BREAK).*\n*')
coordline = re.compile(r'.*(\[u\'sender coords\'.*\]).*\n*')
colorline = re.compile(r'.*(\[u\'color\'.*\]).*\n*')
targetline = re.compile(r'Target: referents\/(.*)\.png.*\n*')
fingeroffline = re.compile(r'.*sender finger off.*\n*')
guessline = re.compile(r'.*\[u\'guess\'\,\su\'(incorrect|correct)\'\,\su\'referents\/(.*)\.png\'].*\n*')
new_referents_line = re.compile(r'.*Adding referents.*\n*')

    

def correct_file(input_file):
    dateline = re.compile(r'.*\;\s(\d+\:\d+\:\d+)\:\s(.*)\n')
    current_time = datetime.datetime.strptime("08:00:00", "%H:%M:%S")
    inf = open(input_file,'r')
    outf = open("NEW"+input_file,'w')
    inf_lines = inf.readlines()
    for i in range(0,len(inf_lines)):
        line = inf_lines[i]
        if re.match(dateline,line):
            m = re.match(dateline,line)
            time = datetime.datetime.strptime(m.group(1), "%H:%M:%S")
            if time >= current_time or current_time == None:
                outf.write(line)
                current_time = time
                if "New round" in m.group(2):
                    if inf_lines[i+1][0] == "S" or inf_lines[i+1][0] == "T":
                        outf.write(inf_lines[i+1])
                    if inf_lines[i+2][0] == "S" or inf_lines[i+2][0] == "T":
                        outf.write(inf_lines[i+2])
                    


            
            
        
        
    

def parse_file(input_file,folder="."):
    #Not recording practice signals for some reason...
    print("parsing file...")
    practice_over = False
    practice_signals = {'0':{},'1':{}}
    signals = {'0':{},'1':{}}
    signal_counter = {'0':{},'1':{}}
    current_sender_movements = []
    current_sender_rgbs = []
    #current_sender_colors = []
    current_sender = None
    current_target = None
    dimensions = []
    if folder == "first_four":
        success_criterion = 1 #relaxed for first four referents
    else:
        success_criterion = 5
    f = open(input_file,"r")
    for line in f:
        m = re.match(senderline,line)
        if m != None:
            current_sender = m.group(1)
        m = re.match(breakline,line)
        if m != None:
            practice_over = True      
        m = re.match(coordline,line)
        if m != None:
            coordlist = ast.literal_eval(m.group(1))
            if type(coordlist[1]) is list:
                coords = coordlist[1]
            else:
                coords = coordlist[1:3]
            current_sender_movements.append(coords)
            if len(coordlist) == 4 and "dimensions" not in signals[current_sender]:
                dimensions = coordlist[3]
        m = re.match(colorline,line)
        if m != None:
            color = ast.literal_eval(m.group(1))[1:4]
            current_sender_rgbs.append(color)
            #current_sender_colors.append(get_color_name(tuple(color)))
        m = re.match(targetline,line)
        if m != None:
            current_target = m.group(1)
        m = re.match(fingeroffline,line)
        if m != None:
            current_sender_movements.append([None,None])
        m = re.match(guessline,line)
        if m != None:
            result = m.group(1)
            guess = m.group(2)
            if (result == "correct" and guess != current_target) or (result == "incorrect" and guess == "current_target"):
                print("guess/target mismatch!")
                print(line)
            elif result == "correct":                    
                if guess not in signal_counter[current_sender]:
                    signal_counter[current_sender][guess] = 1
                elif guess in signal_counter[current_sender] and signal_counter[current_sender][guess] < success_criterion-1:
                    signal_counter[current_sender][guess] += 1
                elif guess in signal_counter[current_sender] and signal_counter[current_sender][guess] >= success_criterion-1:
                    if practice_over == False:
                        practice_signals[current_sender][guess] = [current_sender_movements, current_sender_rgbs]#,current_sender_colors]
                    else:
                        signals[current_sender][guess] = [current_sender_movements, current_sender_rgbs]#,current_sender_colors]
                    
                    
                    
                current_sender_movements = []
                current_sender_rgbs = []
                #current_sender_colors = []
    return(practice_signals,signals,dimensions)
                    
                    




def parse_files(folder = "."):
    print("finding results files...")
    alldata = {}
    files = os.listdir(folder)
    for f in files:
        if f[-4:] == ".txt" and f[0] == "r":
            print(f)
            fdata = parse_file(os.path.join(folder,f),folder)
            alldata[f] = fdata
    datapath = os.path.join(folder,"most_recent_data")
    pickle.dump(alldata,open(datapath,"w"))
    return alldata



def find_mean_value(vec):
    xvec = []
    yvec = []
    for item in vec:
        if item[0] != None and item[1] != None:
            xvec.append(item[0])
            yvec.append(item[1])
    if len(xvec) > 0:
        return((np.mean(xvec),np.mean(yvec)))
    else:
        return(None)
        
    

def find_mean_values(data):
    print("finding mean values...")
    player_dic = {'0':[],'1':[]}
    if len(data[0]) > 2:
        dimensions = data[0][2]
    else:
        dimensions = [0,0]
    data = data[0][1] #ignore practice rounds
    for player in data:
        for referent in data[player]:
            vec = data[player][referent][0]
            player_dic[player].append(find_mean_value(vec))
    return(player_dic,dimensions)


def get_vectors(data):
    #This actually does very little,
    #but it's worth keeping a separate function for the sake of adapting it later.
    print("finding vectors...")
    player_dic = {'0':{},'1':{}}
    if len(data) > 2:
        dimensions = data[2]
    else:
        dimensions = [0,0]
    data = data[1] #data[0] is practice rounds
    #data = data[0][1] #[0] because we currently only care about the first data file, [1] to ignore practice rounds
    for player in data:
        for referent in data[player]:
            player_dic[player][referent] = data[player][referent][0] 
    return(player_dic,dimensions)
    


def parse_and_get_vectors(source,folder="."):
    if source == "pickle" and "most_recent_data" in os.listdir(folder):
        datapath = os.path.join(folder,"most_recent_data")
        data = pickle.load(open(datapath,"r"))
    elif source == "parse":
        data = parse_files()
    else:
        data = source
    vectors, dimensions = get_vectors(data)
    return(vectors,dimensions)



def parse_and_get_means(source,folder="."):
    if source == "pickle" and "most_recent_data" in os.listdir(folder):
        datapath = os.path.join(folder,"most_recent_data")
        data = pickle.load(open(datapath,"r"))
    elif source == "parse":
        data = parse_files()
    else:
        data = source
    means, dimensions = find_mean_values(data)
    return(means,dimensions)

def plot_means(player,source="pickle",folder="."):
    player = str(player)
    means, dimensions = parse_and_get_means(source)
    data = means[player]
    xs = []
    ys = []
    for item in data:
        if item != None:
            xs.append(item[0])
            ys.append(item[1]) 
    plt.plot(xs,ys,'ro')
    if dimensions == [0,0]:
        print("guessing dimensions!")
        plt.axis([0,960,0,540])
    else:
        plt.axis([0,dimensions[0],0,dimensions[1]])
    plt.legend()
    plt.show()
    
    
    
    
def plot_vectors(include_unshared = True,source="pickle",pair = None, plot_type="vectors",save_to_file=False,plot_folder = "vowelspace-plots",folder="."):
    print(plot_type)
    legend_space = 300
    #player = str(player)
    vectors, dimensions = parse_and_get_vectors(source)
    data = []
    data.append(vectors["0"])
    data.append(vectors["1"])
    colors = ["b","g","c","r","m","y","k"]
    shapes = ["^","+","o"]
    points = []
    for shape in shapes:
        for color in colors:
            points.append(color+shape)
    random.shuffle(points)
    point_counter = 0
    referent_dic = {}
    if include_unshared == True:
        referent_list = set(data[0].keys()).union(data[1].keys())
    else:
        referent_list = set(data[0].keys()).intersection(data[1].keys())

    
    
    for player in range(0,2):
        plt.figure(player)
        print(len(referent_list))
        for referent in referent_list:
            xs = []
            ys = []
            if referent in data[player]:
                for coords in data[player][referent]:
                    if coords == [None,None]:
                        xs.append(99999)
                        ys.append(99999)
                    else:
                        xs.append(coords[0])
                        ys.append(coords[1])
            if referent in referent_dic:
                marker = referent_dic[referent]
            else:
                marker = points[point_counter]
                referent_dic[referent] = marker
                point_counter += 1
            if xs == []:
                referent = "(" + referent + ")"
            if plot_type == "endpoints":
                xs = [x for x in xs if x != 99999]
                ys = [y for y in ys if y != 99999]
                if xs != []:
                    xs = [xs[0],xs[-1]]
                if ys != []:
                    ys = [ys[0],ys[-1]]
            plt.plot(xs,ys,marker,label = referent)
                
        if dimensions == [0,0]:
            print("guessing dimensions!")
            plt.axis([0,960+legend_space,0,540])
        else:
            plt.axis([0,dimensions[0]+legend_space,0,dimensions[1]])
        title = "Player " + str(player)
        if pair != None:
            title = pair +  "-" + title
        plt.title(title)    
        plt.legend()
    
    
    if save_to_file == True:
        thisdir = os.listdir(folder)
        if plot_folder not in thisdir:
            os.mkdir(plot_folder)
            os.mkdir(os.path.join(plot_folder,"vectors"))
            os.mkdir(os.path.join(plot_folder,"endpoints"))
        plot_filename = os.path.join(plot_folder,plot_type,title+".png")
        plt.savefig(plot_filename)
    plt.show()
    
    


#def plot(player):
#    xs = []
#    ys = []
#    player = str(player)
#    data = parse_files()[0][1]
#    for referent in data[player]:
#        print(referent)
#        vec = data[player][referent][0]
#        for item in vec:
#            if item[0] != None and item[1] != None:
#                xs.append(item[0])
#                ys.append(item[1])
#    plt.plot(xs,ys,'ro')
#    plt.axis([0,960,0,540])
#    plt.show()
    

def plot_all(include_unshared = True, source = "pickle", folder=".",plot_type="vectors",save_to_file = False,plot_folder = "vowelspace-plots"):
    if source == "pickle" and "most_recent_data" in os.listdir(folder):
        datapath = os.path.join(folder,"most_recent_data")
        data = pickle.load(open(datapath,'r'))
    elif source == "parse":
        data = parse_files(folder)
    else:
        data = source
    pairs = data.keys()
    for pair in pairs:
        print(pair)
        plot_vectors(include_unshared = True,source=data[pair], pair = pair, plot_type=plot_type,save_to_file=save_to_file,folder=folder)
        
    

        
        
def summarize_data(source="pickle",folder="."):
    if source == "pickle" and "most_recent_data" in os.listdir(folder):
        dataplath = os.path.join(folder,"most_recent_data")
        data = pickle.load(open(dataplath,"r"))
    elif source == "parse":
        data = parse_files()
    else:
        data = source
    pairs = data.keys()
    datadic = {"p0.refs":[],"p1.refs":[],"mean.refs":[],
        "p0.mean.coordlengths":[],"p1.mean.coordlengths":[],"mean.coordlengths":[],
            "p0.mean.xrange":[],"p0.mean.yrange":[],
                "p1.mean.xrange":[],"p1.mean.yrange":[],
                    "mean.xrange":[],"mean.yrange":[],
                        "mean.range":[]}
    
    dataindex = []
    for pair in pairs:
        dataindex.append(pair)
        pairdata = data[pair][1]
        
        reflength = []
        coordlengths = [[],[]]
        xranges = [[],[]]
        yranges = [[],[]]
        for player in range(0,2):
            reflength.append(len(pairdata[str(player)].keys()))
            for referent in pairdata[str(player)]:
                coordlengths[player].append(len(pairdata[str(player)][referent][0]))
                refx = [x[0] for x in pairdata[str(player)][referent][0] if x[0] is not None]
                refy = [x[1] for x in pairdata[str(player)][referent][0] if x[1] is not None]
                try:
                    xranges[player].append(np.max(refx)-np.min(refx))
                except:
                    xranges[player].append(np.nan)
                try:
                    yranges[player].append(np.max(refy)-np.min(refy))
                except:
                    yranges[player].append(np.nan)

                
            
            

        datadic["p0.refs"].append(reflength[0])
        datadic["p1.refs"].append(reflength[1])
        datadic["mean.refs"].append(np.mean(reflength))
        datadic["p0.mean.coordlengths"].append(np.mean(coordlengths[0]))
        datadic["p1.mean.coordlengths"].append(np.mean(coordlengths[1]))
        datadic["mean.coordlengths"].append(np.mean([np.mean(coordlengths[0]),np.mean(coordlengths[1])]))
        
        datadic["p0.mean.xrange"].append(np.mean(xranges[0]))
        datadic["p0.mean.yrange"].append(np.mean(yranges[0]))
        datadic["p1.mean.xrange"].append(np.mean(xranges[1]))
        datadic["p1.mean.yrange"].append(np.mean(yranges[1]))
        datadic["mean.xrange"].append(np.mean([np.mean(xranges[0]),np.mean(xranges[1])]))
        datadic["mean.yrange"].append(np.mean([np.mean(yranges[0]),np.mean(yranges[1])]))
        datadic["mean.range"].append(np.mean([np.mean(yranges[0]),np.mean(yranges[1]),np.mean(xranges[0]),np.mean(xranges[1])]))
        
    #print(dataindex)
    df = pd.DataFrame(datadic,index=dataindex)
    return df


def first_four(thisfolder = ".", newfolder = "first_four"):
    files = os.listdir(thisfolder)
    if not newfolder in files:
        os.mkdir(newfolder)
    for f in files:
        if f[-4:] == ".txt" and f[0] == "r":
            oldpath = os.path.join(thisfolder,f)
            op = open(oldpath,"r")
            newfile = f[:-4] + "FIRSTFOUR.txt"
            newpath = os.path.join(newfolder,newfile)
            np = open(newpath,"w")
            print(f)
            for line in op:
                if re.match(new_referents_line,line):
                    np.close()
                    break
                else:
                    np.write(line)
    

    

        

    

    
    
            
    
    
    
    
    
    
    
    


    
#def closest_color(requested_color):
#    min_colors = {}
#    for key, name in webcolors.css3_hex_to_names.items():
#        r_c, g_c, b_c = webcolors.hex_to_rgb(key)
#        rd = (r_c - requested_color[0]) ** 2
#        gd = (g_c - requested_color[1]) ** 2
#        bd = (b_c - requested_color[2]) ** 2
#        min_colors[(rd + gd + bd)] = name
#    return min_colors[min(min_colors.keys())]
#
#def get_color_name(requested_color):
#    try:
#        closest_name = actual_name = webcolors.rgb_to_name(requested_color)
#    except ValueError:
#        closest_name = closest_color(requested_color)
#        actual_name = None
#    return actual_name, closest_name
            
        
    