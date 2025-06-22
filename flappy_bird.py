import pygame
import neat
import time
import os
import random
pygame.font.init()  # Initialize the pygame font module
# Constants
WIN_WIDTH = 500
WIN_HEIGHT = 800


bird_images = [pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bird" + str(i) + ".png"))) for i in range(1, 4)] # list of bird images for animation
#scale2x is used to double the size of the images , image.load loads the image from the specified path 
pipe_image = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "pipe.png"))) # pipe image
base_image = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "base.png"))) # base image
bg_image = pygame.transform.scale2x(pygame.image.load(os.path.join("imgs", "bg.png"))) # background image
stat_font = pygame.font.SysFont("comicsans", 50) # font for the score display

###### Bird Class ######
class Bird:
    imgs = bird_images # list of bird images for animation
    max_rotation = 25 # maximum rotation angle of the bird
    rotation_vel = 20 # how fast the bird rotates
    animation_time = 5 # how long each frame of the bird animation lasts
    
    def __init__(self, x, y):
        self.x = x # starting x position of the bird
        self.y = y # starting y position of the bird
        self.tilt = 0 # how much the bird is tilted
        self.tick_count = 0 # initial tick count to keep track of time
        self.vel = 0 # velocity of the bird
        self.height = self.y # initial height of the bird
        self.img_count = 0 # current frame (1,2 or 3) of the bird animation
        self.img = self.imgs[0]

    def jump(self): # make the bird jump
        self.vel = -10.5 # negative velocity to make the bird go up
        self.tick_count = 0 # keep track of the time since the last jump
        self.height = self.y # keep track of the height of the bird when it jumped

    def move(self): # update the position of the bird
        self.tick_count += 1 # increment the tick count
        d = self.vel * self.tick_count + 1.5 * self.tick_count ** 2 # calculate the distance the bird has moved
        # -10.5 * 1 + 1.5 * 1 ** 2 = -10.5 + 1.5 = -9, this means the bird has moved up 9 pixels
        if d >= 16: # if we move down 16 pixels, we set the distance to 16 pixels
            d = 16
        if d < 0:
            d -= 2 # if we move up, lets move up a bit more
        
        self.y = self.y + d # update the y position of the bird based on displacement

        if d < 0 or self.y < self.height + 50: # if we are moving upgwards or if we are below the height of the bird when it jumped
            if self.tilt < self.max_rotation:
                self.tilt = self.max_rotation
        else: # if we are moving downwards
            if self.tilt > -90:
                self.tilt -= self.rotation_vel

    def draw(self, win): # draw the bird on the window
        self.img_count += 1
        # this shows what bird animation is used when
        if self.img_count < self.animation_time:
            self.img = self.imgs[0]
        elif self.img_count < self.animation_time * 2:
            self.img = self.imgs[1]
        elif self.img_count < self.animation_time * 3:
            self.img = self.imgs[2]
        elif self.img_count < self.animation_time * 4:
            self.img = self.imgs[1]
        elif self.img_count == self.animation_time * 4 + 1:
            self.img = self.imgs[0]
            self.img_count = 0         
        
        if self.tilt <= -80:
            self.img = self.imgs[1]
            self.img_count = self.animation_time * 2 # if the bird is falling down, we use the second image of the bird animation

        rotated_image = pygame.transform.rotate(self.img, self.tilt) # rotate the bird image based on the tilt
        new_rect = rotated_image.get_rect(center=self.img.get_rect(topleft=(self.x, self.y)).center)
        win.blit(rotated_image, new_rect.topleft)
        # blit the rotated image on the window at the new position
        # we use the center of the image to draw it so that it rotates around its center

    def get_mask(self): # get the mask of the bird image for collision detection
        # mask is used for pixel perfect collision detection
        return pygame.mask.from_surface(self.img)

###### Pipe Class ######
class Pipe:
    gap = 200  # gap between the top and bottom pipes
    velocity = 5  # speed at which the pipes move left

    def __init__(self, x):
        self.x = x # x position of the pipe
        self.height = 0  # height of the top pipe
        self.gap = 100 # gap between the top and bottom pipes

        self.top = 0  # y position of the top pipe
        self.bottom = 0  # y position of the bottom pipe
        self.top_pipe = pygame.transform.flip(pipe_image, False, True)  # flip the pipe image for the top pipe
        self.bottom_pipe = pipe_image  # image of the bottom pipe

        self.passed = False  # flag to check if the pipe has been passed by the bird
        self.set_height()  # set the height of the pipes to define where the top and bottom of the pipe is

    def set_height(self):
        self.height = random.randrange(50, 450) # random height for the top pipe
        self.top = self.height - self.top_pipe.get_height()  # calculate the y position of the top pipe
        self.bottom = self.height + self.gap  # calculate the y position of the bottom pipe 
    
    def move(self):
        self.x -= self.velocity # move the pipes to the left by the velocity amount
    
    def draw(self, win):
        win.blit(self.top_pipe, (self.x, self.top))
        win.blit(self.bottom_pipe, (self.x, self.bottom))  # draw the top and bottom pipes on the window
    
    # check for collision between the bird and the pipes
    def collide(self, bird): 
        bird_mask = bird.get_mask() # get the mask of the bird image for collision detection
        
        # get the mask of the top and bottom pipes for collision detection
        top_mask = pygame.mask.from_surface(self.top_pipe)
        bottom_mask = pygame.mask.from_surface(self.bottom_pipe)

        top_offset = (self.x - bird.x, self.top - round(bird.y))  # offset for the top pipe, they are rounded to the nearest integer
        bottom_offset = (self.x - bird.x, self.bottom - round(bird.y))

        # check for collision between the bird and the top pipe
        b_point = bird_mask.overlap(bottom_mask, bottom_offset)  # get the point of collision between the bird and the bottom pipe
        t_point = bird_mask.overlap(top_mask, top_offset)  # get the point of collision between the bird and the top pipe
        if t_point or b_point:  # if there is a collision
            return True  # return True if there is a collision
        return False  # return False if there is no collision

###### Base Class ######
class Base:
    velocity = 5  # speed at which the base moves left
    width = base_image.get_width()  # width of the base image
    image = base_image  # base image

    def __init__(self, y):
        self.y = y  # y position of the base
        self.x1 = 0  # x position of the first base image
        self.x2 = self.width  # x position of the second base image

    # This allows the base image to be looped
    def move(self):
        self.x1 -= self.velocity
        self.x2 -= self.velocity  # move the base images to the left by the velocity
        if self.x1 + self.width < 0:  # if the first base image goes off the screen
            self.x1 = self.x2 + self.width  # reset the x position of the first base image to the right of the second base image
        if self.x2 + self.width < 0:  # if the second base image goes off the screen
            self.x2 = self.x1 + self.width  # reset the x position of the second base image to the right of the first base image
    
    def draw(self, win):
        win.blit(self.image, (self.x1, self.y))
        win.blit(self.image, (self.x2, self.y))  # draw the base

    
def draw_window(win, birds,pipes = [],base= None, score = 0):
    win.blit(bg_image, (0, 0))  # Draw the background blit means to draw the image on the window
    for pipe in pipes:  # Draw each pipe in the list of pipes
        pipe.draw(win)
    score_label = stat_font.render("Score: " + str(score), 1, (255, 255, 255))  # Render the score label
    win.blit(score_label, (WIN_WIDTH - score_label.get_width() - 15, 10))  # Draw the score label on the window
    base.draw(win)  # Draw the base
    for bird in birds:  # Draw each bird in the list of birds
        bird.draw(win)  # Draw the bird
    pygame.display.update()  # Update the display

###### Main Function ######
def main(genomes, config):
    nets = []  # List to hold the neural networks for each bird
    ge = []  # List to hold the genome objects for each bird this is a tuple of (id, genome)
    birds = []

    for _,g in genomes:  # Iterate through the genomes
        net = neat.nn.FeedForwardNetwork.create(g, config)  # Create a neural network for each genome
        nets.append(net)  # Add the neural network to the list
        birds.append(Bird(230, 350))  # Create a Bird instance and add it to the list
        g.fitness = 0  # Initialize the fitness of the genome to 0
        ge.append(g)  # Add the genome to the list

    base = Base(730)  # Create a base instance at y position 730
    pipes = [Pipe(600)]  # Create a list of pipes with one pipe at x position 700
    win = pygame.display.set_mode((WIN_WIDTH, WIN_HEIGHT))  # Create a window with specified width and height
    pygame.display.set_caption("Flappy Bird")  # Set the window title
    score = 0  # Initialize the score
    clock = pygame.time.Clock()  # Create a clock to control the frame rate
    
    run = True  # Game loop control variable
    while run:
        clock.tick(30)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.quit()  # Quit the game if the window is closed
                quit()
        
        pipe_index = 0  # Index of the current pipe
        if len(birds) > 0:  # If there are birds in the game
            if len(pipes) > 1 and birds[0].x > pipes[0].x + pipes[0].top_pipe.get_width():
                pipe_index = 1  # If the first bird has passed the first pipe, set the index to 1 to check the second
        else:
            run = False
            break  # If there are no birds left, end the game loop
    
        for x, bird in enumerate(birds):  # Iterate through the list of birds
            bird.move()
            ge[x].fitness += 0.1  # Increment the fitness of the genome for each frame the bird is alive
            output = nets[x].activate((bird.y, abs(bird.y - pipes[pipe_index].height), abs(bird.y - pipes[pipe_index].bottom)))

            if output[0] > 0.5:  # If the output of the neural network is greater than 0.5, make the bird jump
                bird.jump()
        
        add_pipe = False  # Flag to check if a new pipe should be added
        rem = []
        for pipe in pipes:  # Move each pipe in the list of pipes
            for x, bird in enumerate(birds):  # Iterate through the list of birds
                if pipe.collide(bird):
                    ge[x].fitness -= 1 # Decrease the fitness of the genome if the bird collides with a pipe
                    birds.pop(x)  # Remove the bird from the list if it collides with a pipe
                    nets.pop(x)  # Remove the neural network associated with the bird
                    ge.pop(x)  # Remove the genome associated with the bird
                
                if not pipe.passed and pipe.x < bird.x:  # If the bird has not passed the pipe and the pipe is to the left of the bird
                    pipe.passed = True
                    add_pipe = True  # Set a flag to add a new pipe

            if pipe.x + pipe.top_pipe.get_width() < 0:
                rem.append(pipe)  # If the pipe goes off the screen, remove it from the list

            pipe.move()
        if add_pipe:
            score += 1  # Increment the score if the bird has passed a pipe
            for g in ge:
                g.fitness += 5 # Increase the fitness of the genome for passing a pipe
            pipes.append(Pipe(600))  # Add a new pipe to the list of pipes
        
        for r in rem:  # Remove pipes that have gone off the screen
            pipes.remove(r)
    
        for x,bird in enumerate(birds):  # Move each bird in the list of birds
            if bird.y + bird.img.get_height() >= 730 or bird.y < 0:  # If the bird goes below the base
                birds.pop(x)  # Remove the bird from the list
                nets.pop(x)  # Remove the neural network associated with the bird
                ge.pop(x)  # Remove the genome associated with the bird

        base.move()
        draw_window(win, birds, pipes, base, score)  # Draw the window with the bird, pipes, and base
    


# This code implements a Flappy Bird game using the NEAT (NeuroEvolution of Augmenting Topologies) algorithm
# The game features a bird that the player controls to avoid pipes, with the help of a neural network that learns to play the game
# The NEAT algorithm evolves the neural networks over generations

def run(config_path):
    # This function is a placeholder for running the NEAT algorithm with the given configuration file
    # It is not implemented in this code snippet, but it would typically involve setting up the NEAT population,
    # running the simulation, and evaluating the fitness of the neural networks controlling the birds.
    config = neat.Config(neat.DefaultGenome, neat.DefaultReproduction, 
                         neat.DefaultSpeciesSet, neat.DefaultStagnation, 
                         config_path)  # Load the NEAT configuration
    
    p = neat.Population(config)  # Create a NEAT population with the configuration
    
    p.add_reporter(neat.StdOutReporter(True))  # Add a reporter to print the output to the console
    stats = neat.StatisticsReporter()  # Create a statistics reporter
    p.add_reporter(stats)  # Add the statistics reporter to the population

    winner = p.run(main, 50)  # Run the NEAT algorithm for 50 generations with the main function as the evaluation function

if __name__ == "__main__": # This allows the script to be run directly
    local_dir = os.path.dirname(__file__)  # Get the directory of the current file
    config_path = os.path.join(local_dir, "config-feedforward.txt")  # Path to the configuration file
    run(config_path)  # Run the NEAT algorithm with the configuration file      
