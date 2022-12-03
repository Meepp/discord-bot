from src.web_server.lib.game.Utils import Point, EntityDirections, direction_to_point
from src.web_server.lib.game.exceptions import InvalidAction


class MovableEntity:
    def __init__(self, unique_identifier: str, game):
        self.uid = unique_identifier
        self.position = Point(1, 1)

        self.last_position = self.position
        self.class_name = None

        self.can_move = True

        self.updated = True
        self.alive = True

        self.movement_cooldown = 2  # Ticks
        self.movement_timer = 0
        self.movement_queue = []
        self.moving = False

        self.direction = EntityDirections.DOWN

        from src.web_server.lib.game.HallwayHunters import HallwayHunters
        self.game: HallwayHunters = game

    def start(self):
        self.movement_timer = 0

    def tick(self):
        self.movement_timer = max(0, self.movement_timer - 1)
        # self.last_position = self.position

    def change_position(self, point):
        self.position = point

    def movement_action(self):
        """
        Performs the movement action, and will raise an InvalidAction exception if the move is not allowed.
        It will return the attempted move, which may result in some additional logic in the inherited class.
        :return:
        """
        if not self.can_move:
            return

        if len(self.movement_queue) == 0:
            self.moving = False
            return

        move = self.movement_queue.pop(0)

        # Set the correct player model direction based on input
        if move.x == 1:
            self.direction = EntityDirections.RIGHT
        elif move.x == -1:
            self.direction = EntityDirections.LEFT
        elif move.y == 1:
            self.direction = EntityDirections.DOWN
        elif move.y == -1:
            self.direction = EntityDirections.UP

        # Compute temporary position based on next move
        new_position = move + self.position
        # Check move validity
        if new_position.x > self.game.size - 1 or \
                new_position.y > self.game.size - 1 or \
                new_position.x < 0 or new_position.y < 0:
            raise InvalidAction("You cannot move out of bounds.")

        tile = self.game.board[new_position.x][new_position.y]
        if not tile.movement_allowed:
            raise InvalidAction("You cannot move on this tile.")

        # Reset the movement timer
        self.movement_timer = self.movement_cooldown
        self.position = new_position

        for entity in self.game.get_entities_at(self.position):
            if entity != self:
                self.collide(entity)
                entity.collide(self)

        self.moving = True
        return move

    def collide(self, other):
        pass

    def get_interpolated_position(self):
        progress = self.movement_timer / self.movement_cooldown

        position = self.position + (-1 * direction_to_point(self.direction)) * progress
        return position

    def to_json(self):
        state = {
            "uid": self.uid,
            "position": self.get_interpolated_position().to_json(),
            "direction": self.direction.value,
            "moving": self.moving,
        }
        return state

    def post_movement_action(self):
        pass

    def prepare_movement(self):
        pass
