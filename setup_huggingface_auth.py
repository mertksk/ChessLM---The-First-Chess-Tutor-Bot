#!/usr/bin/env python3
"""
Helper script to set up Hugging Face authentication for gated models.
Run this script if you want to use models like google/gemma-3-4b-it.
"""

import os
import sys
import subprocess

def check_authentication():
    """Check if HuggingFace authentication is already set up."""
    # Check for token in environment
    if os.environ.get("HF_TOKEN") or os.environ.get("HUGGING_FACE_HUB_TOKEN"):
        print("✓ HuggingFace token found in environment variables")
        return True

    # Check for token in HF cache
    hf_token_path = os.path.expanduser("~/.cache/huggingface/token")
    if os.path.exists(hf_token_path):
        print("✓ HuggingFace token found in cache")
        return True

    print("✗ No HuggingFace authentication found")
    return False

def setup_authentication():
    """Guide user through HuggingFace authentication setup."""
    print("\n" + "="*60)
    print("HUGGING FACE AUTHENTICATION SETUP")
    print("="*60)

    print("\nTo use gated models like Gemma 3 4B, you need to:")
    print("\n1. Create a Hugging Face account (if you don't have one):")
    print("   https://huggingface.co/join")

    print("\n2. Accept the model's license agreement:")
    print("   https://huggingface.co/google/gemma-3-4b-it")
    print("   (Click 'Accept License' on the model page)")

    print("\n3. Create an access token:")
    print("   https://huggingface.co/settings/tokens")
    print("   - Click 'New token'")
    print("   - Give it a name (e.g., 'chess-assistant')")
    print("   - Select 'Read' permission")
    print("   - Click 'Generate token'")
    print("   - Copy the token")

    print("\n" + "-"*60)

    choice = input("\nDo you have a HuggingFace token ready? (y/n): ").lower()

    if choice == 'y':
        print("\nYou can set up authentication in two ways:")
        print("1. Use huggingface-cli (recommended)")
        print("2. Set environment variable")

        method = input("\nChoose method (1 or 2): ")

        if method == '1':
            print("\nRunning huggingface-cli login...")
            print("Paste your token when prompted (it won't be visible):")
            try:
                subprocess.run(["huggingface-cli", "login"], check=True)
                print("\n✓ Authentication successful!")
            except subprocess.CalledProcessError:
                print("\n✗ Authentication failed. Please try again.")
            except FileNotFoundError:
                print("\n✗ huggingface-cli not found. Installing...")
                subprocess.run([sys.executable, "-m", "pip", "install", "huggingface-hub[cli]"], check=True)
                print("Please run this script again.")

        elif method == '2':
            token = input("\nPaste your token here: ").strip()

            print("\nAdd this to your shell configuration file:")
            print(f"export HF_TOKEN='{token}'")

            shell = os.environ.get('SHELL', '').split('/')[-1]
            if shell == 'bash':
                config_file = "~/.bashrc"
            elif shell == 'zsh':
                config_file = "~/.zshrc"
            else:
                config_file = "your shell configuration file"

            print(f"\nFor permanent setup, add the above line to {config_file}")
            print("Then run: source " + config_file)

            # Set for current session
            os.environ['HF_TOKEN'] = token
            print("\n✓ Token set for current session")

    else:
        print("\nPlease follow the steps above to create a token, then run this script again.")
        print("\nAlternatively, you can use open models that don't require authentication:")
        print("- google/gemma-2b-it")
        print("- google/gemma-7b-it")

def test_gated_model_access():
    """Test if we can access a gated model."""
    print("\n" + "-"*60)
    print("Testing access to gated models...")

    try:
        from transformers import AutoConfig
        config = AutoConfig.from_pretrained("google/gemma-3-4b-it")
        print("✓ Successfully accessed google/gemma-3-4b-it")
        return True
    except Exception as e:
        if "gated repo" in str(e):
            print("✗ Cannot access gated model. Authentication required.")
        else:
            print(f"✗ Error: {e}")
        return False

def main():
    print("Checking HuggingFace authentication status...")

    is_authenticated = check_authentication()

    if is_authenticated:
        if test_gated_model_access():
            print("\n✓ You're all set! You can now use gated models.")
        else:
            print("\nAuthentication found but cannot access gated models.")
            print("You may need to accept the model's license agreement:")
            print("https://huggingface.co/google/gemma-3-4b-it")
    else:
        setup_authentication()

if __name__ == "__main__":
    main()
