from ui_window import UIManager

def main():
    # Create and initialize the UI manager
    ui = UIManager()
    ui.initialize()

    # Sample result data to display
    sample_result = {
        "corrected_text": "This is an example of corrected text, shown in the green box.",
        "error_analysis": [
            {
                "original": "He go to school yesterday.",
                "corrected": "He went to school yesterday.",
                "explanation": "Use the past tense 'went' instead of 'go' when referring to the past."
            },
            {
                "original": "She don't like coffee.",
                "corrected": "She doesn't like coffee.",
                "explanation": "For 'she/he/it', use 'doesn't' instead of 'don't'."
            },
            {
                "original": "I am agree with you.",
                "corrected": "I agree with you.",
                "explanation": "'Agree' is a normal verb here; you don't need 'am'."
            },
        ]
    }

    # Show the result in the UI
    ui.show_result(sample_result)

    # Start the Qt event loop
    if ui.app is not None:
        ui.app.exec()

if __name__ == "__main__":
    main()
