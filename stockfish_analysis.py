import chess
import chess.engine

def evaluate_moves(fen, stockfish_path="stockfish", analysis_time=0.2):
    """
    For the given FEN, evaluate all legal moves using Stockfish.
    Returns a list of (move_uci, score_cp, san) sorted best to worst.
    """
    board = chess.Board(fen)
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        move_scores = []
        for move in board.legal_moves:
            san = board.san(move)
            board.push(move)
            info = engine.analyse(board, chess.engine.Limit(time=analysis_time))
            # Use centipawn score (score relative to the side to move)
            score = info["score"].white().score(mate_score=100000)
            move_scores.append((move.uci(), score, san))
            board.pop()
        # Sort: higher score is better for the side to move
        move_scores.sort(key=lambda x: x[1], reverse=(board.turn == chess.WHITE))
        return move_scores

def get_principal_variations(fen, stockfish_path="stockfish", depth=5, multipv=5, analysis_time=0.5):
    """
    For the given FEN, get the top principal variations (lines) up to the given depth.
    Returns a list of dicts: { 'pv': [move1, move2, ...], 'score': cp }
    """
    board = chess.Board(fen)
    with chess.engine.SimpleEngine.popen_uci(stockfish_path) as engine:
        infos = engine.analyse(
            board,
            chess.engine.Limit(depth=depth, time=analysis_time),
            multipv=multipv
        )
        lines = []
        for info in infos:
            # To get correct SAN, push moves in order on a copy of the board
            pv_moves = []
            pv_board = board.copy()
            for m in info["pv"]:
                san = pv_board.san(m)
                pv_moves.append(san)
                pv_board.push(m)
            score = info["score"].white().score(mate_score=100000)
            lines.append({"pv": pv_moves, "score": score})
        # Sort by score
        lines.sort(key=lambda x: x["score"], reverse=(board.turn == chess.WHITE))
        return lines
