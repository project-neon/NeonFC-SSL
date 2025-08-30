import pytest
import math
from neonfc_ssl.control_layer.path_planning.rrt import RRT, RRTStar
from neonfc_ssl.control_layer.path_planning.rrt import Node


@pytest.fixture
def setup_rrt():
    start = (1, 1)
    goal = (8, 5)
    obstacles = [Node(4, 4), Node(5, 5)]
    return RRT(start, goal, obstacles, map_area=(9, 6), step_size=0.1)

@pytest.mark.unit
def test_get_random_node(setup_rrt):
    rrt = setup_rrt
    node = rrt.get_random_node()

    assert 0 <= node.x <= 9
    assert 0 <= node.y <= 6

@pytest.mark.unit
def test_get_nearest_node(setup_rrt):
    rrt = setup_rrt
    rrt.node_list = [Node(1, 1), Node(2, 2), Node(3, 3)]

    test_node = Node(2.1, 2.1)
    nearest = rrt.get_nearest_node(test_node)

    assert nearest.x == 2
    assert nearest.y == 2

@pytest.mark.unit
def test_steer(setup_rrt):
    rrt = setup_rrt
    start = Node(1, 1)
    end = Node(3, 3)

    new_node = rrt.steer(start, end)

    expected_theta = math.atan2(2, 2)
    expected_x = 1 + rrt.step_size * math.cos(expected_theta)
    expected_y = 1 + rrt.step_size * math.sin(expected_theta)

    assert abs(new_node.x - expected_x) < 1e-9
    assert abs(new_node.y - expected_y) < 1e-9
    assert new_node.parent == start
    assert new_node.cost == start.cost + rrt.step_size

@pytest.mark.unit
def test_is_collision_free(setup_rrt):
    rrt = setup_rrt
    start = Node(1, 2)
    end = Node(3, 4)

    assert rrt.is_collision_free(start, end)

    obstacle = Node(2, 3)
    rrt_with_collision = RRT(
        start=(1, 2),
        goal=(3, 4),
        obstacles=[obstacle],
        map_area=(9, 6),
        collision_margin=0.18
    )

    assert not rrt_with_collision.is_collision_free(Node(1, 2), Node(3, 4))

@pytest.mark.unit
def test_generate_final_path(setup_rrt):
    rrt = setup_rrt
    rrt.goal = Node(3, 3)
    rrt.goal.parent = Node(2, 2)
    rrt.goal.parent.parent = Node(1, 1)

    path = rrt.generate_final_path()

    assert path == [[1, 1], [2, 2], [3, 3]]
    assert rrt.path == [[3, 3], [2, 2], [1, 1]]

@pytest.mark.unit
def test_plan_success(setup_rrt):
    rrt = setup_rrt
    # Use simple scenario that should always work
    rrt.obstacles = []
    path = rrt.plan()

    assert len(path) > 0
    assert path[0] == [1, 1]
    assert path[-1] == [8, 5]

@pytest.mark.unit
def test_plan_failure(setup_rrt):
    rrt = setup_rrt
    # Create impossible scenario
    rrt.obstacles = [Node(x, y) for x in range(9) for y in range(6)]
    path = rrt.plan()

    assert len(path) == 0

@pytest.mark.unit
def test_collision_margin(setup_rrt):
    rrt = setup_rrt
    rrt.collision_margin = 1.0  # Large margin

    start = Node(1, 1)
    end = Node(3, 3)

    # Should detect collision with large margin
    assert not rrt.is_collision_free(start, end)


@pytest.fixture
def setup_rrt_star():
    start = (1, 1)
    goal = (8, 5)
    obstacles = [Node(4, 4), Node(5, 5)]
    return RRTStar(start, goal, obstacles, map_area=(9, 6), step_size=0.1)

@pytest.mark.unit
def test_get_random_node(setup_rrt_star):
    rrt_star = setup_rrt_star
    node = rrt_star.get_random_node()

    assert 0 <= node.x <= 9
    assert 0 <= node.y <= 6

@pytest.mark.unit
def test_get_nearest_node(setup_rrt_star):
    rrt_star = setup_rrt_star
    rrt_star.node_list = [Node(1, 1), Node(2, 2), Node(3, 3)]

    test_node = Node(2.1, 2.1)
    nearest = rrt_star.get_nearest_node(test_node)

    assert nearest.x == 2
    assert nearest.y == 2

@pytest.mark.unit
def test_steer(setup_rrt_star):
    rrt_star = setup_rrt_star
    start = Node(1, 1)
    end = Node(3, 3)

    new_node = rrt_star.steer(start, end)

    expected_theta = math.atan2(2, 2)
    expected_x = 1 + rrt_star.step_size * math.cos(expected_theta)
    expected_y = 1 + rrt_star.step_size * math.sin(expected_theta)

    assert abs(new_node.x - expected_x) < 1e-9
    assert abs(new_node.y - expected_y) < 1e-9
    assert new_node.parent == start
    assert new_node.cost == start.cost + rrt_star.step_size

@pytest.mark.unit
def test_is_collision_free(setup_rrt_star):
    rrt_star = setup_rrt_star
    start = Node(1, 2)
    end = Node(3, 4)

    assert rrt_star.is_collision_free(start, end)

    obstacle = Node(2, 3)
    rrt_star_with_collision = RRTStar(
        start=(1, 2),
        goal=(3, 4),
        obstacles=[obstacle],
        map_area=(9, 6),
        collision_margin=0.18
    )

    assert not rrt_star_with_collision.is_collision_free(Node(1, 2), Node(3, 4))

@pytest.mark.unit
def test_generate_final_path(setup_rrt_star):
    rrt_star = setup_rrt_star
    rrt_star.goal = Node(3, 3)
    rrt_star.goal.parent = Node(2, 2)
    rrt_star.goal.parent.parent = Node(1, 1)

    path = rrt_star.generate_final_path()

    assert path == [[1, 1], [2, 2], [3, 3]]
    assert rrt_star.path == [[3, 3], [2, 2], [1, 1]]

@pytest.mark.unit
def test_plan_success(setup_rrt_star):
    rrt_star = setup_rrt_star
    # Use simple scenario that should always work
    rrt_star.obstacles = []
    path = rrt_star.plan()

    assert len(path) > 0
    assert path[0] == [1, 1]
    assert path[-1] == [8, 5]

@pytest.mark.unit
def test_plan_failure(setup_rrt_star):
    rrt_star = setup_rrt_star
    # Create impossible scenario
    rrt_star.obstacles = [Node(x, y) for x in range(9) for y in range(6)]
    path = rrt_star.plan()

    assert len(path) == 0

@pytest.mark.unit
def test_collision_margin(setup_rrt_star):
    rrt_star = setup_rrt_star
    rrt_star.collision_margin = 1.0  # Large margin

    start = Node(1, 1)
    end = Node(3, 3)

    # Should detect collision with large margin
    assert not rrt_star.is_collision_free(start, end)
