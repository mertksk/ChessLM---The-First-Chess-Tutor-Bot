"""
Pygame-based GUI for playing chess using the ChessGame logic module.
Handles rendering, user interaction, and game state updates.
chess_gui.py - Enhanced version with improved chat UI
"""

import pygame
from pygame.locals import QUIT, MOUSEBUTTONDOWN, SRCALPHA, KEYDOWN, K_RETURN, K_BACKSPACE, K_TAB, K_ESCAPE  # pylint: disable=no-name-in-module
import os
import math
from chess_logic import ChessGame, Piece, Pawn, Rook, Knight, Bishop, Queen, King # Import your logic
import stockfish_analysis
import model_chat

# --- Pygame Setup ---
pygame.init()  # pylint: disable=no-member
pygame.font.init()  # pylint: disable=no-member

# --- Constants ---
SQUARE_SIZE = 80
BOARD_SIZE = 8 * SQUARE_SIZE
CHAT_PANEL_WIDTH = 400  # Increased width for better chat experience
WIDTH = BOARD_SIZE + CHAT_PANEL_WIDTH
HEIGHT = BOARD_SIZE
FPS = 30

# Enhanced Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (238, 238, 210) # Cream
DARK_SQUARE = (118, 150, 86)   # Green
HIGHLIGHT_COLOR = (186, 202, 68, 150) # Semi-transparent yellow for selection
LEGAL_MOVE_COLOR = (100, 100, 100, 100) # Semi-transparent gray for legal moves
PROMOTION_BG_COLOR = (200, 200, 200)
PROMOTION_BORDER_COLOR = (50, 50, 50)

# Enhanced Chat Colors
CHAT_BG = (248, 249, 250)  # Light gray background
CHAT_BORDER = (225, 228, 232)  # Border color
USER_BUBBLE = (0, 123, 255)  # Blue for user messages
USER_TEXT = (255, 255, 255)  # White text on blue
BOT_BUBBLE = (255, 255, 255)  # White for bot messages
BOT_TEXT = (33, 37, 41)  # Dark text on white
BOT_BUBBLE_BORDER = (222, 226, 230)  # Light border for bot messages
INPUT_BG = (255, 255, 255)  # White input background
INPUT_BORDER = (206, 212, 218)  # Input border
INPUT_FOCUS_BORDER = (0, 123, 255)  # Blue focus border
TYPING_INDICATOR = (108, 117, 125)  # Gray for typing indicator

# Screen
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Pygame Chess")
clock = pygame.time.Clock()

# Enhanced Fonts
FONT_SMALL = pygame.font.SysFont("segoeui", 14)
FONT = pygame.font.SysFont("segoeui", 16)
FONT_MEDIUM = pygame.font.SysFont("segoeui", 18)
LARGE_FONT = pygame.font.SysFont("segoeui", 36, bold=True)
CHAT_FONT = pygame.font.SysFont("segoeui", 15)
CHAT_FONT_SMALL = pygame.font.SysFont("segoeui", 13)

# --- Load Assets ---
PIECE_IMAGES = {}
PROMOTION_PIECE_IMAGES = {} # For promotion dialog

def load_assets():
    piece_chars = ['P', 'R', 'N', 'B', 'Q', 'K']
    colors = ['w', 'b']
    assets_path = "assets/pieces" # Ensure this path is correct

    if not os.path.isdir(assets_path):
        print(f"Error: Asset directory not found: {os.path.abspath(assets_path)}")
        print("Please create an 'assets/pieces' directory with piece images (e.g., wP.png, bR.png).")
        pygame.quit()  # pylint: disable=no-member
        exit()

    for color in colors:
        for char in piece_chars:
            filename = f"{color}{char.upper()}.svg"
            try:
                img = pygame.image.load(os.path.join(assets_path, filename)).convert_alpha()
                PIECE_IMAGES[f"{color}{char.upper()}"] = pygame.transform.smoothscale(img, (SQUARE_SIZE, SQUARE_SIZE))
                if char in ['Q', 'R', 'B', 'N']: # For promotion dialog
                     PROMOTION_PIECE_IMAGES[f"{color}{char.upper()}"] = pygame.transform.smoothscale(img, (SQUARE_SIZE // 2, SQUARE_SIZE // 2))
            except pygame.error as e:  # pylint: disable=no-member
                print(f"Error loading image {filename}: {e}")
                print(f"Searched in: {os.path.abspath(os.path.join(assets_path, filename))}")
                # Create a placeholder if image not found
                placeholder_surface = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), SRCALPHA)
                placeholder_surface.fill((255,0,0,100)) # Red semi-transparent
                pygame.draw.rect(placeholder_surface, BLACK, (0,0,SQUARE_SIZE,SQUARE_SIZE), 2)
                text_surf = FONT.render(f"{color}{char}", True, BLACK)
                text_rect = text_surf.get_rect(center=(SQUARE_SIZE//2, SQUARE_SIZE//2))
                placeholder_surface.blit(text_surf, text_rect)
                PIECE_IMAGES[f"{color}{char.upper()}"] = placeholder_surface
                if char in ['Q', 'R', 'B', 'N']:
                     PROMOTION_PIECE_IMAGES[f"{color}{char.upper()}"] = pygame.transform.smoothscale(placeholder_surface, (SQUARE_SIZE // 2, SQUARE_SIZE // 2))


# --- Helper Functions for GUI ---
def draw_board(surface):
    for r in range(8):
        for c in range(8):
            color = LIGHT_SQUARE if (r + c) % 2 == 0 else DARK_SQUARE
            pygame.draw.rect(surface, color, (c * SQUARE_SIZE, r * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

def draw_pieces(surface, board_state):
    for r in range(8):
        for c in range(8):
            piece = board_state[r][c]
            if piece:
                img_key = f"{piece.color.lower()}{piece.symbol_char.upper()}"
                if img_key in PIECE_IMAGES:
                    surface.blit(PIECE_IMAGES[img_key], (c * SQUARE_SIZE, r * SQUARE_SIZE))
                else: # Fallback if image key somehow wrong (shouldn't happen with new Piece init)
                    text_surf = FONT.render(str(piece), True, BLACK if piece.color == 'W' else WHITE)
                    text_rect = text_surf.get_rect(center=(c * SQUARE_SIZE + SQUARE_SIZE // 2,
                                                           r * SQUARE_SIZE + SQUARE_SIZE // 2))
                    surface.blit(text_surf, text_rect)


def draw_highlights(surface, selected_sq, legal_targets):
    if selected_sq:
        r, c = selected_sq
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), SRCALPHA)
        s.fill(HIGHLIGHT_COLOR)
        surface.blit(s, (c * SQUARE_SIZE, r * SQUARE_SIZE))

    for r_target, c_target in legal_targets:
        s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE), SRCALPHA)
        s.fill(LEGAL_MOVE_COLOR)
        pygame.draw.circle(s, (0,0,0,150), (SQUARE_SIZE // 2, SQUARE_SIZE // 2), SQUARE_SIZE // 6) # Inner dot
        surface.blit(s, (c_target * SQUARE_SIZE, r_target * SQUARE_SIZE))

def draw_info_panel(surface, game_status, game_over_msg):
    panel_rect = pygame.Rect(0, BOARD_SIZE, BOARD_SIZE, 40)
    pygame.draw.rect(surface, (220, 220, 220), panel_rect) # Light gray background
    pygame.draw.line(surface, BLACK, (0, BOARD_SIZE), (BOARD_SIZE, BOARD_SIZE), 2) # Separator

    y_offset = BOARD_SIZE + 10

    if game_over_msg:
        text_surf = LARGE_FONT.render(game_over_msg, True, (200, 0, 0) if "Checkmate" in game_over_msg else (0,0,200))
        text_rect = text_surf.get_rect(center=(BOARD_SIZE // 2, BOARD_SIZE + 20))
        surface.blit(text_surf, text_rect)

        # Reset button
        reset_button_rect = pygame.Rect(BOARD_SIZE // 2 - 75, BOARD_SIZE + 30, 150, 30)
        pygame.draw.rect(surface, (180, 180, 180), reset_button_rect)
        pygame.draw.rect(surface, BLACK, reset_button_rect, 2)
        reset_text = FONT.render("New Game", True, BLACK)
        reset_text_rect = reset_text.get_rect(center=reset_button_rect.center)
        surface.blit(reset_text, reset_text_rect)
        return reset_button_rect # Return for click detection
    else:
        text_surf = FONT.render(game_status, True, BLACK)
        text_rect = text_surf.get_rect(topleft=(10, BOARD_SIZE + 10))
        surface.blit(text_surf, text_rect)
    return None

def create_rounded_rect_surface(width, height, radius, color, border_color=None, border_width=0):
    """Create a surface with rounded corners"""
    surface = pygame.Surface((width, height), SRCALPHA)

    # Main rectangle
    main_rect = pygame.Rect(radius, radius, width - 2*radius, height - 2*radius)
    pygame.draw.rect(surface, color, main_rect)

    # Top and bottom rectangles
    pygame.draw.rect(surface, color, (radius, 0, width - 2*radius, radius))
    pygame.draw.rect(surface, color, (radius, height - radius, width - 2*radius, radius))

    # Left and right rectangles
    pygame.draw.rect(surface, color, (0, radius, radius, height - 2*radius))
    pygame.draw.rect(surface, color, (width - radius, radius, radius, height - 2*radius))

    # Corner circles
    pygame.draw.circle(surface, color, (radius, radius), radius)
    pygame.draw.circle(surface, color, (width - radius, radius), radius)
    pygame.draw.circle(surface, color, (radius, height - radius), radius)
    pygame.draw.circle(surface, color, (width - radius, height - radius), radius)

    # Border if specified
    if border_color and border_width > 0:
        # This is a simplified border - for better results, you'd need more complex logic
        pygame.draw.rect(surface, border_color, (0, 0, width, height), border_width)

    return surface

def wrap_text(text, font, max_width):
    """Wrap text to fit within max_width"""
    words = text.split(' ')
    lines = []
    current_line = ""

    for word in words:
        test_line = current_line + word + " " if current_line else word + " "
        if font.size(test_line)[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line.rstrip())
                current_line = word + " "
            else:
                # Word is too long, break it
                lines.append(word)
                current_line = ""

    if current_line:
        lines.append(current_line.rstrip())

    return lines

def draw_message_bubble(surface, message, x, y, max_width, is_user=True):
    """Draw a modern message bubble"""
    # Choose colors based on sender
    if is_user:
        bg_color = USER_BUBBLE
        text_color = USER_TEXT
        border_color = None
    else:
        bg_color = BOT_BUBBLE
        text_color = BOT_TEXT
        border_color = BOT_BUBBLE_BORDER

    # Wrap text
    lines = wrap_text(message, CHAT_FONT, max_width - 24)  # 24px for padding

    # Calculate bubble dimensions
    line_height = CHAT_FONT.get_height()
    padding = 12
    bubble_height = len(lines) * line_height + 2 * padding

    # Calculate bubble width based on longest line
    max_line_width = 0
    for line in lines:
        line_width = CHAT_FONT.size(line)[0]
        max_line_width = max(max_line_width, line_width)

    bubble_width = min(max_line_width + 2 * padding, max_width)

    # Position bubble (right-align for user, left-align for bot)
    if is_user:
        bubble_x = x + max_width - bubble_width
    else:
        bubble_x = x

    # Create bubble surface
    bubble_surface = create_rounded_rect_surface(
        bubble_width, bubble_height, 16, bg_color, border_color, 1 if border_color else 0
    )

    # Add text to bubble
    text_y = padding
    for line in lines:
        text_surf = CHAT_FONT.render(line, True, text_color)
        text_x = padding if not is_user else bubble_width - padding - CHAT_FONT.size(line)[0]
        bubble_surface.blit(text_surf, (text_x, text_y))
        text_y += line_height

    # Draw bubble on main surface
    surface.blit(bubble_surface, (bubble_x, y))

    return bubble_height + 8  # Return height including margin

def draw_enhanced_chat_panel(surface, chat_messages, input_text, is_typing=False, chat_active=False):
    """Draw an enhanced, modern chat panel"""
    panel_rect = pygame.Rect(BOARD_SIZE, 0, CHAT_PANEL_WIDTH, HEIGHT)

    # Main background
    pygame.draw.rect(surface, CHAT_BG, panel_rect)

    # Left border
    pygame.draw.line(surface, CHAT_BORDER, (BOARD_SIZE, 0), (BOARD_SIZE, HEIGHT), 2)

    # Header
    header_rect = pygame.Rect(BOARD_SIZE, 0, CHAT_PANEL_WIDTH, 50)
    header_gradient = pygame.Surface((CHAT_PANEL_WIDTH, 50))
    for i in range(50):
        color_intensity = int(248 - i * 0.2)  # Subtle gradient
        pygame.draw.line(header_gradient, (color_intensity, color_intensity + 1, color_intensity + 2),
                        (0, i), (CHAT_PANEL_WIDTH, i))
    surface.blit(header_gradient, (BOARD_SIZE, 0))

    # Header text
    header_text = FONT_MEDIUM.render("Chess Assistant", True, (52, 58, 64))
    header_rect_center = header_text.get_rect(center=(BOARD_SIZE + CHAT_PANEL_WIDTH // 2, 25))
    surface.blit(header_text, header_rect_center)

    # Header border
    pygame.draw.line(surface, CHAT_BORDER, (BOARD_SIZE, 50), (BOARD_SIZE + CHAT_PANEL_WIDTH, 50), 1)

    # Chat area
    chat_area_y = 60
    chat_area_height = HEIGHT - 120  # Space for header and input
    chat_area_width = CHAT_PANEL_WIDTH - 20

    # Display messages
    current_y = chat_area_y + 10  # Start from top with some padding
    max_bubble_width = chat_area_width - 40

    # Show recent messages (from oldest to newest, up to what fits)
    visible_messages = []
    recent_messages = chat_messages[-15:]  # Get last 15 messages

    for role, msg in recent_messages:
        message_height = len(wrap_text(msg, CHAT_FONT, max_bubble_width - 24)) * CHAT_FONT.get_height() + 32
        if current_y + message_height <= chat_area_y + chat_area_height - 10:
            visible_messages.append((role, msg, current_y))
            current_y += message_height
        else:
            # If we run out of space, show only the most recent messages
            break

    # If we have too many messages, keep only the most recent ones that fit
    if len(visible_messages) < len(recent_messages):
        # Work backwards to fit as many recent messages as possible
        visible_messages = []
        current_y = chat_area_y + chat_area_height - 10

        for role, msg in reversed(recent_messages):
            message_height = len(wrap_text(msg, CHAT_FONT, max_bubble_width - 24)) * CHAT_FONT.get_height() + 32
            if current_y - message_height >= chat_area_y + 10:
                visible_messages.append((role, msg, current_y - message_height))
                current_y -= message_height
            else:
                break

        # Reverse to get chronological order for drawing
        visible_messages.reverse()

    # Draw messages from top to bottom
    for role, msg, msg_y in visible_messages:
        is_user = role == "user"
        bubble_height = draw_message_bubble(
            surface, msg, BOARD_SIZE + 10, msg_y, max_bubble_width, is_user
        )

    # Input area
    input_area_y = HEIGHT - 60
    input_rect = pygame.Rect(BOARD_SIZE + 10, input_area_y, CHAT_PANEL_WIDTH - 20, 40)

    # Input background
    input_border_color = INPUT_FOCUS_BORDER if chat_active else INPUT_BORDER
    input_surface = create_rounded_rect_surface(
        input_rect.width, input_rect.height, 8, INPUT_BG, input_border_color, 2
    )
    surface.blit(input_surface, input_rect.topleft)

    # Input placeholder or text
    if input_text or is_typing:
        display_text = input_text + ("|" if is_typing else "")
        input_surf = CHAT_FONT.render(display_text, True, BOT_TEXT)
    else:
        input_surf = CHAT_FONT.render("Ask about the position...", True, TYPING_INDICATOR)

    # Ensure text fits in input box
    if input_surf.get_width() > input_rect.width - 16:
        # Scroll text if too long
        text_surface = pygame.Surface((input_rect.width - 16, input_surf.get_height()), SRCALPHA)
        text_surface.blit(input_surf, (-(input_surf.get_width() - (input_rect.width - 16)), 0))
        surface.blit(text_surface, (input_rect.x + 8, input_rect.y + 8))
    else:
        surface.blit(input_surf, (input_rect.x + 12, input_rect.y + 10))

    # Send button hint
    send_hint = CHAT_FONT_SMALL.render("Press Enter to send", True, TYPING_INDICATOR)
    surface.blit(send_hint, (BOARD_SIZE + 12, HEIGHT - 18))

def get_square_from_mouse(pos):
    x, y = pos
    if y >= BOARD_SIZE: return None # Clicked in info panel
    r = y // SQUARE_SIZE
    c = x // SQUARE_SIZE
    if 0 <= r < 8 and 0 <= c < 8:
        return r, c
    return None

def display_promotion_dialog(surface, player_color):
    """Displays promotion choices and returns the chosen piece type ('Q', 'R', 'B', 'N')."""
    choices = ['Q', 'R', 'B', 'N']
    piece_options = [] # To store rects for click detection

    dialog_width = SQUARE_SIZE * 2.5
    dialog_height = SQUARE_SIZE * 1.5
    dialog_x = (WIDTH - dialog_width) / 2
    dialog_y = (HEIGHT - dialog_height) / 2

    # Background with rounded corners
    dialog_surface = create_rounded_rect_surface(
        int(dialog_width), int(dialog_height), 12, PROMOTION_BG_COLOR, PROMOTION_BORDER_COLOR, 3
    )
    surface.blit(dialog_surface, (dialog_x, dialog_y))

    text_surf = FONT.render("Promote to:", True, BLACK)
    surface.blit(text_surf, (dialog_x + 10, dialog_y + 10))

    spacing = 10
    img_size = SQUARE_SIZE // 2
    current_x = dialog_x + (dialog_width - (len(choices) * img_size + (len(choices)-1) * spacing)) / 2

    for i, choice_char in enumerate(choices):
        img_key = f"{player_color.lower()}{choice_char.upper()}"
        img_rect = pygame.Rect(current_x, dialog_y + SQUARE_SIZE * 0.5, img_size, img_size)

        if img_key in PROMOTION_PIECE_IMAGES:
            surface.blit(PROMOTION_PIECE_IMAGES[img_key], img_rect.topleft)
        else: # Fallback drawing (should not be needed)
            pygame.draw.rect(surface, (100,100,100), img_rect)
            txt = FONT.render(choice_char, True, BLACK)
            surface.blit(txt, txt.get_rect(center=img_rect.center))

        piece_options.append({'rect': img_rect, 'choice': choice_char})
        current_x += img_size + spacing

    pygame.display.flip() # Update screen to show dialog

    # Wait for user choice
    while True:
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()  # pylint: disable=no-member
                exit()
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    for option in piece_options:
                        if option['rect'].collidepoint(mouse_pos):
                            return option['choice']
        clock.tick(FPS)


# --- Main Game Loop ---
def main():
    global game # Make game accessible for reset
    game = ChessGame()
    load_assets() # Load images after Pygame init

    selected_piece_pos = None # (r, c) of the selected piece
    legal_move_targets = []   # List of (r, c) for legal moves of selected piece

    # Stockfish analysis results
    best_moves = None
    pv_lines = None

    # Chat state
    chat_messages = [
        ("bot", "Hello! I'm your chess assistant. I can help analyze positions, suggest moves, and answer questions about the game. What would you like to know?")
    ]
    input_text = ""
    is_typing = False
    chat_active = False

    running = True
    while running:
        reset_button_rect = None
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False

            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    mouse_pos = pygame.mouse.get_pos()
                    # Chat input box area
                    input_rect = pygame.Rect(BOARD_SIZE + 10, HEIGHT - 60, CHAT_PANEL_WIDTH - 20, 40)
                    if input_rect.collidepoint(mouse_pos):
                        chat_active = True
                        is_typing = True
                    else:
                        chat_active = False
                        is_typing = False

                    # Only process board clicks if not typing in chat
                    if not chat_active:
                        # Check reset button first if game is over
                        if game.game_over_message and hasattr(main, 'last_reset_button_rect') and main.last_reset_button_rect:
                            if main.last_reset_button_rect.collidepoint(mouse_pos):
                                game = ChessGame() # Reset game
                                selected_piece_pos = None
                                legal_move_targets = []
                                continue # Skip further click processing for this event

                        if game.game_over_message: # If game is over, don't process board clicks
                            continue

                        clicked_sq = get_square_from_mouse(mouse_pos)
                        if not clicked_sq: continue

                        r_clk, c_clk = clicked_sq

                        if selected_piece_pos:
                            from_sq = selected_piece_pos
                            to_sq = clicked_sq

                            if to_sq in legal_move_targets: # Attempt to make the move
                                promotion_choice = None
                                if game.needs_promotion(from_sq, to_sq):
                                    # Draw current state before dialog
                                    screen.fill(WHITE)
                                    draw_board(screen)
                                    draw_pieces(screen, game.get_board_state())
                                    draw_highlights(screen, selected_piece_pos, legal_move_targets)
                                    main.last_reset_button_rect = draw_info_panel(screen, game.status_message, game.game_over_message)
                                    pygame.display.flip() # Show board state before dialog

                                    promotion_choice = display_promotion_dialog(screen, game.current_player)

                                result = game.process_move(from_sq, to_sq, promotion_choice)
                                # process_move updates game.status_message and game.game_over_message

                                # After a successful move, run Stockfish analysis
                                if result is True:
                                    fen = game.get_fen()
                                    try:
                                        best_moves = stockfish_analysis.evaluate_moves(fen)
                                        pv_lines = stockfish_analysis.get_principal_variations(fen)
                                    except Exception as e:
                                        best_moves = None
                                        pv_lines = None
                                        print("Stockfish analysis error:", e)

                                selected_piece_pos = None # Deselect after move attempt
                                legal_move_targets = []

                            elif game.get_board_state()[r_clk][c_clk] and \
                                 game.get_board_state()[r_clk][c_clk].color == game.current_player:
                                # Clicked on another of own pieces, select it instead
                                selected_piece_pos = clicked_sq
                                piece_obj = game.get_board_state()[r_clk][c_clk]
                                all_legal_moves = game.get_all_legal_moves_for_player(game.current_player)
                                legal_move_targets = [m[1] for m in all_legal_moves if m[0] == selected_piece_pos]
                            else:
                                # Clicked on empty square or opponent (not a legal move target), deselect
                                selected_piece_pos = None
                                legal_move_targets = []

                        else: # No piece selected yet
                            piece_at_click = game.get_board_state()[r_clk][c_clk]
                            if piece_at_click and piece_at_click.color == game.current_player:
                                selected_piece_pos = clicked_sq
                                all_legal_moves = game.get_all_legal_moves_for_player(game.current_player)
                                legal_move_targets = [m[1] for m in all_legal_moves if m[0] == selected_piece_pos]
                            else:
                                selected_piece_pos = None
                                legal_move_targets = []

            if event.type == pygame.KEYDOWN and chat_active:  # pylint: disable=no-member
                if event.key == pygame.K_RETURN:  # pylint: disable=no-member
                    if input_text.strip():
                        chat_messages.append(("user", input_text.strip()))
                        # Compose Stockfish summary for context
                        fen = game.get_fen()
                        stockfish_summary = ""
                        if best_moves:
                            stockfish_summary += "Best moves: " + ", ".join(f"{san} ({score})" for _, score, san in best_moves[:3])
                        if pv_lines:
                            stockfish_summary += " | Top lines: " + " | ".join(" ".join(line['pv']) for line in pv_lines[:2])
                        try:
                            llm_response = model_chat.ask_model(input_text.strip(), fen, stockfish_summary)
                        except Exception as e:
                            llm_response = f"Error: {e}"
                        chat_messages.append(("bot", llm_response))
                        input_text = ""
                elif event.key == pygame.K_BACKSPACE:  # pylint: disable=no-member
                    input_text = input_text[:-1]
                elif event.key == pygame.K_TAB:  # pylint: disable=no-member
                    pass  # Ignore tab
                elif event.key == pygame.K_ESCAPE:  # pylint: disable=no-member
                    chat_active = False
                    is_typing = False
                else:
                    if len(input_text) < 200:
                        input_text += event.unicode

        # Drawing
        screen.fill(WHITE) # Fill background for info panel area
        draw_board(screen)
        if selected_piece_pos or legal_move_targets: # Only draw if there's something to highlight
            draw_highlights(screen, selected_piece_pos, legal_move_targets)
        draw_pieces(screen, game.get_board_state())
        main.last_reset_button_rect = draw_info_panel(
            screen,
            game.status_message,
            game.game_over_message
        )
        draw_enhanced_chat_panel(screen, chat_messages, input_text, is_typing, chat_active)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()  # pylint: disable=no-member

if __name__ == "__main__":
    main()
