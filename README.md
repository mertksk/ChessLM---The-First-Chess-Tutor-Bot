# Pygame Chess with AI Assistant

This is a Python-based chess application built using Pygame, featuring a graphical user interface, core chess logic, integration with the Stockfish analysis engine, and an AI chat assistant powered by a Hugging Face language model.

## Features

*   **Pygame GUI:** A visual interface for playing chess, displaying the board, pieces, and game status.
*   **Core Chess Logic:** Implements standard chess rules, including move validation, special moves (castling, en passant, promotion), and game end conditions (checkmate, stalemate).
*   **Stockfish Analysis:** Integrates with the Stockfish chess engine to provide move evaluations and principal variations for the current board position.
*   **AI Chat Assistant:** Interact with a language model (defaulting to TinyLlama, configurable for Gemma and others) to ask questions about the game, positions, or get general chess advice.

## Requirements

*   Python 3.7 or higher
*   The Python libraries listed in `requirements.txt`.
*   The Stockfish chess engine executable. You will need to download and install Stockfish separately for the analysis features to work. Ensure the `stockfish` executable is in your system's PATH or update the `stockfish_path` variable in `stockfish_analysis.py`.
*   For using gated Hugging Face models (like `google/gemma-3-4b-it`), you will need a Hugging Face account and an access token. See the instructions in `gemini_chat.py` on how to set this up.

## Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd <repository_directory>
    ```
    (Replace `<repository_url>` and `<repository_directory>` with the actual details.)

2.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Install Stockfish:**
    Download and install the Stockfish chess engine from the official website ([https://stockfishchess.org/](https://stockfishchess.org/)). Make sure the `stockfish` executable is accessible from your system's PATH.

## Usage

1.  **Run the application:**
    ```bash
    python chess_gui.py
    ```

2.  **Playing the game:**
    *   Click on a piece to select it.
    *   Legal moves for the selected piece will be highlighted.
    *   Click on a highlighted square to move the piece.
    *   If a pawn reaches the opposite end of the board, a promotion dialog will appear.

3.  **Using the AI Chat Assistant:**
    *   Click on the chat input box on the right side of the window.
    *   Type your question or message.
    *   Press Enter to send your message.
    *   The AI assistant will respond based on the current board position and (if available) Stockfish analysis.

## File Structure

*   `chess_gui.py`: Handles the Pygame graphical user interface, drawing the board, pieces, and chat, and processing user input.
*   `chess_logic.py`: Contains the core chess game rules, piece definitions, move validation, and game state management.
*   `stockfish_analysis.py`: Provides functions to interact with the Stockfish engine for move evaluation and principal variation analysis.
*   `gemini_chat.py`: Manages the integration with the Hugging Face language model for the AI chat assistant.
*   `requirements.txt`: Lists the necessary Python libraries.
*   `.env`: (Optional) Can be used to store environment variables like the Hugging Face token.
*   `assets/pieces/`: Contains the SVG image files for the chess pieces.

## Configuration

*   **Changing the LLM Model:** You can modify the `MODEL_ID` variable in `gemini_chat.py` to use a different compatible Hugging Face language model. Be aware that larger models may require more system resources (RAM, GPU).
*   **Stockfish Path:** If the `stockfish` executable is not in your system's PATH, you can update the `stockfish_path` variable in `stockfish_analysis.py` to the full path of the executable.

## Contributing

(Add information on how others can contribute if this is an open-source project.)

## License

(Add license information here.)
