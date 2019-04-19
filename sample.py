import pygame
import pygame.mask
from pygame.locals import *
import sys
import math
import random
import time

vec = pygame.math.Vector2
randint = random.randint

SCREEN_SIZE = (1200, 800)
START_POSITION = (300, 400)
START_SIZE = 10.
black = (0, 0, 0)
white = (255,255,255)
grey = (200,200,200)

class State(object):
    # Creating the states of a state machine
    def __init__(self, name):
        self.name = name

    def do_actions(self):
        # Actions for the AI to be performing
        pass

    def check_conditions(self):
        # AI monitors to change any actions
        pass

    def entry_actions(self):
        # AI completes its entry onto the screen
        pass

    def exit_actions(self):
        # AI completes its exit off of the screen
        pass

class StateMachine(object):

    def __init__(self):
        self.states = {} # Stores the states of the entities
        self.active_state = None # The currently active state

    def add_state(self, state):
        # Add a state to the internal dictionary
        self.states[state.name] = state

    def think(self):
        # Only continue if there is an active state
        if self.active_state is None:
            return

        # Perform the actions of the active state, and check conditions
        self.active_state.do_actions()

        new_state_name = self.active_state.check_conditions()
        if new_state_name is not None:
            self.set_state(new_state_name)

    def set_state(self, new_state_name):
        # Change states and perform any exit/entry actions
        if self.active_state is not None:
            self.active_state.exit_actions()

        self.active_state = self.states[new_state_name]
        self.active_state.entry_actions()

class World(object):
    # Class to store the positions of all entities in map
    #   This object will help one entity determine attributes about other entites.
    def __init__(self, background):
        self.entities = {} # Store all of the entities
        self.entity_id = 0 # Last entity ID assignment
        self.background_size = pygame.surface.Surface(SCREEN_SIZE).convert()
        self.background = pygame.image.load(background).convert()

    def add_entity(self, entity):
        # Adds an entity to the world and stores an ID for it
        self.entities[self.entity_id] = entity
        entity.id = self.entity_id
        self.entity_id += 1

    def remove_entity(self, entity):
        # Remove an entity from the world
        del self.entities[entity.id]

    def get(self, entity_id):
        # Find the entity, given its ID (or None if no ID is found)
        if entity_id in self.entities:
            return self.entities[entity_id]
        else:
            return None

    def process(self, time_passed):
        # Process every entity in the world
        time_passed_seconds = time_passed / 1000.0
        for entity in self.entities.copy().values():
            entity.process(time_passed_seconds)

    def render(self, surface):
        # Draw the background and all the entities
        surface.blit(self.background, (0, 0))
        for entity in self.entities.values():
            entity.render(surface)

    def get_close_entity(self, name, location, range=100.):
        # Find an entity within range of a location
        location = vec(*location)

        for entity in self.entities.values():
            if entity.name == name:
                distance = location.distance_to(entity.location)
                if distance < range:
                    return entity
        return None

class GameEntity(pygame.sprite.Sprite):
    # Creating a base class to store common properties of entities and their actions
    def __init__(self, world, name, image):
        # Call the parent class (Sprite) constructor
        super().__init__()
        self.world = world
        self.name = name
        self.image = image
        self.rect = self.image.get_rect()
        self.location = vec(0, 0)
        self.destination = vec(0, 0)
        self.speed = 0
        self.brain = StateMachine()
        self.id = 0
        self.mask = pygame.mask.from_surface(self.image)

    def render(self, surface):
        # Blits the entities' images onto the screen
        x, y = self.location
        w, h = self.image.get_size()
        surface.blit(self.image, (x-w/2, y-h/2))

    def process(self, time_passed):
        # Run StateMachine to control the entity
        self.brain.think()

        if self.speed > 0 and self.location != self.destination:

            vec_to_destination = self.destination - self.location
            distance_to_destination = vec_to_destination.length()
            heading = vec_to_destination.normalize()
            travel_distance = min(distance_to_destination, time_passed * self.speed)
            self.location += travel_distance * heading

class Player(GameEntity):
    # Player object holds the same capabilities of Game Entity.
    def __init__(self, world, image):
        # Call the base constructor class
        GameEntity.__init__(self, world, "player", image)
        self.image = image
        self.dead_image = pygame.image.load('explosion.png').convert_alpha()
        self.health = 100
        self.location = vec(0, 0)
        self.max_speed = 300
        self.acceleration = 0
        self.speed = 0
        self.movement_direction = 0
        self.rotation = 0
        self.rotation_speed = 360 # Degrees per second
        self.rotation_direction = 0
        self.heading_x = 0
        self.heading_y = 0

    def render(self, surface):
        # Rotating image to match the rotation angle of the player and
        #  blitting to the screen
        self.rotated_player = pygame.transform.rotate(self.image, self.rotation)
        w, h = self.rotated_player.get_size()
        self.sprite_draw_pos = vec(self.location.x - w/2, self.location.y - h/2)
        surface.blit(self.rotated_player, self.sprite_draw_pos)

        # Draw health bar for player
        x, y = self.location
        w, h = self.image.get_size()
        bar_x = x - 12
        bar_y = y + h/2
        surface.fill((255, 0, 0), (bar_x, bar_y, 20, 4))
        surface.fill((0, 255, 0), (bar_x, bar_y, self.health, 4))

    def attacked(self):
        self.health -= 1
        if self.health <= 0:
            self.speed = 0
            self.image = self.dead_image

    def move(self, events, time_passed):
        time_passed_seconds = time_passed / 1000.0
        # Defining movement of player's object

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    #  Direction of increase in angle set to positive
                    self.rotation_direction = +1
                if event.key == pygame.K_RIGHT:
                    #  Direction of increase in angle set to negative
                    self.rotation_direction = -1
                if event.key == pygame.K_UP:
                    self.movement_direction = -1
                    self.acceleration = 10
                if event.key == pygame.K_DOWN:
                    self.movement_direction = 1
                    self.acceleration = -10

            if event.type == pygame.KEYUP:
                if event.key == pygame.K_LEFT:
                    self.rotation_direction = 0
                if event.key == pygame.K_RIGHT:
                    self.rotation_direction = 0
                if event.key == pygame.K_UP:
                    self.acceleration = 0
                    self.movement_direction = -1
                if event.key == pygame.K_DOWN:
                    self.acceleration = 0
                    self.movement_direction = 1

        # Increasing speed of player by acceleration
        self.speed += self.acceleration
        if self.speed > self.max_speed:
            self.speed = self.max_speed

        self.rotation += (self.rotation_direction * self.rotation_speed
            * time_passed_seconds)
        # Using unit circle trigonometry to find x value of triangle vector
        self.heading_x = math.sin(self.rotation*math.pi/180.0)
        # Using unit circle trigonometry to find y value of triangle vector
        self.heading_y = math.cos(self.rotation*math.pi/180.0)
        # Creating new vector using values
        self.heading = vec(self.heading_x, self.heading_y)
        self.heading *= self.movement_direction

        # Increasing position of PLayer by heading and speed and time
        self.location += self.heading * self.speed * time_passed_seconds

        # Prevent player from leaving the map
        if (self.location.x > SCREEN_SIZE[0]):
            self.location.x = SCREEN_SIZE[0]
        elif (self.location.x < 0):
            self.location.x = 0
        if (self.location.y > SCREEN_SIZE[1]):
            self.location.y = SCREEN_SIZE[1]
        elif (self.location.y < 0):
            self.location.y = 0

    def process(self, time_passed):
        #  Updating rect coordinates of projectile to new location.
        #  self.rect = self.image.get_rect(center=self.location)
        pass

class Alien(GameEntity):

    def __init__(self, world, image):
        # Call the base constructor class
        GameEntity.__init__(self, world, "alien", image)
        self.dead_image = pygame.image.load('explosion.png').convert_alpha()

        # Create instance of each of the states
        exploring_state = AlienStateExploring(self)
        hunting_state = AlienStateHunting(self)

        # Add states to the state machine (self.brain)
        self.brain.add_state(exploring_state)
        self.brain.add_state(hunting_state)

    def render(self, surface):
        # Call the render function of the base class
        GameEntity.render(self, surface)

class AlienStateExploring(State):

    def __init__(self, alien):
        # Call the base class constructor to initialize the state
        State.__init__(self, "exploring")
        # Set the alien that this State will manipulate
        self.alien = alien

    def random_destination(self):
        # Select a random point on the screen to move towards
        w, h = SCREEN_SIZE
        self.alien.destination = vec(random.randint(0, w), random.randint(0, h))

    def do_actions(self):
        # Change direction 1 in 20 calls
        if random.randint(1, 20) == 1:
            self.random_destination()

    def check_conditions(self):
        # If the player is nearby, switch to seeking state
        player = self.alien.world.get_close_entity("player",
            self.alien.location)
        if player is not None:
            self.alien.player_id = player.id
            return "hunting"

        return None

    def entry_actions(self):
        # Set speed for alien
        self.alien.speed = 75.
        # Select spawn point for alien off of the screen
        spawn_zones = []
        # Randomly generated two spawn points for enemy ships
        spawn1_coords = ([-50, random.randint(0, SCREEN_SIZE[1])])
        spawn_zones.append(spawn1_coords)
        spawn2_coords = (SCREEN_SIZE[0] + 50, random.randint(0, SCREEN_SIZE[1]))
        spawn_zones.append(spawn2_coords)

        # Randomly choose spawn point off the map for the enemey ships
        alien_spawn = random.choice(spawn_zones)
        self.alien.destination = vec(alien_spawn[0], alien_spawn[1])

class AlienStateHunting(State):

    def __init__(self, alien):

        State.__init__(self, "hunting")
        self.alien = alien
        self.got_kill = False

    def do_actions(self):

        player = self.alien.world.get(self.alien.player_id)

        if player is None:
            return

        self.alien.destination = player.location

        if self.alien.location.distance_to(player.location) < 15:

            # Reduce player's health
            if random.randint(1, 5) == 1:
                player.attacked()

                if player.health <= 0:
                    self.got_kill = True

    def check_conditions(self):

        player = self.alien.world.get(self.alien.player_id)

        # If player is dead or there is no player, return to exploring state
        if self.got_kill or player is None:
            return "exploring"

        return None

    def entry_actions(self):

        self.speed = 75. + random.randint(0, 50)

    def exit_actions(self):

        self.got_kill = False

class Projectile(GameEntity):
    # Projectile object holds the same capabilities of Game Entity.
    def __init__(self, world, image):
        # Firing projectile based on location and direction of Player
        GameEntity.__init__(self, world, "projectile", image)

    def fire_laser(self, x_cor, y_cor, degree_x, degree_y, time_passed):
        self.speed = 500
        self.location = vec(x_cor, y_cor)
        self.direction = vec(degree_x, degree_y)
        return self.location, self.direction

    def do_actions(self):
        pass
        # alien = self.alien.world.get(self.alien.player_id)

    def render(self, surface):
        # Call the render function of the base class
        GameEntity.render(self, surface)
        # Call the base function of the Game Entity
        x, y = self.location # pass in player's current location
        w, h = self.image.get_size()
        self.rect = self.image.get_rect(center=self.rect.center)
        surface.blit(self.image, (x, y, w, h))

    def process(self, time_passed):
        # Firing projectile based on location and direction of Player
        #  updating rect coordinates of projectile to new location.
        self.location += self.direction * self.speed * time_passed

def text_objects(text, font, color):
    # Create a new surface with the specified text on it. Surface returned
    #  will be the dimensions required to hold the text.
    textSurface = font.render(text, True, color)
    return textSurface, textSurface.get_rect()

def button(screenname, textType, msg, x, y, wdth, hght, act_clr, inact_clr, action=None):

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()

    if (x + wdth) > mouse[0] > x and (y + hght) > mouse[1] > y:
        pygame.draw.rect(screenname, white, (x, y, wdth, hght))
        textSurf, textRect = text_objects(msg, textType, black)
        textRect.center = ((x + (wdth/2)), (y + (hght/2)))
        screenname.blit(textSurf, textRect)
        if click[0] == 1 and action != None:
            if action == "play":
                main()
            elif action == "quit":
                pygame.quit()
                quit()
    else:
        pygame.draw.rect(screenname, grey, (x, y, wdth, hght))
        textSurf, textRect = text_objects(msg, textType, black)
        textRect.center = ((x + (wdth/2)), (y + (hght/2)))
        screenname.blit(textSurf, textRect)

def main():

    w, h = SCREEN_SIZE
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    clock = pygame.time.Clock()
    clock.get_time()
    score_text = pygame.font.Font('BebasNeue-Regular.ttf', 20)

    background_image_file = "space_background.png"
    player_image_file = pygame.image.load("spaceship.png").convert_alpha()
    enemy_image =  pygame.image.load("enemyship.png").convert_alpha()
    laser_image = pygame.image.load("laser.png").convert_alpha()

    world = World(background_image_file)
    player = Player(world, player_image_file)
    projectile = Projectile(world, laser_image)
    player.location = vec(w/2, h/2)
    world.add_entity(player)
    player_score = 0
    pygame.display.set_caption("SpaceHunter")

    aliens = pygame.sprite.Group()
    bullets = pygame.sprite.Group()

    alien_key_list = []

    def end_scene(surf, score, text, x, y):
        final_score = str(score)
        font = pygame.font.Font('BebasNeue-Regular.ttf', 20)
        text_surface = font.render(text + final_score, True, white)
        text_rect = text_surface.get_rect()
        text_rect.midtop = (x, y)
        surf.blit(text_surface, text_rect)

    def add_aliens(world, alien_count, enemy_image):
        # Create list of spawn zones for aliens
        spawn_zones = []
        # Randomly generated two spawn points for enemy ships
        spawn1_coords = ([-50, random.randint(0, SCREEN_SIZE[1])])
        spawn_zones.append(spawn1_coords)
        spawn2_coords = (SCREEN_SIZE[0] + 50, random.randint(0, SCREEN_SIZE[1]))
        spawn_zones.append(spawn2_coords)

        # Randomly choose spawn point off the map for the enemey ships
        alien_spawn = random.choice(spawn_zones)

        for alien_no in range(alien_count):
            alien = Alien(world, enemy_image)
            aliens = pygame.sprite.Group(alien)
            world.add_entity(alien)
            alien_key = world.entity_id
            alien_key_list.append(alien_key)
            alien.location = vec(alien_spawn[0], alien_spawn[1])
            alien.brain.set_state("exploring")

    add_aliens(world, 30, enemy_image)

    while True:
        events = pygame.event.get()

        time_passed = clock.tick(30)
        # Passing keys and key events to player.
        player.move(events, time_passed)
        # Creating new list to hold projectiles for deletion
        projectiles_list = []

        world.render(screen)
        world.process(time_passed)

        for e in events:
            if e.type == QUIT:
                pygame.quit()
                sys.exit()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    # Creating instance of projectile and accessing projectile's functionality
                    projectile_X, projectile_Y = player.heading
                    projectile_x, projectile_y = player.location
                    world.add_entity(projectile)
                    bullets.add(projectile)
                    key = projectile.id
                    projectile.fire_laser(projectile_x, projectile_y,
                        projectile_X, projectile_Y, time_passed)

        # Adding projectile to deletion list if coordinates greater than screen
        if projectile.location[0] < 0 or projectile.location[0] > (SCREEN_SIZE[0]):
            projectiles_list.append(key)
        elif projectile.location[1] < 0 or projectile.location[1] > (SCREEN_SIZE[1]):
            projectiles_list.append(key)

        # Iterate over the list and delete the corresponding key from world dict
        #   Reduce the world entity iterator by 1.
        for key in projectiles_list:
            if key in world.entities:
                world.entity_id -= 1
                del world.entities[key]

        for key in alien_key_list:
            if key in world.entities:
                alienObj = world.entities.get(key)

                offset_x = int(alienObj.location.x) - int(projectile.location.x)
                offset_y = int(alienObj.location.y) - int(projectile.location.y)

                overlap = projectile.mask.overlap(alienObj.mask, (offset_x, offset_y))

                if overlap:
                    world.remove_entity(alienObj)
                    player_score += 1
                    add_aliens(world, random.randint(0, 2), enemy_image)
                else:
                    None

        TextSurf, TextRect = text_objects(str(player_score), score_text, white)
        TextRect.center = (SCREEN_SIZE[0]/2, 100)
        screen.blit(TextSurf, TextRect)

        if player.health <= 0:
            screen.fill(black)
            end_scene(screen, str(player_score), "Game Over! Your Final Score: ", SCREEN_SIZE[0]/2, 100)
            button(screen, score_text, "Play again?", 400, 525, 100, 50, white, grey, "play")
            button(screen, score_text, "Quit", 700, 525, 100, 50, white, grey, "quit")

        pygame.display.update()

def game_intro():

    MAX_STARS = 250
    STAR_SPEED = 1

    def createStars(screenname):
        # Create the starfield
        global stars
        stars = []
        for i in range(MAX_STARS):
            # Star represented in list as tuple of coordinates
            star = [random.randrange(0, screen.get_width() -1),
                    random.randrange(0, screen.get_height() - 1)]
            stars.append(star)

    def move_stars(screenname):
        # Move and draw the stars in the given screen
        global stars
        for star in stars:
            star[1] += STAR_SPEED
            # If a star hits the bottom border of the screen, we
            #   reposition it at the top of the screen with random x-coord
            if star[1] >= screen.get_height():
                star[1] = 0
                star[0] = random.randrange(0, SCREEN_SIZE[0])
            # Setting the color for each star
            screenname.set_at(star, (white))

    pygame.init()
    screen = pygame.display.set_mode(SCREEN_SIZE, 0, 32)
    largeText = pygame.font.Font('BebasNeue-Regular.ttf', 120)
    mediumText = pygame.font.Font('BebasNeue-Regular.ttf', 20)
    smallText = pygame.font.Font('BebasNeue-Regular.ttf', 15)
    # Creating stars for the background of the introduction screen
    createStars(screen)

    intro = True

    while intro:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        introduction_1 = "You are the last battleship remaining, and the enemy is closing in..."
        introduction_2 = "Dodge the alienships with the arrow keys [UP + DOWN + LEFT + RIGHT] to control the steering of the ship"
        introduction_3 = "Hit the spacebar [SPACEBAR] to fire the ship's lasers"

        screen.fill(black)
        TextSurf, TextRect = text_objects("Space Hunter", largeText, white)
        directions1Surf, directions1Rect = text_objects(introduction_1, mediumText, white)
        directions2Surf, directions2Rect = text_objects(introduction_2, smallText, white)
        directions3Surf , directions3Rect = text_objects(introduction_3, smallText, white)
        directions1Rect.center = (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2 - 100)
        directions2Rect.center = (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2 + 75)
        directions3Rect.center = (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2 + 100)
        TextRect.center = (SCREEN_SIZE[0]/2, SCREEN_SIZE[1]/2)
        screen.blit(directions1Surf, directions1Rect)
        screen.blit(directions2Surf, directions2Rect)
        screen.blit(directions3Surf, directions3Rect)
        screen.blit(TextSurf, TextRect)

        button(screen, smallText, "Start", 400, 525, 100, 50, white, grey, "play")
        button(screen, smallText, "Quit", 700, 525, 100, 50, white, grey, "quit")

        # Calling stars for background imagery
        move_stars(screen)

        pygame.display.update()

if __name__ == "__main__":
    game_intro()
