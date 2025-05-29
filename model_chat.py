import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
import warnings
import os

# Suppress transformers warnings
warnings.filterwarnings("ignore", category=UserWarning)

# Model configuration - Using Gemma 2B which is open access
MODEL_ID = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"  # 1.1B, fast and open# Alternative open models you can use:
# MODEL_ID = "google/gemma-2-2b-it"  # Newer 2B model
# MODEL_ID = "google/gemma-7b-it"    # Larger 7B model (needs more RAM)

# For the gated 4B model, you would need to authenticate first (see instructions below)
# MODEL_ID = "google/gemma-3-4b-it"  # Requires authentication

CACHE_DIR = os.path.expanduser("~/.cache/huggingface")  # Where models are cached

# Initialize the model pipeline
print(f"Loading {MODEL_ID} model...")
print("Note: This model will be downloaded on first use.")
print(f"Models are cached in: {CACHE_DIR}")

# Check if CUDA is available
device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32

if device == "cpu":
    print("Running on CPU. Performance may be slower than GPU.")

try:
    # Try to load with authentication token if available
    hf_token = os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN")

    # Initialize the pipeline
    pipe = pipeline(
        "text-generation",
        model=MODEL_ID,
        device=device,
        torch_dtype=dtype,
        model_kwargs={"cache_dir": CACHE_DIR},
        token=hf_token,  # Will be None if not set
        max_new_tokens=500,
        temperature=0.7,
        do_sample=True,
        top_p=0.95
    )
    print(f"Model loaded successfully on {device}")
except Exception as e:
    print(f"Error loading model: {e}")

    # Try without token for open models
    if "gated repo" in str(e):
        print("\n" + "="*60)
        print("AUTHENTICATION REQUIRED")
        print("="*60)
        print("The model you're trying to use requires authentication.")
        print("\nTo use gated models like 'google/gemma-3-4b-it', follow these steps:")
        print("1. Create a Hugging Face account at https://huggingface.co/")
        print("2. Visit the model page: https://huggingface.co/google/gemma-3-4b-it")
        print("3. Accept the license agreement")
        print("4. Create an access token at https://huggingface.co/settings/tokens")
        print("5. Set your token using one of these methods:")
        print("   - Run: huggingface-cli login")
        print("   - Or set environment variable: export HF_TOKEN='your_token_here'")
        print("\nFor now, switching to an open model...")
        print("="*60 + "\n")

        # Fallback to open model
        MODEL_ID = "google/gemma-2b-it"
        print(f"Using open model: {MODEL_ID}")

        pipe = pipeline(
            "text-generation",
            model=MODEL_ID,
            device=device,
            torch_dtype=dtype,
            model_kwargs={"cache_dir": CACHE_DIR},
            max_new_tokens=500,
            temperature=0.7,
            do_sample=True,
            top_p=0.95
        )
        print(f"Model loaded successfully on {device}")
    else:
        raise

def ask_model(question, fen, stockfish_summary=None):
    """
    Ask Gemma a question about the current chess position.
    The prompt includes the FEN and optionally a Stockfish summary.
    Returns the LLM's response as a string.

    Note: This function name is kept as 'ask_model' for compatibility
    with the existing chess_gui.py code, even though we're using Gemma.
    """

    # Build the prompt
    prompt = f"""You are a helpful chess assistant. Analyze the given position and answer the user's question.

Current chess position (FEN): {fen}"""

    if stockfish_summary:
        prompt += f"\n\nEngine analysis: {stockfish_summary}"

    prompt += f"\n\nUser question: {question}\n\nAssistant: "

    try:
        # Generate response
        response = pipe(
            prompt,
            max_new_tokens=300,
            temperature=0.7,
            do_sample=True,
            top_p=0.95,
            pad_token_id=pipe.tokenizer.eos_token_id,
            return_full_text=False
        )

        # Extract the generated text
        assistant_response = response[0]['generated_text'].strip()

        # Clean up any potential formatting issues
        if assistant_response.startswith("Assistant:"):
            assistant_response = assistant_response[10:].strip()

        # If response is empty, provide a fallback
        if not assistant_response:
            assistant_response = "I'm analyzing the position. Could you please rephrase your question?"

        return assistant_response

    except Exception as e:
        error_msg = f"Error generating response: {str(e)}"
        print(error_msg)
        return "I apologize, but I encountered an error while analyzing the position. Please try again."


# Optional: Preload the model with a test query to ensure it's ready
if __name__ == "__main__":
    # Test the model
    test_fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    print("\nTesting model...")
    test_response = ask_model("What opening should I play?", test_fen)
    print(f"Test response: {test_response}")

    print("\n" + "="*60)
    print("AVAILABLE MODELS")
    print("="*60)
    print("Open models (no authentication required):")
    print("- google/gemma-2b-it     (2B parameters, fastest)")
    print("- google/gemma-2-2b-it   (2B parameters, newer)")
    print("- google/gemma-7b-it     (7B parameters, needs ~16GB RAM)")
    print("\nGated models (require authentication):")
    print("- google/gemma-3-4b-it   (4B parameters)")
    print("- google/gemma-2-9b-it   (9B parameters)")
    print("- google/gemma-2-27b-it  (27B parameters)")
    print("\nTo change models, edit MODEL_ID in this file.")
    print("="*60)
