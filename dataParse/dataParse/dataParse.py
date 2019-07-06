import math

from typing import List

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket


class PythonExample(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller_state = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        field = FieldInfo(self.get_field_info())
        game = Packet(packet)

        my_car = game.game_cars[self.index]
        ball = game.game_ball

        steer_correction_radians = my_car.get_steer_correction(ball.physics.location)
        text = "Lets get that ball"

        if steer_correction_radians > 0:
            self.controller_state.steer = -1.0
        else:
            self.controller_state.steer = 1.0

        if steer_correction_radians > -0.5 and steer_correction_radians < 0.5:
            self.controller_state.throttle = 1
        else:
            self.controller_state.throttle = 0.2

        self.draw_debug(packet, my_car, text)
        return self.controller_state

    def draw_debug(self, packet, car, action_display):
        self.renderer.begin_rendering()
        # print the action that the bot is taking
        self.renderer.draw_string_3d(packet.game_cars[car.index].physics.location, 2, 2, action_display, self.renderer.white())
        self.renderer.end_rendering()


class Packet:
    num_cars: int
    num_boost: int
    num_tiles: int
    num_teams: int
    game_cars: List['Car']
    game_boosts: List['GameBoosts']
    dropshot_tiles: List['TileState']
    teams: List['Team']

    def __init__(self, packet):
        self.num_cars = packet.num_cars
        self.num_boost = packet.num_boost
        self.num_tiles = packet.num_tiles
        self.num_teams = packet.num_teams
        self.game_cars = []
        self.game_boosts = []
        self.game_ball = GameBall(packet.game_ball)
        self.game_info = GameInfo(packet.game_info)
        self.dropshot_tiles = []
        self.teams = []

        for car in range(0, self.num_cars):
            self.game_cars.append(Car(packet.game_cars[car], car))

        for boost in range(0, self.num_boost):
            self.game_boosts.append(GameBoosts(packet.game_boosts[boost]))
            break

        for tile in range(0, self.num_tiles):
            self.dropshot_tiles.append(TileState(packet.tile_state[tile]))
            break

        for team in range(0, self.num_teams):
            self.teams.append(Team(packet.teams[team]))


class Car:
    index: int
    physics: 'Physics'
    score_info: 'ScoreInfo'
    is_demolished: bool
    has_wheel_contact: bool
    is_super_sonic: bool
    is_bot: bool
    jumped: bool
    double_jumped: bool
    name: str
    team: int
    boost: float

    def __init__(self, car, index):
        self.index = index
        self.physics = Physics(car.physics)
        self.score_info = ScoreInfo(car.score_info)
        self.is_demolished = car.is_demolished
        self.has_wheel_contact = car.has_wheel_contact
        self.is_super_sonic = car.is_super_sonic
        self.is_bot = car.is_bot
        self.jumped = car.jumped
        self.double_jumped = car.double_jumped
        self.name = car.name
        self.team = car.team
        self.boost = car.boost

    def get_steer_correction(self, destenation: 'Vector3') -> float:
        car_direction = self.get_facing_vector()
        car_to_ball = destenation - self.physics.location
        turn_correction = self.correction_to(car_direction, car_to_ball)
        return turn_correction

    def correction_to(self, car_direction: 'Vector3', ideal_direction: 'Vector3') -> float:
        # The in-game axes are left handed, so use -x
        current_in_radians = math.atan2(car_direction.y, -car_direction.x)
        ideal_in_radians = math.atan2(ideal_direction.y, -ideal_direction.x)

        correction = ideal_in_radians - current_in_radians

        # Make sure we go the 'short way'
        if abs(correction) > math.pi:
            if correction < 0:
                correction += 2 * math.pi
            else:
                correction -= 2 * math.pi
        return correction

    def get_facing_vector(self) -> 'Vector3':
        pitch = float(self.physics.rotation.pitch)
        yaw = float(self.physics.rotation.yaw)

        facing_x = math.cos(pitch) * math.cos(yaw)
        facing_y = math.cos(pitch) * math.sin(yaw)

        return Vector3(facing_x, facing_y)


class Physics:
    location: 'Vector3'
    rotation: 'Rotation'
    velocity: 'Vector3'
    angular_velocity: 'Vector3'

    def __init__(self, physics):
        self.location = Vector3(physics.location.x, physics.location.y, physics.location.z)
        self.rotation = Rotation(physics.rotation.pitch, physics.rotation.yaw, physics.rotation.roll)
        self.velocity = Vector3(physics.velocity.x, physics.velocity.y, physics.velocity.z)
        self.angular_velocity = Vector3(physics.angular_velocity.x, physics.angular_velocity.y, physics.angular_velocity.z)


class Vector3:
    x: float
    y: float
    z: float

    def __init__(self, x=0, y=0, z=0):
        self.x = float(x)
        self.y = float(y)
        self.z = float(z)

    def __add__(self, val):
        return Vector3(self.x + val.x, self.y + val.y, self.z + val.z)

    def __sub__(self, val):
        return Vector3(self.x - val.x, self.y - val.y, self.z - val.z)


class Rotation:
    pitch: float
    yaw: float
    roll: float

    def __init__(self, pitch=0, yaw=0, roll=0):
        self.pitch = float(pitch)
        self.yaw = float(yaw)
        self.roll = float(roll)


class ScoreInfo:
    score: int
    goals: int
    own_goals: int
    assists: int
    saves: int
    shots: int
    demolitions: int

    def __init__(self, score_info):
        self.score = score_info.score
        self.goals = score_info.goals
        self.own_goals = score_info.own_goals
        self.assists = score_info.assists
        self.saves = score_info.saves
        self.shots = score_info.shots
        self.demolitions = score_info.demolitions


class GameBoosts:
    is_active: bool
    timer: float

    def __init__(self, boost):
        self.is_active = boost.is_active
        self.timer = boost.timer


class GameBall:
    Physics: 'Physics'
    latest_touch: 'LatestTouch'
    drop_shot_info: 'DropShotInfo'

    def __init__(self, ball):
        self.physics = Physics(ball.physics)
        self.latest_touch = LatestTouch(ball.latest_touch)
        self.drop_shot_info = DropShotInfo(ball.drop_shot_info)


class LatestTouch:
    player_name: str
    time_seconds: float
    hit_location: 'Vector3'
    hit_normal: 'Vector3'
    team: int

    def __init__(self, touch):
        self.player_name = touch.player_name
        self.time_seconds = touch.time_seconds
        self.hit_location = Vector3(touch.hit_location.x, touch.hit_location.y, touch.hit_location.z)
        self.hit_normal = Vector3(touch.hit_normal.x, touch.hit_normal.y, touch.hit_normal.z)
        self.team = touch.team


class DropShotInfo:
    damage_index: int
    absorbed_force: int
    force_accum_recent: int

    def __init__(self, info):
        self.damage_index = info.damage_index
        self.absorbed_force = info.absorbed_force
        self.force_accum_recent = info.force_accum_recent


class GameInfo:
    seconds_elapsed: float
    game_time_remaining: float
    is_overtime: bool
    is_unlimited_time: bool
    is_round_active: bool
    is_kickoff_pause: bool
    is_match_ended: bool
    world_gravity_z: float
    game_speed: float

    def __init__(self, game_info):
        self.seconds_elapsed = game_info.seconds_elapsed
        self.game_time_remaining = game_info.game_time_remaining
        self.is_overtime = game_info.is_overtime
        self.is_unlimited_time = game_info.is_unlimited_time
        self.is_round_active = game_info.is_round_active
        self.is_kickoff_pause = game_info.is_kickoff_pause
        self.is_match_ended = game_info.is_match_ended
        self.world_gravity_z = game_info.world_gravity_z
        self.game_speed = game_info.game_speed


class TileState:
    def __init__(self, state):
        tile_state: int

        self.tile_state = state.tile_state  # 0 == UNKNOWN
                                            # 1 == FILLED
                                            # 2 == DAMAGED
                                            # 3 == OPEN


class Team:
    team_index: int
    score: int

    def __init__(self, team):
        self.team_index = team.team_index
        self.score = team.score


class FieldInfo:
    num_boosts: int
    num_goals: int
    boost_pads: List['BoostPad']
    goals: List['Goal']

    def __init__(self, field):
        self.num_boosts = field.num_boosts
        self.num_goals = field.num_goals
        self.boost_pads = []
        self.goals = []

        for boost in range(0, self.num_boosts):
            self.boost_pads.append(BoostPad(field.boost_pads[boost]))

        for goal in range(0, self.num_goals):
            self.goals.append(Goal(field.goals[goal]))


class BoostPad:
    location: 'Vector3'
    is_full_boost: bool

    def __init__(self, boost):
        self.location = Vector3(boost.location.x, boost.location.y, boost.location.z)
        self.is_full_boost = boost.is_full_boost


class Goal:
    team_num: int
    location: 'Vector3'
    direction: 'Vector3'

    def __init__(self, goal):
        self.team_num = goal.team_num
        self.location = Vector3(goal.location.x, goal.location.y, goal.location.z)
        self.direction = Vector3(goal.direction.x, goal.direction.y, goal.direction.z)
