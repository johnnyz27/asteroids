import sys
import asyncio
import pygame
import random
import math

pygame.init()
pygame.font.init()
WIDTH = 1000
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Asteroid Game")
clock = pygame.time.Clock()


async def main():
    MISSILE_SPEED = 7

    font = pygame.font.Font(None, 36)

    running = True

    class Ship:
        def __init__(self, x, y):
            self.r = 15

            self.pos = pygame.math.Vector2(x, y)
            self.vel = pygame.math.Vector2(0,0)
            self.acceleration = pygame.math.Vector2(0,0)

            self.angle = 90
            self.rotate_speed = 3
            self.ship_speed = 4
            self.max_speed = 7

            self.thrust = 0.15
            self.drag = 0.99
            self.forward = pygame.math.Vector2(0,-1)

        def move(self):
            self.acceleration = pygame.math.Vector2(0,0)
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                self.angle += self.rotate_speed
            if keys[pygame.K_RIGHT]:
                self.angle -= self.rotate_speed

            radians = math.radians(self.angle)

            self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))

            if keys[pygame.K_UP]:
                self.acceleration = self.forward * self.thrust
            self.vel += self.acceleration
            self.vel *= self.drag
            if self.vel.length() > self.max_speed:
                self.vel.scale_to_length(self.max_speed)
            
            self.pos += self.vel

            self.pos.x %= (WIDTH + self.r * 2)
            self.pos.y %= (HEIGHT + self.r * 2)

        def draw(self):
            left = self.forward.rotate(140)
            right = self.forward.rotate(-140)

            p1 = self.pos + self.forward * 22
            p2 = self.pos + left * 16
            p3 = self.pos + right * 16

            pygame.draw.polygon(
                screen,
                "white",
                [p1, p2, p3],
                2
            )



    class Missile:
        
        def __init__(self, start_pos, end_pos):
            self.pos = pygame.math.Vector2(start_pos)
            self.r = 5
            direction = end_pos - start_pos
            direction = direction.normalize()
            self.missile_vel = direction * MISSILE_SPEED
        def move(self):
            self.pos += self.missile_vel
        def draw(self):
            pygame.draw.circle(screen, (255, 50, 50), (int(self.pos.x), int(self.pos.y)), self.r)


    class Asteroid:
        def __init__(self):
            self.r = random.randint(30, 50)
            self.mass = self.r
            # Asteroid Positions
            self.pos = pygame.math.Vector2(random.randint(0,WIDTH), random.randint(0, HEIGHT))
            
            # Asteroid Velocities
            speed = random.randint(1, 4)
            angle = random.uniform(0, 2 * math.pi)
            self.vel = pygame.math.Vector2(speed, 0).rotate_rad(angle)

        def draw(self):
            pygame.draw.circle(screen, (128,128,128), (self.pos.x, self.pos.y), self.r)
        def move(self):
            self.pos += self.vel
            self.pos.x %= (WIDTH + self.r * 2)
            self.pos.y %= (HEIGHT + self.r * 2)

    class Enemy:
        def __init__(self):
            self.detection_range = 300
            self.fov_threshold = 0.7

            self.pos = pygame.Vector2(WIDTH/4, HEIGHT/2)
            self.speed = 1.25
            self.angle = 0

            self.detected = False

        def update(self, player_pos):
            radians = math.radians(self.angle)
            self.forward = pygame.Vector2(math.cos(radians), -math.sin(radians))
            to_player = (player_pos - self.pos)
            if to_player.length() > 0:
                to_player = to_player.normalize()
            distance = self.pos.distance_to(player_pos)
            dot = self.forward.dot(to_player)
            if (
                distance < self.detection_range
                and dot > self.fov_threshold
            ):
                self.detected = True
                self.pos += to_player * self.speed
                self.angle = to_player.angle_to((1,0))

            else:
                self.detected = False
        
        def draw(self):
            pygame.draw.circle(
                screen,
                "gray",
                self.pos,
                self.detection_range,
                1
            )

            pygame.draw.line(
                screen,
                "red",
                self.pos,
                self.pos + self.forward * 100,
                3
            )

            color = (255,0,0) if self.detected else (255,255,255)

            left = self.forward.rotate(140)
            right = self.forward.rotate(-140)

            p1 = self.pos + self.forward * 22
            p2 = self.pos + left * 16
            p3 = self.pos + right * 16

            pygame.draw.polygon(
                screen,
                color,
                [p1, p2, p3],
                2
            )


    ship = Ship(WIDTH // 2, HEIGHT // 2)
    enemy = Enemy()

    asteroids = []
    missiles = []
    for i in range(6):
        asteroids.append(Asteroid())

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                target = pygame.Vector2(event.pos)
                missiles.append(Missile(ship.pos, target))

        screen.fill((0,0,0))
        ship.move()
        ship.draw()
        enemy.update(ship.pos)
        enemy.draw()

        if (ship.pos.distance_to(enemy.pos) < ship.r):
            running = False

        for missile in missiles:
            missile.move()
            missile.draw()

        for ast in asteroids:
            ast.move()
            ast.draw()
        
            if (ship.pos.distance_to(ast.pos) < ship.r + ast.r):
                running = False

        

        for i in range(len(asteroids)):
            ast1 = asteroids[i]
            for j in range(i+1, len(asteroids)):
                ast2 = asteroids[j]
                dist = ast1.pos - ast2.pos
                dist_len = dist.length()
                if dist_len < ast1.r + ast2.r and dist_len > 0:
                    m1, m2 = ast1.mass, ast2.mass
                    normal_vector = dist.normalize()
                    angle1 = math.radians(ast1.vel.angle_to(normal_vector))
                    angle2 = math.radians(ast2.vel.angle_to(normal_vector))

                    vel1_n = ast1.vel.length() * math.cos(angle1)
                    vel2_n = ast2.vel.length() * math.cos(angle2)
                    if vel1_n - vel2_n < 0:
                        new_vel1 = (vel1_n * (m1-m2) + (2 * m2 * vel2_n))/(m1+m2)
                        new_vel2 = (vel2_n * (m2-m1) + (2 * m1 * vel1_n))/(m1+m2)
                        ast1.vel += (new_vel1 - vel1_n) * normal_vector
                        ast2.vel += (new_vel2 - vel2_n) * normal_vector
        
        if enemy.detected:
            state_text = font.render("State: Enemy Detected", True, (255,0,0))
        else:
            state_text = font.render("State: Patrol", True, ((255,255,255)))
        screen.blit(state_text, (30, 30))

        for missile in missiles:
            for ast in asteroids:
                if missile.pos.distance_to(ast.pos) < missile.r + ast.r:
                    if missile in missiles:
                        missiles.remove(missile)
                    if ast in asteroids:
                        asteroids.remove(ast)
        
        if len(asteroids) == 0:
            for i in range(6):
                asteroids.append(Asteroid())
                

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()
    sys.exit()
asyncio.run(main())
