# 🌌 Gravitroids
**Gravitroids** is a 2D arcade-style gravitational shooter built with Python and Pygame. The player pilots a small triangular ship through space, using momentum and gravity from nearby planets to maneuver, destroy planetary bodies, and avoid deadly collisions.

---

## 🎮 Goal

Break apart moving planets using your ship’s projectiles. Each successful hit splits a planet into two smaller ones and grants you points. Survive as long as possible by managing your movement, shooting wisely, and avoiding both planets and the screen edges.

---

## 🕹️ Controls

| Action         | Key         |
|----------------|-------------|
| Thrust         | Up Arrow    |
| Turn Left      | Left Arrow  |
| Turn Right     | Right Arrow |
| Shoot          | Spacebar    |
| Pause          | P           |
| Quit           | Q           |
| Restart (on death screen) | R |

---

## 💥 Fail Conditions

- **Colliding with a planet** will result in death.
- **Falling off the screen** resets your position and deducts 40 points.
- **Reaching 0 or negative points** ends the game.

---

## 🧠 Gameplay Mechanics

- **Gravity Simulation**: Planets exert Newtonian gravity on the player and each other.
- **Shooting**: Bullets move in a straight line, can destroy planets, and cost 2 points per shot.
- **Planet Splitting**: When hit by a bullet, planets split into two smaller ones if large enough.
- **Trajectory Preview**: A green (or red) line shows a predicted future path to help navigate.

---

## ✨ Visuals & Feedback

- **Gradient Background**: The background color dynamically changes based on the player's current score.
- **Glow Effects**: Planets emit soft glows based on mass.
- **Death Screen**: Custom messages depending on cause of death (collision or point loss).
- **Title Screen**: Animated, with orbiting circles and pulsating "Press Enter" prompt.

---

## 🧪 Libraries Used

- [`pygame`](https://www.pygame.org/) — for graphics, input, sound, and game loop
- `math`, `random`, and `sys` — for physics, randomness, and system control

---

## 🚀 Setup & Run

Make sure you have Python 3 installed. Then run:

```bash
pip install pygame
python Gravitroids.py
```

## Pending additions
- **readability**: split project into several files to enhance readability. also further classify functions
- **exe compiling**: compile the game into an EXE so it can be run independently of Python. Have to find a work around for the virus flag

## Notes
- gravitroids will save your information to a json file. I will not be collecting this information (partly as I don't know how to, and partly because I don't want to invade your privacy)
- if you wish to leave feedback, you can add me on discord (theroyalgamer65) or email me directly (gillmuntaj03@gmail.com)
