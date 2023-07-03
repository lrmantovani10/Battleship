import pygame as pg
import pandas as pd
import numpy as np
import math, random, csv, pathlib, os
import pymsgbox as ms
from datetime import datetime
from screeninfo import get_monitors

# Path to Output file
player_path = 'Player_Data//'

# Create folder with player data
current_dir = str(pathlib.Path(__file__).parent.resolve())
if not os.path.exists(player_path):
    os.mkdir(current_dir + "//" + player_path)

# Folders containing data corresponding to previous players 
player_folders = os.listdir(player_path)

# Automatically generate player_id based on the folder names contained in
# Player_Data:
if len(player_folders) == 0:
    player_id = 1
else:
    player_id = [int(f) for f in player_folders]
    player_id.sort()
    player_id = player_id[-1] + 1

player_dir = current_dir + "//" + player_path + "{}".format(
    str(player_id))

if not os.path.exists(player_dir):
    os.mkdir(player_dir)

# Get monitor data
monitor = get_monitors()[0]

# Screen width
screen_width = monitor.width * 0.95

# Screen height
screen_height = monitor.height * 0.95

# Setting screen height to be proportional to screen width
if (screen_height < ((2.052/3.648) * screen_width)):
    screen_height = (2.052/3.648) * screen_width

# Pixels per meter
ppm = 0.52

# height of the end button
end_button_height = (screen_width / 20) * ppm

# size of the title text
title_size = end_button_height * 2

# Game initialization
pg.init()
window = pg.display.set_mode((screen_width, screen_height))
pg.display.set_caption("Battleship Game")
game_icon = pg.image.load('Images/icon.png')
pg.display.set_icon(game_icon)
background_color = 'black'
opposite_color = 'white'

# Number of rows and columns
nrows = 5
ncols = 5

# Color of each square by default and when hovered over
sq_col = (103, 77, 255)
faded_col = (159, 142, 255)

# Time taken for each tile to flip
tile_timer = 1200

# Horizontal offset
horizontal_offset = (0.575658 * screen_width) * ppm

# Square side length and spacing
screen_choice = screen_width
sq_len = ((screen_width - (2 * horizontal_offset))/ncols)/1.15
interdistance = (screen_width - (ncols * sq_len) - (2 * horizontal_offset))/(ncols - 1)
vertical_offset = (screen_height - (ncols * sq_len) - ((nrows - 1) * interdistance) - end_button_height + title_size) / 2

# List of squares generated
square_list = list()

# What happens while the game is running
run = True
score = 0
hits = 0
choices = 0
rounds = 1

# Default color of the end game button
end_button_color = 'white'
default_btn_col = (192,192,192)

# Default timer for buttons to be pressed
exit_timer = 2 * tile_timer
button_timer = datetime.now()

# Variable that checks whether fixating or not and
# timer for fixation period
fixation_period = 1200
fixation_timer = datetime.now()
fixation_interval = False
interval_start = True
shape_start = None

# Current state of the game
state = "intro"
previous = False

# Boolean to trigger functions that should only be run when user can
# start selecting squares
select_sq_start = True

# Time during which each user alert lasts, in miliseconds
msg_time = 10000000000

# Initial alert message and title
alert_title = "Hi! Welcome to the Battleship game!"
alert_message = """ [This message will close after 20 seconds]
The goal of this game is to identify the shapes
with the fewest number of searches. You are free to select a target by hovering over the
target in the desired square.
Once you have found a shape, the game will start over. Good luck!"""

# Check whether user is selectinge exit button or not
exiting = False

# Whether all correct tiles have been revealed
all_revealed = False

# Dataframe with game-by-game data for player
initial_df = pd.DataFrame(columns = ["Round","Choice", "Position_(Column,Row)", "Hit",
"Start_Time", "End_Time"])
player_attempts = initial_df

# Show mouse 
pg.mouse.set_visible(True)

# Write data to file
def write_data(player_data):
    global player_general, previous, player_attempts
    with open(player_general, 'a', newline = '') as output_file:
        writer = csv.DictWriter(output_file,
        fieldnames = player_data[0].keys())
        if not previous:
            writer.writeheader()
        writer.writerows(player_data)
        output_file.close()

    if not previous:
        player_attempts.to_csv(player_choices, mode = 'w', index = False)
    else:
        player_attempts.to_csv(player_choices, mode = 'a',
        index = False, header = False)

# Select one shape to be used in the game among the possibilities given
def generate_shape():

    # List of possible shape combinations (0-based indexing system).
    #  First value is x, second is y position of tile
    shape_list = [
    [[3,0], [3, 1], [4, 1], [4, 2]],
    [[2, 2], [3, 2], [4, 2], [2, 3], [2, 4], [3, 4], [4, 4]],
    [[1, 3], [1, 4], [2, 3], [3, 3]],
    [[0, 1], [0, 2], [1, 2], [1, 3]],
    [[0, 0], [0, 1], [1, 0], [1, 1]]
    ]

    # Color of shapes
    shape_colors = ['Red', 'Green', 'Purple', 'Seagreen', 'Blue', 'Orange',
    'Palevioletred', 'Gold', 'Blueviolet', 'Darkgoldenrod1', 'Lightsalmon']

    # Randomly select one of the shapes and colors in the list
    shape_number = random.randrange(0, 5)

    selected_shape = shape_list[shape_number]
    selected_color = shape_colors[random.randrange(0, 11)]

    return (selected_shape, selected_color, shape_number + 1)

class Square:
    global sq_len, sq_col, ppm, tile_timer
    def __init__ (self, x, y, selected_col, tile_coordinates):
        self.length = sq_len
        self.color = sq_col
        self.selected_col = selected_col
        self.position = tile_coordinates
        self.timer = datetime.now()
        self.inner_square_col = (52, 255, 33)
        self.inner_square_len = (sq_len / 6)
        self.selected = False
        self.x = x
        self.y = y

    # Draw squares
    def draw(self, window):
        pg.draw.rect(window, self.color, (self.x, self.y,
        self.length, self.length))

        #  Show square in the middle of each tile
        if not fixation_interval and not self.selected:
            pg.draw.rect(window, self.inner_square_col,
            ((self.x + (self.length / 2) - (self.inner_square_len / 2)),
            (self.y + (self.length / 2) - (self.inner_square_len / 2)),
            self.inner_square_len, self.inner_square_len))

    # When hovering over tile, change color based on whether it is empty or not
    def mouse_over(self, mouse_x, mouse_y):
        global faded_col, score, fixation_interval, shape_start, interval_start
        global rounds, choices, player_attempts, select_sq_start, hits

        if self.selected:
            if self.selected_col == opposite_color:
                self.color = opposite_color
            else:
                self.color = self.selected_col

        if not fixation_interval:
            if (self.x <= mouse_x <= self.x + self.length) and (self.y <=
            mouse_y <= self.y + self.length):
                if not self.selected:
                    self.color = faded_col
                    if select_sq_start:
                        self.timer = datetime.now()
                        select_sq_start = False
                    time_diff = (datetime.now() - self.timer)
                    if ((time_diff.microseconds / 1000) + (
                        1000 * time_diff.seconds)) >= tile_timer:
                        self.selected = True
                        select_sq_start = True
                        choices += 1
                        correct = (self.selected_col != opposite_color)
                        if correct:
                            score += 1
                            hits += 1
                        fixation_interval = True
                        interval_start = True
                        current_time = str(datetime.now()).split(' ')
                        shape_end = current_time[1].replace(' ', '')
                        inserts = [rounds, choices, self.position,
                        correct, shape_start, shape_end]
                        temp__attempts = pd.DataFrame(np.insert(
                            player_attempts.values,
                        len(player_attempts.index), values = inserts, axis=0))
                        temp__attempts.columns = player_attempts.columns
                        player_attempts = temp__attempts

            elif not self.selected:
                self.color = sq_col
                self.timer = datetime.now()

## Function to reveal whole board
def reveal_board(squares):
    temp_sqrs = list()
    for s in squares:
        s.selected = True
        temp_sqrs.append(s)
    return temp_sqrs

# Time in which game started running
start_moment = datetime.now()

# What happens while game is running
while run:

    pg.time.delay(10)
    now = datetime.now()

    # End simulation if user has been playing for an hour
    if float((now - start_moment).seconds / 3000) > 1:

        # Task end time
        current_time = str(now).split(' ')
        end_time = current_time[1].replace(' ', '')

        player_general = player_dir + "//{}.csv".format(str(player_id))
        player_choices = player_dir + "//{}_choices.csv".format(
            str(player_id))

        player_data = [{'Round' : rounds,
            'Shape Number': shape_number, 'Player_ID' : player_id,
            'Score' : score, 'Attempts' : choices, 'Start_Time' : start_time,
            'End_Time': end_time, 'Date' : game_date}]

        write_data(player_data)
        run = False

    # Fill screen with background color
    window.fill(background_color)

    # Getting mouse coordinates
    mouse_x, mouse_y = pg.mouse.get_pos()

    # Draw squares
    if len(square_list) < ncols * nrows:
        x_pos = horizontal_offset
        acc_x = 0
        shape_output = generate_shape()
        chosen_shape = shape_output[0]
        shape_color = shape_output[1]

        # Shape number follows a top to bottom notation based on the new shape
        # set. That is, red 4-square shape = 1, green U = 2, and so on.
        shape_number = shape_output[2]
        for a in range(0, ncols):
            y_pos = vertical_offset
            acc_y = 0
            for b in range(0, nrows):
                if [acc_x, acc_y] in chosen_shape:
                    square = Square(x_pos, y_pos, shape_color, [a, b])
                else:
                    square = Square(x_pos, y_pos, opposite_color, [a, b])
                square_list.append(square)
                if state != "intro" and state != "ending":
                    square.mouse_over(mouse_x, mouse_y)
                square.draw(window)
                y_pos += (interdistance + sq_len)
                acc_y += 1
            x_pos += (interdistance + sq_len)
            acc_x += 1

    else:
        for sq in square_list:
            if state != "intro" and state != "ending":
                sq.mouse_over(mouse_x, mouse_y)
            sq.draw(window)


    # User selecting a shape
    if fixation_interval:
        if len([s for s in square_list if (s.selected and
        s.selected_col != opposite_color)]) == len(chosen_shape):

            # Reveal board
            square_list = reveal_board(square_list)
            all_revealed = True

        if interval_start:
            fixation_timer = datetime.now()
            interval_start = False

        fixation_diff = (datetime.now() - fixation_timer)
        if ((fixation_diff.microseconds / 1000) + (
                1000 * fixation_diff.seconds)) >= fixation_period:
            fixation_interval = False
            current_time = str(now).split(' ')
            shape_start = current_time[1].replace(' ', '')
            if all_revealed:
                state = "ending"

    # Title above tiles
    top_font = pg.font.SysFont(None, math.floor(title_size))
    top_text = top_font.render('Battleship', True, opposite_color)
    window.blit(top_text, (((screen_width / 2) - (top_text.get_width() / 2)),
    vertical_offset - title_size))

    # Updating x_pos and y_pos variables for score text and end game button
    u_x_pos = x_pos - interdistance
    u_y_pos = y_pos - interdistance

    # Score text
    score_font = pg.font.SysFont(None, math.floor(end_button_height * 1.2))
    lower_text = score_font.render('Score: ' + str(score), True, opposite_color)
    window.blit(lower_text, (horizontal_offset, u_y_pos + lower_text.get_height()))

    # End game button
    end_button_width  = (screen_width / 3) * ppm
    end_button_x = u_x_pos - end_button_width
    end_button_y = u_y_pos + lower_text.get_height()

    pg.draw.rect(window, end_button_color, pg.Rect(end_button_x, end_button_y,
    end_button_width, end_button_height),
    border_radius = math.floor(end_button_height / 5))

    # End game button text
    end_button_font = pg.font.SysFont(None, math.floor(end_button_height * 0.9))
    end_button_text = end_button_font.render('Finish Game',
    True, background_color)
    window.blit(end_button_text, ((end_button_x +
    ((end_button_width - end_button_text.get_width()) / 2)),
    (end_button_y + ((end_button_height - end_button_text.get_height()) / 2))))

    # When user enters game
    if state == "intro":

        # Update display
        pg.display.update()

        # Instructions in case user is playing for the first time
        if not previous:
            try:
                begin = ms.confirm('Begin game?', 'Start', ["Let's go!", "Not now"])
                if begin == "Not now":
                    run = False
                else:
                    ms.alert(alert_message, alert_title, timeout = msg_time)
                    start_moment = datetime.now()
            except:
                ms.alert(alert_message, alert_title, timeout = msg_time)

        state = "playing"
        current_time = str(now).split(' ')
        start_time = current_time[1].replace(' ', '')
        game_date = current_time[0].replace(' ', '')


    # After user finishes one round
    elif state == "ending":

        # Task end time
        current_time = str(now).split(' ')
        end_time = current_time[1].replace(' ', '')

        # Write down player data in CSV and save the file in a separate folder.
        # Include general and round-specific data.

        player_general = player_dir + "//{}.csv".format(str(player_id))
        player_choices = player_dir + "//{}_choices.csv".format(
            str(player_id))

        player_data = [{'Round' : rounds,
            'Shape Number': shape_number, 'Player_ID' : player_id,
            'Score' : score, 'Attempts' : choices, 'Start_Time' : start_time,
            'End_Time': end_time, 'Date' : game_date}]

        write_data(player_data)

        # Reset game
        state = "intro"
        previous = True
        select_sq_start = True
        interval_start = True
        square_list = list()
        choices = 0
        hits = 0
        rounds += 1
        all_revealed = False
        player_attempts = initial_df

    # Game events
    for event in pg.event.get():

        # Quit game when exit button is pressed
        if event.type == pg.QUIT:
            run = False
                
    # Other events (besides quitting) are disabled
    # during the fixation interval
    # for better performance
    if not fixation_interval and state == "playing":

        # Exit game when exit button is pressed and make
        # it lighter when hovered
        if (end_button_x <= mouse_x
        <= (end_button_x + end_button_width)) and (end_button_y <= mouse_y
        <= (end_button_y + end_button_height)):
            end_button_color = default_btn_col
            if len([tile for tile in square_list
            if tile.selected == True]) != 0:
                exiting = True
        else:
            end_button_color = opposite_color
            exiting = False
            button_timer = datetime.now()

        fixation_timer = datetime.now()

    # Check exit button timer while user is looking at it
    if exiting and state == "playing":
        btn_diff = (datetime.now() - button_timer)
        if ((btn_diff.microseconds / 1000) + (
                1000 * btn_diff.seconds)) >= exit_timer:

            # Reveal board before exiting game
            square_list = reveal_board(square_list)
            fixation_interval = True
            interval_start = True

            if(end_button_color == default_btn_col):
                run = False

    # Update display
    pg.display.update()

# End game
pg.quit()