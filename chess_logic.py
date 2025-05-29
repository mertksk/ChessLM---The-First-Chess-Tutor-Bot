# chess_logic.py
import copy

# --- Helper Functions ---
def to_coords(notation):
    if not isinstance(notation, str) or len(notation) != 2: return None
    col_char, row_char = notation[0], notation[1]
    if not ('a' <= col_char <= 'h' and '1' <= row_char <= '8'): return None
    col = ord(col_char) - ord('a')
    row = 8 - int(row_char)
    return row, col

def to_notation(coords):
    row, col = coords
    if not (0 <= row <= 7 and 0 <= col <= 7): return None
    return chr(ord('a') + col) + str(8 - row)

# --- Piece Classes (Pawn, Rook, Knight, Bishop, Queen, King) ---
class Piece:
    def __init__(self, color, symbol_char):
        self.color = color
        self.symbol_char = symbol_char
        self.symbol = symbol_char.upper() if color == 'W' else symbol_char.lower()
        self.has_moved = False

    def get_image_filename(self):
        return f"{self.color.lower()}{self.symbol_char.upper()}.png"

    def __str__(self):
        return self.symbol

    def get_possible_moves(self, r, c, board_state):
        raise NotImplementedError("Subclasses must implement this method")

    def is_valid_move(self, r, c, nr, nc, board_state):
        possible_moves = self.get_possible_moves(r, c, board_state)
        return (nr, nc) in possible_moves

class Pawn(Piece):
    def __init__(self, color):
        super().__init__(color, 'P')

    def get_possible_moves(self, r, c, board_state, en_passant_target=None):
        moves = []
        direction = -1 if self.color == 'W' else 1
        # Forward moves
        if 0 <= r + direction <= 7 and board_state[r + direction][c] is None:
            moves.append((r + direction, c))
            # Two squares initial move
            if not self.has_moved and 0 <= r + 2 * direction <= 7 and \
               board_state[r + 2 * direction][c] is None and \
               board_state[r + direction][c] is None: # Ensure path is clear
                moves.append((r + 2 * direction, c))
        # Captures
        for dc in [-1, 1]:
            nr, nc = r + direction, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                target_piece = board_state[nr][nc]
                if target_piece and target_piece.color != self.color:
                    moves.append((nr, nc))
                # En passant
                if en_passant_target and (nr, nc) == en_passant_target:
                    moves.append((nr, nc))
        return moves

class Rook(Piece):
    def __init__(self, color):
        super().__init__(color, 'R')
    def get_possible_moves(self, r, c, board_state):
        moves = []
        directions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr <= 7 and 0 <= nc <= 7): break
                target_piece = board_state[nr][nc]
                if target_piece is None: moves.append((nr, nc))
                elif target_piece.color != self.color:
                    moves.append((nr, nc)); break
                else: break
        return moves

class Knight(Piece):
    def __init__(self, color):
        super().__init__(color, 'N')
    def get_possible_moves(self, r, c, board_state):
        moves = []
        knight_moves = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]
        for dr, dc in knight_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                target_piece = board_state[nr][nc]
                if target_piece is None or target_piece.color != self.color:
                    moves.append((nr, nc))
        return moves

class Bishop(Piece):
    def __init__(self, color):
        super().__init__(color, 'B')
    def get_possible_moves(self, r, c, board_state):
        moves = []
        directions = [(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in directions:
            for i in range(1, 8):
                nr, nc = r + dr * i, c + dc * i
                if not (0 <= nr <= 7 and 0 <= nc <= 7): break
                target_piece = board_state[nr][nc]
                if target_piece is None: moves.append((nr, nc))
                elif target_piece.color != self.color:
                    moves.append((nr, nc)); break
                else: break
        return moves

class Queen(Piece):
    def __init__(self, color):
        super().__init__(color, 'Q')
    def get_possible_moves(self, r, c, board_state):
        rook_moves = Rook(self.color).get_possible_moves(r, c, board_state)
        bishop_moves = Bishop(self.color).get_possible_moves(r, c, board_state)
        return rook_moves + bishop_moves

class King(Piece):
    def __init__(self, color):
        super().__init__(color, 'K')
    def get_possible_moves(self, r, c, board_state, game_context=None): # game_context for castling
        moves = []
        king_moves = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, dc in king_moves:
            nr, nc = r + dr, c + dc
            if 0 <= nr <= 7 and 0 <= nc <= 7:
                target_piece = board_state[nr][nc]
                if target_piece is None or target_piece.color != self.color:
                    moves.append((nr, nc))
        # Castling moves
        if game_context and not self.has_moved: # Check if game_context is provided
            if game_context.can_castle(self.color, 'K', board_state, check_intermediate_squares_attack=False): # Initial check
                moves.append((r, c + 2))
            if game_context.can_castle(self.color, 'Q', board_state, check_intermediate_squares_attack=False): # Initial check
                moves.append((r, c - 2))
        return moves

# --- Board Class ---
class Board:
    def __init__(self):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.setup_pieces()
        self.move_history = [] # For undo, not strictly needed for FEN but good practice

    def setup_pieces(self):
        # Pawns
        for i in range(8): self.board[1][i] = Pawn('B'); self.board[6][i] = Pawn('W')
        # Rooks, Knights, Bishops, Queens, Kings
        back_rank_pieces = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for i, piece_class in enumerate(back_rank_pieces):
            self.board[0][i] = piece_class('B')
            self.board[7][i] = piece_class('W')

    def get_piece(self, r, c):
        if 0 <= r <= 7 and 0 <= c <= 7: return self.board[r][c]
        return None

    def make_move(self, from_sq, to_sq, promotion_choice_char=None):
        r1, c1 = from_sq; r2, c2 = to_sq
        piece = self.board[r1][c1]
        if not piece: return None, False, False # captured_piece, is_castling, is_ep

        captured_piece = self.board[r2][c2]
        is_pawn_move = isinstance(piece, Pawn)
        is_capture = captured_piece is not None
        is_castling_move = False
        is_en_passant_capture = False

        # Special King move: Castling
        if isinstance(piece, King) and abs(c2 - c1) == 2:
            is_castling_move = True
            rook_c1_orig = 0 if c2 < c1 else 7
            rook_c2_new = c1 + (1 if c2 > c1 else -1) # Rook's new column
            rook = self.board[r1][rook_c1_orig]
            self.board[r1][rook_c2_new] = rook
            self.board[r1][rook_c1_orig] = None
            if rook: rook.has_moved = True
        # Special Pawn move: En Passant
        elif isinstance(piece, Pawn) and abs(c2 - c1) == 1 and self.board[r2][c2] is None:
            # This implies en passant if it's a diagonal pawn move to an empty square
            # The actual en_passant_target check is done in ChessGame.process_move
            # Here, we identify the captured pawn for removal.
            captured_pawn_r, captured_pawn_c = r1, c2 # Opponent pawn is on same rank as moving pawn, target column
            captured_piece = self.board[captured_pawn_r][captured_pawn_c] # This will be the captured pawn
            self.board[captured_pawn_r][captured_pawn_c] = None
            is_en_passant_capture = True
            is_capture = True # En passant is a capture

        # Standard move
        self.board[r2][c2] = piece
        self.board[r1][c1] = None

        # Pawn Promotion
        if isinstance(piece, Pawn):
            if (piece.color == 'W' and r2 == 0) or (piece.color == 'B' and r2 == 7):
                promo_map = {'Q': Queen, 'R': Rook, 'B': Bishop, 'N': Knight}
                new_piece_class = promo_map.get(str(promotion_choice_char).upper(), Queen) # Default to Queen
                promoted_piece = new_piece_class(piece.color)
                promoted_piece.has_moved = True # Promoted piece counts as moved
                self.board[r2][c2] = promoted_piece
                piece = promoted_piece # update piece reference

        # Record move for history (optional, but good)
        self.move_history.append({
            'piece': piece, 'from': (r1,c1), 'to': (r2,c2),
            'captured': captured_piece, 'was_castling': is_castling_move,
            'was_ep': is_en_passant_capture, 'promoted_to': piece.symbol_char if isinstance(piece, Pawn) and promotion_choice_char else None,
            'piece_had_moved': piece.has_moved # before this move (for undo)
        })

        piece.has_moved = True
        return captured_piece, is_pawn_move, is_capture or is_en_passant_capture


# --- Game Logic (ChessGame class) ---
class ChessGame:
    def __init__(self):
        self.board_obj = Board()
        self.current_player = 'W'
        self.castling_rights = {'W': {'K': True, 'Q': True}, 'B': {'K': True, 'Q': True}}
        self.en_passant_target = None # (r, c) of the square *behind* the pawn that moved two steps
        self.halfmove_clock = 0 # For 50-move rule
        self.fullmove_number = 1 # Starts at 1, increments after Black's move
        self.status_message = "White's turn."
        self.game_over_message = None

    def switch_player(self):
        if self.current_player == 'B':
            self.fullmove_number += 1
        self.current_player = 'B' if self.current_player == 'W' else 'W'

    def find_king(self, color, board_state=None):
        b = board_state if board_state is not None else self.board_obj.board
        for r in range(8):
            for c in range(8):
                piece = b[r][c]
                if isinstance(piece, King) and piece.color == color:
                    return (r, c)
        return None

    def is_square_attacked(self, r_target, c_target, attacker_color, board_state=None):
        b = board_state if board_state is not None else self.board_obj.board
        for r_idx in range(8):
            for c_idx in range(8):
                piece = b[r_idx][c_idx]
                if piece and piece.color == attacker_color:
                    # For pawn attacks, their get_possible_moves includes non-capturing forward moves.
                    # We need to check only their capture capabilities.
                    if isinstance(piece, Pawn):
                        direction = -1 if piece.color == 'W' else 1
                        if r_idx + direction == r_target:
                            if c_idx + 1 == c_target or c_idx - 1 == c_target:
                                return True
                    # For other pieces, use their standard move generation logic
                    # but we must be careful: is_valid_move checks against full possible_moves.
                    # We need a version of get_possible_moves that doesn't consider game_context for king (to avoid recursion in check checks for castling)
                    # and that strictly returns squares they *can* move to (attack or empty).
                    else:
                        # Simulate piece.is_valid_move without the king's castling part if it causes issues
                        # A simpler way: generate raw attack moves
                        raw_moves = []
                        if isinstance(piece, King): # King attacks adjacent squares
                            king_moves = [(0,1),(0,-1),(1,0),(-1,0),(1,1),(1,-1),(-1,1),(-1,-1)]
                            for dr_k, dc_k in king_moves:
                                nr_k, nc_k = r_idx + dr_k, c_idx + dc_k
                                if nr_k == r_target and nc_k == c_target: raw_moves.append((nr_k, nc_k))
                        elif isinstance(piece, Pawn): # Already handled above
                            pass
                        else: # For Rook, Knight, Bishop, Queen
                             raw_moves = piece.get_possible_moves(r_idx, c_idx, b)

                        if (r_target, c_target) in raw_moves:
                            return True
        return False

    def is_in_check(self, color, board_state=None):
        b = board_state if board_state is not None else self.board_obj.board
        king_pos = self.find_king(color, b)
        if not king_pos:
            # This case should ideally not happen in a valid game state.
            # Could occur if a FEN without a king is loaded, or during faulty simulation.
            # print(f"Warning: King of color {color} not found in is_in_check.")
            return True # Consider it a critical error, perhaps king is captured (though logic should prevent this)
        opponent_color = 'B' if color == 'W' else 'W'
        return self.is_square_attacked(king_pos[0], king_pos[1], opponent_color, b)

    def get_all_possible_moves_for_player(self, color, board_state=None, check_castling_rights_in_king=True):
        b = board_state if board_state is not None else self.board_obj.board
        current_en_passant_target = self.en_passant_target if board_state is None else None # Only use game's EP target for current board

        moves = []
        for r in range(8):
            for c in range(8):
                piece = b[r][c]
                if piece and piece.color == color:
                    piece_moves = []
                    if isinstance(piece, Pawn):
                        piece_moves = piece.get_possible_moves(r, c, b, current_en_passant_target)
                    elif isinstance(piece, King):
                        # Pass self (ChessGame instance) as game_context if checking current board
                        game_ctx = self if board_state is None and check_castling_rights_in_king else None
                        piece_moves = piece.get_possible_moves(r, c, b, game_context=game_ctx)
                    else:
                        piece_moves = piece.get_possible_moves(r, c, b)

                    for move in piece_moves:
                        moves.append(((r,c), move))
        return moves

    def get_all_legal_moves_for_player(self, color):
        legal_moves = []
        # Get raw possible moves, including special moves like castling if conditions are met initially
        possible_raw_moves = self.get_all_possible_moves_for_player(color, check_castling_rights_in_king=True)

        for from_sq, to_sq in possible_raw_moves:
            # Simulate the move on a temporary board
            # Create a deep copy of the board state for simulation
            # Using copy.deepcopy on the board_obj.board (list of lists of Pieces)
            # is safer than trying to manage a temporary Board object's full state (like move history).

            original_board_pieces = [[self.board_obj.board[r][c] for c in range(8)] for r in range(8)]
            sim_board_state = copy.deepcopy(original_board_pieces)

            piece_to_move_sim = sim_board_state[from_sq[0]][from_sq[1]]
            if not piece_to_move_sim: continue # Should not happen

            # Handle castling simulation: king and rook move
            is_castling_attempt = False
            if isinstance(piece_to_move_sim, King) and abs(to_sq[1] - from_sq[1]) == 2:
                is_castling_attempt = True
                # Check if castling is actually valid through non-attacked squares
                # The can_castle method needs to be called with check_intermediate_squares_attack=True
                side = 'K' if to_sq[1] > from_sq[1] else 'Q'
                if not self.can_castle(color, side, self.board_obj.board, check_intermediate_squares_attack=True):
                    continue # This castling path is not safe, so it's not a legal move.

                # Simulate rook move for castling
                rook_c1_orig = 0 if to_sq[1] < from_sq[1] else 7
                rook_c2_new = from_sq[1] + (1 if to_sq[1] > from_sq[1] else -1)
                sim_rook = sim_board_state[from_sq[0]][rook_c1_orig]
                sim_board_state[from_sq[0]][rook_c2_new] = sim_rook
                sim_board_state[from_sq[0]][rook_c1_orig] = None


            # Handle en passant capture simulation
            if isinstance(piece_to_move_sim, Pawn) and \
               to_sq == self.en_passant_target and \
               abs(to_sq[1] - from_sq[1]) == 1 and \
               sim_board_state[to_sq[0]][to_sq[1]] is None: # Target square must be empty for EP
                ep_capture_r = from_sq[0] # Pawn captured is on the same rank as the moving pawn's start
                ep_capture_c = to_sq[1]   # Pawn captured is in the same column as the EP target square
                sim_board_state[ep_capture_r][ep_capture_c] = None

            # Simulate the main piece move
            sim_board_state[to_sq[0]][to_sq[1]] = piece_to_move_sim
            sim_board_state[from_sq[0]][from_sq[1]] = None

            # Check if the king of 'color' is in check on this simulated board
            if not self.is_in_check(color, sim_board_state):
                legal_moves.append((from_sq, to_sq))
        return legal_moves


    def update_castling_rights(self, piece_moved, from_sq, captured_piece_at_to_sq_original_pos=None, to_sq_for_capture=None):
        # piece_moved is the piece object, from_sq is its original square
        color = piece_moved.color
        r, c = from_sq

        if isinstance(piece_moved, King):
            self.castling_rights[color]['K'] = False
            self.castling_rights[color]['Q'] = False
        elif isinstance(piece_moved, Rook):
            original_king_side_rook_col = 7
            original_queen_side_rook_col = 0
            original_rook_row = 7 if color == 'W' else 0

            if r == original_rook_row:
                if c == original_queen_side_rook_col:
                    self.castling_rights[color]['Q'] = False
                elif c == original_king_side_rook_col:
                    self.castling_rights[color]['K'] = False

        # If a rook is captured, update opponent's castling rights
        if captured_piece_at_to_sq_original_pos and isinstance(captured_piece_at_to_sq_original_pos, Rook):
            cap_color = captured_piece_at_to_sq_original_pos.color
            cap_r, cap_c = to_sq_for_capture # The square where the rook was captured

            cap_original_king_side_rook_col = 7
            cap_original_queen_side_rook_col = 0
            cap_original_rook_row = 7 if cap_color == 'W' else 0

            if cap_r == cap_original_rook_row:
                if cap_c == cap_original_queen_side_rook_col:
                    self.castling_rights[cap_color]['Q'] = False
                elif cap_c == cap_original_king_side_rook_col:
                    self.castling_rights[cap_color]['K'] = False


    def can_castle(self, color, side, board_state, check_intermediate_squares_attack=True):
        # board_state is self.board_obj.board typically
        if self.is_in_check(color, board_state): return False # Cannot castle out of check

        king_r = 7 if color == 'W' else 0
        king_c = 4 # Standard king column

        king = board_state[king_r][king_c]
        if not isinstance(king, King) or king.has_moved or king.color != color:
            return False # King has moved or is not the right king

        path_squares_to_check_empty = []
        squares_king_traverses_for_attack_check = [] # Squares king passes *through* or *lands on*

        if side == 'K': # Kingside
            if not self.castling_rights[color]['K']: return False
            rook_c_orig = 7
            # Squares between king and rook must be empty
            path_squares_to_check_empty = [(king_r, king_c + 1), (king_r, king_c + 2)]
            # Squares king passes over/to must not be attacked
            squares_king_traverses_for_attack_check = [(king_r, king_c + 1), (king_r, king_c + 2)]
        elif side == 'Q': # Queenside
            if not self.castling_rights[color]['Q']: return False
            rook_c_orig = 0
            # Squares between king and rook must be empty
            path_squares_to_check_empty = [(king_r, king_c - 1), (king_r, king_c - 2), (king_r, king_c - 3)]
            # Squares king passes over/to must not be attacked
            squares_king_traverses_for_attack_check = [(king_r, king_c - 1), (king_r, king_c - 2)]
        else:
            return False # Invalid side

        # Check if rook is in place and hasn't moved
        rook = board_state[king_r][rook_c_orig]
        if not isinstance(rook, Rook) or rook.has_moved or rook.color != color:
            return False

        # Check path empty
        for r_path, c_path in path_squares_to_check_empty:
            if board_state[r_path][c_path] is not None:
                return False

        # Check if squares king passes through are attacked
        if check_intermediate_squares_attack:
            opponent_color = 'B' if color == 'W' else 'W'
            # King's current square is already checked by "not self.is_in_check"
            for r_check, c_check in squares_king_traverses_for_attack_check:
                if self.is_square_attacked(r_check, c_check, opponent_color, board_state):
                    return False
        return True

    def process_move(self, from_sq, to_sq, promotion_choice_char=None):
        if self.game_over_message: return False

        r1, c1 = from_sq; r2, c2 = to_sq
        piece = self.board_obj.get_piece(r1, c1)
        self.status_message = ""

        if not piece or piece.color != self.current_player:
            self.status_message = "Invalid selection or not your turn."
            return False

        legal_moves = self.get_all_legal_moves_for_player(self.current_player)
        if (from_sq, to_sq) not in legal_moves:
            self.status_message = "Illegal move."
            if self.is_in_check(self.current_player, self.board_obj.board):
                 self.status_message += f" {self.current_player} is in check!"
            return False

        is_promotion = False
        if isinstance(piece, Pawn) and \
           ((piece.color == 'W' and r2 == 0) or (piece.color == 'B' and r2 == 7)):
            is_promotion = True
            if not promotion_choice_char:
                return "PROMOTION_NEEDED" # Signal GUI

        # --- En Passant Setup for *next* turn ---
        # Store current EP target before it's potentially changed or cleared
        # This is used by Board.make_move if the current move *is* an EP capture.
        # The new EP target is set *after* the move is made.

        # Make the move on the board
        # `make_move` needs to know about the game's en_passant_target if the move *is* an en_passant capture
        # However, the primary check for EP validity is implicit in get_all_legal_moves_for_player
        # (via Pawn.get_possible_moves using self.en_passant_target).
        # Board.make_move handles the actual removal of the EP captured pawn.

        original_piece_at_to_sq = self.board_obj.get_piece(r2, c2) # For castling rights update if rook captured

        captured_piece, is_pawn_move, is_capture = self.board_obj.make_move(from_sq, to_sq, promotion_choice_char)

        # --- Update Game State AFTER move is made ---
        # 1. Halfmove clock
        if is_pawn_move or is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        # 2. Castling rights
        # Pass the piece *that moved* and its *original square*
        self.update_castling_rights(self.board_obj.get_piece(r2,c2), from_sq, original_piece_at_to_sq, to_sq)

        # 3. En passant target for *opponent's next turn*
        self.en_passant_target = None # Clear previous EP target by default
        if isinstance(self.board_obj.get_piece(r2,c2), Pawn) and abs(r1 - r2) == 2:
            self.en_passant_target = ((r1 + r2) // 2, c1) # Square *behind* the pawn

        # 4. Switch player (this also updates fullmove_number)
        self.switch_player()

        # 5. Check game end conditions for the NEW current player
        new_player_in_check = self.is_in_check(self.current_player, self.board_obj.board)
        new_player_legal_moves = self.get_all_legal_moves_for_player(self.current_player)

        if new_player_in_check and not new_player_legal_moves:
            winner_color_map = {'W': 'Black', 'B': 'White'} # If current is W (and checkmated), Black wins.
            self.game_over_message = f"Checkmate! {winner_color_map[self.current_player]} wins."
            self.status_message = self.game_over_message
        elif not new_player_in_check and not new_player_legal_moves:
            self.game_over_message = "Stalemate! It's a draw."
            self.status_message = self.game_over_message
        elif new_player_in_check:
            self.status_message = f"{self.current_player}'s turn. Check!"
        else:
            self.status_message = f"{self.current_player}'s turn."

        # (Fifty-move rule and threefold repetition are not implemented here for brevity)

        return True


    def needs_promotion(self, from_sq, to_sq):
        piece = self.board_obj.get_piece(from_sq[0], from_sq[1])
        if not isinstance(piece, Pawn): return False
        return (piece.color == 'W' and to_sq[0] == 0) or \
               (piece.color == 'B' and to_sq[0] == 7)

    def get_board_state(self):
        return self.board_obj.board

    def reset_game(self):
        self.__init__()

    def get_fen(self):
        fen_parts = []
        # 1. Piece placement
        for r in range(8):
            empty_count = 0
            rank_str = ""
            for c in range(8):
                piece = self.board_obj.board[r][c]
                if piece:
                    if empty_count > 0:
                        rank_str += str(empty_count)
                        empty_count = 0
                    rank_str += piece.symbol
                else:
                    empty_count += 1
            if empty_count > 0:
                rank_str += str(empty_count)
            fen_parts.append(rank_str)
        piece_placement = "/".join(fen_parts)

        # 2. Active color
        active_color = 'w' if self.current_player == 'W' else 'b'

        # 3. Castling availability
        castling_str = ""
        if self.castling_rights['W']['K']: castling_str += "K"
        if self.castling_rights['W']['Q']: castling_str += "Q"
        if self.castling_rights['B']['K']: castling_str += "k"
        if self.castling_rights['B']['Q']: castling_str += "q"
        if not castling_str: castling_str = "-"

        # 4. En passant target square
        ep_target_str = "-"
        if self.en_passant_target:
            ep_target_str = to_notation(self.en_passant_target)

        # 5. Halfmove clock
        halfmove_clock_str = str(self.halfmove_clock)

        # 6. Fullmove number
        fullmove_number_str = str(self.fullmove_number)

        return f"{piece_placement} {active_color} {castling_str} {ep_target_str} {halfmove_clock_str} {fullmove_number_str}"
