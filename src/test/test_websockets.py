"""
    Test excersing the backend API

    YOUR IP SHOULD BE WHITELISTED DB_SERVER ON THE AZURE PROJECT

"""
from unittest.mock import patch, MagicMock
import json
import tempfile
import werkzeug
import os

current_directory = os.path.dirname(os.path.abspath(__file__))
src_directory = os.path.dirname(current_directory)
root_directory = os.path.dirname(src_directory)
HARAMBE_PATH = os.path.join(root_directory, 'data/harambe.png')

mock_classifier = MagicMock()
mock_classifier.predict_image_by_post = MagicMock(
    return_value=({"angel": 1}, "angel"))


def test_join_game_same_pair_id(test_clients):
    """
        tests whether a player is able to join game
    """
    _, ws_client1, ws_client2 = test_clients

    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "joinGame"
    assert r1[0]["args"][0]['player_nr'] == 'player_1'
    assert not r1[1]["args"][0]['ready']
    r2 = ws_client2.get_received()
    assert r2 == []

    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "joinGame"
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "joinGame"
    assert r2[0]["args"][0]['player_nr'] == 'player_2'
    assert r2[1]["args"][0]['ready']


def test_join_game_diff_pair_id(four_test_clients):
    """
        tests wether a player is able to join game
    """
    _, ws_client1_1, ws_client1_2, ws_client2_1, ws_client2_2 = four_test_clients
    data_1 = '{"pair_id": "pair_id_1","difficulty_id": 1}'
    data_2 = '{"pair_id": "pair_id_2","difficulty_id": 1}'

    # the first player is added to both games
    ws_client1_1.emit("joinGame", data_1)

    r11 = ws_client1_1.get_received()
    assert r11[0]["name"] == "joinGame"
    assert r11[0]["args"][0]['player_nr'] == 'player_1'
    assert not r11[1]["args"][0]['ready']
    r21 = ws_client2_1.get_received()
    assert r21 == []

    ws_client2_1.emit("joinGame", data_2)

    r21 = ws_client2_1.get_received()
    assert r21[0]["name"] == "joinGame"
    assert r21[0]["args"][0]['player_nr'] == 'player_1'
    assert not r21[1]["args"][0]['ready']
    r11 = ws_client1_1.get_received()
    assert r11 == []

    # a second player is added to both games
    ws_client1_2.emit("joinGame", data_1)

    r12 = ws_client1_2.get_received()
    assert r12[0]["name"] == "joinGame"
    assert r12[0]["args"][0]['player_nr'] == 'player_2'
    assert r12[1]["args"][0]['ready']
    r11 = ws_client1_1.get_received()
    assert r11[0]["name"] == "joinGame"
    r21 = ws_client2_1.get_received()
    assert r21 == []

    ws_client2_2.emit("joinGame", data_2)

    r2 = ws_client2_2.get_received()
    assert r2[0]["name"] == "joinGame"
    assert r2[0]["args"][0]['player_nr'] == 'player_2'
    assert r2[1]["args"][0]['ready']
    r11 = ws_client1_1.get_received()
    assert r11 == []
    r21 = ws_client2_1.get_received()
    assert r21[0]["name"] == "joinGame"


def test_join_game_different_difficulty(test_clients):
    """
    tests whether a player with a different difficulty is able to join game
    """
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "pair_id_1A","difficulty_id": 1}')

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "joinGame"
    assert r1[0]["args"][0]['player_nr'] == 'player_1'
    assert not r1[1]["args"][0]['ready']
    r2 = ws_client2.get_received()
    assert r2 == []

    ws_client2.emit("joinGame", '{"pair_id": "pair_id_2A","difficulty_id": 2}')

    assert r1[0]["name"] == "joinGame"
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "joinGame"
    assert r2[0]["args"][0]["game_id"] != r1[0]["args"][0]["game_id"]
    assert not r2[1]["args"][0]['ready']


@patch('singleplayer.api.classifier', mock_classifier)
def test_classification_only_client1_correct(test_clients):
    time_left = 1
    correct_label = "angel"
    wrong_label = "bicycle"
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]
    data = {"game_id": game_id, "time_left": time_left, "lang": "NO"}
    ws_client1.emit(
        "classify",
        data,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)
    ws_client2.emit(
        "classify",
        data,
        _get_image_as_stream(HARAMBE_PATH),
        wrong_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "prediction"
    assert type(r1[0]["args"][0]["certainty"]) is dict
    assert r1[0]["args"][0]["correctLabel"] == "engel"
    assert r1[0]["args"][0]["guess"] == "engel"
    assert r1[0]["args"][0]["hasWon"] is True
    assert len(r1) == 1

    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "prediction"
    assert type(r2[0]["args"][0]["certainty"]) is dict
    assert r2[0]["args"][0]["correctLabel"] == "sykkel"
    assert r2[0]["args"][0]["guess"] == "engel"
    assert r2[0]["args"][0]["hasWon"] is False
    assert len(r2) == 1


@patch('singleplayer.api.classifier', mock_classifier)
def test_game_in_different_languages(test_clients):
    correct_label = "angel"
    wrong_label = "bicycle"

    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]
    data_1 = {"game_id": game_id, "time_left": 1, "lang": "NO"}
    data_2 = {"game_id": game_id, "time_left": 1, "lang": "ENG"}

    ws_client1.emit(
        "classify",
        data_1,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)
    ws_client2.emit(
        "classify",
        data_2,
        _get_image_as_stream(HARAMBE_PATH),
        wrong_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "prediction"
    assert type(r1[0]["args"][0]["certainty"]) is dict
    assert r1[0]["args"][0]["correctLabel"] == "engel"
    assert r1[0]["args"][0]["guess"] == "engel"
    assert r1[0]["args"][0]["hasWon"] is True
    assert len(r1) == 1

    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "prediction"
    assert type(r2[0]["args"][0]["certainty"]) is dict
    assert r2[0]["args"][0]["correctLabel"] == wrong_label
    assert r2[0]["args"][0]["guess"] == correct_label
    assert r2[0]["args"][0]["hasWon"] is False
    assert len(r2) == 1


@patch('singleplayer.api.classifier', mock_classifier)
def test_classification_both_correct(test_clients):
    time_left = 1
    correct_label = "angel"
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]
    data = {"game_id": game_id, "time_left": time_left, "lang": "NO"}

    ws_client1.emit(
        "classify",
        data,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "prediction"
    assert type(r1[0]["args"][0]["certainty"]) is dict
    assert r1[0]["args"][0]["correctLabel"] == "engel"
    assert r1[0]["args"][0]["guess"] == "engel"
    assert r1[0]["args"][0]["hasWon"] is True
    assert len(r1) == 1
    ws_client2.get_received() == []

    ws_client2.emit(
        "classify",
        data,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "roundOver"
    assert r1[0]["args"][0]["round_over"] is True
    assert len(r1) == 1
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "prediction"
    assert type(r2[0]["args"][0]["certainty"]) is dict
    assert r2[0]["args"][0]["correctLabel"] == "engel"
    assert r2[0]["args"][0]["guess"] == "engel"
    assert r2[0]["args"][0]["hasWon"] is True
    assert r2[1]["name"] == "roundOver"
    assert r2[1]["args"][0]["round_over"] is True
    assert len(r2) == 2


@patch('singleplayer.api.classifier', mock_classifier)
def test_classification_client1_timeout_and_client2_correct(test_clients):
    time_out = 0
    time_left = 1
    correct_label = "angel"
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]

    data1 = {"game_id": game_id, "time_left": time_out, "lang": "NO"}
    ws_client1.emit(
        "classify",
        data1,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    assert ws_client1.get_received() == []
    assert ws_client2.get_received() == []

    data2 = {"game_id": game_id, "time_left": time_left, "lang": "NO"}
    ws_client2.emit(
        "classify",
        data2,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "roundOver"
    assert r1[0]["args"][0]["round_over"] is True
    assert len(r1) == 1
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "prediction"
    assert type(r2[0]["args"][0]["certainty"]) is dict
    assert r2[0]["args"][0]["correctLabel"] == "engel"
    assert r2[0]["args"][0]["guess"] == "engel"
    assert r2[0]["args"][0]["hasWon"] is True
    assert r2[1]["name"] == "roundOver"
    assert r2[1]["args"][0]["round_over"] is True
    assert len(r2) == 2


@patch('singleplayer.api.classifier', mock_classifier)
def test_classification_client1_correct_and_client2_timeout(test_clients):
    time_out = 0
    time_left = 1
    correct_label = "angel"
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]

    data1 = {"game_id": game_id, "time_left": time_left, "lang": "NO"}
    ws_client1.emit(
        "classify",
        data1,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "prediction"
    assert type(r1[0]["args"][0]["certainty"]) is dict
    assert r1[0]["args"][0]["correctLabel"] == "engel"
    assert r1[0]["args"][0]["guess"] == "engel"
    assert r1[0]["args"][0]["hasWon"] is True
    assert len(r1) == 1
    assert ws_client2.get_received() == []

    data2 = {"game_id": game_id, "time_left": time_out, "lang": "NO"}
    ws_client2.emit(
        "classify",
        data2,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "roundOver"
    assert r1[0]["args"][0]["round_over"] is True
    assert len(r1) == 1
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "roundOver"
    assert r2[0]["args"][0]["round_over"] is True
    assert len(r2) == 1


@patch('singleplayer.api.classifier', mock_classifier)
def test_classification_both_timeout(test_clients):
    time_out = 0
    correct_label = "angel"
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"pair_id": "classify","difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    args = r1[0]["args"][0]
    game_id = args["game_id"]

    data1 = {"game_id": game_id, "time_left": time_out, "lang": "NO"}
    ws_client1.emit(
        "classify",
        data1,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    assert ws_client1.get_received() == []
    assert ws_client2.get_received() == []

    data2 = {"game_id": game_id, "time_left": time_out, "lang": "NO"}
    ws_client2.emit(
        "classify",
        data2,
        _get_image_as_stream(HARAMBE_PATH),
        correct_label)

    r1 = ws_client1.get_received()
    assert r1[0]["name"] == "roundOver"
    assert r1[0]["args"][0]["round_over"] is True
    assert len(r1) == 1
    r2 = ws_client2.get_received()
    assert r2[0]["name"] == "roundOver"
    assert r2[0]["args"][0]["round_over"] is True
    assert len(r2) == 1


def test_players_not_with_same_playerid(test_clients):
    """TODO: implement me"""
    _, ws_client1, ws_client2 = test_clients

    ws_client1.emit("joinGame", '{"difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"difficulty_id": 1}')

    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    assert r1[0]["args"][0]["player_id"] != r2[0]["args"][0]["player_id"]
    assert r1[0]["args"][0]["game_id"] == r2[0]["args"][0]["game_id"]


def test_players_can_keep_guessing(test_clients):
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    game_id = r1[0]["args"][0]["game_id"]

    for i in range(3):
        data = {"game_id": game_id, "time_left": 1, "lang": "NO"}

        ws_client1.emit("classify", data, _get_image_as_stream(HARAMBE_PATH))
        ws_client2.emit("classify", data, _get_image_as_stream(HARAMBE_PATH))

        r1 = ws_client1.get_received()
        r2 = ws_client2.get_received()
        assert not r1[0]["args"][0]["hasWon"]
        assert not r2[0]["args"][0]["hasWon"]


def test_end_game(test_clients):
    _, ws_client1, ws_client2 = test_clients
    ws_client1.emit("joinGame", '{"difficulty_id": 1}')
    ws_client2.emit("joinGame", '{"difficulty_id": 1}')
    r1 = ws_client1.get_received()
    r2 = ws_client2.get_received()
    player_1_id = r1[0]["args"][0]["player_id"]
    game_id = r1[0]["args"][0]["game_id"]
    data = json.dumps(
        {"game_id": game_id, "player_id": player_1_id, "score": 100})

    ws_client1.emit('endGame', data)

    assert ws_client1.get_received() == []
    r2 = ws_client2.get_received()
    r2_json = json.loads(r2[0]["args"][0])
    assert r2_json['score'] == 100
    assert r2_json['playerId'] == player_1_id


def _get_image_as_stream(file_path):
    image_file = open(file_path, "rb")
    data_stream = image_file.read()

    tmp = tempfile.SpooledTemporaryFile()
    tmp.write(data_stream)
    tmp.seek(0)
    # Create file storage object containing the image
    content_type = "image/png"
    image = werkzeug.datastructures.FileStorage(
        stream=tmp, filename=HARAMBE_PATH, content_type=content_type
    )
    return image.stream.read()
