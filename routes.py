from flask import request, jsonify, render_template
from game_logic import Game

# Create a single instance of the game.
game = Game()

def init_routes(app):
    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/new_game', methods=['POST'])
    def new_game():
        game.deal_hands()
        return jsonify({"message": "New game started.", "phase": game.phase})

    @app.route('/show_state', methods=['GET'])
    def show_state():
        state = game.get_state()
        return jsonify(state)

    @app.route('/bid', methods=['POST'])
    def bid():
        data = request.get_json()
        bid_value = data.get('bid_value')
        result = game.process_bid("player", bid_value)
        response = {
            "message": result,
            "next_phase": game.phase
        }
        return jsonify(response)

    @app.route('/play_card', methods=['POST'])
    def play_card():
        data = request.get_json()
        card_name = data.get('card_name')
        result = game.play_card("player", card_name)
        return jsonify(result)

    @app.route('/discard', methods=['POST'])
    def discard():
        data = request.get_json()
        cards_to_discard = data.get('cards', [])
        result = game.discard_cards("player", cards_to_discard)
        return jsonify(result)
