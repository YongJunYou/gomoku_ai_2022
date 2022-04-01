from ursina import * # 게임엔진 import
import numpy as np
from tensorflow.keras.models import load_model

model = load_model('models/best_model.h5')
app = Ursina()

#기본 설정
camera.orthographic = True
camera.fov = 1280
camera.position = (0, 0)
Text.default_resolution *= 2
mouse.visible = True

#플레이어 설정
player = Entity(name='1', color=color.black) #플레이어가 흑(1)->백(2)->흑(1)-> 으로 바뀌면서 플레이됨.

#배경 Entity 만들기
bg = Entity(parent=scene, model='quad', texture="img.jpg", scale=(1900,1280), z=10, color=color.light_gray)

#가로세로 길이
w=15
h=15

#오목판 정의
board = [[None for x in range(w)] for y in range(h)]    #보여지는 오목판 UI
pan = [[ 0 for x in range(w)] for y in range(h)]        #보여지지 않는 오목판
per = [[None for x in range(w)] for y in range(h)] 

#오목판 가로 세로 인덱스

eng = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O']

############### UI 관련 함수 #######################

def create_UI():
    global player, board
    for y in range(h):
        for x in range(w):
            b = Button(parent=scene,text='0', radius=0.5, position=(70*(y-7),-70*(x-7)), scale=(70,70), color=Color(0, 0, 0, 0))
            board[x][y] = b

            def button_click(b=b,x=x,y=y):
                global player, board
                global x_on ,y_on
                x_on = x
                y_on = y
                player.name = '1' # 흑 차례
                b.text = '1'
                b.color = color.black
                b.collision = False
                pan[x][y] = 1
                print('인간:',str(15-x_on),'-',str(eng[y_on]))
                read_board_and_debug_on_terminal()


                check_for_six_black()
                if not connect_six:
                    check_for_victory_black()
                check_for_three_three_black(x_on,y_on)
                check_for_four_four_black(x_on,y_on)
                

                if black_won==False and connect_six==False and three_three==False and four_four==False:
                    read_board_and_put_by_cpu()
                check_for_victory_white()
                
            b.on_click = button_click

def create_win_UI():
    name = player.name
    global p,b_exit,b_replay,t
    p = Panel(z=1, scale=10, model='quad')
    b_exit = Button(text='exit', color=color.azure, scale=(0.05,0.03), text_origin=(0,0),position=(-0.05,-0.1))
    b_exit.on_click = application.quit # 종료
    b_exit.tooltip = Tooltip('exit')
    b_replay = Button(text='replay', color=color.azure, scale=(0.08,0.03), text_origin=(0,0),position=(0.05,-0.1))
    b_replay.on_click = delete_and_create_all_UI # 재시작
    b_replay.tooltip = Tooltip('replay')
    t = Text(f'Player{name}\n  won!', scale=3, origin=(0,0), background=True)
    t.create_background(padding=(.5,.25), radius=Text.size/2)
    t.background.color = player.color.tint(-.2)
    print('winner is:', name)

def create_ban_UI():
    global p1, b_0, t1
    p1 = Panel(z=1, scale=10, model='quad')
    b_0 = Button(color=Color(0,0,0,0), scale=(200,600),position=(-0.05,-0.1))
    b_0.on_click = delete_and_create_board_UI
    b_0.tooltip = Tooltip('resume')
    t1 = Text(f'Play is banned', scale=3, origin=(0,0), background=True)
    t1.create_background(padding=(.5,.25), radius=Text.size/2)
    t1.background.color = player.color.tint(-.2)

############### UI 수정 관련 함수 #######################

def delete_and_create_all_UI():
    global player, board, pan
    #밀기
    for y in range(h):
        for x in range(w):
            destroy(board[y][x])
    destroy(t)
    destroy(p)
    destroy(b_exit)
    destroy(b_replay)
    #재정의
    player = Entity(name='1', color=color.black) 
    board = [[None for x in range(w)] for y in range(h)]
    pan = [[ 0 for x in range(w)] for y in range(h)]
    create_UI()

def delete_and_create_board_UI():
    global board
    global pan
    pan[x_on][y_on] = 0
    destroy(board[x_on][y_on])
    b = Button(parent=scene, radius=0.5, position=(70*(y_on-7),-70*(x_on-7)), scale=(70,70), color=Color(0, 0, 0, 0))
    board[x_on][y_on] = b

    def button_click(b=b,x=x_on,y=y_on):
        global player
        global x_on ,y_on
        x_on = x
        y_on = y
        player.name = '1' # 흑 차례
        b.text = '1'
        b.color = color.black
        b.collision = False
        pan[x][y] = 1
        #print('인간:',str(15-x_on),'-',str(eng[y_on]))
        #read_board_and_debug_on_terminal()


        check_for_six_black()
        if not connect_six:
            check_for_victory_black()
        check_for_three_three_black(x_on,y_on)
        check_for_four_four_black(x_on,y_on)
        

        if black_won==False and connect_six==False and three_three==False and four_four==False:
            read_board_and_put_by_cpu()
        check_for_victory_white()

    b.on_click = button_click

    
    global player
    player.name = '1'
    player.color = color.black
    destroy(t1)
    destroy(p1)
    destroy(b_0)

############### 터미널에 현재 상태 출력해주는 함수 #######################

def read_board_and_debug_on_terminal():
    for i in pan:
        print(i)
    print('\n')

############### 인공지능이 오목을 두는 함수 #######################

def read_board_and_put_by_cpu():
    global per
    input = pan.copy()
    input = np.array(input)
    input[(input != 1) & (input != 0)] = -1
    input[(input == 1) & (input != 0)] = 1
    input = np.expand_dims(input, axis=(0, -1)).astype(np.float32)

    output = model.predict(input).squeeze()
    output = output.reshape((w, h))
    output_x, output_y = np.unravel_index(np.argmax(output), output.shape)

    percent = output
    percent = percent.tolist()
    for i in percent:
        for j in i:
            print("{:.10f}".format(j),end=' ')
        print('\n')

    for y in range(h):
        for x in range(w):
            destroy(per[y][x])

    per = [[None for x in range(w)] for y in range(h)]
    for y in range(h):
        for x in range(w):
            p = Button(parent=scene,text='0', radius=0, position=(70*(y-7),-70*(x-7)), scale=(8,8), color=Color(1, 0, 0, percent[x][y]))
            per[x][y] = p

    pan[output_x][output_y] = 2
    board[output_x][output_y].text = '2'
    board[output_x][output_y].color = Color(1,1,1,0.5)
    board[output_x][output_y].collision = False

    #print('AI:',str(15-output_x),'-',str(eng[output_y]))
    # read_board_and_debug_on_terminal()

############### 오목의 승리에 관한 함수들 #######################

def check_for_victory_white():
    global player
    player.name = '2'
    name='2'
    won=False

    for y in range(h):
        for x in range(w):
            try:
                if board[y][x].text == name and board[y+1][x].text == name and board[y+2][x].text == name and board[y+3][x].text == name and board[y+4][x].text == name:
                    name = player.name
                    won = True
                    break
            except:
                pass

            try:
                if board[y][x].text == name and board[y][x+1].text == name and board[y][x+2].text == name and board[y][x+3].text == name and board[y][x+4].text == name:
                    name = player.name
                    won = True
                    break
            except:
                pass

            try:
                if board[y][x].text == name and board[y+1][x+1].text == name and board[y+2][x+2].text == name and board[y+3][x+3].text == name and board[y+4][x+4].text == name:
                    name = player.name
                    won = True
                    break
            except:
                pass

            try:
                if x >= 4 and board[y][x].text == name and board[y+1][x-1].text == name and board[y+2][x-2].text == name and board[y+3][x-3].text == name and board[y+4][x-4].text == name:
                    name = player.name
                    won = True
                    break

            except:
                pass

        if won == True:
            break
        
    if won:
        create_win_UI()

def check_for_victory_black():
    name = '1'
    global black_won 
    black_won = False


    for y in range(h):
        for x in range(w):
            try:
                if board[y][x].text == name and board[y+1][x].text == name and board[y+2][x].text == name and board[y+3][x].text == name and board[y+4][x].text == name:
                    name = player.name
                    black_won = True
                    break
            except:
                pass

            try:
                if board[y][x].text == name and board[y][x+1].text == name and board[y][x+2].text == name and board[y][x+3].text == name and board[y][x+4].text == name:
                    name = player.name
                    black_won = True
                    break
            except:
                pass

            try:
                if board[y][x].text == name and board[y+1][x+1].text == name and board[y+2][x+2].text == name and board[y+3][x+3].text == name and board[y+4][x+4].text == name:
                    name = player.name
                    black_won = True
                    break
            except:
                pass

            try:
                if x >= 4 and board[y][x].text == name and board[y+1][x-1].text == name and board[y+2][x-2].text == name and board[y+3][x-3].text == name and board[y+4][x-4].text == name:
                    name = player.name
                    black_won = True
                    break

            except:
                pass

        if black_won == True:
            break
        
    if black_won:
        create_win_UI()

############### 오목의 금수에 관한 함수들 #######################

def check_for_three_three_black(x_on,y_on):
    global three_three
    three_three=False
    open_three = 0
    x=x_on
    y=y_on
    direction_vector = [[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]
    direction_vector_half = [[0,1],[1,1],[1,0],[1,-1]]
    
    for i,j in direction_vector:
        try:
            # 열린3 N*@@N -> ^N*@@N^ 
            if pan[x-2*i][y-2*j]!=1 and pan[x-1*i][y-1*j]==0 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==0 and pan[x+4*i][y+4*j]!=1  :
                open_three += 1
            # 열린3 N@*N@N
            if pan[x-2*i][y-2*j]==0 and pan[x-1*i][y-1*j]==1 and pan[x][y]==1 and pan[x+1*i][y+1*j]==0 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==0 :
                open_three += 1
            # 열린3 N*N@@N 
            if pan[x-1*i][y-1*j]==0 and pan[x][y]==1 and pan[x+1*i][y+1*j]==0 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==1 and pan[x+4*i][y+4*j]==0 :
                open_three += 1
            # 열린3 N*@N@N
            if pan[x-1*i][y-1*j]==0 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==0 and pan[x+3*i][y+3*j]==1 and pan[x+4*i][y+4*j]==0 :
                open_three += 1
        except:
            pass

    for i,j in direction_vector_half:    
        try:   
            # 열린3 N@*@N
            if pan[x-3*i][y-3*j]!=1 and pan[x-2*i][y-2*j]==0 and pan[x-1*i][y-1*j]==1 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==0 and pan[x+3*i][y+3*j]!=1:
                open_three += 1
        except:
            pass

    if open_three >= 2:
        three_three = True
        create_ban_UI()

def check_for_four_four_black(x_on,y_on):
    global four_four
    four_four=False
    four = 0
    x=x_on
    y=y_on

    direction_vector = [[0,1],[1,1],[1,0],[1,-1],[0,-1],[-1,-1],[-1,0],[-1,1]]

    for i,j in direction_vector:
        try:
            # 열린4 N*@@@N / 닫힌4 N*@@@O O*@@@N
            if pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==1 :
                if pan[x-1*i][y-1*j]==0 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==2 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==0 and pan[x+4*i][y+4*j]==2:
                    four += 1    
            #0[1]01110
            if pan[x][y]==1 and pan[x+1*i][y+1*j]==0 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==1 and pan[x+4*i][y+4*j]==1 :
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==2 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==2:
                    four += 1    
            #0[1]10110
            if pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==0 and pan[x+3*i][y+3*j]==1 and pan[x+4*i][y+4*j]==1 :
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==2 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==2:
                    four += 1    
            #0[1]11010
            if pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==0 and pan[x+4*i][y+4*j]==1 :
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==2 and pan[x+5*i][y+5*j]==0:
                    four += 1
                if pan[x-1*i][y-1*j]==0 and pan[x+5*i][y+5*j]==2:
                    four += 1    
            #01[1]110
            if pan[x-1*i][y-1*j]==1 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==1 :
                if pan[x-2*i][y-2*j]==0 and pan[x+3*i][y+3*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==2 and pan[x+3*i][y+3*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==0 and pan[x+3*i][y+3*j]==2:
                    four += 1    
            #01[1]0110
            if pan[x-1*i][y-1*j]==1 and pan[x][y]==1 and pan[x+1*i][y+1*j]==0 and pan[x+2*i][y+2*j]==1 and pan[x+3*i][y+3*j]==1 :
                if pan[x-2*i][y-2*j]==0 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==2 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==0 and pan[x+4*i][y+4*j]==2:
                    four += 1    
            #01[1]1010
            if pan[x-1*i][y-1*j]==1 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==0 and pan[x+3*i][y+3*j]==1 :
                if pan[x-2*i][y-2*j]==0 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==2 and pan[x+4*i][y+4*j]==0:
                    four += 1
                if pan[x-2*i][y-2*j]==0 and pan[x+4*i][y+4*j]==2:
                    four += 1    
            #010[1]110
            if pan[x-2*i][y-2*j]==1 and pan[x-1*i][y-1*j]==0 and pan[x][y]==1 and pan[x+1*i][y+1*j]==1 and pan[x+2*i][y+2*j]==1 :
                if pan[x-3*i][y-3*j]==0 and pan[x+3*i][y+3*j]==0:
                    four += 1
                if pan[x-3*i][y-3*j]==2 and pan[x+3*i][y+3*j]==0:
                    four += 1
                if pan[x-3*i][y-3*j]==0 and pan[x+3*i][y+3*j]==2:
                    four += 1    
        except:
            pass

    if four >= 2:
        four_four = True
        create_ban_UI()

def check_for_six_black():
    global connect_six
    connect_six = False

    for y in range(h):
        for x in range(w):
            try:
                if board[y][x].text == board[y+1][x].text == board[y+2][x].text == board[y+3][x].text == board[y+4][x].text == board[y+5][x].text == '1':
                    connect_six = True
                    break
            except:
                pass

            try:
                if board[y][x].text == board[y][x+1].text == board[y][x+2].text == board[y][x+3].text == board[y][x+4].text == board[y][x+5].text == '1':
                    connect_six = True
                    break
            except:
                pass

            try:
                if board[y][x].text == board[y+1][x+1].text == board[y+2][x+2].text == board[y+3][x+3].text == board[y+4][x+4].text == board[y+5][x+5].text == '1':
                    connect_six = True
                    break
            except:
                pass

            try:
                if x>=5 and board[y][x].text == board[y+1][x-1].text == board[y+2][x-2].text == board[y+3][x-3].text == board[y+4][x-4].text == board[y+5][x-5].text == '1':
                    connect_six = True
                    break
            except:
                pass
        if connect_six == True:
            break
        
    if connect_six:
        create_ban_UI()   


if __name__ == '__main__':
    create_UI()
    app.run()